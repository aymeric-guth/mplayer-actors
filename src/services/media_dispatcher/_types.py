from enum import Enum


class PlaybackState(Enum):
    IDLE = 0
    PLAY = 1
    PAUSE = 2
    SEEK = 4

    def __eq__(self, value: int) -> bool:
        return self._value_ == value

    def __neq__(self, value: int) -> bool:
        return not self.__eq__(value)

    def __lt__(self, value: int) -> bool:
        return self._value_ < value

    def __le__(self, value: int) -> bool:
        return self.__lt__(value) or self.__eq__(value)

    def __gt__(self, value: int) -> bool:
        return self._value_ > value

    def __ge__(self, value: int) -> bool:
        return self.__gt__(value) or self.__eq__(value)


class PlaybackMode(Enum):
    NORMAL = 0
    LOOP_ONE = 1
    LOOP_ALL = 2
    # SHUFFLE = auto()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self._name_}"

    def __str__(self) -> str:
        return self._name_
