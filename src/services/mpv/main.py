import locale
from threading import Thread
from pathlib import Path
from ctypes import c_char_p, c_uint64
import copy
from dataclasses import dataclass
from typing import Any


from ..base import Actor, Message, Sig, actor_system, sanity_check

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
        self.DEBUG = 0
        self.handle = kwargs.get('handle')
        self.event_handle = _mpv_create_client(self.handle, b'py_event_handler')
        # self.event_thread = Thread(target=self.event_runner, daemon=True).start()

    def run(self) -> None:
        while 1:
            event = _mpv_wait_event(self.handle, -1).contents
            e = copy.deepcopy(event.as_dict())
            e.update({'name': copy.deepcopy(repr(event.event_id))})
            # print(f'Got new event: event={e}')
            actor_system.send(self.parent, Message(sig=Sig.MPV_EVENT, args=MPVEventWrapper(**e)))


class MPV(Actor):
    def __init__(self, pid: int, name='',parent: Actor=None, **kwargs) -> None:
        super().__init__(pid, name, parent)
        self.DEBUG = 1
        self.state = 0
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
        _mpv_set_option_string(self.handle, b'osc', b'yes')
        # mpv_load_config_file(self.handle, str(path).encode('utf-8'))
        # mpv_set_option_string(self.handle, b'vo', b'opengl')
        # mpv_set_option_string(self.handle, b'script-opts', b'osc-layout=box,osc-seekbarstyle=bar,osc-deadzonesize=0,osc-minmousemove=3')

        _mpv_initialize(self.handle)
        self.event_loop = actor_system.create_actor(MPVEvent, handle=self.handle)

    async def command_async(self, *args) -> int:
        args = [c_uint64(0xffff), (c_char_p*len(args))(*args)]
        return _mpv_command_async(self.handle, *args)

    def command(self, *args) -> int:
        args = (c_char_p*len(args))(*args)
        return _mpv_command(self.handle, args)

    def set_property(self, name: str, value: list|dict|set|str):
        ename = name.encode('utf-8')
        if isinstance(value, (list, set, dict)):
            _1, _2, _3, pointer = _make_node_str_list(value)
            _mpv_set_property(self.handle, ename, MpvFormat.NODE, pointer)
        else:            
            _mpv_set_property_string(self.handle, ename, _mpv_coax_proptype(value))

    def terminate(self) -> None:
        self.handle, handle = None, self.handle
        _mpv_terminate_destroy(handle)
        self.event_thread.join()

    @sanity_check
    def dispatch(self, sender: Actor, msg: Message) -> None:
        match msg.sig:
            case Sig.MPV_EVENT:
                # print(f'processing MPV_EVENT: event={msg.args}')
                match msg.args.event_id:
                    case MpvEventID.NONE:
                        ...
                    case MpvEventID.END_FILE:
                        ...
                    case MpvEventID.IDLE:
                        self.post(None, Message(sig=Sig.STATE_CHANGE, args=4))
                    case MpvEventID.PAUSE:
                        self.post(None, Message(sig=Sig.STATE_CHANGE, args=2))
                    case MpvEventID.PLAYBACK_RESTART:
                        self.post(None, Message(sig=Sig.STATE_CHANGE, args=1))
                    case MpvEventID.UNPAUSE:
                        self.post(None, Message(sig=Sig.STATE_CHANGE, args=1))
                    case _:
                        ...

            case Sig.INIT:
                ...

            case Sig.STATE_CHANGE:
                self.state = msg.args
                if self.state == 4:
                    self.post(None, Message(sig=Sig.DONE))

            case Sig.PLAY_ALL:
                path = msg.args
                args = [b'loadfile', path.encode('utf-8'), b'replace', b'', None]
                self.command(*args)

            case Sig.PLAY_PAUSE:
                if self.state == 1:
                    self.set_property('pause', 'yes')
                elif self.state == 2:
                    self.set_property('pause', 'no')

            case Sig.VOLUME:
                self.set_property('volume', msg.args)

            case Sig.STOP:
                args = [b'stop', b'', None]
                self.command(*args)

            case Sig.DONE:
                actor_system.send(self.parent, Message(sig=Sig.DONE))

            case Sig.SIGINT:
                self.terminate()
                actor_system.send(self.parent, Message(sig=Sig.DONE))
                self.parent = None
                raise SystemExit

            case _:
                raise SystemExit(f'{msg=}')
