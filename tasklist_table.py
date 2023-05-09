from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt, QAbstractTableModel, QDate, QTime

from tasklist import Tasklist, Task, DeadlineType

class TasklistTableModel(QAbstractTableModel):
    def __init__(self, parent, tasklist, headers, *args):
        QAbstractTableModel.__init__(self, parent, *args)
        self._tasklist = tasklist
        self._data = []
        self._header = headers
        self.EDITABLE_COLUMNS = [0, 1, 2, 3, 5, 7]

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
        return len(self._tasklist.tasks)

    def columnCount(self, parent):
        return len(self._header)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            task = self._tasklist.tasks[index.row()]
            return self._get_task_property_by_column_index(task, index.column())
        return None

    def headerData(self, column, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._header[column]
        return None

    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            if not value:
                return False
            task = self._tasklist.tasks[index.row()]
            self._set_task_property_by_column_index(task, index.column(), value)
            self._tasklist.calculate()
            self.dataChanged.emit(index, index)
            return True

    def flags(self, index):
        if index.column() in self.EDITABLE_COLUMNS:
            return super().flags(index) | Qt.ItemIsEditable
        return super().flags(index)
