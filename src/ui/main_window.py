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
    QInputDialog,
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
from ui.settings import SettingsDialog
from ui.stats import StatsDialog

class MainWindow(QMainWindow, Ui_MainWindow):
    planNewRequested = pyqtSignal()
    planImportRequested = pyqtSignal(str, dict)
    planExportRequested = pyqtSignal(str, list)
    tasklistImportRequested = pyqtSignal(str, dict)
    tasklistExportRequested = pyqtSignal(str, list)

    planStartRequested = pyqtSignal(bool)
    planStartFromSelectedRequested = pyqtSignal(int, bool)
    planEndRequested = pyqtSignal(bool)
    planInterruptRequested = pyqtSignal(str)
    planReplaceRequested = pyqtSignal(str)
    planAbortRequested = pyqtSignal()

    planInsertActivity = pyqtSignal(int)
    planDeleteActivities = pyqtSignal(list)

    planCutActivities = pyqtSignal(list)
    planCopyActivities = pyqtSignal(list)
    planPasteActivities = pyqtSignal(int)

    tasklistNewTask = pyqtSignal()
    tasklistDeleteTasks = pyqtSignal(list)

    backupExportRequested = pyqtSignal(str)
    backupRestoreRequested = pyqtSignal(str)
    appExitRequested = pyqtSignal()

    def __init__(self, application, config, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.application = application
        self.config = config
        self.tray_icon = QSystemTrayIcon(self)

        self.setupUi(self)
        self.config.restore_state(self)
        self.config.restore_geometry(self)
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
        self.actionExport_Backup.triggered.connect(self.export_backup_dialog)
        self.actionRestore_Backup.triggered.connect(self.restore_backup_dialog)
        self.actionSettings.triggered.connect(self.show_settings_dialog)
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
            lambda: self._emit_plan_start_from_selected_signal(False)
        )
        self.actionStart_Plan_Preemptively.triggered.connect(
            lambda: self.planStartRequested.emit(True)
        )
        self.actionStart_Plan_from_Here_Preemptively.triggered.connect(
            lambda: self._emit_plan_start_from_selected_signal(True)
        )
        self.actionEnd.triggered.connect(
            lambda: self.planEndRequested.emit(False)
        )
        self.actionEnd_Preemptively.triggered.connect(
            lambda: self.planEndRequested.emit(True)
        )
        self.actionInterrupt.triggered.connect(self.plan_interrupt_dialog)
        self.actionReplace.triggered.connect(self.plan_replace_dialog)
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

        self.actionPlan_Cut_Selected_Activities.triggered.connect(
            lambda: self.planCutActivities.emit(
                self._get_selected_plan_indices()
            )
        )
        self.actionPlan_Copy_Selected_Activities.triggered.connect(
            lambda: self.planCopyActivities.emit(
                self._get_selected_plan_indices()
            )
        )
        self.actionPlan_Paste_Before.triggered.connect(
            lambda: self.planPasteActivities.emit(
                self._get_plan_insertion_index(False)
            )
        )
        self.actionPlan_Paste_After.triggered.connect(
            lambda: self.planPasteActivities.emit(
                self._get_plan_insertion_index(True)
            )
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
        self.pushButton_interrupt.clicked.connect(self.plan_interrupt_dialog)
        self.pushButton_abort.clicked.connect(self.planAbortRequested)

        self.pushButton_new_task.clicked.connect(self.tasklistNewTask)
        self.pushButton_add_activity.clicked.connect(
            lambda: self.planInsertActivity.emit(
                self._get_plan_insertion_index(True)
            )
        )

        # Other widgets
        self.tasklist_filter.returnPressed.connect(self.filter_tasklist)

        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.messageClicked.connect(self.show)

        self._tasklist_proxy.sourceModel().layoutChanged.connect(self.table_count_changed)
        self.table_plan.model().layoutChanged.connect(self.table_count_changed)

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
        self.application.clipboard().dataChanged.connect(
            self._enable_paste_actions
        )

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

    def show_settings_dialog(self):
        SettingsDialog(self, self.config)

    def show_stats_dialog(self):
        StatsDialog(self, self.application)

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

    def plan_interrupt_dialog(self):
        input_text, ok = QInputDialog().getText(
                    self,
                    "Interrupt activity...",
                    "Set name for interruption:"
                )

        if ok and input_text:
            self.planInterruptRequested.emit(input_text)

    def plan_replace_dialog(self):
        input_text, ok = QInputDialog().getText(
                    self,
                    "Replace activity...",
                    "Set name for replacement:"
                )

        if ok and input_text:
            self.planReplaceRequested.emit(input_text)

    def export_backup_dialog(self):
        path = QFileDialog.getSaveFileName(None, "Create Backup")[0]

        if path:
            self.backupExportRequested.emit(path)

    def restore_backup_dialog(self):
        path = QFileDialog.getOpenFileName(
            self,
            "Restore Backup",
            self.application.PATH_BACKUPS
        )[0]

        if path:
            dialog = QMessageBox.warning(
                self,
                "Restore from Backup?",
                "Do you want to restore from backup and restart? A backup of the current database will be made.",
                QMessageBox.Ok | QMessageBox.Cancel
            )

            if dialog == QMessageBox.Ok:
                self.backupRestoreRequested.emit(path)

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

    def tray_icon_activated(self, reason):
        if reason != QSystemTrayIcon.Context:
            self.show()

    def activity_started(self):
        self._toggle_plan_running(True)

    def activity_stopped(self):
        self._toggle_plan_running(False)
        self.table_count_changed()

    def _toggle_plan_running(self, enabled):
        # Start Buttons/Actions
        self.pushButton_start_now.setDisabled(enabled)

        self.actionStart_now.setDisabled(enabled)
        self.actionStart_Plan_from_Here_Now.setDisabled(enabled)
        self.actionStart_Plan_Preemptively.setDisabled(enabled)
        self.actionStart_Plan_from_Here_Preemptively.setDisabled(enabled)

        # Other Buttons/Actions
        self.pushButton_end.setEnabled(enabled)
        self.pushButton_interrupt.setEnabled(enabled)
        self.pushButton_abort.setEnabled(enabled)

        self.actionEnd.setEnabled(enabled)
        self.actionEnd_Preemptively.setEnabled(enabled)
        self.actionInterrupt.setEnabled(enabled)
        self.actionAbort.setEnabled(enabled)
        self.actionReplace.setEnabled(enabled)

    def _enable_paste_actions(self):
        self.actionPlan_Paste_Before.setEnabled(True)
        self.actionPlan_Paste_After.setEnabled(True)

    def activity_began(self, current_activity):
        self.tray_icon.showMessage(
            f"Activity \"{current_activity.name}\" has begun.",
            "Activity was preemptively started.",
        )

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
                self.config.get_setting(
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
            self.table_tasklist.setItemDelegateForColumn(i, col["delegate"](self._tasklist_proxy))

        self.table_tasklist.horizontalHeader().setSectionsMovable(True)
        self.table_tasklist.horizontalHeader().restoreState(
            bytes(
                self.config.get_setting(
                    "ui.tasklist/header_state",
                    self.table_tasklist.horizontalHeader().saveState()
                )
            )
        )
        self._populate_header_context_menu(self.table_tasklist, self.menuTasklist_Show_Hide_Columns)

        self.table_count_changed()

    def _get_selected_plan_indices(self):
        return sorted([index.row() for index in self.table_plan.selectionModel().selectedRows()])

    def _emit_plan_start_from_selected_signal(self, preemptive=False):
        self.planStartFromSelectedRequested.emit(
            self._get_first_selected_plan_index(),
            preemptive
        )

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

    def set_title(self, title):
        self.setWindowTitle(title)
        self.tray_icon.setToolTip(title)

    def table_count_changed(self):
        activity_count = self.table_plan.model().rowCount() - 1
        task_count = self._tasklist_proxy.sourceModel().rowCount()

        self.set_title(f"{activity_count} Activities, {task_count} Tasks - LibrePlan")

    def countdown_to_start(self, secs_to):
        self.set_title(f"{self._stringify_time_duration(secs_to)} Until Start - LibrePlan")

    def countdown_to_end(self, secs_to):
        self.set_title(f"{self._stringify_time_duration(secs_to)} Until End - LibrePlan")

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
        self.config.save_state(self)
        self.config.save_geometry(self)
        self.config.set_setting(
            "ui.plan/header_state",
            self.table_plan.horizontalHeader().saveState()
        )
        self.config.set_setting(
            "ui.tasklist/header_state",
            self.table_tasklist.horizontalHeader().saveState()
        )
