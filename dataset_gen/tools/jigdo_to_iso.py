import os
import os.path
import subprocess
import threading
import sys
import json
import logging
import shlex

from helpers.call_cmd import call_cmd

logger = logging.getLogger(__name__)


class ISOMetadata():
    def __init__(self):
        self.iso_path = "unknown"
        self.version = "unknown"


DEFAULT_THREAD_COUNT = 4


class JigdoDownloader():
    def init(self, thread_count, crawler_output_path,
             iso_ignore_list, architectures,
             verbose, output_path, input_json):
        self.threadLimiter = threading.BoundedSemaphore(int(thread_count))
        self.crawler_output_path = crawler_output_path
        self.iso_ignore_list = iso_ignore_list
        self.architectures = architectures
        self.verbose = verbose
        self.output_path = output_path
        self.input_json = input_json

    def dlfile(self, directory, fileToDownload):
        self.threadLimiter.acquire()
        directory = format(shlex.quote(directory))
        cmd = "cd " + directory + " && jigdo-lite --noask " + \
                            fileToDownload
        try:
            call_cmd(cmd=cmd, shell=True, verbose=self.verbose)
        except subprocess.CalledProcessError:
            logging.error("Error while running jigdo-lite")
        finally:
            self.threadLimiter.release()

    def download_jigdos(self):
        try:
            with open(self.input_json) as f:
                jigdos = json.load(f)
        except IOError:
            logging.error("Failed to open JSON file: " + input_json)
            exit(1)

        if (not os.path.exists(self.crawler_output_path)):
            logging.error("Invalid path in dataset_gen.output_path")
            exit(1)

        results = {}
        for jigdo in jigdos:
            filename = jigdo["files"][0]["path"]
            jigdo_path = os.path.join(self.crawler_output_path, filename)
            # Check that only "full installations" are downloaded, ignore rest of the isos
            if (os.path.isfile(jigdo_path) and "jigdo" in filename and
                not any(ignored in filename for ignored in self.iso_ignore_list) and
                    any(archs in filename for archs in self.architectures)):
                arch = jigdo["architecture"]
                version = jigdo["version"]
                directory = os.path.join(self.crawler_output_path,
                                         "isos", arch, version)
                if not os.path.exists(directory):
                    os.makedirs(directory)

                # save metadata about ISO to results
                data = ISOMetadata()
                iso_filename = jigdo["files"][0]["path"].split(
                    "/")[-1].replace("jigdo", "iso")
                data.iso_path = os.path.join(directory, iso_filename)
                data.version = version

                if arch not in results:
                    results[arch] = []

                results[arch].append(data)

                try:
                    t = threading.Thread(
                        target=self.dlfile, args=(directory, jigdo_path, ))
                    t.start()
                except Exception as e:
                    logging.error("Error while downloading " +
                                 jigdo_path + ": " + e)
            elif ("iso" in filename and not any(ignored in filename for ignored in self.iso_ignore_list)
                    and any(archs in filename for archs in self.architectures)):

                arch = jigdo["architecture"]
                version = jigdo["version"]
                data = ISOMetadata()
                data.iso_path = jigdo_path
                data.version = version
                if arch not in results:
                    results[arch] = []
                results[arch].append(data)

        with open(self.output_path, 'w', encoding="utf-8") as result_file:
            result_file.write(json.dumps(
                results, default=lambda x: x.__dict__))
