import json
from enum import Enum, auto

from PyQt5.QtCore import Qt, QAbstractTableModel, QDate

class DeadlineType(Enum):
    NONE = auto()
    STANDARD = auto()
    DECLINE = auto()
    POSTDATE = auto()
    POSTDECLINE = auto()

class Task:
    def __init__(self,
        name="Task",
        value=0,
        cost=1,
        deadline=QDate(),
        deadline_type=DeadlineType.NONE,
    ):
        self.name = name
        self.value = value
        self.cost = cost

        self.deadline_type = deadline_type
        self.DATE_CREATED = QDate.currentDate()
        self.set_deadline(deadline)

    def set_deadline(self, deadline):
        if deadline:
            self.deadline = deadline
            self.halftime = self.DATE_CREATED.addDays(self.DATE_CREATED.daysTo(self.deadline) // 2)

            if self.deadline_type == DeadlineType.NONE:
                self.deadline_type = DeadlineType.STANDARD
        else:
            self.deadline = QDate()
            self.halftime = QDate()

    def _select_deadline_function(self, today):
        functions = {
            DeadlineType.STANDARD: self._deadline_standard,
            DeadlineType.DECLINE: self._deadline_decline,
            DeadlineType.POSTDATE: self._deadline_postdate,
            DeadlineType.POSTDECLINE: self._deadline_postdecline,
        }

        try:
            return functions[self.deadline_type](today, self.deadline, self.DATE_CREATED)
        except:
            return 1.0

    @staticmethod
    def _deadline_standard(today, deadline, date_created):
        try:
            return min(date_created.daysTo(today) / date_created.daysTo(deadline), 1.0)
        except (ZeroDivisionError):
            return 1.0

    @staticmethod
    def _deadline_decline(today, deadline, date_created):
        try:
            return max(1.0 - date_created.daysTo(today) / date_created.daysTo(deadline), 0.0)
        except (ZeroDivisionError):
            return 0.0

    @staticmethod
    def _deadline_postdate(today, deadline, date_created):
        if today >= deadline:
            return 1.0
        return 0.0

    @staticmethod
    def _deadline_postdecline(today, deadline, date_created):
        if today > deadline:
            to_deadline = date_created.daysTo(deadline)
            return Task._deadline_decline(today.addDays(-to_deadline), deadline, date_created)
        return 1.0

    def calculate_priority(self, today):
        self.priority = self.value / self.cost * self._select_deadline_function(today)

class TasklistTableModel(QAbstractTableModel):
    def __init__(self, parent, *args):
        QAbstractTableModel.__init__(self, parent, *args)
        self._tasks = []
        self._header = ["Priority", "Value", "Cost", "Name", "Date Added", "Deadline", "Halftime", "Deadline Type"]
        self._EDITABLE_COLUMNS = [0, 1, 2, 3, 5, 7]
        self._DATE_FORMAT = "yyyy-MM-dd"

    def get_task(self, index):
        return self._tasks[index]

    def set_task(self, index, property):
        self._set_task_property_by_column_index(index, property)

    def add_task(self, task=Task()):
        today = QDate.currentDate()
        task.calculate_priority(today)
        self._tasks.append(task)

    def delete_task(self, index=0):
        self._tasks.pop(index)

    def clear(self):
        self._tasks = []

    def calculate(self):
        today = QDate.currentDate()
        if self._tasks:
            for task in self._tasks:
                task.calculate_priority(today)
            self._tasks.sort(key = lambda task: task.priority, reverse = True)

    def import_tasks(self, path, replace=False):
        with open(path) as f:
            if replace:
                self._tasks = []

            tasks_json = json.load(f)

            for task_json in tasks_json:
                task = Task()
                task.name = task_json["name"]
                task.value = task_json["value"]
                task.cost = task_json["cost"]
                task.DATE_CREATED = QDate.fromString(task_json["DATE_CREATED"], self._DATE_FORMAT)
                try:
                    task.set_deadline(QDate.fromString(task_json["deadline"], self._DATE_FORMAT))
                    task.deadline_type = DeadlineType[task_json["deadline_type"]]
                except:
                    task.deadline_type = DeadlineType.NONE

                self._tasks.append(task)

        self.calculate()

    def export_tasks(self, path):
        with open(path, "w") as f:
            tasks_properties = []
            for task in self._tasks:
                properties = {}

                properties["name"] = task.name
                properties["value"] = task.value
                properties["cost"] = task.cost
                properties["DATE_CREATED"] = task.DATE_CREATED.toString(self._DATE_FORMAT)
                properties["deadline_type"] = task.deadline_type.name
                properties["deadline"] = task.deadline.toString(self._DATE_FORMAT)

                tasks_properties.append(properties)

            tasks_json = json.dumps(tasks_properties)
            f.write(tasks_json)

    def debug_print_tasks(self):
        for task in self._tasks:
            print(f"Name: {task.name}: ")
            print(f"    Priority: {'{:.2f}'.format(task.priority)}")
            print(f"    Value: {task.value}")
            print(f"    Cost: {task.cost}")
            print(f"    Date Added: {task.DATE_CREATED.toString(self._DATE_FORMAT)}")
            print(f"    Deadline: {task.deadline.toString(self._DATE_FORMAT)}")
            print(f"    Halftime: {task.halftime.toString(self._DATE_FORMAT)}")
            print(f"    Deadline Type: {task.deadline_type}")

    def _get_task_property_by_column_index(self, task, index):
        if index == 0:
            return task.priority
        elif index == 1:
            return task.value
        elif index == 2:
            return task.cost
        elif index == 3:
            return task.name
        elif index == 4:
            return task.DATE_CREATED
        elif index == 5:
            return task.deadline
        elif index == 6:
            return task.halftime
        elif index == 7:
            return task.deadline_type

    def _set_task_property_by_column_index(self, task, index, value):
        if index == 0:
            task.priority = value
        elif index == 1:
            task.value = value
        elif index == 2:
            task.cost = value
        elif index == 3:
            task.name = value
        elif index == 5:
            task.deadline = value
        elif index == 7:
            task.deadline_type = value

    # Qt API Implementation
    ################################################################################

    def rowCount(self, parent):
        return len(self._tasks)

    def columnCount(self, parent):
        return len(self._header)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            task = self._tasks[index.row()]
            return self._get_task_property_by_column_index(task, index.column())
        return None

    def headerData(self, column, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._header[column]
        return None

    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            if not index.isValid():
                return False
            task = self._tasks[index.row()]
            self._set_task_property_by_column_index(task, index.column(), value)
            self.calculate()
            self.dataChanged.emit(index, index)
            return True

    def flags(self, index):
        if index.column() in self._EDITABLE_COLUMNS:
            return super().flags(index) | Qt.ItemIsEditable
        return super().flags(index)
