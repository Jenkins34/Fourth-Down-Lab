# Fourth Down Lab - R visualization
# Usage: Rscript R/visualize.R

real_path <- "data/cleaned_play_by_play.csv"
demo_path <- "data/demo_play_by_play.csv"
input_path <- if (file.exists(real_path)) real_path else demo_path
cat("Using dataset:", input_path, "\n")

plays <- read.csv(input_path)
if (!dir.exists("outputs")) dir.create("outputs")

# Success rate by down
rate_by_down <- aggregate(success ~ down, data=plays, FUN=mean)
png("outputs/r_success_by_down.png", width=900, height=600)
barplot(rate_by_down$success * 100,
        names.arg=rate_by_down$down,
        main="Offensive Success Rate by Down (R)",
        xlab="Down", ylab="Success Rate (%)")
dev.off()

# EPA by play type
epa_by_type <- aggregate(epa ~ play_type, data=plays, FUN=mean)
png("outputs/r_epa_by_play_type.png", width=900, height=600)
barplot(epa_by_type$epa,
        names.arg=epa_by_type$play_type,
        main="Average EPA by Play Type (R)",
        xlab="Play Type", ylab="Average EPA")
abline(h=0)
dev.off()

cat("Wrote R visualizations to outputs/.\n")
