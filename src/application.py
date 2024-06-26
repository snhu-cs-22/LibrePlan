from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QStandardPaths, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QApplication, QMessageBox

from model.backup import Backup
from model.config import Config
from model.storage import Database
from model.plan import PlanTableModel, PlanHandler, Activity
from model.tasklist import TasklistTableModel, Task
from ui.main_window import MainWindow

class Application(QApplication):
    PATH_APPDATA = QStandardPaths.writableLocation(
        QStandardPaths.AppDataLocation
    ) + "/LibrePlan"
    PATH_DB = PATH_APPDATA + "/collection.db"
    PATH_BACKUPS = PATH_APPDATA + "/backups"

    EXIT_CODE_RESTART = 6

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.database = Database(self.PATH_DB)
        if not self.database.connect():
            self.db_open_failed_dialog()

        self.config = Config(self.database)
        self.backup = Backup(
            self.PATH_BACKUPS,
            self.database,
            self.config
        )

        self.plan = PlanTableModel(
            self,
            self.database,
            self.config
        )
        self.tasklist = TasklistTableModel(
            self,
            self.database,
            self.config
        )
        self.plan_handler = PlanHandler(self.plan)

        self.main_window = MainWindow(self, self.config)

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

        self.main_window.planCutActivities.connect(self.plan.cut_activities)
        self.main_window.planCopyActivities.connect(self.plan.copy_activities)
        self.main_window.planPasteActivities.connect(self.plan.paste_activities)

        self.main_window.tasklistNewTask.connect(self.tasklist.add_task)
        self.main_window.tasklistDeleteTasks.connect(self.tasklist.delete_tasks)

        self.main_window.backupExportRequested.connect(self.backup.export)
        self.main_window.backupRestoreRequested.connect(self.restore_backup)
        self.main_window.appExitRequested.connect(self.exit_app)

        # Plan Handler
        self.plan_handler.countdownToStart.connect(self.main_window.countdown_to_start)
        self.plan_handler.countdownToEnd.connect(self.main_window.countdown_to_end)
        self.plan_handler.activityBegan.connect(self.main_window.activity_began)
        self.plan_handler.activityStarted.connect(self.main_window.activity_started)
        self.plan_handler.activityExpired.connect(self.main_window.activity_expired)
        self.plan_handler.activityStopped.connect(self.main_window.activity_stopped)
        if self.config.get_setting("user.backup/on_plan_complete", False):
            self.plan_handler.completed.connect(self.backup.create)

    # Dialogs
    ################################################################################

    def db_open_failed_dialog(self):
        dialog = QMessageBox.critical(
            None,
            "Cannot open database",
            "Failed to establish a connection to the database.",
            QMessageBox.Ok
        )

        if dialog == QMessageBox.Ok:
            self.exit_app_unexpected()

    # App exit
    ################################################################################

    def exit_app(self):
        if self.config.get_setting("user.backup/on_exit", True):
            self.backup.create()
        super().exit(0)

    def exit_app_unexpected(self):
        super().exit(1)

    def restore_backup(self, path):
        self.backup.restore(path)
        super().exit(self.EXIT_CODE_RESTART)
