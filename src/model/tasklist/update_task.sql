UPDATE "tasks"
SET
	name = :name,
	value = :value,
	cost = :cost,
	date_created = :date_created,
	deadline = :deadline,
	deadline_type = :deadline_type
WHERE "id" = :id
