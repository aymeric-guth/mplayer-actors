from collections import defaultdict
import os
import re
import logging

from ...utils import SingletonMeta

from ...external.actors import Actor, Message, Sig, actor_system
from ...settings import extensions_all
from . import helpers
from ._types import CWD


# Synthetic CWD, recompose un tree à partir de critères de recherche
# regroupe tous les noeuds matchs dans une nouvelle racine récursivement

class Files(Actor, metaclass=SingletonMeta):
    def __init__(self, pid: int, parent: int, name='', **kwargs) -> None:
        super().__init__(pid, parent, name, **kwargs)
        self.files_tree: dict[tuple[str, ...], list[tuple[str, str]]] = defaultdict(list)
        self.dir_tree: dict[tuple[str, ...], set[str]] = defaultdict(set)
        self.log_lvl = logging.ERROR

    def dispatch(self, sender: int, msg: Message) -> None:
        match msg:
            case Message(sig=Sig.INIT):
                self.init()

            case Message(sig=Sig.EXIT):
                self.terminate()

            case Message(sig=Sig.CWD_GET, args=args):
                actor_system.send(sender, Message(sig=Sig.CWD_GET, args=helpers.get_kwargs(self)))

            case Message(sig=Sig.FILES_NEW, args=args):
                self.files_tree.clear()
                self.dir_tree.clear()

                for r in args:
                    path: str = r.get('path')
                    filename: str = r.get('filename')
                    ext: str = r.get('extension')
                    if ext not in extensions_all:
                        continue

                    formated_path = tuple( path.split('/')[1:-1] )
                    self.files_tree[formated_path].append((filename, ext))
                    for i, v in enumerate(formated_path):
                        key = formated_path[:i+1]
                        self.dir_tree[key[:-1]].add(key[-1])

                self.post(Message(sig=Sig.PATH_SET))

            case Message(sig=Sig.SEARCH, args=args):
                pattern = re.compile(args, re.IGNORECASE)
                self.dirs = [ 
                    i for i in list(self.dir_tree.get(CWD().path, []))
                    if pattern.search(i)
                ]
                self.files = [ 
                    i for i in list(self.files_tree.get(CWD().path, []))
                    if pattern.search(i[0])
                ]
                self.post(Message(Sig.PATH_REFRESH))

            case Message(sig=Sig.FILES_GET, args=args):
                match args:
                    case [p1, None] if isinstance(p1, int) and p1 > 0 and p1 < len(self.files):
                        # selection valide 1+
                        # selection en range de la liste de fichiers affichés
                        # selection d'UN fichier
                        f, e = self.files[p1]
                        actor_system.send('MediaDispatcher', Message(sig=Sig.FILES_GET, args=[f'{CWD().realpath}{f}{e}',]))

                    case [p1] if p1 > 0 and p1 < len(self.files):
                        args = [ f'{CWD().realpath}{f}{e}' for f, e in self.files[p1:] ]
                        actor_system.send(sender, Message(sig=Sig.FILES_GET, args=args))

                    case [p1, p2] if (p1 > 0 and p1 < len(self.files)) and (p2 > 0 and p2 < len(self.files)):
                        if p1 < p2:
                            args = [ f'{CWD().realpath}{f}{e}' for f, e in self.files[p1:p2+1] ]
                            actor_system.send(sender, Message(sig=Sig.FILES_GET, args=args))
                        elif p1 > p2:
                            args = [ f'{CWD().realpath}{f}{e}' for f, e in self.files[p1:p2-1:-1] ]
                            actor_system.send(sender, Message(sig=Sig.FILES_GET, args=args))
                        else:
                            self.post(Message(sig=Sig.FILES_GET, args=[p1, None]))

                    case None:
                        args = [ f'{CWD().realpath}{f}{e}' for f, e in self.files[1:] ]
                        actor_system.send(sender, Message(sig=Sig.FILES_GET, args=args))

                    case _:
                        # selection invalide
                        # envoi d'un message d'erreur
                        actor_system.send('Display', Message(sig=Sig.ERROR, args=f'Invalid selection: {args}'))


            case Message(sig=Sig.PATH_SET, args=param) if isinstance(param, int):
                if not param:
                    CWD().pop()
                    self.post(Message(sig=Sig.PATH_CONTENT))
                elif param < len(self.dirs):
                    # selection valide 1+
                    # selection en range de la liste des dossisers affichés
                    # default vers selection parmi les dossiers
                    CWD().push(f"{self.dirs[param]}")
                    self.post(Message(sig=Sig.PATH_CONTENT))
                else:
                    self.post(Message(sig=Sig.FILES_GET, args=[param, None]))

            case Message(sig=Sig.PATH_SET, args=param) if isinstance(param, list | tuple):
                # bookmark overload de path?
                CWD().path = param
                self.post(Message(sig=Sig.PATH_CONTENT))

            case Message(sig=Sig.PATH_SET, args=param) if param is None:
                self.post(Message(sig=Sig.PATH_CONTENT))

            case Message(sig=Sig.PATH_SET, args=param):
                actor_system.send(sender, Message(sig=Sig.ERROR, args=f'Invalid selection: {param}'))

            case Message(sig=Sig.PATH_CONTENT):
                self.dirs = list( self.dir_tree.get(CWD().path, []) )
                self.files = list( self.files_tree.get(CWD().path, []) )
                self.post(Message(sig=Sig.PATH_REFRESH))

            case Message(sig=Sig.PATH_REFRESH):
                # Guard si un folder a été delete
                while not(os.access(CWD().realpath, os.F_OK) ) or ( not(self.files_tree[CWD().path]) and not(self.dir_tree[CWD().path]) ):
                    if len(CWD()) < 2: 
                        raise OSError
                    CWD().pop()

                self.dirs.sort()
                self.files.sort()
                self.dirs.insert(0, '..')
                self.files.insert(0, ('', ''))
                self.len_dir = len(self.dirs)
                self.len_files = len(self.files)
                actor_system.send('Display', Message(sig=Sig.CWD_GET, args=helpers.get_kwargs(self)))

            case Message(sig=Sig.SIGQUIT):
                self.terminate()

            case _:
                self.logger.warning(f'Unprocessable msg={msg}')

    def terminate(self) -> None:
        raise SystemExit('SIGQUIT')
