BOT_NAME = "firmware"

SPIDER_MODULES = ["scraper.firmware.spiders"]
NEWSPIDER_MODULE = "scraper.firmware.spiders"

DOWNLOAD_HANDLERS = {
    's3': None,
}

DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
}

SPIDER_MIDDLEWARES = {
}

ITEM_PIPELINES = {
    "scraper.firmware.pipelines.FirmwarePipeline": 1,
}

import os
import sys
from configparser import ConfigParser, ExtendedInterpolation, SafeConfigParser

root_dir = os.getenv("DATASET_GEN_ROOT_FOLDER")
if root_dir is None:
    os.environ.setdefault('DATASET_GEN_ROOT_FOLDER', os.getcwd())

config = SafeConfigParser(os.environ, interpolation=ExtendedInterpolation())


if config.sections() == []:
    ret = config.read(os.path.abspath("config.ini"))
    if ret == []:
        print("Failed to read config.ini. Check that it exists.")
        sys.exit(1)

FILES_STORE = config["dataset_gen"]["output_path"]

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 0
AUTOTHROTTLE_MAX_DELAY = 15
CONCURRENT_REQUESTS = 8

DOWNLOAD_TIMEOUT = 1200
DOWNLOAD_MAXSIZE = 0
DOWNLOAD_WARNSIZE = 0

FILES_RESULT_FIELD = 'files'

ROBOTSTXT_OBEY = False
USER_AGENT = "FirmwareBot/1.0 (+https://github.com/firmadyne/scraper)"

EXTENSIONS = {'scrapy.extensions.telnet.TelnetConsole': None}
