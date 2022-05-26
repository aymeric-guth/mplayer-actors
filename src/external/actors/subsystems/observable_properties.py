from typing import Any, Callable
from collections import defaultdict

from ..message import Event, Message, Sig
from ..actor_system import send, ActorSystem, _get_caller
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
        # ActorSystem().logger.error(f'Unregistering pid={pid} for events={name}')
        obs = self._observers.get(name)
        if pid in obs: # type: ignore
            obs.remove(pid) # type: ignore

    def notify(self, name, value) -> None:
        event = Event(type='property-change', name=to_kebab_case(name), args=value)
        # ActorSystem().logger.error(f'Notifying observers={self._observers[name]} for events={name} {value=}')
        caller = _get_caller(4)
        for obs in self._observers[name]:
            # send(to=obs, what=event)
            ActorSystem()._send(sender=caller, receiver=obs, msg=event)

    def __contains__(self, key: str) -> bool:
        return key in self._registred

    def __repr__(self) -> str:
        return repr(self._observers) + repr(self._registred)
