import logging

from actors import (
    Actor,
    Message,
    send,
    create,
    DispatchError,
    Event,
    Request,
    Response,
    SystemMessage,
)
from actors.subsystems.observable_properties import Observable

from ..mpv import MPV
from .playlist import Playlist

from ._types import PlaybackMode


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

    def __init__(self, pid: int, parent: int, name="", **kwargs) -> None:
        super().__init__(pid, parent, name, **kwargs)
        self.wid = b"\x00\x00\x00\x00"
        self.current_item = ""
        self.playlist_pos = (0, 0)
        self.playback_mode = PlaybackMode.NORMAL
        self.log_lvl = logging.ERROR
        self.subs = [
            # ('MPV', 'volume'),
            # ('MPV', 'time-pos'),
            # ('MPV', 'duration'),
            ("MPV", "player-state"),
        ]

    def dispatch(self, sender: int, msg: Message) -> None:
        try:
            super().dispatch(sender, msg)
        except SystemMessage:
            return

        match msg:
            # case Response(type='get', name='file', args=data):
            #     path = self.localpath / 'cached'
            #     with open(path, 'wb') as f:
            #         f.write(data)
            #     send(self.pid, Request(type='player', name='play-item', args=str(path)))
            case Request(type="player", name="play-selection", args=args):
                send(to="Files", what=Request(type="files", name="content", args=args))

            case Response(type="files", name="content", args=args):
                # send(to='API', what=Request(type='get', name='file', args=args))
                Playlist().init(args)
                item = Playlist().next()
                send(self.pid, Request(type="player", name="play-item", args=item))

            case Request(type="player", name="play-item", args=item):
                if item is None:
                    return
                self.current_item = item
                send(
                    to=self.child,
                    what=Request(
                        type="player", name="play-item", args=self.current_item
                    ),
                )
                self.playlist_pos = Playlist().pos()

            case Request(type="player", name="playback-mode", args=args):
                if (
                    args >= PlaybackMode.NORMAL._value_
                    and args <= PlaybackMode.LOOP_ALL._value_
                ):
                    self.playback_mode = args

            case Request(type="player", name="play-previous", args=args):
                item = Playlist().prev()
                send(
                    to=self.pid,
                    what=Request(type="player", name="play-item", args=item),
                )

            case Request(type="player", name="play-next"):
                match self.playback_mode:
                    case PlaybackMode.NORMAL:
                        item = Playlist().next()
                    case PlaybackMode.LOOP_ONE:
                        item = Playlist().current()
                    case PlaybackMode.LOOP_ALL:
                        item = None
                    case _:
                        item = None
                send(
                    to=self.pid,
                    what=Request(type="player", name="play-item", args=item),
                )

            case Request(type="player", name="play-stop") as msg:
                Playlist().clear()
                send(to=self.child, what=msg)

            case Event(type="property-change", name=name, args=args) as event:
                if name == "player-state" and args == 4:
                    send(to=self.pid, what=Request(type="player", name="play-next"))
                send(to="Display", what=event)

            case _:
                # self.logger.error(f"Unprocessable msg={msg}")
                raise DispatchError

    def init(self) -> None:
        create(MPV, wid=self.wid)
        for actor, event in self.subs:
            self.subscribe(to=actor, what=event)

    def terminate(self) -> None:
        for actor, event in self.subs:
            self.unsubscribe(to=actor, what=event)
        raise SystemExit
