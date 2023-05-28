from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QStandardPaths, QTimer, QTime, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QApplication, QFileDialog, QInputDialog, QMessageBox, QLineEdit

from main_window import MainWindow
from plan import PlanTableModel, Activity
from tasklist import TasklistTableModel, Task

class Application(QApplication):
    PATH_APPDATA = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation) + "/LibrePlan"
    PATH_ACTIVITY_DATA = PATH_APPDATA + "/plan.json"
    PATH_TASK_DATA = PATH_APPDATA + "/tasklist.json"

    countdownUpdateRequested = pyqtSignal(int)
    titleUpdateRequested = pyqtSignal()
    planActivityEnded = pyqtSignal(Activity)
    planCompleted = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.plan = PlanTableModel(self)
        self.tasklist = TasklistTableModel(self)
        self.load_data()

        self.timer_countdown = QTimer()
        self.countdown_to = QTime()

        self.main_window = MainWindow(self)

        self._connectSignals()
        self._connectSlots()
        self.main_window.show()

    # State management
    ################################################################################

    def load_data(self):
        self.plan.import_activities(self.PATH_ACTIVITY_DATA)
        self.tasklist.import_tasks(self.PATH_TASK_DATA)

    def save_data(self):
        self.plan.export_activities(self.PATH_ACTIVITY_DATA)
        self.tasklist.export_tasks(self.PATH_TASK_DATA)

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
        self.main_window.planInterruptRequested.connect(self.plan_interrupt)
        self.main_window.planAbortRequested.connect(self.plan_abort)

        self.main_window.planAppendActivity.connect(
            lambda: self.new_activity(True)
        )
        self.main_window.planInsertActivity.connect(
            lambda: self.new_activity(False)
        )
        self.main_window.planDeleteActivities.connect(self.delete_activities)

        self.main_window.tasklistNewTask.connect(self.new_task)
        self.main_window.tasklistDeleteTasks.connect(self.delete_tasks)

        self.main_window.appExitRequested.connect(self.exit_app)

    # Dialogs
    ################################################################################

    def show_about_dialog(self):
        text = (
            "<center>"
            "<h1>LibrePlan</h1>"
            "<p>A simple, free and open-source day planner and to-do list.</p>"
            "<p>Based on Plan and Tasklist Manager from SuperMemo.</p>"
            "</center>"
        )
        QMessageBox.about(self.main_window, "About LibrePlan", text)

    def import_tasks_dialog(self):
        path = QFileDialog.getOpenFileName(None, "Import Tasks")[0]

        if path:
            if self.tasklist.rowCount(self) != 0:
                replace = QMessageBox.warning(
                            self.main_window, "Replace Tasks?",
                            "There are tasks currently in this list.\n\nWould you like to replace them with what you've imported?",
                            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
                        )

                if replace == QMessageBox.Yes:
                    self.tasklist.import_tasks(path, True)
                elif replace == QMessageBox.No:
                    self.tasklist.import_tasks(path, False)
            else:
                self.tasklist.import_tasks(path)

    def export_tasks_dialog(self, export_all):
        path = QFileDialog.getSaveFileName(None, "Export Tasks")[0]

        if path:
            if export_all:
                self.tasklist.export_tasks(path)
            else:
                selected_indices = self.main_window.get_selected_tasklist_indices()
                self.tasklist.export_tasks(path, selected_indices)

    def new_plan_dialog(self):
        if self.plan.rowCount(self) != 0:
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
            if self.plan.rowCount(self) != 0:
                replace = QMessageBox.warning(
                            self.main_window, "Replace Activities?",
                            "There are activities in the current plan.\n\nWould you like to replace them with what you've imported?",
                            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
                        )

                if replace == QMessageBox.Yes:
                    self.plan.import_activities(path, True)
                elif replace == QMessageBox.No:
                    self.plan.import_activities(path, False)
            else:
                self.plan.import_activities(path)

    def export_activities_dialog(self, export_all):
        path = QFileDialog.getSaveFileName(None, "Export Activities")[0]

        if path:
            if export_all:
                self.plan.export_activities(path)
            else:
                selected_indices = self.main_window.get_selected_plan_indices()
                self.plan.export_activities(path, selected_indices)

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

    def plan_start_from_selected(self, preemptive=False):
        selected_indices = self.main_window.get_selected_plan_indices()
        if selected_indices:
            self.plan.set_current_activity_index(selected_indices[0])
            self.plan_start(preemptive)

    def plan_end(self):
        if self.timer_countdown.isActive():
            self.timer_countdown.stop()

            self.plan.complete_activity()
            self.planCompleted.emit()

            self.save_data()
            self.send_window_title_update_signal()

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

    def plan_abort(self):
        self.timer_countdown.stop()
        self.send_window_title_update_signal()

    # Model handling
    ################################################################################

    def new_activity(self, append):
        selected_indices = self.main_window.get_selected_plan_indices()
        if len(selected_indices) == 0:
            insertion_point = self.plan.rowCount(None)
        elif append:
            insertion_point = selected_indices[0] + 1
        else:
            insertion_point = selected_indices[0]
        self.plan.insert_activity(insertion_point, Activity())

    def delete_activities(self):
        selected_indices = self.main_window.get_selected_plan_indices()
        if selected_indices:
            self.plan.delete_activities(selected_indices)

    def new_task(self):
        self.tasklist.add_task(Task())

    def delete_tasks(self):
        selected_indices = self.main_window.get_selected_tasklist_indices()
        if selected_indices:
            self.tasklist.delete_tasks(selected_indices)

    # App exit
    ################################################################################

    def exit_app(self):
        self.save_data()
        print("Program exited successfully.")
        super().exit(0)
