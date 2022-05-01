from mplayer_data import VALID_INPUTS, SPECIAL_ACTIONS_KEYS, FORMAT_INPUT

class UserInput(object):

    def __init__(self, len_files, len_dir):
        self.input = input("> ")
        self.result = False
        self.len_files = len_files
        self.len_dir = len_dir
        self.parsed_input = tuple( [ self.test_input(i) for i in self.input.split() ] )
        self.keyword1 = None
        self.keyword2 = None
        self.args = None

        if self.parsed_input in VALID_INPUTS:
            self.input = tuple( [ int(i) if i.isdigit() else i for i in self.input.split() ] )
            if self.arg_parser():
                exec(f"{FORMAT_INPUT[self.parsed_input[0]]}")
                self.result = True
                self.output = (self.parsed_input[0], self.keyword1, self.keyword2, self.args)

    def test_input(self, key):
        if key.isdigit() and int(key) > 0:
            return 1
        elif key in SPECIAL_ACTIONS_KEYS:
            return SPECIAL_ACTIONS_KEYS[key]
        return 0

    def arg_parser(self):
        if self.parsed_input[0] == 1 and self.input[0] > self.len_dir - 1:
            return False
        elif self.parsed_input[0] == 3 and self.input[1] > self.len_files - 1:
            return False
        elif self.parsed_input[0] == 4:
            for i in self.input[1:]:
                if i > self.len_files - 1:
                    return False
        return True
