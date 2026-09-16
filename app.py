"""Fourth Down Lab V2: interactive NFL offensive-efficiency dashboard.

Run:
    streamlit run app.py
"""
from __future__ import annotations

from pathlib import Path
import json
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
REAL = ROOT / "data" / "cleaned_play_by_play.csv"
DEMO = ROOT / "data" / "demo_play_by_play.csv"
OUT = ROOT / "outputs"
source = REAL if REAL.exists() else DEMO

st.set_page_config(page_title="Fourth Down Lab V2", page_icon="🏈", layout="wide")


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "distance_bucket" not in df.columns:
        df["distance_bucket"] = pd.cut(
            df["ydstogo"], [-1, 3, 6, 10, np.inf],
            labels=["Short (1-3)", "Medium (4-6)", "Long (7-10)", "Very Long (11+)"]
        )
    if "field_zone" not in df.columns:
        df["field_zone"] = pd.cut(
            df["yardline_100"], [-1, 20, 50, 80, 100],
            labels=["Red Zone", "Plus Territory", "Own Territory", "Backed Up"]
        )
    if "red_zone" not in df.columns:
        df["red_zone"] = (df["yardline_100"] <= 20).astype(int)
    if "goal_to_go" not in df.columns:
        df["goal_to_go"] = (df["yardline_100"] <= df["ydstogo"]).astype(int)
    if "score_state" not in df.columns:
        df["score_state"] = np.select(
            [df["score_differential"] >= 8, df["score_differential"] <= -8],
            ["Leading by 8+", "Trailing by 8+"],
            default="Within 7 points",
        )
    if "explosive" not in df.columns:
        df["explosive"] = np.where(
            df["play_type"].eq("pass"), df["yards_gained"] >= 20, df["yards_gained"] >= 10
        ).astype(int)
    return df


@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    return add_features(pd.read_csv(path))


df = load_data(str(source))

st.title("🏈 Fourth Down Lab V2")
st.caption("NFL Offensive Efficiency Analytics | Python • SQL • R • Machine Learning • Streamlit")

if source.name.startswith("demo_"):
    st.warning("Synthetic demo data is active. Run the real-data loader before presenting numerical results as NFL findings.")
else:
    season_text = ""
    if "season" in df.columns and df["season"].notna().any():
        vals = sorted(df["season"].dropna().astype(int).unique().tolist())
        season_text = f" | Season: {', '.join(map(str, vals))}"
    st.success(f"Real-data mode: {source.name}{season_text}")

# ---------------- Sidebar filters ----------------
st.sidebar.header("Situation Filters")

if "posteam" in df.columns:
    teams = sorted(df["posteam"].dropna().astype(str).unique())
    selected_team = st.sidebar.selectbox("Offense", ["All teams"] + teams)
else:
    selected_team = "All teams"

if "week" in df.columns and df["week"].notna().any():
    weeks = sorted(df["week"].dropna().astype(int).unique().tolist())
    selected_weeks = st.sidebar.multiselect("Week", weeks, default=weeks)
else:
    selected_weeks = []

play_types = sorted(df["play_type"].dropna().astype(str).unique())
selected_play_types = st.sidebar.multiselect("Play type", play_types, default=play_types)
selected_downs = st.sidebar.multiselect("Down", [1, 2, 3, 4], default=[1, 2, 3, 4])

bucket_order = ["Short (1-3)", "Medium (4-6)", "Long (7-10)", "Very Long (11+)"]
available_buckets = [b for b in bucket_order if b in set(df["distance_bucket"].astype(str))]
selected_buckets = st.sidebar.multiselect("Distance", available_buckets, default=available_buckets)

zone_order = ["Red Zone", "Plus Territory", "Own Territory", "Backed Up"]
available_zones = [z for z in zone_order if z in set(df["field_zone"].astype(str))]
selected_zones = st.sidebar.multiselect("Field zone", available_zones, default=available_zones)

