from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QDate, QTime
from PyQt5.QtWidgets import QStyledItemDelegate, QCheckBox, QSpinBox, QComboBox, QLineEdit, QDateEdit, QTimeEdit

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
