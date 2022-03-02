BASE_URL = "https://ars-virtualis.org/api"
BASE_NAS = f"{BASE_URL}/nas"
BASE_AUTH = f"{BASE_URL}/authentication"


class AUTH:
    LOGIN = f'{BASE_AUTH}/login'
    REGISTER = f'{BASE_AUTH}/register'


class NAS(object):
    FILES = f"{BASE_NAS}/files"
    PLAYBACK = f"{BASE_NAS}/playback"
    EXT = f"{BASE_NAS}/extensions"
