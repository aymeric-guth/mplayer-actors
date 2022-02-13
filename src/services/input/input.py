import select
import sys
import os

from ..base import Actor, Message, Sig, actor_system


class Input(Actor):
    def __init__(self, pid: int, name='',parent: Actor=None) -> None:
        super().__init__(pid, name, parent)

    def run(self) -> None:
        while 1:
            (rr, wr, er) = select.select([sys.stdin], [], [])
            for f in rr:
                cmd = f.readline().lstrip().rstrip()
                actor_system.send('Dispatcher', Message(sig=Sig.PARSE, args=cmd))
