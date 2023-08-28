from typing import Callable, Sequence, Tuple, List

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import (
    Qt,
    QRegularExpression,
    QEvent,
    QTime,
    pyqtSignal,
    pyqtSlot,
)
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QFileDialog,
    QMessageBox,
    QMenu,
    QShortcut,
    QSystemTrayIcon,
)

from model.config import Config
from model.plan import PlanTableModel, Activity
from model.tasklist import TasklistTableModel, TasklistProxyModel, Task
from ui.forms.main_window import Ui_MainWindow
from ui.importing import ImportDialog, ReplaceOption
from ui.stats import StatsDialog

class MainWindow(QMainWindow, Ui_MainWindow):
    planNewRequested = pyqtSignal()
    planImportRequested = pyqtSignal(str, dict)
    planExportRequested = pyqtSignal(str, list)
    tasklistImportRequested = pyqtSignal(str, dict)
    tasklistExportRequested = pyqtSignal(str, list)

    planStartRequested = pyqtSignal(bool)
    planStartFromSelectedRequested = pyqtSignal(list, bool)
    planEndRequested = pyqtSignal(bool)
    planInterruptRequested = pyqtSignal()
    planReplaceRequested = pyqtSignal()
    planAbortRequested = pyqtSignal()

    planInsertActivity = pyqtSignal(int)
    planDeleteActivities = pyqtSignal(list)

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
        self.actionAbout.triggered.connect(self.show_about_dialog)
        self.actionExit.triggered.connect(self.appExitRequested)
        self.actionNew_Plan.triggered.connect(self.new_plan_dialog)
        self.actionImport_Tasks.triggered.connect(self.import_tasks_dialog)
        self.actionExport_Tasklist.triggered.connect(
            lambda: self.export_tasks_dialog(True)
        )
        self.actionImport_Activities.triggered.connect(self.import_activities_dialog)
        self.actionExport_Plan.triggered.connect(
            lambda: self.export_activities_dialog(True)
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
        self.actionShow_Statistics.triggered.connect(self.show_stats_dialog)

        self.actionAdd_New_Activity.triggered.connect(
            lambda: self.planInsertActivity.emit(
                self._get_plan_insertion_index(True)
            )
        )
        self.actionInsert_New_Activity.triggered.connect(
            lambda: self.planInsertActivity.emit(
                self._get_plan_insertion_index(False)
            )
        )
        self.actionExport_Selected_Activities.triggered.connect(
            lambda: self.export_activities_dialog(False)
        )
        self.actionDelete_Selected_Activities.triggered.connect(
            lambda: self.planDeleteActivities.emit(
                self._get_selected_plan_indices()
            )
        )

        self.actionNew_Task.triggered.connect(self.tasklistNewTask)
        self.actionExport_Selected_Tasks.triggered.connect(
            lambda: self.export_tasks_dialog(False)
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
            lambda: self.planInsertActivity.emit(
                self._get_plan_insertion_index(True)
            )
        )

        # Other widgets
        self.tasklist_filter.returnPressed.connect(self.filter_tasklist)

        self.tray_icon.activated.connect(self.show)
        self.tray_icon.messageClicked.connect(self.show)

        self._tasklist_proxy.sourceModel().layoutChanged.connect(self.update_title)
        self.table_plan.model().layoutChanged.connect(self.update_title)

        self.table_tasklist.selectionModel().selectionChanged.connect(
            lambda: self.show_selection_count(self.table_tasklist.selectionModel())
        )
        self.table_plan.selectionModel().selectionChanged.connect(
            lambda: self.show_selection_count(self.table_plan.selectionModel())
        )

        self.table_tasklist.selectionModel().selectionChanged.connect(
            lambda: self._toggle_menu_enabled_on_selection(
                self.table_tasklist.selectionModel(),
                self.menuTask
            )
        )
        self.table_plan.selectionModel().selectionChanged.connect(
            lambda: self._toggle_menu_enabled_on_selection(
                self.table_plan.selectionModel(),
                self.menuActivity
            )
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
        QMessageBox.about(self, "About LibrePlan", text)

    def show_stats_dialog(self):
        self.stats_dialog = StatsDialog(self)
        self.stats_dialog.show()

    def import_tasks_dialog(self):
        path = QFileDialog.getOpenFileName(self, "Import Tasks")[0]

        if path:
            options = ImportDialog.get_import_options(self)
            if options:
                self.tasklistImportRequested.emit(path, options)

    def export_tasks_dialog(self, export_all):
        path = QFileDialog.getSaveFileName(self, "Export Tasks")[0]

        if path:
            indices = [] if export_all else self._get_selected_tasklist_indices()
            self.tasklistExportRequested.emit(path, indices)

    def new_plan_dialog(self):
        if self.table_plan.model().rowCount() != 0:
            discard = QMessageBox.warning(
                        self, "Discard Activities?",
                        "There are activities in the current plan.\n\nWould you like to discard them?",
                        QMessageBox.Ok | QMessageBox.Cancel
                    )

            if discard == QMessageBox.Ok:
                self.planNewRequested.emit()

    def import_activities_dialog(self):
        path = QFileDialog.getOpenFileName(self, "Import Activities")[0]

        if path:
            options = ImportDialog.get_import_options(self)
            if options:
                self.planImportRequested.emit(path, options)

    def export_activities_dialog(self, export_all):
        path = QFileDialog.getSaveFileName(self, "Export Activities")[0]

        if path:
            indices = [] if export_all else self._get_selected_plan_indices()
            self.planExportRequested.emit(path, indices)

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

    def activity_expired(self, current_activity):
        self.tabWidget.setCurrentIndex(0)
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

        self._tasklist_proxy = TasklistProxyModel(self)
        self._tasklist_proxy.setSourceModel(tasklist_model)

        self.table_tasklist.setModel(self._tasklist_proxy)

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

    def _get_plan_insertion_index(self, append):
        index = self._get_first_selected_plan_index()
        if index is None:
            return self.table_plan.model().rowCount()

        if append:
            index += 1

        return index

    def _get_first_selected_plan_index(self):
        selected_indices = self._get_selected_plan_indices()
        return selected_indices[0] if selected_indices else None

    def _get_selected_tasklist_indices(self):
        return sorted(
            [self._tasklist_proxy.mapToSource(index).row()
            for index in self.table_tasklist.selectionModel().selectedRows()]
        )

    def filter_tasklist(self):
        self._tasklist_proxy.setFilterRegularExpression(
            QRegularExpression(
                self.tasklist_filter.text(),
                QRegularExpression.CaseInsensitiveOption
                | QRegularExpression.UseUnicodePropertiesOption
            )
        )
        count = self._tasklist_proxy.rowCount()
        self.statusbar.showMessage(f"{count} tasks found")

    def show_selection_count(self, selection_model):
        count = len(selection_model.selectedRows())
        self.statusbar.showMessage(f"{count} selected")

    def update_title(self):
        activity_count = self.table_plan.model().rowCount() - 1
        task_count = self._tasklist_proxy.sourceModel().rowCount()

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

    def _show_context_menu(self, obj, menu, pos):
        gpos = obj.mapToGlobal(pos)
        menu.exec_(gpos)

    def _populate_header_context_menu(self, table_view, menu):
        if isinstance(table_view.model(), TasklistProxyModel):
            table_model = table_view.model().sourceModel()
        else:
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

    def _toggle_menu_enabled_on_selection(self, selection_model, menu):
        is_selected = len(selection_model.selectedRows()) > 0
        menu.setEnabled(is_selected)

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
