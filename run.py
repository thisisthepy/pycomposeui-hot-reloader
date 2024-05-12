import sys

if "server" in sys.argv:
    from .src.main.server import server

