import requests
from bs4 import BeautifulSoup
import os
import unicodedata
import re
import shutil
import time
import browser_cookie3

class Page:
    def __init__(self, url, name, dir, downloadImages, root=None, parent=None, propagate=True, download_delay=0, path="0", depth=0, depth_path="0"):
        self.root = root
        self.dir = dir
        self.downloadImages = downloadImages
        self.name = name
        # Get cookies from the browser
        self.cookies = browser_cookie3.firefox()  # or browser_cookie3.vivaldi() for vivaldi, chrome() for chrome etc...
        # Fetch page content using cookies for authentication
        self.content = BeautifulSoup(requests.get(url, cookies=self.cookies).text, 'html.parser')
        #Name root directory according to story title
        if root == None:
            self.root = self
            self.traversed = []
            title = self.sanitize_title(self.content.find("h1").text)
            self.dir = dir + "/" + title
            self.name = title
            self.pageCurrent = 0
            self.filename = "index.html"
            os.makedirs(self.dir+"/images", exist_ok=True)
            os.makedirs(self.dir+"/chapters", exist_ok=True)
            self.known = {}
        else:
            self.root.pageCurrent += 1
            self.filename = f"{self.root.pageCurrent}.html"

        self.parent = parent
        self.url = url
        self.propagate = propagate
        self.download_delay = download_delay
        self.path = path
        self.depth = depth
        self.depth_path = depth_path
        self.children = []

        if propagate:
            link_total = self.root.pageCurrent + 1 
            print(f"{link_total} Links Scraped | Parent chain: {self.path}")  

            self.root.known[url] = self.filename
            self.getChildren()
        else:
            self.filename = self.root.known.get(url)

    def __str__(self):
        retval = "Children: \n"
        try:
            for i in self.children:
                retval += "------" + str(i)
        except AttributeError:
            pass
        return retval

    def getChildren(self):
        temp = self.content.find("div",class_="question-content")
        links = BeautifulSoup(str(temp), 'html.parser')
        #Create new Page for each link in div
        count = 1
        for i in links.find_all("a", class_=""):
            time.sleep(self.download_delay)
            href = i['href']

            #if count is 1, simply add period to path
            new_path = f"{self.path}."
            if count > 1 or self.path == "0":
                new_path += f"{count}"
              
            if (not (href in self.root.known.keys())):
                child = Page(href,i.text, self.dir, self.downloadImages,root=self.root, parent=self, download_delay=self.download_delay, path=new_path, depth=self.depth+1, depth_path=f"{self.depth}.{count}")
            else:
                child = Page(href,i.text, self.dir, self.downloadImages,root=self.root, parent=self, propagate=False, download_delay=self.download_delay, path=new_path,depth=self.depth+1, depth_path=f"{self.depth}.{count}")

            self.children.append(child)
            count+= 1
    
    def createHTML(self):
        if not self.propagate:
            return

        #Base HTML
        with open('default.html', 'r') as f:
            html = BeautifulSoup(f.read(), 'html.parser')

        if(self.downloadImages):
            if(self.root == self):
                try:
                    coverImage = self.content.find("div",class_="cover").find("img")
                    if(coverImage):
                        name = self.slugify(coverImage['alt'])
                        savePath = self.dir + "/images/" + name
                        self.saveImage(coverImage['src'],savePath)
                        coverImage['src'] = "./images/" + name if self.root == self else "../images/" + name
                except AttributeError:
                    pass
            try:
                contentImages = self.content.find('div',class_="chapter-content").find_all('img')
            except AttributeError:
                contentImages = []

            for i in range(len(contentImages)):
                image = contentImages[i]
                name = self.slugify(str(i)+self.name)
                savePath = "./images/" + name if self.root == self else "../images/" + name
                imgPath = image['src']
                try:
                    self.saveImage(imgPath, self.dir + "/images/" + name)
                except (requests.exceptions.InvalidSchema) as err:
                    pass
                image['src'] = savePath

        head = html.find("head")
        stylesheet = [link for link in html.findAll("link") if "style.css" in link.get("href", [])][0]
        body = html.find("body")


        #Copy Story/Chapter header from chyoa.com
        try:
            header = self.content.find("header", class_="story-header")
            header.p.decompose()
        except AttributeError:
            try:
                header = self.content.find("header", class_="chapter-header")
                header.p.decompose()
            #Remnant from initial work (possibly redundant)
            except AttributeError:
                header = html.new_tag('h1')
                header.string = self.name

        body.append(header)

        #Copy main content from chyoa.com
        try:
            mainContent = self.content.find("div",class_="chapter-content")
            body.append(mainContent)
        except ValueError:
            print("Unable to fetch content at " + self.url)

        #Div container for choice links
        linkContainer = html.new_tag('div')
        linkContainer['class'] = "linkContainer"

        try:
            body.append(self.content.find("header", class_="question-header"))
        except ValueError:
            pass

        body.append(linkContainer)

        #Adds text informing user that there are no more paths
        if not self.children:
            alert = html.new_tag("p")
            alert.string = "[No Further Paths]"
            linkContainer.append(alert)

        #Iterate through child Pages and add as links
        for i in self.children:
            link = html.new_tag("a")
            link.string = i.name
            link['href'] = "./chapters/"+i.filename if self.root == self else i.filename 
            link['class'] = "chapterLinks"
            linkContainer.append(link)

        #Div container for persistent options (return, restart, etc.)
        persistent = html.new_tag("div")
        persistent['class'] = "persistent"
        back = html.new_tag("a")

        #Link to return to previous page
        try:
            back.string = "Previous Chapter"
            back['href'] = "../index.html" if self.parent==self.root else self.parent.filename
            back['class'] = "styledLink prev"
            persistent.append(back)

            #Link to return to beginning
            restart = html.new_tag("a")
            restart.string = "Restart"
            restart['class'] = "styledLink prev"
            if self.root == self:
                restart['href'] = "./index.html"
            else:
                restart['href'] = "../index.html"
            persistent.append(restart)
        except AttributeError:
            #Case for first chapter
            pass

        #Link to go to outline
        outline = html.new_tag("a")
        outline.string = "Outline"
        outline['class'] = "styledLink prev"
        if self.root == self:
            outline['href'] = "./outline.html"
        else:
            outline['href'] = "../outline.html"

        #Link to original page on chyoa.com
        original = html.new_tag('a')
        original.string = "Link to Original"
        original['class'] = "styledLink"
        original['href'] = self.url

        #Add subelements to linkContainer
        persistent.append(outline)
        persistent.append(original)
        linkContainer.append(persistent)

        #Create HTML file in proper location
        if self.root == self:
            #index.html file in root directory
            published = open(self.dir+"/index.html", 'w', encoding='utf-8')
            stylesheet['href'] = "chapters/style.css"
            css = open(self.dir+"/chapters/style.css", 'w', encoding='utf-8')
            with open('default.css', 'r') as f:
                css.write(f.read())
                css.close()
        else:
            #[chapter name].html file in 'chapters' directory
            published=open(self.dir+'/chapters/'+self.filename, 'w', encoding="utf-8")
        published.write(str(html.prettify()))
        published.close()

        #Create HTML for child Pages
        [i.createHTML() for i in self.children]

    def saveImage(self, url, file):
        try:
            r = requests.get(url, stream=True, cookies=self.cookies)
        except requests.exceptions.MissingSchema:
            r = requests.get("http://" + url, stream=True)
        except requests.exceptions.SSLError:
            print("Unable to download image from " + url)
            return
        except requests.exceptions.TooManyRedirects:
            print("Unable to download image from " + url)
            return
        except requests.exceptions.ConnectionError:
            print("Unable to download image from " + url)
            return
        except requests.exceptions.InvalidURL:
            print(url + " is invalid url")
            return

        # Check if the image was retrieved successfully
        if r.status_code == 200:
            # Set decode_content value to True, otherwise the downloaded image file's size will be zero.
            r.raw.decode_content = True
            
            # Open a local file with wb ( write binary ) permission.
            with open(file,'wb') as f:
                shutil.copyfileobj(r.raw, f)
        else:
            print("Unable to download image from " + url)

    #Function to convert page names into valid file paths
    def slugify(self, value, allow_unicode=False):
        """
        Taken from https://github.com/django/django/blob/master/django/utils/text.py
        Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
        dashes to single dashes. Remove characters that aren't alphanumerics,
        underscores, or hyphens. Convert to lowercase. Also strip leading and
        trailing whitespace, dashes, and underscores.
        """
        value = str(value)
        if allow_unicode:
            value = unicodedata.normalize('NFKC', value)
        else:
            value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
        value = re.sub(r'[^\w\s-]', '', value.lower())
        thing = re.sub(r'[-\s]+', '-', value).strip('-_')
        if len(thing) > 248:
            thing = thing[::248]
        return thing

    # Replace invalid characters with an empty string and strip trailing whitespace
    def sanitize_title(self, title: str) -> str:
        return re.sub(r'[<>:"/\\|?*]', '', title).strip()


if __name__ == "__main__":
    #Test 
    p = Page("", "Introduction", os.getcwd()+"/land")

