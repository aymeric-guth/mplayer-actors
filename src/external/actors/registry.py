from typing import Optional, Union

from .base_actor import BaseActor

from ...utils import SingletonMeta


class ActorRegistry(metaclass=SingletonMeta):
    def __init__(self) -> None:
        self._container: dict[int, BaseActor] = {}
        # self._names: dict[str, int] = {}
        # self._types: dict[type, int] = {}
        # self._actors: dict[BaseActor, int] = {}

    def register(self, key: int, actor: BaseActor) -> None:
        if self.get(key) is None:
            self._container.update({key: actor})
        else:
            raise Exception

    def unregister(self, key: int) -> Optional[BaseActor]:
        try:
            return self._container.pop(key)
        except KeyError:
            return None
        # if self.get(key) is not None:
        #     del self._container[key]

    def get(self, key: int) -> Optional[BaseActor]:
        return self._container.get(key)

    def lookup(self, actor: int|str|type|BaseActor) -> Optional[BaseActor]:
        '''
        renvoie l'instance d'un acteur
        valeurs possibles pour récupérer l'instance d'un acteur:
        pid (int)
        nom (str)
        nom de classe (str)
        classe (type)
        instance (BaseActor)
        '''
        match actor:
            case actor if isinstance(actor, int):
                return self.get(actor)

            case actor if isinstance(actor, str):
                func = lambda a: actor == a.name

            case actor if isinstance(actor, type) and issubclass(actor, BaseActor):
                func = lambda a: actor is a.__class__

            case actor if isinstance(actor, BaseActor):
                func = lambda a: actor is a

            case actor if actor is None:
                return None

            case _:
                return None

        for k, v in self._container.items():
            if func(v):
                return v
        else:
            return None

    def __iter__(self):
        self.n = 0
        self.max = len(self._container)
        self.items = [i for i in self._container.items()]
        return self

    def __next__(self) -> tuple[int, BaseActor]:
        if self.n < self.max:
            return self.items[self.n]
        else:
            raise StopIteration

    def __str__(self) -> str:
        return self._container.__str__()

    def __repr__(self) -> str:
        return self._container.__repr__()

    def __getitem__(self, key: int) -> BaseActor:
        return self._container[key]

    def __delitem__(self, key: int) -> BaseActor:
        return self.__getitem__(key)

    def __len__(self) -> int:
        return len(self._container)

    def items(self) -> dict[int, BaseActor]:
        return self._container.items()
