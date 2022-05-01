import os
import time
from DisplayMatrix import *
import sys


def multiple_args(fnc):
    def inner(self, *args):
        return [ fnc(self, i[0], i[1], i[2]) for i in args ]
    return inner

class StringFormat(object):

    def __init__(self, **kwargs):

        self.format_terminal()
        self.path = kwargs.get('path')
        self.dir_list = kwargs.get('dir_list')
        self.len_dir = kwargs.get('len_dir')
        self.files_list = kwargs.get('files_list')
        self.len_files = kwargs.get('len_files')
        self.dir_unlisted = kwargs.get('dir_unlisted')
        self.files_unlisted = kwargs.get('files_unlisted')
        self.len_dir_unlisted = kwargs.get('len_dir_unlisted')
        self.len_files_unlisted = kwargs.get('len_files_unlisted')
        self.build_dir_object()
        self.template_screen()

    def build_dir_object(self):
        self.dir_object = []
        self.dir_object.append(self.standard_separator(*(' FOLDERS ', '-', 'half')))
        for i in range(1, self.len_dir):
            self.dir_object.append(self.standard_separator(*('', '-', 'half')))
            self.dir_object.append(self.format_line(i, self.dir_list[i]))
        self.dir_object.append(self.standard_separator(*('', '-', 'half')))
        #for i in self.dir_object:
        #    print(''.join(i))

    def build_files_object(self):
        self.files_object = []
        self.files_object.append(self.standard_separator(*(' FILES ', '-', 'half')))
        for i in range(1, self.len_files):
            #self.files_object.append(self.standard_separator(*('', '-', 'half')))
            self.files_object.append(self.format_line(i, self.files_list[i]))
        self.files_object.append(self.standard_separator(*('', '-', 'half')))


    def template_screen(self):
        mtx = DisplayMatrix()
        mtx.get_object_size(self.dir_object)
        mtx.feed_scene_matrix(*(66, 20))
        mtx.push_disp_matrix()
        mtx.refresh_display()

    def files_listing(self):
        #mtx = DisplayMatrix()
        for i in reversed(range(53, 60)):
            mtx = DisplayMatrix()
            mtx.get_object_size(self.dir_object)
            mtx.feed_scene_matrix(*(66, 20))
            mtx.get_object_size(self.files_object)
            mtx.feed_scene_matrix(*(66, i))
            mtx.push_disp_matrix()
            mtx.refresh_display()
            time.sleep(0.05)

    def insert_str(self, **kwargs):
        s = kwargs.get('s')
        y = kwargs.get('y')
        try:
            s2 = kwargs.get('s2')
        except:
            s2 = None

        len_s = len(s)
        if len_s > self.half_terminal:
            self.print_matrix[y][0] = s[:len_s]
            self.print_matrix[y][1] = s[len_s:]
        elif s2 == None:
            self.print_matrix[y][0] = s
            self.print_matrix[y][1] = ''
        else:
            self.print_matrix[y][0] = s
            self.print_matrix[y][1] = s2

    def display_matrix(self):
        len_mtx = len(self.print_matrix)
        for i in range(0, len_mtx):
            print(
                ''.join(self.print_matrix[i])
            )

    def template_screen_s(self):
        template_scrren = (
            (' ', ' ', 'full'),
            (' Current Working Directory: ', '-', 'full'),
            (f" ../{self.path[-1][:-1]} ", '-', 'full'),
            (' ', ' ', 'full'),
            (' FOLDERS ', '-', 'half'),
            (' FILES ', '-', 'half')
        )

    def default_print(self):
        self.standard_separator(
            (' ', ' ', 'full'),
            (' Current Working Directory: ', '-', 'full'),
            (f" ../{self.path[-1][:-1]} ", '-', 'full'),
            (' ', ' ', 'full'),
            (' FOLDERS ', '-', 'half')
        )

        for i in range(1, self.len_dir):
            self.format_line(i, self.dir_list[i])
            if i != self.len_dir - 1:
                self.standard_separator(
                    ('', '-', 'half'),
                )

        if self.len_files > 1:
            self.standard_separator(
                ('', '-', 'half'),
                ('', ' ', 'half'),
                (' FILES ', '-', 'half')
            )
            if self.len_files < 100:
                for i in range(1, self.len_files):
                    self.format_line(i, self.files_list[i])
            else:
                for i in range(1, self.len_files):
                    self.format_line(i, self.files_list[i], self.len_files)
            self.standard_separator(
                ('', '-', 'half'),
                ('', ' ', 'half')
            )

        if self.len_dir_unlisted != 0:
            if self.len_files_unlisted != 0:
                self.standard_separator(
                    (f" {self.len_dir_unlisted} Unlisted Folder(s) | {self.len_dir_unlisted} Unlisted File(s) ", '-', 'half'),
                    ('', ' ', 'half')
                )
            else:
                self.standard_separator(
                    (f" {self.len_dir_unlisted} Unlisted Folder(s) ", '-', 'half'),
                    ('', ' ', 'half')
                )
        elif self.len_files_unlisted != 0:
            self.standard_separator(
                (f" {self.len_dir_unlisted} Unlisted File(s) ", '-', 'half'),
                ('', ' ', 'half')
            )
        else:
            self.standard_separator(
                ('', '-', 'half'),
                ('', ' ', 'half')
            )

    #@multiple_args
    def standard_separator(self, *args):
        size_map = {
            'half': self.quarter_terminal,
            'full': self.half_terminal
        }
        text, symbol, dimension = args

        text = StringFormat.crop_text(text, size_map[dimension])
        len_text = len(text)
        separateur = ( symbol * (size_map[dimension] - int(len_text / 2)) )
        s = separateur + text + separateur
        len_s = len(s)
        if len_s > size_map[dimension] * 2:
            s = s[:-1]
        return s

    def format_line(self, s1, s2, max=99):
        if s1 < 10 and max < 100:
            s1 = '0' + str(s1)
        elif s1 < 10 and max >= 100:
            s1 = '00' + str(s1)
        elif s1 < 100 and max >= 100:
            s1 = '0' + str(s1)
        s = f"| {s1} | {s2}"
        size = self.half_terminal - len(s)
        if size > 0:
            s += ' ' * (size)
        else:
            s = StringFormat.crop_text(s, self.half_terminal)

        return s[:-1] + '|'

    def format_terminal(self):
        self.term_x, self.term_y = os.get_terminal_size(0)
        if self.crop_terminal():
            sys.stdout.write("\x1b[8;{rows};{cols}t".format(rows=self.term_y, cols=self.term_x))
            self.format_terminal()
        self.half_terminal = int(self.term_x / 2)
        self.quarter_terminal = int(self.term_x / 4)

    def crop_terminal(self):
        if self.term_x % 2 != 0:
            self.term_x -= 1
            return True
        if self.term_y %2 == 0:
            self.term_y -= 1
            return True
        return False

    @staticmethod
    def crop_text(s, max_len):
        evaluate_len = max_len - len(s)
        if evaluate_len < 0:
            s = s[:evaluate_len - 4] + '... '
        return s
