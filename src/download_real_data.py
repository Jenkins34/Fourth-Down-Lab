"""Download and clean NFL play-by-play data from nflverse.

Usage:
    python src/download_real_data.py --year 2024

Writes data/cleaned_play_by_play.csv.
V2 uses requests + certifi so macOS Python installs are less likely to hit
urllib SSL certificate errors.
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path
import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "cleaned_play_by_play.csv"
KEEP = [
    "play_id", "game_id", "season", "season_type", "week", "game_date",
    "home_team", "away_team", "posteam", "defteam", "down", "ydstogo",
    "yardline_100", "qtr", "quarter_seconds_remaining", "half_seconds_remaining",
    "game_seconds_remaining", "score_differential", "posteam_timeouts_remaining",
    "defteam_timeouts_remaining", "play_type", "yards_gained", "epa", "success",
    "shotgun", "no_huddle", "goal_to_go",
]


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["distance_bucket"] = pd.cut(
        df["ydstogo"], bins=[-1, 3, 6, 10, float("inf")],
        labels=["Short (1-3)", "Medium (4-6)", "Long (7-10)", "Very Long (11+)"]
    )
    df["field_zone"] = pd.cut(
        df["yardline_100"], bins=[-1, 20, 50, 80, 100],
        labels=["Red Zone", "Plus Territory", "Own Territory", "Backed Up"]
    )
    df["red_zone"] = (df["yardline_100"] <= 20).astype(int)
    if "goal_to_go" not in df.columns:
        df["goal_to_go"] = (df["yardline_100"] <= df["ydstogo"]).astype(int)
    else:
        df["goal_to_go"] = df["goal_to_go"].fillna((df["yardline_100"] <= df["ydstogo"]).astype(int)).astype(int)
    df["score_state"] = np.select(
        [df["score_differential"] >= 8, df["score_differential"] <= -8],
        ["Leading by 8+", "Trailing by 8+"], default="Within 7 points"
    )
    df["late_down"] = df["down"].isin([3, 4]).astype(int)
    df["short_yardage"] = (df["ydstogo"] <= 3).astype(int)
    return df


def download(year: int) -> pd.DataFrame:
    url = (
        "https://github.com/nflverse/nflverse-data/releases/download/pbp/"
        f"play_by_play_{year}.csv.gz"
    )
    print(f"Downloading {year} NFL play-by-play data from nflverse...")
    response = requests.get(url, timeout=180)
    response.raise_for_status()
    df = pd.read_csv(io.BytesIO(response.content), compression="gzip", low_memory=False)

    available = [c for c in KEEP if c in df.columns]
    missing = [c for c in KEEP if c not in df.columns]
    if missing:
        print("Columns not present and skipped:", ", ".join(missing))

    df = df[available].copy()
    df = df[df["play_type"].isin(["run", "pass"])]
    df = df[df["down"].between(1, 4, inclusive="both")]
    df = df.dropna(subset=["ydstogo", "yardline_100", "yards_gained", "epa", "score_differential"])

    if "success" not in df.columns:
        df["success"] = (df["epa"] > 0).astype(int)
    else:
        fallback = (df["epa"] > 0).astype(int)
        df["success"] = df["success"].fillna(fallback).astype(int)

    for col in ("shotgun", "no_huddle"):
        if col not in df.columns:
            df[col] = 0
        df[col] = df[col].fillna(0).astype(int)

    if "season" not in df.columns:
        df["season"] = year

    return add_features(df)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2024)
    args = parser.parse_args()
    df = download(args.year)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"Saved {len(df):,} offensive plays to {OUT}")
    if "week" in df.columns:
        print(f"Weeks represented: {int(df['week'].min())}-{int(df['week'].max())}")
    print(f"Offenses represented: {df['posteam'].nunique() if 'posteam' in df.columns else 'N/A'}")


if __name__ == "__main__":
    main()
