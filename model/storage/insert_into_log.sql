INSERT INTO "activity_log"
SELECT
    date(),
    :start_time,
    "id",
    :length,
    :actual_length,
    :optimal_length,
    :is_fixed,
    :is_rigid
FROM "activities"
WHERE "name"=:name
