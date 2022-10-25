import sys
from PySide2.QtWidgets import QAction, QApplication, QMainWindow
from PySide2.QtWidgets import QMenu
from ipso_phen.ui.qy_split import Ui_MainWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        tool_menu = QMenu()
        tool_menu.addSeparator()
        tool_menu.addAction(QAction("Default empty group", self))
        tool_menu.addAction(QAction("Default empty group", self))
        tool_menu.addAction(QAction("Default empty group", self))
        tool_menu.addAction(QAction("Default empty group", self))
        tool_menu.addSeparator()
        tool_menu.addAction(QAction("Default empty group", self))
        tool_menu.addAction(QAction("Default empty group", self))
        tool_menu.addAction(QAction("Default empty group", self))
        tool_menu.addSeparator()
        tool_menu.addAction(QAction("Default empty group", self))
        tool_menu.setToolTipsVisible(True)
        self.ui.toolButton.setMenu(tool_menu)
        self.ui.toolButton.clicked.connect(self.on_toolButton)

    def on_toolButton(self):
        self.ui.toolButton.showMenu()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())
