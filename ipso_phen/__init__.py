import sys
import logging

version = "0.7.103.534"


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
        logger.info("Closing IPSO Phen, ret = {ret}")
        sys.exit(ret)


except:
    logger = logging.getLogger("entry point")
    logger.info("No UI available")
    sys.exit(-1)
