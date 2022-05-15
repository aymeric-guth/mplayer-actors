import logging
import logging.handlers

from . import config
from . import fix_encoding
from . import mpv_bootstrap as _mpv
from . import actors

LOG_HOST = '127.0.0.1'
LOG_PORT = 8080
LOG_FORMAT = '[%(asctime)s][%(levelname)s][%(filename)s:%(lineno)s][%(funcName)s][%(message)s]'

_logger = logging.getLogger(__name__)
fmt = logging.Formatter(fmt=LOG_FORMAT)
handler = logging.handlers.SocketHandler(LOG_HOST, LOG_PORT)
handler.setFormatter(fmt)
_logger.addHandler(handler)
# _logger.setLevel(logging.INFO)
# _logger.info(dir(_mpv))