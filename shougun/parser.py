import logging
import re
import sys
from datetime import datetime
from .thread import JavaThreadDump, JavaThread, ThreadState, Lock


__all__ = ["thread_dumps"]

RE_THREAD_INFO = re.compile(r"^\"(?P<thread>[^\"]+)\".+(os_prio=(?P<os_prio>[0-9]+))?.+(tid=(?P<tid>[a-z0-9x]+)) (nid=(?P<nid>[a-fx0-9]+))? (?P<status>[^[]+) ?(\[(?P<id>[a-fx0-9]+)\])?$")  # noqa
RE_ADDRESS = re.compile(r"<(?P<address>[a-fx0-9]+)> \(a (?P<type>.+)\)")


def get_thread_state(line):
    if "BLOCKED" in line:
        return ThreadState.BLOCKED
    elif "TIMED_WAITING" in line:
        return ThreadState.TIMED_WAITING
    elif "WAITING" in line:
        return ThreadState.WAITING
    elif "RUNNABLE" in line:
        return ThreadState.RUNNABLE
    elif "TERMINATED" in line:
        return ThreadState.TERMINATED
    else:
        raise ValueError(f"Unknown java.lang.Thread.State: {line}")


def thread_dumps(filename, start_datetime=None, end_datetime=None, thread_name_filter_exclude=None, thread_name_filter_include=None, max_count=-1):
    with open(filename, "r") as f:
        current_thread = None
        current_stack_traces = None
        skip = False

        while (raw_line := f.readline()):
            line = raw_line.strip()

            if line.startswith("2023-"):
                dt = datetime.strptime(line.strip(), "%Y-%m-%d %H:%M:%S")
                if (start_datetime and dt < start_datetime) or (end_datetime and dt > end_datetime):
                    logging.debug(f"Skipping thread dump \"{line}\"")
                    skip = True
                    continue

                if current_stack_traces:
                    logging.debug(f"Processed {len(current_stack_traces)} threads")
                    yield current_stack_traces

                if max_count == 0:
                    break

                max_count -= 1

                logging.info(f"Processing thread dump \"{line}\"...")
                skip = False

                current_stack_traces = JavaThreadDump(dt)
                continue

            if skip:
                continue

            if line.startswith("Full thread dump"):
                current_stack_traces.info = line[:-1]
                continue

            if line.startswith("\""):
                if current_thread:
                    current_stack_traces.append(current_thread)

                try:
                    m = RE_THREAD_INFO.search(line)
                    name = m.group("thread")
                    tid = m.group("tid")
                    nid = m.group("nid")
                    status = m.group("status")
                    conditional = m.group("id")
                except AttributeError as e:
                    print(f"{e}\n{line}")
                    sys.exit(1)

                if thread_name_filter_exclude and re.search(thread_name_filter_exclude, name):
                    current_thread = None
                    continue

                if thread_name_filter_include and not re.search(thread_name_filter_include, name):
                    current_thread = None
                    continue

                thread = JavaThread(name)
                thread.tid = int(m.group("tid"), 16) if tid else -1
                thread.nid = int(m.group("nid"), 16) if nid else -1
                thread.status = status
                thread.conditional = conditional
                thread.line = line
                thread.stacktrace = list()

                current_thread = thread
                continue

            if current_thread is None:
                continue

            if "java.lang.Thread.State" in line:
                current_thread.state = get_thread_state(line)

            if "parking to wait" in line:
                m = RE_ADDRESS.search(line)
                address = m.group("address")
                current_thread.parking_for = address

            if "waiting to lock" in line:
                m = RE_ADDRESS.search(line)
                address = m.group("address")
                t = m.group("type")
                lock = Lock(address, t)
                current_thread.waiting_to_lock = lock
                if address not in current_stack_traces.waiting_to_lock:
                    current_stack_traces.waiting_to_lock[address] = list()
                current_stack_traces.waiting_to_lock[address].append(current_thread.thread_name)

            if "locked <" in line:
                m = RE_ADDRESS.search(line)
                address = m.group("address")
                obj_type = m.group("type")
                lock = Lock(address, obj_type)
                if "locking" not in current_thread:
                    current_thread.locking = list()
                current_thread.locking.append(lock)
                current_stack_traces.locks[address] = lock
                current_stack_traces.locks_held[address] = current_thread.thread_name

            current_thread.stacktrace.append(line)
