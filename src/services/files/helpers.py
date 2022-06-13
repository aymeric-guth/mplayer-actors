from typing import Any
from ._types import CWD


def get_kwargs(self) -> dict[str, str|int|tuple[Any, ...]]:
    return {
        "path": CWD().path,
        # "path_full": CWD().realpath,
        "dir_list": tuple(self.dirs),
        "len_dir": len(self.dirs),
        "files_list": tuple(self.files),
        "len_files": len(self.files),
    }
