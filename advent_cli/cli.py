import argparse
from datetime import datetime as dt

from . import commands
from . import config
from ._version import __version__
from .utils import CustomHelpFormatter


def main():
    parser = argparse.ArgumentParser(formatter_class=CustomHelpFormatter)
    parser.add_argument(
        '-v', '--version',
        action='version',
        version=f'advent-cli {__version__}'
    )
    command_subparsers = parser.add_subparsers(
        dest='command', description='use advent {subcommand} --help for arguments'
    )
    parser_get = command_subparsers.add_parser(
        'get',
        help='download prompt and input, generate solution template',
        formatter_class=CustomHelpFormatter
    )
    parser_get.add_argument(
        'date',
        help='the year and day in YYYY/DD format (e.g. "2021/01")'
    )
    parser_get.add_argument(
        '-p','--propmt',
        dest='prompt',
        action='store_true',
        help='get the propmt only for the specified day'
    )
    parser_stats = command_subparsers.add_parser(
        'stats',
        help='show personal stats or private leaderboards',
        formatter_class=CustomHelpFormatter
    )
    parser_stats.add_argument(
        'year',
        nargs='?',
        default=dt.now().year,
        help='year to show stats for, defaults to current year'
    )
    parser_stats.add_argument(
        '-p', '--private',
        dest='show_private',
        action='store_true',
        help='show private leaderboard(s)'
    )
    parser_test = command_subparsers.add_parser(
        'test',
        help='run solution and output answers without submitting',
        formatter_class=CustomHelpFormatter
    )
    parser_test.add_argument(
        'date',
        help='the year and day in YYYY/DD format (e.g. "2021/01")'
    )
    parser_test.add_argument(
        '-e', '--example',
        dest='run_example',
        action='store_true',
        help='use example_input.txt for input'
    )
    parser_test.add_argument(
        '-p', '--print',
        dest='print_output',
        default=False,
        action='store_true'
    )
    parser_test.add_argument(
        '-f', '--solution-file',
        dest='solution_file',
        default='main{day}{ext}',
        help='solution file to run instead of solution.py\n'
             '(e.g. "solution2" for solution2.py)'
    )
    parser_submit = command_subparsers.add_parser(
        'submit',
        help='run solution and submit answers',
        formatter_class=CustomHelpFormatter
    )
    parser_submit.add_argument(
        'date',
        help='the year and day in YYYY/DD format (e.g. "2021/01")'
    )
    parser_submit.add_argument(
        '-f', '--solution-file',
        dest='solution_file',
        default='solution',
        help='solution file to run instead of solution.py\n'
             '(e.g. "solution2" for solution2.py)\n'
             '*only works if answers not yet submitted*'
    )
    parser_countdown = command_subparsers.add_parser(
        'countdown',
        help='display countdown to puzzle unlock',
        formatter_class=CustomHelpFormatter
    )
    parser_countdown.add_argument(
        'date',
        help='the year and day in YYYY/DD format (e.g. "2021/01")'
    )
    parser_run = command_subparsers.add_parser(
        'run',
        help='shows the config'
    )
    parser_run.add_argument(
        'date',
        help='the year and day in YYYY/DD format (e.g. "2021/01")'
    )
    parser_run.add_argument(
        '-p', '--print',
        dest='printfullout',
        default=False,
        help='weather to print the full output from the code',
        action='store_const',
        const=True
    
    )
    parser_info = command_subparsers.add_parser(
        'info',
        help='show all stored variable in the config.ini'
    )
    parser_priv = command_subparsers.add_parser(
        'private'
    )
    parser_priv.add_argument(
        'year'
    )
    
    args = parser.parse_args()
    print("AOC CLI for c++")
    if args.command == 'get':
        
        year, day = args.date.split('/')
        commands.get(year, day,args.prompt)

    elif args.command == 'stats':
        if args.show_private:
            commands.private_leaderboards_json(args.year)
        else:
            commands.stats(args.year)

    elif args.command == 'test':
        year, day = args.date.split('/')
        commands.test(year, day, solution_file=args.solution_file, example=args.run_example, print_output=args.print_output)

    elif args.command == 'submit':
        year, day = args.date.split('/')
        commands.submit(year, day, solution_file=args.solution_file)

    elif args.command == 'countdown':
        year, day = args.date.split('/')
        commands.countdown(year, day)
    elif args.command == 'run':
        printfull = args.printfullout
        print(printfull)
        year, day = args.date.split('/')
    elif args.command == 'info':
        
        conf = config.get_local_config()
        print("printing config settings")
        for options,values in conf['local'].items():
            print(options,values,sep=": ")
    elif args.command == 'private':
        commands.private_leaderboards_json(args.year)
        
        
    
