from os import makedirs, path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from key_spyder.logs import Logger
from key_spyder.defaults import DEFAULT_PATH, NOW
from requests.exceptions import RequestException
from requests_cache import CachedSession


class Crawler:
    def __init__(self,
                 url: str,
                 params: dict = None,
                 keywords: list[str] = None,
                 recursive: bool = False,
                 output_directory: str = None,
                 verbose: bool = False,
                 clear_cache: bool = False,
                 known_urls: list[str] = None):

        self.logger = Logger(__class__.__name__, verbose)
        if params is None:
            params = {}
        if keywords is None:
            keywords = []
        if output_directory is None:
            output_directory = DEFAULT_PATH

        for folder in ["logs", "results"]:
            dir_path = path.join(output_directory, folder)
            if not path.exists(dir_path):
                makedirs(dir_path)

        self.first_url = url
        self.urls_to_visit = [self.first_url]
        self.keywords = keywords
        self.params = params
        self.recursive = recursive
        self.output_directory = output_directory

        self.visited_urls = []
        self.results = ["url,params,keyword,line\n"]

        if known_urls:
            self.urls_to_visit = known_urls

        cache_name = f"{output_directory}/cache"
        self.session = CachedSession(cache_name, expire_after=86400)
        if clear_cache:
            self.session.cache.clear()

    @property
    def all_urls(self):
        return self.urls_to_visit + self.visited_urls

    def get_html(self, url):
        self.logger.debug(f"Getting: {url} {f'with {self.params}' if self.params else ''}")
        try:
            response = self.session.get(url, params=self.params, allow_redirects=False)
            if response.from_cache:
                self.logger.debug(f"Got: {url} from cache")
            else:
                self.logger.debug(f"Got: {url} in {response.elapsed.total_seconds()} seconds")
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
                self.logger.debug(f"Checking: '{keyword}' in '{line}'")
                if keyword.lower() in line.lower():
                    self.logger.info(f"Found: '{keyword}' in '{line}' on {url}")
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
        self.results = self.results + [f'{url},{self.params},{keyword},"{line}"\n']

    def write_results(self):
        filename = f"{urlparse(self.first_url).netloc}_results_{NOW}.csv"
        filepath = path.join(self.output_directory, "results", filename)
        if len(self.results) > 1:
            with open(filepath, "w") as f:
                f.writelines(self.results)
        else:
            self.logger.info(f"No results found for Keywords: {self.keywords}")

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
        self.logger.info(f"Output can be found at: {self.output_directory}")

    def __exit__(self):
        self.write_results()
        self.session.close()
