from typing import Any


def get_kwargs(self) -> dict[str, str|int|tuple[Any, ...]]:
    return {
        "path": self._path.path,
        "path_full": self._path.realpath,
        "dir_list": tuple(self.dirs),
        "len_dir": len(self.dirs),
        "files_list": tuple(self.files),
        "len_files": len(self.files),
    }
