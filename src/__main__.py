import sys
import traceback

from .wcurses import deinit, wrapper
from .external.actors import create, ActorSystem, Sig, Message, send
from .services import API, Display, Files, Input, External, MediaDispatcher, Dummy#, SocketServer


def main():
    create(API)
    create(Display)
    create(Files)
    create(Input)
    create(External)
    create(MediaDispatcher)
    # create(SocketServer)

    # ActorSystem().post(Message(sig=Sig.INIT))
    # send('ActorSystem', Message(sig=Sig.INIT))
    send('API', Message(sig=Sig.INIT))
    send('Display', Message(sig=Sig.INIT))
    send('Files', Message(sig=Sig.INIT))
    send('Input', Message(sig=Sig.INIT))
    send('External', Message(sig=Sig.INIT))
    send('MediaDispatcher', Message(sig=Sig.INIT))

    try:
        ActorSystem().run()
    finally:       
        deinit()
        traceback.print_exc()
        errtype, errval, exc_traceback = sys.exc_info()
        traceback.print_tb(exc_traceback, file=sys.stdout)
        return 0


if __name__ == '__main__':
    sys.exit(main())
