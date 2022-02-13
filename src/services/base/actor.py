from typing import TypeVar
from queue import Queue

from .base_actor import BaseActor
from .message import Message
from .actor_system import actor_system


T = TypeVar('T', bound='Actor')


class Actor(BaseActor):
    def __init__(self, pid: int, name:str='', parent: T=None) -> None:
        super().__init__(pid, name)
        self.parent = parent
        self.DEBUG = 0
        self.mq = Queue()

    def run(self) -> None:
        while 1:
            (sender, msg) = self.mq.get()
            self.debug(sender, msg)
            self.dispatch(sender, msg)
            self.mq.task_done()

    def dispatch(self, sender: T, msg: Message) -> None:
        ...

    def post(self, sender: int, msg: Message) -> None:
        self.mq.put((sender, msg))

    def debug(self, sender: T, msg: Message) -> None:
        sender = actor_system.get_actor(sender)
        if self.DEBUG:
            print(f'{self=} {sender=} {msg=}')

    def __del__(self) -> None:
        actor_system.terminate(self)
