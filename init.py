import os
from load_and_write_files import write_json


proj_path = os.getcwd()
config_path = proj_path + '/config'

def init():
    if not 'config' in os.listdir():
        os.mkdir('config')
    if not 'Data' in os.listdir():
        os.mkdir('Data')
    cur_path = os.getcwd()
    os.chdir(config_path)
    if not 'solved_tasks.txt' in os.listdir():
        open('solved_tasks.txt', 'a').close()
    if not 'accounts_for_analysis.json' in os.listdir():
        write_json({"accounts": {}}, 'accounts_for_analysis')
    
    os.chdir(cur_path)




