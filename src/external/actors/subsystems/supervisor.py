from typing import Any
import threading

from ..base_actor import BaseActor


class Supervisor:
    def __init__(self, actor: BaseActor, policy: Any) -> None:
        self.actor = actor
        # self.t = threading.Thread(target=self.actor.run, daemon=True)
        # on_crash(policy)

    def __call__(self, *args: Any, **kwds: Any) -> None:
        ...


