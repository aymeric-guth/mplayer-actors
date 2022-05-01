from UserInput import UserInput
#from ErrorsHandler import *
# from Directory import Directory
# from ExecuteInput import ExecuteInput
# from mplayer_data import SPECIAL_ACTIONS, REFRESH_LIST, HELP
from DisplayMatrix import *
# from StringFormat import *

# def execution_branching(*args):
#     flag, keyword1, keyword2, args = args
#     try:
#         if type(args) != int:
#             len_args = len(args)
#         else:
#             len_args = 1
#     except:
#         len_args = None

#     if keyword2 != None:
#         print(SPECIAL_ACTIONS[keyword1][keyword2])
#     else:
#         action = f"{SPECIAL_ACTIONS[keyword1]}"
#         kwargs = dir.get_cwd()
#         str_f = StringFormat(**kwargs)
#         kwargs.update( [('args', args), ('len_args', len_args), ('str_f', str_f)] )
#         exe = ExecuteInput(**kwargs)
#         exec(action)

#     if keyword1 in REFRESH_LIST:
#         return True
#     return False

if __name__ == "__main__":

    # refresh_flag = True
    # dir = Directory()
    animated_logo()

    # while True:
    #     if refresh_flag:
    #         dir.default_print()
    #     # ecrire une liste avec tous les bad input pour tester la logique
    #     user_input = UserInput(dir.len_files, dir.len_dir)
    #     if user_input.result:
    #         print('\nINPUT: ', user_input.output)
    #         refresh_flag = execution_branching(*user_input.output)
    #     else:
    #         print("\nBad input. Type 'help' or 'help keyword'")
    #         print(user_input.parsed_input)
    #         refresh_flag = False
    #         continue
