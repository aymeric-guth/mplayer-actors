from dataclasses import dataclass
import copy
import threading

from ...settings import MOUNT_POINT, extensions_all, ROOT
from ...utils import SingletonMeta


@dataclass(frozen=True)
class File:
    path: str
    filename: str
    extension: str

    @classmethod
    def from_path_full(cls, path_full: str) -> File:
        ...

class CWD(metaclass=SingletonMeta):
    cwd_l: threading.Lock = threading.Lock()

    def __init__(self) -> None:
        self.mountpoint = MOUNT_POINT[:]
        self.path = list(ROOT)
    
    def push(self, value: str) -> None:
        self.path.append(value)

    def pop(self) -> None:
        if len(self.path) > 1:
            self.path.pop()

    def to_tuple(self) -> tuple[str, ...]:
        return tuple(self.path)

    def copy(self) -> CWD:
        return copy.copy(self)

    @property
    def realpath(self) -> str:
        return f"{self.mountpoint}{'/'.join(self.path[1:])}/"
