import os
from mplayer_config import PATH, FILTER
from StringFormat import StringFormat

class Directory(object):

    def __init__(self, path=PATH):

        self.path = [ *path ]
        self.path_full = ''.join(self.path)
        self.dir_list = []
        self.files_list = []
        self.dir_unlisted = []
        self.files_unlisted = []

        with os.scandir(self.path_full) as dir_content:
            for i in dir_content:
                if i.is_file(follow_symlinks=False):
                    if self.filter_file(i.name):
                        self.files_list.append(i.name)
                    else:
                        self.files_unlisted.append(i.name)
                elif i.is_dir():
                    if self.files_or_dir_in_subdir(i.name):
                        self.dir_list.append(i.name)
                    else:
                        self.dir_unlisted.append(i.name)

        self.dir_list.sort()
        self.files_list.sort()
        self.dir_list.insert(0, 'Working Directory: ' + path[-1][:-1])
        self.files_list.insert(0, '')

        self.len_dir = len(self.dir_list)
        self.len_files = len(self.files_list)
        self.len_dir_unlisted = len(self.dir_unlisted)
        self.len_files_unlisted = len(self.files_unlisted)

        #self.dir_list.append(f'{self.len_dir_unlisted} Unlisted Folder(s)')
        #self.files_list.append(f'{self.len_files_unlisted} Unlisted File(s)')

    # ajouter un parametre depth qui rend la fonction recursive?
    def files_or_dir_in_subdir(self, sub_path):
        with os.scandir(self.path_full + sub_path) as dir_content:
            for i in dir_content:
                if i.is_dir() or (i.is_file() and self.filter_file(i.name)):
                    return True
                else:
                    continue
                return False

    def filter_file(self, file):
        for i in FILTER:
            if file.endswith(i):
                return True
            else:
                return False

    def default_print(self):
        os.system('clear')
        str_format = StringFormat(**self.get_cwd())
        #str_format.default_print()
        str_format.template_screen()

    def update_path(self, reference=None):
        if reference != None:
            path = self.path
            if reference != 0:
                sub_path = self.dir_list[reference]
                path.append(sub_path + '/')
            elif len(path) > 2:
                path.pop(-1)
            self.__init__(path)
        else:
            self.__init__(self.path)

    def get_cwd(self):
        kwargs = {
            'path': self.path,
            'path_full': self.path_full,
            'dir_list': self.dir_list,
            'len_dir': self.len_dir,
            'files_list': self.files_list,
            'len_files': self.len_files,
            'dir_unlisted': self.dir_unlisted,
            'files_unlisted': self.files_unlisted,
            'len_dir_unlisted': self.len_dir_unlisted,
            'len_files_unlisted': self.len_files_unlisted
        }
        return kwargs

    def scan_depth_and_update_database(self):
        pass
