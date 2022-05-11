import socket
import select
import json
import traceback
from collections import deque, defaultdict
from enum import Enum, auto
from typing import Any, Callable
import threading

from ..base import Actor, Message, Sig, actor_system
from .helpers import BiMap, serialize, deserialize
from .constants import BUFFSIZE


def ctx_handler(fnc, exc) -> Callable:
    def inner(*args, **kwargs) -> None:
        try:
            fnc(*args, **kwargs)
        except exc:
            ...
    return inner


class State(Enum):
    INIT = auto()
    POLL = auto()
    READ_READY = auto()
    WRITE_READY = auto()
    NEW_CONN = auto()
    CLOSE = auto()


class RequestHandler(Actor):
    def __init__(
        self,
        pid: int,
        name='',
        parent: Actor|None=None
    ) -> None:
        super().__init__(pid, name, parent)
        self.child: Actor
        self.subscribed: list[Actor] = []
        self.init_logger(__name__)
        # self.post(self, {'state': 'init'})        

    def dispatch(self, sender, msg) -> None:
        match msg:
            case {'type': 'init'}:
                ...

            case {'type': 'subscribe', 'actor': actor}:
                actor_system.send(actor, {'type': 'subscribe'})
                self.subscribed.append(actor)

            case {'type': 'state', 'args': 'terminate'}:
                for a in self.subscribed:
                    actor_system.send(a, {'type': 'subscribe', 'args': 'unsubscribe'})
                raise SystemExit

            case {'type': 'publish', 'args': args}:
                actor_system.send(self.parent, {'type': 'publish', 'args': args})

            case {'type': 'acknowledge'}:
                ...

            case _:
                ...


class SocketServer(Actor):
    def __init__(self, pid: int, name='',parent: Actor|None=None, **kwargs) -> None:
        super().__init__(pid, name, parent)
        self.childs: dict[int, Actor] = {}

        addr = socket.getaddrinfo('127.0.0.1', 8081)[0][-1]
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.bind(addr)
        except OSError as err:
            self._logger.error(str(err))
            raise SystemExit
        self.sock.setblocking(False)
        self.sock.listen(5)

        self.inputs: list[socket.socket] = [self.sock]
        self.outputs: list[socket.socket] = []
        self.buffer = BiMap()
        # self.lock = threading.Lock()
        threading.Thread(target=self.runner, daemon=True).start()
        self.c = 0
        self.init_logger(__name__)
        self.post(self, {'state': 'init'})

    def runner(self) -> None:
        state = State.INIT
        stack: list[Any] = []

        while 1:
            try:
                state = self.polling_loop(stack, state)
            except Exception as err:
                try:
                    self.sock.close()
                except Exception:
                    ...

                self.logger.error(str(err))
                raise SystemExit
            finally:
                ...

    def polling_loop(self, stack: list[Any], state: State) -> State:
        match state:
            case State.INIT:
                return State.POLL

            case State.POLL:
                match select.select(self.inputs, self.outputs, self.inputs):
                    case [rr, wr, err] if rr and (s := rr[0]) and s is self.sock:
                        self.inputs.remove(s) if s in self.inputs else None
                        stack.append(s)
                        return State.NEW_CONN

                    case [rr, wr, err] if rr and (s := rr[0]):
                        self.inputs.remove(s) if s in self.inputs else None
                        stack.append(s)
                        return State.READ_READY

                    case [rr, wr, err] if wr and (s := wr[0]):
                        self.outputs.remove(s) if s in self.outputs else None
                        stack.append(s)
                        return State.WRITE_READY

                    case [rr, wr, err] if err and (s := err[0]):
                        self.inputs.remove(s) if s in self.inputs else None
                        stack.append(s)
                        return State.CLOSE

                    case _:
                        return State.POLL

            case State.NEW_CONN:
                s = stack.pop()
                conn, addr = s.accept()
                conn.setblocking(False)
                self.inputs.append(conn)
                self.inputs.append(s)
                self.post(self, {'state': 'new-conn', 'args': conn})
                return State.POLL

            case State.READ_READY:
                s = stack.pop()
                d = s.recv(BUFFSIZE)
                if not d:
                    stack.append(s)
                    return State.CLOSE
            
                self.buffer.push(s, d)
                data = self.buffer.get_data(s)
                if data.is_ready():
                    self.outputs.append(s) if s not in self.outputs else None
                    pid = self.buffer.get(s)
                    message = data.deserialize()
                    self.post(self, {'state': 'new-msg', 'pid': pid, 'message': message})
                else:
                    self.inputs.append(s) if s not in self.inputs else None
                return State.POLL

            case State.WRITE_READY:
                s = stack.pop()
                data = self.buffer.get_data(s)
                if data._is_ready():
                    s.send(data._serialize())
                    data.clear()
                    self.inputs.append(s) if s not in self.inputs else None
                else:
                    # si il y a eu un problèmne avec la récupération des données
                    # va poll infiniment, implementer timeout sur data?
                    # passer directement par un future?
                    self.outputs.append(s) if s not in self.outputs else None
                return State.POLL

            case State.CLOSE:
                s = stack.pop()
                self.post(self, {'state': 'terminate', 'args': s})
                self.inputs.remove(s) if s in self.inputs else None
                self.outputs.remove(s) if s in self.outputs else None
                ctx_handler(s.shutdown, OSError)(socket.SHUT_RDWR)
                ctx_handler(s.close, OSError)()
                return State.POLL

            case _:
                return State.POLL

    def dispatch(self, sender: Actor, msg: Message) -> None:
        match msg:
            case {'state': 'init'}:
                ...

            case {'state': 'new-conn', 'args': conn}:
                actor = actor_system.create_actor(RequestHandler)
                self.buffer.set(conn, str(actor.pid))

            case {'state': 'new-msg', 'pid': pid, 'message': message}:
                # actor = self.buffer.get(pid)
                actor_system.send(int(pid), message)

            case {'state': 'terminate', 'args': s}:
                child = self.buffer.get(s)
                self.buffer.clear(s)

            case {'type': 'publish', 'args': args}:
                data = self.buffer.get_data(str(sender))
                data.clear()
                data._data_bis = args

    def __del__(self) -> None:
        try:
            self.sock.close()
        except OSError:
            ...

# pid / actor pid
# socket hash
# data header taille totale des données envoyées



# echo serveur actor async avec la gestion des connexion et les send dans une state machine
# quand un message reçu dépasse la taille du buffer? 
# quand un acteur ne répond pas et que la connexion est active
# passer sur un modele pubsub plutot que request response?
# utiliser le socket comme un transport
# ajouter une option pour souscrire à un acteur
# serialisation / déserialisation des messages