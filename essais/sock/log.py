import logging
import logging.handlers


logger = logging.getLogger(__name__)
HOST = '127.0.0.1'
PORT = 8080
LOG_FORMAT = '[%(asctime)s][%(levelname)s][%(filename)s:%(lineno)s][%(funcName)s][%(message)s]'
fmt = logging.Formatter(fmt=LOG_FORMAT)
handler = logging.handlers.SocketHandler(HOST, PORT)
handler.setFormatter(fmt)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


logger.info('lol')