from typing import Any
import dataclasses
from ctypes import cast, sizeof, POINTER, create_string_buffer, pointer
import threading
import copy
import logging

from ...external import _mpv
from ...external.actors import ActorIO, send, Message, Sig, DispatchError


@dataclasses.dataclass(frozen=True)
class MpvEvent:
    event: str
    id: int
    name: str
    data: Any

    def __repr__(self) -> str:
        return f'MpvEvent(event={self.event}, id={self.id}, name={self.name}, data={self.data})'


def handler(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as err:
            args[0].logger.error(f'{err=}')
    return inner
class MPVEvent(ActorIO):
    def __init__(self, pid: int, parent: int, name='', handle: Any=None, **kwargs) -> None:
        super().__init__(pid, parent, name, **kwargs)
        if handle is None:
            raise SystemExit
        self.run = handler(self.run)
        self.handle = handle
        self.event_handle = _mpv.mpv_create_client(self.handle, b'py_event_handler')
        self._t = threading.Thread(target=self._run, daemon=True)
        self._t.start()
        self.log_lvl = logging.ERROR

    def _run(self) -> None:
        while 1:
            (sender, msg) = self._mq.get()
            self.logger.log(sender=sender, receiver=repr(self), msg=msg)
            try:
                self.dispatch(sender, msg)
            except Exception as err:
                self.logger.error(f'Got err={err}')
            finally:
                self._mq.task_done()

    def run(self) -> None:
        while 1:
            # self.logger.error(f'Polling event loop')
            mpv_event = _mpv.mpv_wait_event(self.handle, -1).contents
            # self.logger.error(f'Got new MPVEvent: {mpv_event}')
            out = cast(create_string_buffer(sizeof(_mpv.MpvNode)), POINTER(_mpv.MpvNode))
            _mpv.mpv_event_to_node(out, pointer(mpv_event))
            
            # try:
            rv = out.contents.node_value(decoder=lambda b: b.decode('utf-8'))
            # id_1 = mpv_event.reply_userdata
            # id_2 = rv.get('id'),
            event = MpvEvent(
                event=rv.get('event'),
                id=mpv_event.reply_userdata,
                name=rv.get('name'),
                data=rv.get('data')
            )
            # self.logger.error(f'event={event}')
            send(self.parent, Message(sig=Sig.MPV_EVENT, args=copy.deepcopy(event)))
            _mpv.mpv_free_node_contents(out)
            self.logger.info(f'event={event}')
            # time.sleep(1)
            # except Exception as err:
            #     self.logger.error(str(err))
            #     self.logger.error(bytes(out))

    def dispatch(self, sender: int, msg: Any) -> None:
        try:
            super().dispatch(sender, msg)
        except DispatchError:
            return
            
    def terminate(self) -> None:
        send(to='ActorSystem', what=Message(sig=Sig.EXIT))
        _mpv.mpv_destroy(self.handle)
        # _mpv.mpv_render_context_free(self.handle)
        self.handle, handle = None, self.handle
        if self._t:
            self._t.join()
        raise SystemExit
