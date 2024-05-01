from PyQt5.QtSql import QSqlDatabase, QSqlQuery

from model.storage import queries

class DbConnectionError(Exception):
    def __init__(self, connection):
        e = connection.lastError()
        message = f"Failed to connect from database: {e.nativeErrorCode()} {e.type()} {e.text()}"
        super().__init__(message)

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
    """Data access object (DAO) for the application's database"""

    DATE_FORMAT = "yyyy-MM-dd"
    TIME_FORMAT = "hh:mm"

    def __init__(self, path):
        self.path = path

    def connect(self):
        """Connects to the Database.

        Returns `True` if it is a unique connection, `False` if one
        already exists, and raising a `DbConnectionError` if a
        connection cannot be made.
        """

        if QSqlDatabase.contains(self.path):
            return False

        self.connection = QSqlDatabase.addDatabase("QSQLITE", self.path)
        self.connection.setHostName("libreplan")

        if self.connection.isOpen():
            return False

        self.connection.setDatabaseName(self.path)
        if self.connection.open():
            self._create_tables()
            return True
        else:
            raise DbConnectionError(self.connection)

    def disconnect(self):
        if self.connection.isOpen():
            self.connection.close()
            QSqlDatabase.removeDatabase(self.path)
        else:
            print("Database connection is not open")

    def get_prepared_query(self, sql):
        query = QSqlQuery(self.connection)
        query.prepare(sql)
        return query

    def execute_query(self, query):
        """Executes a query with parameters bound to a single value.

        This method is good for running `SELECT` queries and queries
        with no parameters.

        Wrapper for `QSqlQuery.exec_()` with additional error and
        transaction handling.
        """

        self.connection.transaction()
        query_successful = query.exec_()
        if query_successful:
            self.connection.commit()
        else:
            self.connection.rollback()
            raise QueryError(query)
        return query_successful

    def execute_batch_query(self, query):
        """Executes a query with parameters bound to a list of values.

        Good for running `INSERT`, `UPDATE`, and `DELETE` queries.

        Wrapper for `QSqlQuery.execBatch()` with additional error and
        transaction handling.
        """

        self.connection.transaction()
        query_successful = query.execBatch()
        if query_successful:
            self.connection.commit()
        else:
            self.connection.rollback()
            raise QueryError(query)
        return query_successful

    def _create_tables(self):
        table_queries = [
            self.get_prepared_query(queries.create_plan_table),
            self.get_prepared_query(queries.create_tasklist_table),
            self.get_prepared_query(queries.create_activity_table),
            self.get_prepared_query(queries.create_log_table),
            self.get_prepared_query(queries.create_config_table),
        ]

        for query in table_queries:
            self.execute_query(query)
