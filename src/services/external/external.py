import subprocess

from ..base import Actor, Message, Sig, actor_system


class External(Actor):
    def __init__(self, pid: int, name='', parent: Actor=None, **kwargs) -> None:
        super().__init__(pid, name, parent, **kwargs)
        self.DEBUG = 0

    def dispatch(self, sender, msg) -> None:
        match msg:
            case Message(sig=Sig.OPEN, args=None):
                actor_system.send('Files', Message(sig=Sig.CWD_GET))

            case Message(sig=Sig.CWD_GET):
                subprocess.run(['open', msg.args.get('path_full')])

            case _:
                ...
