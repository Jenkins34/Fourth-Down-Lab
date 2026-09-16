# Analysis Summary — Fourth Down Lab V2

Dataset: **cleaned_play_by_play.csv**  
Plays analyzed: **34,902**

## Descriptive findings

- Highest observed success-rate down: **4** (56.7%).
- Higher observed average EPA play type: **Pass** (0.026 EPA/play).

## Predictive modeling

- Models compared: Logistic Regression, Random Forest, Gradient Boosting.
- Best holdout model: **Gradient Boosting**.
- Best holdout ROC AUC: **0.606**.
- Best holdout accuracy: **58.4%**.
- 3-fold CV ROC AUC: **0.600 ± 0.001**.
- Majority-class accuracy baseline: **56.0%**.

> EPA and success-rate comparisons are descriptive. They do not by themselves establish the causal effect of calling pass vs. run because play selection depends on personnel, opponent, score, field position, game plan, and other context.
