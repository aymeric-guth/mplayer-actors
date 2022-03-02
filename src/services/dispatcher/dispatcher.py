from ..base import Actor, Message, Sig, actor_system
from .helpers import eval_cmd
from ..api import API


class Dispatcher(Actor):
    def __init__(self, pid: int, name='',parent: Actor=None, **kwargs) -> None:
        super().__init__(pid, name, parent, **kwargs)
        self.DEBUG = 0

    def dispatch(self, sender: Actor, msg: Message) -> None:
        match msg:
            case Message(sig=Sig.INIT, args=args):
                actor_system.send(API, Message(sig=Sig.LOGIN))
                # actor_system.send('API', Message(sig=Sig.LOGIN))

            case Message(sig=Sig.LOGIN_SUCCESS, args=args):
                actor_system.send('API', Message(sig=Sig.EXT_SET))

            case Message(sig=Sig.EXT_SET, args=args):
                actor_system.send('API', Message(sig=Sig.FILES_GET, args=args))

            case Message(sig=Sig.FILES_GET, args=args):
                actor_system.send('Files', Message(sig=Sig.FILES_SET, args=args))

            case Message(sig=Sig.PARSE, args=args):
                (actor, msg) = eval_cmd(args)
                actor_system.send(actor, msg)

            case Message(sig=Sig.LOGIN_FAILURE, args=args):
                print(f'LOGIN_FAILURE SIGNAL handler, exiting... {msg=}')
                raise SystemExit

            case Message(sig=Sig.NETWORK_FAILURE, args=args):
                print(f'NETWORK_FAILURE SIGNAL handler, exiting... {msg=}')
                raise SystemExit
            
            case Message(sig=Sig.NONE, args=args):
                ...

            case _:
                print(f'Default SIGNAL handler, exiting... {msg=}')
                raise SystemExit
