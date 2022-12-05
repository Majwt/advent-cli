import curses
import os
import pytz
import re
import requests
import sys
import time

from bs4 import BeautifulSoup
from datetime import datetime as dt
from datetime import timedelta
from tabulate import tabulate
import json
from . import config
from .utils import (
    colored,
    compute_answers,
    custom_markdownify,
    get_time_until_unlock,
    submit_answer,
    Status
)
headers = {
    'User-Agent': 'https://github.com/Majwt/advent-cli by theodor.wase@icloud.com'
}

def get(year, day:str,promptonly:bool):
    dayfilled = day.zfill(2)
        
    if not promptonly:
        if os.path.exists(f'{year}/{dayfilled}/'):
            print(colored('Directory already exists:', 'red'))
            print(colored(f'  {os.getcwd()}/{year}/{dayfilled}/', 'red'))
            return
        
        os.makedirs(f'{year}/{dayfilled}/')
    conf = config.get_local_config()
    print(conf['local']['session_cookie'])
    print("post request")
    r = requests.get(f'https://adventofcode.com/{year}/day/{int(day)}',
                     cookies={'session': conf['local']['session_cookie']},headers=headers)
    if r.status_code == 404:
        if 'before it unlocks!' in r.text:
            print(colored('This puzzle has not unlocked yet.', 'red'))
            print(colored(f'It will unlock on Dec {day} {year} at midnight EST (UTC-5).',
                          'red'))
            print(colored(f'Use "advent countdown {year}/{day}" to view a live countdown.',
                          'grey'))
            return
        else:
            print(colored('The server returned error 404 for url:', 'red'))
            print(colored(f'  "https://adventofcode.com/{year}/day/{int(day)}/"', 'red'))
            return
    elif '[Log In]' in r.text:
        print(colored('Session cookie is invalid or expired.', 'red'))
        return

    soup = BeautifulSoup(r.text, 'html.parser')
    parts_html = soup.find_all('article', class_='day-desc')
    parts_str = []
    parts_str.clear()
    for part in parts_html:
        s = part.decode_contents()
        
        # remove hyphens from title sections, makes markdown look nicer
        s = re.sub('--- (.*) ---', r'\1', s)
        # also makes markdown look better
        s = s.replace('\n\n', '\n')
        parts_str.append(s)

    with open(f'{year}/{dayfilled}/prompt.md', 'w') as f:
        pass

    with open(f'{year}/{dayfilled}/prompt.md', 'a') as f:
        for part in parts_str:
            f.write(custom_markdownify(part))
            
    print(f'Downloaded prompt to {year}/{dayfilled}/prompt.md')
    if promptonly:
        return
    print("post request")
    r = requests.get(f'https://adventofcode.com/{year}/day/{int(day)}/input',
                     cookies={'session': conf['local']['session_cookie']},headers=headers)
    with open(f'{year}/{dayfilled}/input.txt', 'w') as f:
        f.write(r.text)
    print(f'Downloaded input to {year}/{dayfilled}/input.txt')

    open(f'{year}/{dayfilled}/example_input.txt', 'w').close()
    print(f'Created {year}/{dayfilled}/example_input.txt')

    with open(f'{year}/{dayfilled}/main{dayfilled}.cpp', 'w') as f:
        f.write(f'// advent of code {year}\n'
                f'// https://adventofcode.com/{year}\n'
                f'// day {dayfilled}\n\n'
                '#include <iostream>\n\n'
                'int main()\n{\n\n    printf(\"hello World!\");\n\n}'
                )
    print(f'Created {year}/{dayfilled}/main{dayfilled}.cpp')


