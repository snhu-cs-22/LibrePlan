INSERT OR IGNORE INTO "tasks" (
    "id",
    "name",
    "value",
    "cost",
    "date_created",
    "deadline",
    "deadline_type"
)
VALUES (
    :id,
    :name,
    :value,
    :cost,
    :date_created,
    :deadline,
    :deadline_type
)
