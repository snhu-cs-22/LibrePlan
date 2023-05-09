import json
from math import floor

from PyQt5.QtCore import QTime

TIME_FORMAT = "hh:mm"

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

class Plan:
    def __init__(self):
        self.activities = []

    def insert_activity(self, index, activity):
        self.activities.insert(index, activity)
        self.calculate()

    def delete_activity(self, index):
        self.activities.pop(index)
        self.calculate()

    def move_activity(self, index, new_index):
        self.activities.insert(new_index, self.activities[index])
        self.activities.delete(index + 1)
        self.calculate()

    def clear(self):
        self.activities = []

    def calculate(self):
        if self.activities:
            self._set_actual_lengths()
            self._set_optimal_lengths()
            self._calculate_non_fixed_times()

    def _calculate_optimum_factor(self, block_start, block_end):
        """Takes the total time duration in block, excluding time taken up by rigid activities since they can't be compressed or expanded, and divides it by the actual allowed block size"""

        block_size = self.activities[block_start].start_time.secsTo(self.activities[block_end].start_time) / 60
        block_lengths = 0

        for activity in self.activities[block_start:block_end]:
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
        for activity in self.activities:
            if activity.is_rigid:
                activity.optimal_length = activity.length
            else:
                activity.optimal_length = floor(activity.length * factor)

    def _set_actual_lengths(self):
        # Keep track of all fixed points in Plan
        self.fixed_points = []
        for i, activity in enumerate(self.activities):
            if activity.is_fixed:
                self.fixed_points.append(i)

        # Use fixed points to define blocks to calculate local OptLens
        for i in range(0, len(self.fixed_points) - 1):
            block_start = self.fixed_points[i]
            block_end = self.fixed_points[i + 1]

            factor = self._calculate_optimum_factor(block_start, block_end)
            for activity in self.activities[block_start:block_end]:
                if activity.is_rigid:
                    activity.actual_length = activity.length
                else:
                    activity.actual_length = floor(activity.length * factor)

    def _calculate_non_fixed_times(self):
        for i in range(1, len(self.activities) - 1):
            if not self.activities[i].is_fixed:
                self.activities[i].start_time = self.activities[i - 1].start_time.addSecs(self.activities[i - 1].actual_length * 60)

    def import_activities(self, path, replace=False):
        with open(path) as f:
            if replace:
                self.activities = []

            activities_json = json.load(f)

            for activity_json in activities_json:
                activity = Activity(
                    name=activity_json["name"],
                    length=activity_json["length"],
                    start_time=QTime.fromString(activity_json["start_time"], TIME_FORMAT),
                    is_fixed=activity_json["is_fixed"],
                    is_rigid=activity_json["is_rigid"]
                )

                self.activities.append(activity)

        self.calculate()

    def export_activities(self, path):
        with open(path, "w") as f:
            activities_properties = []
            for activity in self.activities:
                properties = {
                    "name": activity.name,
                    "length": activity.length,
                    "start_time": activity.start_time.toString(TIME_FORMAT),
                    "is_fixed": activity.is_fixed,
                    "is_rigid": activity.is_rigid,
                }
                activities_properties.append(properties)

            activities_json = json.dumps(activities_properties)
            f.write(activities_json)

    def debug_print_activities(self):
        for activity in self.activities:
            print(f"Name: {activity.name}")
            print(f"    Is Fixed?: {activity.is_fixed}")
            print(f"    Start Time: {activity.start_time.toString(TIME_FORMAT)}")
            print(f"    Is Rigid?: {activity.is_rigid}")
            print(f"    Length: {activity.length}")
            print(f"    ActLen: {activity.actual_length}")
            print(f"    OptLen: {activity.optimal_length}")
            print(f"    Percent: {activity.get_percent()}")
