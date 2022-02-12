import threading

from .services import Dispatcher


dispatcher = Dispatcher()
t = threading.Thread(target=dispatcher.run, daemon=False)
t.start()
t.join()