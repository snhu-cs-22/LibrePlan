from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QDate, QTime, QPoint, QRect
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

from tasklist import DeadlineType

class GenericDelegate(QStyledItemDelegate):
    """Generic delegate for the editing of build-in and Qt datatypes (int, str, QDate, etc.)"""

    def __init__(self, parent, *args):
        QStyledItemDelegate.__init__(self, parent, *args)

    def createEditor(self, parent, option, index):
        """Returns the proper editor widget based on item datatype"""

        if isinstance(index.data(), bool):
            checkbox = QCheckBox(parent)
            return checkbox

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
        if isinstance(editor, QCheckBox):
            editor.setChecked(index.data())

        if isinstance(editor, QSpinBox):
            editor.setValue(index.data())

        if isinstance(editor, QLineEdit):
            editor.setText(index.data())

        if isinstance(editor, QDateEdit):
            editor.setDate(index.data())

        if isinstance(editor, QTimeEdit):
            editor.setTime(index.data())

        return None

class BoolDelegate(QStyledItemDelegate):

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

class DeadlineTypeDelegate(QStyledItemDelegate):

    def __init__(self, parent, *args):
        QStyledItemDelegate.__init__(self, parent, *args)

    def createEditor(self, parent, option, index):
        if isinstance(index.data(), DeadlineType):
            combo_box = QComboBox(parent)
            for type in list(DeadlineType):
                combo_box.addItem(type.name)
            return combo_box
        return None

    def setEditorData(self, editor, index):
        if isinstance(index.data(), DeadlineType):
            editor.setCurrentText(index.data().name)

    def setModelData(self, editor, model, index):
        value = editor.currentText()
        model.setData(index, DeadlineType[value])

    def displayText(self, value, locale):
        if isinstance(value, DeadlineType):
            return value.name
        return str(value)

class PercentDelegate(QStyledItemDelegate):

    def __init__(self, parent, *args):
        QStyledItemDelegate.__init__(self, parent, *args)

    def displayText(self, value, locale):
        if isinstance(value, float):
            return f"{value * 100:.0f}%"
        return str(value)
