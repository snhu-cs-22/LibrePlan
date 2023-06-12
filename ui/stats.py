from PyQt5.QtChart import (
    QChart,
    QChartView,

    QBarSeries,
    QBarSet,
    QLineSeries,
    QPieSeries,

    QBarCategoryAxis,
    QDateTimeAxis,
    QValueAxis
)
from PyQt5.QtCore import Qt, QDate, QTime, QDateTime
from PyQt5.QtSql import QSqlQuery
from PyQt5.QtWidgets import QApplication, QCompleter, QDialog

from database import Database
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

        self.setupUi(self)

        self._setupQueries()

        self._setupWidgets()

        self._setupPieChart()
        self._setupActivityPerfChart()
        self._setupDailyAvgChart()
        self._setupActivityCircadianChart()
        self._plot_days_ago(0)

        self._connectSignals()

    # Qt Slots/Signals
    ################################################################################

    def _connectSignals(self):
        self.nameFilter.editingFinished.connect(self.update_plots)

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

        self.pie_series.hovered.connect(self._pie_slice_hover)

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
        # Populate name filter autocomplete with names
        name_list = []
        Database.execute_query(self.query_activity_names)
        while self.query_activity_names.next():
            name_list.append(self.query_activity_names.value(0))
        completer = QCompleter(name_list)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        self.nameFilter.setCompleter(completer)

        # Set date limits to date edit widgets based on log data
        Database.execute_query(self.query_log_date_range)
        self.query_log_date_range.first()
        if self.query_log_date_range.value(0) != "":
            min_date = QDate.fromString(
                self.query_log_date_range.value(0),
                Database.DATE_FORMAT
            )
            max_date = QDate.fromString(
                self.query_log_date_range.value(1),
                Database.DATE_FORMAT
            )
            self.dateEditTo.setMaximumDate(QDate.currentDate())
            self.dateEditFrom.setMinimumDate(min_date)

    def _setupPieChart(self):
        chart = QChart()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.setAnimationDuration(500)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignRight)
        chart.setTitle("Proportion of Time Spent on Activities")

        self.pie_series = QPieSeries()

        chart.addSeries(self.pie_series)

        self.chart_view_pie.setChart(chart)

    def _setupActivityPerfChart(self):
        # Chart
        chart = QChart()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.setAnimationDuration(500)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)
        chart.setTitle("Activity Performance")

        # Series
        self.activity_length_series = QBarSeries()
        self.activity_percent_series = QBarSeries()

        chart.addSeries(self.activity_length_series)
        chart.addSeries(self.activity_percent_series)

        # Axes
        self.perf_x_axis = QBarCategoryAxis()

        self.perf_minute_axis = QValueAxis()
        self.perf_minute_axis.applyNiceNumbers()
        self.perf_minute_axis.setLabelFormat("%.0f min.")

        self.perf_percent_axis = QValueAxis()
        self.perf_percent_axis.applyNiceNumbers()
        self.perf_percent_axis.setLabelFormat("%.0f%%")

        chart.addAxis(self.perf_x_axis, Qt.AlignBottom)
        chart.addAxis(self.perf_minute_axis, Qt.AlignLeft)
        chart.addAxis(self.perf_percent_axis, Qt.AlignRight)

        self.activity_length_series.attachAxis(self.perf_x_axis)
        self.activity_length_series.attachAxis(self.perf_minute_axis)
        self.activity_percent_series.attachAxis(self.perf_x_axis)
        self.activity_percent_series.attachAxis(self.perf_percent_axis)

        self.chart_view_perf.setChart(chart)

    def _setupDailyAvgChart(self):
        # Chart
        chart = QChart()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.setAnimationDuration(500)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)
        chart.setTitle("Daily Activity Performance")

        # Series
        self.activity_daily_length = QLineSeries()
        self.activity_daily_length.setName("Planned Length")
        self.activity_daily_actual_length = QLineSeries()
        self.activity_daily_actual_length.setName("Actual Length")
        self.activity_daily_percent = QLineSeries()
        self.activity_daily_percent.setName("Percent")

        chart.addSeries(self.activity_daily_length)
        chart.addSeries(self.activity_daily_actual_length)
        chart.addSeries(self.activity_daily_percent)

        # Axes
        self.daily_date_axis = QDateTimeAxis()

        self.daily_minute_axis = QValueAxis()
        self.daily_minute_axis.applyNiceNumbers()
        self.daily_minute_axis.setLabelFormat("%.0f min.")

        self.daily_percent_axis = QValueAxis()
        self.daily_percent_axis.applyNiceNumbers()
        self.daily_percent_axis.setLabelFormat("%.0f%%")

        chart.addAxis(self.daily_date_axis, Qt.AlignBottom)
        chart.addAxis(self.daily_minute_axis, Qt.AlignLeft)
        chart.addAxis(self.daily_percent_axis, Qt.AlignRight)

        self.activity_daily_length.attachAxis(self.daily_date_axis)
        self.activity_daily_length.attachAxis(self.daily_minute_axis)
        self.activity_daily_actual_length.attachAxis(self.daily_date_axis)
        self.activity_daily_actual_length.attachAxis(self.daily_minute_axis)
        self.activity_daily_percent.attachAxis(self.daily_date_axis)
        self.activity_daily_percent.attachAxis(self.daily_percent_axis)

        self.chart_view_daily_avg.setChart(chart)

    def _setupActivityCircadianChart(self):
        # Chart
        chart = QChart()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.setAnimationDuration(500)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)
        chart.setTitle("Average Activity Performance Based on Time of Day")

        # Series
        self.activity_circadian_percent = QLineSeries()
        self.activity_circadian_percent.setName("Percent")

        chart.addSeries(self.activity_circadian_percent)

        # Axes
        self.circadian_hour_axis = QValueAxis()
        self.circadian_hour_axis.setRange(0, 24)
        self.circadian_hour_axis.setLabelFormat("%d:00")

        self.circadian_percent_axis = QValueAxis()
        self.circadian_percent_axis.applyNiceNumbers()
        self.circadian_percent_axis.setLabelFormat("%.0f%%")

        chart.addAxis(self.circadian_hour_axis, Qt.AlignBottom)
        chart.addAxis(self.circadian_percent_axis, Qt.AlignLeft)

        self.activity_circadian_percent.attachAxis(self.circadian_hour_axis)
        self.activity_circadian_percent.attachAxis(self.circadian_percent_axis)

        self.chart_view_circadian.setChart(chart)

    ## Plot data
    ################################################################################

    def _setupQueries(self):
        self.query_activity_names = QSqlQuery()
        self.query_activity_names.prepare(
            'SELECT "name" FROM "activities" ORDER BY "name"'
        )

        self.query_log_date_range = QSqlQuery()
        self.query_log_date_range.prepare(
            'SELECT MIN("date"), MAX("date") FROM "activity_log"'
        )

        self.query_pie = QSqlQuery()
        self.query_perf_axis_range = QSqlQuery()
        self.query_activity_performance = QSqlQuery()
        self.query_daily_axis_range = QSqlQuery()
        self.query_daily_avg = QSqlQuery()
        self.query_circadian_axis_range = QSqlQuery()
        self.query_circadian_performance = QSqlQuery()

    def _prepare_dynamic_queries(self):
        self.query_pie.prepare(
            f"""
            SELECT "name", SUM("actual_length")
            FROM "activity_log" AS l
                INNER JOIN "activities" AS a
                    ON a.id = l.activity_id
            WHERE "date" BETWEEN :date_from AND :date_to
                AND "actual_length" > 0
                AND "name" LIKE :name
            GROUP BY "name"
            ORDER BY SUM("actual_length") DESC
            """
        )

        self.query_perf_axis_range.prepare(
            f"""
            SELECT MIN("avg_actual_length"),
                    MAX("avg_actual_length"),
                    MIN("avg_percent"),
                    MAX("avg_percent")
            FROM (
                SELECT
                    AVG("actual_length") AS "avg_actual_length",
                    AVG("actual_length" * 100/CAST("length" AS REAL)) AS "avg_percent"
                FROM "activity_log" AS l
                    INNER JOIN "activities" AS a
                        ON a.id = l.activity_id
                WHERE "date" BETWEEN :date_from AND :date_to
                    AND "length" <> 0
                    AND "name" LIKE :name
                GROUP BY "name"
            )
            """
        )

        self.query_activity_performance.prepare(
            f"""
            SELECT "name",
                    AVG("length"),
                    AVG("actual_length"),
                    AVG("actual_length" * 100/CAST("length" AS REAL))
            FROM "activity_log" AS l
                INNER JOIN "activities" AS a
                    ON a.id = l.activity_id
            WHERE "date" BETWEEN :date_from AND :date_to
                AND "length" <> 0
                AND "name" LIKE :name
            GROUP BY "name"
            ORDER BY AVG("actual_length") DESC
            """
        )

        self.query_daily_axis_range.prepare(
            """
            SELECT MIN(MIN("avg_actual_length"), MIN("avg_length")),
                    MAX(MAX("avg_actual_length"), MAX("avg_length")),
                    MIN("avg_percent"),
                    MAX("avg_percent")
            FROM (
                SELECT
                    AVG("actual_length") AS "avg_actual_length",
                    AVG("length") AS "avg_length",
                    AVG("actual_length" * 100/CAST("length" AS REAL)) AS "avg_percent"
                FROM "activity_log" AS l
                    INNER JOIN "activities" AS a
                        ON a.id = l.activity_id
                WHERE "date" BETWEEN :date_from AND :date_to
                    AND "length" <> 0
                    AND "name" LIKE :name
                GROUP BY "date"
            )
            """
        )

        self.query_daily_avg.prepare(
            f"""
            SELECT "date",
                   AVG("actual_length"),
                   AVG("length"),
                   AVG("actual_length" * 100/CAST("length" AS REAL))
            FROM "activity_log" AS l
                INNER JOIN "activities" AS a
                    ON a.id = l.activity_id
            WHERE "date" BETWEEN :date_from AND :date_to
                AND "length" <> 0
                AND "name" LIKE :name
            GROUP BY "date"
            ORDER BY "date" ASC
            """
        )

        self.query_circadian_axis_range.prepare(
            f"""
            SELECT MIN("avg_percent"),
                    MAX("avg_percent")
            FROM (
                SELECT cast(strftime('%H', "start_time") AS INTEGER) AS "hour",
                       AVG("actual_length" * 100/CAST("length" AS REAL)) AS "avg_percent"
                FROM "activity_log" AS l
                    INNER JOIN "activities" AS a
                        ON a.id = l.activity_id
                WHERE "date" BETWEEN :date_from AND :date_to
                    AND "length" <> 0
                    AND "name" LIKE :name
                GROUP BY "hour"
            )
            """
        )

        self.query_circadian_performance.prepare(
            f"""
            SELECT cast(strftime('%H', "start_time") AS INTEGER) AS "hour",
                   AVG("actual_length" * 100/CAST("length" AS REAL)) AS "avg_percent"
            FROM "activity_log" AS l
                INNER JOIN "activities" AS a
                    ON a.id = l.activity_id
            WHERE "date" BETWEEN :date_from AND :date_to
                AND "length" <> 0
                AND "name" LIKE :name
            GROUP BY "hour"
            ORDER BY "hour" ASC
            """
        )

    def _plot_all_time(self):
        self.dateEditFrom.setDate(self.dateEditFrom.minimumDate())
        self.dateEditTo.setDate(self.dateEditFrom.maximumDate())

        self.update_plots()

    def _plot_days_ago(self, days):
        if days >= 0:
            self.dateEditTo.setDate(QDate.currentDate())
            self.dateEditFrom.setDate(QDate.currentDate().addDays(-days))

        self.update_plots()

    def update_plots(self):
        self._date_to = self.dateEditTo.date()
        self._date_from = self.dateEditFrom.date()

        self._prepare_dynamic_queries()

        self._plot_pie_chart()
        self._plot_activity_perf_chart()
        self._plot_activity_circadian_chart()
        self._plot_daily_avg_chart()

    def _plot_pie_chart(self):
        # Clear previous chart data
        self.pie_series.clear()

        # Populate sets to chart
        self.query_pie.bindValue(":name", f"%{self.nameFilter.text()}%")
        self.query_pie.bindValue(":date_from", self._date_from)
        self.query_pie.bindValue(":date_to", self._date_to)
        Database.execute_query(self.query_pie)

        while self.query_pie.next():
            total_actual_length = self.query_pie.value(1)
            name = f"{self.query_pie.value(0)} ({total_actual_length} min.)"
            self.pie_series.append(name, total_actual_length)

    def _plot_activity_perf_chart(self):
        # Clear previous chart data
        self.activity_length_series.clear()
        self.activity_percent_series.clear()
        self.perf_x_axis.clear()

        # Set axis range
        self.query_perf_axis_range.bindValue(":name", f"%{self.nameFilter.text()}%")
        self.query_perf_axis_range.bindValue(
            ":date_from",
            self._date_from.toString(Database.DATE_FORMAT)
        )
        self.query_perf_axis_range.bindValue(
            ":date_to",
            self._date_to.toString(Database.DATE_FORMAT)
        )
        Database.execute_query(self.query_perf_axis_range)

        self.query_perf_axis_range.first()
        if self.query_perf_axis_range.value(0) != "":
            min_actual_length = self.query_perf_axis_range.value(0) - 1
            max_actual_length = self.query_perf_axis_range.value(1) + 1
            min_percent = self.query_perf_axis_range.value(2) - 1
            max_percent = self.query_perf_axis_range.value(3) + 1
        else:
            min_actual_length = 0
            max_actual_length = 0
            min_percent = 0
            max_percent = 0

        self.perf_minute_axis.setRange(min_actual_length, max_actual_length)
        self.perf_percent_axis.setRange(min_percent, max_percent)

        # Create and append sets to chart
        length_set = QBarSet("Planned Length")
        actual_length_set = QBarSet("Actual Length")
        percent_set = QBarSet("Percent")

        self.query_activity_performance.bindValue(":name", f"%{self.nameFilter.text()}%")
        self.query_activity_performance.bindValue(":date_from", self._date_from)
        self.query_activity_performance.bindValue(":date_to", self._date_to)
        Database.execute_query(self.query_activity_performance)

        while self.query_activity_performance.next():
            name = self.query_activity_performance.value(0)
            length = self.query_activity_performance.value(1)
            actual_length = self.query_activity_performance.value(2)
            percent = self.query_activity_performance.value(3)

            self.perf_x_axis.append(name)

            length_set.append(length)
            actual_length_set.append(actual_length)
            percent_set.append(percent)

        self.activity_length_series.append(length_set)
        self.activity_length_series.append(actual_length_set)
        self.activity_percent_series.append(percent_set)

    def _plot_daily_avg_chart(self):
        # Clear previous chart data
        self.activity_daily_length.clear()
        self.activity_daily_actual_length.clear()
        self.activity_daily_percent.clear()

        # Set axis range
        self.query_daily_axis_range.bindValue(":name", f"%{self.nameFilter.text()}%")
        self.query_daily_axis_range.bindValue(
            ":date_from",
            self._date_from.toString(Database.DATE_FORMAT)
        )
        self.query_daily_axis_range.bindValue(
            ":date_to",
            self._date_to.toString(Database.DATE_FORMAT)
        )
        Database.execute_query(self.query_daily_axis_range)

        self.query_daily_axis_range.first()
        if self.query_daily_axis_range.value(0) != "":
            self.daily_date_axis.setRange(
                QDateTime(self._date_from),
                QDateTime(self._date_to)
            )

            min_minute = self.query_daily_axis_range.value(0) - 1
            max_minute = self.query_daily_axis_range.value(1) + 1
            min_percent = self.query_daily_axis_range.value(2) - 1
            max_percent = self.query_daily_axis_range.value(3) + 1

        else:
            min_minute = -1
            max_minute = 1
            min_percent = -1
            max_percent = 1

        self.daily_minute_axis.setRange(min_minute, max_minute)
        self.daily_percent_axis.setRange(min_percent, max_percent)

        # Populate sets to chart
        self.query_daily_avg.bindValue(":name", f"%{self.nameFilter.text()}%")
        self.query_daily_avg.bindValue(":date_from", self._date_from)
        self.query_daily_avg.bindValue(":date_to", self._date_to)
        Database.execute_query(self.query_daily_avg)

        while self.query_daily_avg.next():
            date = QDateTime(QDate.fromString(
                self.query_daily_avg.value(0),
                Database.DATE_FORMAT
            ), QTime(0,0,0))
            actual_length = self.query_daily_avg.value(1)
            length = self.query_daily_avg.value(2)
            percent = self.query_daily_avg.value(3)

            self.activity_daily_actual_length.append(date.toMSecsSinceEpoch(), actual_length)
            self.activity_daily_length.append(date.toMSecsSinceEpoch(), length)
            self.activity_daily_percent.append(date.toMSecsSinceEpoch(), percent)

    def _plot_activity_circadian_chart(self):
        # Clear previous chart data
        self.activity_circadian_percent.clear()

        # Set axis range
        self.query_circadian_axis_range.bindValue(":name", f"%{self.nameFilter.text()}%")
        self.query_circadian_axis_range.bindValue(
            ":date_from",
            self._date_from.toString(Database.DATE_FORMAT)
        )
        self.query_circadian_axis_range.bindValue(
            ":date_to",
            self._date_to.toString(Database.DATE_FORMAT)
        )
        Database.execute_query(self.query_circadian_axis_range)

        self.query_circadian_axis_range.first()
        if self.query_circadian_axis_range.value(0) != "":
            min_percent = self.query_circadian_axis_range.value(0) - 1
            max_percent = self.query_circadian_axis_range.value(1) + 1
        else:
            min_percent = 0
            max_percent = 0

        self.circadian_percent_axis.setRange(min_percent, max_percent)

        # Populate sets to chart
        self.query_circadian_performance.bindValue(":name", f"%{self.nameFilter.text()}%")
        self.query_circadian_performance.bindValue(":date_from", self._date_from)
        self.query_circadian_performance.bindValue(":date_to", self._date_to)
        Database.execute_query(self.query_circadian_performance)

        while self.query_circadian_performance.next():
            start_hour = self.query_circadian_performance.value(0)
            percent = self.query_circadian_performance.value(1)

            self.activity_circadian_percent.append(start_hour, percent)
