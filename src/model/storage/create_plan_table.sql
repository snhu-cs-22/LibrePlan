CREATE TABLE IF NOT EXISTS "plan" (
    "id" INTEGER PRIMARY KEY,
    "order" INTEGER NOT NULL,
    "start_time" TEXT NOT NULL CHECK (length("start_time") <= 5),
    "name" TEXT NOT NULL CHECK (length("name") < 256) DEFAULT "Activity",
    "length" INTEGER NOT NULL DEFAULT 0,
    "actual_length" INTEGER NOT NULL DEFAULT 0,
    "is_fixed" INTEGER NOT NULL CHECK ("is_fixed" IN (0, 1)),
    "is_rigid" INTEGER NOT NULL CHECK ("is_rigid" IN (0, 1))
)
