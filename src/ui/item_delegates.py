from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt, QDate, QTime, QPoint, QRect, QModelIndex
from PyQt5.QtWidgets import (
    QApplication,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionButton,

    QCheckBox,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QDateEdit,
    QTimeEdit
)

class GenericDelegate(QStyledItemDelegate):
    """Generic delegate for the editing of build-in and Qt datatypes (int, str, QDate, etc.)"""

    def __init__(self, parent, *args):
        QStyledItemDelegate.__init__(self, parent, *args)

    def createEditor(self, parent, option, index):
        """Returns the proper editor widget based on item datatype"""

        if isinstance(index.data(), int):
            spin_box = QSpinBox(parent)
            spin_box.setMaximum(999999)
            return spin_box

        if isinstance(index.data(), str):
            line_edit = QLineEdit(parent)
            return line_edit

        if isinstance(index.data(), QDate):
            date_edit = QDateEdit(parent)
            return date_edit

        if isinstance(index.data(), QTime):
            time_edit = QTimeEdit(parent)
            return time_edit

        return None

    def setEditorData(self, editor, index):
        if isinstance(editor, QSpinBox):
            editor.setValue(index.data())

        elif isinstance(editor, QLineEdit):
            editor.setText(index.data())

        elif isinstance(editor, QDateEdit):
            editor.setDate(index.data())

        elif isinstance(editor, QTimeEdit):
            editor.setTime(index.data())

class BoolDelegate(QStyledItemDelegate):
    """Clickable checkbox for boolean values."""

    def __init__(self, parent, *args):
        QStyledItemDelegate.__init__(self, parent, *args)

    def createEditor(self, parent, option, index):
        return None

    def getCheckBoxRect(self, check_box, option):
        check_box_rect = QApplication.style().subElementRect(QStyle.SE_CheckBoxIndicator, check_box, None)
        check_box_point = QPoint(
                            option.rect.x() +
                            (option.rect.width() -
                            check_box_rect.width()) / 2,

                            option.rect.y() +
                            (option.rect.height() -
                            check_box_rect.height()) / 2)

        return QRect(check_box_point, check_box_rect.size())

    def paint(self, painter, option, index):
        check_box = QStyleOptionButton()

        checked = index.data()
        is_editable = int(index.flags() & QtCore.Qt.ItemIsEditable) > 0

        check_box.state |= QStyle.State_On if checked else QStyle.State_Off
        check_box.state |= QStyle.State_Enabled if is_editable else QStyle.State_ReadOnly

        check_box.rect = self.getCheckBoxRect(check_box, option)

        QApplication.style().drawControl(QStyle.CE_CheckBox, check_box, painter)

    def editorEvent(self, event, model, option, index):
        if not int(index.flags() & QtCore.Qt.ItemIsEditable) > 0:
            return False

        if event.type() == QtCore.QEvent.MouseButtonRelease and event.button() == QtCore.Qt.LeftButton:
            self.setModelData(None, model, index)
            self.sizeHintChanged.emit(index)
            return True

        return False

    def setModelData(self, editor, model, index):
        value = not index.data()
        model.setData(index, value)

class DeadlineDelegate(QStyledItemDelegate):
    """Delegate for selecting a deadline.

    This prevents a user from setting a deadline that is earlier than
    the date the task was created.
    """

    def __init__(self, parent, *args):
        QStyledItemDelegate.__init__(self, parent, *args)
        self._model = parent

    def createEditor(self, parent, option, index):
        if isinstance(index.data(), QDate):
            date_edit = QDateEdit(parent)
            date_edit.setCalendarPopup(True)
            return date_edit
        return None

    def setEditorData(self, editor, index):
        from model.tasklist import Task
        if isinstance(editor, QDateEdit):
            date_created = self._model.mapToSource(index).siblingAtColumn(
                Task.COLUMN_INDICES["DATE_CREATED"]
            ).data()
            editor.setMinimumDate(date_created)
            editor.setDate(index.data())

class DeadlineTypeDelegate(QStyledItemDelegate):
    """Delegate for showing all deadline types in a combo box."""

    def __init__(self, parent, *args):
        QStyledItemDelegate.__init__(self, parent, *args)

    def createEditor(self, parent, option, index):
        from model.tasklist import DeadlineType
        if isinstance(index.data(), DeadlineType):
            combo_box = QComboBox(parent)
            for type in list(DeadlineType):
                combo_box.addItem(type.name)
            return combo_box
        return None

    def setEditorData(self, editor, index):
        from model.tasklist import DeadlineType
        if isinstance(index.data(), DeadlineType):
            editor.setCurrentText(index.data().name)

    def setModelData(self, editor, model, index):
        from model.tasklist import DeadlineType
        value = editor.currentText()
        model.setData(index, DeadlineType[value])

    def displayText(self, value, locale):
        from model.tasklist import DeadlineType
        if isinstance(value, DeadlineType):
            return value.name
        return str(value)

class PercentDelegate(QStyledItemDelegate):
    """Delegate for displaying float values as a percentage (i.e. 0.5 ->
    50%).
    """

    def __init__(self, parent, *args):
        QStyledItemDelegate.__init__(self, parent, *args)

    def displayText(self, value, locale):
        if isinstance(value, float):
            return f"{value * 100:.0f}%"
        return str(value)
