import requests
from bs4 import BeautifulSoup
import os
import unicodedata
import re
import shutil
from page import Page

class Outline:
    def __init__(self, root: Page) -> None:
        self.root = root
        

    def createHTML(self):
        path = self.root.dir
        with open(f'{path}/outline.html', 'w', encoding="utf-8") as file:
            # Further file processing goes here
            file.write("<!DOCTYPE html>\n")