"""
isadetect - "ML-based ISA detection (architecture and endianness of binary code/sequences)"

Copyright (C) Sami Kairajarvi <sami.kairajarvi@gmail.com>, 2019

See COPYRIGHT, AUTHORS, LICENSE for more details.
"""

import sys
import numpy as np

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from keras.models import Sequential
from keras.layers import Dense
from keras import optimizers, regularizers
from keras.utils import to_categorical

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
    parser.add_argument("--classifier", type=str, choices=["logistic_regression_keras", "logistic_regression_scikit", "random_forest"])
    args = parser.parse_args()

    if args.input and args.output:
        try:
            # Load input data from file
            final_data = np.genfromtxt(args.input, delimiter=',', skip_header=True, filling_values=0)

            # Separate features (X) and the architecture (Y)
            final_X = final_data[:,0:-1]
            final_Y = final_data[:,-1]

            # Based on user choise, choose the classifier to be trained
            if args.classifier == "random_forest":
                final_model = RandomForestClassifier(n_estimators=100, max_depth=32, random_state=0, n_jobs=-1, verbose=True)
            elif args.classifier == "logistic_regression_keras":
                classes = 24
                final_model = Sequential()
                final_model.add(Dense(classes, activation='softmax', kernel_regularizer=regularizers.l1(0.0000001), input_shape=(293,)))
                final_model.compile(optimizer=optimizers.adam(lr=0.01),
                            loss='categorical_crossentropy',
                            metrics=['accuracy'])
                final_model.fit(final_X, to_categorical(final_Y), epochs=100, batch_size=32)
            elif args.classifier == "logistic_regression_scikit":
                final_model = LogisticRegression(penalty='l1', C=1000, multi_class="multinomial", solver="saga", max_iter=100, verbose=True, n_jobs=-1)
                final_model.fit(final_X, final_Y)

            # Save model to file
            joblib.dump(final_model, args.output)
        except Exception as e:
            logging.error("Failed to train the model")
            logging.error(e)
    else:
        parser.print_help()