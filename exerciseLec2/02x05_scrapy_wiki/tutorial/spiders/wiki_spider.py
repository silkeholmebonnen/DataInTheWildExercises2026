# -*- coding: utf-8 -*-

"""
@author: lajello

A Scrapy spider to crawl the information about bands and musicians from Wikipedia.
This code was written for teaching purposes.
If you plan to scrape information from Wikipedia extensively, please be mindful of the additional load
that your process will give to the servers. To match the resources you consume, consider a donation to
the Wikimedia foundation: https://donate.wikimedia.org/

COMMAND:
scrapy crawl wiki [execute this command from the shell]

OPTIONS:
[add these options after the command as needed]
-o result.json [to output all data in a single result file]
-s LOG_FILE=WikiSpider.log [to set a log file]
-s JOBDIR=crawls/wikispider1 [to set persistence status of the crawl, temporary files will be saved in the specified directory]
-a wiki/James_Hetfield [an example of url to start the crawl from]
-a ... [any other additional input parameters]

EXAMPLE OF FULL COMMAND:
scrapy crawl wiki -o result.json -s LOG_FILE=WikiSpider.log -s JOBDIR=crawls/wikispider_musicnet -a start_url=wiki/James_Hetfield

REFERENCES:
Scrapy documentation: https://docs.scrapy.org/en/latest/index.html
CSS selectors: https://www.w3schools.com/cssref/css_selectors.asp
Scrapy extension to CSS selectors: https://docs.scrapy.org/en/latest/topics/selectors.html#extensions-to-css-selectors
Xpath syntax: https://www.w3schools.com/xml/xpath_syntax.asp
Xpath cheat sheet: https://devhints.io/xpath
Xpath tutorial: http://www.zvon.org/comp/r/tut-XPath_1.html
Python logging (e.g, standard codes): https://docs.python.org/3/library/logging.html
Alternative solution for state persistence: https://medium.com/analytics-vidhya/scrapy-state-between-job-runs-b880c7b34a9d
List of HTTP status codes: https://en.wikipedia.org/wiki/List_of_HTTP_status_codes
Another example implementation of a Scrapy crawler (many can be found on the web): https://github.com/bsobbe/hemnet-crawler
"""

# standard python libraries
import string
import time
import urllib
import logging

# libraries for scraping
import scrapy
from scrapy import signals
from scrapy.crawler import CrawlerProcess
from pydispatch import dispatcher

# custom class definitions of the items
from ..items import *


