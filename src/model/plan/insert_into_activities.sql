INSERT OR IGNORE
INTO "activities"("name")
SELECT "name"
FROM "plan"
WHERE "order" < (
    SELECT MAX("order")
    FROM "plan"
)
