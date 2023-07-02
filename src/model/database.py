from PyQt5.QtCore import QStandardPaths
from PyQt5.QtSql import QSqlDatabase, QSqlQuery

import model.storage.queries as queries

class QueryError(Exception):
    def __init__(self, query):
        q = query.executedQuery()
        b = query.boundValues()
        e = query.lastError()
        message = f"Error code {e.nativeErrorCode()}, type {e.type()}: {e.text()}\n" \
            f"Query\n" \
            f"{q}\n" \
            f"was bound to these values: {b}"
        super().__init__(message)

class Database:
    PATH_APPDATA = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation) + "/LibrePlan"
    PATH_DB = PATH_APPDATA + "/collection.db"

    connection = QSqlDatabase.addDatabase("QSQLITE")
    connection.setHostName("libreplan")

    DATE_FORMAT = "yyyy-MM-dd"
    TIME_FORMAT = "hh:mm"

    @classmethod
    def connect(cls):
        if not cls.connection.isOpen():
            cls.connection.setDatabaseName(cls.PATH_DB)
            connected = cls.connection.open()
            if connected:
                cls._create_tables()
            else:
                e = cls.connection.lastError()
                print(f"Failed to connect from database: {e.nativeErrorCode()} {e.type()} {e.text()}")
            return connected
        return True

    @classmethod
    def disconnect(cls):
        if cls.connection.isOpen():
            cls.connection.close()
        else:
            print("Database connection is not open")

    @staticmethod
    def get_prepared_query(sql):
        query = QSqlQuery()
        query.prepare(sql)
        return query

    @staticmethod
    def execute_query(query):
        """Executes a query with parameters bound to a single value.

        This method is good for running `SELECT` queries and queries
        with no parameters.

        Wrapper for `QSqlQuery.exec_()` with additional error and
        transaction handling.
        """

        Database.connection.transaction()
        query_successful = query.exec_()
        if query_successful:
            Database.connection.commit()
        else:
            Database.connection.rollback()
            raise QueryError(query)
        return query_successful

    @staticmethod
    def execute_batch_query(query):
        """Executes a query with parameters bound to a list of values.

        Good for running `INSERT`, `UPDATE`, and `DELETE` queries.

        Wrapper for `QSqlQuery.execBatch()` with additional error and
        transaction handling.
        """

        Database.connection.transaction()
        query_successful = query.execBatch()
        if query_successful:
            Database.connection.commit()
        else:
            Database.connection.rollback()
            raise QueryError(query)
        return query_successful

    @staticmethod
    def _create_tables():
        table_queries = [
            Database.get_prepared_query(queries.create_plan_table),
            Database.get_prepared_query(queries.create_tasklist_table),
            Database.get_prepared_query(queries.create_activity_table),
            Database.get_prepared_query(queries.create_log_table),
            Database.get_prepared_query(queries.create_config_table),
        ]

        for query in table_queries:
            Database.execute_query(query)

Database.connect()