class WikiSpider(scrapy.Spider):
    """
    Scrapy spider for collecting information about artists and bands from Wikipedia.
    """

    # your spider's name, it must be unique
    name = "wiki"
    # list of domains the spider is allowed to crawl
    allowed_domains = ["wikipedia.org"]

    def __init__(self, start_url, **kwargs):
        """
        Instantiate the spider.
        NOTE: When executing a persistent crawl (i.e., the JOBDIR is set), the attribute self.state
        is not set yet when __init__ is executed.
        @param kwargs: keyword arguments
        """
        # the base url common to all urls; just a convenience variable so that we do not have to repeat it
        self.base_url = "https://en.wikipedia.org/"
        # set the functions spider_opened and spider_closed to be executed at the start/end of the crawl
        dispatcher.connect(self.spider_closed, signals.spider_closed)
        dispatcher.connect(self.spider_opened, signals.spider_opened)
        # flag to signal if the crawl is in persistent mode
        self.is_persistent = False
        self.start_url = start_url
        super().__init__(**kwargs)

    # a shortcut that replaces the start_requests method is to declare start_urls as a class variable:
    # start_urls = ['url1', ..., 'urlN']
    async def start(self):
        """
        Execute for the very first time the crawler runs, mainly useful to provide the seed urls to crawl
        """
        # the url to start scraping from. to use a local html file, use file:///path/to/file.html
        urls = [self.start_url]
        # start with the crawl
        for url in urls:
            yield scrapy.Request(
                url=urllib.parse.urljoin(self.base_url, url), callback=self.parse_artist
            )

    def spider_opened(self):
        """
        Execute some action here when the spider starts
        """
        try:
            # this is how settings are accessed
            persistence_directory = self.settings.attributes["JOBDIR"].value
            # if persistence directory is set, make it persistent
            if persistence_directory:
                self.is_persistent = True
                print(f"Crawler is persistent (dir: {persistence_directory})")
                self.logger.info(f"Crawler is persistent (dir: {persistence_directory}")
        except:
            pass

        # example on how logging is performed.
        # replace '.info' with .warning .error .critical .debug for different types of message
        self.logger.info(f"Crawl started")
        print(f"Crawl started")

    def spider_closed(self):
        """
        Execute some action here when the spider is closed
        """
        # check if the crawl is persistent
        if self.is_persistent:
            try:
                self.logger.info(
                    f"#Crawled {self.state['artist_count']} artists and {self.state['band_count']} bands"
                )
            except:
                # this except block is just to cover the rare case in which the crawler is stopped before any item has been scraped
                self.logger.info(f"Nothing has been crawled")
        self.logger.info(f"Crawl finished")
        print(f"Crawl finished")

    def _clean_list(self, l):
        """
        Parses a list of strings and removes instances containing spaces and punctuation only
        @param l: a list of strings
        @return clean_l: the cleaned list
        """
        # erase punctuation and blanks from sttings
        clean_l = [
            item.translate(str.maketrans("", "", string.punctuation)).strip()
            for item in l
        ]
        # discard empty strings
        clean_l = list(filter(lambda x: x != "", clean_l))
        return clean_l

    def parse_wiki_infobox_image(self, infobox):
        """
        Parse a Wikipedia infobox to extract the image
        @param infobox: the Selector if a Wikipedia infobox
        @return: the url of the infobox image; None if none found
        """
        # img_url = infobox.css('.infobox-image > img::attr(src)').get()
        infobox_image = infobox.css(".infobox-image")
        img_url = infobox_image.css("a > img::attr(src)").get()
        if img_url is not None:
            img_url = img_url.strip("/")
            img_url = "https://" + img_url
        return img_url

    def parse_wiki_infobox_text(self, row, section_titles):
        """
        Parse a row of a Wikipedia infobox to extract the names and urls that it contains
        @param row: the Selector of a Wikipedia infobox row
        @param section_titles: a list of possible titles of the row to parse; if title does not match, returns None
        @return (names, urls): two matched lists of names and urls; None if section not found
        """
        # get the section title
        data_type = row.css(".infobox-label *::text").get()
        # consider only the row corresponding to the desired section title
        if data_type in section_titles:
            # get all band names without a link (url)
            names = self._clean_list(row.css(".infobox-data::text").getall())
            urls = [None for _ in names]
            # add all names for which a link is available
            html_list = row.css(".infobox-data li")
            if html_list:
                for x in html_list:
                    url = x.css("a::attr(href)").get()
                    name = x.css("::text").get()
                    names.append(name)
                    urls.append(url)
            else:
                for x in row.css(".infobox-data > :not(br)"):
                    url = x.css("a::attr(href)").get()
                    name = x.css("::text").get()
                    names.append(name)
                    urls.append(url)
            return (names, urls)
        else:
            return None

    def parse_band(self, response):
        """
        parses a wikipedia page of a music artist
        @param reponse the http reponse
        """

        page_url = response.url
        response_status = response.status
        if response_status != 200:
            self.logger.warning(
                f"({response_status}) for {page_url}, putting back in queue"
            )
            yield scrapy.Request(
                url=urllib.parse.urljoin(self.base_url, page_url),
                callback=self.parse_band,
            )
            return

        # return an instance of Selector correpsonding to the info table
        infobox = response.css(".infobox.vcard")  # .plainlist
        if not infobox:
            self.logger.warning(f"({response_status}) no infobox for {page_url}")
            return
        # print(f'band infobox', page_url)

        # prepare a dictionary to store all the information scraped
        band_item = BandItem()
        band_item["url"] = page_url
        band_item["img_url"] = self.parse_wiki_infobox_image(infobox)
        band_urls = []
        artist_urls = []

        # get the band mane from the top of the infobox
        band_item["name"] = infobox.css(".infobox-above > div::text").get()

        # iterate over all the rows in the table
        table_rows = infobox.css("tr")
        for i, row in enumerate(table_rows):
            # calls a function that extracts names and urls from a row of the infobox
            genres = self.parse_wiki_infobox_text(row, ["Genres"])
            past_members = self.parse_wiki_infobox_text(row, ["Past members"])
            current_members = self.parse_wiki_infobox_text(row, ["Members"])
            if genres is not None:
                # add the band information to the result dictionary
                band_item["genres_names"], band_item["genres_urls"] = genres
            # the remaining sections of the infobox are used to extract urls to continue the crawl
            if past_members is not None:
                artist_urls += past_members[1]
            if current_members is not None:
                artist_urls += current_members[1]

        if self.is_persistent:
            self.state["band_count"] = self.state.get("band_count", 0) + 1
            self.logger.info(
                f"({response_status}) [b={len(band_urls)}, a={len(artist_urls)}] crawled band #{self.state['band_count']} {page_url}"
            )
        else:
            self.logger.info(
                f"({response_status}) [b={len(band_urls)}, a={len(artist_urls)}] crawled band {page_url}"
            )

        yield band_item
        # feed the spider with new urls to crawl.
        for url in artist_urls:
            yield scrapy.Request(
                url=urllib.parse.urljoin(self.base_url, url), callback=self.parse_artist
            )

    def parse_artist(self, response):
        """
        parses a wikipedia page of a music artist
        @param reponse the http reponse
        """
        page_url = response.url
        response_status = response.status
        # if some HTTP error is returned, the page can be put back into the queue for later trials
        if response_status != 200:
            self.logger.warning(
                f"({response_status}) for {page_url}, putting back in queue"
            )
            yield scrapy.Request(
                url=urllib.parse.urljoin(self.base_url, page_url),
                callback=self.parse_artist,
            )
            return

        # return an instance of Selector correpsonding to the info table
        infobox = response.css(".infobox.vcard.plainlist")
        if not infobox:
            self.logger.warning(f"({response_status}) no infobox for {page_url}")
            return
        # print(f'artist infobox', page_url)

        # create an item to store all the information scraped
        artist_item = ArtistItem()
        # alternatiely, simple dictionaries can be used instead of items
        # artist_item = {'url':None, 'img_url':None, 'name':None, 'band_names':[], 'band_urls':[]}

        artist_item["url"] = page_url
        # convenience function to parse the image info
        artist_item["img_url"] = self.parse_wiki_infobox_image(infobox)
        # taking the artist name from the top title in the infobox
        artist_name = infobox.css(".infobox-above > div::text").get()
        artist_item["name"] = artist_name

        # getting info on the bands
        all_infobox_rows = infobox.css("tr")
        band_urls = []
        band_names = []
        # the rows we are interested in have no unique id. we need to find them by scanning all the rows and checking the title in the header
        for row in all_infobox_rows:
            # a convenience function that checks if the row has any of the desired names and if so gets the content
            res = self.parse_wiki_infobox_text(row, ["Member of", "Formerly of"])
            if res is not None:
                # add the band information to the result dictionary
                band_names += res[0]
                band_urls += res[1]
                # band_urls = [response.urljoin(url) for url in band_urls]
        artist_item["band_names"] = band_names
        artist_item["band_urls"] = band_urls

        if self.is_persistent:
            self.state["artist_count"] = self.state.get("artist_count", 0) + 1
            self.logger.info(
                f"({response_status}) [b={len(band_urls)}] crawled artist #{self.state['artist_count']} {page_url}"
            )
        else:
            self.logger.info(
                f"({response_status}) [b={len(band_urls)}] crawled artist {page_url}"
            )

        yield artist_item

        # feed the spider with the band urls to crawl. the responses will be handled by a different parsing method
        if len(band_urls) > 0:
            for url in band_urls:
                if url is not None:
                    yield scrapy.Request(
                        url=urllib.parse.urljoin(self.base_url, url),
                        callback=self.parse_band,
                    )
