# Interview Prep: Fourth Down Lab

## 30-second explanation
“I built Fourth Down Lab to connect my interest in football with data science. I created a reproducible pipeline that takes play-by-play data, cleans it in Python, loads it into SQLite for situational queries, compares offensive efficiency using EPA and success rate, and trains an interpretable logistic-regression model to estimate play success. I also built visualizations in Python and R and an interactive dashboard so a nontechnical user can explore the results.”

## Be ready to explain

- **EPA:** Expected Points Added measures how much a play changes the offense’s expected scoring value.
- **Success rate:** In this project, the source-provided success flag is used when available; otherwise positive EPA is the fallback.
- **Why logistic regression?** It is fast, interpretable, appropriate for a binary target, and provides a strong baseline before more complex models.
- **Why train/test split?** To evaluate how well the model generalizes to unseen plays instead of memorizing the training set.
- **Why SQL?** Situational football questions are naturally expressed as filtering, grouping, and aggregation problems.
- **Why both Python and R?** Python handles the main data/ML pipeline; R demonstrates cross-language analytics and visualization capability.

## Good technical follow-ups

1. Add cross-validation and compare logistic regression with random forest or gradient boosting.
2. Calibrate predicted probabilities and create reliability plots.
3. Add team/opponent strength, personnel, formation, motion, weather, and clock features when the data support them.
4. Separate model evaluation by down or game situation to check whether performance varies by subgroup.
5. Deploy the Streamlit app to a cloud platform.

## What not to say

Do not say you built the nflverse/cfbfastR data itself. Your project **uses** those open data sources. Also do not quote demo-data metrics as real-world findings.
