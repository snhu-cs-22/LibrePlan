from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QStandardPaths, QTimer, QTime, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox, QShortcut

from main_window import MainWindow
from plan import PlanTableModel
from tasklist import TasklistTableModel

class Application(QApplication):
    PATH_APPDATA = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation) + "/LibrePlan"
    PATH_ACTIVITY_DATA = PATH_APPDATA + "/plan.json"
    PATH_TASK_DATA = PATH_APPDATA + "/tasklist.json"

    countdownUpdateRequested = pyqtSignal(int)
    titleUpdateRequested = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.plan = PlanTableModel(self)
        self.tasklist = TasklistTableModel(self)
        self.load_data()

        self.timer_activity_end = QTimer()
        self.timer_activity_end.setSingleShot(True)
        self.timer_countdown = QTimer()

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
        # Timers
        self.timer_activity_end.timeout.connect(self.activity_end_dialog)
        self.timer_countdown.timeout.connect(self.send_window_title_update_signal)

        # Data
        self.plan.dataChanged.connect(self.titleUpdateRequested)
        self.tasklist.dataChanged.connect(self.titleUpdateRequested)

    def _connectSlots(self):
        # Main window
        self.main_window.aboutDialogRequested.connect(self.show_about_dialog)
        self.main_window.planImportRequested.connect(self.import_plan_dialog)
        self.main_window.planExportRequested.connect(self.export_plan_dialog)
        self.main_window.tasklistImportRequested.connect(self.import_tasklist_dialog)
        self.main_window.tasklistExportRequested.connect(self.export_tasklist_dialog)

        self.main_window.planStartRequested.connect(self.plan_start)
        self.main_window.planEndRequested.connect(self.plan_end)
        self.main_window.planInterruptRequested.connect(self.plan_interrupt)
        self.main_window.planAbortRequested.connect(self.plan_abort)

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

    def activity_end_dialog(self):
        """Alert user that the activity is ended"""

        # Bring main window to front
        self.main_window.setWindowState(self.main_window.windowState() & ~QtCore.Qt.WindowMinimized | QtCore.Qt.WindowActive)
        self.main_window.activateWindow()

        self.alert(self.main_window)
        dialog = QMessageBox.question(self.main_window, "End of activity", "Time's up for activity: [PLACEHOLDER], end now?")

        if dialog == QMessageBox.Yes:
            self.plan_end()

    def import_tasklist_dialog(self):
        path = QFileDialog.getOpenFileName(None, "Import Tasks")[0]

        if path:
            if self.tasklist.rowCount(self) != 0:
                replace = QMessageBox.warning(
                            None, None,
                            "There are tasks currently in this list. Replace?",
                            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
                        )

                if replace == QMessageBox.Yes:
                    self.tasklist.import_tasks(path, True)
                elif replace == QMessageBox.No:
                    self.tasklist.import_tasks(path, False)
            else:
                self.tasklist.import_tasks(path)

    def export_tasklist_dialog(self):
        path = QFileDialog.getSaveFileName(None, "Export Tasks")[0]

        if path:
            self.tasklist.export_tasks(path)

    def import_plan_dialog(self):
        path = QFileDialog.getOpenFileName(None, "Import Plan")[0]

        if path:
            if self.plan.rowCount(self) != 0:
                replace = QMessageBox.warning(
                            None, None,
                            "There are activities in the current plan. Replace?",
                            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
                        )

                if replace == QMessageBox.Yes:
                    self.plan.import_activities(path, True)
                elif replace == QMessageBox.No:
                    self.plan.import_activities(path, False)
            else:
                self.plan.import_activities(path)

    def export_plan_dialog(self):
        path = QFileDialog.getSaveFileName(None, "Export Plan")[0]

        if path:
            self.plan.export_activities(path)

    # Program functions
    ################################################################################

    def send_window_title_update_signal(self):
        if self.timer_countdown.isActive():
            self.countdownUpdateRequested.emit(self._time_remaining())
        else:
            self.titleUpdateRequested.emit()

    def _time_remaining(self):
        return QTime().currentTime().secsTo(self.countdown_to)

    def plan_start(self):
        print("Activity started")

        now = QTime.currentTime()
        self.countdown_to = self.plan.get_activity(1).start_time
        self.timer_activity_end.start(now.msecsTo(self.countdown_to))
        self.timer_countdown.start(490)

        self.send_window_title_update_signal()

    def plan_end(self):
        print("Activity ended")
        self.timer_countdown.stop()
        self.timer_activity_end.stop()
        self.send_window_title_update_signal()

    def plan_interrupt(self):
        print("Activity interrupted")

    def plan_abort(self):
        print("Activity aborted")
        self.timer_countdown.stop()
        self.timer_activity_end.stop()
        self.send_window_title_update_signal()

    # App exit
    ################################################################################

    def exit_app(self):
        self.save_data()
        print("Program exited successfully.")
        super().exit(0)
