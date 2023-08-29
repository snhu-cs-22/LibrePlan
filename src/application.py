from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QApplication, QMessageBox

from model.database import Database
from model.plan import PlanTableModel, PlanHandler, Activity
from model.tasklist import TasklistTableModel, Task
from ui.main_window import MainWindow

class Application(QApplication):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.plan = PlanTableModel(self)
        self.plan_handler = PlanHandler(self.plan)

        self.tasklist = TasklistTableModel(self)

        self.main_window = MainWindow(self)

        self._connectSlots()
        self.main_window.show()

    # Qt Slots/Signals
    ################################################################################

    def _connectSlots(self):
        # Main window
        self.main_window.planNewRequested.connect(self.plan.clear)
        self.main_window.planImportRequested.connect(self.plan.import_activities)
        self.main_window.planExportRequested.connect(self.plan.export_activities)
        self.main_window.tasklistImportRequested.connect(self.tasklist.import_tasks)
        self.main_window.tasklistExportRequested.connect(self.tasklist.export_tasks)

        self.main_window.planStartRequested.connect(self.plan_handler.start)
        self.main_window.planStartFromSelectedRequested.connect(self.plan_handler.start_from_index)
        self.main_window.planEndRequested.connect(self.plan_handler.end)
        self.main_window.planReplaceRequested.connect(self.plan_handler.replace)
        self.main_window.planInterruptRequested.connect(self.plan_handler.interrupt)
        self.main_window.planAbortRequested.connect(self.plan_handler.abort)

        self.main_window.planInsertActivity.connect(self.plan.insert_activity)
        self.main_window.planDeleteActivities.connect(self.plan.delete_activities)

        self.main_window.tasklistNewTask.connect(self.tasklist.add_task)
        self.main_window.tasklistDeleteTasks.connect(self.tasklist.delete_tasks)

        self.main_window.appExitRequested.connect(self.exit_app)

        # Plan Handler
        self.plan_handler.countdown.connect(self.main_window.update_title_countdown)
        self.plan_handler.activityExpired.connect(self.main_window.activity_expired)
        self.plan_handler.activityStopped.connect(self.main_window.update_title)

    # Dialogs
    ################################################################################

    def db_open_failed_dialog(self):
        dialog = QMessageBox.critical(
            self.main_window,
            "Cannot open database",
            "Failed to establish a connection to the database.",
            QMessageBox.Ok
        )

        if dialog == QMessageBox.Ok:
            self.exit_app_unexpected()

    # App exit
    ################################################################################

    def exit_app(self):
        print("Program exited successfully.")
        super().exit(0)

    def exit_app_unexpected(self):
        super.exit(1)
