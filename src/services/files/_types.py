from dataclasses import dataclass
import copy
from pathlib import PurePath
import threading

from ...settings import MOUNT_POINT, ROOT
from utils import SingletonMeta


@dataclass(frozen=True)
class File:
    path: str
    filename: str
    ext: str

    @classmethod
    def from_json(cls, param: dict[str, str]):
        cls(
            path=param['path'],
            filename=param['file_name'],
            ext=param['extension']
        )

    @property
    def file(self) ->str:
        return f'{self.filename}{self.ext}'

    @property
    def realpath(self) ->str:
        return f'{self.path}{self.filename}{self.ext}'


class CWD(metaclass=SingletonMeta):
    cwd_l: threading.Lock = threading.Lock()

    def __init__(self) -> None:
        self.mountpoint = copy.deepcopy(MOUNT_POINT)
        self._path: list[str] = list(ROOT)
    
    def push(self, value: str) -> None:
        self._path.append(value)

    def pop(self) -> None:
        if len(self) > 2:
            self._path.pop()

    @property
    def realpath(self) -> PurePath:
        return self.mountpoint / '/'.join(self._path[1:])

    @property
    def path(self) -> tuple[str, ...]:
        return tuple(self._path)

    @path.setter
    def path(self, value: list[str]) -> None:
        self._path = list(value)

    def __len__(self) -> int:
        return len(self._path)

    def __repr__(self) -> str:
        return f'CWD(_path={self._path}, mounpoint={self.mountpoint})'
