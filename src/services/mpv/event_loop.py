from typing import Any
import dataclasses
from ctypes import cast, sizeof, POINTER, create_string_buffer, pointer
import threading
import logging

from actors import ActorIO, send, Event, Request, Response, SystemMessage
from utils import try_not

from ...external import _mpv


@dataclasses.dataclass(frozen=True)
class MpvEvent:
    event: str
    id: int
    name: str
    data: Any

    def __repr__(self) -> str:
        return f"MpvEvent(event={self.event}, id={self.id}, name={self.name}, data={self.data})"

    def to_event(self) -> Event:
        return Event(type=self.event, name=self.name, args=self.data)


def handler(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as err:
            args[0].logger.error(f"{err=}")

    return inner


class MPVEvent(ActorIO):
    def __init__(
        self, pid: int, parent: int, name="", handle: Any = None, **kwargs
    ) -> None:
        super().__init__(pid, parent, name, **kwargs)
        if handle is None:
            raise SystemExit
        # self.run = handler(self.run)
        self.handle = _mpv.mpv_create_client(handle, b"py_event_handler")

        self._t = threading.Thread(target=handler(self._run), daemon=True)
        self._t.start()
        self.log_lvl = logging.ERROR

    def _run(self) -> None:
        while 1:
            # écoute des event, adaptation vers Event(), envoi sur la mailbox publique
            mpv_event = _mpv.mpv_wait_event(self.handle, -1).contents
            out = cast(
                create_string_buffer(sizeof(_mpv.MpvNode)), POINTER(_mpv.MpvNode)
            )
            _mpv.mpv_event_to_node(out, pointer(mpv_event))
            try:
                rv = out.contents.node_value(decoder=lambda b: b.decode("utf-8"))
                event = MpvEvent(
                    event=rv.get("event"),
                    id=mpv_event.reply_userdata,
                    name=rv.get("name"),
                    data=rv.get("data"),
                )
                # send(to=self.pid, what=copy.deepcopy(event))
                send(to=self.pid, what=event.to_event())
                _mpv.mpv_free_node_contents(out)
            except Exception as err:
                self.logger.error(f"{err=} out={bytes(out)}")

    def observe_property(self, name: str) -> None:
        property_id = hash(name) & 0xFFFFFFFFFFFFFFFF
        _mpv.mpv_observe_property(
            self.handle, property_id, name.encode("utf-8"), _mpv.MpvFormat.NODE
        )

    def dispatch(self, sender: int, msg: Any) -> None:
        try:
            super().dispatch(sender, msg)
        except SystemMessage:
            return

        match msg:
            case Event(type="playback-restart" | "start-file" | "unpause"):
                event = Event(type="property-change", name="player-state", args=1)

            case Event(type="idle"):
                event = Event(type="property-change", name="player-state", args=4)

            case Event(type="pause"):
                event = Event(type="property-change", name="player-state", args=2)

            case Event(type="seek"):
                event = Event(type="property-change", name="player-state", args=3)

            case _:
                event = msg

        send(to=self.parent, what=event)

    def terminate(self) -> None:
        _mpv.mpv_destroy(self.handle)
        self.handle = None
        try_not(self._t.join, Exception) if self._t else None
        raise SystemExit

    def init(self) -> None:
        self.observe_property("volume")
        # self.observe_property('percent-pos')
        self.observe_property("time-pos")
        self.observe_property("playback-time")
        self.observe_property("playtime-remaining")
        self.observe_property("duration")
        self.observe_property("metadata")
