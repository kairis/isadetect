from scrapy.exceptions import DropItem
from scrapy.http import Request
from scrapy.pipelines.files import FilesPipeline
from scrapy.utils.request import referer_str
from scrapy.utils.log import failure_to_exc_info

from twisted.internet import defer

import os
import hashlib
import logging
from urllib.parse import urlparse, urljoin, urlsplit, unquote
from urllib.request import urlopen
import time
import re


logger = logging.getLogger(__name__)


class FileException(Exception):
    """General media error exception"""


class FirmwarePipeline(FilesPipeline):
    def __init__(self, store_uri, download_func=None, settings=None):
        self.database = None
        self.filename = ''
        super(FirmwarePipeline, self).__init__(
            store_uri, download_func, settings)

    @classmethod
    def from_settings(cls, settings):
        store_uri = settings['FILES_STORE']
        cls.expires = settings.getint('FILES_EXPIRES')
        cls.files_urls_field = settings.get('FILES_URLS_FIELD')
        cls.files_result_field = settings.get('FILES_RESULT_FIELD')

        return cls(store_uri, settings=settings)

    # overrides function from FilesPipeline
    def file_path(self, request, response=None, info=None):
        if (self.filename != ''):
            name = self.filename
        else:
            name = request.url.split('/')[-1]
        if request.meta["architecture"] != "" and request.meta["version"] != "":
            return "%s/%s/%s/%s" % (request.meta["vendor"], request.meta["architecture"], request.meta["version"],
                                    name)
        else:
            return "%s/%s" % (request.meta["vendor"],
                              name)

    # overrides function from FilesPipeline
    def get_media_requests(self, item, info):
        # check for mandatory fields
        for x in ["vendor", "url"]:
            if x not in item:
                raise DropItem(
                    "Missing required field '%s' for item: " % (x, item))

        # resolve dynamic redirects in urls
        for x in ["mib", "sdk", "url"]:
            if x in item:
                split = urlsplit(item[x])
                # remove username/password if only one provided
                if split.username or split.password and not (split.username and split.password):
                    item[x] = urlunsplit(
                        (split[0], split[1][split[1].find("@") + 1:], split[2], split[3], split[4]))

                if split.scheme == "http":
                    item[x] = urlopen(item[x]).geturl()

        # check for filtered url types in path
        url = urlparse(item["url"])
        if any(url.path.endswith(x) for x in [".pdf", ".php", ".txt", ".doc", ".rtf", ".docx", ".htm", ".html", ".md5", ".sha1", ".torrent"]):
            raise DropItem("Filtered path extension: %s" % url.path)
        elif any(x in url.path for x in ["utility", "install", "wizard", "gpl", "login"]):
            raise DropItem("Filtered path type: %s" % url.path)

        # generate list of url's to download
        item[self.files_urls_field] = [item[x]
                                       for x in ["mib", "url"] if x in item]
        if "architecture" not in item:
            item["architecture"] = ""
        if "version" not in item:
            item["version"] = ""
        # pass vendor so we can generate the correct file path and name
        return [Request(x, meta={"ftp_user": "anonymous", "ftp_password": "chrome@example.com", "vendor": item["vendor"], "architecture": item["architecture"], "version": item["version"]}) for x in item[self.files_urls_field]]

    def media_downloaded(self, response, request, info):
        referer = referer_str(request)
        if response.status != 200:
            logger.warning(
                'File (code: %(status)s): Error downloading file from '
                '%(request)s referred in <%(referer)s>',
                {'status': response.status,
                 'request': request, 'referer': referer},
                extra={'spider': info.spider}
            )
            raise FileException('download-error')

        if not response.body:
            logger.warning(
                'File (empty-content): Empty file from %(request)s referred '
                'in <%(referer)s>: no-content',
                {'request': request, 'referer': referer},
                extra={'spider': info.spider}
            )
            raise FileException('empty-content')
        status = 'cached' if 'cached' in response.flags else 'downloaded'

        if ('content-disposition' in response.headers):
            # Pineapple crawler returns content-disposition header
            # but it is type of "bytes" so it needes to be encoded as ascii.
            # Decode function can't be called on string, so need to check type
            if isinstance(response.headers['content-disposition'], bytes):
                d = response.headers['content-disposition'].decode('ascii')
            else:
                d = response.headers['content-disposition']
            fname = re.findall("filename=(.+)", d)
            self.filename = fname[0]
        logger.debug(
            'File (%(status)s): Downloaded file from %(request)s referred in '
            '<%(referer)s>',
            {'status': status, 'request': request, 'referer': referer},
            extra={'spider': info.spider}
        )

        self.inc_stats(info.spider, status)

        try:
            path = self.file_path(request, response=response, info=info)
            checksum = self.file_downloaded(response, request, info)
        except FileException as exc:
            logger.warning(
                'File (error): Error processing file from %(request)s '
                'referred in <%(referer)s>: %(errormsg)s',
                {'request': request, 'referer': referer, 'errormsg': str(exc)},
                extra={'spider': info.spider}, exc_info=True
            )
            raise
        except Exception as exc:
            logger.error(
                'File (unknown-error): Error processing file from %(request)s '
                'referred in <%(referer)s>',
                {'request': request, 'referer': referer},
                exc_info=True, extra={'spider': info.spider}
            )
            raise FileException(str(exc))

        return {'url': request.url, 'path': path, 'checksum': checksum}

    # overrides function from FilesPipeline
    def item_completed(self, results, item, info):
        if isinstance(item, dict) or self.files_result_field in item.fields:
            item[self.files_result_field] = [x for ok, x in results if ok]
        if self.database:
            try:
                cur = self.database.cursor()
                # create mapping between input URL fields and results for each
                # URL
                status = {}
                for ok, x in results:
                    for y in ["mib", "url", "sdk"]:
                        # verify URL's are the same after unquoting
                        if ok and y in item and unquote(item[y]) == unquote(x["url"]):
                            status[y] = x
                        elif y not in status:
                            status[y] = {"checksum": None, "path": None}

                if not status["url"]["path"]:
                    logger.warning("Empty filename for image: %s!" % item)
                    return item

                # attempt to find a matching image_id
                cur.execute("SELECT id FROM image WHERE hash=%s",
                            (status["url"]["checksum"], ))
                image_id = cur.fetchone()

                if not image_id:
                    cur.execute("SELECT id FROM brand WHERE name=%s",
                                (item["vendor"], ))
                    brand_id = cur.fetchone()

                    if not brand_id:
                        cur.execute(
                            "INSERT INTO brand (name) VALUES (%s) RETURNING id", (item["vendor"], ))
                        brand_id = cur.fetchone()
                        logger.info(
                            "Inserted database entry for brand: %d!" % brand_id)

                    cur.execute("INSERT INTO image (filename, description, brand_id, hash) VALUES (%s, %s, %s, %s) RETURNING id",
                                (status["url"]["path"], item.get("description", None), brand_id, status["url"]["checksum"]))
                    image_id = cur.fetchone()
                    logger.info(
                        "Inserted database entry for image: %d!" % image_id)
                else:
                    cur.execute("SELECT filename FROM image WHERE hash=%s",
                                (status["url"]["checksum"], ))
                    path = cur.fetchone()

                    logger.info(
                        "Found existing database entry for image: %d!" % image_id)
                    if path[0] != status["url"]["path"]:
                        os.remove(os.path.join(self.store.basedir,
                                               status["url"]["path"]))
                        logger.info("Removing duplicate file: %s!" %
                                    status["url"]["path"])

                # attempt to find a matching product_id
                cur.execute("SELECT id FROM product WHERE iid=%s AND product IS NOT DISTINCT FROM %s AND version IS NOT DISTINCT FROM %s AND build IS NOT DISTINCT FROM %s",
                            (image_id, item.get("product", None), item.get("version", None), item.get("build", None)))
                product_id = cur.fetchone()

                if not product_id:
                    cur.execute("INSERT INTO product (iid, url, mib_filename, mib_url, mib_hash, sdk_filename, sdk_url, sdk_hash, product, version, build, date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
                                (image_id, item["url"], status["mib"]["path"], item.get("mib", None), status["mib"]["checksum"], status["sdk"]["path"], item.get("sdk", None), status["sdk"]["checksum"], item.get("product", None), item.get("version", None), item.get("build", None), item.get("date", None)))
                    product_id = cur.fetchone()
                    logger.info(
                        "Inserted database entry for product: %d!" % product_id)
                else:
                    cur.execute("UPDATE product SET (iid, url, mib_filename, mib_url, mib_hash, sdk_filename, sdk_url, sdk_hash, product, version, build, date) = (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) WHERE id=%s",
                                (image_id, item["url"], status["mib"]["path"], item.get("mib", None), status["mib"]["checksum"], status["sdk"]["path"], item.get("sdk", None), status["sdk"]["checksum"], item.get("product", None), item.get("version", None), item.get("build", None), item.get("date", None), image_id))
                    logger.info(
                        "Updated database entry for product: %d!" % product_id)

                self.database.commit()
            except BaseException as e:
                self.database.rollback()
                logger.warning("Database connection exception: %s!" % e)
                raise
            finally:
                if self.database and cur:
                    cur.close()

        return item
