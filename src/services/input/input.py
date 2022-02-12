import select
import sys
import os

from ..base import Actor, Message, Sig


class Input(Actor):
    def __init__(self, dispatcher: Actor) -> None:
        super().__init__()
        self.dispatcher = dispatcher

    def run(self) -> None:
        while 1:
            (rr, wr, er) = select.select([sys.stdin], [], [])
            for f in rr:
                cmd = f.readline().lstrip().rstrip()
                self.dispatcher.post(self, Message(sig=Sig.PARSE, args=cmd))
