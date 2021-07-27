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
    parser.add_argument("--input", help="Path to the trained ML model that will be used for all scenarios (code only, full and fragment)")
    parser.add_argument("--code_only_model", help="Path to the trained ML model with code only sections")
    parser.add_argument("--full_binary_model", help="Path to the trained ML model with code only sections")
    parser.add_argument("--fragment_model", help="Path to the trained ML model for code fragments")
    parser.add_argument("--port", type=int, help="Port where the API is exposed to. Defaults to 5000", default=5000)
    parser.add_argument("--debug", action="store_true", help="Used for debug prints")
    args = parser.parse_args()

    if args.input:
        try:
            model = joblib.load(args.input)
        except Exception as e:
            if args.debug:
                print(e)
            sys.exit("Failed to load model: " + args.input)
        app.config["code"] = model
        app.config["full"] = model
        app.config["fragment"] = model
    elif args.code_only_model:
        try:
            code_only_model = joblib.load(args.code_only_model)
        except Exception as e:
            if args.debug:
                print(e)
            sys.exit("Failed to load model: " + args.code_only_model)
        app.config["code"] = code_only_model
    else:
        parser.print_help()

    if args.full_binary_model:
        try:
            full_binary_model = joblib.load(args.full_binary_model)
        except:
            if args.debug:
                print(e)
            sys.exit("Failed to load model: " + args.full_binary_model)
        app.config["full"] = full_binary_model

    if args.fragment_model:
        try:
            fragment_model = joblib.load(args.fragment_model)
        except:
            if args.debug:
                print(e)
            sys.exit("Failed to load model: " + args.fragment_model)
        app.config["fragment"] = fragment_model

    app.run(debug=True, host='0.0.0.0', port=args.port)
