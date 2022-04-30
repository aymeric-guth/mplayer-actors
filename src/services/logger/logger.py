import datetime
from collections import deque
import socket

from ..base import Message, Sig, actor_system
from ..base.base_actor import BaseActor


def get_dt() -> str:
    return datetime.datetime.now().isoformat()


class Logger(BaseActor):
    def __init__(self, pid: int, name='', parent: BaseActor=None) -> None:
        super().__init__(pid, name)
        self.logs = deque()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect(('127.0.0.1', 8080))
        except Exception:
            self.sock = None

    def dispatch(self, sender: BaseActor, msg: Message) -> None:
        match msg:
            case Message(sig=Sig.INIT, args=args):
                ...

            case Message(sig=Sig.PUSH, args=args) if isinstance(args, list):
                [ self.post(None, a) for a in args ]
                # for i in args:
                #     self.sock.send(f'{get_dt()} {i}'.encode('utf-8'))

            case Message(sig=Sig.PUSH, args=args) if isinstance(args, str):
                if self.sock:
                    self.sock.send(f'{get_dt()} {args}\n'.encode('utf-8'))
                self.logs.appendleft(f'{get_dt()} {args}')

            case Message(sig=Sig.GET, args=None):
                actor_system.send(sender, Message(Sig.LOGS, list(self.logs)))

            case Message(sig=Sig.GET, args=args) if isinstance(args, int) and args >= 0 and args < len(self.logs):
                actor_system.send(sender, Message(Sig.LOGS, list(self.logs[:args])))

            case _:
                ...
