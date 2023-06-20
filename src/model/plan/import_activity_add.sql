INSERT INTO "plan" (
    "id",
    "order",
    "start_time",
    "name",
    "length",
    "is_fixed",
    "is_rigid"
)
VALUES (
    (
      CASE
        WHEN :id IN (
          SELECT "id"
          FROM "plan"
        ) THEN (
          SELECT MAX("id") + 1
          FROM "plan"
        )
        ELSE :id
      END
    ),
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
