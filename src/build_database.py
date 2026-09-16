"""Build a SQLite database from the active Fourth Down Lab dataset."""
from pathlib import Path
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REAL = ROOT / "data" / "cleaned_play_by_play.csv"
DEMO = ROOT / "data" / "demo_play_by_play.csv"
DB = ROOT / "outputs" / "football_analytics.db"
source = REAL if REAL.exists() else DEMO

print(f"Using dataset: {source.name}")
df = pd.read_csv(source)
DB.parent.mkdir(parents=True, exist_ok=True)
with sqlite3.connect(DB) as conn:
    df.to_sql("plays", conn, if_exists="replace", index=False)
    for col in ["down", "play_type", "posteam", "defteam", "week", "field_zone", "distance_bucket"]:
        if col in df.columns:
            conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{col} ON plays({col})")
print(f"Created {DB} with {len(df):,} rows")
