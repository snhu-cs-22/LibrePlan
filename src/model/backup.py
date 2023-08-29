from PyQt5.QtCore import QDir, QFile, QDateTime

class Backup:
    DATETIME_FORMAT = "yyyy-MM-dd-hh-mm-ss"

    def __init__(self, path, database, config):
        self.path = path
        self.database = database
        self.config = config

    def backup_name(self, time):
        datetime = time.toString(
            self.DATETIME_FORMAT
        )
        return f"{self.path}/backup-{datetime}.db"

    def export(self, path):
        db_file = QFile(self.database.path)
        db_file.copy(path)

    def create(self):
        # Make copy of database

        db_file = QFile(self.database.path)
        db_file.copy(self.backup_name(QDateTime.currentDateTime()))

        # Delete old backups

        number_of_backups = self.config.get_setting("user.backup/number_of_backups", 50)

        backup_dir = QDir(self.path)
        backup_dir.setFilter(QDir.Files)
        backup_dir.setNameFilters(["backup-????-??-??-??-??-??.db"])
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
