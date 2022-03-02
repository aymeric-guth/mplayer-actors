# from __future__ import annotations
from typing import Optional, Any

from .message import Message
from .sig import Sig
from .actor_system import actor_system



def last_will(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as err:
            actor, *_ = args
            actor_system.post(actor, Message(sig=Sig.SIGINT, args=err))

    return inner


@last_will
def run(self) -> None:
    while 1:
        (sender, msg) = self.mq.get()
        self.debug(sender, msg)
        self.dispatch(sender, msg)
        self.mq.task_done()
