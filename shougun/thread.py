from enum import StrEnum
from collections import namedtuple
from typing import Dict, List, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

ThreadState = StrEnum('ThreadState', ['BLOCKED', 'RUNNABLE', 'TIMED_WAITING', 'WAITING', 'TERMINATED', 'DAEMON'])

Lock = namedtuple('Lock', 'address,type')


class JavaThread(dict):
    def __init__(self, thread_name: str) -> None:
        super().__init__()
        self.name = thread_name

    def __getattr__(self, attr: str) -> Any:
        return super().__getitem__(attr)

    def __setattr__(self, key: str, value: Any):
        return super().__setitem__(key, value)

    def __str__(self):
        stacktrace = '\n\t'.join(self.stacktrace)
        return f"{self.line}\n{stacktrace}"

    def __repr__(self):
        return f"<JavaThreadInfo({self.name})>"

    def __eq__(self, obj: Any) -> bool:
        if isinstance(obj, JavaThread):
            # NOTE(iwalker): currently we consider two threads the same if
            #  - they are both in the same state
            #  - they both have the same length stacktrace
            # This is not great, but it seems to work for now.
            return (self.state == obj.state) and (len(self.stacktrace) == len(obj.stacktrace))
        return False


class JavaThreadDump(object):
    def __init__(self, timestamp: 'datetime') -> None:
        self.timestamp = timestamp
        self.info: Optional[str] = None
        self.locks: Dict[str, Lock] = dict()
        self.locks_held: Dict[str, str] = dict()
        self.waiting_to_lock: Dict[str, List[str]] = dict()
        self._statistics: Dict[str, int] = {k.value: 0 for k in ThreadState}
        self._threads: Dict[str, JavaThread] = dict()

    def __iter__(self):
        for stack_trace in self._threads.values():
            yield stack_trace

    def __len__(self):
        return len(self._threads)

    def __getitem__(self, items: str) -> Any:
        return self._threads[items]

    def __contains__(self, item: str) -> bool:
        return item in self._threads

    def get(self, item: str, default: Optional[Any] = None) -> Any:
        return self._threads.get(item, default)

    def names(self):
        return self._threads.keys()

    def append(self, thread: JavaThread):
        self._statistics[thread.state.value] += 1
        self._threads[thread.name] = thread

    def __str__(self) -> str:
        return f"JavaThreadDump for {self.timestamp} with {len(self._threads)} threads " \
            f"[B: {self._statistics['blocked']}, R: {self._statistics['runnable']}, TW: {self._statistics['timed_waiting']}, " \
            f"W: {self._statistics['waiting']}, D: {self._statistics['daemon']}]"

    def __repr__(self) -> str:
        return f"<JavaThreadDump({self.timestamp})>"
