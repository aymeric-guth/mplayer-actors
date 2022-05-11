from collections import defaultdict

from ..base import Actor, Message, Sig, actor_system, ActorGeneric
from ...settings import MOUNT_POINT, extensions_all, ROOT
from . import helpers


# search current path
# search all files
# search all dirs

class Files(Actor):
    def __init__(self, pid: int, name='',parent: Actor|None=None, **kwargs) -> None:
        super().__init__(pid, name, parent, **kwargs)
        self.mount_point = MOUNT_POINT[:]
        self.extensions = extensions_all
        self.files_tree: dict[tuple[str, ...], list[str]] = defaultdict(list)
        self.dir_tree: dict[tuple[str, ...], set[str]] = defaultdict(set)
        self.path = list(ROOT)
        self.path_full = f"{self.mount_point}{'/'.join(self.path[1:])}/"
        # self.init_logger(__name__)

    def dispatch(self, sender: ActorGeneric, msg: Message) -> None:
        match msg:
            case Message(sig=Sig.INIT, args=args):
                ...

            case Message(sig=Sig.TEST, args=args):
                ...
                # actor_system.send('Dispatcher', Message(sig=Sig.PARSE, args='1'))
                # actor_system.send('Dispatcher', Message(sig=Sig.PARSE, args='3'))
                # actor_system.send('Dispatcher', Message(sig=Sig.PARSE, args='10'))

            case Message(sig=Sig.CWD_GET, args=args):
                actor_system.send(sender, Message(sig=Sig.CWD_GET, args=helpers.get_kwargs(self)))

            case Message(sig=Sig.FILES_NEW, args=args):
                self.files_tree.clear()
                self.dir_tree.clear()

                for r in args:
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
                self.post(Message(sig=Sig.PATH_SET, args=ROOT))
                self.post(Message(sig=Sig.TEST))

            case Message(sig=Sig.SEARCH, args=args):
                self.path_full = f"{self.mount_point}{'/'.join(self.path[1:])}/"
                path = tuple(self.path)               
                self.dirs = [ 
                    i for i in list(self.dir_tree.get(path, []))
                    if i and args.lower() in i.lower()
                ]
                self.files = [ 
                    i for i in list(self.files_tree.get(path, []))
                    if i and args.lower() in i[0].lower()
                ]
                self.dirs.sort()
                self.files.sort()
                self.dirs.insert(0, "..")
                self.files.insert(0, "")
                self.len_dir = len(self.dirs)
                self.len_files = len(self.files)
                actor_system.send('Display', Message(sig=Sig.CWD_GET, args=helpers.get_kwargs(self)))

            case Message(sig=Sig.FILES_GET, args=args):
                match args:
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
                actor_system.send(sender, Message(sig=Sig.FILES_GET, args=args))

            case Message(sig=Sig.PATH_SET, args=args):
                match args:
                    case param if isinstance(param, int):
                        if not param:
                            if len(self.path) > 1:
                                self.path.pop(-1)
                            else:
                                ...
                        elif param < len(self.dirs):
                            self.path.append(f"{self.dirs[param]}")
                        elif self.files[1:] and param < len(self.files):
                            f, e = self.files[param]
                            args = [f'{self.path_full}{f}{e}',]
                            actor_system.send('MediaDispatcher', Message(sig=Sig.FILES_GET, args=args))
                        else:
                            actor_system.send('Display', Message(sig=Sig.ERROR, args=f'Invalid selection: {param}'))
                            return

                    case param if isinstance(param, list|tuple):
                        self.path = list(param)

                    case param if param is None:
                        ...

                    case param:
                        actor_system.send(sender, Message(sig=Sig.ERROR, args=f'Invalid selection: {param}'))
                        return

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
                actor_system.send('Display', Message(sig=Sig.CWD_GET, args=helpers.get_kwargs(self)))

            case Message(sig=Sig.AUDIT, args=None):
                actor_system.send(sender, {'event': 'audit', 'data': self.introspect()})

            case Message(sig=Sig.SIGQUIT):
                self.terminate()

            case _:
                print(f'Files Could not process {msg=}')
                raise SystemExit(f'{msg=}')

    def terminate(self) -> None:
        raise SystemExit('SIGQUIT')
