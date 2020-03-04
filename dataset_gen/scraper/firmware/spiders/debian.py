from scraper.firmware.settings import config
from scrapy import Spider
from scrapy.http import Request
from scraper.firmware.items import FirmwareImage
from scraper.firmware.loader import FirmwareLoader
import os
from urllib.parse import urlparse, urljoin
import re
import sys
import logging

logger = logging.getLogger(__name__)


class DebianSpider(Spider):
    name = "debian"
    allowed_domains = ["debian.org"]
    start_urls = ["http://cdimage.debian.org/mirror/cdimage/archive/"]
    custom_settings = {
        "CONCURRENT_REQUESTS_PER_DOMAIN": 3, "CLOSESPIDER_ITEMCOUNT": 10, "DOWNLOAD_DELAY": 0.5, "FEED_FORMAT": "json", "FEED_URI": config["crawler"]["output_path"]}

    def parse(self, response):
        self.architectures = config["crawler"]["architectures"].split(",")
        self.versions = config["crawler"]["debian_versions"].split(",")

        # Delete old content of the output file, otherwise scrapy
        # just appends data to it
        if (os.path.exists(config["crawler"]["output_path"])):
            with open(config["crawler"]["output_path"], "w") as json_file:
                json_file.write("")

        self.download_urls = []
        self.download_files = []
        for link in response.xpath(".//a"):
            href = link.xpath("./@href").extract()
            if (bool(re.search(r'\d', str(href)))):
                yield Request(
                    url=urljoin(response.url, href[0]),
                    meta={"version": href[0].replace("/", "")},
                    callback=self.parse_product)

    def parse_product(self, response):
        for link in response.xpath(".//a")[4:]:
            architecture = link.xpath("./@href").extract()[0].replace("/", "")
            version = response.meta["version"]
            if ("9." in version and architecture in self.architectures and version in self.versions):
                href = urljoin(response.url, link.xpath(
                    "./@href").extract()[0])
                url = urljoin(href, "jigdo-dvd/")
                if url not in self.download_urls:
                    self.download_urls.append(url)
                    yield Request(
                        url=url,
                        meta={
                            "version": response.meta["version"], "architecture": architecture},
                        callback=self.parse_item)
            elif (architecture in self.architectures and version in self.versions):
                href = urljoin(response.url, link.xpath(
                    "./@href").extract()[0])
                url = urljoin(href, "jigdo-cd/")
                if url not in self.download_urls:
                    self.download_urls.append(url)
                    yield Request(
                        url=url,
                        meta={
                            "version": response.meta["version"], "architecture": architecture},
                        callback=self.parse_item)

    def parse_item(self, response):
        for link in response.xpath(".//a"):
            href = link.xpath("./@href").extract()[0]
            if href.endswith(".template") or href.endswith(".jigdo"):
                if href not in self.download_files:
                    self.download_files.append(href)
                    item = FirmwareLoader(item=FirmwareImage(),
                                          response=response)
                    item.add_value("vendor", self.name)
                    item.add_value("version", response.meta["version"])
                    item.add_value("url", href)
                    item.add_value(
                        "architecture", response.meta["architecture"])
                    yield item.load_item()
