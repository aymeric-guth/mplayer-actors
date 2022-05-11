import sys

from .wcurses import deinit, wrapper
from .services import ActorSystem, Dispatcher, API, Display, Files, Input, External, MediaDispatcher, SocketServer



def main():
    actor_system = ActorSystem()
    actor_system.create_actor(Dispatcher)
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
        print(sys.exc_info())
        return 0

    # try:
    #     actor_system.run()
    # finally:
    #     return 0


if __name__ == '__main__':   
    # sys.exit(wrapper(main))
    sys.exit(main())
