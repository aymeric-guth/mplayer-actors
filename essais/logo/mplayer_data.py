HELP = {
    'play': 'plays all files in current folder.',
    'loop': 'takes 2 integer arguments X and Y,\nplays X file Y times,\nLOOP_DEFAULT in Y is not provided.',
    'purge':
"""
takes integer arguments,
moves target FILES to .purge,
if no arguments are provided deletes .purge
'purge -'
purges unlisted files in cwd
'purge - args'
purges all FILES except args
""",
    'list': 'lists all FILES in cwd.',
    'pwd': 'prints working directory.',
    'root': 'goto root directory (PATH).',
    'exit': 'exit and returns 0.'
}

SPECIAL_ACTIONS = {
    '..': "dir.update_path(0)",
    'cd': "dir.update_path(args)",
    'play': "exe.play_files()",
    'root': "dir.update_path()",
    'pwd': "print(dir.path_full)",
    'list': "exe.print_files()",
    'unlisted': "exe.print_unlisted()",
    'switcharoo': 'exe.print_vars()',
    'loop': "exe.play_files()",
    'purge':
"""
if len(dir.path) < 3:
    print("Error, cannot purge at root level!")
else:
    if exe.purge():
        dir.update_path()
    else:
        dir.update_path(0)
""",
# purge all : rm -rf cwd
# purge - purges all except target files
    #'purge': "if exe.purge():\n\tdir.update_path()\nelse:\n\tdir.update_path(0);",
    'exit': "sys.exit(0)",
    'clear': "os.system('clear')",
    'help': {
        'play': HELP['play'],
        'loop': HELP['loop'],
        'purge': HELP['purge'],
        'list': HELP['list'],
        'pwd': HELP['pwd'],
        'root': HELP['root'],
        'exit': HELP['exit']
    },
}
# 'convert': "converts folder in mp3 bitrate and metadata in config and deletes files after"

REFRESH_LIST = (
    'cd',
    '..',
    'root',
    'purge'
)

SPECIAL_ACTIONS_KEYS = {
    '..': 2,
    'play': 2,
    'pwd': 2,
    'root': 2,
    'clear': 2,
    'list': 2,
    'unlisted': 2,
    'switcharoo': 2,
    'exit': 2,
    'help': 5,
    'loop': 3,
    'purge': 4
}

VALID_INPUTS = (
    (1,), # basic 1 int
    (2,), # one key-word
    # one key-word and 1 or 2 int arguments
    (3, 1), (3, 1, 1), # loop : one key-word multiple int argument(s)
    # one key-word and/or multiple int arguments
    (4,), (4, 1), (4, 1, 1), (4, 1, 1, 1), (4, 1, 1, 1, 1), # purge : one key-word multiple int argument(s)
    # ( (4,), (*args) )
    # type(args) == int()
    # one or two key-words
    (5, 2), (5, 3), (5, 4) # help : two key-word(s)
)

FORMAT_INPUT = {
    1: "self.keyword1 = 'cd'; self.args = (self.input[0])",
    2: "self.keyword1 = self.input[0]",
    3: "self.keyword1 = self.input[0]; self.args = self.input[1:]",
    4: "self.keyword1 = self.input[0]; self.args = self.input[1:]",
    5: "self.keyword1 = self.input[0]; self.keyword2 = self.input[1]"
}

LOGO = (
"""
        A R S
       /\\\\\\\\ / / / / / / / /
      / /\\\\\\\\ / / / / / / /
     / / /\\\\\\\\ / / / / / /  A U D I O
    / / / /\\\\\\\\ / / / / /
   / / / / /\\\\\\\\ / / / /  V I D E O
  / / / / / /\\\\\\\\ / / /
 / / / / / / /\\\\\\\\ / /  P L A Y E R
/ / / / / / / /\\\\\\\\ /
   V I R T U A L I S
"""
)
