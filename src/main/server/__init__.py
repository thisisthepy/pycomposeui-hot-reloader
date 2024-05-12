import sys
import os
from os.path import abspath

from ..server.main import run_server
watch_dir = []
zip_dir = "../"

for index, arg in enumerate(sys.argv):
    if arg == "-w":
        watch_dir.append(abspath(sys.argv[index+1]))
    elif arg == "-z":
        zip_dir = abspath(sys.argv[index+1])

if len(watch_dir) == 0:
    watch_dir.append(os.getcwd())

run_server(directory_to_watch=watch_dir[0], zipfile_dir=zip_dir)
