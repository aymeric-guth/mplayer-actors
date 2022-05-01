import os
from mplayer_config import LOOP_DEFAULT, PURGE_TARGET

class ExecuteInput(object):

    def __init__(self, **kwargs):

        self.path = kwargs.get('path')
        self.path_full = kwargs.get('path_full')
        self.dir_list = kwargs.get('dir_list')
        self.files_list = kwargs.get('files_list')
        self.dir_unlisted = kwargs.get('dir_unlisted')
        self.files_unlisted = kwargs.get('files_unlisted')
        self.args = kwargs.get('args')
        self.len_args = kwargs.get('len_args')
        self.len_files = len(self.files_list)

        self.len_dir = kwargs.get('len_dir')
        self.files_list = kwargs.get('files_list')
        self.len_files = kwargs.get('len_files')
        self.len_dir_unlisted = kwargs.get('len_dir_unlisted')
        self.len_files_unlisted = kwargs.get('len_files_unlisted')
        self.str_f = kwargs.get('str_f')

    def print_files(self):
        self.str_f.build_files_object()
        self.str_f.files_listing()

    def print_unlisted(self):
        len_dir_unlisted = len(self.dir_unlisted)
        len_files_unlisted = len(self.files_unlisted)
        #print(f'\n{len_dir_unlisted} Unlisted Folders, and {len_files_unlisted} Unlisted Files')
        if len_dir_unlisted > 0:
            print(f'\n{len_dir_unlisted} Unlisted Folder(s)')
            for i in range(0, len_dir_unlisted):
                print(self.dir_unlisted[i])
        if len_files_unlisted > 0:
            print(f'\n{len_files_unlisted} Unlisted File(s)')
            for i in range(0, len_files_unlisted):
                print(self.files_unlisted[i])

    def play_files(self):
        try:
            counter = self.args[1]
        except:
            counter = LOOP_DEFAULT
        if self.len_args == None:
            playList = [ self.format_bash(i) for i in self.files_list ]
        else:
            playList = [ self.format_bash(self.files_list[self.args[0]]) for i in range(0, counter) ]
        for i in playList:
            os.system(f"mpg123 {i}")

    def purge(self):
        path = self.format_bash('/.purge')
        os.system(f"mkdir -p {path}")

        if self.len_args > 0:
            action = "mv {} {}"
            for i in self.args:
                source = self.format_bash(self.files_list[i])
                dest = self.format_bash('.purge/')
                os.system(action.format(source, dest))
                print(f"Purging {self.files_list[i]}.")
            return True
        else:
            action = ''
            if len(self.files_list) > 1:
                dir = f"''.join({PURGE_TARGET}){self.path[-1]}"
                dest = self.format_bash('', dir)
                for i in self.files_list:
                    source = self.format_bash(i)
                    action += "mv {} {};".format(source, dest)
                print(f"Purging {''.join(self.path)}.")
            action += "rm -rf {};".format(self.format_bash(''))
            #print(action)
            os.system(action)
            print(f"Purge done.\n")
            return False

    def format_bash(self, s, switch=None):
        if switch != None:
            file =  switch + s
        else:
            file =  self.path_full + s
        characters_to_escape = {
            ' ': '\ ',
            '(': '\(',
            ')': '\)',
            "'": "\\'",
            ':': '\:',
            '&': '\&'
        }
        len_str = len(file)
        s = ''
        for i in range(0, len_str):
            if file[i] in characters_to_escape:
                s += characters_to_escape[file[i]]
            else:
                s += file[i]
        return s

    def print_vars(self):
        print(self.__dict__)
