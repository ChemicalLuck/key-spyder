import logging
import logging.handlers
from urllib.parse import urljoin, urlparse
from datetime import datetime
from os import path, makedirs

import requests
import requests_cache
from requests.exceptions import RequestException
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
                 verbose: bool = False,
                 clear_cache: bool = False):

        if urls is None:
            urls = []
        if params is None:
            params = {}
        if keywords is None:
            keywords = []
        if output_directory is None:
            output_directory = path.expanduser('~\Documents\key-spyder')

        for folder in ["logs", "results", "cache"]:
            dir_path = path.join(output_directory, folder)
            if not path.exists(dir_path):
                makedirs(dir_path)

        self.urls_to_visit = urls
        self.keywords = keywords
        self.params = params
        self.recursive = recursive
        self.output_directory = output_directory

        self.visited_urls = []
        self.results = ["url,params,keyword,line\n"]

        now = datetime.now().strftime('%Y-%m-%dT%H%M%SZ')
        fh_path = f"{output_directory}/logs/key-spyder_{now}.log"
        file_handler = logging.FileHandler(fh_path, "w")
        self.logger = logging.getLogger("key-spyder")
        self.logger.addHandler(file_handler)

        if verbose:
            self.logger.setLevel(10)

        requests_cache.install_cache(f"{output_directory}/cache")
        if clear_cache:
            requests_cache.clear()

    @property
    def all_urls(self):
        return self.urls_to_visit + self.visited_urls

    def get_html(self, url):
        try:
            response = requests.get(url, self.params, allow_redirects=False)
        except RequestException as e:
            self.logger.exception(e)
        else:
            return response.text

    @staticmethod
    def get_links(url, html):
        """
        For a given url, search all anchor tags, return a list of all new links.
        """
        soup = BeautifulSoup(html, 'html.parser')
        parsed_url = urlparse(url)
        prot_host_tld = f"{parsed_url.scheme}://{parsed_url.hostname}"

        # Find all anchor tags on the page.
        for link in soup.find_all('a'):
            path = link.get('href')
            # Make sure the href was set.
            if path:
                # If it's an internal link, prepend the hostname to the path.
                if path.startswith('/'):
                    path = urljoin(prot_host_tld, path)
                # If the new path is still on the beginning host.
                if prot_host_tld in path:
                    yield path

    def get_keywords(self, url, html):
        """
        For a given url, check for keywords and write them to the results list.
        """
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.body.get_text().split("\n")

        text = [line.strip() for line in text if line.strip()]

        for line in text:
            for keyword in self.keywords:
                self.logger.debug(f"Checking for '{keyword}' in '{line}' on {url}")
                if keyword.lower() in line.lower():
                    self.logger.info(f"Found '{keyword}' in '{line}' on {url}")
                    self.write_line(url, keyword, line)

    def crawl(self, url, html):
        """
        For a given url, Discover new links on that page.
        """
        self.logger.info(f'Crawling: {url}')
        for link in self.get_links(url, html):
            if link not in self.all_urls:
                self.logger.info(f'Discovered: {link}')
                self.urls_to_visit.append(link)

    def write_line(self, url, keyword, line):
        self.results = self.results + [f"{url},{self.params},{keyword},'{line}'\n"]

    def write_results(self):
        now = datetime.now().strftime('%Y-%m-%dT%H%M%SZ')
        filename = path.join(self.output_directory, "results", f"results_{now}.csv")
        if len(self.results) > 1:
            with open(filename, "w") as f:
                f.writelines(self.results)
        else:
            logging.info(f"No results found for Keywords: {self.keywords}")

    def run(self):
        while self.urls_to_visit:
            url = self.urls_to_visit.pop(0)
            self.visited_urls.append(url)
            html = self.get_html(url)
            if html:
                if self.recursive:
                    self.crawl(url, html)
                if self.keywords:
                    self.get_keywords(url, html)
        self.write_results()

    def __exit__(self):
        self.write_results()
