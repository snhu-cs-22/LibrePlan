CREATE TABLE IF NOT EXISTS "activity_log" (
    "id" INTEGER NOT NULL,
    "date" TEXT NOT NULL CHECK (length("date") <= 10),
    "order" INTEGER NOT NULL,
    "start_time" TEXT NOT NULL CHECK (length("start_time") <= 5),
    "activity_id" INTEGER NOT NULL,
    "length" INTEGER NOT NULL,
    "actual_length" INTEGER NOT NULL,
    "optimal_length" INTEGER NOT NULL,
    "is_fixed" INTEGER NOT NULL CHECK ("is_fixed" IN (0, 1)),
    "is_rigid" INTEGER NOT NULL CHECK ("is_rigid" IN (0, 1)),

    PRIMARY KEY("id" AUTOINCREMENT),
    FOREIGN KEY("activity_id") REFERENCES activities("id")
)
