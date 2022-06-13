import os
import subprocess
from pathlib import Path

from dotenv import load_dotenv

# from .external.config import Config


def getenv(key: str, cast: type=str) -> str:
    val = os.getenv(key)
    if val is None:
        raise SystemExit
    return cast(val)


env_file = Path(__file__).parent.parent / ".env"
load_dotenv(env_file)


MOUNT_POINT = getenv('MOUNT_POINT') + '/'
ENV = Path(getenv('HOME'))
ENV_PATH = ENV / '.av-mp'
CACHE_PATH = ENV_PATH / '.cache'
CONFIG_PATH = ENV_PATH / '.config'
subprocess.run(["mkdir", "-p", ENV_PATH])


ROOT_PREFIX = 'shared'
ROOT = ( ROOT_PREFIX, 'Audio')


USERNAME = getenv('API_USER')
PASSWORD = getenv('API_PASS')

SMB_ADDR = getenv('SMB_ADDR')
SMB_PORT = getenv('SMB_PORT', cast=int)
SMB_USER = getenv('SMB_USER')
SMB_PASS = getenv('SMB_PASS')

LOG_HOST = getenv('LOG_HOST')
LOG_PORT = getenv('LOG_PORT', cast=int)

LOG_FORMAT = '[%(asctime)s][%(levelname)s][%(actor)s][%(name)s:%(lineno)s][%(message)s]'
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
