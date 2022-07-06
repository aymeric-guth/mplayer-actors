from collections import defaultdict
import re
import logging

from actors import (
    Actor,
    Message,
    send,
    DispatchError,
    Event,
    Request,
    Response,
    SystemMessage,
    forward,
)
from ...settings import extensions_all
from . import helpers
from ._types import CWD
from actors.subsystems.observable_properties import Observable


# Synthetic CWD, recompose un tree à partir de critères de recherche
# regroupe tous les noeuds matchs dans une nouvelle racine récursivement


class Files(Actor):
    cwd = Observable()

    def __init__(self, pid: int, parent: int, name="", **kwargs) -> None:
        super().__init__(pid, parent, name, **kwargs)
        self.files_tree: dict[tuple[str, ...], list[tuple[str, str]]] = defaultdict(
            list
        )
        self.dir_tree: dict[tuple[str, ...], set[str]] = defaultdict(set)
        self.log_lvl = logging.ERROR

    def dispatch(self, sender: int, msg: Message) -> None:
        try:
            super().dispatch(sender, msg)
        except SystemMessage:
            return

        match msg:
            case Request(type="files", name="cwd-content"):
                send(
                    to=sender,
                    what=Response(
                        type="files", name="cwd-content", args=helpers.get_kwargs(self)
                    ),
                )

            case Event(type="files", name="new-data", args=args):
                self.files_tree.clear()
                self.dir_tree.clear()

                for r in args:
                    ext: str = r.get("extension")
                    if ext not in extensions_all:
                        continue
                    path: str = r.get("path")
                    filename: str = r.get("filename")

                    formated_path = tuple(path.split("/")[1:-1])
                    self.files_tree[formated_path].append((filename, ext))
                    for i, v in enumerate(formated_path):
                        key = formated_path[: i + 1]
                        self.dir_tree[key[:-1]].add(key[-1])

                # send(to=self.pid, what=Event(type='files', name='cwd-changed'))
                # initialisation apres modification globales de la structure de données
                send(
                    to=self.pid,
                    what=Event(type="files", name="data-changed", args=args),
                )

            case Request(type="files", name="search", args=args):
                pattern = re.compile(args, re.IGNORECASE)
                self.dirs = [
                    i
                    for i in list(self.dir_tree.get(CWD().path, []))
                    if pattern.search(i)
                ]
                self.files = [
                    i
                    for i in list(self.files_tree.get(CWD().path, []))
                    if pattern.search(i[0])
                ]
                send(to=self.pid, what=Event(type="files", name="content-reloaded"))

            case Request(type="files", name="cwd-change", args=param) if isinstance(
                param, int
            ):
                if not param:
                    CWD().pop()
                    send(to=self.pid, what=Request(type="files", name="content-reload"))
                elif param < len(self.dirs):
                    # selection valide 1+
                    # selection en range de la liste des dossisers affichés
                    # default vers selection parmi les dossiers
                    CWD().push(f"{self.dirs[param]}")
                    send(to=self.pid, what=Request(type="files", name="content-reload"))
                else:
                    send(
                        to=self.pid,
                        what=Request(type="files", name="content", args=[param, None]),
                    )

            case Request(type="files", name="cwd-change", args=param) if isinstance(
                param, list | tuple
            ):
                # bookmark overload de path?
                CWD().path = param
                send(to=self.pid, what=Request(type="files", name="content-reload"))

            case Request(type="files", name="cwd-change", args=param) if param is None:
                send(to=self.pid, what=Request(type="files", name="content-reload"))

            case Request(type="files", name="cwd-change", args=param):
                send(
                    to=self.pid,
                    what=Event(
                        type="files",
                        name="cwd-invalid",
                        args=f"Invalid selection: {param}",
                    ),
                )

            case Event(type="files", name="data-changed", args=args):
                send(to=self.pid, what=Request(type="files", name="content-reload"))

            case Request(type="files", name="content-reload"):
                self.dirs = list(self.dir_tree.get(CWD().path, []))
                self.files = list(self.files_tree.get(CWD().path, []))
                send(to=self.pid, what=Event(type="files", name="content-changed"))

            case Event(type="files", name="content-changed"):
                # Guard si un folder a été delete
                # while not(os.access(CWD().realpath, os.F_OK) ) or ( not(self.files_tree[CWD().path]) and not(self.dir_tree[CWD().path]) ):
                #     self.logger.warning(f'Unavailable path: {CWD().path}')
                #     if len(CWD()) < 2:
                #         raise OSError
                #     CWD().pop()

                self.dirs.sort()
                self.files.sort()
                self.dirs.insert(0, "..")
                self.files.insert(0, ("", ""))
                self.len_dir = len(self.dirs)
                self.len_files = len(self.files)
                send(
                    to="Display",
                    what=Event(
                        type="files", name="cwd-changed", args=helpers.get_kwargs(self)
                    ),
                )

            # case Request(type="files", name="content-local", args=args):
            #     forward(sender, self.pid, Request(type="files", name="content", args=args))

            # case Request(type="files", name="content-remote", args=args):
            #     forward(sender, self.pid, Request(type="files", name="content", args=args))

            case Request(type="files", name="content", args=args):
                match args:
                    case [p1, None] if isinstance(p1, int) and p1 > 0 and p1 < len(
                        self.files
                    ):
                        # selection valide 1+
                        # selection en range de la liste de fichiers affichés
                        # selection d'UN fichier
                        f, e = self.files[p1]
                        args = [
                            str(CWD().realpath / f"{f}{e}"),
                        ]
                        send(
                            to=sender,
                            what=Response(type="files", name="content", args=args),
                        )

                    case [p1] if p1 > 0 and p1 < len(self.files):
                        args = [
                            str(CWD().realpath / f"{f}{e}") for f, e in self.files[p1:]
                        ]
                        send(
                            to=sender,
                            what=Response(type="files", name="content", args=args),
                        )

                    case [p1, p2] if (p1 > 0 and p1 < len(self.files)) and (
                        p2 > 0 and p2 < len(self.files)
                    ):
                        if p1 < p2:
                            args = [
                                str(CWD().realpath / f"{f}{e}")
                                for f, e in self.files[p1 : p2 + 1]
                            ]
                            send(
                                to=sender,
                                what=Response(type="files", name="content", args=args),
                            )
                        elif p1 > p2:
                            args = [
                                str(CWD().realpath / f"{f}{e}")
                                for f, e in self.files[p1 : p2 - 1 : -1]
                            ]
                            send(
                                to=sender,
                                what=Response(type="files", name="content", args=args),
                            )
                        else:
                            forward(
                                sender,
                                self.pid,
                                Request(type="files", name="content", args=[p1, None]),
                            )

                    case None:
                        args = [
                            str(CWD().realpath / f"{f}{e}") for f, e in self.files[1:]
                        ]
                        send(
                            to=sender,
                            what=Response(type="files", name="content", args=args),
                        )

                    case _:
                        send(
                            to="Display",
                            what=Event(
                                type="error",
                                name="bad-cmd",
                                args=f"Invalid selection: {args}",
                            ),
                        )
            case _:
                self.logger.warning(f"Unprocessable msg={msg}")
