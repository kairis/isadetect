import sys
import os
import subprocess
import logging
import argparse

from configparser import ConfigParser, ExtendedInterpolation, SafeConfigParser
from tools.jigdo_to_iso import JigdoDownloader
from tools.mount_and_extract_deb import MountAndExtractDebs
from tools.deb_unpacker import UnpackDebianFiles
from tools.extract_binaries import BinaryExtractor
from tools.debian_port_converter import DebianPortConverter
from scraper.firmware.spiders.debian_ports_ftp import DebianPortSpider
from scraper.firmware.spiders.debian import DebianSpider
from scraper.firmware.spiders.debian_package_list import DebianPackageListSpider
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

config = SafeConfigParser(os.environ, interpolation=ExtendedInterpolation())
os.environ.setdefault('SCRAPY_SETTINGS_MODULE', "scraper.firmware.settings")


def check_requirements():
    try:
        print("---------------------")
        print("Checking if jigdo-lite exists")
        subprocess.check_output(["jigdo-lite", "--help"])
        print("Jigdo-lite found, continuing\n")
    except (subprocess.CalledProcessError, FileNotFoundError):
        logging.error(
            "jigdo-lite is not installed. Try 'sudo apt install jigdo-file'")
        sys.exit(1)

    try:
        print("---------------------")
        print("Checking if fuseiso exists")
        subprocess.check_output(["fuseiso", "-h"])
    except (subprocess.CalledProcessError, FileNotFoundError):
        logging.error(
            "fuseiso is not installed. Try 'sudo apt install fuseiso'")
        sys.exit(1)

    try:
        subprocess.check_output(["fusermount", "-V"])
    except (subprocess.CalledProcessError, FileNotFoundError):
        logging.error(
            "fusermount is not installed. Try 'sudo apt install fuseiso'")
        sys.exit(1)
    print("fuseiso found, continuing\n")

    try:
        print("---------------------")
        print("Checking if dpkg-deb exists")
        subprocess.check_output(["dpkg-deb", "--help"])
        print("dpkg-deb found, continuing\n")
    except (subprocess.CalledProcessError, FileNotFoundError):
        logging.error(
            "dpkg-deb is not installed")
        sys.exit(1)

    print("---------------------")
    print("Checking if list of debian packages exists")
    if not os.path.exists(config["crawler"]["iot_packages_location"]):
        print("Package list missing, downloading")
        c = CrawlerProcess(settings=get_project_settings())
        c.crawl(DebianPackageListSpider)
        c.start()
        print("Done downloading the list")
    else:
        print("Package list found, continuing\n")


def parse_config_file():
    ret = config.read("config.ini")
    if ret == []:
        print("Failed to read config.ini. Check that it exists.")
        sys.exit(1)

    # Check that the comma separated lists are well formatted
    try:
        iso_ignore_list = config["jigdo_downloader"]["iso_ignore_list"].split(
            ",")
    except:
        logging.error("Failed to parse jigdo_downloader.iso_ignore_list")
        sys.exit(1)

    try:
        downloaded_architectures = config["jigdo_downloader"]["downloaded_architectures"].split(
            ",")
    except:
        logging.error(
            "Failed to parse jigdo_downloader.downloaded_architectures")
        sys.exit(1)

    return iso_ignore_list, downloaded_architectures

# -----------------------
# Download ISO files using jigdo files


def download_iso_files(verbose=False):
    print("-----------------------")
    print("Starting to download ISO files from jigdos")
    jigdoDownloader = JigdoDownloader()

    jigdoDownloader.init(thread_count=config["dataset_gen"]["thread_count"],
                         crawler_output_path=config["dataset_gen"]["output_path"],
                         iso_ignore_list=iso_ignore_list,
                         downloaded_architectures=downloaded_architectures,
                         verbose=verbose,
                         input_json=config["crawler"]["iso_metadata"],
                         output_path=config["jigdo_downloader"]["output_path"])

    jigdoDownloader.download_jigdos()
    print("Downloading ISO files done\n")

# -----------------------
# Mount ISO files and extract debian files from there


def extract_debians(verbose=False):
    print("-----------------------")
    print("Starting to mount ISO files")
    isoExtractor = MountAndExtractDebs()
    isoExtractor.init(thread_count=config["deb_extractor"]["thread_count"],
                      iot_packages_location=config["crawler"]["iot_packages_location"],
                      verbose=verbose,
                      input_json=config["jigdo_downloader"]["output_path"],
                      output_path=config["deb_extractor"]["output_path"])

    isoExtractor.mount_and_extract_debs()
    print("Mounting ISO files done\n")

# -----------------------
# Unpack debian files from the extracted ISO files


