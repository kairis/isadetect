# How to run

1. ```python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt```
2. Run train.py by giving path to the CSV file containing the extracted features of binaries (input), path to the output file, which will contain the trained classifier, and the desired classifier to be used, for example:
```python3 train.py --input ../dataset_gen/output/features.csv --output trained_model.ml --classifier random_forest```

The examples folder includes a sample that is a trained random forest classifier for all the 23 architectures supported by this toolset.
