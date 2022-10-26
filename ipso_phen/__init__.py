import sys
import logging

version = "0.7.112.546"

import os

os.environ["QT_MAC_WANTS_LAYER"] = "1"


def cli():
    from ipso_phen.ipso_cli import run_cli

    sys.exit(run_cli())


try:
    from PySide2.QtWidgets import QApplication

    def launch_ui():
        from ipso_phen.ui.app import IpsoMainForm

        logger = logging.getLogger("entry point")
        logger.info("Starting UI")
        app = QApplication(sys.argv)
        IpsoMainForm().show()
        ret = app.exec_()
        logger.info(f"Closing IPSO Phen, ret = {ret}")
        sys.exit(ret)

except:
    logger = logging.getLogger("entry point")
    logger.info("No UI available")
    sys.exit(-1)
