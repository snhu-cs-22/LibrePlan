from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QCheckBox,
    QSpinBox,
)

from model.config import Config
from ui.forms.settings import Ui_SettingsDialog

class SettingsDialog(QDialog, Ui_SettingsDialog):
    def __init__(self, parent, config, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.setupUi(self)
        self.apply_button = self.buttonBox.button(QDialogButtonBox.Apply)
        self.apply_button.setEnabled(False)

        self.config = config

        self.settings = [
            ("user.backup/on_exit", True, self.checkBoxOnExit),
            ("user.backup/on_plan_complete", False, self.checkBoxOnPlanComplete),
            ("user.backup/number_of_backups", 50, self.spinBoxBackupNum),
        ]

        for (name, value, widget) in self.settings:
            if isinstance(widget, QCheckBox):
                widget.setChecked(self.config.get_setting(name, value))
                widget.toggled.connect(
                    lambda: self.apply_button.setEnabled(True)
                )
            elif isinstance(widget, QSpinBox):
                widget.setValue(self.config.get_setting(name, value))
                widget.valueChanged.connect(
                    lambda: self.apply_button.setEnabled(True)
                )

        self.apply_button.clicked.connect(self.apply)
        self.setModal(True)
        self.open()

    def apply(self):
        self.apply_button.setEnabled(False)
        for (name, _, widget) in self.settings:
            if isinstance(widget, QCheckBox):
                self.config.set_setting(name, widget.isChecked())
            elif isinstance(widget, QSpinBox):
                self.config.set_setting(name, widget.value())

    def accept(self):
        self.apply()
        return super().accept()
