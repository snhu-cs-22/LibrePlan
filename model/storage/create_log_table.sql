CREATE TABLE IF NOT EXISTS "activity_log" (
    "date" TEXT NOT NULL CHECK (length("date") <= 10),
    "start_time" TEXT NOT NULL CHECK (length("start_time") <= 5),
    "activity_id" INTEGER NOT NULL,
    "length" INTEGER NOT NULL,
    "actual_length" INTEGER NOT NULL,
    "optimal_length" INTEGER NOT NULL,
    "is_fixed" INTEGER NOT NULL CHECK ("is_fixed" IN (0, 1)),
    "is_rigid" INTEGER NOT NULL CHECK ("is_fixed" IN (0, 1)),

    PRIMARY KEY("date", "start_time", "activity_id"),
    FOREIGN KEY("activity_id") REFERENCES activities("id")
)
