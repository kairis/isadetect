import re
import os
import logging

from scrapy import Spider
from scrapy.http import Request
from scraper.firmware.items import FirmwareImage
from scraper.firmware.loader import FirmwareLoader
from urllib.parse import urlparse, urljoin
from scraper.firmware.settings import config


logger = logging.getLogger(__name__)


class DebianPortSpider(Spider):
    name = "debian_ports_ftp"
    allowed_domains = ["debian.org"]
    start_urls = ["http://ftp.ports.debian.org/debian-ports/"]
    custom_settings = {
        "CONCURRENT_REQUESTS_PER_DOMAIN": 3, "DOWNLOAD_DELAY": 0.5, "FEED_FORMAT": "json", "FEED_URI": config["debian_port_downloader"]["output_path"]}

    def parse(self, response):
        architectures = config["crawler"]["port_architectures"].split(",")

        # Delete old content of the output file, otherwise scrapy
        # just appends data to it
        if (os.path.exists(config["debian_port_downloader"]["output_path"])):
            with open(config["debian_port_downloader"]["output_path"], "w") as json_file:
                json_file.write("")

        for link in response.xpath(".//a")[4:]:
            href = link.xpath("./@href").extract()
            architecture = link.xpath("./@href").extract()[0]
            if "pool-" in architecture and architecture.replace("/", "").replace("pool-", "") in architectures:
                architecture = architecture.replace("/", "").replace("pool-", "")
                url = urljoin(response.url, href[0])
                url = urljoin(url, "main")
                yield Request(
                    url=url,
                    # The website does not specify the debian version, but let's use 9.0 so we have some value
                    meta={"version": "9.0", "architecture": architecture},
                    callback=self.parse_products)

    def parse_products(self, response):
        for link in response.xpath(".//a")[4:]:
            href = urljoin(response.url, link.xpath("./@href").extract()[0])
            yield Request(
                url=href,
                meta={
                    "version": response.meta["version"], "architecture": response.meta["architecture"]},
                callback=self.parse_product)

    def parse_product(self, response):
        for link in response.xpath(".//a")[4:]:
            href = urljoin(response.url, link.xpath("./@href").extract()[0])
            yield Request(
                url=href,
                meta={
                    "version": response.meta["version"], "architecture": response.meta["architecture"]},
                callback=self.parse_item)

    def parse_item(self, response):
        for link in response.xpath(".//a")[4:]:
            href = link.xpath("./@href").extract()[0]
            if href.endswith(".deb"):
                item = FirmwareLoader(item=FirmwareImage(),
                                      response=response)
                item.add_value("vendor", self.name)
                item.add_value("version", response.meta["version"])
                item.add_value("url", href)
                item.add_value("architecture", response.meta["architecture"])
                yield item.load_item()
