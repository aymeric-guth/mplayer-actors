import locale
from ctypes import c_char_p, c_uint64, c_int, pointer, POINTER, c_void_p, sizeof, cast, create_string_buffer
from dataclasses import dataclass
from typing import Any, Optional, Callable
import logging
import time
from typing import Callable, Any
from functools import wraps

from ...settings import VOLUME_DEFAULT
from ...external import _mpv

from ...utils import clamp
from ...external.actors import Actor, Message, Sig, send, create, DispatchError, Event, Request, ActorSystem, SystemMessage
from ...external.actors.utils import Observable

from .event_loop import MpvEvent, MPVEvent



def volume_setter() -> Callable[[str], float]:
    _volume = 0.
    func = lambda x: clamp(0., 100.)(x) if x is not None else 0.

    def inner(volume: str):
        nonlocal _volume

        if isinstance(volume, str) and (volume.startswith('+') or volume.startswith('-')):
            _volume = func(_volume + float(volume))
        else:
            _volume = func(float(volume))
        return _volume
    return inner


class MPV(Actor):
    volume = Observable(setter=volume_setter())
    time_pos = Observable()
    duration = Observable()
    player_state = Observable(setter=lambda x: int(clamp(0, 4)(x)))
    playtime_remaining = Observable()
    metadata = Observable()

    def __init__(self, pid: int, parent: int, name='', **kwargs) -> None:
        super().__init__(pid, parent, name, **kwargs)
        self.volume = str(VOLUME_DEFAULT)
        self.time_pos = 0.
        self.duration = 0.
        self.player_state = 0
        self.playtime_remaining = 0.
        self.metadata = None
        lc, enc = locale.getlocale(locale.LC_NUMERIC)
        locale.setlocale(locale.LC_NUMERIC, 'C')

        self.handle = _mpv.mpv_create()
        _mpv.mpv_set_option_string(self.handle, b'audio-display', b'no')
        _mpv.mpv_set_option_string(self.handle, b'input-default-bindings', b'no')
        _mpv.mpv_set_option_string(self.handle, b'input-vo-keyboard', b'no')
        # mpv_load_config_file(self.handle, str(path).encode('utf-8'))
        _mpv.mpv_initialize(self.handle)
        # self.log_lvl = logging.INFO
        self.log_lvl = logging.ERROR

    def dispatch(self, sender: int, msg: Message) -> None:
        try:
            super().dispatch(sender, msg)
        except SystemMessage:
            return

        match msg:
            case Event(type='property-change', name=name, args=data):
                self.publish(name=name, value=data)

            case Request(type='player', name='play-item', args=item):
                args = [b'loadfile', item.encode('utf-8'), b'replace', b'', None]
                self.set_property('pause', 'no')
                self.command(*args)

            case Request(type='player', name='play-pause'):
                if self.player_state == 1:
                    self.set_property('pause', 'yes')
                    self.player_state = 2
                elif self.player_state == 2:
                    self.set_property('pause', 'no')
                    self.player_state = 1

            case Request(type='player', name='volume', args=args):
                self.volume = args
                self.set_property('volume', self.volume)
            
            case Request(type='player', name='play-stop'):
                args = [b'stop', b'', None]
                self.command(*args)

            case Request(type='player', name='seek', args=args):
                if args < 0.:
                    req = clamp(-self.time_pos, 0.)(args)
                else:                    
                    req = clamp(0., self.duration-self.time_pos)(args)
                args = [b'seek', str(req).encode('utf-8'), b'relative', b'default-precise', None]
                self.command(*args)

            case _:
                self.logger.error(f'Unprocessable msg={msg}')
                # raise DispatchError

    async def command_async(self, *args) -> int:
        args = [c_uint64(0xffff), (c_char_p*len(args))(*args)]
        return _mpv.mpv_command_async(self.handle, *args)

    def command(self, *args) -> int:
        # self.logger.error(f'command({args})')
        try:        
            args = (c_char_p*len(args))(*args)
            return _mpv.mpv_command(self.handle, args)
        except SystemError:
            return -1

    def set_property(self, name: str, value: list|dict|set|str):
        # self.logger.info(f'set_property({name=}, {value=})')
        ename = name.encode('utf-8')
        if isinstance(value, (list, set, dict)):
            _1, _2, _3, pointer = _mpv.make_node_str_list(value)
            _mpv.mpv_set_property(self.handle, ename, _mpv.MpvFormat.NODE, pointer)
        else:            
            _mpv.mpv_set_property_string(self.handle, ename, _mpv.mpv_coax_proptype(value))

    def terminate(self) -> None:       
        self.handle, handle = None, self.handle
        send(to=self.child, what=Message(sig=Sig.EXIT))
        _mpv.mpv_render_context_free(self.handle)
        raise SystemExit

    def init(self) -> None:
        create(MPVEvent, handle=self.handle)
