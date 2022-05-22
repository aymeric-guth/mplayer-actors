from typing import Any, Union

from .actor_system import ActorSystem, _get_caller

from ...utils import SingletonMeta


class Send(metaclass=SingletonMeta):
    def __init__(self) -> None:
        self.init()

    def init(self) -> None:
        self._pid: Union[int, str, type] = 0
        self._msg: Any = None
        self._sender: Any = None

    def __call__(self) -> None:
        ActorSystem()._send(sender=self._sender, receiver=self._pid, msg=self._msg)
        return self.init()

    def to(self, pid: Union[int, str, type]) -> Any:
        self._sender = _get_caller()
        self.pid = pid
        return self

    def what(self, msg: Any) -> None:
        self.msg = msg
        return self.__call__()

    @property
    def pid(self) -> Union[int, str, type]:
        return self._pid

    @pid.setter
    def pid(self, value: Union[int, str, type]) -> None:
        self._pid = value

    @property
    def msg(self) -> Any:
        return self._msg

    @msg.setter
    def msg(self, value: Any) -> None:
        self._msg = value
