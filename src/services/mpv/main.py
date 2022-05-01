import locale
from threading import Thread
from pathlib import Path
from ctypes import c_char_p, c_uint64, c_int, pointer, POINTER, c_void_p, sizeof, cast, create_string_buffer
import copy
from dataclasses import dataclass
from typing import Any

from src.services.base import message
from ...utils import clamp
from ..settings import VOLUME_DEFAULT


from ..base import Actor, Message, Sig, actor_system

from .mpv import (
    _mpv_set_option_string, 
    _mpv_initialize, 
    _mpv_create, 
    _mpv_create_client,
    _mpv_command_async,
    _mpv_command,
    _mpv_wait_event,
    # MpvEvent,
    MpvEventID,
    _mpv_set_property,
    _mpv_set_property_string,
    _mpv_terminate_destroy,
    _mpv_coax_proptype,
    MpvRenderContext,
    _make_node_str_list,
    MpvFormat,
    backend,
    MpvHandle,
    _mpv_event_to_node,
    _mpv_free_node_contents,
    MpvNode
)

mpv_observe_property = getattr(backend, 'mpv_observe_property')
mpv_observe_property.argtypes = [MpvHandle, c_uint64, c_char_p, MpvFormat]
mpv_observe_property.restype = c_int



@dataclass(frozen=True)
class MPVEventWrapper:
    name: str
    event_id: int
    error: int
    reply_userdata: Any
    event: Any

    def __repr__(self) -> str:
        return f'MPVEventWrapper(name={self.name}, event_id={self.event_id}, error={self.error}, reply_userdata={self.reply_userdata}, event={self.event})'


@dataclass(frozen=True)
class MpvEvent:
    event: str
    id: int
    name: str
    data: Any

    def __repr__(self) -> str:
        return f'MpvEvent(event={self.event}, id={self.id}, name={self.name}, data={self.data})'


class MPVEvent(Actor):
    def __init__(self, pid: int, name='',parent: Actor|None=None, **kwargs) -> None:
        super().__init__(pid, name, parent)
        self.LOG = 1
        self.handle = kwargs.get('handle')
        self.event_handle = _mpv_create_client(self.handle, b'py_event_handler')

    def run(self) -> None:
        while 1:
            mpv_event = _mpv_wait_event(self.handle, -1).contents            
            out = cast(create_string_buffer(sizeof(MpvNode)), POINTER(MpvNode))
            _mpv_event_to_node(out, pointer(mpv_event))
            rv = out.contents.node_value(decoder=lambda b: b.decode('utf-8'))
            event = MpvEvent(
                event=rv.get('event'),
                id=mpv_event.reply_userdata,
                name=rv.get('name'),
                data=rv.get('data')
            )
            _mpv_free_node_contents(out)
            actor_system.send(self.parent, Message(sig=Sig.MPV_EVENT, args=event))


