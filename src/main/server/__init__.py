import sys
from os.path import abspath

from pycomposeui_hot_reloader.src.main.server.main import run_server

watch_dir = []
zip_dir = ""

for index, arg in enumerate(sys.argv):
    if arg == "-w":
        watch_dir.append(abspath(sys.argv[index+1]))
    elif arg == "-z":
        zip_dir = abspath(sys.argv[index+1])


run_server(directory_to_watch=watch_dir[0], zipfile_dir=zip_dir)
