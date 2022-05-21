import sys
import traceback

from .wcurses import deinit, wrapper
from .external.actors import create, actor_system
from .services import API, Display, Files, Input, External, MediaDispatcher#, SocketServer



def main():
    create(API)
    create(Display)
    create(Files)
    create(Input)
    create(External)
    create(MediaDispatcher)
    # create(SocketServer)

    try:
        actor_system.run()
    finally:       
        deinit()
        # traceback.print_exc()
        errtype, errval, exc_traceback = sys.exc_info()
        traceback.print_tb(exc_traceback, file=sys.stdout)
        return 0

    # try:
    #     actor_system.run()
    # finally:
    #     return 0


if __name__ == '__main__':   
    # sys.exit(wrapper(main))
    sys.exit(main())
