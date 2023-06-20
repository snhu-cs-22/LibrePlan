INSERT INTO "tasks" (
    "id",
    "name",
    "value",
    "cost",
    "date_created",
    "deadline",
    "deadline_type"
)
VALUES (
    (
      CASE
        WHEN :id IN (
          SELECT "id"
          FROM "tasks"
        ) THEN (
          SELECT MAX("id") + 1
          FROM "tasks"
        )
        ELSE :id
      END
    ),
    :name,
    :value,
    :cost,
    :date_created,
    :deadline,
    :deadline_type
)
