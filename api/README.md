# Requirements

You first need to create the ML model file.
See 'ml' folder for more details.
The 'ml' folder contains some initial sample file to get you started.

From pip:
- flask-restplus
- pandas
- scikit-learn

# How to run

1. ```python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt```
2. Run main.py giving path to the trained random forest classifier model as input parameter, for example:
```python3 main.py --input ../ml/samples/final_model.pkl```
3. It is possible to use different models for different cases, for example define logistic regression for full binaries with --full_binary_model. See --help for more information.
4. You can find API running at http://localhost:5000. If you go to it with your browser, you will get a simple API interface,
which can be used to upload files for analysis.
