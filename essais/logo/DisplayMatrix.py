import time
import os
import random

def pseudo_center(func):
    def inner(self, *args, **kwargs):
        try:
            (x_l, y_l) = args
        except:
            x_l = 0
            y_l = 0
        try:
            center = kwargs.get('center')
            del kwargs['center']
        except:
            center = False
        if center:
            x_l += self.half_term_x - self.half_len_x_logo
            y_l += self.half_term_y - self.half_len_y_logo
        return func(self, *(x_l, y_l+1), **kwargs)
    return inner

class DisplayMatrix(object):

    def __init__(self, default_character=' '):

        self.term_x, self.term_y = os.get_terminal_size(0)
        self.half_term_x = int(self.term_x / 2)
        self.half_term_y = int(self.term_y / 2)
        self.default_character = default_character
        self.disp_matrix = [ [
            self.default_character for i in range(0, self.term_x)
            ]
                for i in range(0, self.term_y)
        ]
        self.animation_matrix = self.disp_matrix.copy()
        self.scene_matrix = [ [
            self.default_character for i in range(0, self.term_x*2)
            ]
                for i in range(0, self.term_y*2)
        ]
        self.scene_matrix_len_y = len(self.scene_matrix)
        self.scene_matrix_len_x = len(self.scene_matrix[0])
        self.disp_matrix_len_y = len(self.disp_matrix)
        self.disp_matrix_len_y = len(self.disp_matrix[0])

    def refresh_display(self):
        for i in self.disp_matrix:
            print(''.join(i))

    def offset_right(self):
        for i, j in enumerate(self.disp_matrix):
            self.disp_matrix[i].insert(0, self.disp_matrix[i][-1])
            self.disp_matrix[i].pop(-1)
        #self.disp_matrix.append(self.disp_matrix[i][:])
        #del self.disp_matrix[i][:]


    def colorize_display_matrix(self, value):
       for indice_y, value_y in enumerate(self.animation_matrix):
           for indice_x, value_x in enumerate(self.animation_matrix[indice_y]):
               self.disp_matrix[indice_y][indice_x] = (
                   value + self.disp_matrix[indice_y][indice_x] + '\033[0m'
               )

    def push_disp_matrix(self):
        for y in range(self.half_term_y, self.half_term_y + self.term_y):
            for x in range(self.half_term_x, self.half_term_x + self.term_x):
                offset_x = x - self.half_term_x
                offset_y = y - self.half_term_y
                self.disp_matrix[offset_y][offset_x] = self.scene_matrix[y][x]

    def get_object_size(self, logo):
        self.logo_matrix = logo
        self.len_x_logo = 0
        self.len_y_logo = len(self.logo_matrix)
        for indice, value in enumerate(self.logo_matrix):
            if len(value) > self.len_x_logo:
                self.len_x_logo = len(value)
        self.half_len_y_logo = int(self.len_y_logo / 2)
        self.half_len_x_logo = int(self.len_x_logo / 2)
        #print(
        #    'self.len_x_logo:',
        #    self.len_x_logo,
        #    'self.len_y_logo:',
        #    self.len_y_logo
        #)

    #@pseudo_center
    def feed_scene_matrix(self, *args, **kwargs):

        (x_l, y_l) = args
        flag = kwargs.get('flag')
        x_condition = x_l + self.len_x_logo
        y_condition = y_l + self.len_y_logo

        if x_l >= 0 and (x_condition - self.term_x*2 <= 0) and y_l >= 0 and (y_condition - self.term_y*2 <= 0):
            offset_x_l = x_l
            offset_x_r = x_condition
            offset_y_l = y_l
            offset_y_r = y_condition
        else:
            print(
                '\nx_l:', x_l, 'x_condition:', x_condition,
                '\ny_l:', y_l, 'y_condition:', y_condition
            )
            raise OverflowError

        for indice_y, value_y in enumerate(self.scene_matrix):
            for indice_x, value_x in enumerate(self.scene_matrix[indice_y]):
                x_condition = indice_x >= offset_x_l and indice_x < offset_x_r
                y_condition = indice_y >= offset_y_l and indice_y < offset_y_r

                if x_condition and y_condition:
                    y = indice_y - offset_y_l
                    x = indice_x - offset_x_l
                    if self.scene_matrix[indice_y][indice_x] != self.default_character and flag != True:
                        print('\nError, two or more objects overlap')
                        raise OverflowError
                    #print(indice_x, indice_y)
                    #print(x, y)
                    self.scene_matrix[indice_y][indice_x] = self.logo_matrix[y][x]
                #elif indice_y == 1 or indice_y == self.term_y - 1:
                #    self.disp_matrix[indice_y][indice_x] = '-'
                #elif indice_x == 0 or indice_x == self.term_x - 1:
                #    self.disp_matrix[indice_y][indice_x] = '|'
                elif indice_x > offset_x_r and indice_y > offset_y_r:
                    break

    @pseudo_center
    def feed_disp_matrix(self, *args, **kwargs):

        (x_l, y_l) = args
        flag = kwargs.get('flag')
        x_condition = x_l + self.len_x_logo
        y_condition = y_l + self.len_y_logo

        if x_l >= 0 and (x_condition - self.term_x <= 0) and y_l >= 0 and (y_condition - self.term_y <= 0):
            offset_x_l = x_l
            offset_x_r = x_condition
            offset_y_l = y_l
            offset_y_r = y_condition
        else:
            print(
                '\nx_l:', x_l, 'x_condition:', x_condition,
                '\ny_l:', y_l, 'y_condition:', y_condition
            )
            raise OverflowError

        for indice_y, value_y in enumerate(self.disp_matrix):
            for indice_x, value_x in enumerate(self.disp_matrix[indice_y]):
                x_condition = indice_x >= offset_x_l and indice_x < offset_x_r
                y_condition = indice_y >= offset_y_l and indice_y < offset_y_r

                if x_condition and y_condition:
                    y = indice_y - offset_y_l
                    x = indice_x - offset_x_l
                    if self.disp_matrix[indice_y][indice_x] != self.default_character and flag != True:
                        print('\nError, two or more objects overlap')
                        raise OverflowError
                    #print(indice_x, indice_y)
                    #print(x, y)
                    self.disp_matrix[indice_y][indice_x] = self.logo_matrix[y][x]
                #elif indice_y == 1 or indice_y == self.term_y - 1:
                #    self.disp_matrix[indice_y][indice_x] = '-'
                #elif indice_x == 0 or indice_x == self.term_x - 1:
                #    self.disp_matrix[indice_y][indice_x] = '|'
                elif indice_x > offset_x_r and indice_y > offset_y_r:
                    break
    def print_to_display(self):
        os.system('clear')
        for i in self.disp_matrix:
            print(''.join(i))
            #time.sleep(0.02)


