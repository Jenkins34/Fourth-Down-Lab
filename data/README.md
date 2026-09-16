# Data

`demo_play_by_play.csv` is a **synthetic demonstration dataset** generated only so the repository runs immediately without an internet connection. It must not be described as real NFL or college-football data.

For a portfolio/resume version, replace the demo file with real play-by-play data using one of the loaders:

- `python src/download_real_data.py --year 2024` for NFLverse/nflfastR data.
- `Rscript R/download_college_data.R 2024` for college-football data via cfbfastR.

Both loaders write `data/cleaned_play_by_play.csv`, which the rest of the project will automatically prefer over the demo file.
