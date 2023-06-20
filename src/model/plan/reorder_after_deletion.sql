UPDATE "plan"
SET "order" = "order" - 1
WHERE "order" >= :deletion_index
