# coding: utf-8

import os 
from os import system, name
import re
import datetime

def validate_datetime_format(datetime_str):
    
    # regular expression to match the format: '2023 7 19 17 40'
    pattern = r'^\d{4} \d{1,2} \d{1,2} \d{1,2} \d{1,2}$'
    
    if not re.match(pattern, datetime_str):
        current_time_utc = datetime.datetime.utcnow()
        valid_date = current_time_utc.strftime('%Y %m %d %H %M')

        print_error('invalid date format', 
                    datetime_str ,
                    f"a valid date format is '{valid_date}'")

        raise SystemExit(1)

    # split the string and convert the parts to integers
    year, month, day, hour, minute = map(int, datetime_str.split())

    # additional checks for valid values
    if not (2022 <= year <= 2050):
        print_error('invalid year', year)
        raise SystemExit(1)
    
    if not (1 <= month <= 12):
        print_error('invalid month', month)
        raise SystemExit(1)
    
    if not (1 <= day <= 31):
        print_error('invalid day', day) 
        raise SystemExit(1)
    
    if not (0 <= hour <= 23):
        print_error('invalid hour', hour) 
        raise SystemExit(1)
    
    if not (0 <= minute <= 59):
        print_error('invalid minute', minute) 
        raise SystemExit(1)
    
    return True

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# def colors
# - - - - - - - - - - - - - - - - - - - - - - - - - -

class Color:
    ESCAPE_SEQ_START = '\033[{}m'
    ESCAPE_SEQ_END = '\033[0m'

    def __init__(self, code):
        self.code = code

    def __call__(self, text):
        try:
            return f'{self.ESCAPE_SEQ_START.format(self.code)}{text}{self.ESCAPE_SEQ_END}'
        except Exception:
            return text

# Color instances
default_c = Color(0)
white = Color(97)
cyan = Color(96)
magenta = Color(95)
blue = Color(94)
yellow = Color(93)
green = Color(92)
red = Color(91)
black = Color(90)
white_b = Color(47)
cyan_b = Color(46)
magenta_b = Color(45)
blue_b = Color(44)
yellow_b = Color(43)
green_b = Color(42)
red_b = Color(41)
black_b = Color(40)

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# clear shell screen
# - - - - - - - - - - - - - - - - - - - - - - - - - -

def clear():
    try:
        if name == 'nt':  # Windows
            system('cls')
        else:  # Mac and Linux
            system('clear')
    except Exception:
        pass

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# expand local path
# - - - - - - - - - - - - - - - - - - - - - - - - - -

def path_expander(path):

    try:
        expanded_path = os.path.expanduser(path)
        return expanded_path
    
    except (ValueError, TypeError, OSError) as e:
        raise SystemExit(1, print_error("check_folder error:", e))

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# print script info
# - - - - - - - - - - - - - - - - - - - - - - - - - -

def print_info(color, v1, v2, v3):
    align = '<35' if isinstance(v3, int) else '35'
    print(color(f"{'*'*5:10} {v1:20} {v2:20} {v3:{align}} {'*'*5:5}"))

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# print script error
# - - - - - - - - - - - - - - - - - - - - - - - - - -

def print_error(*args, color=red, level='ERROR'):

    color = yellow if level == 'INFO' else color 
    max_length = min(max(len(str(error_message)) for error_message in args) + 6, 98)
    error_box_width = max_length + 4
    error_message_width = max_length + 2
    blank_line = color("║" + " " * error_box_width + "║")

    print(color("\n╔" + "=" * error_box_width + "╗"))
    print(blank_line)
    print(color("║"), color(f"{level}!".center(error_message_width)), color("║"))
    print(blank_line)

    for error_message in args:
        error_message = str(error_message)
        if len(error_message) > 98:
            split_messages = [error_message[i:i + 98] for i in range(0, len(error_message), 98)]
            for split_message in split_messages:
                print(color("║"), color(split_message.center(error_message_width)), color("║"))
        else:
            print(color("║"), color(error_message.center(error_message_width)), color("║"))

    print(blank_line)
    print(blank_line)
    print(color("╚" + "=" * error_box_width + "╝\n"))

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# print formated output 
# - - - - - - - - - - - - - - - - - - - - - - - - - -

def print_output(color, user_rank, data):

    rank = str(user_rank)
    user = data.get('name')
    last_login = data.get('last_login')
    state = data.get('state')
    active = data.get('active')
    days = data.get('days')
    ocid = data.get('ocid')

    formatted_string = color(
        f'{rank:<5} '
        f'{user[0:40]:<40} '
        f'{last_login:<30} '
        f'{active:<10} '
        f'{state:<10} '
        f'{days:<13} '
        f'{ocid:<40}'
    )
    print(formatted_string)

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# calculate time delta
# - - - - - - - - - - - - - - - - - - - - - - - - - -
    
def strfdelta(td):
    days = td.days
    hours, rem = divmod(td.seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    return f"{days} days, {hours} hours, {minutes} minutes, {seconds} seconds"