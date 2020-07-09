import sys
import logging

from ipapi import __init__

logger = logging.getLogger(__name__)
logger.info("Starting IPSO Phen")

from PySide2.QtWidgets import QApplication

from ui_qt.app import IpsoMainForm


if __name__ == "__main__":
    """Launch IPSO Phen with Qt UI"""
    app = QApplication(sys.argv)
    IpsoMainForm().show()
    ret = app.exec_()
    logger.info("Closing IPSO Phen")
    sys.exit(ret)
