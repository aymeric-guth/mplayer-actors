import socket
import select
import json
import traceback
from collections import deque, defaultdict
from enum import Enum, auto
from typing import Any, Callable
import queue


from ..base import Actor, Message, Sig, actor_system


BUFFSIZE = 4096

class State(Enum):
    INIT = auto()
    POLL = auto()
    NEW_CONNECTION = auto()
    READ_READY = auto()
    WRITE_READY = auto()
    

def serialize(data: dict[str, Any]) -> bytes:
    return json.dumps(data).encode('utf-8')


def deserialize(data: bytes) -> dict[str, Any]:
    return json.loads(data.decode("utf-8"))


class BiMap:
    def __init__(self):
        self._d = {}

    def get(self, value: Any) -> Any:
        return self._d.__getitem__(value)

    def set(self, key: Any, value: Any) -> None:
        if key in self._d or value in self._d:
            raise KeyError
        return self._d.__setitem__(key, value) or self._d.__setitem__(value, key)

    def __getitem__(self, __k: Any) -> Any:
        return self.get(__k)

    def __setitem__(self, __k: Any, __v: Any) -> None:
        return self.set(__k, __v)


class RequestHandler(Actor):
    def __init__(
        self,
        pid: int,
        name='',
        parent: Actor|None=None,
        request: bytes=b''
    ) -> None:
        super().__init__(pid, name, parent)
        self.LOG = 0
        if not request:
            raise SystemExit

        try:
            message = deserialize(request)
        except Exception:
            raise SystemExit
        self.__hash__: Callable[[RequestHandler], str] = lambda self: str(hash(self.pid))
        self.post(self, {'state': 'init', 'args': message})

    def dispatch(self, sender: Actor, msg: Message) -> None:
        match msg:
            case {'state': 'init', 'args': args}:
                (actor, message) = args
                actor_system.send(actor, message)

            case {'state': 'response', 'message': response}:
                actor_system.send(self.parent, response)


class Introspecter(Actor):
    def __init__(self, pid: int, name='',parent: Actor|None=None, **kwargs) -> None:
        super().__init__(pid, name, parent)
        self.LOG = 1
        self.childs: dict[str, Actor] = {}
        port = 8081

        addr = socket.getaddrinfo('127.0.0.1', 8081)[0][-1]
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setblocking(True)
        try:
            self.sock.bind(addr)
        except OSError:
            raise SystemExit
        self.sock.listen(5)
        
        self.inputs: deque[socket.socket] = deque([self.sock])
        # self.inputs: list[socket.socket] = [self.sock]
        self.outputs: deque[socket.socket] = deque()
        # self.outputs: list[socket.socket] = []
        
        self.sock_map: dict[socket.socket, dict[str, Any]] = {}
        self.rid_map: dict[int, socket.socket] = {}
        self.buff: dict[socket.socket, queue.Queue] = {}
        actor_system.send('Logger', Message(Sig.PUSH, f'actor={self!r} listening on port={port}'))
        self.post(self, {'state': 'poll'})
        self._buff: BiMap[Actor|socket.socket, Actor|socket.socket] = BiMap()

    def run(self) -> None:
        while 1:
            (sender, msg) = self.mq.get()
            if self.LOG == 1:
                self.logger(sender, msg)
            try:
                self.dispatch(sender, msg)
            except Exception as err:
                self.terminate()
                raise SystemExit
            else:
                self.mq.task_done()

    def logger(self, sender: Actor, msg: Message) -> None:
        s = actor_system.get_actor(sender)
        actor_system.send('Logger', Message(Sig.PUSH, f'sender={s!r} receiver={self!r} msg={msg!r}'))

    def dispatch(self, sender: Actor, msg: Message) -> None:
        match msg:
            case {'state': 'poll'}:
                # [*self.inputs, *self.outputs]
                rr, wr, err = select.select(self.inputs, self.outputs, [])
                if rr:
                    s = self.inputs.popleft()
                    state = 'new-conn' if s is self.sock else 'read-ready'
                    self.post(self, {'state': state, 'args': s})
                elif wr:
                    s = self.outputs.popleft()
                    self.post(self, {'state': 'write-ready', 'args': s})
                elif err:
                    ...
                    # s = self.inputs.popleft()
                    # self.post(self, {'state': 'error', 'args': s})
                else:
                    self.post(self, {'state': 'poll'})

            case {'state': 'response', '': '', 'message': response}:
                # socket -> pid | pid -> socket
                conn = self._buff[sender.pid]
                self._buff[sender.pid].append(response.copy())
                
                ...

            case {'state': 'new-conn', 'args': s}:
                conn, addr = s.accept()
                conn.setblocking(0)
                self.inputs.append(conn)
                self.inputs.append(s)
                self.post(self, {'state': 'poll'})

            case {'state': 'read-ready', 'args': s}:
                data = s.recv(BUFFSIZE)
                if data:
                    self.outputs.append(s) if s not in self.outputs else None
                    rid = actor_system.get_rid()
                    self.rid_map.update({rid: s})
                    message = deserialize(data)
                    if message is None:
                        ...
                    else:
                        message.update({'rid': rid})
                        self.post(self, message)
                else:
                    self.outputs.remove(s) if s in self.outputs else None
                    self.inputs.remove(s) if s in self.inputs else None
                    s.close()
                    self.post(self, {'state': 'poll'})

            case {'state': 'write-ready', 'args': s}:
                resp = self.sock_map.pop(s)
                if resp is not None:
                    s.send(serialize(resp))
                else:
                    self.outputs.append(s)
                self.post(self, {'state': 'poll'})

            case {'state': 'error', 'args': s}:
                if s in self.inputs:
                    self.inputs.remove(s)
                if s in self.outputs:
                    self.outputs.remove(s)
                s.close()
                self.post(self, {'state': 'poll'})

            case {'cmd': 'audit', 'actor': name, 'rid': rid}:
                actor = actor_system.get_actor(name)
                if actor is not None:
                    actor_system.send(actor, Message(sig=Sig.AUDIT, args=rid))

            case {'event': 'audit', 'rid': rid, 'data': data} as msg:
                s = self.rid_map.pop(rid)
                self.sock_map.update({s: data})
                self.post(self, {'state': 'poll'})

            case Sig.SIGINT:
                self.terminate()
                raise SystemExit

    def terminate(self):
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
            self.sock.close()
        except OSError:
            ...
        finally:
            self.conn = None


