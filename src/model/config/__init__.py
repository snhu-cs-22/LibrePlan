from model.database import Database

from model.config import queries

class Config:
    """Interface for application settings"""

    query_get = Database.get_prepared_query(queries.get_setting)
    query_set = Database.get_prepared_query(queries.insert_setting)

    @classmethod
    def get_setting(cls, key, default_value):
        cls.query_get.bindValue(":key", key)
        Database.execute_query(cls.query_get)
        cls.query_get.first()
        value = cls.query_get.value("value")

        if not value:
            cls.set_setting(key, default_value)
            return default_value

        # Cast value to type of default value
        return type(default_value)(value)

    @classmethod
    def set_setting(cls, key, value):
        cls.query_set.bindValue(":key", key)
        cls.query_set.bindValue(":value", value)
        Database.execute_query(cls.query_set)

    @classmethod
    def get_state(cls, widget):
        key = f"ui.{widget.objectName()}/state"
        return cls.get_setting(
            key,
            widget.saveState()
        )

    @classmethod
    def set_state(cls, widget):
        key = f"ui.{widget.objectName()}/state"
        cls.set_setting(key, widget.saveState())

    @classmethod
    def get_geometry(cls, widget):
        key = f"ui.{widget.objectName()}/geometry"
        return cls.get_setting(
            key,
            widget.saveGeometry()
        )

    @classmethod
    def set_geometry(cls, widget):
        key = f"ui.{widget.objectName()}/geometry"
        cls.set_setting(key, widget.saveGeometry())
