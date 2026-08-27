# -*- coding: utf-8 -*-

"""
@author: lajello

Pipelines that process the items after they are scraped.

*** To enable a pipeline you must add it to the ITEM_PIPELINES variable in settings.py ***

REFERENCES:
pipelines documentation: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
images pipeline documentation: https://docs.scrapy.org/en/0.24/topics/images.html#scrapy.contrib.pipeline.images.ImagesPipeline
exporters documentation: https://docs.scrapy.org/en/latest/topics/exporters.html
"""

from scrapy.exceptions import DropItem

from scrapy.exporters import CsvItemExporter
from scrapy.exporters import JsonItemExporter

from scrapy.pipelines.images import ImagesPipeline

from .items import ArtistItem, BandItem
import scrapy


class StoreItemPipeline:

    item_types = ['artist', 'band']
    outfiles = {t: None for t in item_types}
    exporters = {t: None for t in item_types}

    def open_spider(self, spider):
        """
        When the spider is started, output files corresponding to each data type are created
        @param spider: the spider
        """
        for t in self.item_types:
            outfile = open(f'{t}.json', 'w+b')
            self.outfiles[t] = outfile
            self.exporters[t] = JsonItemExporter(self.outfiles[t])
            self.exporters[t].start_exporting()

    def close_spider(self, spider):
        """
        When the spider is closed, output files are closed
        @param spider: the spider
        """
        for t in self.item_types:
            self.exporters[t].finish_exporting()
            self.outfiles[t].close()

    def process_item(self, item, spider):
        """
        Stores an item on file
        @param item: the item
        @param spider: the spider
        """
        # recognize the item type
        if isinstance(item, ArtistItem):
            t = 'artist'
        elif isinstance(item, BandItem):
            t = 'band'
        else:
            t = None
        # Warning: type checking is not a best practice in python,
        # but Scrapy has some architectural constraints that make this
        # the easiest way to handle multiple types of items

        # save the item in the appropriate file
        if t in self.item_types:
            self.exporters[t].export_item(item)
        else:
            #this should never occur in this code, but it is an example of how to drop an item
            raise DropItem(f'Item type {t} not recognized')
        return item


class CrawlImagesPipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        """
        Method responsible for locating image urls in the item and issuing requests to download them
        @param item: the item
        """
        if item['img_url'] is not None:
            yield scrapy.Request(item['img_url'])
        
    def item_completed(self, results, item, info):
        """
        Method called when all image requests for a single item have completed 
        (either finished downloading, or failed).
        @param results: a 2-element tuple: (success, image_info_or_failure)
        """
        item['img_path'] = None
        if results:
            image_paths = [image['path'] for success, image in results if success]
            #image_hash = [image['checksum'] for success, image in results if success]
            if image_paths:
                #adapter = ItemAdapter(item)
                item['img_path'] = image_paths[0]
        return item



