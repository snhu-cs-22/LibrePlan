import json
from enum import Enum, auto

from PyQt5.QtCore import QDate

DATE_FORMAT = "yyyy-MM-dd"

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

class Tasklist:
    def __init__(self, tasks=[]):
        self.tasks = tasks

    def add_task(self, task=Task()):
        today = QDate.currentDate()
        task.calculate_priority(today)
        self.tasks.append(task)

    def delete_task(self, index=0):
        self.tasks.pop(index)

    def clear(self):
        self.tasks = []

    def calculate(self):
        today = QDate.currentDate()
        if self.tasks:
            for task in self.tasks:
                task.calculate_priority(today)
            self.tasks.sort(key = lambda task: task.priority, reverse = True)

    def import_tasks(self, path, replace=False):
        with open(path) as f:
            if replace:
                self.tasks = []

            tasks_json = json.load(f)

            for task_json in tasks_json:
                task = Task()
                task.name = task_json["name"]
                task.value = task_json["value"]
                task.cost = task_json["cost"]
                task.DATE_CREATED = QDate.fromString(task_json["DATE_CREATED"], DATE_FORMAT)
                try:
                    task.set_deadline(QDate.fromString(task_json["deadline"], DATE_FORMAT))
                    task.deadline_type = DeadlineType[task_json["deadline_type"]]
                except:
                    task.deadline_type = DeadlineType.NONE

                self.tasks.append(task)

        self.calculate()

    def export_tasks(self, path):
        with open(path, "w") as f:
            tasks_properties = []
            for task in self.tasks:
                properties = {}

                properties["name"] = task.name
                properties["value"] = task.value
                properties["cost"] = task.cost
                properties["DATE_CREATED"] = task.DATE_CREATED.toString(DATE_FORMAT)
                properties["deadline_type"] = task.deadline_type.name
                properties["deadline"] = task.deadline.toString(DATE_FORMAT)

                tasks_properties.append(properties)

            tasks_json = json.dumps(tasks_properties)
            f.write(tasks_json)

    def debug_print_tasks(self):
        for task in self.tasks:
            print(f"Name: {task.name}: ")
            print(f"    Priority: {'{:.2f}'.format(task.priority)}")
            print(f"    Value: {task.value}")
            print(f"    Cost: {task.cost}")
            print(f"    Date Added: {task.DATE_CREATED.toString(DATE_FORMAT)}")
            print(f"    Deadline: {task.deadline.toString(DATE_FORMAT)}")
            print(f"    Halftime: {task.halftime.toString(DATE_FORMAT)}")
            print(f"    Deadline Type: {task.deadline_type}")
