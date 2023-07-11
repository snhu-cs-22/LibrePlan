SELECT
    MIN(MIN("avg_actual_length"), MIN("avg_length")) AS "min_minute",
    MAX(MAX("avg_actual_length"), MAX("avg_length")) AS "max_minute",
    MIN("avg_percent") AS "min_percent",
    MAX("avg_percent") AS "max_percent"
FROM (
    SELECT
        AVG("actual_length") AS "avg_actual_length",
        AVG("length") AS "avg_length",
        AVG("actual_length" * 100/CAST("length" AS REAL)) AS "avg_percent"
    FROM "activity_log" AS l
        INNER JOIN "activities" AS a
            ON a.id = l.activity_id
    WHERE "date" BETWEEN :date_from AND :date_to
        AND "length" <> 0
        AND "name" LIKE :name
    GROUP BY "date"
)
