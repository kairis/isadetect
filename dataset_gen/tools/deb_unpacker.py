# Metadata and file extractor for DEB packages
# Extracts files from a Debian package and saves metadata to JSON
# meta data extracted includes: 1)software name, 2)version number, 3)architecture, 4)package file structure, 5)md5 file hashes 6)control info

import os
import re
import argparse
import os.path
import json
import logging
import subprocess
import threading
import multiprocessing

from helpers.call_cmd import call_cmd


class Data():
    def __init__(self):
        self.software = "unknown"
        self.version = "unknown"
        self.filestructure = "unknown"
        self.controlinfo = "unknown"
        self.package = "unknown"
        self.iso = "unknown"
        self.architecture = "unknown"


class UnpackDebianFiles():

    def main(self, filename, deb, arch, result):
        try:
            data = self.extract_info(filename, deb, arch, result)

        finally:
            self.threadLimiter.release()

    def extract_info(self, line, deb, arch, result):
        o = Data()
        o.iso = deb["iso"]
        o.architecture = arch
        o.package = line.strip()

        candidates = self.create_candidates(o.package)

        o.software = candidates[0].split("/")[-1]
        o.version = candidates[1]

        fstruct = self.extract_filesysinfo(o.package)
        hash_control = self.extract_files(o.package)
        # extraction probably failed
        if hash_control == []:
            result.append(o)
            return

        if hash_control[0] != "N/A":
            o.filestructure = self.extract_hash(fstruct, hash_control[0])
        o.controlinfo = hash_control[1]

        result.append(o)
        return

    def create_candidates(self, filename):
        rpart = filename.rpartition('.')
        if rpart[0] == "":
            name_no_ext = rpart[2]
        else:
            name_no_ext = rpart[0]

        candidates = []
        candidates = candidates + name_no_ext.rsplit('_', 1)
        return candidates

    def extract_hash(self, fstruct, hashlist):
        for line in hashlist.split('\n')[:-2]:
            split = line.split()
            for item in fstruct:
                if '/' + split[1] == item['path']:
                    item['hash'] = split[0]

        return fstruct

    def dump_json(self, data_object):
        return json.dumps(data_object, default=lambda x: x.__dict__)

    def extract_filesysinfo(self, debpackagefilename):
        filesysinfo = debpackagefilename + "_filesysinfo.txt"
        try:
            cmd = "dpkg-deb -c " + debpackagefilename + " > " + filesysinfo
            call_cmd(cmd=cmd, shell=True, verbose=self.verbose)
        except subprocess.CalledProcessError as e:
            return
        try:
            f = open(filesysinfo, "r")
            fstruct = f.read()
            f.close()
            os.remove(filesysinfo)
        except:
            return

        filelist = fstruct.split("\n")[:-2]

        result = []
        for x in filelist:
            data = {}
            results = x.split()
            data["size"] = results[2]
            data["date"] = results[3]
            data["path"] = " ".join(results[5:])
            if data["path"].startswith("."):
                data["path"] = data["path"][1:]
            data['hash'] = ''
            result.append(data)
        return result

    def extract_files(self, debpackagefilename):
        ret = -1
        try:
            cmd = ["dpkg-deb", "-R", debpackagefilename,
                   debpackagefilename + "_extraction"]
            ret = call_cmd(cmd=cmd, shell=False, verbose=self.verbose)
        except subprocess.CalledProcessError as e:
            return []

        if ret != 0:
            return []

        md5_path = debpackagefilename + "_extraction/DEBIAN/md5sums"
        control_path = debpackagefilename + "_extraction/DEBIAN/control"
        hash_control = []

        if os.path.exists(md5_path):
            f = open(md5_path, "r", errors='replace')
            hash_control.append(f.read())
            f.close()
        else:
            hash_control.append("N/A")

        if os.path.exists(control_path):
            g = open(control_path, "r", errors='replace')
            hash_control.append(g.read())
            g.close()

        return hash_control

    def init(self, thread_count, verbose, input_json, output_path):
        self.threadLimiter = threading.BoundedSemaphore(int(thread_count))
        self.verbose = verbose
        self.input_json = input_json
        self.output_path = output_path

    def unpack_debian_files(self):
        try:
            with open(self.input_json) as f:
                json_data = json.load(f)
        except IOError:
            logging.error("Failed to open JSON file: " + input_json)
            exit(1)

        with multiprocessing.Manager() as manager:
            results = {}
            result = manager.list()
            threads = []

            for arch in json_data:
                for deb in json_data[arch]:
                    self.threadLimiter.acquire()
                    deb_path = deb["deb_path"]
                    t = threading.Thread(target=self.main, args=(
                        deb_path, deb, arch, result))
                    t.start()
                    threads.append(t)

                if arch not in results:
                    results[arch] = []

            for t in threads:
                t.join()

            count_of_debs = 0
            for deb in result:
                count_of_debs += 1
                # remove architecture from the Data object
                # so it is not repeated for no reason
                arch = deb.architecture
                del deb.__dict__['architecture']
                results[arch].append(deb)

        logging.debug("Succesfully extracted " + str(count_of_debs) + " debians")

        with open(self.output_path, 'w', encoding="utf-8") as result_file:
            result_file.write(self.dump_json(results))

