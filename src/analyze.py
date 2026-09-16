"""Fourth Down Lab V2 analytics and model comparison.

Outputs descriptive tables, charts, three success-prediction models, cross-validation
metrics, holdout metrics, feature importance, and an executive summary.
"""
from __future__ import annotations

from pathlib import Path
import json
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report, precision_score, recall_score, f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

warnings.filterwarnings("ignore", category=FutureWarning)

ROOT = Path(__file__).resolve().parents[1]
REAL = ROOT / "data" / "cleaned_play_by_play.csv"
DEMO = ROOT / "data" / "demo_play_by_play.csv"
OUT = ROOT / "outputs"
OUT.mkdir(parents=True, exist_ok=True)
source = REAL if REAL.exists() else DEMO
print(f"Analyzing {source.name}")
df = pd.read_csv(source)


def ensure_features(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    if "distance_bucket" not in frame.columns:
        frame["distance_bucket"] = pd.cut(frame["ydstogo"], [-1, 3, 6, 10, np.inf], labels=["Short (1-3)", "Medium (4-6)", "Long (7-10)", "Very Long (11+)"])
    if "field_zone" not in frame.columns:
        frame["field_zone"] = pd.cut(frame["yardline_100"], [-1, 20, 50, 80, 100], labels=["Red Zone", "Plus Territory", "Own Territory", "Backed Up"])
    if "red_zone" not in frame.columns:
        frame["red_zone"] = (frame["yardline_100"] <= 20).astype(int)
    if "goal_to_go" not in frame.columns:
        frame["goal_to_go"] = (frame["yardline_100"] <= frame["ydstogo"]).astype(int)
    if "late_down" not in frame.columns:
        frame["late_down"] = frame["down"].isin([3, 4]).astype(int)
    if "short_yardage" not in frame.columns:
        frame["short_yardage"] = (frame["ydstogo"] <= 3).astype(int)
    if "score_state" not in frame.columns:
        frame["score_state"] = np.select(
            [frame["score_differential"] >= 8, frame["score_differential"] <= -8],
            ["Leading by 8+", "Trailing by 8+"], default="Within 7 points"
        )
    return frame


df = ensure_features(df)

# ---------------- Descriptive tables ----------------
def summary(group_cols: list[str], extra: bool = False) -> pd.DataFrame:
    aggs = {
        "plays": ("play_id", "count"),
        "success_rate": ("success", "mean"),
        "avg_epa": ("epa", "mean"),
        "avg_yards": ("yards_gained", "mean"),
    }
    if extra:
        df["explosive"] = np.where(df["play_type"].eq("pass"), df["yards_gained"] >= 20, df["yards_gained"] >= 10).astype(int)
        aggs["explosive_rate"] = ("explosive", "mean")
    return df.groupby(group_cols, observed=True).agg(**aggs).reset_index()

by_down = summary(["down"])
by_type = summary(["play_type"])
by_zone = summary(["field_zone"])
by_distance = summary(["distance_bucket"])
by_team = summary(["posteam"], extra=True) if "posteam" in df.columns else pd.DataFrame()
by_situation = summary(["down", "distance_bucket", "field_zone", "play_type"])

by_down.to_csv(OUT / "summary_by_down.csv", index=False)
by_type.to_csv(OUT / "summary_by_play_type.csv", index=False)
by_zone.to_csv(OUT / "summary_by_field_zone.csv", index=False)
by_distance.to_csv(OUT / "summary_by_distance.csv", index=False)
by_situation.to_csv(OUT / "summary_by_situation.csv", index=False)
if not by_team.empty:
    by_team.to_csv(OUT / "team_rankings.csv", index=False)

# Descriptive pass/run leaders where both have enough samples.
comp = by_situation[by_situation["plays"] >= 30].copy()
if not comp.empty:
    p = comp.pivot_table(index=["down", "distance_bucket", "field_zone"], columns="play_type", values=["avg_epa", "plays"], aggfunc="first")
    needed = {("avg_epa", "pass"), ("avg_epa", "run")}
    if needed.issubset(p.columns):
        p = p.dropna(subset=list(needed)).copy()
        p["higher_observed_epa"] = np.where(p[("avg_epa", "pass")] > p[("avg_epa", "run")], "pass", "run")
        p["epa_gap"] = (p[("avg_epa", "pass")] - p[("avg_epa", "run")]).abs()
        p.reset_index().to_csv(OUT / "situational_play_type_comparison.csv", index=False)

# ---------------- Static charts ----------------
fig, ax = plt.subplots(figsize=(8, 5))
ax.bar(by_down["down"].astype(str), by_down["success_rate"] * 100)
ax.set_title("Offensive Success Rate by Down")
ax.set_xlabel("Down")
ax.set_ylabel("Success Rate (%)")
ax.grid(axis="y", alpha=0.25)
fig.tight_layout()
fig.savefig(OUT / "success_rate_by_down.png", dpi=180)
plt.close(fig)

fig, ax = plt.subplots(figsize=(8, 5))
ax.bar(by_type["play_type"].str.title(), by_type["avg_epa"])
ax.set_title("Average EPA by Play Type")
ax.set_xlabel("Play Type")
ax.set_ylabel("Average EPA")
ax.axhline(0, linewidth=1)
ax.grid(axis="y", alpha=0.25)
fig.tight_layout()
fig.savefig(OUT / "epa_by_play_type.png", dpi=180)
plt.close(fig)

fig, ax = plt.subplots(figsize=(9, 5))
ax.bar(by_distance["distance_bucket"].astype(str), by_distance["success_rate"] * 100)
ax.set_title("Success Rate by Distance to First Down")
ax.set_xlabel("Distance Bucket")
ax.set_ylabel("Success Rate (%)")
ax.tick_params(axis="x", rotation=15)
ax.grid(axis="y", alpha=0.25)
fig.tight_layout()
fig.savefig(OUT / "success_rate_by_distance.png", dpi=180)
plt.close(fig)

# ---------------- Predictive modeling ----------------
# Pre-snap/situation variables only. Never use yards_gained or EPA to predict success.
base_numeric = [
    "down", "ydstogo", "yardline_100", "qtr", "score_differential", "shotgun", "no_huddle",
    "red_zone", "goal_to_go", "late_down", "short_yardage"
]
optional_numeric = [
    "week", "quarter_seconds_remaining", "half_seconds_remaining", "game_seconds_remaining",
    "posteam_timeouts_remaining", "defteam_timeouts_remaining"
]
base_categorical = ["play_type", "distance_bucket", "field_zone", "score_state"]
optional_categorical = ["posteam", "defteam", "season_type"]

num_cols = [c for c in base_numeric + optional_numeric if c in df.columns]
cat_cols = [c for c in base_categorical + optional_categorical if c in df.columns]
model_cols = num_cols + cat_cols + ["success"]
model_df = df[model_cols].dropna().copy()

X = model_df.drop(columns="success")
y = model_df["success"].astype(int)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42, stratify=y
)

