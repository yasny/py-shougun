from enum import StrEnum
from collections import namedtuple
from typing import Dict, List

ThreadState = StrEnum('ThreadState', ['BLOCKED', 'RUNNABLE', 'TIMED_WAITING', 'WAITING', 'TERMINATED'])

Lock = namedtuple('Lock', 'address,type')


class JavaThread(dict):
    def __init__(self, thread_name):
        super().__init__()
        self.thread_name = thread_name

    def __getattr__(self, attr):
        return super().__getitem__(attr)

    def __setattr__(self, key, value):
        return super().__setitem__(key, value)

    def __str__(self):
        stacktrace = '\n\t'.join(self.stacktrace)
        return f"{self.line}\n{stacktrace}"

    def __repr__(self):
        return f"<JavaThreadInfo({self.thread_name})>"

    def __eq__(self, obj):
        if isinstance(obj, JavaThread):
            return len(self.stacktrace) == len(obj.stacktrace)
        return False


class JavaThreadDump(object):
    def __init__(self, timestamp) -> None:
        self.timestamp = timestamp
        self.info = None
        self.locks: Dict[str, Lock] = dict()
        self.locks_held: Dict[str, str] = dict()
        self.waiting_to_lock: Dict[str, List[str]] = dict()
        self._statistics = {k.value: 0 for k in ThreadState}
        self._threads: Dict[str, JavaThread] = dict()

    def __iter__(self):
        for stack_trace in self._threads.values():
            yield stack_trace

    def __len__(self):
        return len(self._threads)

    def __getitem__(self, items):
        return self._threads[items]

    def __contains__(self, item):
        return item in self._threads

    def get(self, item, default):
        return self._threads.get(item, default)

    def names(self):
        return self._threads.keys()

    def append(self, stack_trace: JavaThread):
        if 'state' in stack_trace:
            self._statistics[stack_trace.state.value] += 1
        self._threads[stack_trace.thread_name] = stack_trace

    def __str__(self):
        return f"JavaThreadDump for {self.timestamp} with {len(self._threads)} threads " \
            f"[B: {self._statistics['blocked']}, R: {self._statistics['runnable']}, TW: {self._statistics['timed_waiting']}, W: {self._statistics['waiting']}]"

    def __repr__(self):
        return f"<JavaThreadDump({self.timestamp})>"
