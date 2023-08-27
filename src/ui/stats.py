from PyQt5.QtChart import QChartView
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtWidgets import QApplication, QCompleter, QDialog

from model.stats import StatsModel
from ui.forms.stats import Ui_StatsDialog

class StatsDialog(QDialog, Ui_StatsDialog):
    def __init__(self, application, *args, **kwargs):
        super().__init__(*args, **kwargs)
        window_flags = (
            Qt.WindowTitleHint | Qt.WindowSystemMenuHint |
            # Explicitly ask for minimize, maximize, and close buttons
            # in case the OS doesn't get the hint
            Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint
        )
        self.setWindowFlags(window_flags)

        self.application = application
        self.model = StatsModel(self.application.database)

        self.setupUi(self)

        self._setupWidgets()
        self._setupCharts()
        self._plot_days_ago(0)

        self._connectSignals()

    # Qt Slots/Signals
    ################################################################################

    def _connectSignals(self):
        self.nameFilter.editingFinished.connect(
            lambda: self.model.set_filter(self.nameFilter.text())
        )
        self.nameFilter.editingFinished.connect(self.model.update_plots)

        self.radioButtonToday.clicked.connect(
            lambda: self._plot_days_ago(0)
        )
        self.radioButtonWeek.clicked.connect(
            lambda: self._plot_days_ago(6)
        )
        self.radioButtonMonth.clicked.connect(
            lambda: self._plot_days_ago(30)
        )
        self.radioButtonAll.clicked.connect(
            lambda: self._plot_all_time()
        )
        self.radioButtonCustom.toggled.connect(
            self.groupBoxDateRange.setEnabled
        )

        self.pushButtonSelect.clicked.connect(lambda: self._plot_days_ago(-1))

        self.dateEditFrom.dateChanged.connect(self._limit_date_range)
        self.dateEditTo.dateChanged.connect(self._limit_date_range)

        self.chart_view_pie.chart().series()[0].hovered.connect(self._pie_slice_hover)

    # UI functionality
    ################################################################################

    def _limit_date_range(self):
        self.dateEditTo.setMinimumDate(self.dateEditFrom.date())
        self.dateEditFrom.setMaximumDate(self.dateEditTo.date())

    def _pie_slice_hover(self, slice, hovered):
        slice.setLabelVisible(hovered)

    # Set up widgets/charts
    ################################################################################

    def _setupWidgets(self):
        completer = QCompleter(self.model.get_activity_names())
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        self.nameFilter.setCompleter(completer)

        self.dateEditTo.setMaximumDate(self.model.get_latest_log_date())
        self.dateEditFrom.setMinimumDate(self.model.get_earliest_log_date())

    def _setupCharts(self):
        self.chart_view_pie.setChart(self.model.get_pie_chart())
        self.chart_view_perf.setChart(self.model.get_perf_chart())
        self.chart_view_daily_avg.setChart(self.model.get_daily_chart())
        self.chart_view_circadian.setChart(self.model.get_circadian_chart())

    # Plotting dispatcher
    ################################################################################

    def _plot_all_time(self):
        self.dateEditFrom.setDate(self.dateEditFrom.minimumDate())
        self.dateEditTo.setDate(self.dateEditFrom.maximumDate())

        self.model.set_date_range(
            self.dateEditFrom.date(),
            self.dateEditTo.date()
        )
        self.model.update_plots()

    def _plot_days_ago(self, days):
        if days >= 0:
            self.dateEditTo.setMinimumDate(QDate.currentDate())
            self.dateEditFrom.setMaximumDate(QDate.currentDate().addDays(-days))
            self.dateEditTo.setDate(QDate.currentDate())
            self.dateEditFrom.setDate(QDate.currentDate().addDays(-days))

        self.model.set_date_range(
            self.dateEditFrom.date(),
            self.dateEditTo.date()
        )
        self.model.update_plots()
