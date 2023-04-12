from typing import TypeVar, Optional

T = TypeVar("T")


def not_none(obj: Optional[T], *, message: Optional[str] = None) -> T:
    if obj is None:
        if message is not None:
            raise TypeError(message)
        raise TypeError("object should not be None")
    return obj
