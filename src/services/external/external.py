import subprocess
import socket

from ..base import Actor, Message, Sig, actor_system
from ...settings import ALLOWED_SHARES, MOUNT_POINT, SMB_USER, SMB_PASS, SMB_ADDR, SMB_PORT


class External(Actor):
    def __init__(self, pid: int, name='', parent: Actor|None=None, **kwargs) -> None:
        super().__init__(pid, name, parent, **kwargs)
        self.LOG = 0
        self.post(self, Message(sig=Sig.INIT))

    def dispatch(self, sender, msg) -> None:
        match msg:
            case Message(sig=Sig.INIT, args=None):
                self.post(self, Message(sig=Sig.SMB_PING))

            case Message(sig=Sig.OPEN, args=None):
                actor_system.send('Files', Message(sig=Sig.CWD_GET))

            case Message(sig=Sig.CWD_GET, args=args):
                subprocess.run(['open', args.get('path_full')])

            case Message(sig=Sig.SMB_PING, args=args):
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.settimeout(1)
                        sock.connect((SMB_ADDR, SMB_PORT))
                except socket.error as err:
                    self.log_msg(f'Could not join host: {SMB_ADDR} on port: {SMB_PORT} cause: {err}')
                    actor_system.send('Dispatcher', Message(sig=Sig.NETWORK_FAILURE))
                else:
                    self.log_msg(f'host: {SMB_ADDR} on port: {SMB_PORT} is up, trying to connect')
                    self.post(self, Message(sig=Sig.SMB_MOUNT))

            case Message(sig=Sig.SMB_MOUNT, args=args):
                result = subprocess.run(["mount", "-t", "smbfs"], capture_output=True)
                mounted_shares = result.stdout[:-1].decode("utf8")
                for share_name in ALLOWED_SHARES:
                    if share_name not in mounted_shares:
                        mount_point = f"{MOUNT_POINT}{share_name}"
                        subprocess.run(["mkdir", "-p", mount_point])
                        subprocess.run([
                            "mount", "-t", "smbfs",
                            f"//{SMB_USER}:{SMB_PASS}@{SMB_ADDR}/{share_name}",
                            mount_point
                        ], capture_output=True)

            # case Message(sig=Sig.SET_CACHE, args=args):
            #     ...

            # case Message(sig=Sig.GET_CACHE, args=args):
            #     ...

            case _:
                ...
