# Fourth Down Lab V2 — Resume Entry

Verified from the user's 2024 real-data run before the V2 upgrade: **34,902 NFL offensive plays**.

## Recommended Baylor-style entry

**FOURTH DOWN LAB — NFL OFFENSIVE EFFICIENCY ANALYTICS**  
*Independent Data Science Project*

- Analyzed **34,902 NFL offensive plays** using Python and SQL to evaluate offensive efficiency across down, distance, field position, play type, and game situation.
- Developed an interactive Streamlit dashboard with team, red-zone, distance, and late-down filters to communicate EPA, success rate, explosive-play rate, and situational trends.
- Built and compared logistic-regression, random-forest, and gradient-boosting classifiers using cross-validation to model offensive play success from pre-snap situation features.

## Optional model-metric version

Only use this after running `python src/analyze.py` and checking `outputs/model_metrics.json`:

- Compared three classification models and achieved a best holdout ROC AUC of **[0.XXX]** with **[MODEL NAME]**, using 3-fold cross-validation to evaluate generalization.

Do not replace the bracketed values until V2 produces the actual metrics.
