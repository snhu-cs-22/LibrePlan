UPDATE "plan"
SET
    "order" = :order,
    "start_time" = :start_time,
    "name" = :name,
    "length" = :length,
    "is_fixed" = :is_fixed,
    "is_rigid" = :is_rigid
WHERE "id" = :id
