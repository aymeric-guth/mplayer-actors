from ctypes import c_uint64, c_char_p, c_int

from .mpv.mpv import *

def patched_repr(self):
    return ['NONE', 'SHUTDOWN', 'LOG_MESSAGE', 'GET_PROPERTY_REPLY', 'SET_PROPERTY_REPLY', 'COMMAND_REPLY',
            'START_FILE', 'END_FILE', 'FILE_LOADED', 'TRACKS_CHANGED', 'TRACK_SWITCHED', 'IDLE', 'PAUSE', 'UNPAUSE',
            'TICK', 'SCRIPT_INPUT_DISPATCH', 'CLIENT_MESSAGE', 'VIDEO_RECONFIG', 'AUDIO_RECONFIG',
            'METADATA_UPDATE', 'SEEK', 'PLAYBACK_RESTART', 'PROPERTY_CHANGE', 'CHAPTER_CHANGE', 'QUEUE_OVERFLOW', 'HOOK'][self.value]

MpvEventID.__repr__ = patched_repr


mpv_observe_property = getattr(backend, 'mpv_observe_property')
mpv_observe_property.argtypes = [MpvHandle, c_uint64, c_char_p, MpvFormat]
mpv_observe_property.restype = c_int
