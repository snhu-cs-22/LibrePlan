SELECT
    cast(strftime('%H', "start_time") AS INTEGER) AS "hour",
    AVG("actual_length" * 100/CAST("length" AS REAL)) AS "avg_percent"
FROM "activity_log" AS l
    INNER JOIN "activities" AS a
        ON a.id = l.activity_id
WHERE "date" BETWEEN :date_from AND :date_to
    AND "length" <> 0
    AND "name" LIKE :name
GROUP BY "hour"
ORDER BY "hour" ASC
