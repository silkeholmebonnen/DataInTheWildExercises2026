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
-a ... [any other additional input parameters]

EXAMPLE OF FULL COMMAND:
scrapy crawl wiki_minimal -o result.json -s LOG_FILE=WikiSpider.log -s JOBDIR=crawls/wikispider1

REFERENCES:
Scrapy documentation: https://docs.scrapy.org/en/latest/index.html
CSS selectors: https://www.w3schools.com/cssref/css_selectors.asp
Scrapy extension to CSS selectors: https://docs.scrapy.org/en/latest/topics/selectors.html#extensions-to-css-selectors
Xpath syntax: https://www.w3schools.com/xml/xpath_syntax.asp
Xpath cheat sheet: https://devhints.io/xpath
"""

# scrapy library
import scrapy

# custom class definitions of the items
from ..items import *


class WikiSpider(scrapy.Spider):
    """
    Scrapy spider for collecting information about artists and bands from Wikipedia.
    """
    # your spider's name, it must be unique
    name = "wiki_minimal"

    def start_requests(self):
        """
        Execute for the very first time the crawler runs, mainly useful to provide the seed urls to crawl
        """
        yield scrapy.Request(url='https://en.wikipedia.org/wiki/Bruce_Dickinson', 
                             callback=self.parse_artist)


    def parse_band(self, response):
        """
        parses a wikipedia page of a music artist
        @param reponse the http reponse 
        """        
        # prepare a dictionary to store all the information scraped
        band_item = BandItem()
        band_item['url'] = response.url
        # use selectors to scrape the image url
        infobox = response.css('.infobox.vcard')
        infobox_image = infobox.css('.infobox-image')
        img_url = infobox_image.css('a > img::attr(src)').get()
        if img_url is not None:
            img_url = 'https://'+img_url.strip('/')
        band_item['img_url'] = img_url
        print(band_item)
        # yield the item
        yield band_item

    def parse_artist(self, response):
        """
        parses a wikipedia page of a music artist
        @param reponse the http reponse 
        """
        # create an item to store all the information scraped
        artist_item = ArtistItem()
        artist_item['url'] = response.url
        
        # use selectors to scrape the image url
        infobox = response.css('.infobox.vcard.plainlist')
        infobox_image = infobox.css('.infobox-image')
        img_url = infobox_image.css('a > img::attr(src)').get()
        if img_url is not None:
            img_url = 'https://'+img_url.strip('/')
        artist_item['img_url'] = img_url


        # use selectors to scrape the list of bands
        band_urls = []
        all_infobox_rows = infobox.css('tr')
        # the rows we are interested in have no unique id. we need to find them by scanning all the rows and checking the title in the header
        for row in all_infobox_rows:
            # row titles come in different formats. here two cases are captured
            row_title = row.css('th::text').get()
            if not row_title:
                row_title = row.css('*::text').get()
            if row_title == 'Member of' or row_title == 'Formerly of':
                band_url = row.css('td > a::attr(href)').get()
                band_urls.append(band_url)
        band_urls = ['https://en.wikipedia.org/'+url for url in band_urls]
        
        print(artist_item)
        # yield the item
        yield artist_item
        # feed the spider with the band urls to crawl. the responses will be handled by the parse_band method
        for url in band_urls:
            print(band_urls)
            yield scrapy.Request(url=url, callback=self.parse_band)
