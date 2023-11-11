import argparse
import os
from page import Page
from outline import Outline

import sys

class recursionlimit:
    def __init__(self, limit):
        self.limit = limit
        self.old_limit = sys.getrecursionlimit()

    def __enter__(self):
        sys.setrecursionlimit(self.limit)

    def __exit__(self, type, value, tb):
        sys.setrecursionlimit(self.old_limit)

parser = argparse.ArgumentParser()

parser.add_argument('--links', help="Comma-separated list of CHYOA URLS. Can provide just one URL without comma for single download", type=str)
parser.add_argument('--images', help="Download images", type=bool, default=True)
parser.add_argument('--directory','-d', help="Directory to store downloaded files", default=os.getcwd(), type=str)
parser.add_argument('--download_delay','-e', help="Wait this many seconds between download requests to avoid overloading the server", default=0, type=float)

args = vars(parser.parse_args())





with recursionlimit(30000):
    print(sys.getrecursionlimit())
    links = []
    for i in args['links'].split(","):
        print("Collecting Links From " + i)
        page = Page(i, "", args['directory'], args['images'], download_delay=max(0, args['download_delay']))
        print("Links Collected")
        print("Building HTML Files")
        page.createHTML()
        print("Download Complete")
        print("Creating outline")
        outline = Outline(page)
        outline.createHTML()
        print("Outline Created")
    print("All Files Downloaded")
