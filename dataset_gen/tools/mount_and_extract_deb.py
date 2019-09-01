import os
import os.path
import threading
import ast
import shutil
import sys
import json
import multiprocessing
import subprocess
import argparse
import logging

from helpers.call_cmd import call_cmd

logger = logging.getLogger()

class Data():
    def __init__(self):
        self.deb_path = "unknown"
        self.version = "unknown"
        self.iso = "unknown"


class MountAndExtractDebs():

    def init(self, thread_count, output_path, verbose,
             iot_packages_location, input_json):
        self.threadLimiter = threading.BoundedSemaphore(int(thread_count))
        self.output_path = output_path
        self.verbose = verbose
        self.iot_packages = iot_packages_location
        self.input_json = input_json

    def read_file(self, dictionary):
        with open(dictionary, "r") as iotPackages:
            iotPackages = ast.literal_eval(iotPackages.read())
        array = []
        for i in range(0, len(iotPackages)):
            array.append(iotPackages[i]["name"])
        return array

    def run(self, directory, fileToMount, version, results, iotPackages):
        mountDir = directory + "/mnt/" + fileToMount.split("/")[-1]
        debDir = directory + "/debs"

        try:
            if not os.path.exists(mountDir):
                os.makedirs(mountDir)
            if not os.path.exists(debDir):
                os.makedirs(debDir)
            try:
                cmd = ["fuseiso", fileToMount, mountDir]
                call_cmd(cmd=cmd, shell=False, verbose=self.verbose)
            except subprocess.CalledProcessError:
                logging.error("Failed to mount ISO: " + fileToMount)

            data = Data()
            data.version = version
            data.iso = fileToMount

            new_extracted = 0
            old_extracted = 0
            for dirpath, dirnames, filenames in os.walk(mountDir):
                for filename in [f for f in filenames if f.endswith(".deb")]:
                    if (dirpath.split("/")[-1] in iotPackages):
                        try:
                            deb = os.path.join(dirpath, filename)
                            output_file = os.path.join(debDir, filename)
                            data.deb_path = output_file
                            results.append(data)
                            if not os.path.exists(output_file):
                                shutil.copyfile(deb, output_file)
                                new_extracted += 1
                            else:
                                old_extracted += 1
                        except shutil.SameFileError:
                            logging.error("src and dst files are the same")
                        except IOError:
                            logging.error(
                                "Destination location is not writable")

            logging.debug("Extracted " + str(new_extracted) +
                         " debian packages from " + fileToMount)
            logging.debug(str(old_extracted) + " packages already existed")
            logging.debug("Done. Finishing up")
            logging.debug("Unmounting")

            try:
                cmd = ["fusermount", "-u", mountDir]
                call_cmd(cmd=cmd, shell=False, verbose=self.verbose)
            except subprocess.CalledProcessError:
                logging.error("Failed to unmount: " + mountDir)
        finally:
            self.threadLimiter.release()

    def mount_and_extract_debs(self):
        try:
            with open(self.input_json) as f:
                json_data = json.load(f)
        except IOError:
            logging.error("Failed to open JSON file:" + self.input_json)
            exit(1)

        if (not os.path.exists(self.iot_packages)):
            logging.error(
                "Missing iot_packages.json. Please use crawler to fetch debian_package_list and save " +
                "it to output/ folder.")
            exit(1)

        with multiprocessing.Manager() as manager:
            iotPackages = self.read_file(self.iot_packages)

            results = {}

            for arch in json_data:
                result = manager.list()
                threads = []
                for iso in json_data[arch]:
                    version = iso["version"]
                    # Get folder name where the ISO file is located in
                    # and put it in iso_folder_join variable
                    iso_file = iso["iso_path"]
                    iso_folder = iso_file.split("/")[:-1]
                    iso_folder_join = '/'.join(map(str, iso_folder))
                    if os.path.isfile(iso_file) and iso_file.endswith("iso"):
                        try:
                            self.threadLimiter.acquire()
                            t = threading.Thread(target=self.run, args=(
                                iso_folder_join, iso_file, version, result, iotPackages))
                            t.start()
                            threads.append(t)
                        except Exception as e:
                            logging.error(
                                "Error while mounting ISO file " + iso + ": " + e)
                for t in threads:
                    t.join()

                if arch not in results:
                    results[arch] = []
                for deb in result:
                    results[arch].append(deb)

            with open(self.output_path, 'w', encoding="utf-8") as result_file:
                result_file.write(json.dumps(
                    results, default=lambda x: x.__dict__))
