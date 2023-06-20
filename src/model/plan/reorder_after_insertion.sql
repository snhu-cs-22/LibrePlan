UPDATE "plan"
SET "order" = "order" + :offset
WHERE "order" >= :insertion_index
