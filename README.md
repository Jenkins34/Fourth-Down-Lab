# 🏈 Fourth Down Lab V2
## NFL Offensive Efficiency Analytics

**Python • SQL • R • Machine Learning • Streamlit • Data Visualization**

Fourth Down Lab V2 is an end-to-end data science portfolio project that studies how game situation relates to NFL offensive efficiency. The project demonstrates data acquisition, cleaning, feature engineering, SQL analysis, exploratory analytics, machine-learning model comparison, interactive visualization, and technical communication.

## V2 upgrades

- Real nflverse download pipeline with macOS-friendly `requests` + `certifi`
- Team and week filters
- Red-zone and late-down filters
- Explosive-play metric
- Third- and fourth-down situation analysis
- Pass-vs-run EPA comparisons by down, distance, and field zone
- Team efficiency rankings
- Three-model ML comparison: Logistic Regression, Random Forest, Gradient Boosting
- 3-fold cross-validation plus holdout ROC AUC
- Feature importance output
- Expanded SQLite analysis queries

## Real-data workflow

```bash
python src/download_real_data.py --year 2024
python src/build_database.py
python src/analyze.py
streamlit run app.py
```

The dashboard automatically prefers `data/cleaned_play_by_play.csv` when it exists.

## Predictive-modeling design

The target is binary play success. Prediction features are limited to pre-snap/situation information such as down, distance, field position, quarter, score differential, play type, shotgun/no-huddle, team/opponent, and time remaining when available. Outcome variables such as `yards_gained` and `epa` are intentionally excluded from the model features to avoid leakage.

V2 compares:

1. Logistic Regression — interpretable baseline
2. Random Forest — nonlinear tree ensemble
3. Gradient Boosting — sequential boosted-tree model

The analysis writes `outputs/model_comparison.csv`, `outputs/model_metrics.json`, `outputs/classification_report.txt`, and `outputs/feature_importance.csv`.

## Interpretation warning

EPA and success-rate differences are observational. A higher observed EPA for pass or run in one situation does **not** prove that calling that play type causes the improvement. Personnel, opponent, score, game plan, and selection effects matter. This limitation is intentionally documented because defensible interpretation is part of good data science.

## Resume use

After running V2 on real data, use the verified row count and your newly generated model metrics. Do not invent model-performance claims. The existing 2024 run verified **34,902 offensive plays** before the V2 upgrade; rerun `src/analyze.py` to generate V2 model-comparison metrics.

Suggested resume wording:

**FOURTH DOWN LAB — NFL OFFENSIVE EFFICIENCY ANALYTICS**  
*Independent Data Science Project*

- Analyzed **34,902 NFL offensive plays** using Python and SQL to evaluate efficiency across down, distance, field position, play type, and game situation.
- Engineered an interactive Streamlit dashboard with team, red-zone, distance, and late-down filters to compare EPA, success rate, explosive-play rate, and situational trends.
- Built and compared logistic-regression, random-forest, and gradient-boosting classifiers with cross-validation to model offensive play success using pre-snap situation features.

## Data source

Real NFL data: nflverse / nflfastR public play-by-play releases.
