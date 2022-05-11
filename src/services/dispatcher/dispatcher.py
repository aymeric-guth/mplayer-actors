import logging

from ..base import Actor, Message, Sig, actor_system, ActorGeneric
from .helpers import eval_cmd
from ...utils import SingletonMeta


class Dispatcher(Actor, metaclass=SingletonMeta):
    def __init__(self, pid: int, name='',parent: Actor|None=None, **kwargs) -> None:
        super().__init__(pid, name, parent, **kwargs)
        # self.log_lvl = logging.INFO

    def dispatch(self, sender: ActorGeneric, msg: Message) -> None:
        match msg:
            case Message(sig=Sig.INIT, args=args):
                ...

            case Message(sig=Sig.PARSE, args=args):
                (actor, msg) = eval_cmd(args)
                actor_system.send(actor, msg)

            case Message(sig=Sig.LOGIN_FAILURE, args=args):
                self.logger.error(f'LOGIN_FAILURE SIGNAL handler, exiting... {msg=}')
                raise SystemExit

            case Message(sig=Sig.NETWORK_FAILURE, args=args):
                self.logger.error(f'NETWORK_FAILURE SIGNAL handler, exiting... {msg=}')
                raise SystemExit

            case Message(sig=Sig.SIGQUIT):
                self.terminate()

            # case Message(sig=Sig.AUDIT, args=None):
            #     actor_system.send(sender, {'event': 'audit', 'data': self.introspect()})

            # case _:
            #     print(f'Default SIGNAL handler, exiting... {msg=}')
            #     raise SystemExit

    def terminate(self) -> None:
        raise SystemExit('SIGQUIT')
