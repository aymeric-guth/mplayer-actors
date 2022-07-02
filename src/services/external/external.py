import subprocess
import socket
import logging
import pickle

from actors import Actor, Message, send, DispatchError, SystemMessage, Request, Response, Event
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
            case Request(type='os', name='open'):
                send(to='Files', what=Request(type='files', name='cwd'))

            case Response(type='files', name='cwd', args=args):
                subprocess.run(['open', args.get('path_full')])

            case Request(type='smb', name='ping', args=args):
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.settimeout(args)
                        sock.connect((SMB_ADDR, SMB_PORT))
                except socket.error as err:
                    self.logger.error(f'Could not join host: {SMB_ADDR} on port: {SMB_PORT} cause: {err}')
                    send(to=self.pid, what=Request(type='smb', name='ping', args=args+1))
                else:
                    self.logger.info(f'host: {SMB_ADDR} on port: {SMB_PORT} is up, trying to connect')
                    send(to=self.pid, what=Response(type='smb', name='ping'))

            case Response(type='smb', name='ping'):
                result = subprocess.run(["mount", "-t", "smbfs"], capture_output=True)
                mounted_shares = result.stdout[:-1].decode("utf8")
                share_name = 'Audio'
                if share_name not in mounted_shares:
                    mount_point = MOUNT_POINT / share_name
                    subprocess.run(["mkdir", "-p", str(mount_point)])
                    subprocess.run([
                        "mount", "-t", "smbfs",
                        f"//{SMB_USER}:{SMB_PASS}@{SMB_ADDR}/{share_name}",
                        str(mount_point)
                    ], capture_output=True)

            case Event(type='files', name='new', args=data):
                with open(CACHE_PATH / 'cache.pckl', 'wb') as f:
                    pickle.dump(data, f)
                send(to='Files', what=Event(type='files', name='new', args=data))

            case Request(type='files', name='cache'):
                try:
                    with open(CACHE_PATH / 'cache.pckl', 'rb') as f:
                        data = pickle.load(f)
                except Exception:
                    send(to='API', what=Event(type='files', name='cache-empty'))
                else:
                    send(to='API', what=Response(type='files', name='cache', args=data))

            case Request(type='cmd', name='hook', args=args) if isinstance(args, list | tuple) and len(args) == 2:
                k, v = args
                try:
                    with open(CACHE_PATH / 'jump-table.pckl', 'rb') as f:
                        jump_table = pickle.load(f)
                except Exception:
                    jump_table = {}

                jump_table.update({k: v})
                with open(CACHE_PATH / 'jump-table.pckl', 'wb') as f:
                    pickle.dump(jump_table, f)

            case Request(type='cmd', name='hook', args=args):
                try:
                    with open(CACHE_PATH / 'jump-table.pckl', 'rb') as f:
                        jump_table = pickle.load(f)
                except Exception:
                    jump_table = {}

                jump_table.update({args: CWD().path})
                with open(CACHE_PATH / 'jump-table.pckl', 'wb') as f:
                    pickle.dump(jump_table, f)

            case Request(type='cmd', name='jump', args=args):
                try:
                    with open(CACHE_PATH / 'jump-table.pckl', 'rb') as f:
                        jump_table = pickle.load(f)
                except Exception:
                    ...
                else:
                    cwd = jump_table.get(args)
                    send(to='Files', what=Request(type='files', name='cwd-change', args=cwd))            

            case _:
                self.logger.warning(f'Unprocessable msg={msg}')


    def init(self) -> None:
        send(to=self.pid, what=Request(type='smb', name='ping', args=1))