quarter_options = sorted(
    df["qtr"].dropna().astype(int).unique().tolist()
)

quarter_labels = {
    1: "Q1",
    2: "Q2",
    3: "Q3",
    4: "Q4",
    5: "OT",
    6: "2OT",
}

selected_quarters = st.sidebar.multiselect(
    "Quarter",
    quarter_options,
    default=quarter_options,
    format_func=lambda q: quarter_labels.get(q, f"{q - 4}OT")
)
red_zone_only = st.sidebar.checkbox("Red zone only")
late_down_only = st.sidebar.checkbox("3rd & 4th down only")

filtered = df[
    df["play_type"].isin(selected_play_types)
    & df["down"].isin(selected_downs)
    & df["distance_bucket"].astype(str).isin(selected_buckets)
    & df["field_zone"].astype(str).isin(selected_zones)
    & df["qtr"].isin(selected_quarters)
].copy()

if selected_team != "All teams":
    filtered = filtered[filtered["posteam"] == selected_team]
if selected_weeks and "week" in filtered.columns:
    filtered = filtered[filtered["week"].astype("Int64").isin(selected_weeks)]
if red_zone_only:
    filtered = filtered[filtered["red_zone"] == 1]
if late_down_only:
    filtered = filtered[filtered["down"].isin([3, 4])]

if filtered.empty:
    st.error("No plays match these filters. Widen the situation filters in the sidebar.")
    st.stop()

# ---------------- KPI row ----------------
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Plays", f"{len(filtered):,}")
c2.metric("Success rate", f"{filtered['success'].mean():.1%}")
c3.metric("Avg EPA/play", f"{filtered['epa'].mean():.3f}")
c4.metric("Avg yards", f"{filtered['yards_gained'].mean():.2f}")
c5.metric("Explosive rate", f"{filtered['explosive'].mean():.1%}")

st.caption("Explosive play = 20+ yards on a pass or 10+ yards on a run. EPA comparisons are descriptive, not causal play-calling recommendations.")

# ---------------- Tabs ----------------
overview_tab, situational_tab, teams_tab, model_tab, data_tab = st.tabs(
    ["Overview", "Situational Lab", "Team Rankings", "Model Lab", "Data Explorer"]
)

with overview_tab:
    left, right = st.columns(2)
    by_down = filtered.groupby("down", as_index=False).agg(
        success_rate=("success", "mean"), avg_epa=("epa", "mean"), plays=("play_id", "count")
    )
    fig = px.bar(
        by_down, x="down", y="success_rate", text=by_down["success_rate"].map(lambda x: f"{x:.1%}"),
        hover_data={"avg_epa": ":.3f", "plays": True}, title="Success Rate by Down"
    )
    fig.update_yaxes(tickformat=".0%")
    left.plotly_chart(fig, width="stretch")

    by_type = filtered.groupby("play_type", as_index=False).agg(
        avg_epa=("epa", "mean"), success_rate=("success", "mean"), plays=("play_id", "count")
    )
    fig = px.bar(
        by_type, x="play_type", y="avg_epa", text=by_type["avg_epa"].map(lambda x: f"{x:.3f}"),
        hover_data={"success_rate": ":.1%", "plays": True}, title="EPA by Play Type"
    )
    right.plotly_chart(fig, width="stretch")

    left2, right2 = st.columns(2)
    by_distance = filtered.groupby("distance_bucket", observed=True, as_index=False).agg(
        success_rate=("success", "mean"), avg_epa=("epa", "mean"), plays=("play_id", "count")
    )
    fig = px.bar(
        by_distance, x="distance_bucket", y="success_rate", category_orders={"distance_bucket": bucket_order},
        hover_data={"avg_epa": ":.3f", "plays": True}, title="Success Rate by Distance"
    )
    fig.update_yaxes(tickformat=".0%")
    left2.plotly_chart(fig, width="stretch")

    by_zone = filtered.groupby("field_zone", observed=True, as_index=False).agg(
        avg_epa=("epa", "mean"), success_rate=("success", "mean"), plays=("play_id", "count")
    )
    fig = px.bar(
        by_zone, x="field_zone", y="avg_epa", category_orders={"field_zone": zone_order},
        hover_data={"success_rate": ":.1%", "plays": True}, title="EPA by Field Zone"
    )
    right2.plotly_chart(fig, width="stretch")

