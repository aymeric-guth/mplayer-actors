from ..base import Actor, Message, Sig


class Dummy(Actor):
    def __init__(self) -> None:
        super().__init__()

    def run(self) -> None:
        while 1:
            (actor, msg) = self.mq.get()
            self.debug(msg, actor)

            match msg.sig:
                case Sig.INIT:
                    ...

                case Sig.REGISTER:
                    self.register(actor)

                case _:
                    raise SystemExit(f'{msg=}')
