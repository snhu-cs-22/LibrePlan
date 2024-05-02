from PyQt5.QtCore import QDir, QFile, QDateTime

class Backup:
    DATETIME_FORMAT = "yyyy-MM-dd-hh-mm-ss"

    def __init__(self, path, database, config):
        self.path = path
        self.database = database
        self.config = config

    def create_backup_name(self):
        """Creates a unique name for a backup file."""

        datetime_str = QDateTime.currentDateTime().toString(
            self.DATETIME_FORMAT
        )

        number = 0
        name = f"{self.path}/backup-{datetime_str}-{number:04}.db"
        while QFile.exists(name):
            number += 1
            name = f"{self.path}/backup-{datetime_str}-{number:04}.db"

        return name

    def export(self, path):
        db_file = QFile(self.database.path)
        db_file.copy(path)

    def create(self):
        # Make copy of database

        db_file = QFile(self.database.path)
        db_file.copy(self.create_backup_name())

        # Delete old backups

        number_of_backups = self.config.get_setting("user.backup/number_of_backups", 50)

        backup_dir = QDir(self.path)
        backup_dir.setFilter(QDir.Files)
        backup_dir.setNameFilters(["backup-????-??-??-??-??-??*.db"])
        backup_dir.setSorting(QDir.Time | QDir.Reversed)

        backups = backup_dir.entryInfoList()
        if len(backups) >= number_of_backups:
            for backup in backups[:-number_of_backups]:
                QFile.remove(backup.absoluteFilePath())

    def restore(self, path):
        self.create()
        self.database.disconnect()
        QFile.remove(self.database.path)
        QFile.copy(path, self.database.path)
