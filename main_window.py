from typing import Callable, Sequence, Tuple, List

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QTime, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QApplication, QMainWindow, QMenu, QShortcut

from ui.forms.main_window import Ui_MainWindow
from item_delegates import GenericDelegate, BoolDelegate, DeadlineTypeDelegate, PercentDelegate
from plan import PlanTableModel
from tasklist import TasklistTableModel

class MainWindow(QMainWindow, Ui_MainWindow):
    aboutDialogRequested = pyqtSignal()
    planImportRequested = pyqtSignal()
    planExportRequested = pyqtSignal(bool)
    tasklistImportRequested = pyqtSignal()
    tasklistExportRequested = pyqtSignal(bool)

    planStartRequested = pyqtSignal()
    planEndRequested = pyqtSignal()
    planInterruptRequested = pyqtSignal()
    planAbortRequested = pyqtSignal()

    planAppendActivity = pyqtSignal()
    planInsertActivity = pyqtSignal()
    planDeleteActivities = pyqtSignal()

    tasklistNewTask = pyqtSignal()
    tasklistDeleteTasks = pyqtSignal()

    appExitRequested = pyqtSignal()

    def __init__(self, application, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.application = application
        self.setupUi(self)
        self._setupTables(application.plan, application.tasklist)
        self._connectSignals()
        self._connectSlots()
        self._setupKeys()

    # Qt Slots/Signals
    ################################################################################

    def _connectSignals(self):
        # Menu Actions
        self.actionAbout.triggered.connect(self.aboutDialogRequested)
        self.actionExit.triggered.connect(self.appExitRequested)
        self.actionImport_Tasks.triggered.connect(self.tasklistImportRequested)
        self.actionExport_Tasklist.triggered.connect(
            lambda: self.tasklistExportRequested.emit(True)
        )
        self.actionImport_Activities.triggered.connect(self.planImportRequested)
        self.actionExport_Plan.triggered.connect(
            lambda: self.planExportRequested.emit(True)
        )

        self.actionStart.triggered.connect(self.planStartRequested)
        self.actionEnd.triggered.connect(self.planEndRequested)
        self.actionInterrupt.triggered.connect(self.planInterruptRequested)
        self.actionAbort.triggered.connect(self.planAbortRequested)

        self.actionAdd_New_Activity.triggered.connect(self.planAppendActivity)
        self.actionInsert_New_Activity.triggered.connect(self.planInsertActivity)
        self.actionExport_Selected_Activities.triggered.connect(
            lambda: self.planExportRequested.emit(False)
        )
        self.actionDelete_Selected_Activities.triggered.connect(self.planDeleteActivities)

        self.actionNew_Task.triggered.connect(self.tasklistNewTask)
        self.actionExport_Selected_Tasks.triggered.connect(
            lambda: self.tasklistExportRequested.emit(False)
        )
        self.actionDelete_Selected_Tasks.triggered.connect(self.tasklistDeleteTasks)

        # Button Actions
        self.pushButton_start.clicked.connect(self.planStartRequested)
        self.pushButton_end.clicked.connect(self.planEndRequested)
        self.pushButton_interrupt.clicked.connect(self.planInterruptRequested)
        self.pushButton_abort.clicked.connect(self.planAbortRequested)

        self.pushButton_new_task.clicked.connect(self.tasklistNewTask)
        self.pushButton_add_activity.clicked.connect(self.planAppendActivity)

        # Other widgets
        self.tasklist_filter.textEdited.connect(self.filter_tasklist)

        self.table_plan.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_plan.customContextMenuRequested.connect(
            lambda pos: self._show_context_menu(
                self.table_plan,
                self.menuActivity,
                pos
            )
        )
        self.table_tasklist.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_tasklist.customContextMenuRequested.connect(
            lambda pos: self._show_context_menu(
                self.table_tasklist,
                self.menuTask,
                pos
            )
        )
        self.table_plan.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_plan.horizontalHeader().customContextMenuRequested.connect(
            lambda pos: self._show_context_menu(
                self.table_plan,
                self.menuPlan_Show_Hide_Columns,
                pos
            )
        )
        self.table_tasklist.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_tasklist.horizontalHeader().customContextMenuRequested.connect(
            lambda pos: self._show_context_menu(
                self.table_tasklist,
                self.menuTasklist_Show_Hide_Columns,
                pos
            )
        )

    def _connectSlots(self):
        self.application.countdownUpdateRequested.connect(self.update_title_countdown)
        self.application.titleUpdateRequested.connect(self.update_title)
        self.application.planCompleted.connect(self._on_plan_completed)

    def _setupKeys(self):
        globalShortcuts = [
            ("Ctrl+Tab", lambda: self.cycle_tabs(1)),
            ("Ctrl+Shift+Tab", lambda: self.cycle_tabs(-1)),
        ]
        self._applyShortcuts(globalShortcuts)

    def _applyShortcuts(
        self, shortcuts: Sequence[Tuple[str, Callable]]
    ) -> List[QShortcut]:
        qshortcuts = []
        for key, fn in shortcuts:
            scut = QShortcut(QKeySequence(key), self, activated=fn)  # type: ignore
            scut.setAutoRepeat(False)
            qshortcuts.append(scut)
        return qshortcuts

    # GUI stuff
    ################################################################################

    def cycle_tabs(self, ahead):
        tab_count = self.tabWidget.count()
        next_index = (self.tabWidget.currentIndex() + ahead) % tab_count
        self.tabWidget.setCurrentIndex(next_index)

    def _setupTables(self, plan_model, tasklist_model):
        # Plan

        self.plan_delegate = GenericDelegate(self)
        self.tasklist_delegate = GenericDelegate(self)
        self.bool_delegate = BoolDelegate(self)
        self.deadline_type_delegate = DeadlineTypeDelegate(self)
        self.percent_delegate = PercentDelegate(self)

        self.table_plan.setModel(plan_model)
        self.table_plan.setItemDelegate(self.plan_delegate)
        self.table_plan.setItemDelegateForColumn(0, self.bool_delegate)
        self.table_plan.setItemDelegateForColumn(1, self.bool_delegate)
        self.table_plan.setItemDelegateForColumn(7, self.percent_delegate)

        self.table_plan.resizeColumnsToContents()
        self.table_plan.horizontalHeader().setSectionsMovable(True)
        self._populate_header_context_menu(self.table_plan, self.menuPlan_Show_Hide_Columns)

        # Tasklist

        self.table_tasklist.setModel(tasklist_model)
        self.table_tasklist.setItemDelegate(self.tasklist_delegate)
        self.table_tasklist.setItemDelegateForColumn(0, self.percent_delegate)
        self.table_tasklist.setItemDelegateForColumn(7, self.deadline_type_delegate)

        self.table_tasklist.resizeColumnsToContents()
        self.table_tasklist.horizontalHeader().setSectionsMovable(True)
        self._populate_header_context_menu(self.table_tasklist, self.menuTasklist_Show_Hide_Columns)

        self.update_title()

    def get_selected_plan_indices(self):
        return [index.row() for index in self.table_plan.selectionModel().selectedRows()]

    def get_selected_tasklist_indices(self):
        return [index.row() for index in self.table_tasklist.selectionModel().selectedRows()]

    def filter_tasklist(self, query):
        print("TODO: Implement tasklist filtering functionality")
        print(f"Text query: {query}")

    def update_title(self):
        activity_count = self.table_plan.model().rowCount(None) - 1
        task_count = self.table_tasklist.model().rowCount(None)

        self.setWindowTitle(f"{activity_count} Activities, {task_count} Tasks - LibrePlan")

    def update_title_countdown(self, secs_to):
        self.setWindowTitle(f"{self._stringify_time_duration(secs_to)} - LibrePlan")

    def _stringify_time_duration(self, secs, time_format="hh:mm:ss"):
        """Workaround for having no idea how to properly represent time *durations*"""

        if secs >= 0:
            return QTime(0,0,0).addSecs(secs).toString(f"{time_format}")
        return QTime(0,0,0).addSecs(-secs).toString(f"-{time_format}")

    def _on_plan_completed(self):
        self.tabWidget.setCurrentIndex(0)

    def _show_context_menu(self, obj, menu, pos):
        gpos = obj.mapToGlobal(pos)
        menu.exec_(gpos)

    def _populate_header_context_menu(self, table_view, menu):
        table_model = table_view.model()
        for i in range(table_model.columnCount(None)):
            action = menu.addAction(table_model.headerData(i))
            action.setCheckable(True)
            action.setChecked(not table_view.isColumnHidden(i))
            action.toggled.connect(
                lambda checked, i=i, table_view=table_view:
                    self._toggle_column_visibility(table_view, i, checked)
            )

    def _toggle_column_visibility(self, table_view, column, checked):
        if checked:
            table_view.showColumn(column)
        else:
            table_view.hideColumn(column)
