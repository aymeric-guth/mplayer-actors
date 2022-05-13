from ..base import Actor, Message, Sig, actor_system, ActorGeneric
from ..mpv import MPV
from .playlist import Playlist
from ...settings import PlaybackMode


class MediaDispatcher(Actor):
    def __init__(self, pid: int, parent: ActorGeneric, name='', **kwargs) -> None:
        super().__init__(pid, parent, name, **kwargs)
        self.wid = b'\x00\x00\x00\x00'
        self.pl: Playlist = None
        self.playback = PlaybackMode.NORMAL
       
    def dispatch(self, sender: ActorGeneric, msg: Message) -> None:
        match msg:
            case Message(sig=Sig.INIT, args=None):
                actor_system.create_actor(MPV, wid=self.wid)

            case Message(sig=Sig.PLAY_ALL, args=args):
                actor_system.send('Files', Message(sig=Sig.FILES_GET, args=args))

            case Message(sig=Sig.FILES_GET, args=args):
                self.pl = Playlist(args)
                item = self.pl.next()
                self.post(Message(sig=Sig.PLAY, args=item))

            case Message(sig=Sig.PLAY, args=args):
                actor_system.send('MPV', Message(sig=Sig.PLAY, args=args))
                actor_system.send('Display', Message(sig=Sig.MEDIA_META, args={'file': args}))
                actor_system.send('Display', Message(sig=Sig.MEDIA_META, args={'pos': self.pl.pos()}))

            case Message(sig=Sig.PLAYBACK_MODE, args=args):
                if args >= PlaybackMode.NORMAL._value_ and args <= PlaybackMode.LOOP_ALL._value_:
                    self.playback = args

            case Message(sig=Sig.VOLUME, args=args) as msg:
                actor_system.send('MPV', msg)

            case Message(sig=Sig.VOLUME_INC, args=args) as msg:
                actor_system.send('MPV', msg)

            case Message(sig=Sig.PLAY_PAUSE, args=args) as msg:
                actor_system.send('MPV', msg)

            case Message(sig=Sig.NEXT, args=None):
                match self.playback:
                    case PlaybackMode.NORMAL:
                        item = self.pl.next()
                    case PlaybackMode.LOOP_ONE:
                        item = self.pl.current()
                    case PlaybackMode.LOOP_ALL:
                        item = None
                    case _:
                        item = None
                self.post(Message(sig=Sig.PLAY, args=item))

            case Message(sig=Sig.PREVIOUS, args=None):
                item = self.pl.prev()
                self.post(Message(sig=Sig.PLAY, args=item))

            case Message(sig=Sig.STOP, args=None):
                self.pl.clear()
                actor_system.send('MPV', msg)

            case Message(sig=Sig.DONE, args=None):
                if self.pl is not None:
                    self.post(Message(sig=Sig.NEXT))

            case Message(sig=Sig.SEEK, args=args) as msg:
                actor_system.send('MPV', msg)

            case Message(sig=Sig.WATCHER, args=args) as msg:
                # self.post(args)
                actor_system.send('Display', Message(sig=Sig.MEDIA_META, args=args))

            # case Message(sig=Sig.PLAYBACK_CHANGE, args=args) as msg:
            #     actor_system.send('Display', Message(sig=Sig.MEDIA_META, args={'player-state': args}))

            # case Message(sig=Sig.VOLUME_CHANGE, args=args) as msg:
            #     actor_system.send('Display', Message(sig=Sig.MEDIA_META, args={'player-volume': args}))

            # case Message(sig=Sig.POS_CHANGE, args=args) as msg:
            #     actor_system.send('Display', Message(sig=Sig.MEDIA_META, args={'playback': args}))

            # case Message(sig=Sig.AUDIT, args=None):
            #     actor_system.send(sender, {'event': 'audit', 'data': self.introspect()})

            case Message(sig=Sig.SIGQUIT):
                self.terminate()

            case _:
                raise SystemExit(f'{msg=}')

    @property
    def playback(self) -> PlaybackMode:
        return self._playback

    @playback.setter
    def playback(self, value: PlaybackMode) -> None:
        match value:
            case PlaybackMode.NORMAL._value_:
                self._playback = PlaybackMode.NORMAL
            case PlaybackMode.LOOP_ONE._value_:
                self._playback = PlaybackMode.LOOP_ONE
            case PlaybackMode.LOOP_ALL._value_:
                self._playback = PlaybackMode.LOOP_ALL
            case _:
                self._playback = PlaybackMode.NORMAL

        actor_system.send('Display', Message(sig=Sig.MEDIA_META, args={'playback-mode': self._playback}))