pre = ColumnTransformer([
    ("num", StandardScaler(), num_cols),
    ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_cols),
], remainder="drop")

models = {
    "Logistic Regression": LogisticRegression(max_iter=1500, class_weight="balanced", random_state=42),
    "Random Forest": RandomForestClassifier(
        n_estimators=250, max_depth=14, min_samples_leaf=8,
        class_weight="balanced_subsample", n_jobs=-1, random_state=42
    ),
    "Gradient Boosting": GradientBoostingClassifier(
        n_estimators=180, learning_rate=0.05, max_depth=3, random_state=42
    ),
}

cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
rows = []
fitted = {}
for name, estimator in models.items():
    print(f"Training {name}...")
    pipe = Pipeline([("preprocess", pre), ("model", estimator)])
    cv_scores = cross_val_score(pipe, X_train, y_train, cv=cv, scoring="roc_auc", n_jobs=1)
    pipe.fit(X_train, y_train)
    pred = pipe.predict(X_test)
    prob = pipe.predict_proba(X_test)[:, 1]
    rows.append({
        "model": name,
        "accuracy": accuracy_score(y_test, pred),
        "precision": precision_score(y_test, pred, zero_division=0),
        "recall": recall_score(y_test, pred, zero_division=0),
        "f1": f1_score(y_test, pred, zero_division=0),
        "test_roc_auc": roc_auc_score(y_test, prob),
        "cv_roc_auc_mean": cv_scores.mean(),
        "cv_roc_auc_std": cv_scores.std(),
    })
    fitted[name] = pipe

