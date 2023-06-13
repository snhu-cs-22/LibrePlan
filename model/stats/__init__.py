from PyQt5.QtChart import (
    QChart,

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
from PyQt5.QtWidgets import QApplication

from model.database import Database

class StatsModel:
    """Provides charts and other summarized statistical data from the activity log."""

    def __init__(self):
        self._filter_text = ""
        self._setupAxes()
        self._setupSeries()
        self._setupQueries()
        self._get_log_date_range()

    # Static values
    ################################################################################

    def get_activity_names(self):
        names = []
        Database.execute_query(self.query_activity_names)
        while self.query_activity_names.next():
            names.append(self.query_activity_names.value("name"))

        return names

    def get_earliest_log_date(self):
        return self.min_date

    def get_latest_log_date(self):
        return self.max_date

    ## Init charts
    ################################################################################

    def _setupAxes(self):
        self.perf_minute_axis = QValueAxis()
        self.perf_minute_axis.applyNiceNumbers()
        self.perf_minute_axis.setLabelFormat("%.0f min.")

        self.perf_percent_axis = QValueAxis()
        self.perf_percent_axis.applyNiceNumbers()
        self.perf_percent_axis.setLabelFormat("%.0f%%")

        self.perf_x_axis = QBarCategoryAxis()


        self.daily_date_axis = QDateTimeAxis()

        self.daily_minute_axis = QValueAxis()
        self.daily_minute_axis.applyNiceNumbers()
        self.daily_minute_axis.setLabelFormat("%.0f min.")

        self.daily_percent_axis = QValueAxis()
        self.daily_percent_axis.applyNiceNumbers()
        self.daily_percent_axis.setLabelFormat("%.0f%%")


        self.circadian_hour_axis = QValueAxis()
        self.circadian_hour_axis.setRange(0, 24)
        self.circadian_hour_axis.setLabelFormat("%d:00")

        self.circadian_percent_axis = QValueAxis()
        self.circadian_percent_axis.applyNiceNumbers()
        self.circadian_percent_axis.setLabelFormat("%.0f%%")

    def _setupSeries(self):
        self.pie_series = QPieSeries()

        self.perf_length_series = QBarSeries()
        self.perf_percent_series = QBarSeries()


        self.daily_actual_length_series = QLineSeries()
        self.daily_actual_length_series.setName("Actual Length")

        self.daily_length_series = QLineSeries()
        self.daily_length_series.setName("Planned Length")

        self.daily_percent_series = QLineSeries()
        self.daily_percent_series.setName("Percent")


        self.circadian_percent_series = QLineSeries()
        self.circadian_percent_series.setName("Percent")

    def get_pie_chart(self):
        chart = QChart()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.setAnimationDuration(500)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignRight)
        chart.setTitle("Proportion of Time Spent on Activities")

        chart.addSeries(self.pie_series)

        return chart

    def get_perf_chart(self):
        # Chart
        chart = QChart()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.setAnimationDuration(500)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)
        chart.setTitle("Activity Performance")

        chart.addSeries(self.perf_length_series)
        chart.addSeries(self.perf_percent_series)

        chart.addAxis(self.perf_x_axis, Qt.AlignBottom)
        chart.addAxis(self.perf_minute_axis, Qt.AlignLeft)
        chart.addAxis(self.perf_percent_axis, Qt.AlignRight)

        self.perf_length_series.attachAxis(self.perf_x_axis)
        self.perf_length_series.attachAxis(self.perf_minute_axis)
        self.perf_percent_series.attachAxis(self.perf_x_axis)
        self.perf_percent_series.attachAxis(self.perf_percent_axis)

        return chart

    def get_daily_chart(self):
        # Chart
        chart = QChart()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.setAnimationDuration(500)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)
        chart.setTitle("Daily Activity Performance")

        chart.addSeries(self.daily_length_series)
        chart.addSeries(self.daily_actual_length_series)
        chart.addSeries(self.daily_percent_series)

        chart.addAxis(self.daily_date_axis, Qt.AlignBottom)
        chart.addAxis(self.daily_minute_axis, Qt.AlignLeft)
        chart.addAxis(self.daily_percent_axis, Qt.AlignRight)

        self.daily_length_series.attachAxis(self.daily_date_axis)
        self.daily_length_series.attachAxis(self.daily_minute_axis)
        self.daily_actual_length_series.attachAxis(self.daily_date_axis)
        self.daily_actual_length_series.attachAxis(self.daily_minute_axis)
        self.daily_percent_series.attachAxis(self.daily_date_axis)
        self.daily_percent_series.attachAxis(self.daily_percent_axis)

        return chart

    def get_circadian_chart(self):
        # Chart
        chart = QChart()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.setAnimationDuration(500)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)
        chart.setTitle("Average Activity Performance Based on Time of Day")

        chart.addSeries(self.circadian_percent_series)

        chart.addAxis(self.circadian_hour_axis, Qt.AlignBottom)
        chart.addAxis(self.circadian_percent_axis, Qt.AlignLeft)

        self.circadian_percent_series.attachAxis(self.circadian_hour_axis)
        self.circadian_percent_series.attachAxis(self.circadian_percent_axis)

        return chart

    ## Plot data
    ################################################################################

    def _setupQueries(self):
        self.query_activity_names = Database.query_from_file("model/stats/get_activity_names.sql")
        self.query_log_date_range = Database.query_from_file("model/stats/get_log_date_range.sql")

        self.query_pie = Database.query_from_file("model/stats/get_pie_chart.sql")

        self.query_perf_axis_range = Database.query_from_file("model/stats/get_perf_axis_range.sql")
        self.query_perf = Database.query_from_file("model/stats/get_perf_chart.sql")

        self.query_daily_axis_range = Database.query_from_file("model/stats/get_daily_axis_range.sql")
        self.query_daily_avg = Database.query_from_file("model/stats/get_daily_avg.sql")

        self.query_circadian_axis_range = Database.query_from_file("model/stats/get_circadian_axis_range.sql")
        self.query_circadian = Database.query_from_file("model/stats/get_circadian_chart.sql")

    def set_filter(self, text):
        self._filter_text = text

    def set_date_range(self, date_from, date_to):
        self._date_from = date_from
        self._date_to = date_to

    def _get_log_date_range(self):
        Database.execute_query(self.query_log_date_range)
        self.query_log_date_range.first()
        if self.query_log_date_range.value(0) != "":
            self.min_date = QDate.fromString(
                self.query_log_date_range.value("min_date"),
                Database.DATE_FORMAT
            )
            self.max_date = QDate.fromString(
                self.query_log_date_range.value("max_date"),
                Database.DATE_FORMAT
            )

    def update_plots(self):
        self._plot_pie_chart()
        self._plot_activity_perf_chart()
        self._plot_activity_circadian_chart()
        self._plot_daily_avg_chart()

    def _plot_pie_chart(self):
        # Clear previous chart data
        self.pie_series.clear()

        # Populate the datasets in chart
        self.query_pie.bindValue(":name", f"%{self._filter_text}%")
        self.query_pie.bindValue(":date_from", self._date_from)
        self.query_pie.bindValue(":date_to", self._date_to)
        Database.execute_query(self.query_pie)

        while self.query_pie.next():
            total_actual_length = self.query_pie.value("total_actual_length")
            name = f'{self.query_pie.value("name")} ({total_actual_length} min.)'
            self.pie_series.append(name, total_actual_length)

    def _plot_activity_perf_chart(self):
        # Clear previous chart data
        self.perf_length_series.clear()
        self.perf_percent_series.clear()
        self.perf_x_axis.clear()

        # Set axis range
        self.query_perf_axis_range.bindValue(":name", f"%{self._filter_text}%")
        self.query_perf_axis_range.bindValue(":date_from", self._date_from)
        self.query_perf_axis_range.bindValue(":date_to", self._date_to)
        Database.execute_query(self.query_perf_axis_range)

        self.query_perf_axis_range.first()
        if self.query_perf_axis_range.value(0) != "":
            min_actual_length = self.query_perf_axis_range.value("min_actual_length") - 1
            max_actual_length = self.query_perf_axis_range.value("max_actual_length") + 1
            min_percent = self.query_perf_axis_range.value("min_percent") - 1
            max_percent = self.query_perf_axis_range.value("max_percent") + 1
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

        self.query_perf.bindValue(":name", f"%{self._filter_text}%")
        self.query_perf.bindValue(":date_from", self._date_from)
        self.query_perf.bindValue(":date_to", self._date_to)
        Database.execute_query(self.query_perf)

        while self.query_perf.next():
            name = self.query_perf.value("name")
            length = self.query_perf.value("avg_length")
            actual_length = self.query_perf.value("avg_actual_length")
            percent = self.query_perf.value("avg_percent")

            self.perf_x_axis.append(name)

            length_set.append(length)
            actual_length_set.append(actual_length)
            percent_set.append(percent)

        self.perf_length_series.append(length_set)
        self.perf_length_series.append(actual_length_set)
        self.perf_percent_series.append(percent_set)

    def _plot_daily_avg_chart(self):
        # Clear previous chart data
        self.daily_length_series.clear()
        self.daily_actual_length_series.clear()
        self.daily_percent_series.clear()

        # Set axis range
        self.query_daily_axis_range.bindValue(":name", f"%{self._filter_text}%")
        self.query_daily_axis_range.bindValue(":date_from", self._date_from)
        self.query_daily_axis_range.bindValue(":date_to", self._date_to)
        Database.execute_query(self.query_daily_axis_range)

        self.query_daily_axis_range.first()
        if self.query_daily_axis_range.value(0) != "":
            self.daily_date_axis.setRange(
                QDateTime(self._date_from),
                QDateTime(self._date_to)
            )

            min_minute = self.query_daily_axis_range.value("min_minute") - 1
            max_minute = self.query_daily_axis_range.value("max_minute") + 1
            min_percent = self.query_daily_axis_range.value("min_percent") - 1
            max_percent = self.query_daily_axis_range.value("max_percent") + 1

        else:
            min_minute = -1
            max_minute = 1
            min_percent = -1
            max_percent = 1

        self.daily_minute_axis.setRange(min_minute, max_minute)
        self.daily_percent_axis.setRange(min_percent, max_percent)

        # Populate the datasets in chart
        self.query_daily_avg.bindValue(":name", f"%{self._filter_text}%")
        self.query_daily_avg.bindValue(":date_from", self._date_from)
        self.query_daily_avg.bindValue(":date_to", self._date_to)
        Database.execute_query(self.query_daily_avg)

        while self.query_daily_avg.next():
            date = QDateTime(QDate.fromString(
                self.query_daily_avg.value("date"),
                Database.DATE_FORMAT
            ), QTime(0,0,0))
            actual_length = self.query_daily_avg.value("avg_actual_length")
            length = self.query_daily_avg.value("avg_length")
            percent = self.query_daily_avg.value("avg_percent")

            self.daily_actual_length_series.append(date.toMSecsSinceEpoch(), actual_length)
            self.daily_length_series.append(date.toMSecsSinceEpoch(), length)
            self.daily_percent_series.append(date.toMSecsSinceEpoch(), percent)

    def _plot_activity_circadian_chart(self):
        # Clear previous chart data
        self.circadian_percent_series.clear()

        # Set axis range
        self.query_circadian_axis_range.bindValue(":name", f"%{self._filter_text}%")
        self.query_circadian_axis_range.bindValue(":date_from", self._date_from)
        self.query_circadian_axis_range.bindValue(":date_to", self._date_to)
        Database.execute_query(self.query_circadian_axis_range)

        self.query_circadian_axis_range.first()
        if self.query_circadian_axis_range.value(0) != "":
            min_percent = self.query_circadian_axis_range.value("min_percent") - 1
            max_percent = self.query_circadian_axis_range.value("max_percent") + 1
        else:
            min_percent = 0
            max_percent = 0

        self.circadian_percent_axis.setRange(min_percent, max_percent)

        # Populate the datasets in chart
        self.query_circadian.bindValue(":name", f"%{self._filter_text}%")
        self.query_circadian.bindValue(":date_from", self._date_from)
        self.query_circadian.bindValue(":date_to", self._date_to)
        Database.execute_query(self.query_circadian)

        while self.query_circadian.next():
            start_hour = self.query_circadian.value("hour")
            percent = self.query_circadian.value("avg_percent")

            self.circadian_percent_series.append(start_hour, percent)
