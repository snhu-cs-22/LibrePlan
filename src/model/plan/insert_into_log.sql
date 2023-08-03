INSERT INTO "activity_log" (
    "date",
    "order",
    "start_time",
    "activity_id",
    "length",
    "actual_length",
    "optimal_length",
    "is_fixed",
    "is_rigid"
)
SELECT
    date(),
    :order,
    :start_time,
    "id",
    :length,
    :actual_length,
    :optimal_length,
    :is_fixed,
    :is_rigid
FROM "activities"
WHERE "name"=:name
