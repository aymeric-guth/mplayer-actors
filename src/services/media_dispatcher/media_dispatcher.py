from collections import deque

from ..base import Actor, Message, Sig, actor_system
from ..mpv import MPV
from .playlist import Playlist
from ...settings import LOOP_DEFAULT


class MediaDispatcher(Actor):
    def __init__(self, pid: int, name='',parent: Actor=None, **kwargs) -> None:
        super().__init__(pid, name, parent, **kwargs)
        self.parent = parent
        self.LOG = 0
        self.wid = b'\x00\x00\x00\x00'
        self.child = None
        self.pl = None
        self.loop_mode = LOOP_DEFAULT
        actor_system.create_actor(MPV, wid=self.wid)
       
    def dispatch(self, sender: Actor, msg: Message) -> None:
        match msg:
            case Message(sig=Sig.INIT, args=None):
                ...

            case Message(sig=Sig.PLAY_ALL, args=args):
                actor_system.send('Files', Message(sig=Sig.FILES_GET, args=args))

            case Message(sig=Sig.FILES_GET, args=args):
                self.pl = Playlist(args)
                item = self.pl.next()
                self.post(self, Message(sig=Sig.PLAY, args=item))

            case Message(sig=Sig.PLAY, args=args):
                actor_system.send('MPV', Message(sig=Sig.PLAY, args=args))
                actor_system.send('Display', Message(sig=Sig.MEDIA_META, args={'file': args}))
                actor_system.send('Display', Message(sig=Sig.MEDIA_META, args={'pos': self.pl.pos()}))

            case Message(sig=Sig.LOOP, args=args):
                self.loop_mode = not self.loop_mode

            case Message(sig=Sig.PLAYBACK_CHANGE, args=args) as msg:
                actor_system.send('Display', Message(sig=Sig.MEDIA_META, args={'player-state': args}))

            case Message(sig=Sig.VOLUME_CHANGE, args=args) as msg:
                actor_system.send('Display', Message(sig=Sig.MEDIA_META, args={'player-volume': args}))

            case Message(sig=Sig.POS_CHANGE, args=args) as msg:
                actor_system.send('Display', Message(sig=Sig.MEDIA_META, args={'playback': args}))

            case Message(sig=Sig.VOLUME, args=args) as msg:
                actor_system.send('MPV', msg)

            case Message(sig=Sig.VOLUME_INC, args=args) as msg:
                actor_system.send('MPV', msg)

            case Message(sig=Sig.PLAY_PAUSE, args=args) as msg:
                actor_system.send('MPV', msg)

            case Message(sig=Sig.NEXT, args=None):
                item = self.pl.next()
                if item is not None:
                    self.post(self, Message(sig=Sig.PLAY, args=item))

            case Message(sig=Sig.PREVIOUS, args=None):
                item = self.pl.prev()
                self.post(self, Message(sig=Sig.PLAY, args=item))

            case Message(sig=Sig.STOP, args=None):
                ...
                self.pl = None

            case Message(sig=Sig.DONE, args=None):
                if self.pl is not None:
                    self.post(self, Message(sig=Sig.NEXT))

            case Message(sig=Sig.SEEK, args=args) as msg:
                actor_system.send('MPV', msg)

            case _:
                raise SystemExit(f'{msg=}')
