import sys
import logging

version = "0.7.102.532"
logger = logging.getLogger("entry point")

from ipso_phen.ipso_cli import run_cli

try:
    from PySide2.QtWidgets import QApplication
    from ipso_phen.ui.app import IpsoMainForm
except:
    logger.info("No UI available")
else:
    logger.info("Starting in UI mode")

    def launch_ui():
        """Launch IPSO Phen with Qt UI"""
        app = QApplication(sys.argv)
        IpsoMainForm().show()
        ret = app.exec_()
        logger.info("Closing IPSO Phen, ret = {ret}")
        sys.exit(ret)


def cli():
    sys.exit(run_cli())
