import socket
import select
import json
import traceback
from collections import deque, defaultdict
from enum import Enum, auto
from typing import Any, Callable
import queue


BUFFSIZE = 4096

addr = socket.getaddrinfo('127.0.0.1', 8081)[0][-1]
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    sock.bind(addr)
except OSError:
    raise SystemExit
sock.setblocking(False)
sock.listen(5)

inputs: deque[socket.socket] = deque([sock])
outputs: deque[socket.socket] = deque()
_inputs: set[socket.socket] = set([sock])
_outputs: set[socket.socket] = set()


state: dict[str, Any] = {'state': 'init'}
stack: list[Any] = []
c = -1


class Data:
    def __init__(self) -> None:
        self._data = b''
        self._size = 0

    def init(self, d: bytes) -> None:
        self._size = int.from_bytes(d[:8], byteorder='big')
        self._data = d[8:]

    def __len__(self) -> int:
        return len(self._data)

    def __bool__(self) -> bool:
        return bool(self.__len__() and self.size)

    def is_ready(self) -> bool:
        return self.__len__() == self._size

    @property
    def data(self) -> bytes:
        return self._data

    @data.setter
    def data(self, value: bytes) -> None:
        if self.__len__() + len(value) > self._size:
            raise TypeError
        self._data = self._data + value

    @property
    def size(self) -> int:
        return self._size
    
    @size.setter
    def size(self, value: int) -> None:
        self._size = value

    def serialize(self) -> bytes:
        return self._size.to_bytes(length=8, byteorder='big') + self._data

    def clear(self) -> None:
        self._data = b''
        self._size = 0


class BiMap:
    def __init__(self):
        self._d: dict[int|str, int|str] = {}
        self._data: dict[int|str, Data] = {}

    def get(self, value: Any) -> Any:
        return self._d.__getitem__(value)

    def set(self, key: Any, value: Any) -> None:
        if key in self._d or value in self._d:
            raise KeyError
        self._d.__setitem__(key, value)
        self._d.__setitem__(value, key)
        d = Data()
        self._data.__setitem__(key, d)
        self._data.__setitem__(value, d)

    def __getitem__(self, __k: Any) -> Any:
        return self.get(__k)

    def __setitem__(self, __k: Any, __v: Any) -> None:
        return self.set(__k, __v)

    def clear(self, key: int|str) -> None:
        complement = self.__getitem__(key)
        del self._data[key]
        del self._data[complement]
        del self._d[key]
        del self._d[complement]

    def get_data(self, key: int|str) -> Data:
        return self._data.__getitem__(key)

    def push(self, key: int|str, value: bytes) -> None:
        buff = self.get_data(key)
        if not buff:
            buff.init(value)
        else:
            buff.data = value

    def pull(self, key: int|str) -> Data:
        d = self.get_data(key)
        complement = self.__getitem__(key)
        del self._data[key]
        del self._data[complement]
        return d

    def is_empty(self, key: int|str) -> bool:
        return not self.get_data(key).__bool__()

    def is_ready(self, key: int|str) -> bool:
        d = self.get_data(key)
        return d.is_ready()

    def exists(self, key: int|str) -> bool:
        return key in self._d



def post(message: dict[str, Any]) -> None:
    global state

    # print(f'Changing state from: state={state.get("state")} to: state={message.get("state")}')
    state.clear()
    state = message.copy()


def get_pid() -> str:
    global c

    c += 1
    return str(c)


buffer = BiMap()

while 1:
    match state:
        case {'state': 'init'}:
            post({'state': 'poll'})

        case {'state': 'poll'}:
            match select.select(inputs, outputs, inputs):
                case [rr, wr, err] if rr and (s := rr[0]) and s is sock:
                    inputs.remove(s) if s in inputs else None
                    post({'state': 'new-conn', 'args': s})

                case [rr, wr, err] if rr and (s := rr[0]):
                    inputs.remove(s) if s in inputs else None
                    post({'state': 'read-ready', 'args': s})

                case [rr, wr, err] if wr and (s := wr[0]):
                    outputs.remove(s) if s in outputs else None
                    post({'state': 'write-ready', 'args': s})

                case [rr, wr, err] if err and (s := err[0]):
                    inputs.remove(s) if s in inputs else None
                    post({'state': 'closed', 'args': s})

                case _:
                    raise Exception
                    post({'state': 'poll'})

        case {'state': 'new-conn', 'args': s}:
            conn, addr = s.accept()
            conn.setblocking(False)
            inputs.append(conn)
            inputs.append(s)
            buffer.set(conn, get_pid())
            post({'state': 'poll'})

        case {'state': 'read-ready', 'args': s}:
            data = s.recv(BUFFSIZE)
            if not data:
                post({'state': 'closed', 'args': s})
                continue
           
            buffer.push(s, data)
            if buffer.is_ready(s):
                outputs.append(s) if s not in outputs else None
            inputs.append(s) if s not in inputs else None
            post({'state': 'poll'})

        case {'state': 'write-ready', 'args': s}:
            data = buffer.get_data(s)
            if data.is_ready():
                s.send(data.serialize())
                inputs.append(s) if s in inputs else None
                data.clear()
            else:
                outputs.append(s) if s in outputs else None
            post({'state': 'poll'})

        case {'state': 'closed', 'args': s}:
            child = buffer.get(s)
            actor_system.send(child, {'type': 'state', 'args': 'terminate'})
            buffer.clear(s)
            inputs.remove(s) if s in inputs else None
            outputs.remove(s) if s in outputs else None
            try:
                s.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                s.close()
            except OSError:
                pass
            post({'state': 'poll'})

        case {'type': 'publish', 'args': message}:
            ...

        case {'type': 'subscribe', 'args': message}:
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