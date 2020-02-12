"""
isadetect - "ML-based ISA detection (architecture and endianness of binary code/sequences)"

Copyright (C) Sami Kairajarvi <sami.kairajarvi@gmail.com>, 2019

See COPYRIGHT, AUTHORS, LICENSE for more details.
"""

from flask_restplus import Resource
from app.model.binary import BinaryDTO
import http
import pandas as pd
import numpy
from flask import request
from flask_restplus import Resource
from app.helpers.calculate_features import UNKNOWN_ARCHITECTURE, get_architecture, calculate_features
import os
import sys
from flask import current_app as app

api = BinaryDTO.api
parser = BinaryDTO.parser
binary_output = BinaryDTO.binary_output

@api.route('/')
class BinaryUpload(Resource):
    @api.expect(parser)
    @api.response(http.HTTPStatus.OK, 'Success', binary_output)
    def post(self):
        # Read uploaded file into memory
        binary = request.files["binary"].read()

        # Calculate features out of the binary
        features = calculate_features(binary)

        # Transform features into pandas dataframe
        query_df = pd.DataFrame([features])
        query = pd.get_dummies(query_df)

        # Use trained model to predict the architecture
        model_type = request.args.get("type")
        try:
            model = app.config[model_type]
        except KeyError:
            return {"message": "Failed to find model to classify type: " + str(model_type)}

        prediction = model.predict(query).astype(numpy.int64)
        prediction_int = prediction[0].item()

        # If the architecture is unknown, return it
        if prediction_int == UNKNOWN_ARCHITECTURE:
            return {"prediction": "unknown", "prediction_probability": 1}

        # Calculate prediction probability
        prediction_proba = model.predict_proba(query)
        probability = prediction_proba[0][prediction_int - 1]

        # Fetch the string representation of the architecture
        return {"prediction": get_architecture(prediction_int), "prediction_probability": probability}
