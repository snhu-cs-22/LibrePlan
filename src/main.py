import sys

from PyQt5.QtCore import QProcess

from application import Application

if __name__ == "__main__":
    app = Application(sys.argv)
    exit_code = app.exec_()

    if exit_code == Application.EXIT_CODE_RESTART:
        QProcess.startDetached(sys.executable, sys.argv)
        sys.exit(0)
    else:
        sys.exit(exit_code)
