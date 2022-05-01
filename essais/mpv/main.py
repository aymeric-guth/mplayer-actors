import locale
from threading import Thread
from pathlib import Path
from ctypes import c_char_p, c_uint64
import copy
from dataclasses import dataclass
from typing import Any

from src.services.base import message
from ...utils import clamp


from ..base import Actor, Message, Sig, actor_system

from .mpv import (
    _mpv_set_option_string, 
    _mpv_initialize, 
    _mpv_create, 
    _mpv_create_client,
    _mpv_command_async,
    _mpv_command,
    _mpv_wait_event,
    MpvEvent,
    MpvEventID,
    _mpv_set_property,
    _mpv_set_property_string,
    _mpv_terminate_destroy,
    _mpv_coax_proptype,
    _mpv_observe_property,
    MpvRenderContext,
    _make_node_str_list,
    MpvFormat
)

@dataclass(frozen=True)
class MPVEventWrapper:
    name: str
    event_id: int
    error: int
    reply_userdata: Any
    event: Any

    def __repr__(self) -> str:
        return f'MPVEventWrapper(name={self.name}, event_id={self.event_id})'


class MPVEvent(Actor):
    def __init__(self, pid: int, name='',parent: Actor=None, **kwargs) -> None:
        super().__init__(pid, name, parent)
        self.LOG = 0
        self.handle = kwargs.get('handle')
        self.event_handle = _mpv_create_client(self.handle, b'py_event_handler')

    def run(self) -> None:
        while 1:
            event = _mpv_wait_event(self.handle, -1).contents
            e = copy.deepcopy(event.as_dict())
            e.update({'name': copy.deepcopy(repr(event.event_id))})
            actor_system.send(self.parent, Message(Sig.MPV_EVENT, MPVEventWrapper(**e)))


class MPV(Actor):
    def __init__(self, pid: int, name='',parent: Actor=None, **kwargs) -> None:
        super().__init__(pid, name, parent, **kwargs)
        self.LOG = 1
        self._state = 0
        self._volume = 100
        lc, enc = locale.getlocale(locale.LC_NUMERIC)
        locale.setlocale(locale.LC_NUMERIC, 'C')

        self.handle = _mpv_create()

        # istr = lambda o: ('yes' if o else 'no') if type(o) is bool else str(o)
        # print(k.replace('_', '-').encode('utf-8'), istr(v).encode('utf-8'))
        wid, *_ = kwargs.get('wid')
        # mpv_set_option_string(self.handle, b'wid', wid)
        _mpv_set_option_string(self.handle, b'audio-display', b'no')
        _mpv_set_option_string(self.handle, b'input-default-bindings', b'yes')
        _mpv_set_option_string(self.handle, b'input-vo-keyboard', b'yes')
        # _mpv_set_option_string(self.handle, b'osc', b'yes')
        # mpv_load_config_file(self.handle, str(path).encode('utf-8'))
        # mpv_set_option_string(self.handle, b'vo', b'opengl')
        # mpv_set_option_string(self.handle, b'script-opts', b'osc-layout=box,osc-seekbarstyle=bar,osc-deadzonesize=0,osc-minmousemove=3')

        _mpv_initialize(self.handle)
        self._event_loop = actor_system.create_actor(MPVEvent, handle=self.handle)
        self.post(self, Message(Sig.INIT))

    @property
    def event_loop(self) -> Any:
        return self._event_loop.event_handle

    @event_loop.setter
    def event_loop(self, value) -> None:
        raise TypeError

    @property
    def volume(self) -> int:
        return self._volume

    @volume.setter
    def volume(self, value: int) -> None:
        self._volume = clamp(0, 100)(value)
        actor_system.send('Display', Message(sig=Sig.MEDIA_META, args={'player-volume': self._volume}))

    @property
    def state(self) -> int:
        return self._state

    @state.setter
    def state(self, value: int) -> None:
        self._state = clamp(0, 4)(value)
        actor_system.send('Display', Message(sig=Sig.MEDIA_META, args={'player-state': self._state}))

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
        # _mpv_terminate_destroy(handle)
        self.event_thread.join()

    def observe_property(self, name: str) -> None:
        _mpv_observe_property(self.event_loop, hash(name) & 0xffffffffffffffff, name.encode('utf-8'), MpvFormat.NODE)

    def dispatch(self, sender: Actor, msg: Message) -> None:
        # actor_system.send('Logger', Message(Sig.PUSH, f'Got new Message: {msg=}'))
        # print(f'Got new Message: {msg=}')
        match msg:
            case Message(sig=Sig.MPV_EVENT, args=args):
                # actor_system.send('Logger', Message(Sig.PUSH, f'processing MPV_EVENT: event={msg.args}'))
                self.log_msg(f'processing MPV_EVENT: event={msg.args}')
                match args.event_id:
                    case MpvEventID.NONE:
                        ...
                    case MpvEventID.SHUTDOWN:
                        ...
                    case MpvEventID.LOG_MESSAGE:
                        ...
                    case MpvEventID.GET_PROPERTY_REPLY:
                        ...
                    case MpvEventID.SET_PROPERTY_REPLY:
                        ...
                    case MpvEventID.COMMAND_REPLY:
                        ...
                    case MpvEventID.START_FILE:
                        self.post(self, Message(sig=Sig.STATE_CHANGE, args=1))
                    case MpvEventID.END_FILE:
                        ...
                    case MpvEventID.FILE_LOADED:
                        ...
                    case MpvEventID.TRACKS_CHANGED:
                        ...
                    case MpvEventID.TRACK_SWITCHED:
                        ...
                    case MpvEventID.IDLE:
                        self.post(self, Message(sig=Sig.STATE_CHANGE, args=4))
                    case MpvEventID.PAUSE:
                        self.post(self, Message(sig=Sig.STATE_CHANGE, args=2))
                    case MpvEventID.UNPAUSE:
                        self.post(self, Message(sig=Sig.STATE_CHANGE, args=1))
                    case MpvEventID.TICK:
                        ...
                    case MpvEventID.SCRIPT_INPUT_DISPATCH:
                        ...
                    case MpvEventID.CLIENT_MESSAGE:
                        ...
                    case MpvEventID.VIDEO_RECONFIG:
                        ...
                    case MpvEventID.AUDIO_RECONFIG:
                        ...
                    case MpvEventID.METADATA_UPDATE:
                        ...
                    case MpvEventID.SEEK:
                        self.post(self, Message(sig=Sig.STATE_CHANGE, args=3))
                    case MpvEventID.PLAYBACK_RESTART:
                        self.post(self, Message(sig=Sig.STATE_CHANGE, args=1))
                    case MpvEventID.PROPERTY_CHANGE:
                        actor_system.send('Logger', Message(Sig.PUSH, f'processing MPV_EVENT: event={msg.args}'))
                    case MpvEventID.CHAPTER_CHANGE:
                        ...
                    case MpvEventID.QUEUE_OVERFLOW:
                        ...
                    case MpvEventID.HOOK:
                        ...

            case Message(sig=Sig.INIT, args=args):
                self.observe_property('volume')
                self.observe_property('stream-end')
                self.observe_property('stream-duration')
                self.observe_property('duration')
                self.post(self, Message(sig=Sig.VOLUME, args=100))
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
                
                # def seek(self, amount, reference="relative", precision="default-precise"):
                #     """Mapped mpv seek command, see man mpv(1)."""
                #     self.command('seek', amount, reference, precision)

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
