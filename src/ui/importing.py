from enum import Enum, auto

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog

from ui.forms.importing import Ui_ImportDialog

class ReplaceOption(Enum):
    IGNORE = 0
    REPLACE = auto()
    ADD = auto()

class ImportDialog(QDialog, Ui_ImportDialog):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.setupUi(self)

        self.options = {
            "replace_option": ReplaceOption(0)
        }

        for option in list(ReplaceOption):
            self.replace_options.addItem(option.name)

        self._connectSignals()

    @staticmethod
    def get_import_options(parent):
        dialog = ImportDialog(parent)
        if dialog.exec_():
            return dialog.options
        return None

    def _connectSignals(self):
        self.replace_options.currentIndexChanged.connect(self.set_replace_option)

    def set_replace_option(self, option):
        self.options["replace_option"] = ReplaceOption(option)

    def accept(self):
        QDialog.accept(self)
        return self.options
