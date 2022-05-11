from typing import TypeVar, Any, Union, Optional
from queue import Queue
import traceback
import sys
from inspect import currentframe, getframeinfo, trace
import threading
import logging
import logging.handlers

from .message import Message
from ...utils import clamp
from ...settings import LOG_HOST, LOG_PORT, LOG_FORMAT


T = TypeVar('T', bound='BaseActor')
ActorGeneric = Union[int, str, T, type]


class BaseActor:
    def __init__(self, pid: int, name:str='') -> None:
        self._pid = pid
        self._name = name if name else self.__class__.__name__

        self.mq: Queue = Queue()
        self.subscribers: list[BaseActor] = []

        self._last = 0
        self._logger: logging.LoggerAdapter[logging.Logger]
        self._log_lock = threading.Lock()

    def run(self) -> None:
        while 1:
            (sender, msg) = self.mq.get()
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
        ...
    
    def handler(self, err) -> None:
        ...

    def post(self, sender: ActorGeneric, msg: Message|dict[str, str]) -> None:
        self.mq.put((sender, msg))

    def __hash__(self) -> int:
        return hash(self.pid)

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

    @property
    def log_lvl(self) -> int:
        return self._log_lvl

    @log_lvl.setter
    def log_lvl(self, value: int) -> None:
        self._log_lvl = int(clamp(0, 50)(value))
        self.logger.setLevel(self._log_lvl)

    @property
    def log_lock(self) -> threading.Lock:
        return self._log_lock

    @log_lock.setter
    def log_lock(self, value: Any) -> None:
        raise TypeError

    @property
    def logger(self) -> logging.LoggerAdapter:
        with self._log_lock:
            return self._logger

    @logger.setter
    def logger(self, value: Any) -> None:
        raise TypeError

    def init_logger(self, name) -> None:
        fmt = logging.Formatter(fmt=LOG_FORMAT)
        handler = logging.handlers.SocketHandler(LOG_HOST, LOG_PORT)
        handler.setFormatter(fmt)
        _logger = logging.getLogger(name)
        _logger.addHandler(handler)
        self._logger = logging.LoggerAdapter(_logger, {'actor': self.__repr__()})
        self.log_lvl = logging.ERROR

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(pid={self.pid})'
        # return f'{self.__class__.__name__}(pid={self.pid}, name={self.name}, ...)'
    
    def __enter__(self) -> None:
        self._log_lock.acquire()
        self._last = self.log_lvl
        self.log_lvl = 0

    def __exit__(self, type, value, traceback) -> None:
        self.log_lvl = self._last
        self._log_lock.release()
