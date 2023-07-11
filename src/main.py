import sys

from application import Application

if __name__ == "__main__":
    app = Application(sys.argv)
    sys.exit(app.exec_())
