import sys
import traceback
import time

from .external.actors import create, ActorSystem, Sig, Message, send, Send
from .services import API, Display, Files, Input, External, MediaDispatcher, Dummy#, SocketServer


def main():
    create(API)
    create(Display)
    create(Files)
    create(Input)
    create(External)
    create(MediaDispatcher)
    # create(SocketServer)

    try:
        ActorSystem().run()
    finally:
        ActorSystem().terminate()
        traceback.print_exc()
        # errtype, errval, exc_traceback = sys.exc_info()
        # traceback.print_tb(exc_traceback, file=sys.stdout)
        return 0


if __name__ == '__main__':
    sys.exit(main())
