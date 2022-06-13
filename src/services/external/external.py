import subprocess
import socket
import logging
from pathlib import Path, PurePath
import pickle

from ...utils import SingletonMeta

from ...external.actors import Actor, Message, Sig, send, DispatchError, SystemMessage
from ...settings import MOUNT_POINT, SMB_USER, SMB_PASS, SMB_ADDR, SMB_PORT, ENV_PATH, CACHE_PATH
from ..files._types import CWD


class External(Actor):
    def __init__(self, pid: int, parent: int, name='', **kwargs) -> None:
        super().__init__(pid, parent, name, **kwargs)
        self.log_lvl = logging.ERROR

    def dispatch(self, sender: int, msg: Message) -> None:
        try:
            super().dispatch(sender, msg)
        except SystemMessage:
            return

        jump_table: dict[str, list|tuple]
        match msg:
            case {'event': 'command', 'name': 'os-open'}:
                ...
            case Message(sig=Sig.OPEN, args=None):
                send('Files', Message(sig=Sig.CWD_GET))
                # send('Files', {'event': 'request', 'name': 'cwd-get'})

            # case {'event': 'response', 'name': 'cwd-get', 'args': args}:
            #     ...
            case Message(sig=Sig.CWD_GET, args=args):
                subprocess.run(['open', args.get('path_full')])

            case Message(sig=Sig.SMB_PING, args=args):
                ...
                # try:
                #     with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                #         sock.settimeout(args)
                #         sock.connect((SMB_ADDR, SMB_PORT))
                # except socket.error as err:
                #     self.logger.error(f'Could not join host: {SMB_ADDR} on port: {SMB_PORT} cause: {err}')
                #     send(self.pid, Message(sig=Sig.SMB_PING, args=args+1))
                # else:
                #     self.logger.info(f'host: {SMB_ADDR} on port: {SMB_PORT} is up, trying to connect')
                #     send(self.pid, Message(sig=Sig.SMB_MOUNT))

            case Message(sig=Sig.SMB_MOUNT, args=args):
                ...
                # result = subprocess.run(["mount", "-t", "smbfs"], capture_output=True)
                # mounted_shares = result.stdout[:-1].decode("utf8")
                # share_name = 'Audio'
                # if share_name not in mounted_shares:
                #     mount_point = MOUNT_POINT / share_name
                #     subprocess.run(["mkdir", "-p", str(mount_point)])
                #     subprocess.run([
                #         "mount", "-t", "smbfs",
                #         f"//{SMB_USER}:{SMB_PASS}@{SMB_ADDR}/{share_name}",
                #         str(mount_point)
                #     ], capture_output=True)

            case Message(sig=Sig.FILES_NEW, args=data):
                with open(CACHE_PATH / 'cache.pckl', 'wb') as f:
                    pickle.dump(data, f)
                send('Files', Message(sig=Sig.FILES_NEW, args=data))

            case Message(sig=Sig.GET_CACHE, args=args):
                try:
                    with open(CACHE_PATH / 'cache.pckl', 'rb') as f:
                        data = pickle.load(f)
                except Exception:
                    send('API', Message(sig=Sig.FILES_GET, args=args))
                else:
                    send('Files', Message(sig=Sig.FILES_NEW, args=data))

            case Message(sig=Sig.HOOK, args=args) if isinstance(args, list | tuple) and len(args) == 2:
                k, v = args
                try:
                    with open(CACHE_PATH / 'jump-table.pckl', 'rb') as f:
                        jump_table = pickle.load(f)
                except Exception:
                    jump_table = {}

                jump_table.update({k: v})
                with open(CACHE_PATH / 'jump-table.pckl', 'wb') as f:
                    pickle.dump(jump_table, f)

            case {'event': 'command', 'name': 'hook', 'args': args}:
                ...
            case Message(sig=Sig.HOOK, args=args):
                try:
                    with open(CACHE_PATH / 'jump-table.pckl', 'rb') as f:
                        jump_table = pickle.load(f)
                except Exception:
                    jump_table = {}

                jump_table.update({args: CWD().path})
                with open(CACHE_PATH / 'jump-table.pckl', 'wb') as f:
                    pickle.dump(jump_table, f)

            case {'event': 'command', 'name': 'jump', 'args': args}:
                ...
            case Message(sig=Sig.JUMP, args=args):
                try:
                    with open(CACHE_PATH / 'jump-table.pckl', 'rb') as f:
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
