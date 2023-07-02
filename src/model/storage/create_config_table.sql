CREATE TABLE IF NOT EXISTS "config" (
    "key" TEXT NOT NULL UNIQUE,
    "value" BLOB,
    PRIMARY KEY("key")
)
