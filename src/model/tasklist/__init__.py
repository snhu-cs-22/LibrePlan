import json
from enum import Enum, auto

from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QDate

class DeadlineType(Enum):
    NONE = auto()
    STANDARD = auto()
    DECLINE = auto()
    POSTDATE = auto()
    POSTDECLINE = auto()

class Task:
    COLUMNS = [
        {
            "attr": "get_priority",
            "label": "Priority",
            "user_editable": False,
        },
        {
            "attr": "value",
            "label": "Value",
            "user_editable": True,
        },
        {
            "attr": "cost",
            "label": "Cost",
            "user_editable": True,
        },
        {
            "attr": "name",
            "label": "Name",
            "user_editable": True,
        },
        {
            "attr": "DATE_CREATED",
            "label": "Date Added",
            "user_editable": True,
        },
        {
            "attr": "deadline",
            "label": "Deadline",
            "user_editable": True,
        },
        {
            "attr": "get_halftime",
            "label": "Halftime",
            "user_editable": False,
        },
        {
            "attr": "deadline_type",
            "label": "Deadline Type",
            "user_editable": True,
        },
    ]

    COLUMN_INDICES = dict([(col["attr"], i) for i, col in enumerate(COLUMNS)])

    def __init__(self,
        name="Task",
        value=0,
        cost=1,
        date_created=QDate.currentDate(),
        deadline=QDate(),
        deadline_type=DeadlineType.NONE,
    ):
        self.name = name
        self.value = value
        self.cost = cost

        self.deadline_type = deadline_type
        self.DATE_CREATED = date_created
        self.deadline = deadline

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

    def get_priority(self, today=QDate.currentDate()):
        if self.cost == 0:
            return 0.0
        return self.value / self.cost * self._select_deadline_function(today)

    def get_halftime(self):
        if self.deadline.isValid():
            return self.DATE_CREATED.addDays(self.DATE_CREATED.daysTo(self.deadline) // 2)
        return QDate()

    def get_attr_by_index(self, index):
        try:
            return getattr(self, Task.COLUMNS[index]["attr"])()
        except:
            return getattr(self, Task.COLUMNS[index]["attr"])

    def set_attr_by_index(self, index, value):
        setattr(self, Task.COLUMNS[index]["attr"], value)

class TasklistTableModel(QAbstractTableModel):
    def __init__(self, parent, *args):
        QAbstractTableModel.__init__(self, parent, *args)
        self._tasks = []
        self._DATE_FORMAT = "yyyy-MM-dd"

    def get_task(self, index):
        return self._tasks[index]

    def set_task(self, index, property):
        self._set_task_property_by_column_index(index, property)

    def add_task(self, task):
        self._tasks.append(task)
        self.insertRow(self.rowCount())
        self.layoutChanged.emit()

    def delete_tasks(self, indices):
        # List is reversed to preserve index numbers
        for index in reversed(indices):
            self._tasks.pop(index)
            model_index = self.createIndex(index, 0)
            self.removeRow(index, model_index)
            self.layoutChanged.emit()

    def clear(self):
        self._tasks = []

    def calculate(self):
        if self._tasks:
            self._tasks.sort(key = lambda task: task.get_priority(), reverse = True)

    def import_tasks(self, path):
        with open(path) as f:
            tasks_json = json.load(f)

            for task_json in tasks_json:
                task = Task(
                    name=task_json["name"],
                    value=task_json["value"],
                    cost=task_json["cost"],
                    date_created=QDate.fromString(task_json["DATE_CREATED"], self._DATE_FORMAT),
                    deadline=QDate.fromString(task_json["deadline"], self._DATE_FORMAT),
                    deadline_type=DeadlineType[task_json["deadline_type"]]
                )

                self.add_task(task)

    def export_tasks(self, path, indices=[]):
        with open(path, "w") as f:
            if indices:
                tasks = [self._tasks[index] for index in indices]
            else:
                tasks = self._tasks

            tasks_properties = []
            for task in tasks:
                properties = {
                    "name": task.name,
                    "value": task.value,
                    "cost": task.cost,
                    "DATE_CREATED": task.DATE_CREATED.toString(self._DATE_FORMAT),
                    "deadline_type": task.deadline_type.name,
                    "deadline": task.deadline.toString(self._DATE_FORMAT),
                }

                tasks_properties.append(properties)

            tasks_json = json.dumps(tasks_properties)
            f.write(tasks_json)

    def debug_print_tasks(self):
        for task in self._tasks:
            print(f"Name: {task.name}: ")
            print(f"    Priority: {'{:.2f}'.format(task.get_priority())}")
            print(f"    Value: {task.value}")
            print(f"    Cost: {task.cost}")
            print(f"    Date Added: {task.DATE_CREATED.toString(self._DATE_FORMAT)}")
            print(f"    Deadline: {task.deadline.toString(self._DATE_FORMAT)}")
            print(f"    Halftime: {task.get_halftime().toString(self._DATE_FORMAT)}")
            print(f"    Deadline Type: {task.deadline_type}")

    # Qt API Implementation
    ################################################################################

    def rowCount(self, parent=QModelIndex):
        return len(self._tasks)

    def columnCount(self, parent=QModelIndex):
        return len(Task.COLUMNS)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            task = self._tasks[index.row()]
            return task.get_attr_by_index(index.column())
        return None

    def headerData(self, index, orientation=Qt.Horizontal, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return Task.COLUMNS[index]["label"]
        return None

    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            if not index.isValid():
                return False
            task = self._tasks[index.row()]
            task.set_attr_by_index(index.column(), value)
            self.calculate()
            self.dataChanged.emit(index, index)
            return True

    def flags(self, index):
        editable_columns = [i for i, col in enumerate(Task.COLUMNS) if col["user_editable"]]
        if index.column() in editable_columns:
            return super().flags(index) | Qt.ItemIsEditable
        return super().flags(index)