def unpack_debians(verbose=False):
    print("-----------------------")
    print("Starting to unpack debian packages")
    debExtractor = UnpackDebianFiles()
    debExtractor.init(thread_count=config["deb_extractor"]["thread_count"],
                      verbose=verbose,
                      input_json=config["deb_extractor"]["output_path"],
                      output_path=config["unpack_debs"]["output_path"])
    debExtractor.unpack_debian_files()
    print("Unpacking debian packages done\n")

# Extract binary files from the extracted debian packages


def extract_binaries(verbose=False):
    print("-----------------------")
    print("Starting to extract binaries from the unpacked debian files")
    binaryExtractor = BinaryExtractor()
    binaryExtractor.init(thread_count=config["dataset_gen"]["thread_count"],
                         md5_buffer_size=config["binary_extractor"]["md5_buffer_size"],
                         verbose=verbose,
                         input_json=config["unpack_debs"]["output_path"],
                         output_path=config["binary_extractor"]["output_path"])
    binaryExtractor.extract_binaries()
    print("Extracting binaries done\n")


def print_prompt(args):
    print("Currently about to download the following versions: " +
          config["crawler"]["debian_versions"] + "\nand architectures: " + config["crawler"]["architectures"])
    print("\nYou can accept this prompt automatically with --accept")
    print("\nWarning! Downloading data for ONE version for ONE architecture will require about 40GB of free space\n")
    if not args.accept:
        ret = input(
            "I understand (input q to exit or any other key to continue): \n")
        if ret == "q":
            print("Exiting")
            sys.exit(0)


def convert_debian_ports():
    print("-----------------------")
    print("Starting to convert list of debian ports")
    debianPortConverter = DebianPortConverter()
    debianPortConverter.init(input_json=config["debian_port_downloader"]["output_path"],
                             crawler_output_path=config["dataset_gen"]["output_path"],
                             output_path=config["deb_extractor"]["output_path"])
    debianPortConverter.convert()
    print("Converting list of debian ports done")


def crawl_debian_jigdos(verbose=False):
    print("-----------------------")
    print("Starting to crawl jigdo files")
    if not verbose:
        from scrapy.utils.log import configure_logging
        configure_logging(install_root_handler=True)
        logging.disable(50)  # CRITICAL = 50
    c = CrawlerProcess(settings=get_project_settings())
    c.crawl(DebianSpider)
    c.start()
    print("Crawling for jigdo files done")


def crawl_debian_ports(verbose=False):
    print("-----------------------")
    print("Starting to crawl debian ports")
    if not verbose:
        from scrapy.utils.log import configure_logging
        configure_logging(install_root_handler=True)
        logging.disable(50)  # CRITICAL = 50
    c = CrawlerProcess(settings=get_project_settings())
    c.crawl(DebianPortSpider)
    c.start()
    print("Crawling for debian ports done")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process debian files. If you want to download one of the officially \
                                     supported architectures, add the architecture to 'architectures' in config.ini and run --all_deb. \
                                     If you want to download debian files for one of the debian ports, add it to 'port_architectures' in config.ini \
                                     and run --all_ports. You can also run each module separately.")
    parser.add_argument("--all_deb", action="store_true",
                        help="Run all modules for official debian architectures")
    parser.add_argument("--all_ports", action="store_true",
                        help="Run all modules for ported debian architectures")
    parser.add_argument("--isos", action="store_true",
                        help="Download ISO files")
    parser.add_argument("--extract_debians",
                        action="store_true", help="Extract debian files")
    parser.add_argument("--unpack", action="store_true",
                        help="Unpack debian files")
    parser.add_argument("--extract_binaries", action="store_true",
                        help="Extract binaries from the debian packages")
    parser.add_argument("--accept", "-a", action="store_true",
                        help="Accept warning about download size")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Produce more verbose output")
    args = parser.parse_args()

    # Check that environment is configured properly
    iso_ignore_list, downloaded_architectures = parse_config_file()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.isos:
        print_prompt(args)
        download_iso_files(verbose=args.verbose)
    elif args.extract_debians:
        extract_debians(verbose=args.verbose)
    elif args.unpack:
        unpack_debians(verbose=args.verbose)
    elif args.extract_binaries:
        extract_binaries(verbose=args.verbose)
    elif args.all_deb:
        check_requirements()
        print_prompt(args)
        crawl_debian_jigdos(verbose=args.verbose)
        download_iso_files(verbose=args.verbose)
        extract_debians(verbose=args.verbose)
        unpack_debians(verbose=args.verbose)
        extract_binaries(verbose=args.verbose)
    elif args.all_ports:
        check_requirements()
        crawl_debian_ports(verbose=args.verbose)
        convert_debian_ports()
        unpack_debians(verbose=args.verbose)
        extract_binaries(verbose=args.verbose)
    else:
        parser.print_help()