with situational_tab:
    st.subheader("Pass vs. Run by Situation")
    situation = filtered.groupby(["down", "distance_bucket", "play_type"], observed=True).agg(
        plays=("play_id", "count"), avg_epa=("epa", "mean"), success_rate=("success", "mean")
    ).reset_index()
    situation = situation[situation["plays"] >= 20]
    fig = px.bar(
        situation, x="distance_bucket", y="avg_epa", color="play_type", barmode="group",
        facet_col="down", category_orders={"distance_bucket": bucket_order},
        hover_data={"plays": True, "success_rate": ":.1%"},
        title="Observed EPA: Pass vs. Run by Down and Distance"
    )
    st.plotly_chart(fig, width="stretch")

    st.subheader("Observed EPA Leader by Situation")
    comp = filtered.groupby(["down", "distance_bucket", "field_zone", "play_type"], observed=True).agg(
        plays=("play_id", "count"), avg_epa=("epa", "mean"), success_rate=("success", "mean")
    ).reset_index()
    comp = comp[comp["plays"] >= 30]
    if not comp.empty:
        pivot = comp.pivot_table(
            index=["down", "distance_bucket", "field_zone"], columns="play_type", values=["avg_epa", "plays"], aggfunc="first"
        )
        if {("avg_epa", "pass"), ("avg_epa", "run")}.issubset(pivot.columns):
            leader = pivot.dropna(subset=[("avg_epa", "pass"), ("avg_epa", "run")]).copy()
            leader["higher_observed_epa"] = np.where(
                leader[("avg_epa", "pass")] > leader[("avg_epa", "run")], "Pass", "Run"
            )
            leader["epa_gap"] = (leader[("avg_epa", "pass")] - leader[("avg_epa", "run")]).abs()
            leader = leader.reset_index()
            display = pd.DataFrame({
                "Down": leader["down"],
                "Distance": leader["distance_bucket"].astype(str),
                "Field zone": leader["field_zone"].astype(str),
                "Higher observed EPA": leader["higher_observed_epa"],
                "EPA gap": leader["epa_gap"].round(3),
                "Pass plays": leader[("plays", "pass")].astype("Int64"),
                "Run plays": leader[("plays", "run")].astype("Int64"),
            }).sort_values("EPA gap", ascending=False)
            st.dataframe(display.head(30), width="stretch", hide_index=True)
            st.caption("Use this as descriptive evidence only. Selection effects and personnel/game-plan context can influence observed EPA.")
        else:
            st.info("Not enough pass and run samples under the current filters to compare situations.")
    else:
        st.info("Not enough plays under the current filters for situation-level comparisons.")

    col1, col2 = st.columns(2)
    third = filtered[filtered["down"] == 3]
    if not third.empty:
        third_tbl = third.groupby("distance_bucket", observed=True, as_index=False).agg(
            plays=("play_id", "count"), success_rate=("success", "mean"), avg_epa=("epa", "mean")
        )
        fig = px.bar(third_tbl, x="distance_bucket", y="success_rate", category_orders={"distance_bucket": bucket_order}, title="3rd-Down Success by Distance")
        fig.update_yaxes(tickformat=".0%")
        col1.plotly_chart(fig, width="stretch")
    fourth = filtered[filtered["down"] == 4]
    if not fourth.empty:
        fourth_tbl = fourth.groupby("distance_bucket", observed=True, as_index=False).agg(
            plays=("play_id", "count"), success_rate=("success", "mean"), avg_epa=("epa", "mean")
        )
        fig = px.bar(fourth_tbl, x="distance_bucket", y="success_rate", category_orders={"distance_bucket": bucket_order}, title="4th-Down Success by Distance")
        fig.update_yaxes(tickformat=".0%")
        col2.plotly_chart(fig, width="stretch")

