import sys
import os
from os.path import abspath

from ..server.main import run_server
watch_dirs = []
zip_dir = None


for index, arg in enumerate(sys.argv):
    if arg == "-w":
        watch_dirs.append(abspath(sys.argv[index+1]))
    elif arg == "-z":
        zip_dir = abspath(sys.argv[index+1])

if len(watch_dirs) == 0:
    watch_dirs.append(os.getcwd())
    if zip_dir == None:
        zip_dir = os.path.abspath(os.path.join(watch_dirs[0], os.pardir))

run_server(directories_to_watch=watch_dirs, zipfile_dir=zip_dir, os_named=False)
