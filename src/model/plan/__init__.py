import json
from math import floor

from PyQt5.QtCore import (
    Qt,
    QAbstractTableModel,
    QObject,
    QModelIndex,
    QTimer,
    QTime,
    QDateTime,
    pyqtSignal,
    pyqtSlot,
)

from model.storage import Database
from ui.importing import ReplaceOption
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
    def __init__(self, parent, database, config, *args):
        QAbstractTableModel.__init__(self, parent, *args)
        self._activities = []
        self.config = config
        self.database = database
        self._current_activity_index = self.config.get_setting("current_activity_index", 0)

        self.query_count = self.database.get_prepared_query(queries.count)
        self.query_insert = self.database.get_prepared_query(queries.insert_activity)
        self.query_increment = self.database.get_prepared_query(queries.reorder_after_insertion)
        self.query_decrement = self.database.get_prepared_query(queries.reorder_after_deletion)
        self.query_read = self.database.get_prepared_query(queries.get_activities)
        self.query_update = self.database.get_prepared_query(queries.update_activity)
        self.query_delete = self.database.get_prepared_query(queries.delete_activity)
        self.query_clear = self.database.get_prepared_query(queries.delete_all_activities)
        self.query_archive_name = self.database.get_prepared_query(queries.insert_into_activities)
        self.query_insert_into_log = self.database.get_prepared_query(queries.insert_into_log)

        self._read_activities()

    # CRUD operations
    ################################################################################

    def get_activity(self, index):
        return self._activities[index]

    def get_current_activity(self):
        return self._activities[self._current_activity_index]

    def get_following_activity(self):
        return self._activities[self._current_activity_index + 1]

    def insert_activity(self, index, activity=None):
        if activity is None:
            activity = Activity()
        self.insert_activities(index, [activity])

    def insert_activities(self, index, activities):
        if index >= self._current_activity_index:
            self.query_increment.bindValue(":insertion_index", index)
            self.query_increment.bindValue(":offset", len(activities))
            self.database.execute_query(self.query_increment)

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
            if self.database.execute_batch_query(self.query_insert):
                self.layoutAboutToBeChanged.emit()
                self._activities[index:index] = activities
                self.calculate()
                self.layoutChanged.emit()

    def insert_replacement(self, replacement_name):
        current_activity = self.get_current_activity()
        following_activity = self.get_following_activity()

        now = self._get_current_time_rounded()
        replacement = Activity(name=replacement_name)
        replacement.length = now.secsTo(following_activity.start_time) // 60

        insertion_index = self._current_activity_index + 1
        self.insert_activity(insertion_index, replacement)

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
        self.database.execute_batch_query(self.query_delete)

        self.query_decrement.bindValue(":deletion_index", list(reversed(valid_indices)))
        self.database.execute_batch_query(self.query_decrement)

        self.layoutAboutToBeChanged.emit()
        self._activities = [a for i, a in enumerate(self._activities) if i not in valid_indices]
        self.calculate()
        self.layoutChanged.emit()

    def clear(self):
        self.layoutAboutToBeChanged.emit()
        self._activities = []
        self.database.execute_query(self.query_clear)
        self.layoutChanged.emit()

    def move_activity(self, index, new_index):
        self._activities.insert(new_index, self._activities[index])
        self._activities.delete(index + 1)
        self.calculate()

    def import_activities(self, path, options):
        if options["replace_option"] == ReplaceOption.REPLACE:
            query_import = self.database.get_prepared_query(queries.import_activity_replace)
        elif options["replace_option"] == ReplaceOption.ADD:
            query_import = self.database.get_prepared_query(queries.import_activity_add)
        else:
            query_import = self.database.get_prepared_query(queries.import_activity_ignore)

        with open(path) as f:
            activities_json = json.load(f)

            query_import.bindValue(":id", [a["id"] for a in activities_json])
            query_import.bindValue(":order", list(range(len(activities_json))))
            query_import.bindValue(":name", [a["name"] for a in activities_json])
            query_import.bindValue(":length", [a["length"] for a in activities_json])
            query_import.bindValue(":start_time", [a["start_time"] for a in activities_json])
            query_import.bindValue(":is_fixed", [a["is_fixed"] for a in activities_json])
            query_import.bindValue(":is_rigid", [a["is_rigid"] for a in activities_json])

        self.database.execute_batch_query(query_import)

        self.layoutAboutToBeChanged.emit()
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

    # Functionality Helper Methods
    ################################################################################

    def set_current_activity_index(self, index):
        # The final activity marks the end of the plan, so we stop one before the end
        final_activity_index = self.rowCount() - 1
        if index <= final_activity_index:
            # layoutChanged is emitted so the view is updated visually
            self.layoutAboutToBeChanged.emit()
            self._current_activity_index = index
            self.layoutChanged.emit()

            self.config.set_setting("current_activity_index", index)

    def set_current_activity_start_time(self):
        self.setData(
            self.createIndex(
                self._current_activity_index,
                Activity.COLUMN_INDICES["start_time"]
            ),
            self._get_current_time_rounded()
        )

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

            self.set_current_activity_start_time()

    def complete(self):
        self._archive()
        self.set_current_activity_index(0)

    def is_completed(self):
        final_activity_index = self.rowCount() - 1
        return self._current_activity_index >= final_activity_index

    def calculate(self):
        if self._activities:
            self._calculate_actual_lengths()
            self._calculate_optimal_lengths()
            self._calculate_non_fixed_times()

    # Private methods
    ################################################################################

    def _calculate_optimum_factor(self, block_start, block_end):
        """Calculates the amount to compress or expand a block of
        activities to make it fit in between two fixed times"""

        block = self._activities[block_start:block_end]

        actual_size = self._activities[block_start].start_time.secsTo(self._activities[block_end].start_time) / 60
        # Rigid activities can't be compressed or expanded,
        # so they are not accounted for in the block's size
        actual_size -= sum(a.length for a in block if a.is_rigid)

        planned_size = sum(a.length for a in block if not a.is_rigid)

        if planned_size != 0:
            return actual_size / planned_size
        else:
            return 1.0

    def _calculate_optimal_lengths(self):
        factor = self._calculate_optimum_factor(0, -1)
        for activity in self._activities:
            if activity.is_rigid:
                activity.optimal_length = activity.length
            else:
                activity.optimal_length = floor(activity.length * factor)

    def _calculate_actual_lengths(self):
        """
        Activity ActLens are calculated by breaking down the list of
        activities into "blocks" whose boundaries are determined by the
        fixed activities in the list. Inside each of these blocks, the
        activities' ActLens are calculated by expanding or compressing
        their Lengths by the local optimal factor.

        The first and last activities in the list, as well as the current
        activity when the schedule is running, are always considered fixed.
        """

        fixed_indices = [0, len(self._activities) - 1]
        fixed_indices[1:-1] = [
            i for i, activity in enumerate(self._activities)
            if activity.is_fixed
        ][1:-1]

        current_fixed_indices = [self._current_activity_index]
        current_fixed_indices.extend(
            [index for index in fixed_indices if index > self._current_activity_index]
        )

        for i in range(len(current_fixed_indices) - 1):
            block_start = current_fixed_indices[i]
            block_end = current_fixed_indices[i + 1]

            factor = self._calculate_optimum_factor(block_start, block_end)
            for activity in self._activities[block_start:block_end]:
                if activity.is_rigid:
                    activity.actual_length = activity.length
                else:
                    activity.actual_length = floor(activity.length * factor)

    def _calculate_non_fixed_times(self):
        for i in range(self._current_activity_index + 1, len(self._activities) - 1):
            current = self._activities[i]
            prev = self._activities[i - 1]
            if not current.is_fixed:
                current.start_time = prev.start_time.addSecs(prev.actual_length * 60)

    def _read_activities(self):
        self._activities = []
        self.database.execute_query(self.query_read)
        while self.query_read.next():
            activity = self._get_activity_from_db()
            self._activities.append(activity)
        self.calculate()

    def _get_activity_from_db(self):
        activity = Activity(
            id=self.query_read.value("id"),
            name=self.query_read.value("name"),
            length=self.query_read.value("length"),
            start_time=QTime.fromString(self.query_read.value("start_time"), Database.TIME_FORMAT),
            is_fixed=bool(self.query_read.value("is_fixed")),
            is_rigid=bool(self.query_read.value("is_rigid")),
        )

        if self.query_read.value("order") < self._current_activity_index:
            activity.actual_length = self.query_read.value("actual_length")

        return activity

    def _get_current_time_rounded(self):
        # TODO: Round down seconds for simplicity
        now = QTime.currentTime()
        now.setHMS(now.hour(), now.minute(), 0)
        return now

    def _increment_current_activity_index(self):
        self.set_current_activity_index(
            self._current_activity_index + 1
        )

    def _archive(self):
        activities = self._activities[:-1]
        self.query_archive_name.bindValue(":name", [a.name for a in activities])
        self.database.execute_batch_query(self.query_archive_name)

        self.query_insert_into_log.bindValue(":order", [i for i, a in enumerate(activities)])
        self.query_insert_into_log.bindValue(":start_time", [a.start_time.toString(Database.TIME_FORMAT) for a in activities])
        self.query_insert_into_log.bindValue(":name", [a.name for a in activities])
        self.query_insert_into_log.bindValue(":length", [a.length for a in activities])
        self.query_insert_into_log.bindValue(":actual_length", [a.actual_length for a in activities])
        self.query_insert_into_log.bindValue(":optimal_length", [a.optimal_length for a in activities])
        self.query_insert_into_log.bindValue(":is_fixed", [int(a.is_fixed) for a in activities])
        self.query_insert_into_log.bindValue(":is_rigid", [int(a.is_rigid) for a in activities])
        self.database.execute_batch_query(self.query_insert_into_log)

    # Qt API Implementation
    ################################################################################

    def rowCount(self, parent=QModelIndex):
        self.database.execute_query(self.query_count)
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
            self.query_update.bindValue(":actual_length", activity.actual_length)
            self.query_update.bindValue(":is_fixed", activity.is_fixed)
            self.query_update.bindValue(":is_rigid", activity.is_rigid)
            self.database.execute_query(self.query_update)

            self.calculate()
            self.dataChanged.emit(index, index)
            return True

    def flags(self, index):
        editable_columns = [i for i, col in enumerate(Activity.COLUMNS) if col["user_editable"]]
        if index.column() in editable_columns and index.row() >= self._current_activity_index:
            return super().flags(index) | Qt.ItemIsEditable
        return super().flags(index)