with teams_tab:
    if "posteam" not in filtered.columns or filtered["posteam"].nunique() < 2:
        st.info("Team rankings need multiple offenses in the current filter selection.")
    else:
        team_tbl = filtered.groupby("posteam", as_index=False).agg(
            plays=("play_id", "count"), avg_epa=("epa", "mean"), success_rate=("success", "mean"),
            avg_yards=("yards_gained", "mean"), explosive_rate=("explosive", "mean")
        )
        min_plays = max(50, int(len(filtered) * 0.005))
        team_tbl = team_tbl[team_tbl["plays"] >= min_plays].sort_values("avg_epa", ascending=False)
        st.caption(f"Showing offenses with at least {min_plays:,} plays under the active filters.")
        fig = px.scatter(
            team_tbl, x="success_rate", y="avg_epa", size="plays", text="posteam",
            hover_data={"avg_yards": ":.2f", "explosive_rate": ":.1%"},
            title="Team Efficiency: Success Rate vs. EPA/play"
        )
        fig.update_xaxes(tickformat=".0%")
        fig.update_traces(textposition="top center")
        st.plotly_chart(fig, width="stretch")
        display = team_tbl.rename(columns={
            "posteam": "Team", "plays": "Plays", "avg_epa": "EPA/play", "success_rate": "Success rate",
            "avg_yards": "Yards/play", "explosive_rate": "Explosive rate"
        }).copy()
        display["EPA/play"] = display["EPA/play"].round(3)
        display["Success rate"] = display["Success rate"].map(lambda x: f"{x:.1%}")
        display["Yards/play"] = display["Yards/play"].round(2)
        display["Explosive rate"] = display["Explosive rate"].map(lambda x: f"{x:.1%}")
        st.dataframe(display, width="stretch", hide_index=True)

with model_tab:
    st.subheader("Model Comparison")
    comparison_path = OUT / "model_comparison.csv"
    metrics_path = OUT / "model_metrics.json"
    importance_path = OUT / "feature_importance.csv"

    if comparison_path.exists():
        comparison = pd.read_csv(comparison_path)
        st.dataframe(comparison, width="stretch", hide_index=True)
        best_row = comparison.sort_values("test_roc_auc", ascending=False).iloc[0]
        st.metric("Best holdout ROC AUC", f"{best_row['test_roc_auc']:.3f}", help=f"Model: {best_row['model']}")
        fig = px.bar(comparison, x="model", y="test_roc_auc", hover_data=["accuracy", "cv_roc_auc_mean", "cv_roc_auc_std"], title="Holdout ROC AUC by Model")
        st.plotly_chart(fig, width="stretch")
    elif metrics_path.exists():
        metrics = json.loads(metrics_path.read_text())
        st.json(metrics)
        st.info("Run `python src/analyze.py` after installing V2 to generate the full model comparison.")
    else:
        st.info("Run `python src/analyze.py` to generate model metrics.")

    if importance_path.exists():
        importance = pd.read_csv(importance_path).head(15).sort_values("importance")
        fig = px.bar(importance, x="importance", y="feature", orientation="h", title="Top Model Features")
        st.plotly_chart(fig, width="stretch")

    st.caption("Models use pre-snap/situation variables only; outcome variables such as yards gained and EPA are intentionally excluded from prediction features.")

with data_tab:
    cols = [
        c for c in ["season", "week", "game_id", "posteam", "defteam", "down", "ydstogo", "yardline_100", "qtr",
                    "score_differential", "play_type", "yards_gained", "epa", "success", "shotgun", "no_huddle"]
        if c in filtered.columns
    ]
    st.dataframe(filtered[cols].head(1000), width="stretch", hide_index=True)
    st.caption(f"Displaying up to 1,000 of {len(filtered):,} filtered plays.")
