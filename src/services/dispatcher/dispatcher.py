from ..base import Actor, Message, Sig, actor_system
from .helpers import eval_cmd


class Dispatcher(Actor):
    def __init__(self, pid: int, name='',parent: Actor=None) -> None:
        super().__init__(pid, name, parent)
        self.DEBUG = 0

    def dispatch(self, sender: Actor, msg: Message) -> None:
        match msg.sig:
            case Sig.INIT:
                actor_system.send('API', Message(sig=Sig.LOGIN))

            case Sig.LOGIN_SUCCESS:
                actor_system.send('API', Message(sig=Sig.EXT_SET))

            case Sig.EXT_SET:
                actor_system.send('API', Message(sig=Sig.FILES_GET, args=msg.args))

            case Sig.FILES_GET:
                actor_system.send('Files', Message(sig=Sig.FILES_SET, args=msg.args))

            case Sig.PARSE:
                (actor, msg) = eval_cmd(msg.args)
                actor_system.send(actor, msg)

            case Sig.LOGIN_FAILURE:
                print(f'LOGIN_FAILURE SIGNAL handler, exiting... {msg=}')
                raise SystemExit

            case Sig.NETWORK_FAILURE:
                print(f'NETWORK_FAILURE SIGNAL handler, exiting... {msg=}')
                raise SystemExit
            
            case Sig.NONE:
                ...

            case _:
                print(f'Default SIGNAL handler, exiting... {msg=}')
                raise SystemExit
