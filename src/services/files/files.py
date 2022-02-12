from collections import defaultdict
import os

from src.services.files.helpers import initial_setup

from ..base import Actor, Message, Sig
from ..settings import MOUNT_POINT, PATH, extensions_all, ROOT
from . import helpers


# search current path
# search all files
# search all dirs

class Files(Actor):
    def __init__(self, dispatcher: Actor) -> None:
        super().__init__()
        self.DEBUG = 0
        self.dispatcher = dispatcher
        self.mount_point = MOUNT_POINT[:]
        self.extensions = extensions_all
        self.files_tree = defaultdict(list)
        self.dir_tree = defaultdict(set)
        self.path = list(ROOT)
        self.path_full = f"{self.mount_point}{'/'.join(self.path[1:])}/"
        self.post(self, Message(sig=Sig.INIT))

    def run(self) -> None:
        while 1:
            (actor, msg) = self.mq.get()
            self.debug(msg, actor)

            match msg.sig:
                case Sig.INIT:
                    ...

                case Sig.FILES_SET:
                    self.files_tree = defaultdict(list)
                    self.dir_tree = defaultdict(set)

                    # res = filter(lambda x: x[-1] in extensions_all, msg.args)
                    # lambda x: tuple( x.split('/')[1:-1] )
                    # self.files_tree = {
                    #     self.files_tree[].append((f, e))
                    #     for p, f, e in res
                    # }

                    for r in msg.args:
                        path = r.get('path')
                        file_name = r.get('filename')
                        extension = r.get('extension')
                        if extension not in extensions_all:
                            continue
                        formated_path = tuple( path.split('/')[1:-1] )
                        self.files_tree[formated_path].append((file_name, extension))
                        for i, v in enumerate(formated_path):
                            key = formated_path[:i+1]
                            self.dir_tree[key[:-1]].add(key[-1])
                    self.post(None, Message(sig=Sig.PATH_SET, args=ROOT))

                case Sig.FILES_GET:
                    match msg.args:
                        case [p1] if isinstance(p1, int) and p1 >= 0 and p1 < len(self.files):
                            args = [ f'{self.path_full}{f}{e}' for f, e in self.files[p1:] ]
                        case [p1, p2]:
                            ...
                        # case [p1, p2] if isinstance(p1, int) and isinstance(p2, int) and p1 >= 0 and p1 < len(self.files) and p2 >= 0 and p2 < len(self.files):
                        #     args = [ f'{self.path_full}{f}{e}' for f, e in self.files[p1:] ]
                        case None:
                            args = [ f'{self.path_full}{f}{e}' for f, e in self.files[1:] ]
                        case _:
                            ...
                    
                    actor.post(None, Message(sig=Sig.PLAY, args=args))

                case Sig.PATH_SET:
                    match msg.args:
                        case param if isinstance(param, int):
                            if not param:
                                if len(self.path) > 1:
                                    self.path.pop(-1)
                                else:
                                    ...
                            elif param < len(self.dirs):
                                self.path.append(f"{self.dirs[param]}")
                            else:
                                actor = self.get_actor('Display')
                                actor.post(self, Message(sig=Sig.ERROR, args=f'Invalid selection: {param}'))
                                continue

                        case param if isinstance(param, list|tuple):
                            self.path = list(param)
                        case param if param is None:
                            ...
                        case param:
                            actor.post(self, Message(sig=Sig.ERROR, args=f'Invalid selection: {param}'))
                            continue

                    self.path_full = f"{self.mount_point}{'/'.join(self.path[1:])}/"
                    path = tuple(self.path)

            # Guard si un folder a été delete
                    # while not(os.access(self.path_full, os.F_OK) ) or ( not(self.files_tree[path]) and not(self.dir_tree[path]) ):
                    #     if len(self.path) < 2: raise OSError
                    #     self.path.pop(-1)
                    #     self.path_full = f"{self.mount_point}{'/'.join(self.path[1:])}/"
                    #     path = tuple(self.path)

                    self.dirs = list( self.dir_tree.get(path, []) )
                    self.files = list( self.files_tree.get(path, []) )
                    self.dirs.sort()
                    self.files.sort()
                    self.dirs.insert(0, "..")
                    self.files.insert(0, "")
                    self.len_dir = len(self.dirs)
                    self.len_files = len(self.files)

                    actor = self.get_actor('Display')
                    actor.post(self, Message(sig=Sig.CWD_GET, args=helpers.get_kwargs(self)))

                case Sig.REGISTER:
                    self.register(actor)

                case _:
                    print(f'Files Could not process {msg=}')
                    raise SystemExit(f'{msg=}')

            self.mq.task_done()