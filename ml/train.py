"""
isadetect - "ML-based ISA detection (architecture and endianness of binary code/sequences)"

Copyright (C) Sami Kairajarvi <sami.kairajarvi@gmail.com>, 2019

See COPYRIGHT, AUTHORS, LICENSE for more details.
"""

import sys
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib
import argparse
import os
import logging

def file_path(string):
    if os.path.isfile(string):
        return string
    else:
        raise NotADirectoryError(string)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train a random forest classifier based on the input CSV")
    parser.add_argument("--input", type=file_path, required=True)
    parser.add_argument("--output", type=str, required=True)
    args = parser.parse_args()

    if args.input and args.output:
        try:
            final_data = np.genfromtxt(args.input, delimiter=',', skip_header=True, filling_values=0)

            final_X = final_data[:,0:-1]
            final_Y = final_data[:,-1]

            final_model = RandomForestClassifier(n_estimators=100, max_depth=32, random_state=0, n_jobs=-1, verbose=True)
            final_model.fit(final_X, final_Y)
            joblib.dump(final_model, args.output)
        except Exception as e:
            logging.error("Failed to train the model")
            logging.error(e)
    else:
        parser.print_help()