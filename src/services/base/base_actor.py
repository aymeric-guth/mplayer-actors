from typing import TypeVar
import traceback
import sys
from queue import Queue
import traceback

from .message import Message

import sys
from inspect import currentframe, getframeinfo, trace



T = TypeVar('T', bound='BaseActor')
ActorGeneric = int|str|T|type


class BaseActor:
    def __init__(self, pid: int, name:str='') -> None:
        self._pid = pid
        if name:
            self._name = name
        else:
            self._name = self.__class__.__name__
        self.LOG = 0
        self.mq: Queue = Queue()
        self.subscribers: list[BaseActor] = []

    def run(self) -> None:
        while 1:
            (sender, msg) = self.mq.get()
            if self.LOG == 1:
                self.logger(sender, msg)
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

    def logger(self, sender: ActorGeneric, msg: Message) -> None:
        ...

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
        return f'{self.__class__.__name__}(pid={self.pid})'
        # return f'{self.__class__.__name__}(pid={self.pid}, name={self.name}, ...)'
    
    # def __del__(self) -> None:
    #     raise SystemExit
