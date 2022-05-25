from typing import Any, Callable
from collections import defaultdict

from ...external.actors import Event, send, Message, Sig


class ObservableProperties:
    def __init__(self, pid: int) -> None:
        self.pid = pid
        self._container: dict[str, Any] = {}
        self._setters: dict[str, Callable] = {}
        self._observers: defaultdict[str, list[str|int]] = defaultdict(list)
        self._registred: set[str] = set()

    def set(self, key: str, value: Any) -> None:
        func = self._setters.get(value, lambda x: x)
        self._container.update({key: func(value)})
        self.notify(key)

    def get(self, key: str, default: Any=None) -> Any:
        return self._container.get(key, default)

    def register_setter(self, name: str, func: Callable) -> None:
        self._setters.update({name: func})
        self._registred.add(name)

    def register(self, name: str, pid: int|str):
        obs = self._observers[name]
        self._registred.add(name)
        if pid not in obs:
        # if obs is not None and pid not in obs:
            obs.append(pid)

    def unregister(self, name: str, pid: int|str):
        obs = self._observers.get(name)
        if pid in obs: # type: ignore
            obs.remove(pid) # type: ignore

    def notify(self, name: str) -> None:
        value = self._container.get(name)
        event = Event(type='property-change', name=name, args=value)
        # msg = Message(sig=Sig.WATCHER, args={name: value})
        for obs in self._observers[name]:
            send(to=obs, what=event)

    def __contains__(self, key: str) -> bool:
        return key in self._registred

    def __repr__(self) -> str:
        # s = ''
        # for k, v in self._observers.items():
        #     s += f'name={k} value={v} '
        return repr(self._observers) + repr(self._container) + repr(self._registred)