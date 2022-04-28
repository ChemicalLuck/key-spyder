import logging
from urllib.parse import urljoin
from datetime import datetime
from os import path

import requests
from bs4 import BeautifulSoup


logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.INFO
)


class Crawler:
    def __init__(self,
                 urls: list[str] = None,
                 params: dict = None,
                 keywords: list[str] = None,
                 recursive: bool = False,
                 output_directory: str = None,
                 verbose: bool = False):

        if urls is None:
            urls = []
        if params is None:
            params = {}
        if keywords is None:
            keywords = []
        if output_directory is None:
            output_directory = path.expanduser('~\Documents')


        self.urls_to_visit = urls
        self.keywords = keywords
        self.params = params
        self.recursive = recursive
        self.output_directory = output_directory
        self.verbose = verbose

        self.visited_urls = []
        self.results = ["url,params,keyword,line\n"]

    @property
    def all_urls(self):
        return self.urls_to_visit + self.visited_urls

    def log(self, message, override=False):
        if self.verbose or override:
            logging.info(message)

    def get_html(self, url):
        return requests.get(url, self.params).text

    def get_links(self, url, html):
        soup = BeautifulSoup(html, 'html.parser')
        for link in soup.find_all('a'):
            path = link.get('href')
            if path:
                if path.startswith('/'):
                    path = urljoin(url, path)
                if "https://ffs.co.uk" in path and path not in self.all_urls:
                    yield path

    def get_keywords(self, url, html):
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.body.get_text().split("\n")

        text = [line.strip() for line in text if line.strip()]

        for line in text:
            for keyword in self.keywords:
                self.log(f"Checking for '{keyword}' in '{line}' on {url}")
                if keyword.lower() in line.lower():
                    self.log(f"Found '{keyword}' in '{line}' on {url}", override=True)
                    self.write_line(url, keyword, line)

    def crawl(self, url, html):
        self.log(f'Crawling: {url}')
        for url in self.get_links(url, html):
            self.log(f'Discovered: {url}')
            if url not in self.all_urls:
                self.urls_to_visit.append(url)

    def write_line(self, url, keyword, line):
        self.results = self.results + [f"{url},{self.params},{keyword},{line}\n"]

    def write_results(self):
        now = datetime.now().strftime('%Y-%m-%dT%H%M%SZ')
        filename = path.join(self.output_directory, f"results_{now}.csv")
        if len(self.results) > 1:
            with open(filename, "w") as f:
                f.writelines(self.results)
        else:
            logging.info(f"No results found for Keywords: {self.keywords}")

    def run(self):
        while self.urls_to_visit:
            url = self.urls_to_visit.pop(0)
            html = self.get_html(url)
            if self.recursive:
                self.crawl(url, html)
            self.get_keywords(url, html)
            self.visited_urls.append(url)
        self.write_results()

    def __exit__(self):
        self.write_results()
