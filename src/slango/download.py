import os
import zipfile

import requests
from lxml import etree


def download_file(url):
    r = requests.get(url)
    return r.content


def parse_xml(data):
    class __Item:
        __slots__ = ("title", "link")

        def __init__(self, title, link):
            self.title = title
            self.link = link

    return [
        __Item(item.find("title").text, item.find("link").text)
        for item in etree.fromstring(data)
    ]


def unzip(file_name):
    with zipfile.ZipFile(file_name, "r") as zip_file:
        zip_file.extractall("./zips/")


def write(file_name, file_data):
    with open(file_name, "wb") as f:
        f.write(file_data)


if __name__ == "__main__":
    toc_url = "https://www.gesetze-im-internet.de/gii-toc.xml"
    toc_file = download_file(toc_url)
    items = parse_xml(toc_file)

    os.mkdir("zips")

    for item in items:
        print(f"Downloading >>{item.title}<<")
        item_data = download_file(item.link)

        write("zips/in_progress.zip", item_data)
        unzip("zips/in_progress.zip")
