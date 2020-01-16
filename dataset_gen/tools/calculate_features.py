import binascii
import collections
import re
import json
import csv
import enum
import sys
import os.path
import numpy as np
import threading
import random
import binascii
import multiprocessing
import logging
import shlex
import subprocess
from helpers.call_cmd import call_cmd


UNKNOWN_ARCHITECTURE = 99

class FeatureCalculator():
    def switch_case(self, argument):
        switcher = {
            "alpha": 1,
            "amd64": 2,
            "arm64": 3,
            "armel": 4,
            "armhf": 5,
            "hppa": 6,
            "i386": 7,
            "ia64": 8,
            "m68k": 9,
            "mips": 10,
            "mips64el": 11,
            "mipsel": 12,
            "powerpc": 13,
            "powerpcspe": 14,
            "ppc64": 15,
            "ppc64el": 16,
            "riscv64": 17,
            "s390": 18,
            "s390x": 19,
            "sh4": 20,
            "sparc": 21,
            "sparc64": 22,
            "x32": 23,
            # Wishlist:
            "avr": 24,
            "cuda": 25,
            "arc": 26,
            "c6x": 27,
            "h8300": 28,
            "hppa64": 29,
            "microblaze": 30,
            "nios2": 31,
            "sh2": 32,
            "riscv32": 33,
            "xtensa": 34,
            "unknown": UNKNOWN_ARCHITECTURE
        }

        return switcher.get(argument, UNKNOWN_ARCHITECTURE)

    def initialize_fingerprints(self):
        self.fps = {}
        # big endian one
        self.fps["be_one"] = br"\x00\x01"
        # little endian one
        self.fps["le_one"] = br"\x01\x00"
        # big endian stack
        self.fps["be_stack"] = br"\xff\xfe"
        # little endian stack
        self.fps["le_stack"] = br"\xfe\xff"

        # armel32 prologs
        self.fps["armel32_prolog_1"] = br"[\x00-\xff][\x00-\xff]\x2d\xe9"
        self.fps["armel32_prolog_2"] = br"\x04\xe0\x2d\xe5"

        # armel32 epilogs
        self.fps["armel32_epilog_1"] = br"[\x00-\xff]{2}\xbd\xe8\x1e\xff\x2f\xe1"
        self.fps["armel32_epilog_2"] = br"\x04\xe0\x9d\xe4\x1e\xff\x2f\xe1"

        # arm32 prologs
        self.fps["arm32_prolog_1"] = br"\xe9\x2d[\x00-\xff][\x00-\xff]"
        self.fps["arm32_prolog_2"] = br"\xe5\x2d\xe0\x04"

        # arm32 epilogs
        self.fps["arm32_epilog_1"] = br"\xe8\xbd[\x00-\xff]{2}\xe1\x2f\xff\x1e"
        self.fps["arm32_epilog_2"] = br"\xe4\x9d\xe0\x04\xe1\x2f\xff\x1e"

        # mips32 prologs
        self.fps["mips32_prolog_1"] = br"\x27\xbd\xff[\x00-\xff]"
        self.fps["mips32_prolog_2"] = br"\x3c\x1c[\x00-\xff][\x00-\xff]\x9c\x27[\x00-\xff][\x00-\xff]"

        # mips32 epilog
        self.fps["mips32_epilog_1"] = br"\x8f\xbf[\x00-\xff]{2}([\x00-\xff]{4}){0,4}\x03\xe0\x00\x08"

        # mips32el prologs
        self.fps["mips32el_prolog_1"] = br"[\x00-\xff]\xff\xbd\x27"
        self.fps["mips32el_prolog_2"] = br"[\x00-\xff][\x00-\xff]\x1c\x3c[\x00-\xff][\x00-\xff]\x9c\x27"

        # mipsel epilog
        self.fps["mips32el_epilog_1"] = br"[\x00-\xff]{2}\xbf\x8f([\x00-\xff]{4}){0,4}\x08\x00\xe0\x03"

        # ppc32 prolog
        self.fps["ppc32_prolog_1"] = br"\x94\x21[\x00-\xff]{2}\x7c\x08\x02\xa6"

        # ppc32 epilog
        self.fps["ppc32_epilog_1"] = br"[\x00-\xff]{2}\x03\xa6([\x00-\xff]{4}){0,6}\x4e\x80\x00\x20"

        # ppcel32 prolog
        self.fps["ppcel32_prolog_1"] = br"[\x00-\xff]{2}\x21\x94\xa6\x02\x08\x7c"

        # ppcel32 epilog
        self.fps["ppcel32_epilog_1"] = br"\xa6\x03[\x00-\xff]{2}([\x00-\xff]{4}){0,6}\x20\x00\x80\x4e"

        # ppc64 prologs
        self.fps["ppc64_prolog_1"] = br"\x94\x21[\x00-\xff]{2}\x7c\x08\x02\xa6"
        self.fps["ppc64_prolog_2"] = br"(?!\x94\x21[\x00-\xff]{2})\x7c\x08\x02\xa6"
        self.fps["ppc64_prolog_3"] = br"\xf8\x61[\x00-\xff]{2}"

        # ppc64 epilog
        self.fps["ppc64_epilog_1"] = br"[\x00-\xff]{2}\x03\xa6([\x00-\xff]{4}){0,6}\x4e\x80\x00\x20"

        # ppcel64 prolog
        self.fps["ppcel64_prolog_1"] = br"[\x00-\xff]{2}\x21\x94\xa6\x02\x08\x7c"

        # ppcel64 epilog
        self.fps["ppcel64_epilog_1"] = br"\xa6\x03[\x00-\xff]{2}([\x00-\xff]{4}){0,6}\x20\x00\x80\x4e"

        # s390x prolog
        self.fps["s390x_prolog_1"] = br'\xeb.[\xf0-\xff]..\x24'

        # s390x epilog
        self.fps["s390x_epilog_1"] = br'\x07\xf4'

        # amd64 prologs
        self.fps["amd64_prolog_1"] = br"\x55\x48\x89\xe5"
        self.fps["amd64_prolog_2"] = br"\x48[\x83,\x81]\xec[\x00-\xff]"

        # amd64 epilogs
        self.fps["amd64_epilog_1"] = br"\xc9\xc3"
        self.fps["amd64_epilog_2"] = br"([^\x41][\x50-\x5f]{1}|\x41[\x50-\x5f])\xc3"
        self.fps["amd64_epilog_3"] = br"\x48[\x83,\x81]\xc4([\x00-\xff]{1}|[\x00-\xff]{4})\xc3"

        # powerpcspe SPE instructions
        self.fps["powerpcspe_spe_instruction_isel"] = br"[\x7d-\x7f][\x00-\xff]{2}(\x1e|\x5e|\x9e)"
        self.fps["powerpcspe_spe_instruction_evl"] = br"(\x10|\x11|\x12|\x13)[\x00-\xff]{2}(\x01|\xc1|\xc8|\xc9|\xc0|\xd0|\xd1|\xda)"


    def init(self, thread_count, code_section_minimum_size, limit_number_of_binaries, architectures, full_binaries, random_sampling, sample_size, input_path, output_path, create_testset):
        self.initialize_fingerprints()
        for key, value in self.fps.items():
            regex = re.compile(value)
            self.fps[key] = regex
        self.threadLimiter = threading.BoundedSemaphore(int(thread_count))
        self.byte_frequencies = []
        self.fingerprints = []
        self.processed_architectures = []
        self.headers_written = False
        self.code_section_minimum_size = int(code_section_minimum_size)
        self.limit_number_of_binaries = int(limit_number_of_binaries)
        self.architectures = architectures
        self.full_binaries = full_binaries
        self.random_sampling = random_sampling
        self.sample_size = int(sample_size)
        self.input_path = input_path
        self.output_path = output_path
        self.create_testset = create_testset
        self.last_arch = 1

        if os.path.exists(self.output_path):
            os.remove(self.output_path)


    def run(self, analyze_this, architecture, count):
        try:
            byte_count = 0

            # architecture to validate model against
            architecture = self.switch_case(architecture)
            if architecture == UNKNOWN_ARCHITECTURE:
                return


            with open(analyze_this, 'rb') as file_t:
                data = bytearray(file_t.read())

            if self.random_sampling:
                start_index = random.randint(0, len(data) - self.sample_size)
                data = bytearray(data[start_index:start_index + self.sample_size])

            # byte frequencies
            byte_frequency_counter = [0] * 256
            for byte in data:
                byte_count += 1
                byte_frequency_counter[byte] += 1
            try:
                byte_frequency_counter = [(x / byte_count)
                                        for x in byte_frequency_counter]
            except Exception as e:
                print(e)
                return

            # function epilog and prolog fingerprints
            fingerprints = {}
            for key, value in self.fps.items():
                i = 0
                for match in value.finditer(data):
                    i += 1
                fingerprints[key] = i / byte_count
            self.processed_architectures.append(architecture)
            self.byte_frequencies.append(byte_frequency_counter)
            self.fingerprints.append(fingerprints)
            count.increment()
        finally:
            self.threadLimiter.release()

    def print_data(self):
        if not self.headers_written:
            with open(self.output_path, 'w') as f:
                filehandle = csv.writer(f)
                self.print_headers(filehandle)
                for i in range(0, len(self.processed_architectures)):
                    data = []
                    try:
                        self.byte_frequencies[i]
                    except IndexError:
                        print("error " + str(self.processed_architectures[i]))
                        continue
                    data = data + self.byte_frequencies[i]
                    for key in sorted(self.fingerprints[i]):
                        data.append(self.fingerprints[i][key])
                    data.append(self.processed_architectures[i])

                    filehandle.writerow(data)
        else:
            with open(self.output_path, 'a') as f:
                filehandle = csv.writer(f)
                for i in range(0, len(self.processed_architectures)):
                    data = []
                    try:
                        self.byte_frequencies[i]
                    except IndexError:
                        print("error " + str(self.processed_architectures[i]))
                        continue
                    data = data + self.byte_frequencies[i]
                    for key in sorted(self.fingerprints[i]):
                        data.append(self.fingerprints[i][key])
                    data.append(self.processed_architectures[i])

                    filehandle.writerow(data)

    def print_headers(self, filehandle):
        header = []

        for i in range(0, 256):
            header.append(i)
        for key in sorted(self.fingerprints[0]):
            header.append(key)
        header.append("architecture")

        filehandle.writerow(header)
        self.headers_written = True

    def find_binaries(self, directory):
        output = ""
        # shell-escape directory-variable
        sanitized_directory = format(shlex.quote(directory))
        # find all executable files from a given directory. "true" is so that
        # grep does not return error code if no results found.
        cmd = "find " + sanitized_directory + " -type f"
        try:
            output = call_cmd(cmd=cmd, shell=True, verbose=False)
        except subprocess.CalledProcessError as cpe:
            logging.error("Failed to find binaries")

        return output

    def calculate_bfd(self):
        if self.create_testset:
            for arch in self.architectures:
                threads = []
                self.processed_architectures = []
                self.byte_frequencies = []
                self.fingerprints = []
                count = Counter()
                path = os.path.join(self.input_path, arch)
                if not os.path.isdir(path):
                    logging.error("Directory for architecture " + arch + " not found")
                    sys.exit(1)
                logging.debug("Processing " + arch)
                binaries = self.find_binaries(path).decode("utf-8").split("\n")
                for binary in binaries:
                    if binary == "":
                        continue
                    if ".json" in binary:
                        continue
                    if self.full_binaries:
                        if ".code" in binary:
                            continue
                    if count.value > self.limit_number_of_binaries:
                        break
                    self.threadLimiter.acquire()
                    t = threading.Thread(target=self.run, args=(binary, arch, count))
                    t.start()
                    threads.append(t)
                for t in threads:
                    t.join()
                logging.debug("Processed " + str(count.value) + " binaries")
                self.print_data()
                self.last_arch = self.switch_case(arch)
            return

        for arch in self.architectures:
            threads = []
            binary_path = os.path.join(self.input_path, "{}/{}.json")
            path = binary_path.format(arch, arch)
            if os.path.exists(path):
                logging.debug("Processing " + arch)
                with open(path) as f:
                    binaries_json = json.load(f)
                count = Counter()
                if self.full_binaries:
                    data = os.path.join(self.input_path, arch, binaries_json[0]["filehash"])
                else:
                    data = binaries_json[0]["only_code"]

                # If using random sampling and sample size is greated than minimum code section size,
                # take minimum of the size of the wanted sample sized binaries
                if self.random_sampling:
                    if self.sample_size > self.code_section_minimum_size:
                        min_binary_size = self.sample_size
                    else:
                        min_binary_size = self.code_section_minimum_size
                else:
                    min_binary_size = self.code_section_minimum_size

                for binary in [f for f in binaries_json if f["only_code_size"] > min_binary_size]:
                    if count.value > self.limit_number_of_binaries:
                        break
                    self.threadLimiter.acquire()
                    t = threading.Thread(target=self.run, args=(data, binary["architecture"], count))
                    t.start()
                    threads.append(t)
                for t in threads:
                    t.join()

                logging.debug("Processed " + str(count.value) + " binaries")

                self.print_data()
            else:
                logging.warning(path + " not found")


class Counter(object):
    def __init__(self, initval=0):
        self.val = multiprocessing.RawValue('i', initval)
        self.lock = multiprocessing.Lock()

    def increment(self):
        with self.lock:
            self.val.value += 1

    @property
    def value(self):
        return self.val.value
