SELECT "name" FROM "activities"
UNION
SELECT "name" FROM "plan"
UNION
SELECT "name" FROM "tasks"
ORDER BY "name"
