from ...external.actors import Actor, Message, Sig, actor_system, ActorGeneric
from ...utils import SingletonMeta


class Dispatcher(Actor, metaclass=SingletonMeta):
    def __init__(self, pid: int, parent: int, name='', **kwargs) -> None:
        super().__init__(pid, parent, name, **kwargs)

    def dispatch(self, sender: int, msg: Message) -> None:
        match msg:
            case Message(sig=Sig.INIT, args=args):
                ...

            case Message(sig=Sig.LOGIN_FAILURE, args=args):
                self.logger.error(f'LOGIN_FAILURE SIGNAL handler, exiting... {msg=}')
                raise SystemExit

            case Message(sig=Sig.NETWORK_FAILURE, args=args):
                self.logger.error(f'NETWORK_FAILURE SIGNAL handler, exiting... {msg=}')
                raise SystemExit

            case Message(sig=Sig.SIGQUIT):
                self.terminate()