def stats(year):
    print(colored("stats",'red'))
    today = dt.today()
    if today.year <= int(year) and today.month < 12:
        print(colored(f'Defaulting to previous year ({today.year - 1}).', 'red'))
        year = str(today.year - 1)

    conf = config.get_local_config()
    print("Don't use this command too often, it's not cached")
    r = requests.get(f'https://adventofcode.com/{year}/leaderboard/self',
                     cookies={'session': conf['local']['session_cookie']},headers=headers)
    if '[Log In]' in r.text:
        print(colored('Session cookie is invalid or expired.', 'red'))
        return

    soup = BeautifulSoup(r.text, 'html.parser')

    table = soup.select('article pre')[0].text
    table_rows = [x.split() for x in table.split('\n')[2:-1]]

    stars_per_day = [0] * 25
    for row in table_rows:
        stars_per_day[int(row[0]) - 1] = 2 if row[4:7] != ['-', '-', '-'] \
                                           else 1 if row[1:4] != ['-', '-', '-'] \
                                           else 0

    print('\n         1111111111222222\n1234567890123456789012345')

    today = dt.now(pytz.timezone('America/New_York'))
    for i, stars in enumerate(stars_per_day):
        if stars == 2:
            print(colored('*', 'yellow'), end='')
        elif stars == 1:
            print(colored('*', 'cyan'), end='')
        elif stars == 0 and today.year == int(year) and today.day < (i + 1):
            print(' ', end='')
        else:
            print(colored('*', 'grey'), end='')

    print(f" ({sum(stars_per_day)}{colored('*', 'yellow')})\n")
    print(f'({colored("*", "yellow")} 2 stars) '
          f'({colored("*", "cyan")} 1 star) '
          f'({colored("*", "grey")} 0 stars)\n')

    print(tabulate(table_rows, stralign='right', headers=[
        '\nDay',
        *['\n'.join([colored(y, 'cyan') for y in x.split('\n')])
            for x in ['----\nTime', '(Part 1)\nRank', '----\nScore']],
        *['\n'.join([colored(y, 'yellow') for y in x.split('\n')])
            for x in ['----\nTime', '(Part 2)\nRank', '----\nScore']]
    ]), '\n')

    if conf['local']['private_leaderboards'].split(','):
        num_private_leaderboards = len(conf['local']['private_leaderboards'].split(','))
        print(colored(f'You are a member of {num_private_leaderboards} '
                      f'private leaderboard(s).', 'grey'))
        print(colored(f'Use "advent stats {year} --private" to see them.\n', 'grey'))


def private_leaderboard_stats(year):
    print("Private leaderboards")
    today = dt.today()
    if today.year <= int(year) and today.month < 12:
        print(colored(f'Defaulting to previous year ({today.year - 1}).', 'red'))
        year = str(today.year - 1)

    conf = config.get_local_config()
    pLeaderBoards = conf['local']['private_leaderboards'].split(',')
    
    if pLeaderBoards:
        for board_id in pLeaderBoards:
            board_id = int(board_id.strip())
            print(conf['local']['session_cookie'])
            print(f'https://adventofcode.com/{year}/leaderboard/private/view/{board_id}')
            r = requests.get(
                f'https://adventofcode.com/{year}/leaderboard/private/view/{board_id}',
                cookies={'session': conf['local']['session_cookie']},
                headers=headers
            )
            if '[Log In]' in r.text:
                print(colored('Session cookie is invalid or expired.', 'red'))
                return
            print(r.text)
            soup = BeautifulSoup(r.text, 'html.parser')
            l = re.findall(r'private leaderboard of (.*) for', soup.main.article.p.text)
            
            board_owner = 'Unknown'
            # with open("html.txt",'w') as f:
            #     f.write(soup)
            if len(board_owner) >=1:
                board_owner = l[0]
            # board_owner = soup.find('div', class_='user').contents[0].strip() \
            #     if 'This is your' in intro_text \
            #     else re.findall(r'private leaderboard of (.*) for', intro_text)[0]

            rows = soup.find_all('div', class_='privboard-row')[1:]
            top_score_len = len(rows[0].find_all(text=True, recursive=False)[0].strip())
            print(f"\n{board_owner}'s private leaderboard {colored(f'({board_id})', 'grey')}")
            print(f'\n{" "*(top_score_len+14)}1111111111222222'
                  f'\n{" "*(top_score_len+5)}1234567890123456789012345')
            

            for row in rows:
                position = row.find('span', class_='privboard-position').text
                if len(position) == 2:
                    position = " " + position
                stars = row.find_all('span', class_=re.compile('privboard-star-*'))
                name = row.find('span', class_='privboard-name').text
                name_link = row.select('.privboard-name a')[0].attrs['href'] \
                    if len(row.select('.privboard-name a')) else None
                score = row.find_all(text=True, recursive=False)[0].strip()

                print(f'{position} {score:>{top_score_len}}', end=' ')
                for span in stars:
                    class_ = span.attrs['class'][0]
                    if 'both' in class_:
                        print(colored('*', 'yellow'), end='')
                    elif 'firstonly' in class_:
                        print(colored('*', 'cyan'), end='')
                    elif 'unlocked' in class_:
                        print(colored('*', 'grey'), end='')
                    elif 'locked' in class_:
                        print(' ', end='')

                print(f' {name}', end=' ')
                print(f'({colored(name_link.split("//")[-1], "blue")})' if name_link is not None else '')

            print()
            print(f'({colored("*", "yellow")} 2 stars) '
                  f'({colored("*", "cyan")} 1 star) '
                  f'({colored("*", "grey")} 0 stars)\n')
    else:
        print(colored('You are not a member of any private leaderboards '
                      'or you have not configured them.', 'red'))
        print(colored('Set the environment variable ADVENT_PRIV_BOARDS to '
                      'a comma-separated list of private leaderboard IDs.', 'red'))

