import logging
from typing import Optional

from ...external.actors import Actor, Message, Sig, send, create, DispatchError

from ..mpv import MPV
from .playlist import Playlist
from ...settings import PlaybackMode

from ...utils import SingletonMeta


class MediaDispatcher(Actor):
    def __init__(self, pid: int, parent: int, name='', **kwargs) -> None:
        super().__init__(pid, parent, name, **kwargs)
        self.wid = b'\x00\x00\x00\x00'
        self.pl: Playlist = None
        self.playback = PlaybackMode.NORMAL
        self.log_lvl = logging.ERROR
        self.child: int

    def dispatch(self, sender: int, msg: Message) -> None:
        try:
            super().dispatch(sender, msg)
        except DispatchError:
            return

        match msg:
            case Message(sig=Sig.PLAY_ALL, args=args):
                send('Files', Message(sig=Sig.FILES_GET, args=args))

            case Message(sig=Sig.FILES_GET, args=args):
                self.pl = Playlist(args)
                item = self.pl.next()
                send(self.pid, Message(sig=Sig.PLAY, args=item))

            case Message(sig=Sig.PLAY, args=args):
                if args is not None:
                    send('MPV', Message(sig=Sig.PLAY, args=args))
                    send('Display', Message(sig=Sig.MEDIA_META, args={'file': args}))
                    send('Display', Message(sig=Sig.MEDIA_META, args={'pos': self.pl.pos()}))

            case Message(sig=Sig.PLAYBACK_MODE, args=args):
                if args >= PlaybackMode.NORMAL._value_ and args <= PlaybackMode.LOOP_ALL._value_:
                    self.playback = args

            case Message(sig=Sig.VOLUME, args=args) as msg:
                self.logger.error(f'{args=} {type(args)=}')
                send('MPV', msg)

            case Message(sig=Sig.PLAY_PAUSE, args=args) as msg:
                send('MPV', msg)

            case {'event': 'command', 'name': 'next', 'args': None}:
                item = self.pl.next()
                send(self.pid, Message(sig=Sig.PLAY, args=item))

            case {'event': 'command', 'name': 'previous', 'args': None}:
                item = self.pl.prev()
                send(self.pid, Message(sig=Sig.PLAY, args=item))

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
                send(self.pid, Message(sig=Sig.PLAY, args=item))

            case Message(sig=Sig.PREVIOUS, args=None):
                item = self.pl.prev()
                send(self.pid, Message(sig=Sig.PLAY, args=item))

            case Message(sig=Sig.STOP, args=None) as msg:
                if self.pl is not None:
                    self.pl.clear()
                send('MPV', msg)

            case Message(sig=Sig.DONE, args=None):
                if self.pl is not None:
                    send(self.pid, Message(sig=Sig.NEXT))

            case Message(sig=Sig.SEEK, args=args) as msg:
                send('MPV', msg)

            case Message(sig=Sig.WATCHER, args=args):
                send('Display', Message(sig=Sig.MEDIA_META, args=args))

            case _:
                self.logger.warning(f'Unprocessable msg={msg}')

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
        # send('Display', Message(sig=Sig.MEDIA_META, args={'playback-mode': self.playback}))

    def init(self) -> None:
        self.child = create(MPV, wid=self.wid)
        send(self.child, Message(sig=Sig.INIT))

    def terminate(self) -> None:
        send(self.child, Message(Sig.SIGQUIT))
