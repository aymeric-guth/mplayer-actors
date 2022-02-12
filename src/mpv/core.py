from ctypes import CDLL, c_char, c_char_p, c_void_p, c_int, POINTER, c_double, c_ulonglong, Structure, c_uint64, c_int64, CFUNCTYPE
import sys
import locale

from ._types import MpvHandle, MpvEvent, MpvEventID


lc, enc = locale.getlocale(locale.LC_NUMERIC)
locale.setlocale(locale.LC_NUMERIC, 'C')
sofile = '/opt/local/lib/libmpv.1.109.0.dylib'
backend = CDLL(sofile)
fs_enc = sys.getfilesystemencoding()

mpv_free = backend.mpv_free
mpv_free.argtypes = [c_void_p]
mpv_free.restype = None

mpv_create = backend.mpv_create
mpv_create.restype = MpvHandle

mpv_set_option_string = getattr(backend, 'mpv_set_option_string')
mpv_set_option_string.argtyp = [c_char_p, c_char_p]
mpv_set_option_string.restype = c_int

mpv_initialize = getattr(backend, 'mpv_initialize')
mpv_initialize.argtyp = [MpvHandle]
mpv_initialize.restype = c_int

mpv_create_client = getattr(backend, 'mpv_create_client')
mpv_create_client.argtyp = [MpvHandle, c_char_p]
mpv_create_client.restype = MpvHandle

mpv_wait_event = getattr(backend, 'mpv_wait_event')
mpv_wait_event.argtypes = [MpvHandle, c_double]
mpv_wait_event.restype = POINTER(MpvEvent)

mpv_command_async = getattr(backend, 'mpv_command_async')
mpv_command_async.restype = c_int
mpv_command_async.argtypes = [MpvHandle, c_uint64, POINTER(c_char_p)]

mpv_command = getattr(backend, 'mpv_command')
mpv_command.restype = c_int
mpv_command.argtypes = [MpvHandle, POINTER(c_char_p)]



class MPV:
    def __init__(self, wid: bytes) -> None:
        self.handle = mpv_create()
        # istr = lambda o: ('yes' if o else 'no') if type(o) is bool else str(o)
        # print(k.replace('_', '-').encode('utf-8'), istr(v).encode('utf-8'))
        mpv_set_option_string(self.handle, b'wid', wid)
        mpv_initialize(self.handle)
        self.event_handle = mpv_create_client(self.handle, b'py_event_handler')

    def _event_generator(self):
        while 1:
            event = mpv_wait_event(self.handle, -1).contents
            if event.event_id.value == MpvEventID.MPV_EVENT_NONE:
                raise StopIteration()
            yield event

    def event_runner(self):
        for event in self._event_generator():
            print(f'Got new event: {event!r}')
            print(f'{event.event_id=}')
            print(f'{event.reply_userdata=}')
            print(f'{event.error=}')
            print(f'{event.data=}')

    async def command_async(self, *args) -> int:
        args = [c_uint64(0xffff), (c_char_p*len(args))(*args)]
        return mpv_command_async(self.handle, *args)

    def command(self, *args) -> int:
        args = (c_char_p*len(args))(*args)
        return mpv_command(self.handle, args)