def updateLeaderboardCache(year,board_id):
    conf = config.get_local_config()
    print("post request")
    r = requests.get(
                f"https://adventofcode.com/{year}/leaderboard/private/view/{board_id}.json",
                cookies={'session': conf['local']['session_cookie']},
                headers=headers
            ).json()
    r['last_access'] = dt.timestamp(dt.now())
    with open(f"{os.path.expanduser('~/.aoc-cfg')}/private_leaderboard_{year}_{board_id}.json", 'w') as f:
        f.write(json.dumps(r, indent=4))
        

def private_leaderboards_json(year):
    print("Private leaderboards")
    today = dt.today()
    if today.year <= int(year) and today.month < 12:
        print(colored(f'Defaulting to previous year ({today.year - 1}).', 'red'))
        year = str(today.year - 1)

    conf = config.get_local_config()
    pLeaderBoards = conf['local']['private_leaderboards'].split(',')
    if len(pLeaderBoards) < 1:
        print(colored('You are not a member of any private leaderboards '
                      'or you have not configured them.', 'red'))
        print(colored('Set the environment variable ADVENT_PRIV_BOARDS to '
                      'a comma-separated list of private leaderboard IDs.', 'red'))
        return
    board_id = pLeaderBoards[0].strip()
    if not os.path.exists(f"{os.path.expanduser('~/.aoc-cfg')}/private_leaderboard_{year}_{board_id}.json"):
        with open(f"{os.path.expanduser('~/.aoc-cfg')}/private_leaderboard_{year}_{board_id}.json", 'w') as f:
            f.write("")
            
    with open(f"{os.path.expanduser('~/.aoc-cfg')}/private_leaderboard_{year}_{board_id}.json", 'r') as f:
        string = f.read()
        if os.path.getsize(f"{os.path.expanduser('~/.aoc-cfg')}/private_leaderboard_{year}_{board_id}.json") > 0:
            r = json.loads(string)
            
            dt.timestamp(dt.utcnow())
            min_age = 60*60
            if 'last_access' not in r or ('last_access' in r and dt.timestamp(dt.now()) - r['last_access'] > min_age):
                updateLeaderboardCache(year,board_id)
                f.close()
                with open(f"{os.path.expanduser('~/.aoc-cfg')}/private_leaderboard_{year}_{board_id}.json", 'r') as f2:
                    r = json.loads(f2.read())
            else:
                
                current_td = timedelta(seconds=min_age - round(timedelta(seconds=abs(dt.timestamp(dt.now())-r['last_access'])).total_seconds()))
                
                print(f"cache is still valid for {current_td}")
        else:
            updateLeaderboardCache(year,board_id)
            print("cache was empty, try again")
            return
    
    owner_id = str(r['owner_id'])
    owner_name = 'Unknown'
    if owner_id in r['members']:
        owner_name = r['members'][owner_id]['name']
    members = [r['members'][x] for x in r['members']]
    
    top_score_len = len(str(r['members'][owner_id]['stars']))
    print_leaderboard(members, owner_name,board_id,top_score_len)
    

