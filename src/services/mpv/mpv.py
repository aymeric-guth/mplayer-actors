from ..base import Actor, Message, Sig
from .python_mpv_jsonipc import MPV as _MPV


class MPV(Actor):
    def __init__(self, dispatcher: Actor) -> None:
        super().__init__()
        self.dispatcher = dispatcher
        self.mpv = _MPV(mpv_location="/opt/local/bin/mpv")

    def run(self) -> None:
        while 1:
            (actor, msg) = self.mq.get()
            self.debug(msg, actor)

            match msg.sig:
                case Sig.INIT:
                    ...

                case Sig.REGISTER:
                    self.register(actor)

                case Sig.PLAY_ALL:
                    self.get_actor('Files').post(self, Message(sig=Sig.FILES_GET, args=msg.args))

                case Sig.PLAY:
                    # print(f'playing files {msg.args=}')
                    # f, *_ = msg.args
                    # self.mpv.play(f)
                    with open('./playlist.txt', 'w') as f:
                        f.write('\n'.join(msg.args))
                    self.mpv.loadlist('./playlist.txt')

                case _:
                    raise SystemExit(f'{msg=}')

