from ..base import Actor, Message, Sig, actor_system
from .helpers import eval_cmd
from ..api import API
from ...utils import SingletonMeta


class Dispatcher(Actor, metaclass=SingletonMeta):
    def __init__(self, pid: int, name='',parent: Actor=None, **kwargs) -> None:
        super().__init__(pid, name, parent, **kwargs)
        self.LOG = 0

    def dispatch(self, sender: Actor, msg: Message) -> None:
        match msg:
            case Message(sig=Sig.INIT, args=args):
                ...

            case Message(sig=Sig.PARSE, args=args):
                (actor, msg) = eval_cmd(args)
                actor_system.send(actor, msg)

            case Message(sig=Sig.LOGIN_FAILURE, args=args):
                self.log_msg(f'LOGIN_FAILURE SIGNAL handler, exiting... {msg=}')
                raise SystemExit

            case Message(sig=Sig.NETWORK_FAILURE, args=args):
                self.log_msg(f'NETWORK_FAILURE SIGNAL handler, exiting... {msg=}')
                raise SystemExit
            
            case _:
                print(f'Default SIGNAL handler, exiting... {msg=}')
                raise SystemExit