def print_leaderboard(members,owner_name,board_id,top_score_len):
    members.sort(key=lambda x: x['local_score'], reverse=True)    
    print(f"\n{owner_name}'s private leaderboard {colored(f'({board_id})', 'grey')}")
    print(f'\n{" "*(top_score_len+14)}1111111111222222'
          f'\n{" "*(top_score_len+5)}1234567890123456789012345')
    for i,member in enumerate(members):
        position = f"  {i})" if len(str(i)) == 1 else f"{i}) {members[member]['local_score']}"
        print(f'{position}', end='  ')
        for day in range(1,26):
            if str(day) in member['completion_day_level']:
                class_ = len(member['completion_day_level'][str(day)])
                if class_ == 2:
                    print(colored('*', 'yellow'), end='')
                elif class_ == 1:
                    print(colored('*', 'cyan'), end='')
                elif class_ == 0:
                    print(colored('*', 'grey'), end='')
            else:
                print(' ', end='')
        id = f'({member["id"]})'
        
        print(f' {member["name"]} {colored(id, "grey")}')
    print(f'({colored("*", "yellow")} 2 stars) '
            f'({colored("*", "cyan")} 1 star) '
            f'({colored("*", "grey")} 0 stars)\n')

def test(year, day, solution_file='main{day}{ext}', example=False, print_output=False):
    conf = config.get_local_config()
    ext = conf['local']['file_ext']
    day = int(day)
    if solution_file == 'main{day}{ext}':
        solution_file = f'main{day:02d}{ext}'
    print(f'Testing {solution_file}...')
    if not os.path.exists(f'{os.getcwd()}/{year}/{day:02d}/'):
        print(colored('Directory does not exist:', 'red'))
        print(colored(f'  "{os.getcwd()}/{year}/{day:02d}/"', 'red'))
        return

    if example:
        if os.stat(f'{year}/{day:02d}/example_input.txt').st_size == 0:
            print(colored('Example input file is empty:', 'red'))
            print(colored(f'  {os.getcwd()}/{year}/{day:02d}/example_input.txt', 'red'))
            return
        else:
            print(colored('(Using example input)', 'red'))

    if solution_file != f'main{day:02d}{ext}':
        if not os.path.exists(f'{year}/{day:02d}/{solution_file}{ext}'):
            print(colored('Solution file does not exist:', 'red'))
            print(colored(f'  "{os.getcwd()}/{year}/{day:02d}/{solution_file}{ext}"', 'red'))
            return
        print(colored(f'(Using {solution_file}{ext})', 'red'))

    part1_answer, part2_answer = compute_answers(year, day,
                                                 solution_file=solution_file,
                                                 example=example,printFullOut=print_output)
    if part1_answer is not None:
        print(f'{colored("Part 1:", "cyan")} {part1_answer}')
    if part2_answer is not None:
        print(f'{colored("Part 2:", "yellow")} {part2_answer}')
    if part1_answer is None and part2_answer is None:
        print(colored('No solution implemented', 'red'))
        return

    if solution_file != f'main{day:02d}{ext}':
        part1_answer_orig, part2_answer_orig = compute_answers(year, day, example=example,printFullOut=print_output)
        if part1_answer == part1_answer_orig and part2_answer == part2_answer_orig:
            print(colored('Output matches solution.py', 'green'))
        else:
            print(colored('Output does not match solution.py', 'red'))


