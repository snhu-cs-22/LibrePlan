from PyQt5.QtCore import QDate, QTime
from PyQt5.QtSql import QSqlDatabase, QSqlQuery

from plan import PlanTableModel, Activity

class Database:
    def __init__(self, *args):
        self._DATE_FORMAT = "yyyy-MM-dd"
        self._TIME_FORMAT = "hh:mm"
        self.connection = QSqlDatabase.addDatabase("QSQLITE")
        self.connection.setHostName("libreplan")

    def connect(self, db_path):
        self.connection.setDatabaseName(db_path)
        connected = self.connection.open()
        if connected:
            self._create_tables()
        else:
            print(f"Connection: {self.connection.lastError().text()}")
        return connected

    def _execute_query(self, query):
        query_successful = query.exec_()
        if not query_successful:
            print(f"Query: {query.lastError().text()}")
            self.connection.rollback()
        else:
            self.connection.commit()
        return query_successful

    def _create_tables(self):
        create_table_query = QSqlQuery()

        create_table_query.prepare(
            """
            CREATE TABLE IF NOT EXISTS "activities" (
                "id" INTEGER PRIMARY KEY,
                "name" TEXT UNIQUE NOT NULL CHECK (length("name") < 256)
            )
            """
        )
        self._execute_query(create_table_query)

        create_table_query.prepare(
            """
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
            """
        )
        self._execute_query(create_table_query)

    def archive_plan(self, plan):
        activity_query = QSqlQuery()
        log_query = QSqlQuery()
        activity_query.prepare('INSERT OR IGNORE INTO "activities"("name") VALUES (?)')
        log_query.prepare(
            """
            INSERT INTO "activity_log"
            SELECT
                date(),
                :start_time,
                "id",
                :length,
                :actual_length,
                :optimal_length,
                :is_fixed,
                :is_rigid
            FROM "activities" WHERE "name"=:name
            """
        )

        for i in range(plan.rowCount(None) - 1):
            activity = plan.get_activity(i)

            activity_query.addBindValue(activity.name)
            self._execute_query(activity_query)

            log_query.bindValue(":start_time", activity.start_time.toString(self._TIME_FORMAT))
            log_query.bindValue(":name", activity.name)
            log_query.bindValue(":length", activity.length)
            log_query.bindValue(":actual_length", activity.actual_length)
            log_query.bindValue(":optimal_length", activity.optimal_length)
            log_query.bindValue(":is_fixed", int(activity.is_fixed))
            log_query.bindValue(":is_rigid", int(activity.is_rigid))
            self._execute_query(log_query)
