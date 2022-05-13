from enum import Enum, auto


class Sig(Enum):
    INIT = auto()
    SIGINT = auto()
    SIGKILL = auto()
    SIGQUIT = auto()
    LOGIN = auto()
    LOGIN_SUCCESS = auto()
    LOGIN_FAILURE = auto()
    NETWORK_FAILURE = auto()
    EXT_SET = auto()
    PATH_SET = auto()
    FILES_GET = auto()
    PARSE = auto()
    CWD_GET = auto()
    NONE = auto()
    ERROR = auto()
    FILES_REINDEX = auto()
    PLAY = auto()
    PLAY_ALL = auto()
    STOP = auto()
    DONE = auto()
    PLAY_PAUSE = auto()
    NEXT = auto()
    PREVIOUS = auto()
    STATE_CHANGE = auto()
    VOLUME = auto()
    MPV_EVENT = auto()
    DISPATCH_ERROR = auto()
    PING = auto()
    PONG = auto()
    OPEN = auto()
    SEEK = auto()
    VOLUME_INC = auto()
    SEARCH = auto()
    SEARCH_ALL = auto()
    POPUP = auto()
    LOGS = auto()
    PUSH = auto()
    GET = auto()
    POISON = auto()
    DRAW_SCREEN = auto()
    PROMPT = auto()
    MEDIA_META = auto()
    RESIZE = auto()
    FILES_NEW = auto()
    PLAYBACK_OVERLAY = auto()
    SMB_MOUNT = auto()
    SMB_PING = auto()
    TEST = auto()
    VOLUME_CHANGE = auto()
    PLAYBACK_CHANGE = auto()
    POS_CHANGE = auto()
    LOOP = auto()
    PBTIME_CHANGE = auto()
    PBREM_CHANGE = auto()
    META = auto()
    DURATION_CHANGE = auto()
    WATCHER = auto()
    AUDIT = auto()
    DRAW_PLAYBACK = auto()
    GET_CACHE = auto()
    SET_CACHE = auto()
    EXT_SUCCESS = auto()
    PATH_REFRESH = auto()
    HOOK = auto()
    JUMP = auto()

# 'type': 'event'
# 'type': 'error'
# 'type': 'cmd'
# 'type': 'request'
# 'type': 'response'