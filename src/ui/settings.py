from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QDialogButtonBox

from model.config import Config
from ui.forms.settings import Ui_SettingsDialog

class SettingsDialog(QDialog, Ui_SettingsDialog):
    def __init__(self, config, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)
        self.apply_button = self.buttonBox.button(QDialogButtonBox.Apply)
        self.apply_button.setEnabled(False)

        self.config = config
        self.spinBoxBackupNum.setValue(
            self.config.get_setting("user.backup/number_of_backups", 50)
        )

        self._connectSignals()

    def _connectSignals(self):
        self.apply_button.clicked.connect(self.apply)
        self.spinBoxBackupNum.valueChanged.connect(
            lambda: self.apply_button.setEnabled(True)
        )

    def apply(self):
        self.apply_button.setEnabled(False)
        self.config.set_setting("user.backup/number_of_backups", self.spinBoxBackupNum.value())

    def accept(self):
        self.apply()
        return super().accept()
