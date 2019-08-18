"""
isadetect - "ML-based ISA detection (architecture and endianness of binary code/sequences)"

Copyright (C) Sami Kairajarvi <sami.kairajarvi@gmail.com>, 2019

See COPYRIGHT, AUTHORS, LICENSE for more details.
"""

from flask_restplus import Namespace, fields
from werkzeug.datastructures import FileStorage

class BinaryDTO:
    api = Namespace('binary', description='Binary related operations')

    parser = api.parser()
    parser.add_argument('binary', type=FileStorage, location='files')
    parser.add_argument('api_key', type=str, location='form')

    binary_output = api.model('Binary output', {
        'prediction': fields.String(),
        'prediction_probability': fields.Integer()
    })
