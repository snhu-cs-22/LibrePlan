import json
from enum import Enum, auto

from PyQt5.QtCore import (
    Qt,
    QAbstractTableModel,
    QSortFilterProxyModel,
    QModelIndex,
    QDate,
    QDateTime
)

from model.database import Database
from model.importing import ReplaceOption
from ui.item_delegates import GenericDelegate, DeadlineTypeDelegate, PercentDelegate

import model.tasklist.queries as queries

class DeadlineType(Enum):
    NONE = 0
    STANDARD = auto()
    DECLINE = auto()
    POSTDATE = auto()
    POSTDECLINE = auto()

    def __lt__(self, other):
        return self.value < other.value

class Task:
    COLUMNS = [
        {
            "attr": "get_priority",
            "label": "Priority",
            "user_editable": False,
            "delegate": PercentDelegate,
        },
        {
            "attr": "value",
            "label": "Value",
            "user_editable": True,
            "delegate": GenericDelegate,
        },
        {
            "attr": "cost",
            "label": "Cost",
            "user_editable": True,
            "delegate": GenericDelegate,
        },
        {
            "attr": "name",
            "label": "Name",
            "user_editable": True,
            "delegate": GenericDelegate,
        },
        {
            "attr": "DATE_CREATED",
            "label": "Date Added",
            "user_editable": True,
            "delegate": GenericDelegate,
        },
        {
            "attr": "deadline",
            "label": "Deadline",
            "user_editable": True,
            "delegate": GenericDelegate,
        },
        {
            "attr": "get_halftime",
            "label": "Halftime",
            "user_editable": False,
            "delegate": GenericDelegate,
        },
        {
            "attr": "deadline_type",
            "label": "Deadline Type",
            "user_editable": True,
            "delegate": DeadlineTypeDelegate,
        },
    ]

    COLUMN_INDICES = dict([(col["attr"], i) for i, col in enumerate(COLUMNS)])

    def __init__(self,
        id=None,
        name="Task",
        value=0,
        cost=1,
        date_created=QDate.currentDate(),
        deadline=QDate(),
        deadline_type=DeadlineType.NONE,
    ):
        self.id = id
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

        self.query_count = Database.get_prepared_query(queries.count)
        self.query_create = Database.get_prepared_query(queries.insert_task)
        self.query_read = Database.get_prepared_query(queries.get_tasks)
        self.query_update = Database.get_prepared_query(queries.update_task)
        self.query_delete = Database.get_prepared_query(queries.delete_task)
        self.query_clear = Database.get_prepared_query(queries.delete_all_tasks)

        self._read_tasks()

    def get_task(self, index):
        return self._tasks[index]

    def add_task(self, task=None):
        if task is None:
            task = Task()
        self.add_tasks([task])

    def add_tasks(self, tasks):
        max_id = QDateTime.currentDateTime().toMSecsSinceEpoch()

        for i, task in enumerate(tasks):
            task.id = max_id + i

        self.query_create.bindValue(":id", [t.id for t in tasks])
        self.query_create.bindValue(":name", [t.name for t in tasks])
        self.query_create.bindValue(":value", [t.value for t in tasks])
        self.query_create.bindValue(":cost", [t.cost for t in tasks])
        self.query_create.bindValue(":date_created", [t.DATE_CREATED for t in tasks])
        self.query_create.bindValue(":deadline", [t.deadline for t in tasks])
        self.query_create.bindValue(":deadline_type", [t.deadline_type.value for t in tasks])
        if Database.execute_batch_query(self.query_create):
            self.layoutAboutToBeChanged.emit()
            self._tasks.extend(tasks)
            self.layoutChanged.emit()

    def delete_tasks(self, indices):
        ids = [t.id for i, t in enumerate(self._tasks) if i in indices]
        self.query_delete.bindValue(":id", ids)
        Database.execute_batch_query(self.query_delete)

        self.layoutAboutToBeChanged.emit()
        self._tasks = [t for i, t in enumerate(self._tasks) if i not in indices]
        self.layoutChanged.emit()

    def clear(self):
        Database.execute_query(self.query_clear)
        self.layoutAboutToBeChanged.emit()
        self._tasks = []
        self.layoutChanged.emit()

    def _read_tasks(self):
        self._tasks = []
        Database.execute_query(self.query_read)
        while self.query_read.next():
            task = self._get_task_from_db()
            self._tasks.append(task)

    def import_tasks(self, path, replace_option):
        if replace_option == ReplaceOption.REPLACE:
            query_import = Database.get_prepared_query(queries.import_task_replace)
        elif replace_option == ReplaceOption.ADD:
            query_import = Database.get_prepared_query(queries.import_task_add)
        else:
            query_import = Database.get_prepared_query(queries.import_task_ignore)

        with open(path) as f:
            tasks_json = json.load(f)

            query_import.bindValue(":id", [t["id"] for t in tasks_json])
            query_import.bindValue(":name", [t["name"] for t in tasks_json])
            query_import.bindValue(":value", [t["value"] for t in tasks_json])
            query_import.bindValue(":cost", [t["cost"] for t in tasks_json])
            query_import.bindValue(":date_created", [t["DATE_CREATED"] for t in tasks_json])
            query_import.bindValue(":deadline", [t["deadline"] for t in tasks_json])
            query_import.bindValue(":deadline_type", [DeadlineType[t["deadline_type"]].value for t in tasks_json])

        Database.execute_batch_query(query_import)

        self.layoutAboutToBeChanged.emit()
        self._read_tasks()
        self.layoutChanged.emit()

    def export_tasks(self, path, indices=[]):
        with open(path, "w") as f:
            if indices:
                tasks = [self._tasks[index] for index in indices]
            else:
                tasks = self._tasks

            tasks_properties = []
            for task in tasks:
                properties = {
                    "id": task.id,
                    "name": task.name,
                    "value": task.value,
                    "cost": task.cost,
                    "DATE_CREATED": task.DATE_CREATED.toString(Database.DATE_FORMAT),
                    "deadline_type": task.deadline_type.name,
                    "deadline": task.deadline.toString(Database.DATE_FORMAT),
                }

                tasks_properties.append(properties)

            tasks_json = json.dumps(tasks_properties)
            f.write(tasks_json)

    # Private methods
    ################################################################################

    def _get_task_from_db(self):
        return Task(
            id=self.query_read.value("id"),
            name=self.query_read.value("name"),
            value=self.query_read.value("value"),
            cost=self.query_read.value("cost"),
            date_created=QDate.fromString(
                self.query_read.value("date_created"),
                Database.DATE_FORMAT
            ),
            deadline=QDate.fromString(
                self.query_read.value("deadline"),
                Database.DATE_FORMAT
            ),
            deadline_type=DeadlineType(self.query_read.value("deadline_type"))
        )

    # Qt API Implementation
    ################################################################################

    def rowCount(self, parent=QModelIndex):
        Database.execute_query(self.query_count)
        self.query_count.first()
        return self.query_count.value("count")

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

            self.query_update.bindValue(":id", task.id)
            self.query_update.bindValue(":name", task.name)
            self.query_update.bindValue(":value", task.value)
            self.query_update.bindValue(":cost", task.cost)
            self.query_update.bindValue(":date_created", task.DATE_CREATED)
            self.query_update.bindValue(":deadline", task.deadline)
            self.query_update.bindValue(":deadline_type", task.deadline_type.value)
            Database.execute_query(self.query_update)

            self.dataChanged.emit(index, index)
            return True

    def flags(self, index):
        editable_columns = [i for i, col in enumerate(Task.COLUMNS) if col["user_editable"]]
        if index.column() in editable_columns:
            return super().flags(index) | Qt.ItemIsEditable
        return super().flags(index)

class TasklistProxyModel(QSortFilterProxyModel):
    """Special proxy model class for use with TasklistTableModel

    This proxy model implements lessThan() for data types not covered
    by the base implementation of QSortFilterProxyModel.

    Classes must have the '<' operator implemented in order to be
    properly sorted by the model.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFilterKeyColumn(Task.COLUMN_INDICES["name"])

    def lessThan(self, source_left, source_right):
        return source_left.data() < source_right.data()
