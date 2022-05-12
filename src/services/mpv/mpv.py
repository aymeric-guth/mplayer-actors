import locale
from ctypes import c_char_p, c_uint64, c_int, pointer, POINTER, c_void_p, sizeof, cast, create_string_buffer
from dataclasses import dataclass
from typing import Any, Optional
import logging

from ...settings import VOLUME_DEFAULT
from ...external import _mpv

from ...utils import clamp
from ..base import Actor, Message, Sig, actor_system, ActorGeneric
from .event_loop import MpvEvent, MPVEvent




class MPV(Actor):
    def __init__(self, pid: int, parent: ActorGeneric, name='', **kwargs) -> None:
        super().__init__(pid, parent, name, **kwargs)
        self._state = 0
        self._volume: int|float
        lc, enc = locale.getlocale(locale.LC_NUMERIC)
        locale.setlocale(locale.LC_NUMERIC, 'C')
        self.handle = _mpv.mpv_create()

        # istr = lambda o: ('yes' if o else 'no') if type(o) is bool else str(o)
        _mpv.mpv_set_option_string(self.handle, b'audio-display', b'no')
        _mpv.mpv_set_option_string(self.handle, b'input-default-bindings', b'yes')
        _mpv.mpv_set_option_string(self.handle, b'input-vo-keyboard', b'yes')
        # mpv_load_config_file(self.handle, str(path).encode('utf-8'))
        _mpv.mpv_initialize(self.handle)

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
        actor_system.send(self.parent, Message(sig=Sig.WATCHER, args={'player-state': self._state}))

    async def command_async(self, *args) -> int:
        args = [c_uint64(0xffff), (c_char_p*len(args))(*args)]
        return _mpv.mpv_command_async(self.handle, *args)

    def command(self, *args) -> int:
        args = (c_char_p*len(args))(*args)
        return _mpv.mpv_command(self.handle, args)

    def set_property(self, name: str, value: list|dict|set|str):
        ename = name.encode('utf-8')
        if isinstance(value, (list, set, dict)):
            _1, _2, _3, pointer = _mpv.make_node_str_list(value)
            _mpv.mpv_set_property(self.handle, ename, _mpv.MpvFormat.NODE, pointer)
        else:            
            _mpv.mpv_set_property_string(self.handle, ename, _mpv.mpv_coax_proptype(value))

    def observe_property(self, name: str) -> None:      
        property_id = hash(name) & 0xffffffffffffffff
        _mpv.mpv_observe_property(self.handle, property_id, name.encode('utf-8'), _mpv.MpvFormat.NODE)

    def dispatch(self, sender: ActorGeneric, msg: Message) -> None:
        match msg:
            case Message(sig=Sig.MPV_EVENT, args=args):
                match args:
                    case MpvEvent(event=event, id=0, name=None, data=None):
                        self.logger.info(f'Processing base event: {args}')
                        match event:
                            case 'playback-restart' | 'start-file' | 'unpause':
                                self.post(Message(sig=Sig.STATE_CHANGE, args=1))
                            case 'idle':
                                self.post(Message(sig=Sig.STATE_CHANGE, args=4))
                            case 'pause':
                                self.post(Message(sig=Sig.STATE_CHANGE, args=2))
                            case 'seek':
                                self.post(Message(sig=Sig.STATE_CHANGE, args=3))

                    case MpvEvent(event=event, id=_id, name=name, data=data):
                        match event:
                            case 'property-change':
                                match name:
                                    case 'volume' | 'playback-time' | 'playtime-remaining' | 'duration' | 'metadata' | 'time-pos':
                                        actor_system.send(self.parent, Message(sig=Sig.WATCHER, args={name: data}))
                                    case 'percent-pos':
                                        ...
                                    case _:
                                        ...

                    case event:
                        ...

            case Message(sig=Sig.INIT, args=args):
                actor_system.create_actor(MPVEvent, handle=self.handle)
                self.observe_property('volume')
                self.observe_property('percent-pos')
                self.observe_property('time-pos')
                self.observe_property('playback-time')
                self.observe_property('playtime-remaining')
                self.observe_property('duration')
                self.observe_property('metadata')
                self.post(Message(sig=Sig.VOLUME, args=VOLUME_DEFAULT))

            case Message(sig=Sig.STATE_CHANGE, args=state):
                self.state = state
                if self.state == 4:
                    self.post(Message(sig=Sig.DONE))

            case Message(sig=Sig.PLAY, args=path):
                args = [b'loadfile', path.encode('utf-8'), b'replace', b'', None]
                self.set_property('pause', 'no')
                self.command(*args)

            case Message(sig=Sig.PLAY_PAUSE, args=None):
                if self.state == 1:
                    self.set_property('pause', 'yes')
                    self.post(Message(sig=Sig.STATE_CHANGE, args=2))
                elif self.state == 2:
                    self.set_property('pause', 'no')
                    self.post(Message(sig=Sig.STATE_CHANGE, args=1))

            case Message(sig=Sig.VOLUME, args=args):
                if args is not None:
                    self.volume = args
                self.set_property('volume', self.volume)
            
            case Message(sig=Sig.VOLUME_INC, args=args):
                self.volume += args
                self.post(Message(sig=Sig.VOLUME))

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

            case Message(sig=Sig.AUDIT, args=None):
                actor_system.send(sender, {'event': 'audit', 'data': self.introspect()})

            case Message(sig=Sig.SIGQUIT):
                self.terminate()

            case _:
                raise SystemExit(f'{msg=}')

    def terminate(self) -> None:
        self.handle, handle = None, self.handle
        # self.event_loop.handle = None
        # self.event_loop.join()
        _mpv.mpv_terminate_destroy(handle)
        raise SystemExit('SIGQUIT')
