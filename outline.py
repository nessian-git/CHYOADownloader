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

        #Base HTML
        with open('default.html', 'r') as f:
            html = BeautifulSoup(f.read(), 'html.parser')
        stylesheet = [link for link in html.findAll("link") if "style.css" in link.get("href", [])][0]
        stylesheet['href'] = "chapters/style.css"
        body = html.find("body")

        header = html.new_tag('h1')
        header.string = "Outline"

        body.append(header)

        soup = BeautifulSoup('', 'html.parser')
        list = soup.new_tag('ul')
        list.append(self.traverse(self.root, soup))

        container_div = soup.new_tag("div", **{"class": "container"})
        container_div.append(list)

        body.append(container_div)

        with open(f'{path}/outline.html', 'w', encoding="utf-8") as file:
            # Further file processing goes here
            file.write(str(html))

    def traverse(self, page: Page, soup: BeautifulSoup):
        li_tag = soup.new_tag("li")
        if page.root == page:
            a_tag = soup.new_tag("a", href=page.filename)
        else:
            a_tag = soup.new_tag("a", href=f"chapters/{page.filename}") 
        a_tag.string = page.name
        li_tag.append(a_tag)

        if page.children:
            ul_tag = soup.new_tag("ul")
            for child in page.children:
                ul_tag.append(self.traverse(child, soup))
            li_tag.append(ul_tag)
        return li_tag

