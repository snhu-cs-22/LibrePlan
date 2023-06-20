INSERT OR REPLACE INTO "plan" (
    "id",
    "order",
    "start_time",
    "name",
    "length",
    "is_fixed",
    "is_rigid"
)
VALUES (
    :id,
	:order,
    :start_time,
    :name,
    :length,
    :is_fixed,
    :is_rigid
)
