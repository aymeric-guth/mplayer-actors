from typing import Any, Callable
import json
import threading


def lock(func) -> Callable:
    def inner(*args, **kwargs) -> Any:
        self, *_ = args
        with self._lock:
            return func(*args, **kwargs)
    return inner

class Data:
    def __init__(self) -> None:
        self._data = b''
        self._data_bis: dict[str, Any] = {}
        self._size = 0
        self._lock = threading.Lock()

    def init(self, d: bytes) -> None:
        self._size = int.from_bytes(d[:8], byteorder='big')
        self._data = d[8:]

    def __len__(self) -> int:
        return len(self._data)

    def __bool__(self) -> bool:
        return bool(self.__len__() and self.size)

    def __repr__(self) -> str:
        return f'Data(_data_bis={self._data_bis!r}, _size={self._size})'

    def is_ready(self) -> bool:
        return self.__len__() == self._size

    def _is_ready(self) -> bool:
        return len(self._data_bis) > 0

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

    def _serialize(self) -> bytes:
        d = json.dumps(self._data_bis).encode('utf-8')
        return len(d).to_bytes(length=8, byteorder='big') + d

    def deserialize(self) -> dict[str, Any]:
        return json.loads(self._data.decode("utf-8"))

    def clear(self) -> None:
        self._data = b''
        self._size = 0
        self._data_bis = {}


class BiMap:
    def __init__(self):
        self._d: dict[int|str, int|str] = {}
        self._data: dict[int|str, Data] = {}

    def get(self, value: Any) -> Any:
        return self._d.get(value)
        # return self._d.__getitem__(value)

    def set(self, key: Any, value: Any) -> None:
        if key in self._d or value in self._d:
            raise KeyError
        self._d.update({key: value})
        self._d.update({value: key})
        d = Data()
        self._data.update({key: d})
        self._data.update({value: d})

    # def __getitem__(self, __k: Any) -> Any:
    #     return self.get(__k)

    # def __setitem__(self, __k: Any, __v: Any) -> None:
    #     return self.set(__k, __v)

    def clear(self, key: int|str) -> None:
        complement = self.get(key)
        del self._data[key]
        del self._data[complement]
        del self._d[key]
        del self._d[complement]

    def get_data(self, key: int|str) -> Data:
        d = self._data.get(key)
        if d is None:
            raise KeyError
        else:
            return d

    def push(self, key: int|str, value: bytes) -> None:
        buff = self.get_data(key)
        if not buff:
            buff.init(value)
        else:
            buff.data = value

    def pull(self, key: int|str) -> Data:
        d = self.get_data(key)
        complement = self.get(key)
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


def serialize(data: dict[str, Any]) -> bytes:
    return _serialize(json.dumps(data).encode('utf-8'))

def _serialize(data: bytes) -> bytes:
    return len(data).to_bytes(length=8, byteorder='big') + data

def deserialize(data: bytes) -> tuple[int, dict[str, Any]]:
    (size, d) = _deserialize(data)
    return (size, json.loads(d.decode("utf-8")))

def _deserialize(data: bytes) -> tuple[int, bytes]:
    return (int.from_bytes(data[:8], byteorder='big'), data[8:])
