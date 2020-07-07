import sys

from PySide2.QtWidgets import QApplication

sys.path.append("./ipapi")


from ui_qt.app import IpsoMainForm


if __name__ == "__main__":
    """Launch IPSO Phen with Qt UI"""
    app = QApplication(sys.argv)
    IpsoMainForm().show()
    sys.exit(app.exec_())