comparison = pd.DataFrame(rows).sort_values("test_roc_auc", ascending=False).reset_index(drop=True)
comparison.to_csv(OUT / "model_comparison.csv", index=False)
best_name = comparison.iloc[0]["model"]
best_pipe = fitted[best_name]

best_pred = best_pipe.predict(X_test)
(OUT / "classification_report.txt").write_text(classification_report(y_test, best_pred))

baseline_accuracy = max(y_test.mean(), 1 - y_test.mean())
metrics = {
    "dataset": source.name,
    "rows_analyzed": int(len(df)),
    "model_rows": int(len(model_df)),
    "target_success_rate": float(y.mean()),
    "majority_class_accuracy": float(baseline_accuracy),
    "best_model": str(best_name),
    "accuracy": float(comparison.iloc[0]["accuracy"]),
    "roc_auc": float(comparison.iloc[0]["test_roc_auc"]),
    "cv_roc_auc_mean": float(comparison.iloc[0]["cv_roc_auc_mean"]),
    "cv_roc_auc_std": float(comparison.iloc[0]["cv_roc_auc_std"]),
    "features_used": num_cols + cat_cols,
}
(OUT / "model_metrics.json").write_text(json.dumps(metrics, indent=2))

# Feature importance for tree-based best model; absolute coefficients for logistic fallback.
feature_names = best_pipe.named_steps["preprocess"].get_feature_names_out()
model_obj = best_pipe.named_steps["model"]
if hasattr(model_obj, "feature_importances_"):
    importance_values = model_obj.feature_importances_
else:
    importance_values = np.abs(model_obj.coef_[0])
importance = pd.DataFrame({"feature": feature_names, "importance": importance_values})
importance["feature"] = importance["feature"].str.replace("num__", "", regex=False).str.replace("cat__", "", regex=False)
importance.sort_values("importance", ascending=False).to_csv(OUT / "feature_importance.csv", index=False)

best_down = by_down.loc[by_down["success_rate"].idxmax()]
best_type = by_type.loc[by_type["avg_epa"].idxmax()]
summary_text = f"""# Analysis Summary — Fourth Down Lab V2

Dataset: **{source.name}**  
Plays analyzed: **{len(df):,}**

## Descriptive findings

- Highest observed success-rate down: **{int(best_down['down'])}** ({best_down['success_rate']:.1%}).
- Higher observed average EPA play type: **{str(best_type['play_type']).title()}** ({best_type['avg_epa']:.3f} EPA/play).

## Predictive modeling

- Models compared: Logistic Regression, Random Forest, Gradient Boosting.
- Best holdout model: **{best_name}**.
- Best holdout ROC AUC: **{metrics['roc_auc']:.3f}**.
- Best holdout accuracy: **{metrics['accuracy']:.1%}**.
- 3-fold CV ROC AUC: **{metrics['cv_roc_auc_mean']:.3f} ± {metrics['cv_roc_auc_std']:.3f}**.
- Majority-class accuracy baseline: **{metrics['majority_class_accuracy']:.1%}**.

> EPA and success-rate comparisons are descriptive. They do not by themselves establish the causal effect of calling pass vs. run because play selection depends on personnel, opponent, score, field position, game plan, and other context.
"""
(OUT / "analysis_summary.md").write_text(summary_text)
print(summary_text)
print("Model comparison:")
print(comparison.to_string(index=False, formatters={
    "accuracy": "{:.3f}".format,
    "precision": "{:.3f}".format,
    "recall": "{:.3f}".format,
    "f1": "{:.3f}".format,
    "test_roc_auc": "{:.3f}".format,
    "cv_roc_auc_mean": "{:.3f}".format,
    "cv_roc_auc_std": "{:.3f}".format,
}))
