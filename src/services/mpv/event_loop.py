from typing import Any
from dataclasses import dataclass
from ctypes import cast, sizeof, POINTER, create_string_buffer, pointer

from ...external import _mpv
from ...external.actors import ActorIO, send, Message, Sig


@dataclass(frozen=True)
class MpvEvent:
    event: str
    id: int
    name: str
    data: Any

    def __repr__(self) -> str:
        return f'MpvEvent(event={self.event}, id={self.id}, name={self.name}, data={self.data})'


class MPVEvent(ActorIO):
    def __init__(self, pid: int, parent: int, name='', handle: Any=None, **kwargs) -> None:
        super().__init__(pid, parent, name, **kwargs)
        if handle is None:
            raise SystemExit
        self.handle = handle
        self.event_handle = _mpv.mpv_create_client(self.handle, b'py_event_handler')

    def run(self) -> None:
        while 1:
            mpv_event = _mpv.mpv_wait_event(self.handle, -1).contents            
            out = cast(create_string_buffer(sizeof(_mpv.MpvNode)), POINTER(_mpv.MpvNode))
            _mpv.mpv_event_to_node(out, pointer(mpv_event))
            try:
                rv = out.contents.node_value(decoder=lambda b: b.decode('utf-8'))
                event = MpvEvent(
                    event=rv.get('event'),
                    id=mpv_event.reply_userdata,
                    name=rv.get('name'),
                    data=rv.get('data')
                )
                _mpv.mpv_free_node_contents(out)
                self.logger.info(f'event={event}')
                send(self.parent, Message(sig=Sig.MPV_EVENT, args=event))
            except Exception as err:
                self.logger.error(str(err))
                self.logger.error(bytes(out))
