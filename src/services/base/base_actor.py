from typing import TypeVar, Any, Union, Optional
from queue import Queue
from inspect import currentframe, getframeinfo, trace
import threading
import logging
import logging.handlers

from .message import Message
from .sig import Sig
from ...utils import clamp
from ...settings import LOG_HOST, LOG_PORT, LOG_FORMAT


T = TypeVar('T', bound='BaseActor')
ActorGeneric = Union[int, str, T, type]


class BaseActor:
    def __init__(self, pid: int, parent: ActorGeneric, name: str='') -> None:
        self._pid = pid
        self._parent = parent
        self._name = name if name else self.__class__.__name__

        self.mq: Queue = Queue()
        self.subscribers: list[BaseActor] = []

        self._last = 0
        self._logger: logging.LoggerAdapter[logging.Logger]
        self._log_l = threading.Lock()
        
        fmt = logging.Formatter(fmt=LOG_FORMAT)
        handler = logging.handlers.SocketHandler(LOG_HOST, LOG_PORT)
        handler.setFormatter(fmt)
        _logger = logging.getLogger(self._name)
        _logger.addHandler(handler)
        self._logger = logging.LoggerAdapter(_logger, {'actor': self.__repr__()})
        self.log_lvl = logging.ERROR

        self.post(Message(sig=Sig.INIT))

    def run(self) -> None:
        while 1:
            (sender, msg) = self.mq.get()
            # self.logger.error(f'receiver={self} sender={sender} {msg=}')
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
                self.mq.task_done()

    def dispatch(self, sender: ActorGeneric, msg: Message) -> None:
        raise NotImplementedError
    
    def handler(self, err) -> None:
        raise NotImplementedError

    def terminate(self) -> None:
        raise NotImplementedError

    def post(self, msg: Message|dict[str, str], sender: ActorGeneric=None) -> None:
        self.mq.put((self, msg)) if sender is None else self.mq.put((sender, msg))

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
    def parent(self) -> ActorGeneric:
        return self._parent

    @parent.setter
    def parent(self, value: Any) -> None:
        raise TypeError('Property is immutable')

    @property
    def log_lvl(self) -> int:
        return self._log_lvl

    @log_lvl.setter
    def log_lvl(self, value: int) -> None:
        self._log_lvl = int(clamp(0, 50)(value))
        self.logger.setLevel(self._log_lvl)

    @property
    def log_lock(self) -> threading.Lock:
        return self._log_l

    @log_lock.setter
    def log_lock(self, value: Any) -> None:
        raise TypeError('Property is immutable')

    @property
    def logger(self) -> logging.LoggerAdapter:
        with self._log_l:
            return self._logger

    @logger.setter
    def logger(self, value: Any) -> None:
        raise TypeError('Property is immutable')

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(pid={self.pid}, parent={self.parent})'
    
    def __enter__(self) -> None:
        self.log_lock.acquire()
        self._last = self.log_lvl
        self.log_lvl = 0

    def __exit__(self, type: Any, value: Any, traceback: Any) -> None:
        self.log_lvl = self._last
        self.log_lock.release()

    def __hash__(self) -> int:
        return hash(self.pid)
