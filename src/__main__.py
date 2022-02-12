import threading

from .services import Dispatcher


if __name__ == '__main__':
    dispatcher = Dispatcher()
    t = threading.Thread(target=dispatcher.run, daemon=False)
    t.start()
    t.join()
