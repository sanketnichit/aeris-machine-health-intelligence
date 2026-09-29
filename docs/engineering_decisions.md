# Engineering Notes

These are the main choices I made while building AERIS.

## Scope

I kept the first version to:

- machine-failure detection
- calibrated risk scoring
- model explanation
- one Streamlit interface
- a small secondary failure-mode study

I left things like RUL, streaming, counterfactuals and deployment for later instead of adding them just to make the project larger.

## Dataset

I used AI4I 2020 because it is small, easy to reproduce and useful for getting the whole pipeline working.

The downside is that it is synthetic, so I treat the numbers as results for this dataset rather than results from real machines.

## Leakage

The main model does not use:

- UDI
- Product ID
- TWF
- HDF
- PWF
- OSF
- RNF

The failure-mode flags are target information and the identifiers do not represent useful prediction inputs.

## Derived features

I added two simple features:

- temperature difference = process temperature - air temperature
- mechanical power = torque x rotational speed / 9549.2966

Both can be calculated from information available at prediction time.

The feature-ablation and split checks are there to see whether the improvement survives beyond one particular train/test split.

## Evaluation

The main reported number comes from a stratified 80/20 split with seed 42.

Model selection happens on the training part using cross-validation. The held-out test part is kept for the final reported evaluation.

Because failures are uncommon, PR-AUC is more useful here than using accuracy as the headline number. Precision, recall and F1 are reported as well.

## Model

The main model is HistGradientBoosting with sigmoid calibration.

I kept Random Forest as the first baseline. The gradient-boosting model was carried forward after the training-side comparison.

I did not add XGBoost as another dependency because the scikit-learn model was enough for this version of the project.

## Explainability

Permutation importance is useful for looking at overall feature ranking.

SHAP is used for individual predictions and a more detailed view of what changed the model output.

Neither one should be described as proof of physical root cause.

## Failure modes

AI4I can have more than one failure-mode flag on the same row, so I did not force everything into one mutually exclusive diagnosis.

HDF, PWF and OSF are used as separate secondary experiments. TWF and RNF were not carried forward as main console outputs because their benchmark signal was weaker/less stable.

## Streamlit app

The app uses the same feature engineering and model builders as the offline scripts.

I wanted to avoid having one model in the research code and another slightly different model hidden inside the UI.

## Extra checks

The repo also contains checks for:

- bootstrap uncertainty
- split sensitivity
- calibration
- error patterns
- feature-importance stability

These are there mainly because a single test split can make a project look more certain than it really is.

## Next step

The biggest next step would be testing the same approach on real industrial data. That would tell me more about whether it actually generalizes than adding more UI features.
