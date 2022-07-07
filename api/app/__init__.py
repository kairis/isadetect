"""
isadetect - "ML-based ISA detection (architecture and endianness of binary code/sequences)"

Copyright (C) Sami Kairajarvi <sami.kairajarvi@gmail.com>, 2019

See COPYRIGHT, AUTHORS, LICENSE for more details.
"""

from .controller.binary_controller import api as binary
from flask import Blueprint
from flask_restx import Api

bp = Blueprint('api', __name__)
api = Api(
    bp,
    title='API that provides ML-based ISA detection for binary code/sequences',
    version=0.01,
)

api.add_namespace(binary)

