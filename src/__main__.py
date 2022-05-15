import sys
import traceback

from .wcurses import deinit, wrapper
from .external.actors import actor_system
from .services import API, Display, Files, Input, External, MediaDispatcher#, SocketServer



def main():
    actor_system.create_actor(API)
    actor_system.create_actor(Display)
    actor_system.create_actor(Files)
    actor_system.create_actor(Input)
    actor_system.create_actor(External)
    actor_system.create_actor(MediaDispatcher)
    # actor_system.create_actor(SocketServer)

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
