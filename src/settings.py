import os
import subprocess
from pathlib import Path
from enum import Enum, auto

from .external.config import Config


class PlaybackMode(Enum):
    NORMAL = 0
    LOOP_ONE = 1
    LOOP_ALL = 2
    # SHUFFLE = auto()

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}.{self._name_}'
    
    def __str__(self) -> str:
        return self._name_


path = Path(__file__).parent.parent
config = Config(path / ".env")


AUDIO_ROOT = config("AUDIO", cast=str)
VIDEO_ROOT = config("AUDIO", cast=str)

ALLOWED_SHARES = (AUDIO_ROOT, VIDEO_ROOT)
_env = os.getenv("HOME")
if _env is None:
    raise SystemExit
ENV = Path(_env)
ENV_PATH = ENV / '.av-mp'
MOUNT_POINT = str(ENV_PATH / 'mount_point') + '/'
subprocess.run(["mkdir", "-p", MOUNT_POINT])

playlist_file = ENV_PATH / 'playlist.txt'

PATH = [ MOUNT_POINT, ]

ROOT_PREFIX = config('ROOT_PREFIX', cast=str)
ROOT = ( ROOT_PREFIX, )

MUSIC_PATH = ( ROOT_PREFIX, config("AUDIO", cast=str) )
VIDEO_PATH = ( ROOT_PREFIX, config("VIDEO", cast=str) )
MUSIC_TODO = ( ROOT_PREFIX, AUDIO_ROOT, "Music.ToDo", "1st Pass", )


VOLUME_DEFAULT = config("VOLUME_DEFAULT", cast=int, default=100)

AUDIO_LANG = config('AUDIO_LANG', cast=str, default='eng')
SUBTITLES_LANG = config('SUBTITLES_LANG', cast=str, default='eng')


# 0 = Main Disp, 1 = Satellite Disp
DEFAULT_DISPLAY = config('DEFAULT_DISPLAY', cast=int, default=0)
auto_fix_bad_encoding = True


# LOOP_DEFAULT = config("LOOP_DEFAULT", cast=bool, default=False)


USERNAME = config('API_USER', cast=str)
PASSWORD = config('API_PASS', cast=str)

SMB_ADDR = config('SMB_ADDR', cast=str)
SMB_PORT = config('SMB_PORT', cast=int)
SMB_USER = config('SMB_USER', cast=str)
SMB_PASS = config('SMB_PASS', cast=str)

LOG_HOST = config('LOG_HOST', cast=str)
LOG_PORT = config('LOG_PORT', cast=int)
# logs:
#     nom_actor (class, pid, )
#     namespace fichier
#     ligne
#     loglevel
LOG_FORMAT = config('LOG_FORMAT', cast=str, default='[%(asctime)s][%(levelname)s][%(actor)s][%(name)s:%(lineno)s][%(message)s]')
_extensions_audio = {
    '.mp3', 
    '.flac', 
    '.m4a', 
    '.ogg', 
    '.wav', 
    '.alac', 
    '.aac', 
    '.aif', 
    '.aiff',
    '.ape',
    '.opus'
}
_extensions_mod = {
    '.mod', 
    '.s3m',
    '.xm',
    '.it',
    '.669',
    '.amt',# both of them?
    '.ams',
    '.dbm',
    '.dmf',
    '.dsm',
    '.far',
    '.mdl',
    '.med',
    '.mtm',
    '.okt',
    '.ptm',
    '.stm',
    '.ult',
    '.umx',
    '.mt2',
    '.psm',
}
_extensions_openmpt = {
    '.mptm',
    '.mod',
    '.s3m',
    '.xm',
    '.it',
    '.669',
    '.amf',
    '.ams',
    '.c67',
    '.dbm',
    '.digi',
    '.dmf',
    '.dsm',
    '.dsym',
    '.dtm',
    '.far',
    '.fmt',
    '.imf',
    '.ice',
    '.j2b',
    '.m15',
    '.mdl',
    '.med',
    '.mms',
    '.mt2',
    '.mtm',
    '.mus',
    '.nst',
    '.okt',
    '.plm',
    '.psm',
    '.pt36',
    '.ptm',
    '.sfx',
    '.sfx2',
    '.st26',
    '.stk',
    '.stm',
    '.stx',
    '.stp',
    '.symmod',
    '.ult',
    '.wow',
    '.gdm',
    '.mo3',
    '.oxm',
    '.umx',
    '.xpk',
    '.ppm',
    '.mmcmp'
}
_extensions_gme = {
    '.vgm',
    '.gym',
    '.spc',
    '.sap',
    '.nsfe',
    '.nsf',
    '.ay',
    '.gbs',
    '.hes',
    '.kss'
}
extensions_audio = _extensions_audio | _extensions_mod | _extensions_gme
extensions_video: set[str] = set()

extensions_all = extensions_audio | extensions_video
extensions_mpv = extensions_audio | extensions_video
extensions_all_regex = '|'.join(extensions_all)
