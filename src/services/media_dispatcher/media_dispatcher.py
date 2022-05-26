import logging
from typing import Optional
import time

from ...external.actors import Actor, Message, Sig, send, create, DispatchError, Event, Request, Response
from ...external.actors.utils import Observable

from ..mpv import MPV
from .playlist import Playlist
from ...settings import PlaybackMode

from ...utils import SingletonMeta


def playback_setter(value: PlaybackMode) -> PlaybackMode:
    match value:
        case PlaybackMode.NORMAL._value_:
            return PlaybackMode.NORMAL
        case PlaybackMode.LOOP_ONE._value_:
            return PlaybackMode.LOOP_ONE
        case PlaybackMode.LOOP_ALL._value_:
            return PlaybackMode.LOOP_ALL
        case _:
            return PlaybackMode.NORMAL

class MediaDispatcher(Actor):
    playback_mode = Observable(setter=playback_setter)
    current_item = Observable(setter=lambda x: x)
    playlist_pos = Observable(setter=lambda x: x)

    def __init__(self, pid: int, parent: int, name='', **kwargs) -> None:
        super().__init__(pid, parent, name, **kwargs)
        self.wid = b'\x00\x00\x00\x00'
        self.current_item = ''
        self.playlist_pos = (0, 0)
        self.playback_mode = PlaybackMode.NORMAL
        # self.log_lvl = logging.INFO
        self.log_lvl = logging.ERROR
        self.subs = [
            ('MPV', 'volume'),
            ('MPV', 'time-pos'),
            ('MPV', 'duration'),
            ('MPV', 'player-state'),
        ]

    def dispatch(self, sender: int, msg: Message) -> None:
        try:
            super().dispatch(sender, msg)
        except DispatchError:
            return

        match msg:
            case Response(type='files', name='content', args=args):
                Playlist().init(args)
                item = Playlist().next()
                send(self.pid, Request(type='player', name='play-item', args=item))

            # case Request(type='player', name='play-selection', args=args):
            case Request(type='play', name='selection', args=args):
                send(to='Files', what=Request(type='files', name='content', args=args))

            case Request(type='player', name='play-item', args=item):
                self.current_item = item if item is not None else self.current_item
                if item is not None:
                    send(to=self.child, what=Request(type='player', name='play-item', args=self.current_item))
                    self.playlist_pos = Playlist().pos()

            case Message(sig=Sig.PLAYBACK_MODE, args=args):
                if args >= PlaybackMode.NORMAL._value_ and args <= PlaybackMode.LOOP_ALL._value_:
                    self.playback_mode = args

            # case Request(type='player', name='volume', args=args):
            case Message(sig=Sig.VOLUME, args=args) as msg:
                send(to=self.child, what=msg)

            # case Request(type='player', name='play-pause', args=args):
            case Message(sig=Sig.PLAY_PAUSE, args=args) as msg:
                send(to=self.child, what=msg)

            case Request(type='player', name='play-next', args=args):
                item = Playlist().next()
                send(to=self.pid, what=Request(type='player', name='play-item', args=item))

            case Request(type='player', name='play-previous', args=args):
                item = Playlist().prev()
                send(to=self.pid, what=Request(type='player', name='play-item', args=item))

            case Message(sig=Sig.NEXT, args=None):
                match self.playback_mode:
                    case PlaybackMode.NORMAL:
                        item = Playlist().next()
                    case PlaybackMode.LOOP_ONE:
                        item = Playlist().current()
                    case PlaybackMode.LOOP_ALL:
                        item = None
                    case _:
                        item = None
                send(to=self.pid, what=Request(type='player', name='play-item', args=item))

            case Message(sig=Sig.PREVIOUS, args=None):
                item = Playlist().prev()
                send(to=self.pid, what=Request(type='player', name='play-item', args=item))

            case Message(sig=Sig.STOP, args=None) as msg:
                Playlist().clear()
                send(to=self.child, what=msg)

            case Message(sig=Sig.DONE, args=None):
                if Playlist():
                    send(to=self.pid, what=Message(sig=Sig.NEXT))

            case Message(sig=Sig.SEEK, args=args) as msg:
                send(to=self.child, what=msg)

            case Event(type='property-change', name=name, args=args) as event:
                if name == 'player-state' and args == 4:
                    send(to=self.pid, what=Message(sig=Sig.DONE, args=None))
                send(to='Display', what=event)

            case _:
                self.logger.warning(f'Unprocessable msg={msg}')


    def init(self) -> None:
        create(MPV, wid=self.wid)
        for actor, event in self.subs:
            send(to=actor, what=Message(sig=Sig.SUBSCRIBE, args=event))

    def terminate(self) -> None:
        for actor, event in self.subs:
            send(to=actor, what=Message(sig=Sig.UNSUBSCRIBE, args=event))
        send(to=self.child, what=Message(Sig.EXIT))
        raise SystemExit
