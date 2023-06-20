from enum import Enum, auto

class ReplaceOption(Enum):
    IGNORE = 0
    REPLACE = auto()
    ADD = auto()

class Importer:
    """Handles file imports and connects them to the proper table."""

    def __init__(self, table, path):
        self.table = table
        self.path = path
        self.replace_option = ReplaceOption.IGNORE

    def import_items(self):
        from model.plan import PlanTableModel
        from model.tasklist import TasklistTableModel

        if isinstance(self.table, PlanTableModel):
            self.table.import_activities(self.path, self.replace_option)
        elif isinstance(self.table, TasklistTableModel):
            self.table.import_tasks(self.path, self.replace_option)

    def set_replace_option(self, option):
        self.replace_option = ReplaceOption(option)