def animated_logo():
    logo_matrix = [
        "        A R S               ",
        "       /\\\\\\\\              / ",
        "      /  \\\\\\\\            /  ",
        "     /    \\\\\\\\          /   ",
        "    /      \\\\\\\\        /    ",
        "   /        \\\\\\\\      /     ",
        "  /          \\\\\\\\    /      ",
        " /            \\\\\\\\  /       ",
        "/              \\\\\\\\/        ",
        "  V I R T U A L I S         ",
    ]

    text_matrix = [
        "    A U D I O",
        "             ",
        "  V I D E O  ",
        "             ",
        "P L A Y E R  ",
        "             ",
    ]

    for i in range(15, 232):
        logo = DisplayMatrix()
        logo.get_object_size(logo_matrix)
        logo.feed_disp_matrix(center=True)
        x = 0 + logo.len_x_logo
        logo.get_object_size(text_matrix)
        logo.feed_disp_matrix(*(x-12, 3), center=True)
        #value = random.choice(range(0, 256))
        value = f"\033[38;5;{i}m"
        logo.colorize_display_matrix(value)
        logo.print_to_display()
        time.sleep(0.1)

logo_matrix = [
    "        A R S               ",
    "       /\\\\\\\\              / ",
    "      /  \\\\\\\\            /  ",
    "     /    \\\\\\\\          /   ",
    "    /      \\\\\\\\        /    ",
    "   /        \\\\\\\\      /     ",
    "  /          \\\\\\\\    /      ",
    " /            \\\\\\\\  /       ",
    "/              \\\\\\\\/        ",
    "  V I R T U A L I S         ",
]
