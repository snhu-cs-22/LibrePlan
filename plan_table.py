from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt, QAbstractTableModel, QDate, QTime

from plan import Plan, Activity

class PlanTableModel(QAbstractTableModel):
    def __init__(self, parent, plan, headers, *args):
        QAbstractTableModel.__init__(self, parent, *args)
        self._plan = plan
        self._header = headers
        self.EDITABLE_COLUMNS = [0, 1, 2, 3, 4]

    def _get_activity_property_by_column_index(self, activity, index):
        if index == 0:
            return activity.is_fixed
        elif index == 1:
            return activity.is_rigid
        elif index == 2:
            return activity.start_time
        elif index == 3:
            return activity.name
        elif index == 4:
            return activity.length
        elif index == 5:
            return activity.actual_length
        elif index == 6:
            return activity.optimal_length
        elif index == 7:
            return activity.get_percent()

    def _set_activity_property_by_column_index(self, activity, index, value):
        if index == 0:
            activity.is_fixed = value
        elif index == 1:
            activity.is_rigid = value
        elif index == 2:
            activity.start_time = value
        elif index == 3:
            activity.name = value
        elif index == 4:
            activity.length = value

    # Qt API Implementation
    ################################################################################

    def rowCount(self, parent):
        return len(self._plan.activities)

    def columnCount(self, parent):
        return len(self._header)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            activity = self._plan.activities[index.row()]
            return self._get_activity_property_by_column_index(activity, index.column())
        return None

    def headerData(self, column, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._header[column]
        return None

    def setData(self, index, value, role=Qt.EditRole):
        if role in (Qt.DisplayRole, Qt.EditRole):
            if not index.isValid():
                return False
            activity = self._plan.activities[index.row()]
            self._set_activity_property_by_column_index(activity, index.column(), value)
            self._plan.calculate()
            self.dataChanged.emit(index, index)
            return True

    def flags(self, index):
        if index.column() in self.EDITABLE_COLUMNS:
            return super().flags(index) | Qt.ItemIsEditable
        return super().flags(index)
