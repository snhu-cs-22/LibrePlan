import sys
import os
from typing import Callable, Sequence, Tuple, List

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QStandardPaths, QTimer, QTime
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QApplication, QFileDialog, QMainWindow, QMessageBox, QShortcut

from mainwin import Ui_MainWindow
from item_delegates import GenericDelegate, DeadlineTypeDelegate
from plan import Plan
from plan_table import PlanTableModel
from tasklist import Tasklist
from tasklist_table import TasklistTableModel

class MainWindow(QMainWindow, Ui_MainWindow):
    PATH_APPDATA = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation) + "/LibrePlan"
    PATH_ACTIVITY_DATA = PATH_APPDATA + "/plan.json"
    PATH_TASK_DATA = PATH_APPDATA + "/tasklist.json"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)
        self.setupUiEvents()
        self.setupKeys()

        self.plan = Plan()
        self.tasklist = Tasklist()
        self.timer_countdown = QTimer()

        self.set_up_tables()

    # State management
    ################################################################################

    def set_up_tables(self):
        # Plan

        self.plan.import_activities(self.PATH_ACTIVITY_DATA)

        headers = ["F", "R", "Start", "Name", "Length", "ActLen", "OptLen", "Percent"]
        self.plan_model = PlanTableModel(self, self.plan, headers)
        self.plan_model.dataChanged.connect(self.update_title)
        self.table_plan.setModel(self.plan_model)

        self.plan_delegate = GenericDelegate(self)
        self.table_plan.setItemDelegate(self.plan_delegate)

        self.table_plan.resizeColumnsToContents()
        self.table_plan.horizontalHeader().setSectionsMovable(True)

        # Tasklist

        self.tasklist.import_tasks(self.PATH_TASK_DATA)

        headers = ["Priority", "Value", "Cost", "Name", "Date Added", "Deadline", "Halftime", "Deadline Type"]
        self.tasklist_model = TasklistTableModel(self, self.tasklist, headers)
        self.tasklist_model.dataChanged.connect(self.update_title)
        self.table_tasklist.setModel(self.tasklist_model)

        tasklist_delegate = GenericDelegate(self)
        deadline_type_delegate = DeadlineTypeDelegate(self)
        self.table_tasklist.setItemDelegate(tasklist_delegate)
        self.table_tasklist.setItemDelegateForColumn(7, deadline_type_delegate)

        self.table_tasklist.resizeColumnsToContents()
        self.table_tasklist.horizontalHeader().setSectionsMovable(True)

        self.update_title()

    def save_data(self):
        self.plan.export_activities(self.PATH_ACTIVITY_DATA)
        self.tasklist.export_tasks(self.PATH_TASK_DATA)

    # Dialogs
    ################################################################################

    def import_tasklist(self):
        path = QFileDialog.getOpenFileName(self, "Import Tasks")[0]

        if path:
            if self.tasklist.tasks:
                replace = QMessageBox.warning(
                            self, None,
                            "There are tasks currently in this list. Replace?",
                            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
                        )

                if replace == QMessageBox.Yes:
                    self.tasklist.import_tasks(path, True)
                elif replace == QMessageBox.No:
                    self.tasklist.import_tasks(path, False)
            else:
                self.tasklist.import_tasks(path)

    def export_tasklist(self):
        path = QFileDialog.getSaveFileName(self, "Export Tasks")[0]

        if path:
            self.tasklist.export_tasks(path)

    def import_plan(self):
        path = QFileDialog.getOpenFileName(self, "Import Plan")[0]

        if path:
            if self.plan.activities:
                replace = QMessageBox.warning(
                            self, None,
                            "There are activities in the current plan. Replace?",
                            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
                        )

                if replace == QMessageBox.Yes:
                    self.plan.import_activities(path, True)
                elif replace == QMessageBox.No:
                    self.plan.import_activities(path, False)
            else:
                self.plan.import_activities(path)

    def export_plan(self):
        path = QFileDialog.getSaveFileName(self, "Export Plan")[0]

        if path:
            self.plan.export_activities(path)

    def show_about_dialog(self):
        text = (
            "<center>"
            "<h1>LibrePlan</h1>"
            "<p>A simple, free and open-source day planner and to-do list.</p>"
            "<p>Based on Plan and Tasklist Manager from SuperMemo.</p>"
            "</center>"
        )
        QMessageBox.about(self, "About LibrePlan", text)

    def activity_end_dialog(self):
        """Alert user that the activity is ended"""

        # Bring window to front
        self.setWindowState(self.windowState() & ~QtCore.Qt.WindowMinimized | QtCore.Qt.WindowActive)
        self.activateWindow()

        QApplication.alert(self)
        dialog = QMessageBox.question(self, "End of activity", "Time's up for activity: [PLACEHOLDER], end now?")

        if dialog == QMessageBox.Yes:
            self.plan_end()

    # Qt Slots/Signals
    ################################################################################

    def setupUiEvents(self):
        # Menu Actions
        self.actionAbout.triggered.connect(self.show_about_dialog)
        self.actionExit.triggered.connect(self.close)
        self.actionImport_Tasklist.triggered.connect(self.import_tasklist)
        self.actionExport_Tasklist.triggered.connect(self.export_tasklist)
        self.actionImport_Plan.triggered.connect(self.import_plan)
        self.actionExport_Plan.triggered.connect(self.export_plan)

        # Button Actions
        self.pushButton_start.clicked.connect(self.plan_start)
        self.pushButton_end.clicked.connect(self.plan_end)
        self.pushButton_interrupt.clicked.connect(self.plan_interrupt)
        self.pushButton_abort.clicked.connect(self.plan_abort)

        # Other widgets
        self.tasklist_filter.textEdited.connect(self.filter_tasklist)

    def setupKeys(self):
        globalShortcuts = [
            ("Ctrl+R", self.plan_start),
            ("Ctrl+E", self.plan_end),
            ("Ctrl+I", self.plan_interrupt),
            ("Ctrl+B", self.plan_abort),

            ("Ctrl+Tab", lambda: self.cycle_tabs(1)),
            ("Ctrl+Shift+Tab", lambda: self.cycle_tabs(-1)),
        ]
        self.applyShortcuts(globalShortcuts)

    def applyShortcuts(
        self, shortcuts: Sequence[Tuple[str, Callable]]
    ) -> List[QShortcut]:
        qshortcuts = []
        for key, fn in shortcuts:
            scut = QShortcut(QKeySequence(key), self, activated=fn)  # type: ignore
            scut.setAutoRepeat(False)
            qshortcuts.append(scut)
        return qshortcuts

    def filter_tasklist(self, query):
        print("TODO: Implement tasklist filtering functionality")
        print(f"Text query: {query}")

    def cycle_tabs(self, ahead):
        tab_count = self.tabWidget.count()
        next_index = (self.tabWidget.currentIndex() + ahead) % tab_count
        self.tabWidget.setCurrentIndex(next_index)

    # GUI stuff
    ################################################################################

    def update_title(self):
        if self.timer_countdown.isActive():
            self.setWindowTitle(f"{self.stringify_time_duration(self.time_remaining())} - LibrePlan")
        else:
            self.setWindowTitle(f"{len(self.plan.activities) - 1} Activities, {len(self.tasklist.tasks)} Tasks - LibrePlan")

    def stringify_time_duration(self, secs, time_format="hh:mm:ss"):
        """Workaround for having no idea how to properly represent time *durations*"""

        if secs >= 0:
            return QTime(0,0,0).addSecs(secs).toString(f"{time_format}")
        return QTime(0,0,0).addSecs(-secs).toString(f"-{time_format}")

    def time_remaining(self):
        return QTime().currentTime().secsTo(self.timer_countdown_to)

    # App exit
    ################################################################################

    def closeEvent(self, event):
        self.save_data()
        print("Program exited successfully.")

    # Program functions
    ################################################################################

    def plan_start(self):
        print("Activity started")

        # Alert user when countdown reaches zero
        now = QTime.currentTime()
        self.timer_countdown_to = self.plan.activities[1].start_time

        self.timer_activity_end = QTimer()
        self.timer_activity_end.setSingleShot(True)
        self.timer_activity_end.start(now.msecsTo(self.timer_countdown_to))
        self.timer_activity_end.timeout.connect(self.activity_end_dialog)

        # Update title with remaining time when counting down
        self.timer_countdown.timeout.connect(self.update_title)
        self.timer_countdown.start(490)

    def plan_end(self):
        print("Activity ended")
        self.timer_countdown.stop()
        self.timer_activity_end.stop()
        self.update_title()

    def plan_interrupt(self):
        print("Activity interrupted")

    def plan_abort(self):
        print("Activity aborted")
        self.timer_countdown.stop()
        self.timer_activity_end.stop()
        self.update_title()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    mainwin = MainWindow()
    mainwin.show()

    sys.exit(app.exec_())
