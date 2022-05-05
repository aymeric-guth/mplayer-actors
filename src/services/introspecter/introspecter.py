import socket
import select
import json
import traceback
from enum import Enum, auto
from typing import Any

from ..base import Actor, Message, Sig, actor_system



class State(Enum):
    INIT = auto()
    POLL = auto()
    READ_READY = auto()
    WRITE_READY = auto()



BUFFSIZE = 4096


def serialize(data: dict[str, Any]) -> bytes:
    return json.dumps(data).encode('utf-8')


def deserialize(data: bytes) -> dict[str, Any]:
    return json.loads(data.decode("utf-8"))


class Socket(Actor):
    def __init__(
        self,
        pid: int,
        name='',
        parent: Actor|None=None,
        conn: socket.socket|None=None,
        data: bytes=b''
    ) -> None:
        super().__init__(pid, name, parent)
        self.LOG = 0
        if conn is None:
            raise SystemExit
        self.conn = conn
        self.data = data

    def run(self) -> None:
        try:
            self.conn.sendall(self.data + b'\n')
            message = {}
        except OSError:
            message = Sig.SIGINT
        finally:
            actor_system.send(self.parent, message)
            raise SystemExit


class ResponseHandler(Actor):
    def __init__(
        self,
        pid: int,
        name='',
        parent: Actor|None=None,
        conn: socket.socket|None=None,
        data: bytes=b''
    ) -> None:
        super().__init__(pid, name, parent)
        self.LOG = 0
        if conn is None:
            raise SystemExit
        self.conn: socket.socket = conn
        self.data = data

    def run(self) -> None:
        try:
            self.conn.sendall(self.data + b'\n')
            # message = {}
        except OSError:
            message = Sig.SIGINT
        finally:
            # actor_system.send(self.parent, message)
            raise SystemExit


class RequestHandler(Actor):
    def __init__(
        self,
        pid: int,
        name='',
        parent: Actor|None=None,
        conn: socket.socket|None=None
    ) -> None:
        super().__init__(pid, name, parent)
        self.LOG = 0
        if conn is None:
            raise SystemExit
        self.conn: socket.socket = conn

    def run(self) -> None:
        try:
            data = self.conn.recv(BUFFSIZE)
            if not data:
                raise OSError
            message = json.loads(data.decode('utf-8'))
        except OSError:
            message = Sig.SIGINT
        finally:
            actor_system.send(self.parent, message)
            raise SystemExit


class SocketHandler(Actor):
    def __init__(
        self,
        pid: int,
        name='',
        parent: Actor|None=None,
        conn: socket.socket|None=None
    ) -> None:
        super().__init__(pid, name, parent)
        self.LOG = 0
        if conn is None:
            raise SystemExit
        self.conn: socket.socket = conn
        self.child: Actor
        self.log_msg(f'Spawning new SocketHandler')
        self.post(self, {'state': 'init'})        

    def log_msg(self, msg: str) ->None:
        actor_system.send('Logger', Message(Sig.PUSH, msg))

    def dispatch(self, sender, msg) -> None:
        match msg:
            case {'state': 'init'}:
                self.child = actor_system.create_actor(RequestHandler, conn=self.conn)

            case {'cmd': 'audit', 'actor': name}:
                actor = actor_system.get_actor(name)
                if actor is not None:
                    actor_system.send(actor, Message(sig=Sig.AUDIT))

            case {'event': 'audit'}:
                actor_system.create_actor(ResponseHandler, conn=self.conn, data=serialize(msg))
                self.post(self, {'state': 'init'})

            case Sig.SIGINT:
                self.terminate()
                raise SystemExit                   

    def terminate(self):
        try:
            self.conn.shutdown(socket.SHUT_RDWR)
            self.conn.close()
        except OSError:
            ...
        finally:
            self.conn = None


class Introspecter(Actor):
    def __init__(self, pid: int, name='',parent: Actor|None=None, **kwargs) -> None:
        super().__init__(pid, name, parent)
        self.LOG = 0
        self.childs: dict[str, Actor] = {}
        port = 8081
        while 1:
            addr = socket.getaddrinfo('127.0.0.1', 8081)[0][-1]
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setblocking(True)
            try:
                self.sock.bind(addr)
            except OSError:
                port += 1
            else:
                break
        self.sock.listen(5)

    def run(self) -> None:
        while 1: 
            rr, wr, err = select.select([self.sock], [], [self.sock])
            for s in rr:
                conn, addr = s.accept()
                actor = actor_system.create_actor(SocketHandler, conn=conn)
            for s in err:
                try:
                    s.shutdown(socket.SHUT_RDWR)
                    s.close()
                except OSError:
                    ...

            # self.childs.update({addr: actor})
            # if addr not in self.childs:                
            #     actor = actor_system.create_actor(SocketHandler, conn=conn)
            #     self.childs.update({addr: actor})
            # else:
            #     ...




    # def run(self) -> None:
    #     stack: list[Any] = []
    #     state = State.INIT
    #     inputs: list[socket.socket] = [self.sock]
    #     outputs: list[socket.socket] = []

    #     while 1: 
    #         match state:
    #             case State.INIT:
    #                 ...
    #             case State.POLL:
    #                 rr, wr, err = select.select(inputs, outputs, inputs, 0.1)
    #                 if rr or wr or err:
    #                     stack.append(rr)
    #                     (s, *_) = rr
    #                 else:
    #                     ...
    #                     connection, client_address = s.accept()
    #         connection.setblocking(0)
    #         inputs.append(connection)
    #         # Give the connection a queue for data we want to send
    #         message_queues[connection] = queue.Queue()
    #                     state = State.READ_READY
    #                     conn, addr = s.accept()
    #                     ...
    #                 if wr:
    #                     ...
    #                 if err:
    #                     ...

    #             case State.READ_READY:
    #                 ...
    #             case State.WRITE_READY:
    #                 ...

            
    #         for s in rr:
    #             conn, addr = s.accept()
    #             actor = actor_system.create_actor(SocketHandler, conn=conn)
    #         for s in err:
    #             try:
    #                 s.shutdown(socket.SHUT_RDWR)
    #                 s.close()
    #             except OSError:
    #                 ...

