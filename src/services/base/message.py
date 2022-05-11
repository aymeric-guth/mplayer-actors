from typing import Any, TypeVar
from dataclasses import dataclass

from .sig import Sig



class Message:
    def __init__(self, sig: Sig, args: Any=None) -> None:
        self._sig = sig
        self._args = args

    def __repr__(self) -> str:
        return f'Message(sig={self.sig}, args={repr(type(self.args))})'

    @property
    def sig(self) -> Sig:
        return self._sig

    @sig.setter
    def sig(self, value: Any) -> None:
        raise TypeError('Property is immutable')

    @property
    def args(self) -> Any:
        return self._args

    @args.setter
    def args(self, value: Any) -> None:
        raise TypeError('Property is immutable')

    # def __lshift__(self, other: Sig) -> T:
    #     return self.__class__(sig=other, args=self)

    # def __rshift__(self, other: Sig) -> T:
    #     return self.__class__(sig=other, args=self)


@dataclass(frozen=True)
class Msg:
    event: str
    name: str
    args: Any = None
