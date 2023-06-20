CREATE TABLE IF NOT EXISTS "tasks" (
    "id" INTEGER PRIMARY KEY,
    "name" TEXT NOT NULL CHECK (length("name") < 256) DEFAULT "Task",
    "value" INTEGER NOT NULL DEFAULT 0,
    "cost" INTEGER NOT NULL DEFAULT 0,
    "date_created" TEXT NOT NULL CHECK (length("date_created") <= 10),
    "deadline" TEXT CHECK (length("deadline") <= 10),
    "deadline_type" INTEGER NOT NULL DEFAULT 1
)