def submit(year, day, solution_file='solution'):
    print("submit")
    dayfilled = str(day).zfill(2)
    if not os.path.exists(f'{year}/{dayfilled}/'):
        print(colored('Directory does not exist:', 'red'))
        print(colored(f'  "{os.getcwd()}/{year}/{dayfilled}/"', 'red'))
        return

    

    part1_answer, part2_answer = compute_answers(year, day, solution_file=solution_file)

    status, response = None, None
    if part2_answer is not None:
        print('Submitting part 2...')
        status, response = submit_answer(year, day, 2, part2_answer)
    elif part1_answer is not None:
        print('Submitting part 1...')
        status, response = submit_answer(year, day, 1, part1_answer)
    else:
        print(colored('No solution implemented', 'red'))
        return

    if status == Status.PASS:
        print(colored('Correct!', 'green'), end=' ')
        if part2_answer is not None:
            print(colored('**', 'yellow'))
            print(f'Day {int(day)} complete!')
        elif part1_answer is not None:
            print(colored('*', 'cyan'))
            conf = config.get_local_config()
            r = requests.get(f'https://adventofcode.com/{year}/day/{int(day)}',
                             cookies={'session': conf['local']['session_cookie']},
                             headers=headers)
            soup = BeautifulSoup(r.text, 'html.parser')
            part2_html = soup.find_all('article', class_='day-desc')[1].decode_contents()

            # remove hyphens from title sections, makes markdown look nicer
            part2_html = re.sub('--- (.*) ---', r'\1', part2_html)

            # also makes markdown look better
            part2_html = part2_html.replace('\n\n', '\n')

            with open(f'{year}/{dayfilled}/prompt.md', 'a') as f:
                f.write(custom_markdownify(part2_html))
            print(f'Appended part 2 prompt to {year}/{dayfilled}/prompt.md')

    elif status == Status.FAIL:
        print(colored('Incorrect!', 'red'))

    elif status == Status.RATE_LIMIT:
        print(colored('Rate limited! Please wait before submitting again.', 'yellow'))

    elif status == Status.COMPLETED:
        print(colored("You've already completed this question.", 'yellow'))

    elif status == Status.NOT_LOGGED_IN:
        print(colored('Session cookie is invalid or expired.', 'red'))

    elif status == Status.UNKNOWN:
        print(colored('Something went wrong. Please view the output below:', 'red'))
        print(response)


def countdown(year, day):
    print("countdown")
    now = dt.now().astimezone(pytz.timezone('EST'))

    if now.year != int(year):
        print(colored(f'Date must be from the current year ({now.year}).', 'red'))
        return

    if now > dt(int(year), 12, int(day)).astimezone(pytz.timezone('EST')):
        print(colored('That puzzle has already been unlocked.', 'red'))
        return

    def curses_countdown(stdscr):  # pragma: no cover
        curses.cbreak()
        curses.halfdelay(2)
        curses.use_default_colors()
        if bool(int(config.get_local_config()['local']['disable_color'])):
            for i in range(1, 4):
                curses.init_pair(i, -1, -1)
        else:
            curses.init_pair(1, curses.COLOR_MAGENTA, -1)
            curses.init_pair(2, curses.COLOR_YELLOW, -1)
            curses.init_pair(3, curses.COLOR_RED, -1)
        hours, minutes, seconds = get_time_until_unlock(year, day)
        while any((hours, minutes, seconds)):
            stdscr.erase()
            stdscr.addstr('advent-cli', curses.color_pair(1))
            stdscr.addstr(' countdown\n\n')
            stdscr.addstr(f'  {year} day {int(day)} will unlock in:\n', curses.color_pair(2))
            stdscr.addstr(f'  {hours} hours, {minutes} minutes, {seconds} seconds\n\n')
            stdscr.addstr('(press Q or CTRL+C to exit)', curses.color_pair(3))
            stdscr.refresh()
            stdscr.nodelay(1)
            key = stdscr.getch()
            if key == 27 or key == 113:
                raise KeyboardInterrupt
            hours, minutes, seconds = get_time_until_unlock(year, day)

    try:  # pragma: no cover
        curses.wrapper(curses_countdown)
        print(colored('Countdown finished', 'green'))
        time.sleep(1)  # wait an extra second, just in case the timing is slightly early
    except KeyboardInterrupt:  # pragma: no cover
        print(colored('Countdown cancelled', 'red'))
        sys.exit(1)


if '__main__' == __name__:
    private_leaderboards_json(2022)