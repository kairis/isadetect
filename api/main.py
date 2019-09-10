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

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run API that offers architecture detection endpoint for files")
    parser.add_argument("--input", help="Path to the trained ML model", required=True)
    args = parser.parse_args()

    if args.input:
        try:
            model = joblib.load(args.input)
        except:
            sys.exit("Failed to load model: " + args.input)
        app.config["model"] = model
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        parser.print_help()
