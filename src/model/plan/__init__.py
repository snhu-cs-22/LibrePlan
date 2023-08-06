import json
from math import floor

from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QTime, QDateTime

from model.database import Database
from model.importing import ReplaceOption
from ui.item_delegates import GenericDelegate, BoolDelegate, PercentDelegate

import model.plan.queries as queries

class Activity:
    COLUMNS = [
        {
            "attr": "is_fixed",
            "label": "F",
            "user_editable": True,
            "delegate": BoolDelegate,
        },
        {
            "attr": "is_rigid",
            "label": "R",
            "user_editable": True,
            "delegate": BoolDelegate,
        },
        {
            "attr": "start_time",
            "label": "Start",
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
            "attr": "length",
            "label": "Length",
            "user_editable": True,
            "delegate": GenericDelegate,
        },
        {
            "attr": "actual_length",
            "label": "ActLen",
            "user_editable": False,
            "delegate": GenericDelegate,
        },
        {
            "attr": "optimal_length",
            "label": "OptLen",
            "user_editable": False,
            "delegate": GenericDelegate,
        },
        {
            "attr": "get_percent",
            "label": "Percent",
            "user_editable": False,
            "delegate": PercentDelegate,
        },
    ]

    COLUMN_INDICES = dict([(col["attr"], i) for i, col in enumerate(COLUMNS)])

    def __init__(self,
        id=None,
        name="Activity",
        length=0,
        start_time=QTime(),
        is_rigid=False,
        is_fixed=False,
    ):
        self.id = id
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
            return 0.0

    def get_attr_by_index(self, index):
        try:
            return getattr(self, Activity.COLUMNS[index]["attr"])()
        except:
            return getattr(self, Activity.COLUMNS[index]["attr"])

    def set_attr_by_index(self, index, value):
        setattr(self, Activity.COLUMNS[index]["attr"], value)

