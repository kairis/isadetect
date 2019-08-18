"""
isadetect - "ML-based ISA detection (architecture and endianness of binary code/sequences)"

Copyright (C) Sami Kairajarvi <sami.kairajarvi@gmail.com>, 2019

See COPYRIGHT, AUTHORS, LICENSE for more details.
"""

import re

UNKNOWN_ARCHITECTURE = 99
ARCHITECTURES = ['alpha', 'amd64', 'arm64', 'armel', 'armhf', 'hppa', 'i386', 'ia64', 'm68k',
                 'mips', 'mips64el', 'mipsel', 'powerpc', 'powerpcspe', 'ppc64', 'ppc64el', 'riscv64', 's390', 's390x',
                 'sh4', 'sparc', 'sparc64', 'x32']
#ARCHITECTURES = ['powerpcspe']


def get_architecture(argument):
    switcher = {
        1: {"architecture": "alpha", "endianness": "little", "wordsize": 64},
        2: {"architecture": "amd64", "endianness": "little", "wordsize": 64},
        3: {"architecture": "arm", "endianness": "little", "wordsize": 64},
        4: {"architecture": "arm", "endianness": "little", "wordsize": 32},
        5: {"architecture": "armhf", "endianness": "little", "wordsize": 32},
        6: {"architecture": "hppa", "endianness": "big", "wordsize": 32},
        7: {"architecture": "i386", "endianness": "little", "wordsize": 32},
        8: {"architecture": "ia64", "endianness": "little", "wordsize": 64},
        9: {"architecture": "m68k", "endianness": "big", "wordsize": 32},
        10: {"architecture": "mips", "endianness": "big", "wordsize": 32},
        11: {"architecture": "mips", "endianness": "little", "wordsize": 64},
        12: {"architecture": "mips", "endianness": "little", "wordsize": 32},
        13: {"architecture": "powerpc", "endianness": "big", "wordsize": 32},
        14: {"architecture": "powerpcspe", "endianness": "big", "wordsize": 32},
        15: {"architecture": "powerpc", "endianness": "big", "wordsize": 64},
        16: {"architecture": "powerpc", "endianness": "little", "wordsize": 64},
        17: {"architecture": "riscv", "endianness": "little", "wordsize": 64},
        18: {"architecture": "s390", "endianness": "big", "wordsize": 32},
        19: {"architecture": "s390x", "endianness": "big", "wordsize": 64},
        20: {"architecture": "sh4", "endianness": "little", "wordsize": 32},
        21: {"architecture": "sparc", "endianness": "big", "wordsize": 32},
        22: {"architecture": "sparc", "endianness": "big", "wordsize": 64},
        23: {"architecture": "x32", "endianness": "little", "wordsize": 32},
        # Wishlist:
        24: "avr",
        25: "cuda",
        26: "arc",
        27: "c6x",
        28: "h8300",
        29: "hppa64",
        30: "microblaze",
        31: "nios2",
        32: "sh2",
        33: "riscv32",
        34: "xtensa",
        UNKNOWN_ARCHITECTURE: "unknown"
    }
    return switcher.get(argument, "unknown")


class BFD():
    HEADERS_WRITTEN = False

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

        # powerpcspe SPE instruction
        self.fps["powerpcspe_spe_instruction_isel"] = br"[\x7d-\x7f][\x00-\xff]{2}(\x1e|\x5e|\x9e)"
        self.fps["powerpcspe_spe_instruction_evl"] = br"(\x10|\x11|\x12|\x13)[\x00-\xff]{2}(\x01|\xc1|\xc8|\xc9|\xc0|\xd0|\xd1|\xda)"

    def init(self):
        self.initialize_fingerprints()
        # Build regexs out of fingerprints
        for key, value in self.fps.items():
            regex = re.compile(value)
            self.fps[key] = regex
        self.byte_frequencies = []
        self.fingerprints = []

    def calc_features(self, analyze_this):
        byte_count = 0

        # Calculate byte frequency
        byte_frequency_counter = [0] * 256
        for byte in analyze_this:
            byte_count += 1
            byte_frequency_counter[byte] += 1
        try:
            byte_frequency_counter = [(x / byte_count)
                                      for x in byte_frequency_counter]
        except Exception as e:
            print(e)
            return

        # Find matches for function epilog and prolog fingerprints
        fingerprints = {}
        for key, value in self.fps.items():
            i = 0
            for match in value.finditer(analyze_this):
                i += 1
            fingerprints[key] = i / byte_count

        self.byte_frequencies.append(byte_frequency_counter)
        self.fingerprints.append(fingerprints)

    def compose_data(self):
        data = []
        data = data + self.byte_frequencies[0]
        for key in sorted(self.fingerprints[0]):
            data.append(self.fingerprints[0][key])

        return data


def calculate_features(input_file):
    bfd = BFD()
    bfd.init()
    bfd.calc_features(input_file)
    data = bfd.compose_data()
    return data
