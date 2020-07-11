#!/usr/bin/env python3
import os
import argparse
import requests
import json
import pprint
import hashlib
from bs4 import BeautifulSoup

class Soup:
    def assertdir(self,dirname):
        if not os.path.isdir(dirname):
            os.makedirs(dirname)

    def __init__(self, soup, bup_dir):
        self.rooturl = "http://"+soup+".soup.io"
        self.bup_dir = os.path.abspath(bup_dir)
        self.assertdir(self.bup_dir)
        self.dlnextfound = False
        self.sep = os.path.sep
        print("Backup: " + self.rooturl)
        print("into: " + self.bup_dir)
    
    def find_next_page(self, cur_page):
        for script in cur_page.find_all('script'):
            if "SOUP.Endless.next_url" in script.get_text():
                print("\t...found")
                self.dlnextfound = True
                return script.get_text().split('\'')[-2].strip()
        self.dlnextfound = False
        return ""
    
    def get_asset_name(self, name):
        return name.split('/')[-1].split('.')[0]
    
    def get_timstemp(self, post):
        for time_meta in post.find_all("abbr"):
            return time_meta.get('title').strip().split(" ")
        return None
    
    def process_image(self, post):
        print("\t\tImage:")
        meta = {}
        meta['time'] = self.get_timstemp(post)
        for caption in post.find_all("div", {'class': 'caption'}):
            meta['source'] = caption.find('a').get("href")
        for desc in post.find_all("div", {'class': 'description'}):
            meta['text'] = desc.get_text()
        for link in post.find_all('div', {"class":"imagecontainer"}):
            lightbox = link.find("a", {"class": "lightbox"})
            if lightbox:
                meta['soup_url'] = lightbox.get('href')
            else:
                meta['soup_url'] = link.find("img").get('src')
        if 'soup_url' in meta:
            basepath = self.bup_dir + self.sep
            if 'time' in meta:
                basepath = basepath + meta['time'][2] + self.sep + meta['time'][0] + self.sep
            filename = self.get_asset_name(meta['soup_url'])
            path = basepath + filename + "." + meta['soup_url'].split(".")[-1]
            if os.path.isfile(path) == True:
                print("\t\t\tSkip " + meta['soup_url'] + ": File exists")
            else:
                print("\t\t\tsoup_ulr: " + meta['soup_url'] + " -> " + path)
                self.assertdir(basepath)
                r = requests.get(meta['soup_url'], allow_redirects=True)
                with open(path, "wb") as tf:
                    tf.write(r.content)
                self.assertdir(basepath + "meta" + self.sep )
                with open(basepath + "meta" + self.sep + filename + ".json", 'w') as outfile:
                    json.dump(meta, outfile)

    def process_quote(self, post):
        print("\t\tQuote:")
        meta = {}
        meta['time'] = self.get_timstemp(post)
        body = post.find("span", {"class", 'body'}).get_text()
        author = post.find("cite").get_text()
        quote = '"' + body + '"' + "\n\t" + author + "\n"
        qhash = hashlib.sha256(quote.encode())
        hashsum = str(qhash.hexdigest().upper())
        filename = "quote_" + hashsum + ".txt"
        basepath = self.bup_dir + self.sep
        if 'time' in meta:
            basepath = basepath + meta['time'][2] + self.sep + meta['time'][0] + self.sep
        path = basepath + filename
        if os.path.isfile(path) == True:
            print("\t\t\tSkip: " + filename + ": File exists")
        else:
            print("\t\t\t-> " + path)
            with open(path, "w") as qf:
                qf.write(quote)

    def process_link(self, post):
        pass
    def process_video(self, post):
        pass
    def process_file(self, post):
        pass
    def process_review(self, post):
        pass
    def process_event(self, post):
        pass
    def process_regular(self, post):
        pass
    def process_unkown(self, post, post_type):
        print("\t\tUnsuported tpye:")
        print("\t\t\tType: " + post_type)
        meta = {}
        meta['type'] = post_type
        meta['time'] = self.get_timstemp(post)
        content = post.prettify()
        qhash = hashlib.sha256(content.encode())
        hashsum = str(qhash.hexdigest().upper())
        meta['content'] = content
        filename = "unknown_" + hashsum + ".txt"
        basepath = self.bup_dir + self.sep
        if 'time' in meta:
            basepath = basepath + meta['time'][2] + self.sep + meta['time'][0] + self.sep
        path = basepath + filename
        if os.path.isfile(path) == True:
            print("\t\t\tSkip: " + filename + ": File exists")
        else:
            print("\t\t\t-> " + path)
            with open(path, "w") as uf:
                json.dump(meta, uf)

    def process_posts(self, cur_page):
        posts = cur_page.find_all('div', {"class": "post"})
        for post in posts:
            post_type = post.get('class')[1] 
            if post_type == "post_image":
                self.process_image(post)
            elif post_type == "post_quote":
                self.process_quote(post)
            elif post_type == "post_video":
                self.process_video(post)
            elif post_type == "post_link":
                self.process_link(post)
            elif post_type == "post_file":
                self.process_file(post)
            elif post_type == "post_review":
                self.process_review(post)
            elif post_type == "post_event":
                self.process_event(post)
            elif post_type == "post_regular":
                self.process_regular(post)
            else:
                self.process_unkown(post, post_type)
        
    def backup(self, cont_url = ""):
        dlurl = self.rooturl + cont_url
        while True:
            print("Get: " + dlurl)
            dl = requests.get(dlurl)
            page = BeautifulSoup(dl.content, 'html.parser')
            print("Looking for next Page")
            dlurl = self.rooturl + self.find_next_page(page)
            print("Process Posts")
            self.process_posts(page)
            break; # debug stop REMOVE!
            if self.dlnextfound == False:
                break

def main(soups, bup_dir, cont_from):
    for site in soups:
        soup = Soup(site, bup_dir)
        soup.backup(cont_from)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Soup.io backup')
    parser.add_argument('soups', nargs=1, type=str, default=None, help="Name your soup")
    parser.add_argument('-d','--dir', default=os.getcwd(), help="Directory for Backup (default: Working dir)")
    parser.add_argument('-c', '--continue_from', default="", help='Continue from given suburl (Example: /since/696270106?mode=own)')
    #parser.add_argument('-f','--foo', action='store_true', default=False, help='sample for option (used later)')
    args = parser.parse_args()
    main(args.soups, args.dir, args.continue_from)