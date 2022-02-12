from ctypes import CDLL, c_char, c_char_p, c_void_p, c_int, POINTER, c_double, c_ulonglong, Structure, c_uint64, c_int64, CFUNCTYPE


class MpvHandle(c_void_p):
    pass


class MpvEventID(c_int):
    # Nothing happened. Happens on timeouts or sporadic wakeups.
    MPV_EVENT_NONE = 0
    # Happens when the player quits. The player enters a state where it tries
    # to disconnect all clients. Most requests to the player will fail, and
    # the client should react to this and quit with mpv_destroy() as soon as
    # possible.
    MPV_EVENT_SHUTDOWN = 1
    # See mpv_request_log_messages().
    MPV_EVENT_LOG_MESSAGE = 2
    # Reply to a mpv_get_property_async() request.
    # See also mpv_event and mpv_event_property.
    MPV_EVENT_GET_PROPERTY_REPLY = 3
    # Reply to a mpv_set_property_async() request.
    # (Unlike MPV_EVENT_GET_PROPERTY, mpv_event_property is not used.)
    MPV_EVENT_SET_PROPERTY_REPLY = 4
    # Reply to a mpv_command_async() or mpv_command_node_async() request.
    # See also mpv_event and mpv_event_command.
    MPV_EVENT_COMMAND_REPLY = 5
    # Notification before playback start of a file (before the file is loaded).
    # See also mpv_event and mpv_event_start_file.
    MPV_EVENT_START_FILE = 6
    # Notification after playback end (after the file was unloaded).
    # See also mpv_event and mpv_event_end_file.
    MPV_EVENT_END_FILE = 7
    # Notification when the file has been loaded (headers were read etc.), and
    # decoding starts.
    MPV_EVENT_FILE_LOADED = 8
    # Idle mode was entered. In this mode, no file is played, and the playback
    # core waits for new commands. (The command line player normally quits
    # instead of entering idle mode, unless --idle was specified. If mpv
    # was started with mpv_create(), idle mode is enabled by default.)
    #
    # @deprecated This is equivalent to using mpv_observe_property() on the
    #             "idle-active" property. The event is redundant, and might be
    #             removed in the far future. As a further warning, this event
    #             is not necessarily sent at the right point anymore (at the
    #             start of the program), while the property behaves correctly.
    MPV_EVENT_TRACKS_CHANGED = 9
    MPV_EVENT_TRACK_SWITCHED = 10
    MPV_EVENT_IDLE = 11
    MPV_EVENT_PAUSE = 12
    MPV_EVENT_UNPAUSE = 13
    # Sent every time after a video frame is displayed. Note that currently,
    # this will be sent in lower frequency if there is no video, or playback
    # is paused - but that will be removed in the future, and it will be
    # restricted to video frames only.
    #
    # @deprecated Use mpv_observe_property() with relevant properties instead
    #             (such as "playback-time").
    MPV_EVENT_TICK = 14
    MPV_EVENT_SCRIPT_INPUT_DISPATCH = 15
    # Triggered by the script-message input command. The command uses the
    # first argument of the command as client name (see mpv_client_name()) to
    # dispatch the message, and passes along all arguments starting from the
    # second argument as strings.
    # See also mpv_event and mpv_event_client_message.
    MPV_EVENT_CLIENT_MESSAGE = 16
    # Happens after video changed in some way. This can happen on resolution
    # changes, pixel format changes, or video filter changes. The event is
    # sent after the video filters and the VO are reconfigured. Applications
    # embedding a mpv window should listen to this event in order to resize
    # the window if needed.
    # Note that this event can happen sporadically, and you should check
    # yourself whether the video parameters really changed before doing
    # something expensive.
    MPV_EVENT_VIDEO_RECONFIG = 17
    # Similar to MPV_EVENT_VIDEO_RECONFIG. This is relatively uninteresting,
    # because there is no such thing as audio output embedding.
    MPV_EVENT_AUDIO_RECONFIG = 18
    MPV_EVENT_METADATA_UPDATE = 19
    # Happens when a seek was initiated. Playback stops. Usually it will
    # resume with MPV_EVENT_PLAYBACK_RESTART as soon as the seek is finished.
    MPV_EVENT_SEEK = 20
    # There was a discontinuity of some sort (like a seek), and playback
    # was reinitialized. Usually happens on start of playback and after
    # seeking. The main purpose is allowing the client to detect when a seek
    # request is finished.
    MPV_EVENT_PLAYBACK_RESTART = 21
    # Event sent due to mpv_observe_property().
    # See also mpv_event and mpv_event_property.
    MPV_EVENT_PROPERTY_CHANGE = 22
    MPV_EVENT_CHAPTER_CHANGE = 23
    # Happens if the internal per-mpv_handle ringbuffer overflows, and at
    # least 1 event had to be dropped. This can happen if the client doesn't
    # read the event queue quickly enough with mpv_wait_event(), or if the
    # client makes a very large number of asynchronous calls at once.
    #
    # Event delivery will continue normally once this event was returned
    # (this forces the client to empty the queue completely).
    MPV_EVENT_QUEUE_OVERFLOW = 24
    # Triggered if a hook handler was registered with mpv_hook_add(), and the
    # hook is invoked. If you receive this, you must handle it, and continue
    # the hook with mpv_hook_continue().
    # See also mpv_event and mpv_event_hook.
    MPV_EVENT_HOOK = 25
    # Internal note: adjust INTERNAL_EVENT_BASE when adding new events.
    ANY = (
        MPV_EVENT_SHUTDOWN,
        MPV_EVENT_LOG_MESSAGE,
        MPV_EVENT_GET_PROPERTY_REPLY,
        MPV_EVENT_SET_PROPERTY_REPLY,
        MPV_EVENT_COMMAND_REPLY,
        MPV_EVENT_START_FILE,
        MPV_EVENT_END_FILE,
        MPV_EVENT_FILE_LOADED,
        MPV_EVENT_TRACKS_CHANGED,
        MPV_EVENT_TRACK_SWITCHED,
        MPV_EVENT_IDLE,
        MPV_EVENT_PAUSE,
        MPV_EVENT_UNPAUSE,
        MPV_EVENT_TICK,
        MPV_EVENT_SCRIPT_INPUT_DISPATCH,
        MPV_EVENT_CLIENT_MESSAGE,
        MPV_EVENT_VIDEO_RECONFIG,
        MPV_EVENT_AUDIO_RECONFIG,
        MPV_EVENT_METADATA_UPDATE,
        MPV_EVENT_SEEK,
        MPV_EVENT_PLAYBACK_RESTART,
        MPV_EVENT_PROPERTY_CHANGE,
        MPV_EVENT_CHAPTER_CHANGE,
        MPV_EVENT_QUEUE_OVERFLOW,
        MPV_EVENT_HOOK,
    )

    def __repr__(self):
        return [
            'MPV_EVENT_NONE',
            'MPV_EVENT_SHUTDOWN',
            'MPV_EVENT_LOG_MESSAGE',
            'MPV_EVENT_GET_PROPERTY_REPLY',
            'MPV_EVENT_SET_PROPERTY_REPLY',
            'MPV_EVENT_COMMAND_REPLY',
            'MPV_EVENT_START_FILE',
            'MPV_EVENT_END_FILE',
            'MPV_EVENT_FILE_LOADED',
            'MPV_EVENT_TRACKS_CHANGED',
            'MPV_EVENT_TRACK_SWITCHED',
            'MPV_EVENT_IDLE',
            'MPV_EVENT_PAUSE',
            'MPV_EVENT_UNPAUSE',
            'MPV_EVENT_TICK',
            'MPV_EVENT_SCRIPT_INPUT_DISPATCH',
            'MPV_EVENT_CLIENT_MESSAGE',
            'MPV_EVENT_VIDEO_RECONFIG',
            'MPV_EVENT_AUDIO_RECONFIG',
            'MPV_EVENT_METADATA_UPDATE',
            'MPV_EVENT_SEEK',
            'MPV_EVENT_PLAYBACK_RESTART',
            'MPV_EVENT_PROPERTY_CHANGE',
            'MPV_EVENT_CHAPTER_CHANGE',
            'MPV_EVENT_QUEUE_OVERFLOW',
            'MPV_EVENT_HOOK',
        ][self.value]

    @classmethod
    def from_str(kls, s):
        return getattr(kls, s.upper().replace('-', '_'))


class MpvEvent(Structure):
    _fields_ = [
        ('event_id', MpvEventID),
        ('error', c_int),
        ('reply_userdata', c_ulonglong),
        ('data', c_void_p)
    ]


def lazy_decoder(b):
    try:
        return b.decode('utf-8')
    except UnicodeDecodeError:
        return b
