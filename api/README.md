Pre-requisites
--------------

You first need to create the ML model file.
See 'ml' folder for more details.
The 'ml' folder contains some initial sample file to get you started.

Setup
-----

python3 -m venv .venv

. .venv/bin/activate

pip3 install -r requirements.txt

Usage
-----

First, set environment value "ISADETECT_MODEL_FILE" to point to the model, for example:

export ISADETECT_MODEL_FILE="../ml/samples/final_model.pkl"

API can be starated with "python3 main.py"

You can go to http://localhost:5000 for a simple API interface, which
can be used to upload files for analysis.
