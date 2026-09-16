"""Generate deterministic synthetic play-by-play data for V2 offline testing."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "demo_play_by_play.csv"
rng = np.random.default_rng(42)
n = 15000
teams = [f"TEAM_{i:02d}" for i in range(1, 13)]
posteam = rng.choice(teams, n)
defteam = np.array([rng.choice([t for t in teams if t != p]) for p in posteam])
down = rng.choice([1, 2, 3, 4], size=n, p=[0.46, 0.29, 0.19, 0.06])
ydstogo = np.clip(np.rint(rng.gamma(2.3, 3.0, n) + 1), 1, 25).astype(int)
yardline_100 = rng.integers(1, 100, n)
qtr = rng.choice([1, 2, 3, 4], n, p=[0.24, 0.26, 0.24, 0.26])
score_diff = np.clip(np.rint(rng.normal(0, 10, n)), -35, 35).astype(int)
week = rng.integers(1, 19, n)
qsec = rng.integers(0, 901, n)
gsec = np.maximum(0, (4-qtr)*900 + qsec)
pass_prob = np.clip(0.46 + 0.055*(down-1) + 0.016*(ydstogo-7) - 0.003*score_diff, 0.25, 0.85)
play_type = np.where(rng.random(n) < pass_prob, "pass", "run")
shotgun = (((play_type == "pass") & (rng.random(n) < 0.78)) | ((play_type == "run") & (rng.random(n) < 0.44))).astype(int)
no_huddle = (rng.random(n) < (0.10 + 0.06*(qtr==4) + 0.05*(score_diff < -7))).astype(int)
base_yards = np.where(play_type == "pass", rng.normal(6.2, 8.5, n), rng.normal(4.4, 4.0, n))
base_yards += np.where(ydstogo <= 3, 0.6, 0) - np.where(yardline_100 <= 10, 0.7, 0)
yards = np.clip(np.rint(base_yards), -15, 80).astype(int)
epa = 0.035*yards - 0.018*ydstogo + 0.08*(play_type == "pass") - 0.06*(down == 3) - 0.12*(down == 4) + rng.normal(0, 0.55, n)
success_prob = 1 / (1 + np.exp(-(-0.25 + 0.10*yards - 0.035*ydstogo - 0.10*(down-1) + 0.10*(play_type == "pass"))))
success = (rng.random(n) < success_prob).astype(int)
epa += np.where(success == 1, 0.18, -0.18)

df = pd.DataFrame({
    "play_id": np.arange(1, n+1),
    "game_id": [f"DEMO_{i//130:04d}" for i in range(n)],
    "season": 2024,
    "season_type": "REG",
    "week": week,
    "posteam": posteam,
    "defteam": defteam,
    "down": down,
    "ydstogo": ydstogo,
    "yardline_100": yardline_100,
    "qtr": qtr,
    "quarter_seconds_remaining": qsec,
    "game_seconds_remaining": gsec,
    "score_differential": score_diff,
    "posteam_timeouts_remaining": rng.integers(0, 4, n),
    "defteam_timeouts_remaining": rng.integers(0, 4, n),
    "play_type": play_type,
    "yards_gained": yards,
    "epa": np.round(epa, 3),
    "success": success,
    "shotgun": shotgun,
    "no_huddle": no_huddle,
})
df["distance_bucket"] = pd.cut(df["ydstogo"], [-1,3,6,10,np.inf], labels=["Short (1-3)","Medium (4-6)","Long (7-10)","Very Long (11+)"])
df["field_zone"] = pd.cut(df["yardline_100"], [-1,20,50,80,100], labels=["Red Zone","Plus Territory","Own Territory","Backed Up"])
df["red_zone"] = (df["yardline_100"] <= 20).astype(int)
df["goal_to_go"] = (df["yardline_100"] <= df["ydstogo"]).astype(int)
df["late_down"] = df["down"].isin([3,4]).astype(int)
df["short_yardage"] = (df["ydstogo"] <= 3).astype(int)
df["score_state"] = np.select([df["score_differential"] >= 8, df["score_differential"] <= -8], ["Leading by 8+", "Trailing by 8+"], default="Within 7 points")
OUT.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT, index=False)
print(f"Wrote {len(df):,} synthetic demo plays to {OUT}")
