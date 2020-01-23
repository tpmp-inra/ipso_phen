import sys
from PyQt5.QtWidgets import QApplication
from ui_qt.main_form import IpsoMainForm

if __name__ == "__main__":
    """Launch IPSO Phen with Qt UI"""
    app = QApplication(sys.argv)
    IpsoMainForm().show()
    sys.exit(app.exec_())
