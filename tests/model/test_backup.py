import pytest
import time

from PyQt5.QtCore import QDir

from model.backup import Backup
from model.config import Config
from model.storage import Database

@pytest.fixture
def backup_path(tmp_path):
    path = str(tmp_path / "backups")
    QDir().mkdir(path)
    return path

@pytest.fixture
def backup(backup_path, database, config):
    return Backup(backup_path, database, config)

def test_backup_rotation(backup, backup_path, config):
    backup_dir = QDir(backup_path)
    backup_dir.setFilter(QDir.Files)

    number_of_backups = 5
    config.set_setting("user.backup/number_of_backups", number_of_backups)

    for i in range(number_of_backups + 2):
        backup.create()

    assert len(backup_dir.entryInfoList()) == number_of_backups
