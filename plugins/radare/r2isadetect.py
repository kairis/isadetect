"""
isadetect - "ML-based ISA detection (architecture and endianness of binary code/sequences)"

Copyright (C) Sami Kairajarvi <sami.kairajarvi@gmail.com>, 2019

See COPYRIGHT, AUTHORS, LICENSE for more details.
"""

import r2lang
import r2pipe
import requests

R2P = r2pipe.open()

# CONF: Configure according to 'src/api/main.py'
api_url = "https://isadetect.com/binary/"
api_key = "testkey"


def r2isadetect(_):

    def process(command):

        # Run commands only when "isadetect" is called
        if not command.startswith("isadetect"):
            return 0

        # Get file size through radare command "iZ"
        file_size_cmd = "iZ"
        file_size = R2P.cmd(file_size_cmd)

        # Get file size worth of bytes from the binary
        binary_in_hex_cmd = "p8 %s" % file_size
        binary_in_hex = R2P.cmd(binary_in_hex_cmd)

        # Send data to the API using multi-part form data
        data = {"binary": bytearray.fromhex(binary_in_hex.rstrip())}
        form = {"api_key": api_key}
        try:
            response = requests.request(
                "POST", verify=False, url=api_url, files=data, data=form)
        except Exception as e:
            print("Error identifying the architecture")

        # Print the results to the user
        try:
            response_json = response.json()
            print("Architecture:", response_json["prediction"]["architecture"],
                  "\nEndianness:", response_json["prediction"]["endianness"],
                  "\nWord size:", response_json["prediction"]["wordsize"],
                  "\nPrediction probabilty:", response_json["prediction_probability"]
                  )
        except Exception:
            print("Unable to identify architecture")

        # Set radare variables for architecture, endianness and word size
        # based on the predicted values
        R2P.cmd("e asm.arch=%s" % response_json["prediction"]["architecture"])
        if response_json["prediction"]["endianness"] == "big":
            R2P.cmd("e cfg.bigendian=true")
        else:
            R2P.cmd("e cfg.bigendian=false")
        R2P.cmd("e asm.bits=%s" % response_json["prediction"]["wordsize"])

    return {
        "name": "isadetect",
        "license": "MIT",
        "desc": "radare2 plugin to call APIs that provide ISA detection for binary code/sequences",
        "call": process
    }


if not r2lang.plugin("core", r2isadetect):
    print("An error occurred while registering r2isadetect!")

