import pytest

from model.storage import Database, DbConnectionError, QueryError

@pytest.fixture
def database_path(tmp_path):
    return str(tmp_path / "test.db")

@pytest.fixture
def unconnected_database(database_path):
    return Database(database_path)

def test_create_db_file_if_it_does_not_exist_upon_connection(unconnected_database):
    assert unconnected_database.connect()

def test_cannot_access_db_file_if_directory_does_not_exist(tmp_path):
    database = Database(str(tmp_path / "nonexistent" / "test.db"))
    with pytest.raises(DbConnectionError):
        database.connect()

def test_can_reconnect_after_disconnect(unconnected_database):
    unconnected_database.connect()
    unconnected_database.disconnect()

    assert unconnected_database.connect()

def test_connecting_to_the_same_database_twice_does_nothing(unconnected_database):
    unconnected_database.connect()

    query = unconnected_database.get_prepared_query(
        'SELECT COUNT("name") AS "count" FROM "activities"'
    )

    unconnected_database.execute_query(query)
    query.first()

    assert not unconnected_database.connect()
    assert query.value("count") is not None

def test_cannot_make_multiple_connections_to_same_database(database_path):
    database1 = Database(database_path)
    database2 = Database(database_path)

    assert database1.connect()
    assert not database2.connect()

def test_valid_query(database):
    query = database.get_prepared_query(
        'SELECT COUNT("name") AS "count" FROM "activities"'
    )

    database.execute_query(query)
    query.first()

    assert query.value("count") == 0

def test_invalid_query(database):
    query = database.get_prepared_query(
        'SELECT "bad_field" FROM "bad_table"'
    )

    with pytest.raises(QueryError) as execinfo:
        database.execute_query(query)
