#!/usr/bin/env bash
set -e
if [ ! -f data/cleaned_play_by_play.csv ]; then
  echo "No real dataset found; generating synthetic demo data for pipeline testing."
  python src/generate_demo_data.py
else
  echo "Real dataset found; preserving data/cleaned_play_by_play.csv."
fi
python src/build_database.py
python src/analyze.py
echo "Done. Launch V2 with: streamlit run app.py"
