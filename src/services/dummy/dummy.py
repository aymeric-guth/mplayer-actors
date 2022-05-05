from ..base import Actor, Message, Sig, actor_system


class Dummy(Actor):
    def __init__(self, pid: int, name='',parent: Actor|None=None) -> None:
        super().__init__(pid, name, parent)

    def run(self) -> None:
        while 1:
            (sender, msg) = self.mq.get()
            self.debug(sender, msg)
            (actor, msg) = self.dispatch(sender, msg)
            # actor_system.send(actor, msg)
            self.mq.task_done()

    def dispatch(self, sender, msg) -> None:
        match msg:
            case Message(Sig.INIT):
                ...

            case Message(Sig.PING):
                return sender, Message(sig=Sig.PONG)

            case Message(Sig.PONG):
                ...

            case Message(Sig.DISPATCH_ERROR):
                print('Could not deliver message to actor')

            case _:
                ...
