from collections import defaultdict


def initial_setup(extensions, data) -> None:
    files_tree = defaultdict(list)
    dir_tree = defaultdict(set)

    for r in data:
        path = r.get('path')
        file_name = r.get('filename')
        extension = r.get('extension')
        if extension not in extensions:
            continue
        formated_path = tuple( path.split('/')[1:-1] )
        files_tree[formated_path].append((file_name, extension))
        for i, v in enumerate(formated_path):
            key = formated_path[:i+1]
            dir_tree[key[:-1]].add(key[-1])

        return files_tree, dir_tree


def get_kwargs(self) -> dict[str, str]:
    return {
        "path": tuple(self.path),
        "path_full": self.path_full,
        "dir_list": tuple(self.dirs),
        "len_dir": len(self.dirs),
        "files_list": tuple(self.files),
        "len_files": len(self.files),
    }
