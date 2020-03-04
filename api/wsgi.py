"""
isadetect - "ML-based ISA detection (architecture and endianness of binary code/sequences)"

Copyright (C) Sami Kairajarvi <sami.kairajarvi@gmail.com>, 2019

See COPYRIGHT, AUTHORS, LICENSE for more details.
"""

from flask import Flask
from app import bp
import argparse
import sys
import joblib

app = Flask(__name__)
app.register_blueprint(bp)

code_only_model = joblib.load("only_code.ml")
full_binary_model = joblib.load("full_binaries.ml")
fragment_model = joblib.load("fragments.ml")

app.config["code"] = code_only_model
app.config["full"] = full_binary_model
app.config["fragment"] = fragment_model

