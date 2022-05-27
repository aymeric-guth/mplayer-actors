from typing import Any
import threading

from ..base_actor import BaseActor


class Manager:
    def __init__(self, actor: BaseActor) -> None:
        self.actor = actor
        self.t = threading.Thread(target=self.actor.run, daemon=True)

    def __call__(self, *args: Any, **kwds: Any) -> None:
        ...