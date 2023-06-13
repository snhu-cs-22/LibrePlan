SELECT
    "name",
    SUM("actual_length") AS "total_actual_length"
FROM "activity_log" AS l
    INNER JOIN "activities" AS a
        ON a.id = l.activity_id
WHERE "date" BETWEEN :date_from AND :date_to
    AND "actual_length" > 0
    AND "name" LIKE :name
GROUP BY "name"
ORDER BY "total_actual_length" DESC