class PlanTableModel(QAbstractTableModel):
    def __init__(self, parent, *args):
        QAbstractTableModel.__init__(self, parent, *args)
        self._activities = []
        self._fixed_indices = []
        self._current_activity_index = 0

        self.query_count = Database.get_prepared_query(queries.count)
        self.query_insert = Database.get_prepared_query(queries.insert_activity)
        self.query_increment = Database.get_prepared_query(queries.reorder_after_insertion)
        self.query_decrement = Database.get_prepared_query(queries.reorder_after_deletion)
        self.query_read = Database.get_prepared_query(queries.get_activities)
        self.query_update = Database.get_prepared_query(queries.update_activity)
        self.query_delete = Database.get_prepared_query(queries.delete_activity)
        self.query_clear = Database.get_prepared_query(queries.delete_all_activities)
        self.query_archive_names = Database.get_prepared_query(queries.insert_into_activities)
        self.query_insert_into_log = Database.get_prepared_query(queries.insert_into_log)

        self._read_activities()

    # CRUD operations
    ################################################################################

    def get_activity(self, index):
        return self._activities[index]

    def get_current_activity(self):
        return self._activities[self._current_activity_index]

    def get_following_activity(self):
        return self._activities[self._current_activity_index + 1]

    def insert_activity(self, index, activity):
        self.insert_activities(index, [activity])

    def insert_activities(self, index, activities):
        if index >= self._current_activity_index:
            self.query_increment.bindValue(":insertion_index", index)
            self.query_increment.bindValue(":offset", len(activities))
            Database.execute_query(self.query_increment)

            max_id = QDateTime.currentDateTime().toMSecsSinceEpoch()

            for i, activity in enumerate(activities):
                activity.id = max_id + i

            self.query_insert.bindValue(":id", [a.id for a in activities])
            self.query_insert.bindValue(":order", [index + i for i in range(len(activities))])
            self.query_insert.bindValue(":start_time", [QTime.toString(a.start_time, Database.TIME_FORMAT) for a in activities])
            self.query_insert.bindValue(":name", [a.name for a in activities])
            self.query_insert.bindValue(":length", [a.length for a in activities])
            self.query_insert.bindValue(":is_fixed", [a.is_fixed for a in activities])
            self.query_insert.bindValue(":is_rigid", [a.is_rigid for a in activities])
            if Database.execute_batch_query(self.query_insert):
                self._activities[index:index] = activities
                self.calculate()
                self.layoutChanged.emit()

    def insert_interruption(self, interruption_name):
        current_activity = self.get_current_activity()
        following_activity = self.get_following_activity()
        interruption = Activity(name=interruption_name, is_rigid=True)

        now = self._get_current_time_rounded()
        split_activity = Activity()
        split_activity.name = current_activity.name
        split_activity.length = now.secsTo(following_activity.start_time) // 60

        insertion_index = self._current_activity_index + 1
        self.insert_activities(insertion_index, [interruption, split_activity])

    def delete_activities(self, indices):
        valid_indices = [i for i in indices if i >= self._current_activity_index]

        ids = [a.id for i, a in enumerate(self._activities) if i in valid_indices]
        self.query_delete.bindValue(":id", ids)
        Database.execute_batch_query(self.query_delete)

        self.query_decrement.bindValue(":deletion_index", list(reversed(valid_indices)))
        Database.execute_batch_query(self.query_decrement)

        self._activities = [a for i, a in enumerate(self._activities) if i not in valid_indices]

        self.calculate()
        self.layoutChanged.emit()

    def clear(self):
        self._activities = []
        Database.execute_query(self.query_clear)
        self.layoutChanged.emit()

    def move_activity(self, index, new_index):
        self._activities.insert(new_index, self._activities[index])
        self._activities.delete(index + 1)
        self.calculate()

    def import_activities(self, path, replace_option):
        if replace_option == ReplaceOption.REPLACE:
            query_import = Database.get_prepared_query(queries.import_activity_replace)
        elif replace_option == ReplaceOption.ADD:
            query_import = Database.get_prepared_query(queries.import_activity_add)
        else:
            query_import = Database.get_prepared_query(queries.import_activity_ignore)

        with open(path) as f:
            activities_json = json.load(f)

            query_import.bindValue(":id", [a["id"] for a in activities_json])
            query_import.bindValue(":order", list(range(len(activities_json))))
            query_import.bindValue(":name", [a["name"] for a in activities_json])
            query_import.bindValue(":length", [a["length"] for a in activities_json])
            query_import.bindValue(":start_time", [a["start_time"] for a in activities_json])
            query_import.bindValue(":is_fixed", [a["is_fixed"] for a in activities_json])
            query_import.bindValue(":is_rigid", [a["is_rigid"] for a in activities_json])

        Database.execute_batch_query(query_import)

        self._read_activities()
        self.layoutChanged.emit()

    def export_activities(self, path, indices=[]):
        with open(path, "w") as f:
            if indices:
                activities = [self._activities[index] for index in indices]
            else:
                activities = self._activities

            activities_properties = []
            for activity in activities:
                properties = {
                    "id": activity.id,
                    "name": activity.name,
                    "length": activity.length,
                    "start_time": activity.start_time.toString(Database.TIME_FORMAT),
                    "is_fixed": activity.is_fixed,
                    "is_rigid": activity.is_rigid,
                }
                activities_properties.append(properties)

            activities_json = json.dumps(activities_properties)
            f.write(activities_json)

    def archive(self):
        Database.execute_query(self.query_archive_names)

        self.query_insert_into_log.bindValue(":start_time", [a.start_time.toString(Database.TIME_FORMAT) for a in self._activities])
        self.query_insert_into_log.bindValue(":name", [a.name for a in self._activities])
        self.query_insert_into_log.bindValue(":length", [a.length for a in self._activities])
        self.query_insert_into_log.bindValue(":actual_length", [a.actual_length for a in self._activities])
        self.query_insert_into_log.bindValue(":optimal_length", [a.optimal_length for a in self._activities])
        self.query_insert_into_log.bindValue(":is_fixed", [int(a.is_fixed) for a in self._activities])
        self.query_insert_into_log.bindValue(":is_rigid", [int(a.is_rigid) for a in self._activities])
        Database.execute_batch_query(self.query_insert_into_log)

    # Functionality Helper Methods
    ################################################################################

    def set_current_activity_index(self, index):
        # The final activity marks the end of the plan, so we stop one before the end
        final_activity_index = self.rowCount() - 1
        if index <= final_activity_index:
            self._current_activity_index = index

    def set_current_activity_start_time(self):
        self.setData(
            self.createIndex(
                self._current_activity_index,
                Activity.COLUMN_INDICES["start_time"]
            ),
            self._get_current_time_rounded()
        )
        self.layoutChanged.emit()

    def complete_activity(self, preemptive=False):
        current_activity = self.get_current_activity()
        now = self._get_current_time_rounded()
        length = current_activity.start_time.secsTo(now) // 60

        self._increment_current_activity_index()

        if not preemptive:
            self.setData(
                self.createIndex(
                    self._current_activity_index - 1,
                    Activity.COLUMN_INDICES["actual_length"]
                ),
                length
            )

        self.layoutChanged.emit()

    def complete(self):
        self.set_current_activity_index(0)

    def is_completed(self):
        final_activity_index = self.rowCount() - 1
        return self._current_activity_index >= final_activity_index

    def calculate(self):
        if self._activities:
            self._set_actual_lengths()
            self._set_optimal_lengths()
            self._calculate_non_fixed_times()

    # Private methods
    ################################################################################

    def _calculate_optimum_factor(self, block_start, block_end):
        """Calculates the amount to compress or expand a block of
        activities to make it fit into the time allocated"""

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
        self._fixed_indices = [i for i, activity in enumerate(self._activities) if activity.is_fixed]

        # Use fixed points after current activity to define blocks to calculate local OptLens
        for i in range(self._current_activity_index, len(self._fixed_indices) - 1):
            block_start = self._fixed_indices[i]
            block_end = self._fixed_indices[i + 1]

            factor = self._calculate_optimum_factor(block_start, block_end)
            for activity in self._activities[block_start:block_end]:
                if activity.is_rigid:
                    activity.actual_length = activity.length
                else:
                    activity.actual_length = floor(activity.length * factor)

    def _calculate_non_fixed_times(self):
        for i in range(self._current_activity_index + 1, len(self._activities) - 1):
            if not self._activities[i].is_fixed:
                self._activities[i].start_time = self._activities[i - 1].start_time.addSecs(self._activities[i - 1].actual_length * 60)

    def _read_activities(self):
        self._activities = []
        Database.execute_query(self.query_read)
        while self.query_read.next():
            activity = self._get_activity_from_db()
            self._activities.append(activity)
        self.calculate()

    def _get_activity_from_db(self):
        return Activity(
            id=self.query_read.value("id"),
            name=self.query_read.value("name"),
            length=self.query_read.value("length"),
            start_time=QTime.fromString(self.query_read.value("start_time"), Database.TIME_FORMAT),
            is_fixed=bool(self.query_read.value("is_fixed")),
            is_rigid=bool(self.query_read.value("is_rigid")),
        )

    def _get_current_time_rounded(self):
        # TODO: Round down seconds for simplicity
        now = QTime.currentTime()
        now.setHMS(now.hour(), now.minute(), 0)
        return now

    def _increment_current_activity_index(self):
        self.set_current_activity_index(
            self._current_activity_index + 1
        )

    # Qt API Implementation
    ################################################################################

    def rowCount(self, parent=QModelIndex):
        Database.execute_query(self.query_count)
        self.query_count.first()
        return self.query_count.value("count")

    def columnCount(self, parent=QModelIndex):
        return len(Activity.COLUMNS)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            activity = self._activities[index.row()]
            return activity.get_attr_by_index(index.column())
        return None

    def headerData(self, index, orientation=Qt.Horizontal, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return Activity.COLUMNS[index]["label"]
        return None

    def setData(self, index, value, role=Qt.EditRole):
        if role in (Qt.DisplayRole, Qt.EditRole):
            if not index.isValid():
                return False
            activity = self._activities[index.row()]
            activity.set_attr_by_index(index.column(), value)

            self.query_update.bindValue(":id", activity.id)
            self.query_update.bindValue(":order", index.row())
            self.query_update.bindValue(":start_time", QTime.toString(activity.start_time, Database.TIME_FORMAT))
            self.query_update.bindValue(":name", activity.name)
            self.query_update.bindValue(":length", activity.length)
            self.query_update.bindValue(":is_fixed", activity.is_fixed)
            self.query_update.bindValue(":is_rigid", activity.is_rigid)
            Database.execute_query(self.query_update)

            self.calculate()
            self.dataChanged.emit(index, index)
            return True

    def flags(self, index):
        editable_columns = [i for i, col in enumerate(Activity.COLUMNS) if col["user_editable"]]
        if index.column() in editable_columns and index.row() >= self._current_activity_index:
            return super().flags(index) | Qt.ItemIsEditable
        return super().flags(index)
