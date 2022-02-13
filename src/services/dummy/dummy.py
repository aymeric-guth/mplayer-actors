from ..base import Actor, Message, Sig, actor_system


class Dummy(Actor):
    def __init__(self, pid: int, name='',parent: Actor=None) -> None:
        super().__init__(pid, name, parent)

    def run(self) -> None:
        while 1:
            (sender, msg) = self.mq.get()
            print(f'{self=} got new {msg=} from {sender=}')
            
            match [msg.sig, msg.args]:
                case [Sig.INIT, None]:
                    ...
                case [Sig.PING, None]:
                    ...

            match msg.sig:
                case Sig.INIT:
                    ...
                
                case Sig.PING:
                    # actor_system.send(self.pid, sender, msg=Message(sig=Sig.PONG))
                    actor_system.send(sender, msg=Message(sig=Sig.PONG))

                case Sig.PONG:
                    ...

                case Sig.DISPATCH_ERROR:
                    print('Could not deliver message to actor')

                case _:
                    ...

            self.mq.task_done()


    def run(self) -> None:
        while 1:
            (sender, msg) = self.mq.get()
            self.debug(sender, msg)
            (actor, msg) = self.dispatch(sender, msg)
            # actor_system.send(actor, msg)
            self.mq.task_done()

    def dispatch(self, sender, msg) -> None:
        match msg.sig:
            case Sig.INIT:
                ...
            
            case Sig.PING:
                return sender, Message(sig=Sig.PONG)

            case Sig.PONG:
                ...

            case Sig.DISPATCH_ERROR:
                print('Could not deliver message to actor')

            case _:
                ...