class MPV(Actor):
    def __init__(self, pid: int, name='',parent: Actor|None=None, **kwargs) -> None:
        super().__init__(pid, name, parent, **kwargs)
        self.LOG = 0
        self._state = 0
        self._volume: int|float
        lc, enc = locale.getlocale(locale.LC_NUMERIC)
        locale.setlocale(locale.LC_NUMERIC, 'C')
        self.handle = _mpv_create()

        # istr = lambda o: ('yes' if o else 'no') if type(o) is bool else str(o)
        _mpv_set_option_string(self.handle, b'audio-display', b'no')
        _mpv_set_option_string(self.handle, b'input-default-bindings', b'yes')
        _mpv_set_option_string(self.handle, b'input-vo-keyboard', b'yes')
        # mpv_load_config_file(self.handle, str(path).encode('utf-8'))

        _mpv_initialize(self.handle)
        self._event_loop = actor_system.create_actor(MPVEvent, handle=self.handle)
        self.observed_properties: dict[int, Sig] = {}
        self.post(self, Message(Sig.INIT))

    def log_msg(self, msg: str) ->None:
        actor_system.send('Logger', Message(Sig.PUSH, msg))

    @property
    def event_loop(self) -> Any:
        return self._event_loop.event_handle

    @event_loop.setter
    def event_loop(self, value) -> None:
        raise TypeError

    @property
    def volume(self) -> int|float:
        return self._volume

    @volume.setter
    def volume(self, value: int|float) -> None:
        self._volume = clamp(0, 100)(value)

    @property
    def state(self) -> int:
        return self._state

    @state.setter
    def state(self, value: int) -> None:
        self._state = int(clamp(0, 4)(value))
        actor_system.send(self.parent, Message(sig=Sig.PLAYBACK_CHANGE, args=self._state))

    async def command_async(self, *args) -> int:
        args = [c_uint64(0xffff), (c_char_p*len(args))(*args)]
        return _mpv_command_async(self.handle, *args)

    def command(self, *args) -> int:
        args = (c_char_p*len(args))(*args)
        return _mpv_command(self.handle, args)

        # args = [name.encode('utf-8')] + [ (arg if type(arg) is bytes else str(arg).encode('utf-8'))
        #         for arg in args if arg is not None ] + [None]
        # _mpv_command(self.handle, (c_char_p*len(args))(*args))

    def set_property(self, name: str, value: list|dict|set|str):
        ename = name.encode('utf-8')
        if isinstance(value, (list, set, dict)):
            _1, _2, _3, pointer = _make_node_str_list(value)
            _mpv_set_property(self.handle, ename, MpvFormat.NODE, pointer)
        else:            
            _mpv_set_property_string(self.handle, ename, _mpv_coax_proptype(value))

    def terminate(self) -> None:
        self.handle, handle = None, self.handle
        self.event_loop.handle = None
        self.event_loop.join()
        _mpv_terminate_destroy(handle)

    def observe_property(self, name: str) -> None:      
        property_id = hash(name) & 0xffffffffffffffff
        if property_id not in self.observed_properties:
            mpv_observe_property(self.handle, property_id, name.encode('utf-8'), MpvFormat.NODE)
            # self.observed_properties.update({property_id: sig})

    def dispatch(self, sender: Actor, msg: Message) -> None:
        match msg:
            case Message(sig=Sig.MPV_EVENT, args=args):
                match args:
                    case MpvEvent(event=event, id=0, name=None, data=None):
                        self.log_msg(f'Processing base event: {args}')
                        match event:
                            case 'playback-restart' | 'start-file':
                                self.post(self, Message(sig=Sig.STATE_CHANGE, args=1))
                            case 'idle':
                                self.post(self, Message(sig=Sig.STATE_CHANGE, args=4))
                            case 'pause':
                                self.post(self, Message(sig=Sig.STATE_CHANGE, args=2))
                            case 'unpause':
                                self.post(self, Message(sig=Sig.STATE_CHANGE, args=1))
                            case 'seek':
                                self.post(self, Message(sig=Sig.STATE_CHANGE, args=3))

                    case MpvEvent(event=event, id=_id, name=name, data=data):
                        self.log_msg(f'Processing propery-change event: {args}')
                        match event:
                            case 'property-change':
                                match name:
                                    case 'volume':
                                        actor_system.send(self.parent, Message(sig=Sig.VOLUME_CHANGE, args=data))
                                    case 'percent-pos':
                                        actor_system.send(self.parent, Message(sig=Sig.POS_CHANGE, args=data))
                                # sig = self.observed_properties.get(args.id)
                                # self.post(self, Message())

                    case event:
                        self.log_msg(f'Unkown event: {args}')


            case Message(sig=Sig.INIT, args=args):
                self.observe_property('volume')
                self.observe_property('percent-pos')
                
                # self.observe_property('stream-end')
                # self.observe_property('stream-duration')
                # self.observe_property('duration')
                self.post(self, Message(sig=Sig.VOLUME, args=VOLUME_DEFAULT))
                # percent-pos
                # time-pos
                # time-start
                # time-remaining
                # ao-volume

            case Message(sig=Sig.STATE_CHANGE, args=state):
                self.state = state
                if self.state == 4:
                    self.post(self, Message(sig=Sig.DONE))

            case Message(sig=Sig.PLAY, args=path):
                args = [b'loadfile', path.encode('utf-8'), b'replace', b'', None]
                self.set_property('pause', 'no')
                self.command(*args)

            case Message(sig=Sig.PLAY_PAUSE, args=None):
                if self.state == 1:
                    self.set_property('pause', 'yes')
                    self.post(self, Message(sig=Sig.STATE_CHANGE, args=2))
                elif self.state == 2:
                    self.set_property('pause', 'no')
                    self.post(self, Message(sig=Sig.STATE_CHANGE, args=1))

            case Message(sig=Sig.VOLUME, args=args):
                if args is not None:
                    self.volume = args
                self.set_property('volume', self.volume)
            
            case Message(sig=Sig.VOLUME_INC, args=args):
                self.volume += args
                actor_system.send(self, Message(sig=Sig.VOLUME))

            case Message(sig=Sig.STOP, args=None):
                args = [b'stop', b'', None]
                self.command(*args)

            case Message(sig=Sig.SEEK, args=args):
                p = str(args).encode('utf-8')
                args = [b'seek', p, b'relative', b'default-precise', None]
                self.command(*args)

            case Message(sig=Sig.DONE, args=args) as msg:
                actor_system.send(self.parent, msg)

            case Message(sig=Sig.SIGINT, args=None):
                self.terminate()
                actor_system.send(self.parent, Message(sig=Sig.DONE))
                self.parent = None
                raise SystemExit

            case Message(sig=Sig.POISON, args=None):
                self.terminate()
                raise Exception

            case _:
                raise SystemExit(f'{msg=}')
