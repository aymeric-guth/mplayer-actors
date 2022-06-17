from ctypes import c_uint64, c_char_p, c_int, POINTER, c_double

from mpv import (
    _mpv_set_option_string as mpv_set_option_string, 
    _mpv_initialize as mpv_initialize, 
    _mpv_create as mpv_create, 
    _mpv_create_client as mpv_create_client,
    _mpv_command_async as mpv_command_async,
    _mpv_command as mpv_command,
    # _mpv_wait_event as mpv_wait_event,
    MpvEvent,
    MpvEventID,
    _mpv_set_property as mpv_set_property,
    _mpv_set_property_string as mpv_set_property_string,
    _mpv_terminate_destroy as mpv_terminate_destroy,
    _mpv_coax_proptype as mpv_coax_proptype,
    MpvRenderContext,
    _make_node_str_list as make_node_str_list,
    MpvFormat,
    backend,
    MpvHandle,
    _mpv_event_to_node as mpv_event_to_node,
    _mpv_free_node_contents as mpv_free_node_contents,
    MpvNode,
    _mpv_destroy as mpv_destroy,
    _mpv_render_context_free as mpv_render_context_free
)

def patched_repr(self):
    return ['NONE', 'SHUTDOWN', 'LOG_MESSAGE', 'GET_PROPERTY_REPLY', 'SET_PROPERTY_REPLY', 'COMMAND_REPLY',
            'START_FILE', 'END_FILE', 'FILE_LOADED', 'TRACKS_CHANGED', 'TRACK_SWITCHED', 'IDLE', 'PAUSE', 'UNPAUSE',
            'TICK', 'SCRIPT_INPUT_DISPATCH', 'CLIENT_MESSAGE', 'VIDEO_RECONFIG', 'AUDIO_RECONFIG',
            'METADATA_UPDATE', 'SEEK', 'PLAYBACK_RESTART', 'PROPERTY_CHANGE', 'CHAPTER_CHANGE', 'QUEUE_OVERFLOW', 'HOOK'][self.value]

MpvEventID.__repr__ = patched_repr


mpv_observe_property = getattr(backend, 'mpv_observe_property')
mpv_observe_property.argtypes = [MpvHandle, c_uint64, c_char_p, MpvFormat]
mpv_observe_property.restype = c_int

mpv_wait_event = getattr(backend, 'mpv_wait_event')
mpv_wait_event.argtypes = [MpvHandle, c_double]
mpv_wait_event.restype = POINTER(MpvEvent)
