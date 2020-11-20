import sys
import logging


from PySide2.QtWidgets import QApplication

from ipso_phen.ui.app import IpsoMainForm

logger = logging.getLogger(__name__)


if __name__ == "__main__":
    """Launch IPSO Phen with Qt UI"""
    app = QApplication(sys.argv)
    IpsoMainForm().show()
    ret = app.exec_()
    logger.info("Closing IPSO Phen, ret = {ret}")
    sys.exit(ret)
