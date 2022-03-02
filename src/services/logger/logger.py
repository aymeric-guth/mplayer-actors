import datetime
from collections import deque

from ..base import Message, Sig, actor_system
from ..base.base_actor import BaseActor


def get_dt() -> str:
    return datetime.datetime.now().isoformat()


class Logger(BaseActor):
    def __init__(self, pid: int, name='', parent: BaseActor=None) -> None:
        super().__init__(pid, name)
        self.logs = deque()

    def dispatch(self, sender: BaseActor, msg: Message) -> None:
        match msg:
            case Message(sig=Sig.INIT, args=args):
                ...

            case Message(sig=Sig.PUSH, args=args) if isinstance(args, list):
                [ self.post(None, a) for a in args ]

            case Message(sig=Sig.PUSH, args=args) if isinstance(args, str):
                self.logs.appendleft(f'{get_dt()} {args}')

            case Message(sig=Sig.GET, args=None):
                actor_system.send(sender, Message(Sig.LOGS, list(self.logs)))

            case Message(sig=Sig.GET, args=args) if isinstance(args, int) and args >= 0 and args < len(self.logs):
                actor_system.send(sender, Message(Sig.LOGS, list(self.logs[:args])))

            case _:
                ...
