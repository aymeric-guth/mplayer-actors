import sys
import locale
from threading import Thread
import asyncio

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from .core import MPV


class Test(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.container = QWidget(self)
        self.setCentralWidget(self.container)
        self.container.setAttribute(Qt.WA_DontCreateNativeAncestors)
        self.container.setAttribute(Qt.WA_NativeWindow)

    @property
    def wid(self):
        return str(int(self.container.winId())).encode('utf-8')


if __name__ == '__main__':
    app = QApplication(sys.argv)

    import locale
    locale.setlocale(locale.LC_NUMERIC, 'C')

    win = Test()
    win.show()
    mpv = MPV(wid=win.wid)

    t = Thread(target=mpv.event_runner, daemon=True)
    t.start()

    args = [b'loadfile', b'/Users/yul/Desktop/Network/mplayer_reborn/src/mpv/Cowboy Bebop - 01 [bdrip.vostfr.1080p.h265.dd5.1.aac]-Yomi.mkv', b'replace', b'', None]
    
    mpv.command(*args)
    # asyncio.run(mpv.command_async(*args))

    sys.exit(app.exec_())


# __init__
# création core object
# initialisation + fichier config
# création client

# event loop (mpv_wait_event) bloquant

# methodes pour communiquer avec le core
# certaines bloquantes
# equivalents async -> génération d'un id et réponse postée sur l'event loop
