# Fourth Down Lab V2 — Upgrade Instructions

This ZIP is designed to be extracted **inside your existing `Fourth_Down_Lab` folder**. It does not contain a `data/` folder, so your real `data/cleaned_play_by_play.csv` will not be deleted.

## Mac / VS Code

1. Stop Streamlit with `Control + C`.
2. Download `Fourth_Down_Lab_V2_Upgrade.zip` to your Downloads folder.
3. Make sure the VS Code terminal is still inside your existing `Fourth_Down_Lab` folder.
4. Run:

```bash
unzip -o ~/Downloads/Fourth_Down_Lab_V2_Upgrade.zip -d .
```

5. Update packages:

```bash
python -m pip install -r requirements.txt
```

6. Re-download 2024 data so the new week/time fields are included:

```bash
python src/download_real_data.py --year 2024
```

7. Rebuild and analyze:

```bash
python src/build_database.py
python src/analyze.py
```

8. Launch V2:

```bash
streamlit run app.py
```

## What to look for

The new dashboard title should say **Fourth Down Lab V2** and include tabs for Overview, Situational Lab, Team Rankings, Model Lab, and Data Explorer.
