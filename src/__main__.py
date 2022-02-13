from src.services import display, media_dispatcher
from src.services.base.message import Message
from .services import Message, Sig, Actor

from .services import ActorSystem, Dispatcher, API, Display, Files, Input, MediaDispatcher


if __name__ == '__main__':
    actor_system = ActorSystem()
    dispatcher = actor_system.create_actor(Dispatcher)
    api = actor_system.create_actor(API)
    display = actor_system.create_actor(Display)
    files = actor_system.create_actor(Files)
    input = actor_system.create_actor(Input)
    media_dispatcher = actor_system.create_actor(MediaDispatcher)
    actor_system.send(dispatcher, Message(Sig.INIT))

    while 1:
        ...

# xy matrix mapping 
# pour la représentation entre sender receiver et message
