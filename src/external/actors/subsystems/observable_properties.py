from typing import Any, Callable
from collections import defaultdict

from ..message import Event, Message, Sig
from ..actor_system import send
from src.utils import to_kebab_case, to_snake_case


class ObservableProperties:
    def __init__(self) -> None:
        self._observers: defaultdict[str, list[str|int]] = defaultdict(list)
        self._registred: set[str] = set()

    def register(self, name: str, pid: int|str):
        obs = self._observers[name]
        if name not in self:
            self._registred.add(name)
        if pid not in obs:
            obs.append(pid)

    def unregister(self, name: str, pid: int|str):
        obs = self._observers.get(name)
        if pid in obs: # type: ignore
            obs.remove(pid) # type: ignore

    def notify(self, descriptor) -> None:
        name = getattr(descriptor, 'name')
        value = getattr(descriptor, 'value')        
        event = Event(type='property-change', name=to_kebab_case(name), args=value)
        for obs in self._observers[name]:
            send(to=obs, what=event)

    def __contains__(self, key: str) -> bool:
        return key in self._registred

    def __repr__(self) -> str:
        return repr(self._observers) + repr(self._registred)


class Observable:
    def __init__(
        self, 
        name=None, 
        default=None, 
        setter=lambda x: 0. if x is None else x
    ) -> None:
        self.name = name
        self.value = default
        self.setter = setter

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name

    def __get__(self, instance: object, owner: type) -> object:
        if instance is None:
            return self
        return instance.__dict__[self.name]

    def __set__(self, instance: object, value: Any) -> None:
        instance.__dict__[self.name] = self.setter(value)
        try:
            obs = instance.__dict__['obs']
        except Exception:
            raise SystemExit
        obs.notify(self)
        # self.value = self.setter(value)

    def register(self, name):
        print(f'Got name={name}')
