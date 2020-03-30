import operator
import json
import time


def load_json(filename):
    with open(filename + '.json', 'r', encoding='utf-8') as infile:
        data = json.load(infile)
    return data


def write_json(data, filename):
    with open(filename + '.json', 'w', encoding='utf-8') as outfile:
        json.dump(data, outfile, indent=4, ensure_ascii=False, separators=(',', ':'))


def add_to_solved_tasks(screen_name):
    with open('config/solved_tasks.txt', 'a', encoding='utf-8') as outfile:
        outfile.write(screen_name.lower() + '\n')


def load_solved_tasks():
    with open('config/solved_tasks.txt', 'r', encoding='utf-8') as infile:
        return infile.read()


def save_exception(username, process, e):
    with open('config/exceptions.txt', 'a', encoding='utf-8') as outfile:
        outfile.write(time.strftime("%Y.%m.%d. - %H:%M:%S") + ' ' + username + ' ' + process + ' ' + str(e) + '\n')


