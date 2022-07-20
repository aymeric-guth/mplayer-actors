from __future__ import annotations
from dataclasses import dataclass
import copy
from pathlib import PurePath
import threading

from ...settings import MOUNT_POINT, ROOT
from utils import SingletonMeta


# API -> model
# model -> API

# model -> full realpath local
# model -> filename
# model -> filename.ext
# model -> ext
# model -> tuple key (formated_path)
# model -> realpath local ?
# model -> to dict


class File:
    def __init__(self, *, path: str, filename: str, extension: str) -> None:
        self._path = path
        self._filename = filename
        self._ext = extension
        self._key = tuple(path.split("/")[1:-1])

    @classmethod
    def from_json(cls, param: dict[str, str]):
        return cls(
            path=param["path"], filename=param["filename"], ext=param["extension"]
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "path": self.path,
            "filename": self.filename,
            "extension": self.ext,
        }

    @property
    def realpath(self) -> str:
        # PurePath
        return str(
            copy.deepcopy(MOUNT_POINT)
            / "/".join(self._key)
            / f"{self.filename}{self.ext}"
        )

    def fullpath(self) -> str:
        return f"{self.path}{self.filename}{self.ext}"

    @property
    def path(self) -> str:
        return self._path

    @property
    def full_filename(self) -> str:
        return f"{self.filename}{self.ext}"

    @property
    def filename(self) -> str:
        return self._filename

    @property
    def ext(self) -> str:
        return self._ext

    @property
    def key(self) -> tuple[str, ...]:
        return self._key

    def to_tuple(self) -> tuple[str, str]:
        return (self.filename, self.ext)

    def __str__(self) -> str:
        return f"{self.path}{self.filename}{self.ext}"

    def __hash__(self) -> int:
        return hash(self.fullpath)

    def __iter__(self):
        ...

    def __next__(self):
        ...


class CWD(metaclass=SingletonMeta):
    cwd_l: threading.Lock = threading.Lock()

    def __init__(self) -> None:
        self.mountpoint = copy.deepcopy(MOUNT_POINT)  # PurePath
        self._path: list[str] = list(ROOT)

    def push(self, value: str) -> None:
        self._path.append(value)

    def pop(self) -> None:
        if len(self) > 2:
            self._path.pop()

    @property
    def realpath(self) -> PurePath:
        return self.mountpoint / "/".join(self._path[1:])  # PurePath

    @property
    def path(self) -> tuple[str, ...]:
        return tuple(self._path)

    @path.setter
    def path(self, value: list[str]) -> None:
        self._path = list(value)

    def __len__(self) -> int:
        return len(self._path)

    def __repr__(self) -> str:
        return f"CWD(_path={self._path}, mounpoint={self.mountpoint})"