class PlanHandler(QObject):
    activityExpired = pyqtSignal(Activity)
    activityStarted = pyqtSignal(Activity)
    activityStopped = pyqtSignal(Activity)
    completed = pyqtSignal()
    countdown = pyqtSignal(int)

    def __init__(self, model, *args, **kwargs):
        super().__init__(model, *args, **kwargs)
        self.model = model

        self.timer_countdown = QTimer(self)
        self.countdown_to = QTime()

        self._connectSignals()

    def _connectSignals(self):
        self.timer_countdown.timeout.connect(self._countdown)

    def _countdown(self):
        self.countdown.emit(self._time_remaining())
        if self._time_remaining() == 0:
            self.activityExpired.emit(self.model.get_current_activity())

    def _time_remaining(self):
        if self.timer_countdown.isActive():
            return QTime().currentTime().secsTo(self.countdown_to)
        return 0

    def start(self, preemptive=False):
        if self.timer_countdown.isActive():
            self.abort()

        if not preemptive:
            self.model.set_current_activity_start_time()

        self.countdown_to = self.model.get_following_activity().start_time
        self.timer_countdown.start(490)
        self.countdown.emit(self._time_remaining())
        self.activityStarted.emit(self.model.get_current_activity())

    def start_from_index(self, index, preemptive=False):
        self.model.set_current_activity_index(index)
        self.start(preemptive)

    def end(self, preemptive=False):
        if self.timer_countdown.isActive():
            self.timer_countdown.stop()
            self.activityStopped.emit(self.model.get_current_activity())

            self.model.complete_activity(preemptive)

            if self.model.is_completed():
                self.model.complete()
                self.completed.emit()
                return

            if preemptive:
                self.start(preemptive)

    def interrupt(self, interruption_name):
        self.model.insert_interruption(interruption_name)
        self.end()

    def replace(self, replacement_name):
        self.model.insert_replacement(replacement_name)
        self.end()

    def abort(self):
        self.timer_countdown.stop()
        self.activityStopped.emit(self.model.get_current_activity())
