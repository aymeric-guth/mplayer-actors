from collections import defaultdict


def get_kwargs(self) -> dict[str, str]:
    return {
        "path": tuple(self.path),
        "path_full": self.path_full,
        "dir_list": tuple(self.dirs),
        "len_dir": len(self.dirs),
        "files_list": tuple(self.files),
        "len_files": len(self.files),
    }
