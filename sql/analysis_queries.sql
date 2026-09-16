-- Fourth Down Lab V2: SQL analysis examples
-- Run after: python src/build_database.py

-- 1) Overall offensive profile
SELECT COUNT(*) AS plays,
       ROUND(AVG(yards_gained), 2) AS avg_yards,
       ROUND(AVG(epa), 3) AS avg_epa,
       ROUND(100.0 * AVG(success), 1) AS success_rate_pct
FROM plays;

-- 2) Team efficiency leaderboard
SELECT posteam,
       COUNT(*) AS plays,
       ROUND(AVG(epa), 3) AS avg_epa,
       ROUND(100.0 * AVG(success), 1) AS success_rate_pct,
       ROUND(AVG(yards_gained), 2) AS avg_yards
FROM plays
GROUP BY posteam
HAVING COUNT(*) >= 300
ORDER BY avg_epa DESC;

-- 3) Pass vs run by down and distance
SELECT down, distance_bucket, play_type,
       COUNT(*) AS plays,
       ROUND(AVG(epa), 3) AS avg_epa,
       ROUND(100.0 * AVG(success), 1) AS success_rate_pct
FROM plays
GROUP BY down, distance_bucket, play_type
HAVING COUNT(*) >= 30
ORDER BY down, distance_bucket, avg_epa DESC;

-- 4) Third-down conversion profile
SELECT distance_bucket,
       COUNT(*) AS plays,
       ROUND(AVG(epa), 3) AS avg_epa,
       ROUND(100.0 * AVG(success), 1) AS success_rate_pct
FROM plays
WHERE down = 3
GROUP BY distance_bucket
ORDER BY success_rate_pct DESC;

-- 5) Fourth-down profile
SELECT distance_bucket, play_type,
       COUNT(*) AS plays,
       ROUND(AVG(epa), 3) AS avg_epa,
       ROUND(100.0 * AVG(success), 1) AS success_rate_pct
FROM plays
WHERE down = 4
GROUP BY distance_bucket, play_type
HAVING COUNT(*) >= 20
ORDER BY distance_bucket, avg_epa DESC;

-- 6) Red-zone play type efficiency
SELECT play_type,
       COUNT(*) AS plays,
       ROUND(AVG(epa), 3) AS avg_epa,
       ROUND(100.0 * AVG(success), 1) AS success_rate_pct,
       ROUND(AVG(yards_gained), 2) AS avg_yards
FROM plays
WHERE yardline_100 <= 20
GROUP BY play_type
ORDER BY avg_epa DESC;

-- 7) Score-state tendencies
SELECT score_state, play_type,
       COUNT(*) AS plays,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY score_state), 1) AS play_share_pct,
       ROUND(AVG(epa), 3) AS avg_epa
FROM plays
GROUP BY score_state, play_type
ORDER BY score_state, play_share_pct DESC;

-- 8) Shotgun vs non-shotgun by play type
SELECT play_type,
       CASE WHEN shotgun = 1 THEN 'Shotgun' ELSE 'Non-shotgun' END AS alignment,
       COUNT(*) AS plays,
       ROUND(AVG(epa), 3) AS avg_epa,
       ROUND(100.0 * AVG(success), 1) AS success_rate_pct
FROM plays
GROUP BY play_type, shotgun
ORDER BY play_type, avg_epa DESC;

-- 9) Weekly offensive trend for one team (replace KC)
SELECT week,
       COUNT(*) AS plays,
       ROUND(AVG(epa), 3) AS avg_epa,
       ROUND(100.0 * AVG(success), 1) AS success_rate_pct
FROM plays
WHERE posteam = 'KC'
GROUP BY week
ORDER BY week;

-- 10) Backed-up offense
SELECT posteam,
       COUNT(*) AS plays,
       ROUND(AVG(epa), 3) AS avg_epa,
       ROUND(100.0 * AVG(success), 1) AS success_rate_pct
FROM plays
WHERE yardline_100 > 80
GROUP BY posteam
HAVING COUNT(*) >= 30
ORDER BY avg_epa DESC;
