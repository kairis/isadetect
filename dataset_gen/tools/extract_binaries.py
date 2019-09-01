import sys
import os
import os.path
import shutil
import hashlib
import json
import logging
import shlex
import threading
import multiprocessing
import subprocess
from helpers.call_cmd import call_cmd


class MetaData():
    def __init__(self):
        self.architecture = "unknown"
        self.code_sections = []
        self.endianness = "unknown"
        self.filehash = "unknown"
        self.fileinfo = "unknown"
        self.filename = "unknown"
        self.filesize = -1
        self.wordsize = -1
        self.deb_package = "unknown"
        # only_code to know if extracting code section was successful or not
        self.only_code = "unknown"
        self.only_code_size = -1


class BinaryExtractor():

    def find_binaries(self, directory):
        output = b""
        # shell-escape directory-variable
        sanitized_directory = format(shlex.quote(directory))
        # find all executable files from a given directory. "true" is so that
        # grep does not return error code if no results found.
        cmd = "find " + sanitized_directory + " -type f -executable -exec file -i '{}' \; " + \
            "| grep 'application' || true"
        try:
            output = call_cmd(cmd=cmd, shell=True, verbose=self.verbose)
        except subprocess.CalledProcessError as cpe:
            logging.error("Failed to find binaries")

        return output

    def extract_information(self, binary, output_path):
        metadata = MetaData()

        metadata.filename = binary
        metadata.deb_package = [f for f in binary.split(
            "/") if "extraction" in f][0].split("_extraction")[0]

        metadata.architecture = metadata.deb_package.split(
            ".")[-2].split("_")[-1]

        md5 = hashlib.md5()
        with open(binary, 'rb') as f:
            while True:
                data = f.read(self.buffer_size)
                if not data:
                    break
                md5.update(data)
        metadata.filehash = md5.hexdigest()

        cmd = ["file", binary]
        ret = call_cmd(cmd=cmd, shell=False, verbose=self.verbose)
        metadata.fileinfo = ret.decode("utf-8").split("\n")[0]
        if "LSB" in metadata.fileinfo:
            metadata.endianness = "little"
        else:
            metadata.endianness = "big"

        if "32-bit" in metadata.fileinfo:
            metadata.wordsize = 32
        else:
            metadata.wordsize = 64

        metadata.filesize = os.path.getsize(binary)

        # shell-escape binary-variable
        sanitized_binary = format(shlex.quote(binary))
        # print the file info and grep the names of the code sections
        cmd = "objdump -h " + sanitized_binary + "| grep -B 1 CODE| awk 'NR%2==1" + \
            "{print $2}'"
        code_sections = call_cmd(cmd=cmd, shell=True, verbose=self.verbose).decode("utf-8").split("\n")
        if code_sections == ['']:
            # No code sections found, skip this one
            return metadata

        sections = ""
        for code_section in [x for x in code_sections if x != ""]:
            metadata.code_sections.append(code_section)
            sections += "--only-section=" + code_section + " "

        code_only_path = os.path.join(output_path, metadata.filehash + ".code")
        if not os.path.exists(code_only_path):
            try:
                # Try to dump identified code sections to its own file.
                # If it fails, try to use endianness and wordsize info to override
                # assumed input file format.
                cmd = shlex.split("objcopy -O binary " + sections +
                                  " " + binary + " " + code_only_path)
                call_cmd(cmd=cmd, shell=False, verbose=self.verbose)
            except subprocess.CalledProcessError as cpe:
                if metadata.endianness == "big" and metadata.wordsize == 32:
                    cmd = shlex.split("objcopy -O binary -I elf32-big " +
                                      sections + " " + binary + " " + code_only_path)
                    call_cmd(cmd=cmd, shell=False, verbose=self.verbose)
                elif metadata.endianness == "big" and metadata.wordsize == 64:
                    cmd = shlex.split("objcopy -O binary -I elf64-big " +
                                      sections + " " + binary + " " + code_only_path)
                    call_cmd(cmd=cmd, shell=False, verbose=self.verbose)
                elif metadata.endianness == "little" and metadata.wordsize == 32:
                    cmd = shlex.split("objcopy -O binary -I elf32-little " +
                                      sections + " " + binary + " " + code_only_path)
                    call_cmd(cmd=cmd, shell=False, verbose=self.verbose)
                elif metadata.endianness == "little" and metadata.wordsize == 64:
                    cmd = shlex.split("objcopy -O binary -I elf64-little " +
                                      sections + " " + binary + " " + code_only_path)
                    call_cmd(cmd=cmd, shell=False, verbose=self.verbose)
                else:
                    logging.error("Can't extract object code from " + binary + ". Endianness: " +
                                 metadata.endianness + ", wordsize: " + str(metadata.wordsize))

        if os.path.exists(code_only_path):
            metadata.only_code = code_only_path
            metadata.only_code_size = os.path.getsize(code_only_path)

        return metadata

    def run(self, filepath, output_directory, result):
        try:
            metadata = self.extract_information(filepath, output_directory)
            if metadata.only_code_size != -1:
                result.append(metadata)
                output_path = os.path.join(output_directory, metadata.filehash)
                if not os.path.exists(output_path):
                    shutil.copyfile(filepath, output_path)

        finally:
            self.threadLimiter.release()

    def init(self, thread_count, md5_buffer_size, verbose,
             input_json, output_path):
        self.threadLimiter = threading.BoundedSemaphore(int(thread_count))
        self.buffer_size = int(md5_buffer_size)
        self.verbose = verbose
        self.input_json = input_json
        self.output_path = output_path

    def extract_binaries(self):
        try:
            with open(self.input_json) as f:
                json_data = json.load(f)
        except IOError:
            logging.error("Failed to open JSON file: " + self.input_json)
            exit(1)

        if (not os.path.exists(self.output_path)):
            try:
                os.mkdir(self.output_path)
            except Exception as e:
                print("Failed to create the output directory:", self.output_path)
                logging.exception(e)
                sys.exit(1)

        with multiprocessing.Manager() as manager:
            for arch in json_data:
                results = []
                result = manager.list()
                threads = []
                for deb in json_data[arch]:
                    # save binaries to {arch}/binaries
                    output_directory = os.path.join(self.output_path,
                                                    arch)
                    if not os.path.exists(output_directory):
                        os.makedirs(output_directory)

                    # get a list of binaries and copy them to {arch}/binaries
                    binaries = self.find_binaries(
                        deb["package"] + "_extraction").decode("utf-8").split("\n")
                    for binary in [x for x in binaries if x != "" and ".code" not in x]:
                        # This was done because of a DEB package containing a colon
                        # in the path
                        self.threadLimiter.acquire()
                        filepath = ":".join(binary.split(":")[:-1])
                        t = threading.Thread(target=self.run, args=(
                            filepath, output_directory, result))
                        t.start()
                        threads.append(t)

                for t in threads:
                    t.join()
                for deb in result:
                    results.append(deb)
                metadata_location = os.path.join(
                    output_directory, arch + ".json")
                with open(metadata_location, 'w', encoding="utf-8") as result_file:
                    result_file.write(json.dumps(
                        results, default=lambda x: x.__dict__))
