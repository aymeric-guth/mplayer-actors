import time
from threading import Thread

from ..base import Actor, Message, Sig
from ..api import API
from ..files import Files
from ..input import Input
from ..display import Display
from ..mpv import MPV

from .helpers import eval_cmd


class Dispatcher(Actor):
    def __init__(self) -> None:
        super().__init__()
        self.DEBUG = 0
        self.api = API(self)
        self.files = Files(self)
        self.input = Input(self)
        self.display = Display(self)
        self.mpv = MPV(self)
        self.actors = [
            self,
            self.api,
            self.files,
            self.input,
            self.display,
            self.mpv
        ]
        print('Starting daemon threads')
        for a in self.actors:
            Thread(target=a.run, daemon=True).start()

        for recipient in self.actors:
            for a in self.actors:
                recipient.post(a, Message(sig=Sig.REGISTER))

        self.post(self, Message(sig=Sig.INIT))

    def run(self) -> None:
        while 1:
            (actor, msg) = self.mq.get(block=True, timeout=None)
            self.debug(msg, actor)

            match msg.sig:
                case Sig.INIT:
                    self.api.post(self, Message(sig=Sig.LOGIN))
                    self.files.post(self, Message(sig=Sig.INIT))

                case Sig.LOGIN_SUCCESS:
                    self.api.post(self, Message(sig=Sig.EXT_SET))

                case Sig.EXT_SET:
                    self.api.post(self, Message(sig=Sig.FILES_GET, args=msg.args))

                case Sig.FILES_GET:
                    self.files.post(self, Message(sig=Sig.FILES_SET, args=msg.args))

                case Sig.PARSE:
                    (actor, msg) = eval_cmd(self, msg.args)
                    actor.post(self, msg)


                case Sig.LOGIN_FAILURE:
                    print(f'LOGIN_FAILURE SIGNAL handler, exiting... {msg=}')
                    raise SystemExit

                case Sig.NETWORK_FAILURE:
                    print(f'NETWORK_FAILURE SIGNAL handler, exiting... {msg=}')
                    raise SystemExit

                case Sig.REGISTER:
                    self.register(actor)
                
                case Sig.NONE:
                    ...

                case _:
                    print(f'Default SIGNAL handler, exiting... {msg=}')
                    raise SystemExit

            self.mq.task_done()
