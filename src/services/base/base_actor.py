from typing import TypeVar

from .message import Message


T = TypeVar('T', bound='BaseActor')


class BaseActor:
    def __init__(self, pid: int, name:str='') -> None:
        self._pid = pid
        if name:
            self._name = name
        else:
            self._name = self.__class__.__name__

    def __hash__(self) -> int:
        return self.pid

    @property
    def pid(self) -> int:
        return self._pid

    @pid.setter
    def pid(self, value) -> None:
        raise TypeError

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        raise TypeError

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(pid={self.pid}, name={self.name}, ...)'
