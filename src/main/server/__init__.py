import os
import sys
import toml
from os.path import abspath
from ..server.main import run_server

script_path = os.path.dirname(__file__)
config_path = abspath(os.path.join(script_path, '..', '..', '..', 'config.toml'))

with open(config_path, 'r') as f:
    settings_toml = toml.load(f)

watch_dirs = settings_toml['user']['directories_to_watch']
zipfile_dir = settings_toml['user']['zipfile_dir']
exception_dir = settings_toml['user']['exception_dir']
os_named = settings_toml['user']['os_named']
os_exception_list = settings_toml['user']['os_exception_list']
host = settings_toml['server']['host']
port = int(settings_toml['server']['port'])
BASE_DIRECTORY = settings_toml['user']['base_directory']
DEFAULT_NAME_TAIL = settings_toml['user']['default_name_tail']

for index, arg in enumerate(sys.argv):
    if arg == "-w":
        watch_dirs.append(abspath(sys.argv[index+1]))
    elif arg == "-z":
        zip_dir = abspath(sys.argv[index+1])

if len(watch_dirs) == 0:
    watch_dirs.append(os.getcwd())
    if not zipfile_dir:
        zipfile_dir = os.path.abspath(os.path.join(watch_dirs[0], os.pardir))

for excepted_dir in exception_dir:
    tmp_excepted_dir = os.path.basename(excepted_dir)
    tmp_excepted_dir = tmp_excepted_dir.replace(DEFAULT_NAME_TAIL, '')
    os_exception_list.append(tmp_excepted_dir)

exception_dir = [os.path.join(item, '*') for item in exception_dir]
print(f'os_exception_list is {os_exception_list}')
run_server(directories_to_watch=watch_dirs, zipfile_dir=zipfile_dir, exception_dir=exception_dir,
           os_exception_list=os_exception_list, os_named=os_named,
           default_name_tail=DEFAULT_NAME_TAIL, base_directory=BASE_DIRECTORY,
           host=host, port=port)
