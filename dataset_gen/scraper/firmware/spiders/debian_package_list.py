from scrapy import Spider
from scrapy.http import Request
from scraper.firmware.items import FirmwareImage
from scraper.firmware.loader import FirmwareLoader
import os
from urllib.parse import urlparse, urljoin
import re

import logging
logger = logging.getLogger(__name__)

from scraper.firmware.settings import config




class DebianPackageListSpider(Spider):
    name = "debian_package_list"
    allowed_domains = ["debian.org"]
    start_urls = ["https://packages.debian.org/stable/"]
    custom_settings = {
        "CONCURRENT_REQUESTS_PER_DOMAIN": 3, "DOWNLOAD_DELAY": 0.5, "ITEM_PIPELINES": {
        }, "FEED_FORMAT": "json", "FEED_URI": config["crawler"]["iot_packages_location"]}

    def parse(self, response):
        if (os.path.exists(config["crawler"]["iot_packages_location"])):
            with open(config["crawler"]["iot_packages_location"], "w") as json_file:
                json_file.write("")

        sites = config["crawler"]["package_list"]
        for link in response.xpath(".//div[@id='content']//a"):
            href = link.xpath("./@href").extract()[0]
            item = link.xpath("./text()").extract()[0]
            if item in sites:
                yield Request(
                    url=urljoin(response.url, href),
                    callback=self.parse_product)

    def parse_product(self, response):
        for link in response.xpath(".//div[@id='content']//a"):
            href = link.xpath("./text()").extract()[0]
            yield {
                'name': str(href)
            }
