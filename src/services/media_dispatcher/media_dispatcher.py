from collections import deque
from enum import Enum, auto

from ..base import Actor, Message, Sig, actor_system, sanity_check
from ..mpv import MPV
from .playlist import Playlist


class MediaDispatcher(Actor):
    def __init__(self, pid: int, name='',parent: Actor=None) -> None:
        super().__init__(pid, name, parent)
        self.parent = parent
        self.DEBUG = 0
        self.wid = b'\x00\x00\x00\x00'
        self.child = None
        self.pl = None
        self.mpv = actor_system.create_actor(MPV, wid=self.wid)
       
    @sanity_check
    def dispatch(self, sender: Actor, msg: Message) -> None:
        match msg.sig:
            case Sig.INIT:
                ...

            case Sig.PLAY_ALL:
                actor_system.send('Files', Message(sig=Sig.FILES_GET, args=msg.args))

            case Sig.FILES_GET:
                self.pl = Playlist(msg.args)
                item = self.pl.next()
                self.post(None, Message(sig=Sig.PLAY, args=item))

            case Sig.PLAY:
                # créer une interface pour dispatcher le fichier vers le bon player
                actor_system.send(self.mpv, Message(sig=Sig.PLAY_ALL, args=msg.args))

            case Sig.VOLUME:
                actor_system.send(self.mpv, Message(sig=Sig.VOLUME, args=msg.args))

            case Sig.PLAY_PAUSE:
                actor_system.send(self.mpv, Message(sig=Sig.PLAY_PAUSE))

            case Sig.NEXT:
                item = self.pl.next()
                if item is not None:
                    self.post(None, Message(sig=Sig.PLAY, args=item))

            case Sig.PREVIOUS:
                item = self.pl.prev()
                self.post(None, Message(sig=Sig.PLAY, args=item))

            case Sig.STOP:
                self.pl = None
                self.mpv.stop()

            case Sig.DONE:
                if self.pl is not None:
                    self.post(None, Message(sig=Sig.NEXT))

            case _:
                raise SystemExit(f'{msg=}')

# FF, F, FW, W