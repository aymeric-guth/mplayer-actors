from typing import TypeVar, Any, Union, Optional
from queue import Queue
from inspect import currentframe, getframeinfo, trace
import threading
import logging
import logging.handlers

from .message import Message
from .sig import Sig
from .subststems import Logging

from ...utils import clamp
from ...settings import LOG_HOST, LOG_PORT, LOG_FORMAT


T = TypeVar('T', bound='BaseActor')
ActorGeneric = Union[int, str, T, type]


# class ActorStr:
#     def __init__(self, pid: int, parent: str, name: str, _cls: str) -> None:
#         self.pid = pid
#         self.parent = parent
#         self.name = name
#         self.cls = _cls

#     def __str__(self) -> str:
#         return f'{self.cls}(pid={self.pid}, parent={self.parent})'

#     def __repr__(self) -> str:
#         return self.__str__()

#     @classmethod
#     def from_actor(cls, pid: int, parent: str, name: str, _cls: str) -> ActorStr:
#         return cls(pid, parent, name, _cls)


class BaseActor:
    def __init__(self, pid: int, parent: int, name: str='') -> None:
        self._pid = pid
        self._parent = parent
        self._name = name if name else self.__class__.__name__

        self._mq: Queue = Queue()
        self.subscribers: list[BaseActor] = []

        ### Subsystems ###
        self._logger = Logging(self._name, self.__str__())

        # self.post(Message(sig=Sig.INIT))

    def run(self) -> None:
        while 1:
            (sender, msg) = self._mq.get()
            self.log_mq(sender, msg)
            try:
                self.dispatch(sender, msg)
            except Exception as err:
                # frameinfo = getframeinfo(currentframe())
                # exc_info = str(sys.exc_info()[2]) + '\n' + repr(frameinfo)
                # print(sys.exc_info()[2])
                # traceback.format_exc()
                self.handler(f'{err} {trace(1)[-1]}')
                raise SystemExit
            else:
                self._mq.task_done()

    def dispatch(self, sender: int, msg: Message) -> None:
        raise NotImplementedError
    
    def handler(self, err) -> None:
        raise NotImplementedError

    def terminate(self) -> None:
        raise NotImplementedError
    
    def init(self) -> None:
        raise NotImplementedError

    def post(self, msg: Message|dict[str, Any], sender: Optional[int]=None) -> None:
        if sender is None:
            sender = self.pid  
        self.log_post(sender, msg)
        self._mq.put_nowait((sender, msg))

    @property
    def pid(self) -> int:
        return self._pid

    @pid.setter
    def pid(self, value: Any) -> None:
        raise TypeError('Property is immutable')

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        raise TypeError('Property is immutable')

    @property
    def parent(self) -> int:
        return self._parent

    @parent.setter
    def parent(self, value: Any) -> None:
        raise TypeError('Property is immutable')

    @property
    def log_lvl(self) -> int:
        return self._logger.log_lvl

    @log_lvl.setter
    def log_lvl(self, value: int) -> None:
        self._logger.log_lvl = value

    @property
    def logger(self) -> logging.LoggerAdapter:
        return self._logger.logger

    @logger.setter
    def logger(self, value: Any) -> None:
        raise TypeError('Property is immutable')

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(pid={self.pid})'

    def __str__(self) -> str:
        return f'{self.__class__.__name__}(pid={self.pid})'

    def __hash__(self) -> int:
        return hash(self.pid)

    def log_mq(self, sender: Optional[int], msg: Message|dict[str, Any]) -> None:
        return self._logger.log(self.pid, sender, msg, '### MQ ###')
    
    def log_post(self, sender: Optional[int], msg: Message|dict[str, Any]) -> None:
        return self._logger.log(self.pid, sender, msg, '### POST ###')
