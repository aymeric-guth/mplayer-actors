import locale
from ctypes import c_char_p, c_uint64, c_int, pointer, POINTER, c_void_p, sizeof, cast, create_string_buffer
from dataclasses import dataclass
from typing import Any, Optional, Callable
import logging
import time

from ...settings import VOLUME_DEFAULT
from ...external import _mpv

from ...utils import clamp
from ...external.actors import Actor, Message, Sig, send, create, DispatchError, Event
# from ...external.actors.utils import observer
from .event_loop import MpvEvent, MPVEvent
from .observable_properties import ObservableProperties



from typing import Callable, Any
from functools import wraps

# from .actor_system import send
# from .message import Event, Message, Sig


def observer(actor: str):
    def inner(func: Callable):
        @wraps(func)
        def _(*args, **kwargs):
            (self, value) = args
            if value is not None:
                name = func.__name__
                func(self, value)
                res = getattr(self, f'_{name}')
                send(to=actor, what=Message(sig=Sig.WATCHER, args={name: res}))
            # send(to=actor, what=Event(type='property-change', name=name, args=res))
        return _
    return inner


class MPV(Actor):
    def __init__(self, pid: int, parent: int, name='', **kwargs) -> None:
        super().__init__(pid, parent, name, **kwargs)
        self._state = 0
        self._volume: int|float
        lc, enc = locale.getlocale(locale.LC_NUMERIC)
        locale.setlocale(locale.LC_NUMERIC, 'C')

        self.handle = _mpv.mpv_create()
        _mpv.mpv_set_option_string(self.handle, b'audio-display', b'no')
        _mpv.mpv_set_option_string(self.handle, b'input-default-bindings', b'no')
        _mpv.mpv_set_option_string(self.handle, b'input-vo-keyboard', b'no')
        # mpv_load_config_file(self.handle, str(path).encode('utf-8'))
        _mpv.mpv_initialize(self.handle)
        self.props = ObservableProperties(self.pid)
        self.log_lvl = logging.ERROR

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

    def dispatch(self, sender: int, msg: Message) -> None:
        try:
            super().dispatch(sender, msg)
        except DispatchError:
            return

        match msg:
            case Event(type='property-change', name=name, args=data) if name in self.props:
                self.props.set(name, data)

            case Message(sig=Sig.PLAY, args=path):
                args = [b'loadfile', path.encode('utf-8'), b'replace', b'', None]
                self.set_property('pause', 'no')
                self.command(*args)

            case Message(sig=Sig.PLAY_PAUSE, args=None):
                if self.props.get('player-state') == 1:
                    self.set_property('pause', 'yes')
                    self.props.set('player-state', 2)
                elif self.props.get('player-state') == 2:
                    self.set_property('pause', 'no')
                    self.props.set('player-state', 1)

            case Message(sig=Sig.VOLUME, args=args):
                self.props.set('volume', args)
                self.set_property('volume', self.props.get('volume'))
            
            case Message(sig=Sig.STOP, args=None):
                args = [b'stop', b'', None]
                self.command(*args)

            case Message(sig=Sig.SEEK, args=args):
                if args < 0.:
                    req = clamp(-self.props.get('time-pos', 0.), 0.)(args)
                else:
                    req = clamp(0., self.props.get('duration', 0.)-self.props.get('time-pos', 0.))(args)
                args = [b'seek', str(req).encode('utf-8'), b'relative', b'default-precise', None]
                self.command(*args)

            case _:
                ...
                # raise DispatchError(f'Unprocessable msg={msg}')


    def terminate(self) -> None:       
        self.handle, handle = None, self.handle
        send(to=self.child, what=Message(sig=Sig.EXIT))
        _mpv.mpv_render_context_free(self.handle)
        raise SystemExit

    def init(self) -> None:
        self.props.register_setter('time-pos', lambda x: 0. if x is None else x)
        self.props.register_setter('duration', lambda x: 0. if x is None else x)
        self.props.register_setter('volume', self.volume_setter)
        self.props.register_setter('player-state', lambda x: int(clamp(0, 4)(x)))
        # self.props.register_setter('playtime-remaining', lambda x: 0. if x is None else x)
        # self.props.register_setter('metadata', lambda x: 0. if x is None else x)

        self.props.register('time-pos', self.parent)
        self.props.register('duration', self.parent)
        self.props.register('volume', self.parent)
        self.props.register('player-state', self.parent)

        self.logger.error(repr(self.props))
        self.props.set('volume', str(VOLUME_DEFAULT))
        # self.props.register('playtime-remaining', self.parent)
        # self.props.register('metadata', self.parent)

        create(MPVEvent, handle=self.handle)
        # send(self.pid, Message(sig=Sig.VOLUME, args=str(VOLUME_DEFAULT)))


    def volume_setter(self, value: str) -> int:
        volume = self.props.get('volume', str(VOLUME_DEFAULT))
        func = lambda x: clamp(0, 100)(x) if x is not None else 0.
        if value.startswith('+') or value.startswith('-'):
            return func(volume + int(value))
        else:
            return func(int(value))
