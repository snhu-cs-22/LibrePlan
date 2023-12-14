import pytest

from model.storage import Database
from model.config import Config

@pytest.fixture
def database(tmp_path):
    database = Database(str(tmp_path / "test.db"))
    database.connect()
    yield database
    database.disconnect()

@pytest.fixture
def config(database):
    return Config(database)
