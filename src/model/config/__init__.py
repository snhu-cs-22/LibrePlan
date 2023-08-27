from model.storage import Database

from model.config import queries

class Config:
    """Interface for application settings"""

    def __init__(self, database):
        self.database = database
        self.query_get = self.database.get_prepared_query(queries.get_setting)
        self.query_set = self.database.get_prepared_query(queries.insert_setting)

    def get_setting(self, key, default_value):
        self.query_get.bindValue(":key", key)
        self.database.execute_query(self.query_get)
        self.query_get.first()
        value = self.query_get.value("value")

        if not value:
            self.set_setting(key, default_value)
            return default_value

        # Cast value to type of default value
        return type(default_value)(value)

    def set_setting(self, key, value):
        self.query_set.bindValue(":key", key)
        self.query_set.bindValue(":value", value)
        self.database.execute_query(self.query_set)

    def get_state(self, widget):
        key = f"ui.{widget.objectName()}/state"
        return self.get_setting(
            key,
            widget.saveState()
        )

    def set_state(self, widget):
        key = f"ui.{widget.objectName()}/state"
        self.set_setting(key, widget.saveState())

    def get_geometry(self, widget):
        key = f"ui.{widget.objectName()}/geometry"
        return self.get_setting(
            key,
            widget.saveGeometry()
        )

    def set_geometry(self, widget):
        key = f"ui.{widget.objectName()}/geometry"
        self.set_setting(key, widget.saveGeometry())
