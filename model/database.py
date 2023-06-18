from PyQt5.QtSql import QSqlDatabase, QSqlQuery
from PyQt5.QtCore import QFile, QIODevice, QTextStream

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
            print(f"Connection: {self.connection.lastError().text()}")
        return connected

    def disconnect(self):
        if self.connection.isOpen():
            if not self.connection.close():
                print(f"Connection: {self.connection.lastError().text()}")

    @staticmethod
    def query_from_file(path):
        """Allows the creation of SQL queries from .sql files

        Path separator must be '/'. '\' is not supported.

        File specified in `path` must not contain multiple queries (i.e.,
        separated by a ';').
        """

        file = QFile(path)
        if not file.open(QIODevice.ReadOnly | QIODevice.Text):
            return None

        text = QTextStream(file)
        query = QSqlQuery()
        query.prepare(text.readAll())
        file.close()
        return query

    @staticmethod
    def execute_query(query):
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
        query_successful = query.execBatch()
        if query_successful:
            q = query.executedQuery()
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
        create_table_query = Database.query_from_file("model/storage/create_activity_table.sql")
        Database.execute_query(create_table_query)
        create_table_query = Database.query_from_file("model/storage/create_log_table.sql")
        Database.execute_query(create_table_query)
