import subprocess
import socket
import logging
from pathlib import Path
import pickle

from ...utils import SingletonMeta

from ...external.actors import Actor, Message, Sig, send, DispatchError
from ...settings import ALLOWED_SHARES, MOUNT_POINT, SMB_USER, SMB_PASS, SMB_ADDR, SMB_PORT, ENV_PATH, VIDEO_PATH, MUSIC_PATH, ROOT, MUSIC_TODO
from ..files._types import CWD


class External(Actor):
    def __init__(self, pid: int, parent: int, name='', **kwargs) -> None:
        super().__init__(pid, parent, name, **kwargs)
        self.log_lvl = logging.ERROR

    def dispatch(self, sender: int, msg: Message) -> None:
        try:
            super().dispatch(sender, msg)
        except DispatchError:
            return

        jump_table: dict[str, list | tuple]
        match msg:
            case Message(sig=Sig.OPEN, args=None):
                send('Files', Message(sig=Sig.CWD_GET))

            case Message(sig=Sig.CWD_GET, args=args):
                subprocess.run(['open', args.get('path_full')])

            case Message(sig=Sig.SMB_PING, args=args):
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.settimeout(args)
                        sock.connect((SMB_ADDR, SMB_PORT))
                except socket.error as err:
                    self.logger.error(f'Could not join host: {SMB_ADDR} on port: {SMB_PORT} cause: {err}')
                    send(self.pid, Message(sig=Sig.SMB_PING, args=args+1))
                else:
                    self.logger.info(f'host: {SMB_ADDR} on port: {SMB_PORT} is up, trying to connect')
                    send(self.pid, Message(sig=Sig.SMB_MOUNT))

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

            case Message(sig=Sig.FILES_NEW, args=data):
                with open(Path(ENV_PATH) / 'cache.pckl', 'wb') as f:
                    pickle.dump(data, f)
                send('Files', Message(sig=Sig.FILES_NEW, args=data))

            case Message(sig=Sig.GET_CACHE, args=args):
                try:
                    with open(Path(ENV_PATH) / 'cache.pckl', 'rb') as f:
                        data = pickle.load(f)
                except Exception:
                    send('API', Message(sig=Sig.FILES_GET, args=args))
                else:
                    send('Files', Message(sig=Sig.FILES_NEW, args=data))

            case Message(sig=Sig.HOOK, args=args) if isinstance(args, list | tuple) and len(args) == 2:
                k, v = args
                try:
                    with open(Path(ENV_PATH) / 'jump-table.pckl', 'rb') as f:
                        jump_table = pickle.load(f)
                except Exception:
                    jump_table = {}

                jump_table.update({k: v})
                with open(Path(ENV_PATH) / 'jump-table.pckl', 'wb') as f:
                    pickle.dump(jump_table, f)

            case Message(sig=Sig.HOOK, args=args):
                try:
                    with open(Path(ENV_PATH) / 'jump-table.pckl', 'rb') as f:
                        jump_table = pickle.load(f)
                except Exception:
                    jump_table = {}

                jump_table.update({args: CWD().path})
                with open(Path(ENV_PATH) / 'jump-table.pckl', 'wb') as f:
                    pickle.dump(jump_table, f)

            case Message(sig=Sig.JUMP, args=args):
                try:
                    with open(Path(ENV_PATH) / 'jump-table.pckl', 'rb') as f:
                        jump_table = pickle.load(f)
                except Exception:
                    ...
                else:
                    cwd = jump_table.get(args)
                    send('Files', Message(sig=Sig.PATH_SET, args=cwd))                       

            case _:
                self.logger.warning(f'Unprocessable msg={msg}')


    def init(self) -> None:
        send(self.pid, Message(sig=Sig.SMB_PING, args=1))
        send(self.pid, Message(sig=Sig.HOOK, args=('root', ROOT[:])))
        send(self.pid, Message(sig=Sig.HOOK, args=('/', ROOT[:])))
        send(self.pid, Message(sig=Sig.HOOK, args=('music', MUSIC_PATH[:])))
        send(self.pid, Message(sig=Sig.HOOK, args=('video', VIDEO_PATH[:])))
        send(self.pid, Message(sig=Sig.HOOK, args=('vdo', VIDEO_PATH[:])))
        send(self.pid, Message(sig=Sig.HOOK, args=('td', MUSIC_TODO[:])))
        send(self.pid, Message(sig=Sig.HOOK, args=('todo', MUSIC_TODO[:])))
