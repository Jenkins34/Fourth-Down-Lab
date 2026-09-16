# Optional college-football version using cfbfastR.
# Usage: Rscript R/download_college_data.R 2024
# Requires: install.packages("cfbfastR")

args <- commandArgs(trailingOnly = TRUE)
year <- if (length(args) >= 1) as.integer(args[1]) else 2024

if (!requireNamespace("cfbfastR", quietly = TRUE)) {
  stop('Install cfbfastR first: install.packages("cfbfastR")')
}

cat("Loading college football play-by-play for", year, "...\n")
pbp <- cfbfastR::load_cfb_pbp(year)

# Keep/standardize fields used by the Python and SQL portions of this project.
needed <- c("play_id", "game_id", "posteam", "defteam", "down", "ydstogo",
            "yardline_100", "qtr", "score_differential", "play_type",
            "yards_gained", "EPA", "success", "shotgun", "no_huddle")
available <- intersect(needed, names(pbp))
clean <- pbp[, available, drop=FALSE]
if ("EPA" %in% names(clean)) names(clean)[names(clean) == "EPA"] <- "epa"

# Keep standard offensive plays when the fields are available.
if ("play_type" %in% names(clean)) clean <- clean[clean$play_type %in% c("run", "pass"), ]
if ("down" %in% names(clean)) clean <- clean[!is.na(clean$down) & clean$down >= 1 & clean$down <= 4, ]

write.csv(clean, "data/cleaned_play_by_play.csv", row.names=FALSE)
cat("Saved", nrow(clean), "college-football plays to data/cleaned_play_by_play.csv\n")
