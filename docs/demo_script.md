# AERIS demo notes

## Before the demo

Make sure the AI4I CSV is available at data/ai4i2020.csv and start the app with:

    streamlit run app.py

The app uses the same model code as the main scripts.

## Start

Say something like:

> "AERIS is my machine-failure prediction project. I used the AI4I 2020 dataset and built a small pipeline that takes machine readings, predicts failure risk, and shows what the model used for that prediction."

## Example 1: failed machine

Use this test-set row:

- Product type: **L**
- Air temperature: **300.8 K**
- Process temperature: **309.9 K**
- Rotational speed: **1312 rpm**
- Torque: **65.3 Nm**
- Tool wear: **192 min**
- Temperature delta: **9.1 K**
- Mechanical power: **9.0 kW**

This row is from the test set used for the project result, so don't change the values during the demo.

The current model gives roughly **93.1%** risk.

Explain it like this:

> "This is the model's estimated risk for this benchmark row. It is not a real machine-health percentage."

Then point at the threshold and say:

> "I kept the risk score separate from the alert threshold because the right threshold depends on how costly false alarms and missed failures are."

## Explanation

Show the SHAP chart.

A simple explanation is:

> "These values show which inputs moved the tree model toward or away from the failure class. They explain the model, not the physical machine."

## Failure modes

Show HDF, PWF and OSF.

Say:

> "The dataset can have more than one failure flag on a row, so I show these as separate scores instead of pretending there is always one diagnosis."

TWF and RNF are left out of the main panel because their results were much weaker in the tests.

## If they ask what is interesting about the project

Say:

> "The dashboard is the easy part. I also checked the class imbalance, compared models, tested the two derived features, checked calibration, looked at errors and tried different train/test splits. The main limitation is that AI4I is synthetic."

## Backup example

Use this row if the first one is inconvenient:

- Product type: **L**
- Air temperature: **297.6 K**
- Process temperature: **308.6 K**
- Rotational speed: **1576 rpm**
- Torque: **32.7 Nm**
- Tool wear: **83 min**
- Temperature delta: **11.0 K**
- Mechanical power: **5.4 kW**

This row is labelled non-failure in the benchmark and gives about **0.07%** risk with the current model.
