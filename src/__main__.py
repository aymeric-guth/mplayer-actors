import sys

from .services import ActorSystem, Dispatcher, API, Display, Files, Input, External, Logger, MediaDispatcher
from .wcurses import deinit



def main():
    actor_system = ActorSystem()
    logger = actor_system.create_actor(Logger)
    dispatcher = actor_system.create_actor(Dispatcher)
    api = actor_system.create_actor(API)
    display = actor_system.create_actor(Display)
    files = actor_system.create_actor(Files)
    input = actor_system.create_actor(Input)
    media_dispatcher = actor_system.create_actor(MediaDispatcher)
    external = actor_system.create_actor(External)
    actor_system.run()


if __name__ == '__main__':
    try:
        sys.exit(main())
    finally:
        deinit()

# xy matrix mapping 
# pour la représentation entre sender receiver et message
