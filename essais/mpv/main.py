import locale
from ctypes import c_char_p, c_uint64, c_int, pointer, POINTER, c_void_p, sizeof, cast, create_string_buffer
from dataclasses import dataclass
from typing import Any
import select

import mpv as _mpv



@dataclass(frozen=True)
class MpvEvent:
    event: str
    id: int
    name: str
    data: Any

    def __repr__(self) -> str:
        return f'MpvEvent(event={self.event}, id={self.id}, name={self.name}, data={self.data})'


def observe_property(handle, name: str) -> None:      
    property_id = hash(name) & 0xffffffffffffffff
    _mpv._mpv_observe_property(handle, property_id, name.encode('utf-8'), _mpv.MpvFormat.NODE)


lc, enc = locale.getlocale(locale.LC_NUMERIC)
locale.setlocale(locale.LC_NUMERIC, 'C')
handle = _mpv._mpv_create()
_mpv._mpv_set_option_string(handle, b'audio-display', b'no')
_mpv._mpv_set_option_string(handle, b'input-default-bindings', b'yes')
_mpv._mpv_set_option_string(handle, b'input-vo-keyboard', b'yes')
_mpv._mpv_initialize(handle)

observe_property(handle, 'time-pos')
event_handle = _mpv._mpv_create_client(handle, b'py_event_handler')

path = '/Users/yul/.av-mp/mount_point/Audio/Music/_Special/motivation/14 Jolly Days.mp3'
args = [b'loadfile', path.encode('utf-8'), b'replace', b'', None]
args = (c_char_p*len(args))(*args)
_mpv._mpv_command(handle, args)


def mpv_handler(event: MpvEvent) -> None:
    ...


while 1:
    # rr, wr, err = select.select([lambda: _mpv._mpv_wait_event(handle, 0)], [], [])
    mpv_event = _mpv._mpv_wait_event(handle, -1).contents
    out = cast(create_string_buffer(sizeof(_mpv.MpvNode)), POINTER(_mpv.MpvNode))
    _mpv._mpv_event_to_node(out, pointer(mpv_event))
    rv = out.contents.node_value(decoder=lambda b: b.decode('utf-8'))
    event = MpvEvent(
        event=rv.get('event'),
        id=mpv_event.reply_userdata,
        name=rv.get('name'),
        data=rv.get('data')
    )
    # print(event)
    _mpv._mpv_free_node_contents(out)
    mpv_handler(event)
