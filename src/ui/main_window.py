from typing import Callable, Sequence, Tuple, List

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QEvent, QTime, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QApplication, QMainWindow, QMenu, QShortcut, QSystemTrayIcon

from model.config import Config
from model.plan import PlanTableModel, Activity
from model.tasklist import TasklistTableModel, Task
from ui.forms.main_window import Ui_MainWindow

class MainWindow(QMainWindow, Ui_MainWindow):
    aboutDialogRequested = pyqtSignal()
    planNewRequested = pyqtSignal()
    planImportRequested = pyqtSignal()
    planExportRequested = pyqtSignal(list, bool)
    tasklistImportRequested = pyqtSignal()
    tasklistExportRequested = pyqtSignal(list, bool)

    planStartRequested = pyqtSignal(bool)
    planStartFromSelectedRequested = pyqtSignal(list, bool)
    planEndRequested = pyqtSignal(bool)
    planInterruptRequested = pyqtSignal()
    planReplaceRequested = pyqtSignal()
    planAbortRequested = pyqtSignal()

    planAddActivity = pyqtSignal(int, bool)
    planDeleteActivities = pyqtSignal(list)

    statsWindowRequested = pyqtSignal()

    tasklistNewTask = pyqtSignal()
    tasklistDeleteTasks = pyqtSignal(list)

    appExitRequested = pyqtSignal()

    def __init__(self, application, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.application = application
        self.tray_icon = QSystemTrayIcon(self)

        self.setupUi(self)
        self.restoreState(Config.get_state(self))
        self.restoreGeometry(Config.get_geometry(self))
        self._setupTables(application.plan, application.tasklist)
        self._setupSystemTrayIcon()
        self._connectSignals()
        self._connectSlots()
        self._setupKeys()

    # Qt Slots/Signals
    ################################################################################

    def _connectSignals(self):
        # Menu Actions
        self.actionAbout.triggered.connect(self.aboutDialogRequested)
        self.actionExit.triggered.connect(self.appExitRequested)
        self.actionNew_Plan.triggered.connect(self.planNewRequested)
        self.actionImport_Tasks.triggered.connect(self.tasklistImportRequested)
        self.actionExport_Tasklist.triggered.connect(
            lambda: self.tasklistExportRequested.emit(
                self._get_selected_tasklist_indices(),
                True
            )
        )
        self.actionImport_Activities.triggered.connect(self.planImportRequested)
        self.actionExport_Plan.triggered.connect(
            lambda: self.planExportRequested.emit(
                self._get_selected_plan_indices(),
                True
            )
        )

        self.actionStart_now.triggered.connect(
            lambda: self.planStartRequested.emit(False)
        )
        self.actionStart_Plan_from_Here_Now.triggered.connect(
            lambda: self.planStartFromSelectedRequested.emit(
                self._get_selected_plan_indices(),
                False
            )
        )
        self.actionStart_Plan_Preemptively.triggered.connect(
            lambda: self.planStartRequested.emit(True)
        )
        self.actionStart_Plan_from_Here_Preemptively.triggered.connect(
            lambda: self.planStartFromSelectedRequested.emit(
                self._get_selected_plan_indices(),
                True
            )
        )
        self.actionEnd.triggered.connect(
            lambda: self.planEndRequested.emit(False)
        )
        self.actionEnd_Preemptively.triggered.connect(
            lambda: self.planEndRequested.emit(True)
        )
        self.actionInterrupt.triggered.connect(self.planInterruptRequested)
        self.actionReplace.triggered.connect(self.planReplaceRequested)
        self.actionAbort.triggered.connect(self.planAbortRequested)
        self.actionShow_Statistics.triggered.connect(self.statsWindowRequested)

        self.actionAdd_New_Activity.triggered.connect(
            lambda: self.planAddActivity.emit(
                self._get_first_selected_plan_index(),
                True
            )
        )
        self.actionInsert_New_Activity.triggered.connect(
            lambda: self.planAddActivity.emit(
                self._get_first_selected_plan_index(),
                False
            )
        )
        self.actionExport_Selected_Activities.triggered.connect(
            lambda: self.planExportRequested.emit(
                self._get_selected_plan_indices(),
                False
            )
        )
        self.actionDelete_Selected_Activities.triggered.connect(
            lambda: self.planDeleteActivities.emit(
                self._get_selected_plan_indices()
            )
        )

        self.actionNew_Task.triggered.connect(self.tasklistNewTask)
        self.actionExport_Selected_Tasks.triggered.connect(
            lambda: self.tasklistExportRequested.emit(
                self._get_selected_tasklist_indices(),
                False
            )
        )
        self.actionDelete_Selected_Tasks.triggered.connect(
            lambda: self.tasklistDeleteTasks.emit(
                self._get_selected_tasklist_indices()
            )
        )

        # Button Actions
        self.pushButton_start_now.clicked.connect(
            lambda: self.planStartRequested.emit(False)
        )
        self.pushButton_end.clicked.connect(
            lambda: self.planEndRequested.emit(False)
        )
        self.pushButton_interrupt.clicked.connect(self.planInterruptRequested)
        self.pushButton_abort.clicked.connect(self.planAbortRequested)

        self.pushButton_new_task.clicked.connect(self.tasklistNewTask)
        self.pushButton_add_activity.clicked.connect(
            lambda: self.planAddActivity.emit(
                self._get_selected_plan_indices(),
                True
            )
        )

        # Other widgets
        self.tasklist_filter.textEdited.connect(self.filter_tasklist)

        self.tray_icon.activated.connect(self.show)
        self.tray_icon.messageClicked.connect(self.show)

        self.table_tasklist.model().layoutChanged.connect(self.update_title)
        self.table_plan.model().layoutChanged.connect(self.update_title)

        self.table_tasklist.selectionModel().selectionChanged.connect(
            lambda: self.show_selection_count(self.table_tasklist.selectionModel())
        )
        self.table_plan.selectionModel().selectionChanged.connect(
            lambda: self.show_selection_count(self.table_plan.selectionModel())
        )

        self.table_plan.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_plan.customContextMenuRequested.connect(
            lambda pos: self._show_context_menu(
                self.table_plan.viewport(),
                self.menuActivity,
                pos
            )
        )
        self.table_tasklist.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_tasklist.customContextMenuRequested.connect(
            lambda pos: self._show_context_menu(
                self.table_tasklist.viewport(),
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
        self.appExitRequested.connect(self.hide)
        self.application.countdownUpdateRequested.connect(self.update_title_countdown)
        self.application.titleUpdateRequested.connect(self.update_title)
        self.application.planActivityEnded.connect(self._message_activity_end)
        self.application.planActivityCompleted.connect(self._on_activity_completed)

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

    def _setupSystemTrayIcon(self):
        self.tray_icon.setIcon(self.windowIcon())
        self.tray_icon.setVisible(True)

        self.tray_icon_menu = QMenu(self)
        self.tray_icon_menu.addAction(self.actionExit)
        self.tray_icon.setContextMenu(self.tray_icon_menu)

    def _message_activity_end(self, current_activity):
        self.tray_icon.showMessage(
            f"Time's up for activity \"{current_activity.name}.\"",
            "Click \"Finish\" to stop countdown."
        )

    def _setupTables(self, plan_model, tasklist_model):
        # Plan

        self.table_plan.setModel(plan_model)
        for i, col in enumerate(Activity.COLUMNS):
            self.table_plan.setItemDelegateForColumn(i, col["delegate"](self))

        self.table_plan.horizontalHeader().setSectionsMovable(True)
        self.table_plan.horizontalHeader().restoreState(
            bytes(
                Config.get_setting(
                    "ui.plan/header_state",
                    self.table_plan.horizontalHeader().saveState()
                )
            )
        )
        self._populate_header_context_menu(self.table_plan, self.menuPlan_Show_Hide_Columns)

        # Tasklist

        self.table_tasklist.setModel(tasklist_model)
        for i, col in enumerate(Task.COLUMNS):
            self.table_tasklist.setItemDelegateForColumn(i, col["delegate"](self))

        self.table_tasklist.horizontalHeader().setSectionsMovable(True)
        self.table_tasklist.horizontalHeader().restoreState(
            bytes(
                Config.get_setting(
                    "ui.tasklist/header_state",
                    self.table_tasklist.horizontalHeader().saveState()
                )
            )
        )
        self._populate_header_context_menu(self.table_tasklist, self.menuTasklist_Show_Hide_Columns)

        self.update_title()

    def _get_selected_plan_indices(self):
        return sorted([index.row() for index in self.table_plan.selectionModel().selectedRows()])

    def _get_first_selected_plan_index(self):
        selected_indices = self._get_selected_plan_indices()
        return selected_indices[0] if selected_indices else None

    def _get_selected_tasklist_indices(self):
        return sorted([index.row() for index in self.table_tasklist.selectionModel().selectedRows()])

    def filter_tasklist(self, query):
        print("TODO: Implement tasklist filtering functionality")
        print(f"Text query: {query}")

    def show_selection_count(self, selection_model):
        count = len(selection_model.selectedRows())
        self.statusbar.showMessage(f"{count} selected")

    def update_title(self):
        activity_count = self.table_plan.model().rowCount() - 1
        task_count = self.table_tasklist.model().rowCount()

        self.setWindowTitle(f"{activity_count} Activities, {task_count} Tasks - LibrePlan")
        self.tray_icon.setToolTip(self.windowTitle())

    def update_title_countdown(self, secs_to):
        self.setWindowTitle(f"{self._stringify_time_duration(secs_to)} - LibrePlan")
        self.tray_icon.setToolTip(self.windowTitle())

    def _stringify_time_duration(self, secs, time_format="hh:mm:ss"):
        """Workaround for having no idea how to properly represent time *durations*"""

        if secs >= 0:
            return QTime(0,0,0).addSecs(secs).toString(f"{time_format}")
        return QTime(0,0,0).addSecs(-secs).toString(f"-{time_format}")

    def _on_activity_completed(self):
        self.tabWidget.setCurrentIndex(0)

    def _show_context_menu(self, obj, menu, pos):
        gpos = obj.mapToGlobal(pos)
        menu.exec_(gpos)

    def _populate_header_context_menu(self, table_view, menu):
        table_model = table_view.model()
        for i in range(table_model.columnCount()):
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

    # Qt API Implementation
    ################################################################################

    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            if self.windowState() & Qt.WindowMinimized:
                self.hide()

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def show(self):
        super().show()
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
        self.activateWindow()

    def hide(self):
        super().hide()
        Config.set_state(self)
        Config.set_geometry(self)
        Config.set_setting(
            "ui.plan/header_state",
            self.table_plan.horizontalHeader().saveState()
        )
        Config.set_setting(
            "ui.tasklist/header_state",
            self.table_tasklist.horizontalHeader().saveState()
        )
