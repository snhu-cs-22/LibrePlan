CREATE TABLE IF NOT EXISTS "activities" (
    "id" INTEGER PRIMARY KEY,
    "name" TEXT UNIQUE NOT NULL CHECK (length("name") < 256) DEFAULT "Activity"
)
