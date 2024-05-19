import os
import sys
import toml
from os.path import abspath
from ..server.main import run_server

script_path = os.path.dirname(__file__)
config_path = abspath(os.path.join(script_path, '../../../config.toml'))

with open(config_path, 'r') as f:
    settings_toml = toml.load(f)

watch_dirs = settings_toml['user']['directories_to_watch']
zipfile_dir = settings_toml['user']['zipfile_dir']
exception_dir = settings_toml['user']['exception_dir']
host = settings_toml['server']['host']
port = settings_toml['server']['port']
for index, arg in enumerate(sys.argv):
    if arg == "-w":
        watch_dirs.append(abspath(sys.argv[index+1]))
    elif arg == "-z":
        zip_dir = abspath(sys.argv[index+1])

if len(watch_dirs) == 0:
    watch_dirs.append(os.getcwd())
    if not zipfile_dir:
        zipfile_dir = os.path.abspath(os.path.join(watch_dirs[0], os.pardir))

run_server(directories_to_watch=watch_dirs, zipfile_dir=zipfile_dir, os_named=False, host=host, port=port)
