import argparse
import markdownify
import os
import re as re
import requests
import sys
import pytz
import subprocess

from datetime import datetime as dt
from enum import Enum
from gettext import gettext
from importlib import import_module
from math import ceil
from termcolor import colored as tc_colored

from . import config


class Status(Enum):
    PASS = 0
    FAIL = 1
    RATE_LIMIT = 2
    COMPLETED = 3
    NOT_LOGGED_IN = 4
    UNKNOWN = 5


def colored(text, color):
    if bool(int(config.get_local_config()['local']['disable_color'])):
        if text == '*':
            if color == 'cyan':
                return '/'
            elif color == 'grey':
                return '.'
        return text
    else:
        return tc_colored(text, color)

    
    
def compute_answers(year, day, solution_file='solution', example=False, printFullOut:bool=False):
    currentdir = os.getcwd()
    day = f"{int(day):02d}"
    conf = config.get_local_config()
    cmd = str(conf['local']['compile_cmd'])
    ext = str(conf['local']['file_ext'])
    outext = str(conf['local']['out_ext'])
    filename = f"main{day}"
    runcmd = str(conf['local']['run_cmd']).replace('{filename}',filename).replace('{ext}',ext).replace('{out_ext}',outext)
    cmd = cmd.replace('{filename}',filename).replace('{ext}',ext).replace('{out_ext}',outext)
    # ext = ".cpp"
    if not os.path.exists(os.path.join(currentdir,year,day,filename+ext)):
        
        print(f"File {filename+ext} does not exist")
        print("Be sure to be in the directory that contains the years folders")
        exit(0)
    
    print(colored(f"compiling \'{filename+ext}\' with:",'green'))
    print(f"\'{cmd=}\'")
    print(f"Running \'{filename+ext}\' with: \'{runcmd}\'")
    lastdir = os.getcwd()
    filepath = os.path.join(currentdir,year,day)
    os.chdir(filepath)
    p = subprocess.Popen(cmd.split(" "))
    p.communicate()
    if example:
        runcmd += " example_input.txt"
    else:
        runcmd += " input.txt"
    output = subprocess.Popen(runcmd.split(' '), stdout=subprocess.PIPE).communicate()[0].decode()
    
    os.chdir(lastdir)
    lines = output.splitlines()
    part1_answer = None
    part2_answer = None
    for line in lines:
        if printFullOut:
            print(line)
        line = line.lower()
        part = line.find("part")
        colon = line.find(":")
        if part != -1 and colon != -1:
            if '1' in line[part:colon]:
                part1_answer = line[colon+1:]
            elif '2' in line[part:colon]:
                part2_answer = line[colon+1:]
            
        
        
    if part1_answer is not None:
        print(f"{part1_answer= }")
    if part2_answer is not None:
        print(f"{part2_answer= }")
    return part1_answer,part2_answer


def submit_answer(year, day, level, answer):
    payload = {'level': level, 'answer': answer}
    print("post request")
    r = requests.post(
        f'https://adventofcode.com/{year}/day/{int(day)}/answer',
        data=payload,
        cookies={'session': config.get_local_config()['local']['session_cookie']}
    )
    response = r.text
    if "That's the right answer" in response:
        return Status.PASS, None
    elif "That's not the right answer" in response:
        return Status.FAIL, None
    elif 'You gave an answer too recently' in response:
        return Status.RATE_LIMIT, None
    elif 'Did you already complete it?' in response:
        return Status.COMPLETED, None
    elif '[Log In]' in response:
        return Status.NOT_LOGGED_IN, None
    else:
        return Status.UNKNOWN, response


def get_time_until_unlock(year, day):
    est = pytz.timezone('EST')
    unlock_time = est.localize(dt(int(year), 12, int(day)))
    delta = ceil((unlock_time - dt.now().astimezone(est)).total_seconds())
    minutes, seconds = divmod(delta, 60)
    hours, minutes = divmod(minutes, 60)
    return hours, minutes, seconds


# class to override default argparse formatter, because I don't think it looks very nice
# adapted from:
# https://github.com/python/cpython/blob/bffce2cbb5543bc63a67e33ad599328a12f2b00a/Lib/argparse.py#L154
class CustomHelpFormatter(argparse.RawTextHelpFormatter):

    class _Section(argparse.HelpFormatter._Section):
        # make section headings purple
        def __init__(self, formatter, parent, heading=None):
            if heading is not None:
                heading = colored(heading, 'magenta')
            super().__init__(formatter, parent, heading=heading)

    # add newlines to beginning and end
    def format_help(self):
        return f'\n{super().format_help()}\n'

    # make "usage:" purple
    def _format_usage(self, usage, actions, groups, prefix):
        return super()._format_usage(
            usage, actions, groups,
            colored(gettext('usage: '), 'magenta') if prefix is None else prefix
        )

    # make arguments yellow
    def _format_action(self, action):
        return re.sub(r'(\-[a-zA-Z\-]+(\s)?([a-zA-Z_]+)?)', colored(r'\1', 'yellow'),
                      re.sub(r'(\s\s[a-zA-Z]+\s\s)', colored(r'\1', 'yellow'),
                             super()._format_action(action)))


class CustomMarkdownConverter(markdownify.MarkdownConverter):

    def __init__(self, md_em, **options):
        self.md_em = md_em
        super().__init__(**options)

    def convert_em(self, el, text, convert_as_inline):
        if el.parent.name == 'code':
            if self.md_em == 'ib':
                return f'<i><b>{text}</b></i>'
            elif self.md_em == 'mark':
                return f'<mark>{text}</mark>'
            elif self.md_em == 'none' or self.md_em == '':
                return text
        return super().convert_em(el, text, convert_as_inline)

    def convert_code(self, el, text, convert_as_inline):
        if self.md_em in ['ib', 'mark']:
            return f'<code>{text}</code>'
        return super().convert_code(el, text, convert_as_inline)

    def convert_pre(self, el, text, convert_as_inline):
        if self.md_em in ['ib', 'mark']:
            return f'\n<pre>{text}</pre>\n'
        return super().convert_pre(el, text, convert_as_inline)


def custom_markdownify(html, **options):
    return CustomMarkdownConverter(config.get_local_config()['local']['md_em'], **options).convert(html)
