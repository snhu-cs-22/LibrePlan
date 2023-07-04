from PyQt5.QtSql import QSqlDatabase, QSqlQuery

import model.storage.queries as queries

class Database:
    connection = QSqlDatabase.addDatabase("QSQLITE")
    connection.setHostName("libreplan")

    DATE_FORMAT = "yyyy-MM-dd"
    TIME_FORMAT = "hh:mm"

    def connect(self, db_path):
        self.connection.setDatabaseName(db_path)
        connected = self.connection.open()
        if connected:
            self._create_tables()
        else:
            e = self.connection.lastError()
            print(f"Failed to connect from database: {e.nativeErrorCode()} {e.type()} {e.text()}")
        return connected

    def disconnect(self):
        if self.connection.isOpen():
            self.connection.close()
        else:
            print("Database connection is not open")

    @staticmethod
    def get_prepared_query(sql):
        query = QSqlQuery()
        query.prepare(sql)
        return query

    @staticmethod
    def execute_query(query):
        Database.connection.transaction()
        query_successful = query.exec_()
        if query_successful:
            Database.connection.commit()
        else:
            q = query.executedQuery()
            e = query.lastError()
            print(
                f"Query \"{q}\" failed:",
                f"\tQuery error {e.nativeErrorCode()} ({e.type()}): {e.text()}"
            )
            Database.connection.rollback()
        return query_successful

    @staticmethod
    def execute_batch_query(query):
        Database.connection.transaction()
        query_successful = query.execBatch()
        if query_successful:
            Database.connection.commit()
        else:
            q = query.executedQuery()
            e = query.lastError()
            print(
                f"Query \"{q}\" failed:",
                f"\tQuery error {e.nativeErrorCode()} ({e.type()}): {e.text()}"
            )
            Database.connection.rollback()
        return query_successful

    def _create_tables(self):
        table_queries = [
            Database.get_prepared_query(queries.create_plan_table),
            Database.get_prepared_query(queries.create_tasklist_table),
            Database.get_prepared_query(queries.create_activity_table),
            Database.get_prepared_query(queries.create_log_table),
        ]

        for query in table_queries:
            Database.execute_query(query)
