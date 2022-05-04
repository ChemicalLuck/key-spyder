from os import makedirs, path
from urllib import request, robotparser
from urllib.parse import urlparse

import pandas as pd
from bs4 import BeautifulSoup
from key_spyder.logs import Logger
from key_spyder.defaults import NOW


class Sitemapper:
    def __init__(self, url, verbose=False):
        self.logger = Logger(__class__.__name__, verbose)
        self.url = urlparse(url)

        self.__filename = f"{self.url.netloc}_sitemap_{NOW}.csv"
        self.__sitemap_index = self.__get_sitemap_url()
        self.all_urls = self.__get_all_urls(self.__sitemap_index)

    def __get_sitemap_url(self):
        robots = f"{self.url.scheme}://{self.url.netloc}/robots.txt"
        rp = robotparser.RobotFileParser()
        rp.set_url(robots)
        rp.read()
        sitemaps = rp.site_maps()
        if sitemaps:
            self.logger.debug(f"Found sitemap index: {sitemaps[0]}")
            return sitemaps[0]
        else:
            self.logger.debug(f"No sitemap index found")
            return None

    @staticmethod
    def __get_sitemap(url):
        r = request.urlopen(url)
        xml = BeautifulSoup(r, 'lxml-xml', from_encoding=r.info().get_param('charset'))
        return xml

    @staticmethod
    def __get_sitemap_type(xml):
        sitemapindex = xml.find('sitemapindex')
        sitemap = xml.find('sitemap')
        if sitemapindex:
            return 'sitemapindex'
        elif sitemap:
            return 'sitemap'
        else:
            return None

    @staticmethod
    def __sitemap_to_df(xml, name=None):
        df = pd.DataFrame(
            columns=['loc', 'changefreq', 'priority', 'domain', 'sitemap_name'])
        urls = xml.find_all("url")
        for url in urls:
            if xml.find("loc"):
                loc = url.findNext("loc").text
                domain = f'{urlparse(loc).netloc}'
            else:
                loc = domain = ''

            changefreq = url.findNext("changefreq").text if xml.find("changefreq") else ''
            priority = url.findNext("priority").text if xml.find('priority') else ''
            sitemap_name = name if name else ''

            df.loc[len(df)] = [loc, changefreq, priority, domain, sitemap_name]
        return df

    @staticmethod
    def __get_child_sitemaps(xml):
        sitemaps = xml.find_all('sitemap')
        return [sitemap.findNext('loc').text for sitemap in sitemaps]

    def __get_all_urls(self, url):
        xml = self.__get_sitemap(url)
        sitemap_type = self.__get_sitemap_type(xml)

        sitemaps = self.__get_child_sitemaps(xml) if sitemap_type == 'sitemapindex' else [url]

        df = pd.DataFrame(columns=['loc', 'changefreq', 'priority', 'domain', 'sitemap_name'])
        for sitemap in sitemaps:
            sitemap_xml = self.__get_sitemap(sitemap)
            df_sitemap = self.__sitemap_to_df(sitemap_xml, name=sitemap)
            df = pd.concat([df, df_sitemap], ignore_index=True)
        self.logger.info(f"Found {len(df)} URLs for {self.__sitemap_index}")
        return df

    def to_csv(self, filepath):
        sitemap_path = path.join(filepath, "sitemaps")
        if not path.exists(sitemap_path):
            makedirs(sitemap_path)
        self.logger.info(f"Saving sitemap to {sitemap_path}")
        self.all_urls.to_csv(f"{sitemap_path}/{self.__filename}", index=False)
