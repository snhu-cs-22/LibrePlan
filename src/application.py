from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QStandardPaths, QTimer, QTime, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QApplication, QFileDialog, QInputDialog, QMessageBox, QLineEdit

from model.database import Database
from model.plan import PlanTableModel, Activity
from model.tasklist import TasklistTableModel, Task
from ui.importing import ImportDialog
from ui.main_window import MainWindow
from ui.stats import StatsDialog

class Application(QApplication):
    PATH_APPDATA = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation) + "/LibrePlan"
    PATH_DB = PATH_APPDATA + "/collection.db"

    countdownUpdateRequested = pyqtSignal(int)
    titleUpdateRequested = pyqtSignal()
    planActivityEnded = pyqtSignal(Activity)
    planActivityCompleted = pyqtSignal()
    planCompleted = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.db = Database()
        self.db.connect(self.PATH_DB)

        self.plan = PlanTableModel(self)
        self.tasklist = TasklistTableModel(self)

        self.timer_countdown = QTimer()
        self.countdown_to = QTime()

        self.main_window = MainWindow(self)

        self._connectSignals()
        self._connectSlots()
        self.main_window.show()

    # Qt Slots/Signals
    ################################################################################

    def _connectSignals(self):
        self.timer_countdown.timeout.connect(self.countdown)

        self.plan.dataChanged.connect(self.titleUpdateRequested)
        self.tasklist.dataChanged.connect(self.titleUpdateRequested)

    def _connectSlots(self):
        # Main window
        self.main_window.aboutDialogRequested.connect(self.show_about_dialog)
        self.main_window.planNewRequested.connect(self.new_plan_dialog)
        self.main_window.planImportRequested.connect(self.import_activities_dialog)
        self.main_window.planExportRequested.connect(self.export_activities_dialog)
        self.main_window.tasklistImportRequested.connect(self.import_tasks_dialog)
        self.main_window.tasklistExportRequested.connect(self.export_tasks_dialog)

        self.main_window.planStartRequested.connect(self.plan_start)
        self.main_window.planStartFromSelectedRequested.connect(self.plan_start_from_selected)
        self.main_window.planEndRequested.connect(self.plan_end)
        self.main_window.planReplaceRequested.connect(self.plan_replace)
        self.main_window.planInterruptRequested.connect(self.plan_interrupt)
        self.main_window.planAbortRequested.connect(self.plan_abort)

        self.main_window.planAddActivity.connect(self.add_activity)
        self.main_window.planDeleteActivities.connect(self.delete_activities)

        self.main_window.statsWindowRequested.connect(self.show_stats_dialog)

        self.main_window.tasklistNewTask.connect(self.add_task)
        self.main_window.tasklistDeleteTasks.connect(self.delete_tasks)

        self.main_window.appExitRequested.connect(self.exit_app)

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

    def show_about_dialog(self):
        text = (
            "<center>"
            "<h1>LibrePlan</h1>"
            "<p>A simple, free and open-source day planner and to-do list.</p>"
            "<p>Based on Plan and Tasklist Manager from SuperMemo.</p>"
            "</center>"
        )
        QMessageBox.about(self.main_window, "About LibrePlan", text)

    def show_stats_dialog(self):
        self.stats_dialog = StatsDialog(self)
        self.stats_dialog.show()

    def import_tasks_dialog(self):
        path = QFileDialog.getOpenFileName(None, "Import Tasks")[0]

        if path:
            self.import_dialog = ImportDialog(self.tasklist, path)

    def export_tasks_dialog(self, indices, export_all):
        path = QFileDialog.getSaveFileName(None, "Export Tasks")[0]

        if path:
            if export_all:
                self.tasklist.export_tasks(path)
            else:
                self.tasklist.export_tasks(path, indices)

    def new_plan_dialog(self):
        if self.plan.rowCount() != 0:
            discard = QMessageBox.warning(
                        self.main_window, "Discard Activities?",
                        "There are activities in the current plan.\n\nWould you like to discard them?",
                        QMessageBox.Ok | QMessageBox.Cancel
                    )

            if discard == QMessageBox.Ok:
                self.plan.clear()

    def import_activities_dialog(self):
        path = QFileDialog.getOpenFileName(None, "Import Activities")[0]

        if path:
            self.import_dialog = ImportDialog(self.plan, path)

    def export_activities_dialog(self, indices, export_all):
        path = QFileDialog.getSaveFileName(None, "Export Activities")[0]

        if path:
            if export_all:
                self.plan.export_activities(path)
            else:
                self.plan.export_activities(path, indices)

    # Plan functionality
    ################################################################################

    def countdown(self):
        self.send_window_title_update_signal()
        if self._time_remaining() == 0:
            self.send_activity_ended_signal()

    def send_activity_ended_signal(self):
        self.planActivityEnded.emit(self.plan.get_current_activity())

    def send_window_title_update_signal(self):
        if self.timer_countdown.isActive():
            self.countdownUpdateRequested.emit(self._time_remaining())
        else:
            self.titleUpdateRequested.emit()

    def _time_remaining(self):
        if self.timer_countdown.isActive():
            return QTime().currentTime().secsTo(self.countdown_to)
        return 0

    def plan_start(self, preemptive=False):
        if self.timer_countdown.isActive():
            self.plan_abort()

        if not preemptive:
            self.plan.set_current_activity_start_time()

        self.countdown_to = self.plan.get_following_activity().start_time
        self.timer_countdown.start(490)

        self.send_window_title_update_signal()

    def plan_start_from_selected(self, selected_indices, preemptive=False):
        if selected_indices:
            self.plan.set_current_activity_index(selected_indices[0])
            self.plan_start(preemptive)

    def plan_end(self, preemptive=False):
        if self.timer_countdown.isActive():
            self.timer_countdown.stop()

            self.plan.complete_activity(preemptive)
            self.planActivityCompleted.emit()

            if self.plan.is_completed():
                self.plan.complete()
                self.planCompleted.emit()
                self.send_window_title_update_signal()
                return

            if preemptive:
                self.plan_start(preemptive)

    def plan_interrupt(self):
        input_text, ok = QInputDialog().getText(
                    self.main_window,
                    "Interrupt activity...",
                    "Set name for interruption:"
                )

        if ok and input_text:
            self.plan.insert_interruption(input_text)
            self.plan_end()

        self.send_window_title_update_signal()

    def plan_replace(self):
        input_text, ok = QInputDialog().getText(
                    self.main_window,
                    "Replace activity...",
                    "Set name for replacement:"
                )

        if ok and input_text:
            self.plan.insert_replacement(input_text)
            self.plan_end()

        self.send_window_title_update_signal()

    def plan_abort(self):
        self.timer_countdown.stop()
        self.send_window_title_update_signal()

    # Model handling
    ################################################################################

    def add_activity(self, index, append):
        if not index:
            insertion_point = self.plan.rowCount()
        elif append:
            insertion_point = index + 1
        else:
            insertion_point = index
        self.plan.insert_activity(insertion_point, Activity())

    def delete_activities(self, indices):
        if indices:
            self.plan.delete_activities(indices)

    def add_task(self):
        self.tasklist.add_task(Task())

    def delete_tasks(self, indices):
        if indices:
            self.tasklist.delete_tasks(indices)

    # App exit
    ################################################################################

    def exit_app(self):
        self.db.disconnect()
        print("Program exited successfully.")
        super().exit(0)

    def exit_app_unexpected(self):
        super.exit(1)
