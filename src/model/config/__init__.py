from model.storage import Database

from model.config import queries

class Config:
    """Interface for application settings"""

    def __init__(self, database):
        self.database = database
        self.query_get = self.database.get_prepared_query(queries.get_setting)
        self.query_has = self.database.get_prepared_query(queries.has_setting)
        self.query_set = self.database.get_prepared_query(queries.insert_setting)

    def has_setting(self, key):
        self.query_has.bindValue(":key", key)
        self.database.execute_query(self.query_has)
        self.query_has.first()
        return bool(self.query_has.value("count"))

    def get_setting(self, key, default_value):
        if not self.has_setting(key):
            self.set_setting(key, default_value)

        self.query_get.bindValue(":key", key)
        self.database.execute_query(self.query_get)
        self.query_get.first()
        value = self.query_get.value("value")

        # Cast value to type of default value
        return type(default_value)(value)

    def set_setting(self, key, value):
        self.query_set.bindValue(":key", key)
        self.query_set.bindValue(":value", value)
        self.database.execute_query(self.query_set)

    def restore_state(self, widget):
        key = f"ui.{widget.objectName()}/state"
        if self.has_setting(key):
            widget.restoreState(
                self.get_setting(
                    key,
                    widget.saveState()
                )
            )

    def save_state(self, widget):
        key = f"ui.{widget.objectName()}/state"
        self.set_setting(key, widget.saveState())

    def restore_geometry(self, widget):
        key = f"ui.{widget.objectName()}/geometry"
        if self.has_setting(key):
            widget.restoreGeometry(
                self.get_setting(
                    key,
                    widget.saveGeometry()
                )
            )

    def save_geometry(self, widget):
        key = f"ui.{widget.objectName()}/geometry"
        self.set_setting(key, widget.saveGeometry())
