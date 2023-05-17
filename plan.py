import json
from math import floor

from PyQt5.QtCore import Qt, QAbstractTableModel, QTime

class Activity:
    def __init__(self,
        name="Activity name",
        length=0,
        start_time=QTime(),
        is_rigid=False,
        is_fixed=False,
    ):
        self.name = name
        self.length = length
        self.start_time = start_time
        self.is_rigid = is_rigid
        self.is_fixed = is_fixed

        self.actual_length = 0
        self.optimal_length = 0

    def get_percent(self):
        if self.length != 0:
                return self.actual_length / self.length
        else:
                return 0

class PlanTableModel(QAbstractTableModel):
    def __init__(self, parent, *args):
        QAbstractTableModel.__init__(self, parent, *args)
        self._activities = []
        self._header = ["F", "R", "Start", "Name", "Length", "ActLen", "OptLen", "Percent"]
        self._EDITABLE_COLUMNS = [0, 1, 2, 3, 4]
        self._TIME_FORMAT = "hh:mm"

    def get_activity(self, index):
        return self._activities[index]

    def set_activity(self, index, property):
        self._set_activity_property_by_column_index(index, property)

    def insert_activity(self, index, activity=Activity()):
        self._activities.insert(index, activity)
        self.calculate()

    def delete_activity(self, index):
        self._activities.pop(index)
        self.calculate()

    def move_activity(self, index, new_index):
        self._activities.insert(new_index, self._activities[index])
        self._activities.delete(index + 1)
        self.calculate()

    def clear(self):
        self._activities = []

    def calculate(self):
        if self._activities:
            self._set_actual_lengths()
            self._set_optimal_lengths()
            self._calculate_non_fixed_times()

    def _calculate_optimum_factor(self, block_start, block_end):
        """Takes the total time duration in block, excluding time taken up by rigid _activities since they can't be compressed or expanded, and divides it by the actual allowed block size"""

        block_size = self._activities[block_start].start_time.secsTo(self._activities[block_end].start_time) / 60
        block_lengths = 0

        for activity in self._activities[block_start:block_end]:
            if activity.is_rigid:
                block_size = block_size - activity.length
            else:
                block_lengths = block_lengths + activity.length

        if block_lengths != 0:
            factor = block_size / block_lengths
        else:
            factor = 1

        return factor

    def _set_optimal_lengths(self):
        factor = self._calculate_optimum_factor(0, -1)
        for activity in self._activities:
            if activity.is_rigid:
                activity.optimal_length = activity.length
            else:
                activity.optimal_length = floor(activity.length * factor)

    def _set_actual_lengths(self):
        # Keep track of all fixed points in Plan
        self.fixed_points = []
        for i, activity in enumerate(self._activities):
            if activity.is_fixed:
                self.fixed_points.append(i)

        # Use fixed points to define blocks to calculate local OptLens
        for i in range(0, len(self.fixed_points) - 1):
            block_start = self.fixed_points[i]
            block_end = self.fixed_points[i + 1]

            factor = self._calculate_optimum_factor(block_start, block_end)
            for activity in self._activities[block_start:block_end]:
                if activity.is_rigid:
                    activity.actual_length = activity.length
                else:
                    activity.actual_length = floor(activity.length * factor)

    def _calculate_non_fixed_times(self):
        for i in range(1, len(self._activities) - 1):
            if not self._activities[i].is_fixed:
                self._activities[i].start_time = self._activities[i - 1].start_time.addSecs(self._activities[i - 1].actual_length * 60)

    def import_activities(self, path, replace=False):
        with open(path) as f:
            if replace:
                self._activities = []

            activities_json = json.load(f)

            for activity_json in activities_json:
                activity = Activity(
                    name=activity_json["name"],
                    length=activity_json["length"],
                    start_time=QTime.fromString(activity_json["start_time"], self._TIME_FORMAT),
                    is_fixed=activity_json["is_fixed"],
                    is_rigid=activity_json["is_rigid"]
                )

                self._activities.append(activity)

        self.calculate()

    def export_activities(self, path):
        with open(path, "w") as f:
            activities_properties = []
            for activity in self._activities:
                properties = {
                    "name": activity.name,
                    "length": activity.length,
                    "start_time": activity.start_time.toString(self._TIME_FORMAT),
                    "is_fixed": activity.is_fixed,
                    "is_rigid": activity.is_rigid,
                }
                activities_properties.append(properties)

            activities_json = json.dumps(activities_properties)
            f.write(activities_json)

    def debug_print_activities(self):
        for activity in self._activities:
            print(f"Name: {activity.name}")
            print(f"    Is Fixed?: {activity.is_fixed}")
            print(f"    Start Time: {activity.start_time.toString(self._TIME_FORMAT)}")
            print(f"    Is Rigid?: {activity.is_rigid}")
            print(f"    Length: {activity.length}")
            print(f"    ActLen: {activity.actual_length}")
            print(f"    OptLen: {activity.optimal_length}")
            print(f"    Percent: {activity.get_percent()}")

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
        return len(self._activities)

    def columnCount(self, parent):
        return len(self._header)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            activity = self._activities[index.row()]
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
            activity = self._activities[index.row()]
            self._set_activity_property_by_column_index(activity, index.column(), value)
            self.calculate()
            self.dataChanged.emit(index, index)
            return True

    def flags(self, index):
        if index.column() in self._EDITABLE_COLUMNS:
            return super().flags(index) | Qt.ItemIsEditable
        return super().flags(index)
