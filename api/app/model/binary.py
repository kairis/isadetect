"""
isadetect - "ML-based ISA detection (architecture and endianness of binary code/sequences)"

Copyright (C) Sami Kairajarvi <sami.kairajarvi@gmail.com>, 2019

See COPYRIGHT, AUTHORS, LICENSE for more details.
"""

from flask_restx import Namespace, fields
from werkzeug.datastructures import FileStorage

class BinaryDTO:
    api = Namespace("binary", description="Binary related operations")

    parser = api.parser()
    parser.add_argument("binary", type=FileStorage, location="files")
    parser.add_argument("type", type=str, location="form", default="code", choices=("code", "full", "fragment"),
    help="Type of file to be analyzed.\n \
    Can be 'code' (only code sections), \
        'full' (full binary with code and data sections),\n or 'fragment' (small fragment to be analyzed, usually less than 2K bytes) ")

    prediction_output = api.model("Prediction output", {
        "architecture": fields.String(),
        "wordsize": fields.Integer(),
        "endianness": fields.String()
    })

    binary_output = api.model("Binary output", {
        "prediction": fields.Nested(prediction_output),
        "prediction_probability": fields.Integer()
    })

