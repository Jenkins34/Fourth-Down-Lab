@echo off
IF NOT EXIST data\cleaned_play_by_play.csv (
  echo No real dataset found; generating synthetic demo data for pipeline testing.
  python src\generate_demo_data.py
) ELSE (
  echo Real dataset found; preserving data\cleaned_play_by_play.csv.
)
python src\build_database.py
python src\analyze.py
echo Done. Launch V2 with: streamlit run app.py
