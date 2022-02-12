from typing import Any

from .sig import Sig


class Message:
    def __init__(self, sig: Sig, args: Any=None) -> None:
        self._sig = sig
        self._args = args

    def __repr__(self) -> str:
        return f'Message(sig={self.sig}, args={repr(self.args)[:100]})'

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
