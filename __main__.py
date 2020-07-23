import sys
import logging
import os
import datetime


from ui_qt.qt_log_streamer import QtHandler


if not os.path.exists("logs"):
    os.mkdir("logs")
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(name)s - %(levelname)s] - %(message)s",
    handlers=[
        QtHandler(),
        logging.FileHandler(
            os.path.join("logs", f"{datetime.datetime.now().strftime('%Y%b%d %H%M%S')}.log"),
            mode="a",
            delay=True,
        ),
    ],
)
logger = logging.getLogger(__name__)
logger.info("Starting IPSO Phen")

from ipapi import __init__


from PySide2.QtWidgets import QApplication

from ui_qt.app import IpsoMainForm


if __name__ == "__main__":
    """Launch IPSO Phen with Qt UI"""
    app = QApplication(sys.argv)
    IpsoMainForm().show()
    ret = app.exec_()
    logger.info("Closing IPSO Phen")
    sys.exit(ret)
