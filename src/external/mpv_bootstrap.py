from ctypes import c_uint64, c_char_p, c_int, POINTER, c_double

from mpv import (
    _mpv_set_option_string as mpv_set_option_string,  # type: ignore
    _mpv_initialize as mpv_initialize,  # type: ignore
    _mpv_create as mpv_create,  # type: ignore
    _mpv_create_client as mpv_create_client,  # type: ignore
    _mpv_command_async as mpv_command_async,  # type: ignore
    _mpv_command as mpv_command,  # type: ignore
    # _mpv_wait_event as mpv_wait_event,
    MpvEvent,
    MpvEventID,
    _mpv_set_property as mpv_set_property,  # type: ignore
    _mpv_set_property_string as mpv_set_property_string,  # type: ignore
    _mpv_terminate_destroy as mpv_terminate_destroy,  # type: ignore
    _mpv_coax_proptype as mpv_coax_proptype,  # type: ignore
    MpvRenderContext,
    _make_node_str_list as make_node_str_list,  # type: ignore
    MpvFormat,  # type: ignore
    backend,
    MpvHandle,
    _mpv_event_to_node as mpv_event_to_node,  # type: ignore
    _mpv_free_node_contents as mpv_free_node_contents,  # type: ignore
    MpvNode,
    _mpv_destroy as mpv_destroy,  # type: ignore
    _mpv_render_context_free as mpv_render_context_free,  # type: ignore
)


def patched_repr(self):
    return [
        "NONE",
        "SHUTDOWN",
        "LOG_MESSAGE",
        "GET_PROPERTY_REPLY",
        "SET_PROPERTY_REPLY",
        "COMMAND_REPLY",
        "START_FILE",
        "END_FILE",
        "FILE_LOADED",
        "TRACKS_CHANGED",
        "TRACK_SWITCHED",
        "IDLE",
        "PAUSE",
        "UNPAUSE",
        "TICK",
        "SCRIPT_INPUT_DISPATCH",
        "CLIENT_MESSAGE",
        "VIDEO_RECONFIG",
        "AUDIO_RECONFIG",
        "METADATA_UPDATE",
        "SEEK",
        "PLAYBACK_RESTART",
        "PROPERTY_CHANGE",
        "CHAPTER_CHANGE",
        "QUEUE_OVERFLOW",
        "HOOK",
    ][self.value]


MpvEventID.__repr__ = patched_repr


mpv_observe_property = getattr(backend, "mpv_observe_property")
mpv_observe_property.argtypes = [MpvHandle, c_uint64, c_char_p, MpvFormat]
mpv_observe_property.restype = c_int

mpv_wait_event = getattr(backend, "mpv_wait_event")
mpv_wait_event.argtypes = [MpvHandle, c_double]
