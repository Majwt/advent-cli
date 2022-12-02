import os
import sys
from termcolor import colored
from configparser import ConfigParser


# def get_config():

#     config = {}

#     if 'ADVENT_PRIV_BOARDS' in os.environ:
#         config['private_leaderboards'] = os.environ['ADVENT_PRIV_BOARDS'].split(',')
#     else:
#         config['private_leaderboards'] = []

#     if 'ADVENT_DISABLE_TERMCOLOR' in os.environ:
#         config['disable_color'] = (os.environ['ADVENT_DISABLE_TERMCOLOR'] == '1')
#     else:
#         config['disable_color'] = False

#     if 'ADVENT_MARKDOWN_EM' in os.environ:
#         config['md_em'] = os.environ['ADVENT_MARKDOWN_EM']
#     else:
#         config['md_em'] = 'default'

#     if 'ADVENT_SESSION_COOKIE' in os.environ:
#         config['session_cookie'] = os.environ['ADVENT_SESSION_COOKIE']
#     else:
#         print("test old")
#         # this is to avoid importing colored() from utils.py, resulting in a circular import
#         error_message = ('Session cookie not set.\nGrab your AoC session cookie from a browser'
#                          ' and store it in an environment variable ADVENT_SESSION_COOKIE.')
#         if not config['disable_color']:
#             error_message = '\n'.join([colored(s, 'red') for s in error_message.split('\n')])
#         print(error_message)
#         sys.exit(1)

#     return config

def get_local_config():
    Config = ConfigParser()
    
    if os.path.isfile(os.path.expanduser('~/.aoc-cfg/config.ini')):
        Config.read(os.path.expanduser("~/.aoc-cfg/config.ini"))
        if Config['local']['session_cookie'] == '':
            error_message = ('Session cookie not set.\nGrab your AoC session cookie from a browser'
                         ' and store it in the config file at ~/.aoc-cfg/config.ini')
            print(error_message)
            sys.exit(1)
        if Config['local']['compile_cmd'] == '':
            error_message = ('Compile command not set.\nSet the compile command in the config file at ~/.aoc-cfg/config.ini')
            print(error_message)
            sys.exit(1)
        if Config['local']['file_ext'] == '':
            error_message = ('File extension not set.\nSet the file extension in the config file at ~/.aoc-cfg/config.ini')
            print(error_message)
            sys.exit(1)
        if Config['local']['out_ext'] == '':
            error_message = ('Output extension not set.\nSet the output extension in the config file at ~/.aoc-cfg/config.ini')
            print(error_message)
            sys.exit(1)
        if Config['local']['run_cmd'] == '':
            error_message = ('Run command not set.\nSet the run command in the config file at ~/.aoc-cfg/config.ini')
            print(error_message)
            sys.exit(1)
        
        
        return Config
    else:
        with open(os.path.expanduser("~/.aoc-cfg/config.ini"),'w') as f:
            Config['local'] = {}
            
            Config['local']['session_cookie'] = ''
            Config['local']['compile_cmd'] = 'g++ {filename}{ext} -o {filename}{out_ext}'
            Config['local']['run_cmd'] = './{filename}'
            Config['local']['out_ext'] ='.exe'
            Config['local']['file_ext'] = '.cpp'
            Config['local']['md_em'] = 'default'
            Config['local']['disable_color'] = ''
            Config['local']['private_leaderboards'] = ''
            
            
            Config.write(f)
            sys.exit(1);
    
if __name__ == "__main__":
    get_local_config()