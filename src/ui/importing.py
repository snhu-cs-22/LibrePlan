from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog

from ui.forms.importing import Ui_ImportDialog
from model.importing import Importer, ReplaceOption

class ImportDialog(QDialog, Ui_ImportDialog):
    def __init__(self, table, path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)

        self.importer = Importer(table, path)

        for option in list(ReplaceOption):
            self.replace_options.addItem(option.name)

        self._connectSignals()

        self.show()

    def _connectSignals(self):
        self.replace_options.currentIndexChanged.connect(self.importer.set_replace_option)

    def accept(self):
        self.importer.import_items()
        QDialog.accept(self)
