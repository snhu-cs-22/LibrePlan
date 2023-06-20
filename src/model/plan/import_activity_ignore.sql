INSERT OR IGNORE INTO "plan" (
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
    (
      CASE
        WHEN :order IN (
          SELECT "order"
          FROM "plan"
        ) THEN (
          SELECT MAX("order") + 1
          FROM "plan"
        )
        ELSE :order
      END
    ),
    :start_time,
    :name,
    :length,
    :is_fixed,
    :is_rigid
)
