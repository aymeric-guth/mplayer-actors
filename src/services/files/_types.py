from typing import Any
from dataclasses import dataclass
import copy
import threading

from ...settings import MOUNT_POINT, ROOT
from ...utils import SingletonMeta


# @dataclass(frozen=True)
# class File:
#     path: str
#     filename: str
#     ext: str

#     @classmethod
#     def from_json(cls, param: dict[str, str]):
#         cls(
#             path=param.get('path'),
#             filename=param.get('file_name'),
#             ext=param.get('extension')
#         )

#     @property
#     def file(self) ->str:
#         return f'{self.filename}{self.ext}'


class CWD(metaclass=SingletonMeta):
    cwd_l: threading.Lock = threading.Lock()

    def __init__(self) -> None:
        self.mountpoint = MOUNT_POINT[:]
        self._path: list[str] = list(ROOT)
    
    def push(self, value: str) -> None:
        self._path.append(value)

    def pop(self) -> None:
        if len(self) > 1:
            self._path.pop()

    @property
    def realpath(self) -> str:
        return f"{self.mountpoint}{'/'.join(self._path[1:])}/"

    @property
    def path(self) -> tuple[str, ...]:
        return tuple(self._path)

    @path.setter
    def path(self, value: list[str]) -> None:
        self._path = value

    def __len__(self) -> int:
        return len(self._path)