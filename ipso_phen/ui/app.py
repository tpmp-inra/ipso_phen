import gc
import glob
import json
import multiprocessing as mp
import os
import random
import string
import sys
import threading
import traceback
from collections import defaultdict
from datetime import datetime as dt
from timeit import default_timer as timer
import shutil
import subprocess
import logging
import webbrowser
from typing import Union, Any
import locale

import cv2
import numpy as np
import pandas as pd
import psutil
from unidecode import unidecode

from PySide2 import QtWidgets
from PySide2.QtCore import (
    QObject,
    QSettings,
    Qt,
    QPoint,
    QThreadPool,
    Signal,
)
from PySide2.QtGui import (
    QColor,
    QFont,
    QIcon,
    QPalette,
    QPixmap,
    QShowEvent,
    QTextCursor,
)
from PySide2.QtWidgets import (
    QAction,
    QActionGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSlider,
    QSpinBox,
    QSplashScreen,
    QStyleFactory,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QToolButton,
    QToolTip,
    QVBoxLayout,
    QWidget,
    QListWidgetItem,
)


class Signaller(QObject):
    signal = Signal(str)


class MemoryFilter(logging.Filter):

    last_process_mem = 0

    def filter(self, record):
        process: psutil.Process = psutil.Process(os.getpid())
        pmp = process.memory_percent()
        sign = (
            "+"
            if pmp > self.last_process_mem
            else "-"
            if pmp < self.last_process_mem
            else "="
        )
        record.mem_data = f"µ{sign} {pmp:02.2f}%"
        self.last_process_mem = pmp
        return True


class QtHandler(logging.Handler):
    def __init__(self, slot_fct=None, *args, **kwargs):
        super(QtHandler, self).__init__(*args, **kwargs)
        self.signaller = Signaller()
        self.set_slot_func(slot_fct)

    def set_slot_func(self, slot_fct):
        if slot_fct is not None:
            self.signaller.signal.connect(slot_fct)

    def emit(self, record):
        record = self.format(record)
        if record:
            self.signaller.signal.emit(record)


g_qt_log_handler = QtHandler()
g_qt_log_handler.addFilter(MemoryFilter())

from ipso_phen.ipapi.tools.folders import ipso_folders

log_file_handler = logging.FileHandler(
    os.path.join(
        ipso_folders.get_path("logs", force_creation=True),
        f"ipso_phen_{dt.now().strftime('%Y_%m_%d')}.log",
    ),
    mode="a",
    delay=True,
)
log_file_handler.addFilter(MemoryFilter())


logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(mem_data)s - %(name)s - %(levelname)s] - %(message)s",
    handlers=[
        g_qt_log_handler,
        log_file_handler,
    ],
)

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))
logger.info("")
logger.info("______________________Starting session________________________________")
logger.info("")


from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
from ipso_phen.ipapi.base.ipt_abstract import IptBase, IptParamHolder
from ipso_phen.ipapi.base.ipt_abstract_analyzer import IptBaseAnalyzer
from ipso_phen.ipapi.base.ipt_functional import call_ipt_code
from ipso_phen.ipapi.base.ipt_holder import IptHolder, WIP_CASE
from ipso_phen.ipapi.base.ipt_loose_pipeline import LoosePipeline, GroupNode, ModuleNode
import ipso_phen.ipapi.base.ip_common as ipc
from ipso_phen.ipapi.tools import error_holder as eh

from ipso_phen.ipapi.class_pipelines.ip_factory import ipo_factory

from ipso_phen.ipapi.tools.regions import RectangleRegion
from ipso_phen.ipapi.tools.comand_line_wrapper import ArgWrapper
from ipso_phen.ipapi.tools.common_functions import (
    force_directories,
    format_time,
    make_safe_name,
    natural_keys,
    open_file,
)
import ipso_phen.ipapi.database.db_initializer as dbi
import ipso_phen.ipapi.database.db_factory as dbf
import ipso_phen.ipapi.database.base as dbb
from ipso_phen.ipapi.base.pipeline_processor import PipelineProcessor

from ipso_phen.ui import ui_consts
from ipso_phen.ui.about import Ui_about_dialog
from ipso_phen.ui.folder_selector import Ui_folder_selector
from ipso_phen.ui.new_tool import Ui_dlg_new_tool
from ipso_phen.ui.qt_mvc import (
    QMouseGraphicsView,
    build_widgets,
    QPandasModel,
    QPandasColumnsModel,
    QImageDatabaseModel,
    PipelineModel,
    QColorDelegate,
    QImageDrawerDelegate,
    PipelineDelegate,
)
from ipso_phen.ui.q_thread_handlers import IpsoCsvBuilder, IpsoMassRunner, IpsoRunnable
from ipso_phen.ui.main import Ui_MainWindow
from ipso_phen.ui.qt_custom_widgets import QLogger
from ipso_phen import version

_DATE_FORMAT = "%Y/%m/%d"
_TIME_FORMAT = "%H:%M:%S"

_TAB_TOOLS = "tab_tools"
_TAB_PIPELINE_V2 = "tb_pipeline_v2"

_PRAGMA_NAME = "IPSO Phen"
_PRAGMA_FULL_NAME = f"{_PRAGMA_NAME} - v{version}"
_PIPELINE_FILE_FILTER = f"""{_PRAGMA_NAME} All available ( *.json)
;;JSON compatible pipeline (*.json)"""


def excepthook(excType, excValue, tracebackobj):
    """
    Global function to catch unhandled exceptions.

    @param excType exception type
    @param excValue exception value
    @param tracebackobj traceback object
    """
    logger.error(
        "".join(
            ["Exception caught outside try block\n"]
            + traceback.format_exception(excType, excValue, sys.last_traceback)
        )
    )


sys.excepthook = excepthook


def log_method_execution_time(f):
    """Decorator: prints execution time
    Arguments:
        f {function} -- function to decorate
    Returns:
        function -- created function
    """

    def time_wrapper(*args, **kwargs):
        before = timer()
        x = f(*args, **kwargs)
        after = timer()
        logger.debug(f"Method {f.__name__} took {format_time(after - before)}")
        return x

    return time_wrapper


class AboutDialog(Ui_about_dialog):
    def set_version(self):
        self.lb_version.setText(f"Version: {version}")

    def set_copyright(self):
        self.lbl_copyright.setText("Unpublished work (c) 2018-2020 INRA.")

    def set_authors(self):
        self.lbl_authors.setText("Authors: Felicià Antoni Maviane Macia")

    def set_used_packages(self):
        self.txt_brw_used_packages.clear()
        with open(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "licenses.html",
            ),
            "r",
            encoding=locale.getdefaultlocale()[1],
        ) as licenses_:
            self.txt_brw_used_packages.insertHtml(licenses_.read())
            self.txt_brw_used_packages.verticalScrollBar().setValue(
                self.txt_brw_used_packages.verticalScrollBar().minimum()
            )
        self.txt_brw_used_packages.moveCursor(QTextCursor.Start)


class NewToolDialog(QDialog):

    folder_path = "./ipso_phen/ipapi/ipt"

    def __init__(self, parent=None, flags=0):
        super().__init__(parent)

        self.ui = Ui_dlg_new_tool()
        self.ui.setupUi(self)
        self.init_form()

    def init_form(self):
        self.set_groups()

        # Set default tool name
        self.ui.le_tool_name.textChanged.connect(self.on_tool_name_changed)
        self.ui.le_tool_name.setText("My new tool")

        # Set Default author
        self.ui.le_package_name.setText("Me")

        # Set description
        self.ui.te_description.clear()
        self.ui.te_description.insertHtml(
            "Write your tool's description here.\n it will be used to generate documentation files"
        )

        # Connect buttons
        self.ui.bt_save.clicked.connect(self.build_file)
        self.ui.bt_cancel.clicked.connect(self.cancel_tool)

    def set_groups(self):
        self.check_boxes = {}

        grp_layout = QVBoxLayout()
        for k, v in ipc.tool_family_hints.items():
            if k in ipc.tool_groups_pipeline:
                cb = QCheckBox(k)
                cb.setToolTip(v)
            else:
                continue
            self.check_boxes[k] = cb
            grp_layout.addWidget(cb)
        self.ui.gb_pipeline_tool_groups.setLayout(grp_layout)

        grp_layout = QVBoxLayout()
        for k, v in ipc.tool_family_hints.items():
            if (k in ipc.tool_groups_pipeline) or (k == "Unknown"):
                continue
            else:
                cb = QCheckBox(k)
                cb.setToolTip(v)
            self.check_boxes[k] = cb
            grp_layout.addWidget(cb)
        self.ui.gb_no_pipeline_tool_groups.setLayout(grp_layout)

    def on_tool_name_changed(self):
        # Get file name
        base_name = (
            "ipt_"
            + make_safe_name(unidecode(self.ui.le_tool_name.text()))
            .replace(" ", "_")
            .replace("(", "")
            .replace(")", "")
            .lower()
        )
        file_name = base_name + ".py"
        self.update_save_state(file_name)

        # Update file name
        self.ui.le_file_name.setText(file_name)
        # Update class name
        self.ui.le_class_name.setText(
            "".join(x.capitalize() for x in base_name.split("_"))
        )

    def update_save_state(self, target_file_path: str):
        # Update icon
        if os.path.isfile(os.path.join(self.folder_path, target_file_path)):
            self.ui.bt_save.setEnabled(False)
            self.ui.lbl_file_exists.setPixmap(
                QPixmap(
                    os.path.join(
                        os.path.dirname(os.path.abspath(__file__)),
                        "resources",
                        "Error.png",
                    )
                )
            )
        else:
            self.ui.bt_save.setEnabled(True)
            self.ui.lbl_file_exists.setPixmap(
                QPixmap(
                    os.path.join(
                        os.path.dirname(os.path.abspath(__file__)),
                        "resources",
                        "OK.png",
                    )
                )
            )

    def build_file(self):
        def add_tab(sc: str) -> str:
            return sc + "    "

        def remove_tab(sc: str) -> str:
            return sc[4:]

        file_path = os.path.join(self.folder_path, self.ui.le_file_name.text())
        with open(file_path, "w", encoding="utf8") as f:
            spaces = ""

            # Imports
            if (
                self.check_boxes[ipc.ToolFamily.FEATURE_EXTRACTION].isChecked()
                or self.check_boxes[ipc.ToolFamily.IMAGE_GENERATOR].isChecked()
            ):
                f.write(
                    f"{spaces}from ipso_phen.ipapi.base.ipt_abstract_analyzer import IptBaseAnalyzer\n"
                )
                inh_class_name_ = "IptBaseAnalyzer"
            else:
                f.write(
                    f"{spaces}from ipso_phen.ipapi.base.ipt_abstract import IptBase\n"
                )
                inh_class_name_ = "IptBase"
            f.write("\n\n")

            f.write("import os\n")
            f.write("import logging\n")
            f.write(
                "logger = logging.getLogger(os.path.splitext(__name__)[-1].replace('.', ''))\n\n"
            )

            # Class
            f.write(f"{spaces}class {self.ui.le_class_name.text()}({inh_class_name_}):\n")
            f.write("\n")

            # Build params
            spaces = add_tab("")
            f.write(f"{spaces}def build_params(self):\n")
            spaces = add_tab(spaces)
            f.write(f"{spaces}self.add_enabled_checkbox()\n")
            if self.ui.rb_rt_widget.isChecked():
                f.write(f"{spaces}self.add_checkbox(\n")
                spaces = add_tab(spaces)
                f.write(f'{spaces}name="is_real_time",\n')
                f.write(f'{spaces}desc="Execute in real time",\n')
                f.write(f"{spaces}default_value=0,\n")
                f.write(
                    f'{spaces}hint="If true, tool image will be processed when widget is modified"\n'
                )
                spaces = remove_tab(spaces)
                f.write(f"{spaces})\n")
            if self.check_boxes[ipc.ToolFamily.IMAGE_GENERATOR].isChecked():
                f.write(
                    f'{spaces}self.add_checkbox(name="save_image", desc="Save generated image", default_value=0)\n'
                )
                f.write(
                    f'{spaces}self.add_text_input(name="img_name", desc="Name in csv", default_value="img")\n'
                )
                f.write(f"{spaces}self.add_file_naming()\n")
                f.write("\n")
            f.write("\n")

            # Process image
            spaces = add_tab("")
            f.write(f"{spaces}def process_wrapper(self, **kwargs):\n")
            spaces = add_tab(spaces)
            f.write(f"{spaces}wrapper = self.init_wrapper(**kwargs)\n")
            f.write(f"{spaces}if wrapper is None:\n")
            f.write(f"{spaces}    return False\n")
            f.write("\n")
            f.write(f"{spaces}res = False\n")
            f.write(f"{spaces}try:\n")
            spaces = add_tab(spaces)
            f.write(f"{spaces}if self.get_value_of('enabled') == 1:\n")
            spaces = add_tab(spaces)
            f.write(f"{spaces}img = wrapper.current_image\n")
            if self.ui.chk_mask_required.isChecked():
                f.write(f"{spaces}mask = self.get_mask()\n")
                f.write(f"{spaces}if mask is None:\n")
                f.write(
                    f"""{spaces}    logger.error(
                        'Failure {self.ui.le_tool_name.text()}: mask must be initialized')\n"""
                )
                f.write(f"{spaces}    return\n")
            f.write("\n")
            f.write(f"{spaces}# Write your code here\n")
            f.write(f"{spaces}wrapper.store_image(img, 'current_image')\n")
            f.write(f"{spaces}res = True\n")
            spaces = remove_tab(spaces)
            f.write(f"{spaces}else:\n")
            f.write(
                f"{spaces}    wrapper.store_image(wrapper.current_image, 'current_image')\n"
            )
            f.write(f"{spaces}    res = True\n")
            spaces = remove_tab(spaces)
            f.write(f"{spaces}except Exception as e:\n")
            f.write(f"{spaces}    res = False\n")
            f.write(
                f"{spaces}"
                + "    logger.error("
                + "f"
                + f'"{self.ui.le_tool_name.text()} FAILED'
                + ', exception: {repr(e)}")\n'
            )
            f.write(f"{spaces}else:\n")
            f.write(f"{spaces}    pass\n")
            f.write(f"{spaces}finally:\n")
            f.write(f"{spaces}    return res\n")
            spaces = remove_tab(spaces)
            f.write("\n")

            # Properties
            spaces = add_tab("")
            f.write(f"{spaces}@property\n")
            f.write(f"{spaces}def name(self):\n")
            f.write(f"{spaces}    return '{self.ui.le_tool_name.text()}'\n")
            f.write("\n")

            f.write(f"{spaces}@property\n")
            f.write(f"{spaces}def package(self):\n")
            f.write(f"{spaces}    return '{self.ui.le_package_name.text()}'\n")
            f.write("\n")

            f.write(f"{spaces}@property\n")
            f.write(f"{spaces}def is_wip(self):\n")
            f.write(f"{spaces}    return True\n")
            f.write("\n")

            f.write(f"{spaces}@property\n")
            f.write(f"{spaces}def real_time(self):\n")
            if self.ui.rb_rt_yes.isChecked():
                f.write(f"{spaces}    return True\n")
            elif self.ui.rb_rt_no.isChecked():
                f.write(f"{spaces}    return False\n")
            elif self.ui.rb_rt_widget.isChecked():
                f.write(f"{spaces}    return self.get_value_of('is_real_time') == 1\n")
            elif self.ui.rb_rt_property.isChecked():
                f.write(f"{spaces}    return False is False else True\n")
            else:
                f.write(f"{spaces}    return False\n")
            f.write("\n")

            f.write(f"{spaces}@property\n")
            f.write(f"{spaces}def result_name(self):\n")
            if self.ui.rb_output_image.isChecked():
                f.write(f"{spaces}    return 'image'\n")
            elif self.ui.rb_output_mask.isChecked():
                f.write(f"{spaces}    return 'mask'\n")
            elif self.ui.rb_output_data.isChecked():
                f.write(f"{spaces}    'dictionary'\n")
            elif self.ui.rb_output_none.isChecked():
                f.write(f"{spaces}    return 'None'\n")
            else:
                f.write(f"{spaces}    return 'None'\n")
            f.write("\n")

            f.write(f"{spaces}@property\n")
            f.write(f"{spaces}def output_kind(self):\n")
            if self.ui.rb_output_image.isChecked():
                f.write(f"{spaces}    return 'image'\n")
            elif self.ui.rb_output_mask.isChecked():
                f.write(f"{spaces}    return 'mask'\n")
            elif self.ui.rb_output_data.isChecked():
                f.write(f"{spaces}    'dictionary'\n")
            elif self.ui.rb_output_none.isChecked():
                f.write(f"{spaces}    return 'None'\n")
            else:
                f.write(f"{spaces}    return 'None'\n")
            f.write("\n")

            f.write(f"{spaces}@property\n")
            f.write(f"{spaces}def use_case(self):\n")
            use_cases_ = ", ".join(
                [
                    f"'{k}'"
                    for k, _ in ipc.tool_family_hints.items()
                    if k in self.check_boxes and self.check_boxes[k].isChecked()
                ]
            )
            f.write(f"{spaces}    return [{use_cases_}]\n")
            f.write("\n")

            f.write(f"{spaces}@property\n")
            f.write(f"{spaces}def description(self):\n")
            desc = (
                self.ui.te_description.toPlainText().replace("'", " ").replace('"', " ")
            )
            f.write(f"{spaces}    return ''''{desc}'''\n")

        subprocess.run(args=("black", file_path))

        self.update_save_state(self.ui.le_file_name.text())

    def cancel_tool(self):
        self.close()


class ShowTextDialog(QDialog):
    def __init__(
        self,
        parent=None,
        title: str = "",
        text: str = "",
        use_html: bool = False,
        pt: QPoint = QPoint(0, 0),
    ):
        super().__init__(parent)

        self.setWindowTitle(title)

        txt_browser = QTextBrowser()
        if use_html:
            txt_browser.insertHtml(text.replace("\n", "<br>"))
        else:
            txt_browser.insertPlainText(text)

        layout = QVBoxLayout()
        layout.addWidget(txt_browser)
        self.setLayout(layout)

        self.setGeometry(pt.x(), pt.y(), 500, 400)

        self.setModal(True)
        self.setWindowModality(Qt.ApplicationModal)


class FrmSelectFolder(QDialog):
    def __init__(self, parent=None, flags=0):
        super().__init__(parent)

        self.ui = Ui_folder_selector()
        self.ui.setupUi(self)

        # Init
        self._db_name_changed = False

        # Select folder
        self.ui.bt_select_folder.setIcon(QIcon(":/common/resources/folder_blue.png"))
        self.ui.bt_select_folder.clicked.connect(self.on_folder_selected)
        # DBMS
        if ui_consts.ENABLE_POSTGRES:
            self.ui.cb_dbms.addItem("Postgress - Only if server is available")
        self.ui.cb_dbms.currentIndexChanged.connect(self.on_cb_dbms_index_changed)
        # Database name
        self.ui.edt_db_name.textEdited.connect(self.on_db_name_changed)
        # Dialog buttons
        self.ui.btn_box.accepted.connect(self.accept)
        self.ui.btn_box.rejected.connect(self.reject)

        self.ui.edt_db_name.setEnabled(False)

        # Finalize
        self.setModal(True)
        self.setWindowModality(Qt.ApplicationModal)

    def show_modal(self, default_path: str = "") -> int:
        if not default_path:
            default_path = os.path.join(os.path.expanduser("~"), "Documents")
        self.folder_path = default_path

        return self.exec_()

    def on_cb_dbms_index_changed(self, idx):
        self.ui.edt_db_name.setEnabled(idx != 0)
        self.db_qualified_name = self.folder_path

    def on_db_name_changed(self, text):
        self._db_name_changed = True
        self.db_qualified_name = text

    def on_folder_selected(self):
        self.folder_path = str(
            QFileDialog.getExistingDirectory(
                parent=self,
                caption="Select folder containing images",
                dir=self.folder_path,
            )
        )

    def accept(self) -> None:
        super(FrmSelectFolder, self).accept()

    def reject(self) -> None:
        super(FrmSelectFolder, self).reject()

    @property
    def folder_path(self):
        if os.path.isdir(self.ui.edt_fld_name.text()):
            return self.ui.edt_fld_name.text()
        else:
            return os.path.join(os.path.expanduser("~"), "Documents")

    @folder_path.setter
    def folder_path(self, value):
        self.ui.edt_fld_name.setText(value)
        if self.ui.edt_db_name.isEnabled():
            if not self._db_name_changed:
                self.db_qualified_name = self.folder_path
        else:
            self.db_qualified_name = ""

    @property
    def db_qualified_name(self):
        return self.ui.edt_db_name.text()

    @property
    def dbms(self):
        ci = self.ui.cb_dbms.currentIndex()
        if ci == 0:
            return "none"
        elif ci == 1:
            return "sqlite"
        elif ci == 2 and ui_consts.ENABLE_POSTGRES:
            return "psql"
        else:
            return "unknown dbms"

    @db_qualified_name.setter
    def db_qualified_name(self, value):
        if not self._db_name_changed:
            if self.dbms == "none":
                self.ui.edt_db_name.setText("NA")
                return
            elif self.dbms == "sqlite":
                value = make_safe_name(value)
            elif self.dbms == "psql":
                value = os.path.basename(os.path.normpath(value))
        val = "".join(
            c if c in string.ascii_letters or c in string.digits else "_" for c in value
        )
        if val != value:
            QToolTip.showText(
                self.ui.edt_db_name.mapToGlobal(self.ui.edt_db_name.rect().center()),
                "Only letters numbers and underscores are allowed",
            )
        self.ui.edt_db_name.setText(val)


class IpsoMainForm(QtWidgets.QMainWindow):
    @log_method_execution_time
    def __init__(self):
        super(IpsoMainForm, self).__init__()

        # Start splash screen
        if ui_consts.DISABLE_SPLASH_SCREEN:
            splash_pic_ = QPixmap(
                os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    "resources",
                    "splash_600px.png",
                )
            )
            self._splash = QSplashScreen(self, splash_pic_, Qt.WindowStaysOnTopHint)
            self._pg_splash = QProgressBar(self._splash)
            self._pg_splash.setMaximum(100)
            self._pg_splash.setGeometry(
                10, splash_pic_.height() - 20, splash_pic_.width() - 20, 18
            )
            self._lbl_splash = QLabel(self._splash)
            self._lbl_splash.setText(f"{_PRAGMA_FULL_NAME}")
            self._lbl_splash.setFont(QFont("Times", 24, QFont.Bold))
            self._lbl_splash.setGeometry(
                splash_pic_.width() - 440,
                splash_pic_.height() - 150,
                splash_pic_.width() - 20,
                80,
            )
            self._lbl_splash_text = QLabel(self._splash)
            self._lbl_splash_text.setText("Splashing the screen")
            self._lbl_splash_text.setFont(QFont("Times", 12))
            self._lbl_splash_text.setGeometry(
                splash_pic_.width() - 440,
                splash_pic_.height() - 120,
                splash_pic_.width() - 20,
                80,
            )
            self._splash.show()
        else:
            self._splash = None

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.lv_log = QLogger(self.ui.dockWidgetContents)
        self.lv_log.setObjectName("lv_log")
        self.lv_log.log_received.connect(self.on_log_received)
        g_qt_log_handler.set_slot_func(self.lv_log.append_text)

        logger.info("Starting IPSO Phen")

        self.ui.horizontalLayout_12.addWidget(self.lv_log)

        self._initializing = True
        self._working = False
        self._updating_saved_image_lists = False
        self._process_in_progress = False
        self._current_database: dbb.DbWrapper = None
        self._current_tool = None
        self._file_name = ""
        self.multithread = True
        self.use_pipeline_cache = True
        self._selected_output_image_luid = None

        self.last_pipeline_path = ""

        self._options = ArgWrapper(
            dst_path=ipso_folders.get_path("image_output"),
            store_images=True,
            write_images="none",
            write_result_text=False,
            overwrite=False,
            seed_output=False,
            threshold_only=False,
        )

        self._file_name = ""
        self.file_name = ""
        self._src_image_wrapper = None
        self._image_dict = None

        self._current_exp = ""
        self._current_plant = ""
        self._current_date = dt.now().date()
        self._current_time = dt.now().time()
        self._current_camera = ""
        self._current_view_option = ""

        self._updating_combo_boxes = False
        self._updating_available_images = False
        self._updating_script_sim_available_images = False
        self._updating_process_modes = False
        self._updating_image_browser = False

        self._batch_is_active = False
        self.ui.mnu_db_action_group = None

        self._image_list_holder_ref_count = 0
        self._image_list_holder = None

        self._current_tool = None
        self.current_tool = None

        self._selected_style = ""
        self._selected_theme = ""

        self._last_progress_update = timer()
        self._last_process_events = timer()
        self._last_garbage_collected = timer()
        self._collecting_garbage = False
        self._global_pb_label = None
        self._global_progress_bar = None
        self._global_stop_button = None
        self._status_label = QLabel("")

        self.act_reset_db = QAction("Reset current database", self)
        self.act_reset_db.setToolTip(
            "Drops rebuilds current database (Only local databases)"
        )

        self.global_progress_update(
            step=0,
            total=100,
            process_events=True,
            msg="Finalizing UI",
            force_update=True,
        )

        self.text_color = QColor(0, 0, 0)
        self.background_color = QColor(255, 255, 255)

        self.gv_last_processed_item = QMouseGraphicsView(self)
        self.ui.ver_layout_last_image.addWidget(self.gv_last_processed_item)

        layout = QVBoxLayout()
        self.ui.frm_src_img.setLayout(layout)
        layout.addWidget(QLabel("Source image"))
        self.ui.gv_source_image = QMouseGraphicsView(self.ui.frm_src_img)
        layout.addWidget(self.ui.gv_source_image)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        layout = QVBoxLayout()
        self.ui.frm_res_img.setLayout(layout)
        self.ui.gv_output_image = QMouseGraphicsView(self.ui.frm_res_img)
        layout.addWidget(self.ui.gv_output_image)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        layout = QVBoxLayout()
        self.ui.frm_data.setLayout(layout)

        layout.addWidget(QLabel("Output data"))
        self.ui.tw_script_sim_output = QtWidgets.QTableWidget(self.ui.frm_data)
        layout.addWidget(self.ui.tw_script_sim_output)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.ui.tw_script_sim_output.setFrameShadow(QtWidgets.QFrame.Plain)
        self.ui.tw_script_sim_output.setAlternatingRowColors(True)
        self.ui.tw_script_sim_output.setObjectName("ui.tw_script_sim_output")
        self.ui.tw_script_sim_output.setColumnCount(2)
        self.ui.tw_script_sim_output.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.ui.tw_script_sim_output.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.ui.tw_script_sim_output.setHorizontalHeaderItem(1, item)
        self.ui.tw_script_sim_output.horizontalHeader().setStretchLastSection(True)
        self.ui.tw_script_sim_output.verticalHeader().setStretchLastSection(False)
        self.ui.tw_script_sim_output.setSortingEnabled(False)
        item = self.ui.tw_script_sim_output.horizontalHeaderItem(0)
        item.setText("Key")
        item = self.ui.tw_script_sim_output.horizontalHeaderItem(1)
        item.setText("Value")
        self.ui.tw_script_sim_output.horizontalHeader().setStretchLastSection(True)
        self.ui.tw_script_sim_output.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        layout = QVBoxLayout()
        self.ui.frm_params.setLayout(layout)

        layout.addWidget(QLabel("Param values"))
        self.ui.tw_params = QtWidgets.QTableWidget(self.ui.frm_params)
        layout.addWidget(self.ui.tw_params)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.ui.tw_params.setFrameShadow(QtWidgets.QFrame.Plain)
        self.ui.tw_params.setAlternatingRowColors(True)
        self.ui.tw_params.setObjectName("ui.tw_params")
        self.ui.tw_params.setColumnCount(2)
        self.ui.tw_params.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.ui.tw_params.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.ui.tw_params.setHorizontalHeaderItem(1, item)
        self.ui.tw_params.horizontalHeader().setStretchLastSection(True)
        self.ui.tw_params.verticalHeader().setStretchLastSection(False)
        self.ui.tw_params.setSortingEnabled(False)
        item = self.ui.tw_params.horizontalHeaderItem(0)
        item.setText("Param")
        item = self.ui.tw_params.horizontalHeaderItem(1)
        item.setText("Value")
        self.ui.tw_params.horizontalHeader().setStretchLastSection(True)
        self.ui.tw_params.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Data editor
        self.gv_de_image = QMouseGraphicsView(self.ui.spl_de_left)
        self.gv_de_image.setObjectName("gv_de_image")

        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(1)
        self.threads_waiting = 0
        self.threads_total = 0
        self.threads_step = 0

        self.pp_thread_pool = QThreadPool()
        self.pp_thread_pool.setMaxThreadCount(1)
        self.pp_threads_total = 0
        self.pp_threads_step = 0
        self.pp_pipeline = None

        self.setWindowIcon(
            QIcon(
                os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    "resources",
                    "leaf-24.ico",
                )
            )
        )

        self.statusBar().addWidget(self._status_label, stretch=0)

        self.global_progress_update(
            step=10,
            total=100,
            process_events=True,
            msg="Load tools",
            force_update=True,
        )
        self._ip_tools_holder = IptHolder()
        self.build_tools_selectors()

        # Build database selectors
        self.current_database = None
        self.distant_databases = []
        self.image_databases = defaultdict(list)
        self.recent_folders = []

        self.global_progress_update(
            step=20,
            total=100,
            process_events=True,
            msg="Connect events",
            force_update=True,
        )

        # Make the connections
        # SQL checkboxes
        self.ui.cb_experiment.currentIndexChanged.connect(
            self.cb_experiment_current_index_changed
        )
        self.ui.cb_plant.currentIndexChanged.connect(self.cb_plant_current_index_changed)
        self.ui.cb_date.currentIndexChanged.connect(self.cb_date_current_index_changed)
        self.ui.cb_camera.currentIndexChanged.connect(
            self.cb_camera_current_index_changed
        )
        self.ui.cb_view_option.currentIndexChanged.connect(
            self.cb_view_option_current_index_changed
        )
        self.ui.cb_time.currentIndexChanged.connect(self.cb_time_current_index_changed)

        self.ui.cb_available_outputs.currentIndexChanged.connect(
            self.cb_available_outputs_current_index_changed
        )

        # Selection handler
        self.ui.bt_add_to_selection.clicked.connect(self.on_bt_add_to_selection)
        self.ui.bt_add_random.clicked.connect(self.on_bt_add_random)
        self.ui.bt_clear_selection.clicked.connect(self.on_bt_clear_selection)
        self.ui.bt_remove_from_selection.clicked.connect(self.on_bt_remove_from_selection)
        self.ui.bt_keep_annotated.clicked.connect(self.on_bt_keep_annotated)

        self.ui.pushButton.setText("Push the button!!!")
        self.ui.pushButton.clicked.connect(self.do_exception)

        # Toolbox
        self.ui.bt_process_image.clicked.connect(self.on_bt_process_image)
        self.ui.bt_reset_op.clicked.connect(self.on_bt_reset_op)
        self.ui.bt_tool_help.clicked.connect(self.on_bt_tool_help)
        self.ui.bt_tool_show_code.clicked.connect(self.on_bt_tool_show_code)

        self.ui.bt_clear_result.clicked.connect(self.on_bt_clear_result)
        self.ui.bt_set_as_selected.clicked.connect(self.on_bt_set_as_selected)
        self.ui.bt_set_as_selected.setEnabled(False)

        # Batches
        self.ui.bt_launch_batch.clicked.connect(self.on_bt_launch_batch)
        self.ui.lw_last_batch.itemSelectionChanged.connect(self.on_itemSelectionChanged)
        self.ui.bt_set_batch_as_selection.clicked.connect(
            self.on_bt_set_batch_as_selection
        )

        # Images browser
        self.ui.tv_image_browser.doubleClicked.connect(
            self.on_tv_image_browser_double_clicked
        )

        # Annotations
        self.ui.bt_delete_annotation.clicked.connect(self.on_bt_delete_annotation)

        # Menu
        self.ui.action_new_tool.triggered.connect(self.on_action_new_tool)
        self.ui.actionSave_selected_image.triggered.connect(self.on_bt_save_current_image)
        self.ui.actionSave_all_images.triggered.connect(self.on_bt_save_all_images)
        self.ui.action_save_image_list.triggered.connect(self.on_action_save_image_list)
        self.ui.action_load_image_list.triggered.connect(self.on_action_load_image_list)
        self.ui.actionExit.triggered.connect(self.close_application)
        self.ui.actionEnable_annotations.triggered.connect(
            self.on_action_enable_annotations_checked
        )
        self.ui.act_parse_folder_memory.triggered.connect(self.on_action_parse_folder)
        self.ui.action_build_video_from_images.triggered.connect(
            self.on_action_build_video_from_images
        )
        self.ui.action_about_form.triggered.connect(self.on_action_about_form)
        self.ui.action_use_dark_theme.triggered.connect(self.on_color_theme_changed)
        self.ui.action_use_multithreading.triggered.connect(
            self.on_action_use_multithreading
        )
        self.ui.action_save_pipeline_processor_state.triggered.connect(
            self.on_action_save_pipeline_processor_state
        )

        # Help
        self.ui.action_show_read_me.triggered.connect(self.on_action_show_read_me)
        self.ui.action_show_documentation.triggered.connect(
            self.on_action_show_documentation
        )
        self.ui.action_build_tool_documentation.triggered.connect(
            self.on_action_build_tool_documentation
        )
        self.ui.action_build_ipso_phen_documentation.triggered.connect(
            self.on_action_build_ipso_phen_documentation
        )
        self.ui.action_build_test_files.triggered.connect(self.on_action_build_test_files)
        self.ui.action_show_log.triggered.connect(self.on_action_show_log)

        # Video
        self.ui.action_video_1_24_second.triggered.connect(
            self.on_video_frame_duration_changed
        )
        self.ui.action_video_half_second.triggered.connect(
            self.on_video_frame_duration_changed
        )
        self.ui.action_video_1_second.triggered.connect(
            self.on_video_frame_duration_changed
        )
        self.ui.action_video_5_second.triggered.connect(
            self.on_video_frame_duration_changed
        )
        self.ui.action_video_res_first_image.triggered.connect(
            self.on_video_resolution_changed
        )
        self.ui.action_video_res_1080p.triggered.connect(self.on_video_resolution_changed)
        self.ui.action_video_res_720p.triggered.connect(self.on_video_resolution_changed)
        self.ui.action_video_res_576p.triggered.connect(self.on_video_resolution_changed)
        self.ui.action_video_res_480p.triggered.connect(self.on_video_resolution_changed)
        self.ui.action_video_res_376p.triggered.connect(self.on_video_resolution_changed)
        self.ui.action_video_res_240p.triggered.connect(self.on_video_resolution_changed)
        self.ui.action_video_ar_16_9.triggered.connect(self.on_video_aspect_ratio_changed)
        self.ui.action_video_ar_4_3.triggered.connect(self.on_video_aspect_ratio_changed)
        self.ui.action_video_ar_1_1.triggered.connect(self.on_video_aspect_ratio_changed)
        self.ui.action_video_bkg_color_black.triggered.connect(
            self.on_action_video_bkg_color_changed
        )
        self.ui.action_video_bkg_color_white.triggered.connect(
            self.on_action_video_bkg_color_changed
        )
        self.ui.action_video_bkg_color_silver.triggered.connect(
            self.on_action_video_bkg_color_changed
        )

        # Pipeline builder
        self.ui.act_settings_sir_keep.triggered.connect(self.on_sis_changed)
        self.ui.act_settings_sir_2x.triggered.connect(self.on_sis_changed)
        self.ui.act_settings_sir_3x.triggered.connect(self.on_sis_changed)
        self.ui.act_settings_sir_4x.triggered.connect(self.on_sis_changed)
        self.ui.act_settings_sir_5x.triggered.connect(self.on_sis_changed)
        self.ui.act_settings_sir_6x.triggered.connect(self.on_sis_changed)

        # Data editor
        self.ui.action_de_new_sheet.triggered.connect(self.on_action_de_new_sheet)
        self.ui.action_de_load_csv.triggered.connect(self.on_action_de_load_csv)
        self.ui.action_de_create_sheet_from_selection.triggered.connect(
            self.on_action_de_create_sheet_from_selection
        )
        self.ui.action_de_add_column.triggered.connect(self.on_action_de_add_column)
        self.ui.action_de_delete_column.triggered.connect(self.on_action_de_delete_column)
        self.ui.action_de_save_csv.triggered.connect(self.on_action_de_save_csv)

        self.ui.bt_update_selection_stats.clicked.connect(
            self.on_bt_update_selection_stats
        )

        # Pipeline processor
        self.ui.sl_pp_thread_count.valueChanged.connect(
            self.on_sl_pp_thread_count_index_changed
        )
        self.ui.bt_pp_select_output_folder.clicked.connect(
            self.on_bt_pp_select_output_folder
        )
        self.ui.bt_pp_select_script.clicked.connect(self.on_bt_pp_load)
        self.ui.bt_pp_reset.clicked.connect(self.on_bt_pp_reset)
        self.ui.bt_pp_start.clicked.connect(self.on_bt_pp_start)
        self.ui.rb_pp_default_process.clicked.connect(self.on_rb_pp_default_process)
        self.ui.rb_pp_load_script.clicked.connect(self.on_rb_pp_load_script)

        # Pipeline editor V2
        self.ui.bt_pp_up.setEnabled(False)
        self.ui.bt_pp_down.setEnabled(False)
        self.ui.bt_pp_delete.setEnabled(False)
        self.ui.bt_pp_new.clicked.connect(self.on_bt_pp_new)
        self.ui.bt_pp_load.clicked.connect(self.on_bt_pp_load)
        self.ui.bt_pp_save.clicked.connect(self.on_bt_pp_save)
        self.ui.bt_pp_up.clicked.connect(self.on_bt_pp_up)
        self.ui.bt_pp_down.clicked.connect(self.on_bt_pp_down)
        self.ui.bt_pp_delete.clicked.connect(self.on_bt_pp_delete)
        self.ui.bt_pp_run.clicked.connect(self.on_bt_pp_run)
        self.ui.bt_pp_invalidate.clicked.connect(self.on_bt_pp_invalidate)

        self.ui.dk_log.visibilityChanged.connect(self.on_log_visibility_changed)

        self.ui.sl_pp_thread_count.setMaximum(mp.cpu_count())
        self.ui.sl_pp_thread_count.setMinimum(1)
        self._custom_csv_name = False
        self.on_bt_pp_reset()

        self._settings_ref_count = 0
        self._settings = None
        self.load_settings()

    def get_image_model(self) -> QImageDatabaseModel:
        ret = self.ui.tv_image_browser.model()
        return ret if isinstance(ret, QImageDatabaseModel) else None

    def get_image_dataframe(self) -> pd.DataFrame:
        model = self.get_image_model()
        return None if model is None else model.images

    def has_image_dataframe(self) -> bool:
        return self.get_image_dataframe() is not None

    def get_image_delegate(self) -> QImageDrawerDelegate:
        ret = self.ui.tv_image_browser.itemDelegate()
        return ret if isinstance(ret, QImageDrawerDelegate) else None

    def update_images_queue(self):
        dataframe = self.get_image_dataframe()
        self.ui.lw_images_queue.clear()
        if dataframe is None:
            return
        dataframe = dataframe.sort_values(by=["date_time"], axis=0, na_position="first")
        for row in reversed(range(dataframe.shape[0])):
            row_data = {
                k: v
                for k, v in zip(
                    list(dataframe.columns),
                    [str(dataframe.iloc[row, ci]) for ci in range(dataframe.shape[1])],
                )
            }
            new_item = QListWidgetItem()
            new_item.setText(row_data["Luid"])
            new_item.setToolTip("\n".join([f"{k}: {v}" for k, v in row_data.items()]))
            self.ui.lw_images_queue.insertItem(0, new_item)

    def build_tools_selectors(self):
        try:
            sg_menu = QMenu(self.ui.bt_select_tool)
            pp_menu = QMenu(self)
            use_cases = self._ip_tools_holder.use_cases
            for use_case in use_cases:
                # Exclude case orphans
                if use_case == "none":
                    continue
                sg_use_case_root = sg_menu.addMenu(use_case)
                sg_use_case_root.setToolTipsVisible(True)
                sg_use_case_root.setToolTip(ipc.tool_family_hints.get(use_case, ""))

                pp_use_case_root = pp_menu.addMenu(use_case)
                pp_use_case_root.setToolTip(ipc.tool_family_hints.get(use_case, ""))
                pp_use_case_root.setToolTipsVisible(True)
                pp_use_case_root.triggered[QAction].connect(self.on_bt_pp_add_tool)

                op_lst = self._ip_tools_holder.list_by_use_case(use_case)
                for op in op_lst:
                    # Single tools menu
                    act = QAction(op.name, self)
                    act.setToolTip(op.hint)
                    sg_use_case_root.addAction(act)
                    # Pipeline tools menu
                    if bool(set(op.use_case).intersection(set(ipc.tool_groups_pipeline))):
                        act = QAction(op.name, self)
                        act.setToolTip(op.hint)
                        pp_use_case_root.addAction(act)

            sg_menu.triggered[QAction].connect(self.on_menu_tool_selection)

            # Pipeline groups
            pp_menu.addSeparator()
            act = QAction("Default empty group", self)
            act.setToolTip("Add an empty group with default settings")
            act.triggered.connect(self.on_bt_pp_add_tool)
            pp_menu.addAction(act)
            group_root = pp_menu.addMenu("Pre filled groups")
            for name, hint in zip(
                [
                    "Fix exposure",
                    "Pre process image",
                    "Threshold",
                    "Mask cleanup",
                    "Feature extraction",
                    "Visualization helpers",
                ],
                [
                    """Default exposure and white balance fixing tools\n
                        Added tools need to be configured""",
                    """Prepare image to make thresholding easier \n
                        Added tools need to be configured""",
                    """Build a mask containing only the target object(s)\n
                        Added tools need to be configured""",
                    """Remove noise from a mask\n
                        Added tools need to be configured""",
                    """Add tools to extract features from the image, some may need a mask\n
                        Added tools need to be configured""",
                    """Add tools to help visualize the pipeline output""",
                ],
            ):
                act = QAction(name, self)
                act.setToolTip(hint)
                group_root.addAction(act)
            group_root.triggered[QAction].connect(self.on_bt_pp_add_tool)

            pp_menu.setToolTipsVisible(True)

            self.ui.bt_pp_select_tool.setMenu(pp_menu)
            self.ui.bt_select_tool.setMenu(sg_menu)
        except Exception as e:
            logger.exception(f"Failed to load tools: {repr(e)}")

    def init_image_browser(self, dataframe):
        self.ui.tv_image_browser.setModel(QImageDatabaseModel(dataframe))
        self.ui.tv_image_browser.setSortingEnabled(True)
        selectionModel = self.ui.tv_image_browser.selectionModel()
        selectionModel.selectionChanged.connect(
            self.on_tv_image_browser_selection_changed
        )
        self.update_images_queue()

        model = self.get_image_model()
        if model is not None:
            self.update_feedback(
                status_message=f"Added {model.rowCount()} items to image browser",
                use_status_as_log=True,
                log_level=logging.INFO,
            )
            hh: QHeaderView = self.ui.tv_image_browser.horizontalHeader()
            hh.setMaximumSectionSize(150)
            hh.setMinimumSectionSize(70)
            if model.rowCount() <= 0:
                for i in range(0, hh.count()):
                    hh.resizeSection(i, hh.sectionSizeHint(i))
            else:
                for i in range(0, hh.count()):
                    hh.resizeSection(
                        i,
                        self.ui.tv_image_browser.sizeHintForIndex(
                            model.createIndex(0, i)
                        ).width(),
                    )
            hh.setMaximumSectionSize(-1)
            self.ui.tv_image_browser.setHorizontalHeader(hh)
            vh: QHeaderView = self.ui.tv_image_browser.verticalHeader()
            vh.setSectionResizeMode(QHeaderView.Fixed)
            self.ui.tv_image_browser.setVerticalHeader(vh)

    def on_tv_image_browser_double_clicked(self, index):
        if not self._updating_image_browser:
            self.run_process(wrapper=self._src_image_wrapper)

    def on_tv_image_browser_selection_changed(self, selected, deselected):
        for index in selected.indexes():
            current_row = index.row()
            break
        else:
            self.select_image_from_luid(None)
            return

        for index in deselected.indexes():
            last_row = index.row()
            break
        else:
            last_row = -1

        if not self._updating_image_browser and (last_row != current_row):
            self.select_image_from_luid(
                self.get_image_model().get_cell_data(
                    row_number=current_row, column_name="Luid"
                )
            )

    def update_image_browser(self, dataframe, mode: str = "add"):
        if mode == "add":
            if not self.has_image_dataframe():
                self.init_image_browser(dataframe=dataframe)
            else:
                model = self.get_image_model()
                old_row_count = model.rowCount()
                model.images = model.images.append(dataframe)
                new_row_count = model.rowCount()
                self.update_images_queue()
                self.update_feedback(
                    status_message=f"Added {new_row_count - old_row_count} items to image browser",
                    use_status_as_log=True,
                    log_level=logging.INFO,
                )
        elif mode == "remove":
            if not self.has_image_dataframe():
                return
            else:
                model = self.get_image_model()
                src_df = model.images
                old_row_count = model.rowCount()
                model.images = src_df[~src_df["Luid"].isin(dataframe["Luid"])]
                new_row_count = model.rowCount()
                self.update_images_queue()
                self.update_feedback(
                    status_message=f"Removed {old_row_count - new_row_count} items to image browser",
                    use_status_as_log=True,
                    log_level=logging.INFO,
                )
        elif mode == "keep":
            if not self.has_image_dataframe():
                return
            else:
                model = self.get_image_model()
                src_df = model.images
                old_row_count = model.rowCount()
                model.images = src_df[src_df["Luid"].isin(dataframe["Luid"])]
                new_row_count = model.rowCount()
                self.update_images_queue()
                self.update_feedback(
                    status_message=f"Removed {old_row_count - new_row_count} items to image browser",
                    use_status_as_log=True,
                    log_level=logging.INFO,
                )
        elif mode == "clear":
            self.init_image_browser(None)
        else:
            logger.exception(f'Failed to update image browser, unknown mode "{mode}"')

    def on_action_save_image_list(self):
        file_name_ = QFileDialog.getSaveFileName(
            parent=self,
            caption="Save image list as CSV",
            dir=ipso_folders.get_path("image_list"),
            filter="CSV(*.csv)",
        )[0]
        if file_name_:
            ipso_folders.set_path(
                "image_list", os.path.join(os.path.dirname(file_name_), "")
            )
            model = self.get_image_model()
            if model is not None and model.images.shape[0] > 0:
                model.images.to_csv(file_name_, index=False)

    def on_action_load_image_list(self):
        file_name_ = QFileDialog.getOpenFileName(
            parent=self,
            caption="Load image list from CSV",
            dir=ipso_folders.get_path("image_list"),
            filter="CSV(*.csv)",
        )[0]
        if file_name_:
            ipso_folders.set_path(
                "image_list", os.path.join(os.path.dirname(file_name_), "")
            )
            self.init_image_browser(pd.read_csv(file_name_))

    def build_recent_folders_menu(self, new_folder: str = ""):
        self.ui.mnu_recent_parsed_folders.clear()
        if new_folder:
            if new_folder in self.recent_folders:
                self.recent_folders.remove(new_folder)
            self.recent_folders.insert(0, new_folder)
            if len(self.recent_folders) > 10:
                self.recent_folders.pop()
        act = QAction("Clear", self, checkable=False)
        act.triggered.connect(self.on_recent_folder_clear)
        self.ui.mnu_recent_parsed_folders.addAction(act)
        self.ui.mnu_recent_parsed_folders.addSeparator()
        for fld in self.recent_folders:
            act = QAction(fld, self, checkable=False)
            act.setEnabled(os.path.isdir(fld))
            act.triggered.connect(self.on_recent_folder_select)
            self.ui.mnu_recent_parsed_folders.addAction(act)

    def add_folder_database(
        self, display_name: str, hint: str, enabled: bool, selected: bool = False
    ):
        # Connect action
        act = QAction(display_name, self, checkable=True)
        act.setEnabled(enabled)
        act.setChecked(selected)
        act.setToolTip(hint)
        act.triggered.connect(self.on_local_database_connect)
        self.ui.mnu_connect_to_db.addAction(self.ui.mnu_db_action_group.addAction(act))

    def on_reset_database(self):
        if self.current_database is not None:
            self.current_database.reset()

    def build_database_menu(self, selected: str = ""):
        self.ui.mnu_connect_to_db.clear()
        self.ui.mnu_db_action_group = QActionGroup(self)
        self.ui.mnu_db_action_group.setExclusive(True)

        self.ui.mnu_connect_to_db.addAction(self.act_reset_db)
        self.act_reset_db.triggered.connect(self.on_reset_database)
        self.ui.mnu_connect_to_db.addSeparator()

        for dbt in dbi.DbType:
            if len(self.image_databases[dbt]) > 0:
                db_type_root = self.ui.mnu_connect_to_db.addMenu(dbt.value)
                for ldb in self.image_databases[dbt]:
                    act = QAction(ldb.display_name, self, checkable=True)
                    act.setData(ldb)
                    act.setEnabled(
                        not ldb.src_files_path or os.path.isdir(ldb.src_files_path)
                    )
                    act.setChecked(selected == ldb.db_qualified_name)
                    act.setToolTip(f"{ldb.full_display_name}\n{ldb.db_folder_name}")
                    act.triggered.connect(self.on_local_database_connect)
                    db_type_root.addAction(self.ui.mnu_db_action_group.addAction(act))

    def do_parse_folder(self, folder_path):
        self.build_recent_folders_menu(new_folder=folder_path)
        self.current_database = dbf.db_info_to_database(
            dbb.DbInfo(
                display_name="Memory database",
                db_qualified_name=":memory:",
                src_files_path=folder_path,
                dbms="sqlite",
                target="sqlite",
                db_folder_name=ipso_folders.get_path("sql_db"),
            ),
        )

    def on_action_parse_folder(self):
        dlg = FrmSelectFolder(self)
        res = dlg.show_modal(default_path=ipso_folders.get_path("db_image_folder"))
        if (res == 1) and os.path.isdir(dlg.folder_path):
            if dlg.dbms == "none":
                self.do_parse_folder(dlg.folder_path)
            else:
                ldb = None
                for ldb in self.image_databases[dbi.DbType.CUSTOM_DB]:
                    if (ldb.src_files_path == dlg.folder_path) and (dlg.dbms == ldb.dbms):
                        self.update_feedback(
                            status_message="Database already exists",
                            log_message=f"""
                            There's already a database named {ldb.display_name}
                            pointing to {ldb.src_files_path} using {ldb.dbms}.
                            Existing database will be used.""",
                            log_level=logging.WARNING,
                        )
                        self.current_database = dbf.db_info_to_database(ldb)
                        return
                ipso_folders.set_path("db_image_folder", dlg.folder_path)
                new_db = dbb.DbInfo(
                    display_name=dlg.db_qualified_name,
                    src_files_path=dlg.folder_path,
                    dbms=dlg.dbms,
                    target="sqlite" if dlg.dbms == "sqlite" else "psql_local",
                    db_folder_name=ipso_folders.get_path("sql_db"),
                )
                self.current_database = dbf.db_info_to_database(new_db)
                self.image_databases[dbi.DbType.CUSTOM_DB].append(new_db)
                self.build_database_menu(selected=dlg.db_qualified_name)

    def on_local_database_connect(self, q):
        data = self.sender().data()
        if data is not None and isinstance(data, dbb.DbInfo):
            db = dbf.db_info_to_database(data)
            if isinstance(db, str):
                logger.exception(f"Unknown DBMS: {db}")
            else:
                self.current_database = db

    def on_recent_folder_select(self):
        self.do_parse_folder(self.sender().text())

    def on_recent_folder_clear(self):
        self.recent_folders = []
        self.build_recent_folders_menu()

    def update_database(self, db_wrapper: dbb.DbWrapper):
        if db_wrapper is None or not isinstance(db_wrapper, dbb.DbWrapper):
            return False
        self.update_feedback(
            status_message="Building image database",
            log_message=f"Building image database for {repr(db_wrapper)}",
            log_level=logging.INFO,
        )
        if not self._initializing:
            self.global_progress_start(add_stop_button=True)
            db_wrapper.progress_call_back = self.global_progress_update
            self.set_global_enabled_state(
                new_state=False, force_enabled=("global_stop_button",)
            )
            self.process_events()
        try:
            db_wrapper.update()
        except Exception as e:
            logger.exception(f"Failed query database because: {repr(e)}")
            ret = False
        else:
            ret = True
        finally:
            if not self._initializing:
                self.global_progress_stop()
                db_wrapper.progress_call_back = None
                self.set_global_enabled_state(True)
                self.process_events()
        return ret

    def query_current_database(
        self,
        command: str,
        table: str = "snapshots",
        columns: str = "*",
        additional: str = "",
        **kwargs,
    ):
        if self.current_database is not None and (
            self.current_database.is_exists()
            or self.update_database(db_wrapper=self.current_database)
        ):
            return self.current_database.query(
                command=command,
                table=table,
                columns=columns,
                additional=additional,
                **kwargs,
            )
        return None

    def query_current_database_as_pandas(
        self,
        command: str,
        table: str = "snapshots",
        columns: str = "*",
        additional: str = "",
        **kwargs,
    ):
        if self.current_database is not None and (
            self.current_database.is_exists()
            or self.update_database(db_wrapper=self.current_database)
        ):
            return self.current_database.query_to_pandas(
                command=command,
                table=table,
                columns=columns,
                additional=additional,
                **kwargs,
            )
        return None

    def query_one_current_database(
        self,
        command: str,
        table: str = "snapshots",
        columns: str = "*",
        additional: str = "",
        **kwargs,
    ):
        ret = self.query_current_database(
            command=command,
            table=table,
            columns=columns,
            additional=additional,
            **kwargs,
        )
        if (ret is not None) and (len(ret) > 0):
            return ret[0]
        else:
            return None

    def set_enabled_database_controls(self, new_state: bool):
        self.ui.cb_experiment.setEnabled(new_state)
        self.ui.cb_plant.setEnabled(new_state)
        self.ui.cb_date.setEnabled(new_state)
        self.ui.cb_camera.setEnabled(new_state)
        self.ui.cb_view_option.setEnabled(new_state)
        self.ui.cb_time.setEnabled(new_state)

        self.ui.chk_experiment.setEnabled(new_state)
        self.ui.chk_plant.setEnabled(new_state)
        self.ui.chk_date.setEnabled(new_state)
        self.ui.chk_camera.setEnabled(new_state)
        self.ui.chk_view_option.setEnabled(new_state)
        self.ui.chk_time.setEnabled(new_state)

        self.ui.bt_add_to_selection.setEnabled(new_state)
        self.ui.bt_add_random.setEnabled(new_state)
        self.ui.bt_remove_from_selection.setEnabled(new_state)

    def process_events(self):
        in_time = timer()
        if in_time - self._last_process_events > 0.2:
            self._last_process_events = in_time
            qApp.processEvents()

    def global_progress_start(self, add_stop_button=False):
        """Displays progress bar and stop button (optional) in status bar

        Keyword Arguments:
            add_stop_button {bool} -- If true stop button will be displayed (default: {False})
        """
        try:
            # Add progress bar
            self._global_progress_bar = QProgressBar()
            self._global_progress_bar.setMaximumWidth(300)
            self._global_progress_bar.setMinimumWidth(300)
            self.statusBar().addPermanentWidget(self._global_progress_bar, stretch=0)
            self.global_progress_update(0, 0)
            # Add stop button
            if add_stop_button:
                self._batch_stop_current = False
                self._global_stop_button = QToolButton()
                self._global_stop_button.setObjectName("global_stop_button")
                icon_ = QIcon(":/image_process/resources/Stop.png")
                self._global_stop_button.setIcon(icon_)
                self._global_stop_button.clicked.connect(self.on_bt_stop_batch)
                self.statusBar().addPermanentWidget(self._global_stop_button)
        except Exception as e:
            logger.exception(f"Failed to init global progress bar: {repr(e)}")

    def global_progress_update(
        self,
        step,
        total,
        process_events: bool = False,
        msg: str = "",
        force_update: bool = False,
    ):
        if force_update or (timer() - self._last_progress_update > 0.2):
            if self._splash is not None:
                if total == 0:
                    self._pg_splash.setValue(0)
                else:
                    self._pg_splash.setValue(step / total * 100)
                self._lbl_splash_text.setText(msg)
            elif self._global_progress_bar is not None:
                if step == 0 and total == 0:
                    self._global_progress_bar.setFormat("Starting")
                    self._global_progress_bar.setValue(0)
                elif step == 1 and total == 1:
                    self._global_progress_bar.setFormat("Done")
                    self._global_progress_bar.setValue(100)
                else:
                    self._global_progress_bar.setFormat(f"{step}/{total}")
                    self._global_progress_bar.setValue(
                        round((min(step, total)) / total * 100)
                    )
            self._last_progress_update = timer()
            if process_events:
                self.process_events()

    def global_progress_stop(self):
        self.global_progress_update(1, 1)
        if self._global_stop_button is not None:
            self.ui.statusbar.removeWidget(self._global_stop_button)
        if self._global_progress_bar is not None:
            self.ui.statusbar.removeWidget(self._global_progress_bar)
        if self._global_pb_label is not None:
            self.ui.statusbar.removeWidget(self._global_pb_label)

    def begin_edit_image_browser(self):
        self._updating_image_browser = True
        self.ui.tv_image_browser.setSortingEnabled(False)

    def end_edit_image_browser(self):
        self.ui.tv_image_browser.setSortingEnabled(True)
        self._updating_image_browser = False

    def lock_settings(self) -> QSettings:
        if not hasattr(self, "_settings") or (self._settings is None):
            self._settings = QSettings("LIPM_TPMP", "ipso_phen")
        self._settings_ref_count += 1
        return self._settings

    def unlock_settings(self):
        self._settings_ref_count -= 1
        if (self._settings_ref_count <= 0) and (self._settings is not None):
            del self._settings

    def restore_annotation(self, tag, experiment):
        id = self.get_image_delegate()
        if id is None:
            return
        if isinstance(tag, BaseImageProcessor):
            luid = tag.luid
        elif isinstance(tag, str):
            luid = tag
        else:
            self.update_feedback(
                status_message="Failed to retrieve annotation data",
                log_message=f"unable to retrieve annotation data for {str(tag)}",
                log_level=logging.ERROR,
            )
            self.ui.bt_delete_annotation.setEnabled(False)
            return
        data = id.get_annotation(luid=luid, experiment=experiment)
        self.ui.bt_delete_annotation.setEnabled(data is not None)
        if data:
            self.ui.te_annotations.insertPlainText(data.get("text", ""))
            data_kind = data.get("kind", "oops").lower()
            if data_kind == "info":
                self.ui.cb_annotation_level.setCurrentIndex(0)
                icon_ = QIcon(":/annotation_level/resources/Info.png")
            elif data_kind == "ok":
                self.ui.cb_annotation_level.setCurrentIndex(1)
                icon_ = QIcon(":/annotation_level/resources/OK.png")
            elif data_kind == "warning":
                self.ui.cb_annotation_level.setCurrentIndex(2)
                icon_ = QIcon(":/annotation_level/resources/Warning.png")
            elif data_kind == "error":
                self.ui.cb_annotation_level.setCurrentIndex(3)
                icon_ = QIcon(":/annotation_level/resources/Error.png")
            elif data_kind == "critical":
                self.ui.cb_annotation_level.setCurrentIndex(4)
                icon_ = QIcon(":/annotation_level/resources/Danger.png")
            elif data_kind == "source issue":
                self.ui.cb_annotation_level.setCurrentIndex(5)
                icon_ = QIcon(":/annotation_level/resources/Problem.png")
            else:
                self.ui.cb_annotation_level.setCurrentIndex(6)
                icon_ = QIcon(":/annotation_level/resources/Help.png")
        else:
            self.ui.cb_annotation_level.setCurrentIndex(0)
            self.ui.te_annotations.clear()
            icon_ = QIcon()

        self.ui.tw_tool_box.setTabIcon(0, icon_)

    def get_image_list_name(self):
        table = self.ui.tv_image_browser
        if table.rowCount() == 0:
            return "Empty list"
        else:
            model = self.get_image_model()
            exp_idx = model.get_column_index_from_name("experiment")
            return f'{model.images.iloc[0, exp_idx]}_{table.rowCount()}_{dt.now().strftime("%Y_%b_%d_%H-%M-%S")}'

    def set_global_enabled_state(
        self, new_state: bool, force_enabled: tuple = (), force_disabled: tuple = ()
    ):
        widgets = self.findChildren(QPushButton)
        widgets.extend(self.findChildren(QToolButton))
        widgets.extend(self.findChildren(QCheckBox))
        widgets.extend(self.findChildren(QComboBox))
        widgets.extend(self.findChildren(QSlider))
        widgets.extend(self.findChildren(QSpinBox))
        widgets.extend(self.findChildren(QLineEdit))
        widgets.extend(self.findChildren(QMenu))
        widgets.extend(self.findChildren(QTableWidget))

        for widget in widgets:
            # if 'ipt_param_' in widget.objectName():
            #     continue
            if "sl_pp_thread_count" in widget.objectName():
                continue
            if "chk_pp_show_last_item" in widget.objectName():
                continue
            if "cb_queue_auto_scroll" in widget.objectName():
                continue
            if "ui.tv_pp_view" in widget.objectName():
                continue
            if widget.objectName() in force_enabled:
                widget.setEnabled(True)
            elif widget.objectName() in force_disabled:
                widget.setEnabled(False)
            else:
                widget.setEnabled(new_state)

        for tab_name_ in [_TAB_TOOLS, _TAB_PIPELINE_V2]:
            tab_widget_ = self.ui.tb_tool_script.findChild(QWidget, tab_name_)
            if tab_widget_ is None:
                continue
            if new_state is True:
                tab_widget_.setEnabled(True)
            else:
                tab_widget_.setEnabled(tab_name_ == self.selected_run_tab)

    def apply_theme(self, style: str, theme: str):
        try:
            qApp.setStyle(style)
            if theme == "dark":
                palette = QPalette()
                palette.setColor(QPalette.WindowText, Qt.white)
                palette.setColor(QPalette.Text, Qt.white)
                palette.setColor(QPalette.ToolTipText, Qt.black)
                palette.setColor(QPalette.ButtonText, Qt.white)
                palette.setColor(QPalette.BrightText, Qt.red)
                palette.setColor(QPalette.HighlightedText, Qt.black)
                palette.setColor(QPalette.Window, QColor(53, 53, 53))
                palette.setColor(QPalette.Base, QColor(60, 60, 60))
                palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
                palette.setColor(QPalette.ToolTipBase, Qt.yellow)
                palette.setColor(QPalette.Button, QColor(53, 53, 53))
                palette.setColor(QPalette.Link, QColor(42, 130, 218))
                palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
            elif theme == "default":
                palette = self.style().standardPalette()
            elif theme == "random !!!":
                palette = QPalette()
                palette.setColor(QPalette.Window, QColor(*ipc.random_color()))
                palette.setColor(QPalette.WindowText, QColor(*ipc.random_color()))
                palette.setColor(QPalette.Base, QColor(*ipc.random_color()))
                palette.setColor(QPalette.AlternateBase, QColor(*ipc.random_color()))
                palette.setColor(QPalette.ToolTipBase, QColor(*ipc.random_color()))
                palette.setColor(QPalette.ToolTipText, QColor(*ipc.random_color()))
                palette.setColor(QPalette.Text, QColor(*ipc.random_color()))
                palette.setColor(QPalette.Button, QColor(*ipc.random_color()))
                palette.setColor(QPalette.ButtonText, QColor(*ipc.random_color()))
                palette.setColor(QPalette.BrightText, QColor(*ipc.random_color()))
                palette.setColor(QPalette.Link, QColor(*ipc.random_color()))
                palette.setColor(QPalette.Highlight, QColor(*ipc.random_color()))
                palette.setColor(QPalette.HighlightedText, QColor(*ipc.random_color()))
            elif theme == "Demo":
                palette = QPalette()
                palette.setColor(QPalette.WindowText, QColor(*ipc.bgr_to_rgb(ipc.C_BLUE)))
                palette.setColor(
                    QPalette.Text, QColor(*ipc.bgr_to_rgb(ipc.C_BLUE_VIOLET))
                )
                palette.setColor(
                    QPalette.ToolTipText, QColor(*ipc.bgr_to_rgb(ipc.C_CABIN_BLUE))
                )
                palette.setColor(QPalette.ButtonText, QColor(*ipc.bgr_to_rgb(ipc.C_CYAN)))
                palette.setColor(
                    QPalette.BrightText, QColor(*ipc.bgr_to_rgb(ipc.C_LIGHT_STEEL_BLUE))
                )
                palette.setColor(
                    QPalette.HighlightedText, QColor(*ipc.bgr_to_rgb(ipc.C_PURPLE))
                )
                palette.setColor(QPalette.Window, QColor(*ipc.bgr_to_rgb(ipc.C_MAROON)))
                palette.setColor(QPalette.Base, QColor(*ipc.bgr_to_rgb(ipc.C_BLACK)))
                palette.setColor(
                    QPalette.AlternateBase, QColor(*ipc.bgr_to_rgb(ipc.C_GREEN))
                )
                palette.setColor(
                    QPalette.ToolTipBase, QColor(*ipc.bgr_to_rgb(ipc.C_LIME))
                )
                palette.setColor(QPalette.Button, QColor(*ipc.bgr_to_rgb(ipc.C_ORANGE)))
                palette.setColor(QPalette.Link, QColor(*ipc.bgr_to_rgb(ipc.C_WHITE)))
                palette.setColor(
                    QPalette.Highlight, QColor(*ipc.bgr_to_rgb(ipc.C_SILVER))
                )
                palette.setColor(QPalette.Highlight, QColor(*ipc.bgr_to_rgb(ipc.C_RED)))
            else:
                self.update_feedback(
                    status_message="Unknown theme",
                    log_message=f'Unknown theme "{theme}" ignored',
                    log_level=logging.ERROR,
                )
                return

            self.text_color = palette.color(QPalette.Text)
            self.background_color = palette.color(QPalette.Base)
            qApp.setPalette(palette)

            item_delegate = self.ui.tb_ge_dataframe.itemDelegate()
            if item_delegate is not None and hasattr(item_delegate, "set_palette"):
                item_delegate.set_palette(new_palette=qApp.palette())

            item_delegate = self.ui.tv_image_browser.itemDelegate()
            if item_delegate is not None and hasattr(item_delegate, "set_palette"):
                item_delegate.set_palette(new_palette=qApp.palette())

            if self.ui.actionEnable_annotations.isChecked():
                self.on_action_enable_annotations_checked()

        except Exception as e:
            logger.exception(f"Failed to load set theme: {repr(e)}")
        else:
            self.update_feedback(
                status_message=f"Changed theme to: {style} ({theme})",
                use_status_as_log=True,
                log_level=logging.INFO,
            )

    def on_color_theme_changed(self):
        self._selected_theme = self.sender().text()
        self.apply_theme(style=self._selected_style, theme=self._selected_theme)

    def on_style_changed(self):
        self._selected_style = self.sender().text()
        self.apply_theme(style=self._selected_style, theme=self._selected_theme)

    @log_method_execution_time
    def load_settings(self):
        """Load and apply settings

        Returns:
            None --
        """
        self.global_progress_update(
            step=30,
            total=100,
            process_events=True,
            msg="Loading settings",
            force_update=True,
        )
        settings_ = self.lock_settings()
        try:
            res = True

            # Theme
            self.global_progress_update(
                step=40,
                total=100,
                process_events=True,
                msg="Setting theme",
                force_update=True,
            )
            self._selected_theme = settings_.value("selected_theme", "dark")
            act_grp = QActionGroup(self)
            act_grp.setExclusive(True)
            # Dark
            act = QAction("dark", self, checkable=True)
            act.setChecked("dark" == self._selected_theme)
            act.triggered.connect(self.on_color_theme_changed)
            self.ui.menu_theme.addAction(act_grp.addAction(act))
            # Light
            act = QAction("default", self, checkable=True)
            act.setChecked("default" == self._selected_theme)
            act.triggered.connect(self.on_color_theme_changed)
            self.ui.menu_theme.addAction(act_grp.addAction(act))
            # Joke
            act = QAction("random !!!", self, checkable=True)
            act.setChecked("random !!!" == self._selected_theme)
            act.triggered.connect(self.on_color_theme_changed)
            self.ui.menu_theme.addAction(act_grp.addAction(act))
            # Test
            act = QAction("Demo", self, checkable=True)
            act.setChecked("Demo" == self._selected_theme)
            act.triggered.connect(self.on_color_theme_changed)
            self.ui.menu_theme.addAction(act_grp.addAction(act))

            self.ui.menu_theme.addSeparator()

            # Style
            self._selected_style = settings_.value(
                "selected_style",
                "Fusion" if "Fusion" in QStyleFactory.keys() else QStyleFactory.keys()[0],
            )
            act_grp = QActionGroup(self)
            act_grp.setExclusive(True)
            for style in QStyleFactory.keys():
                act = QAction(style, self, checkable=True)
                act.setChecked(style == self._selected_style)
                act.triggered.connect(self.on_style_changed)
                self.ui.menu_theme.addAction(act_grp.addAction(act))

            self.apply_theme(style=self._selected_style, theme=self._selected_theme)

            self.global_progress_update(
                step=50,
                total=100,
                process_events=True,
                msg="Restore geometry",
                force_update=True,
            )
            geom = settings_.value("main_geometry", None)
            if geom is not None:
                self.restoreGeometry(geom)
            state = settings_.value("main_state", None)
            if state is not None:
                self.restoreState(state)

            available_width = self.geometry().width()
            available_height = self.geometry().height()

            frame_rect = settings_.value("log_geometry", None)
            if frame_rect is not None:
                self.ui.dk_log.setGeometry(frame_rect)
            state = settings_.value("log_state", None)
            if state is not None:
                self.ui.dk_log.restoreState(state)
            self.ui.action_show_log.setChecked(self.ui.dk_log.isVisible())

            # Two way splitter for main side panels in pipeline builder
            spl_state = settings_.value("spl_pb_ver_main", None)
            if spl_state is not None:
                self.ui.spl_pb_ver_main.restoreState(spl_state)
            else:
                w = (available_width - 50) // 8
                self.ui.spl_pb_ver_main.setSizes((w * 3, w * 5))

            # Three way splitter between source, result and data panels in pipeline builder
            spl_state = settings_.value("ui.spl_ver_src_res_data", None)
            if False and spl_state is not None:
                self.ui.spl_ver_src_res_data.restoreState(spl_state)
            else:
                w = ((available_width - 50) // 8 * 5) // 6
                self.ui.spl_ver_src_res_data.setSizes((w * 2, w * 4))

            # Three way splitter between source, result and data panels in pipeline builder
            spl_state = settings_.value("ui.spl_hor_src_data_params", None)
            if spl_state is not None:
                self.ui.spl_hor_src_data_params.restoreState(spl_state)
            else:
                w = (available_height - 50) // 3
                self.ui.spl_hor_src_data_params.setSizes((w, w, w))

            # Three way splitter for left side panels in pipeline builder
            spl_state = settings_.value("spl_hor_pb_left", None)
            if spl_state is not None:
                self.ui.spl_hor_pb_left.restoreState(spl_state)
            else:
                h = (available_height - 50) // 5
                self.ui.spl_hor_pb_left.setSizes((h * 1, h * 1, h * 2))

            # Data editor splitters
            spl_state = settings_.value("ui.spl_de_left", None)
            if spl_state is not None:
                self.ui.spl_de_left.restoreState(spl_state)
            else:
                w = (available_width - 50) // 5
                self.ui.spl_de_left.setSizes((w, w * 4))

            spl_state = settings_.value("spl_de_right", None)
            if spl_state is not None:
                self.ui.spl_de_right.restoreState(spl_state)
            else:
                w = (available_width - 50) // 5
                self.ui.spl_de_right.setSizes((w * 4, w))

            spl_state = settings_.value("spl_de_hor", None)
            if spl_state is not None:
                self.ui.spl_de_hor.restoreState(spl_state)
            else:
                h = (available_height - 50) // 5
                self.ui.spl_de_hor.setSizes((h * 4, h))

            self.ui.selected_main_tab = settings_.value("global_tab_name", "")
            self.ui.tw_tool_box.setCurrentIndex(
                int(settings_.value("toolbox_tab_index", 0))
            )

            for k, v in ipso_folders.dynamic.items():
                ipso_folders.add_dynamic(
                    k, settings_.value(k, v.get_path(force_creation=False))
                )

            # Fill main menu
            self.ui.actionEnable_annotations.setChecked(
                settings_.value("actionEnable_annotations", "false").lower() == "true"
            )
            self.ui.actionEnable_log.setChecked(
                settings_.value("actionEnable_log", "true").lower() == "true"
            )
            self.multithread = settings_.value("multithread", "true").lower() == "true"
            self.ui.action_use_multithreading.setChecked(self.multithread)
            self.use_pipeline_cache = (
                settings_.value("use_pipeline_cache", "true").lower() == "true"
            )

            # Retrieve last active database
            self.global_progress_update(
                step=60,
                total=100,
                process_events=True,
                msg="Restore database",
                force_update=True,
            )
            last_db = dbb.DbInfo(
                display_name=settings_.value("current_data_base/display_name", ""),
                db_qualified_name=settings_.value(
                    "current_data_base/db_qualified_name", ""
                ),
                src_files_path=settings_.value("current_data_base/src_files_path", ""),
                dbms=settings_.value("current_data_base/dbms", ""),
                target=settings_.value("current_data_base/target", ""),
                db_folder_name=settings_.value("current_data_base/db_folder_name", ""),
            )
            if last_db.db_qualified_name == "":
                last_db = None
            elif (
                last_db.dbms == "sqlite"
                and last_db.db_qualified_name != ":memory:"
                and not os.path.isfile(os.path.join(last_db.db_full_file_path))
            ):
                last_db = None

            # Load saved databases
            settings_.beginGroup(dbi.DbType.CUSTOM_DB.name)
            for ldb_name in settings_.childGroups():
                db_info = dbb.DbInfo(
                    display_name=settings_.value(f"{ldb_name}/display_name", ""),
                    db_qualified_name=settings_.value(
                        f"{ldb_name}/db_qualified_name", ""
                    ),
                    src_files_path=settings_.value(f"{ldb_name}/src_files_path", ""),
                    dbms=settings_.value(f"{ldb_name}/dbms", ""),
                    target=settings_.value(f"{ldb_name}/target", ""),
                    db_folder_name=settings_.value(f"{ldb_name}/db_folder_name", ""),
                )
                # Remove from databases if dead link
                if db_info.dbms == "sqlite" and not os.path.isfile(
                    db_info.db_full_file_path
                ):
                    continue
                self.image_databases[dbi.DbType.CUSTOM_DB].append(db_info)
            settings_.endGroup()

            # Add default postgress databases if missing and enabled
            for dbt in dbi.DbType:
                if dbi.available_db_dicts[dbt]:
                    self.image_databases[dbt] = dbi.available_db_dicts[dbt]

            if (
                last_db is not None
                and last_db.db_qualified_name
                and last_db.db_qualified_name != ":memory:"
            ):
                for db in [n for v in self.image_databases.values() for n in v]:
                    if db.db_qualified_name == last_db.db_qualified_name:
                        break
                else:
                    self.image_databases[dbi.DbType.CUSTOM_DB].append(last_db)

            # Load data bases
            self.build_database_menu(
                selected="" if last_db is None else last_db.db_qualified_name
            )

            # Load recent folders
            i = 0
            while settings_.contains(f"recent_folders/{i}"):
                self.recent_folders.append(settings_.value(f"recent_folders/{i}", ""))
                i += 1
            self.recent_folders = [fld for fld in self.recent_folders if fld]
            self.build_recent_folders_menu()

            # Restore database
            if last_db is not None:
                ldb = dbf.db_info_to_database(last_db)
                if isinstance(ldb, str):
                    logger.exception(f"Unable to restore database: {ldb}")
                else:
                    self.current_database = ldb

            # Fill check options
            self.global_progress_update(
                step=70,
                total=100,
                process_events=True,
                msg="Restore check states",
                force_update=True,
            )
            self.ui.chk_experiment.setChecked(
                settings_.value(
                    "checkbox_status/experiment_checkbox_state", "true"
                ).lower()
                == "true"
            )
            self.ui.chk_plant.setChecked(
                settings_.value("checkbox_status/plant_checkbox_state", "true").lower()
                == "true"
            )
            self.ui.chk_date.setChecked(
                settings_.value("checkbox_status/date_checkbox_state", "true").lower()
                == "true"
            )
            self.ui.chk_camera.setChecked(
                settings_.value("checkbox_status/camera_checkbox_state", "true").lower()
                == "true"
            )
            self.ui.chk_view_option.setChecked(
                settings_.value(
                    "checkbox_status/view_option_checkbox_state", "true"
                ).lower()
                == "true"
            )
            self.ui.chk_time.setChecked(
                settings_.value("checkbox_status/time_checkbox_state", "true").lower()
                == "true"
            )

            # Fill batch options
            self.ui.cb_batch_mode.setCurrentIndex(
                int(
                    settings_.value(
                        "batch_configuration/mode", self.ui.cb_batch_mode.currentIndex()
                    )
                )
            )
            self.ui.sb_batch_count.setValue(
                int(
                    settings_.value(
                        "batch_configuration/skim_count", self.ui.sb_batch_count.value()
                    )
                )
            )

            # Fill image list
            self.global_progress_update(
                step=80,
                total=100,
                process_events=True,
                msg="Restore image list",
                force_update=True,
            )
            file_path_ = settings_.value("last_image_browser_state", "")
            if file_path_ and os.path.isfile(file_path_):
                self.init_image_browser(pd.read_csv(file_path_))

            # Fill process modes
            lst = self._ip_tools_holder.ipt_list
            target_process = str(settings_.value("process_Mode", "Default"))
            for i, ip_t in enumerate(lst):
                if ip_t.name.lower() == target_process.lower():
                    process_name = ip_t.name
            else:
                process_name = ""

            if not process_name:
                process_name = lst[0].name
            self.select_tool_from_name(process_name)

            # Fill pipeline processor
            self.ui.le_pp_output_folder.setText(
                settings_.value(
                    "pipeline_processor/output_folder",
                    self.ui.le_pp_output_folder.text(),
                )
            )
            self.ui.cb_pp_overwrite.setChecked(
                settings_.value("pipeline_processor/overwrite", "true").lower() == "true"
            )
            self.ui.cb_pp_generate_series_id.setChecked(
                settings_.value("pipeline_processor/generate_series_id", "true").lower()
                == "true"
            )
            self.ui.cb_pp_append_experience_name.setChecked(
                settings_.value(
                    "pipeline_processor/append_experience_name", "true"
                ).lower()
                == "true"
            )
            self.ui.cb_pp_append_timestamp_to_output_folder.setChecked(
                settings_.value("pipeline_processor/append_timestamp", "true").lower()
                == "true"
            )
            self.ui.sl_pp_thread_count.setValue(
                int(
                    settings_.value(
                        "pipeline_processor/thread_count",
                        self.ui.sl_pp_thread_count.value(),
                    )
                )
            )
            self.pp_thread_pool.setMaxThreadCount(self.ui.sl_pp_thread_count.value())
            self.ui.sp_pp_time_delta.setValue(
                int(
                    settings_.value(
                        "pipeline_processor/sp_pp_time_delta",
                        self.ui.sp_pp_time_delta.value(),
                    )
                )
            )

            # Fill selected plant
            self.global_progress_update(
                step=90,
                total=100,
                process_events=True,
                msg="Restore selected plant",
                force_update=True,
            )
            self.select_image_from_luid(settings_.value("selected_plant_luid", ""))

            # Load last pipeline
            self.last_pipeline_path = settings_.value("last_pipeline_path", "")
            if os.path.isfile(self.last_pipeline_path):
                try:
                    self.pipeline = LoosePipeline.load(file_name=self.last_pipeline_path)
                except Exception as e:
                    logger.exception(f'Unable to load pipeline: "{repr(e)}"')
                    self.last_pipeline_path = ""

        except Exception as e:
            logger.exception(f"Failed to load settings because: {repr(e)}")
            res = False
        else:
            self.update_feedback(
                status_message="Settings loaded, ready to play",
                use_status_as_log=True,
                log_level=logging.INFO,
            )
        finally:
            self.unlock_settings()
            self._initializing = False
        return res

    def save_settings(self):
        settings_ = self.lock_settings()
        try:
            settings_.setValue("settings_exists", True)

            # Geometry
            settings_.setValue("main_geometry", self.saveGeometry())
            settings_.setValue("main_state", self.saveState())
            settings_.setValue("dimension", self.geometry())
            settings_.setValue("spl_pb_ver_main", self.ui.spl_pb_ver_main.saveState())
            settings_.setValue("spl_hor_pb_left", self.ui.spl_hor_pb_left.saveState())
            settings_.setValue(
                "ui.spl_ver_src_res_data",
                self.ui.spl_ver_src_res_data.saveState(),
            )
            settings_.setValue("ui.spl_de_left", self.ui.spl_de_left.saveState())
            settings_.setValue("spl_de_right", self.ui.spl_de_right.saveState())
            settings_.setValue("spl_de_hor", self.ui.spl_de_hor.saveState())

            settings_.setValue("global_tab_name", self.ui.selected_main_tab)
            settings_.setValue("toolbox_tab_index", self.ui.tw_tool_box.currentIndex())
            settings_.setValue(
                "actionEnable_annotations",
                self.ui.actionEnable_annotations.isChecked(),
            )
            settings_.setValue("actionEnable_log", self.ui.actionEnable_log.isChecked())
            settings_.setValue("process_mode", self.current_tool.name)
            settings_.setValue("selected_style", self._selected_style)
            settings_.setValue("selected_theme", self._selected_theme)
            settings_.setValue(
                "multithread",
                self.ui.action_use_multithreading.isChecked(),
            )
            settings_.setValue("log_geometry", self.ui.dk_log.geometry())

            for k, v in ipso_folders.dynamic.items():
                settings_.setValue(k, v.get_path(force_creation=False))

            settings_.beginGroup("checkbox_status")
            settings_.setValue(
                "experiment_checkbox_state",
                self.ui.chk_experiment.isChecked(),
            )
            settings_.setValue("plant_checkbox_state", self.ui.chk_plant.isChecked())
            settings_.setValue("date_checkbox_state", self.ui.chk_date.isChecked())
            settings_.setValue("camera_checkbox_state", self.ui.chk_camera.isChecked())
            settings_.setValue(
                "view_option_checkbox_state",
                self.ui.chk_view_option.isChecked(),
            )
            settings_.setValue("time_checkbox_state", self.ui.chk_time.isChecked())
            settings_.endGroup()

            settings_.beginGroup("batch_configuration")
            settings_.setValue("mode", self.ui.cb_batch_mode.currentIndex())
            settings_.setValue("skim_count", self.ui.sb_batch_count.value())
            settings_.endGroup()

            settings_.setValue(
                "selected_plant_luid",
                self._src_image_wrapper.luid
                if self._src_image_wrapper is not None
                else "",
            )

            if self.current_database is not None:
                settings_.beginGroup("current_data_base")
                settings_.setValue("display_name", self.current_database.display_name)
                settings_.setValue(
                    "db_qualified_name",
                    self.current_database.db_qualified_name,
                )
                settings_.setValue("src_files_path", self.current_database.src_files_path)
                settings_.setValue("dbms", self.current_database.dbms)
                settings_.setValue("target", self.current_database.target)
                settings_.setValue("db_folder_name", self.current_database.db_folder_name)
                settings_.endGroup()
            else:
                settings_.remove("current_data_base")

            settings_.remove("sqlite_databases")
            for ldb in self.image_databases[dbi.DbType.CUSTOM_DB]:
                settings_.beginGroup(f"{dbi.DbType.CUSTOM_DB.name}/{ldb.display_name}")
                settings_.setValue("display_name", ldb.display_name)
                settings_.setValue("db_qualified_name", ldb.db_qualified_name)
                settings_.setValue("src_files_path", ldb.src_files_path)
                settings_.setValue("dbms", ldb.dbms)
                settings_.setValue("target", ldb.target)
                settings_.setValue("db_folder_name", ldb.db_folder_name)
                settings_.endGroup()

            settings_.beginGroup("recent_folders")
            for i, fld in enumerate(self.recent_folders):
                settings_.setValue(str(i), fld)
            settings_.endGroup()

            settings_.beginGroup("pipeline_processor")
            settings_.setValue("output_folder", self.ui.le_pp_output_folder.text())
            settings_.setValue("overwrite", self.ui.cb_pp_overwrite.isChecked())
            settings_.setValue(
                "generate_series_id",
                self.ui.cb_pp_generate_series_id.isChecked(),
            )
            settings_.setValue(
                "append_experience_name",
                self.ui.cb_pp_append_experience_name.isChecked(),
            )
            settings_.setValue(
                "append_timestamp",
                self.ui.cb_pp_append_timestamp_to_output_folder.isChecked(),
            )
            settings_.setValue("thread_count", self.ui.sl_pp_thread_count.value())
            settings_.setValue("sp_pp_time_delta", self.ui.sp_pp_time_delta.value())
            settings_.endGroup()

            model = self.get_image_model()
            if model is not None and model.rowCount() > 0:
                if model.rowCount() > 100000:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setWindowTitle("Too many items in image list")
                    msg.setText(
                        f"Too many items in image list: {model.rowCount()}\n"
                        f"Do you really want to save the list?"
                    )
                    msg.setDetailedText(
                        "It may take really long to save and later load all this data"
                    )
                    msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                    save_lst_ = msg.exec_() == QMessageBox.Yes
                else:
                    save_lst_ = True
            else:
                save_lst_ = False

            if os.path.isfile(self.last_pipeline_path):
                settings_.setValue("last_pipeline_path", self.last_pipeline_path)
            else:
                settings_.setValue("last_pipeline_path", "")

            if save_lst_ is True:
                model.images.to_csv(
                    os.path.join(
                        ipso_folders.get_path("saved_data", force_creation=True),
                        "last_image_browser_state.csv",
                    ),
                    index=False,
                )
                settings_.setValue(
                    "last_image_browser_state",
                    os.path.join(
                        ipso_folders.get_path("saved_data", force_creation=False),
                        "last_image_browser_state.csv",
                    ),
                )
            else:
                settings_.setValue("last_image_browser_state", "")

        except Exception as e:
            logger.exception(f"Failed to save settings because: {repr(e)}")
            res = False
        else:
            res = True
        finally:
            self.unlock_settings()
        return res

    @staticmethod
    def close_application():
        sys.exit()

    def closeEvent(self, *args, **kwargs):
        self.save_settings()
        super(QtWidgets.QMainWindow, self).closeEvent(*args, **kwargs)

    def showEvent(self, a0: QShowEvent):
        if self._splash is not None:
            self._pg_splash.setValue(100)
            self._lbl_splash_text.setText("Almost Ready")
            self._splash.finish(self)
            self._splash = None
            self._pg_splash = None

    def update_feedback(
        self,
        status_message: str = "",
        log_message: Any = None,
        use_status_as_log: bool = False,
        collect_garbage: bool = True,
        log_level: int = 20,
        target_logger=logger,
    ):

        # Update status bar
        if status_message:
            self._status_label.setText(status_message)
            if log_message is None:
                eh.log_data(
                    log_msg=f"(Status) {status_message}",
                    log_level=log_level,
                    target_logger=target_logger,
                )
        else:
            self._status_label.setText("")

        # Update log
        if self.ui.actionEnable_log.isChecked():
            if log_message is not None and isinstance(log_message, str):
                eh.log_data(
                    log_msg=log_message,
                    log_level=log_level,
                    target_logger=target_logger,
                )
            elif use_status_as_log and status_message:
                eh.log_data(
                    log_msg=status_message,
                    log_level=log_level,
                    target_logger=target_logger,
                )
        process: psutil.Process = psutil.Process(os.getpid())
        if (
            not self._collecting_garbage
            and (timer() - self._last_garbage_collected > 60)
            and collect_garbage
            and (process.memory_percent() > 30)
        ):
            self._collecting_garbage = True
            try:
                old_mm_percent = process.memory_percent()
                target_logger.info(
                    "Collecting garbage, memory used {process.me} ({old_mm_percent}%)..."
                )
                self.update_feedback(
                    status_message="Collecting garbage...",
                    collect_garbage=False,
                    log_level=logging.INFO,
                )
                gc.collect()
                self.update_feedback(
                    status_message="Garbage collected",
                    log_message=f"""Garbage collection freed {old_mm_percent - process.memory_percent():02.2f}% memory""",
                    log_level=logging.INFO,
                    collect_garbage=False,
                )
            except Exception as e:
                target_logger.exception(f"Unable to collect garbage: {repr(e)}")
            finally:
                self._collecting_garbage = False
                self._last_garbage_collected = timer()

    def on_action_about_form(self):
        about_frm = QDialog(self)
        about_frm.ui = AboutDialog()
        about_frm.ui.setupUi(about_frm)
        about_frm.ui.set_version()
        about_frm.ui.set_authors()
        about_frm.ui.set_copyright()
        about_frm.ui.set_used_packages()

        about_frm.show()

    def on_action_new_tool(self):
        ntd = NewToolDialog(self)
        ntd.show()

    def on_action_show_read_me(self):
        webbrowser.open("https://github.com/tpmp-inra/ipso_phen/blob/master/readme.md")

    def on_action_show_documentation(self):
        webbrowser.open("https://ipso-phen.readthedocs.io/en/latest/")

    def build_tool_documentation(self, tool, tool_name):
        with open(os.path.join("docs", f"{tool_name}.md"), "w") as f:
            f.write(f"# {tool.name}\n\n")
            f.write("## Description\n\n")
            f.write(tool.description.replace("\n", "  \n") + "\n")
            f.write(f"**Real time**: {str(tool.real_time)}\n\n")
            f.write("## Usage\n\n")
            for use_case in tool.use_case:
                f.write(f"- **{use_case}**: {ipc.tool_family_hints[use_case]}\n")
            f.write("\n## Parameters\n\n")
            if tool.has_input:
                for p in tool.gizmos:
                    if p.is_input:
                        f.write(
                            f"- {p.desc} ({p.name}): {p.hint} (default: {p.default_value})\n"
                        )
            f.write("\n")
            f.write("## Example\n\n")
            f.write("### Source\n\n")
            f.write(f"![Source image](images/{self._src_image_wrapper.name}.jpg)\n")
            if not os.path.isfile(
                os.path.join(".", "docs", "images", f"{self._src_image_wrapper.name}.jpg")
            ):
                shutil.copyfile(
                    src=self._src_image_wrapper.file_path,
                    dst=os.path.join(
                        ".", "docs", "images", f"{self._src_image_wrapper.name}.jpg"
                    ),
                )
            f.write("\n")
            f.write("### Parameters/Code\n\n")
            f.write("Default values are not needed when calling function\n\n")
            f.write("```python\n")
            f.write(
                call_ipt_code(
                    ipt=self.current_tool,
                    file_name=f"{self._src_image_wrapper.name}.jpg",
                )
            )
            f.write("```\n\n")
            if hasattr(tool, "data_dict"):
                f.write("### Result image\n\n")
            else:
                f.write("### Result\n\n")
            self.save_image(
                image_data=self.ui.cb_available_outputs.itemData(
                    self.ui.cb_available_outputs.currentIndex()
                ),
                text=tool_name,
                image_path="./docs/images/",
            )
            f.write(f"![Result image](images/{tool_name}.jpg)\n")
            if hasattr(tool, "data_dict"):
                f.write("\n### Result data\n\n")
                f.write("|         key         |        Value        |\n")
                f.write("|:-------------------:|:-------------------:|\n")
                for r in range(self.ui.tw_script_sim_output.rowCount()):
                    f.write(
                        f"|{self.ui.tw_script_sim_output.item(r, 0).text()}|{self.ui.tw_script_sim_output.item(r, 1).text()}|\n"
                    )

    def on_action_build_tool_documentation(self):
        self.build_tool_documentation(
            tool=self.current_tool,
            tool_name=f'ipt_{self.current_tool.name.replace(" ", "_")}',
        )

    def on_action_build_test_files(self):
        tmp_ip_holder = IptHolder()
        self.update_feedback(
            status_message="Building test scripts",
            log_message="Building test scripts",
            log_level=logging.INFO,
        )
        tmp_ip_holder.build_test_files(log_callback=self.update_feedback)
        self.update_feedback(
            status_message="Test scripts built",
            log_message="Test scripts built",
            log_level=logging.INFO,
        )

    def on_action_show_log(self):
        self.ui.dk_log.setVisible(not self.ui.dk_log.isVisible())

    def on_log_visibility_changed(self, visible):
        self.ui.action_show_log.setChecked(visible)

    def on_log_received(self, line: str):
        if "ERROR" in line or "WARNING" in line or "CRITICAL" in line:
            if not self.ui.dk_log.isVisible():
                self.ui.dk_log.setVisible(True)
            self.ui.dk_log.setWindowTitle("Log: last error - " + line)
        if hasattr(self, "_status_label"):
            self._status_label.setText("Last log entry: " + line)
            self.process_events()

    def on_action_build_ipso_phen_documentation(self):
        # Build tools overview
        with open(os.path.join("docs", "tools.md"), "w", encoding="utf8") as f:
            f.write("# Tools overview by category\n\n")
            f.write("!!! info\n")
            f.write("    Some tools may be in more than one category  \n")
            lst = self._ip_tools_holder.ipt_list
            for use_case in self._ip_tools_holder.use_cases:
                if use_case in ["none", WIP_CASE]:
                    continue
                f.write(f"## {use_case}\n\n")
                f.write(ipc.tool_family_hints[use_case] + "\n\n")
                op_lst = self._ip_tools_holder.list_by_use_case(use_case)
                for ipt_ in op_lst:
                    tool_name = f'ipt_{ipt_.name.replace(" ", "_")}'
                    if os.path.isfile(os.path.join("docs", f"{tool_name}.md")):
                        f.write(f"### {ipt_.name}\n\n")
                        f.write(ipt_.description.replace("\n", "  \n") + "  \n")
                        f.write(f"Details [here]({tool_name}.md)\n\n")
            logger.info("Built documentation index file")

        # Fill TOC
        with open(os.path.join("mkdocs.yml"), "w", encoding="utf8") as f:
            f.write("site_name: IPSO Phen documentation\n")
            f.write("site_description: UI for plant phenotyping\n")
            f.write("site_author: Felicià Antoni Maviane Macia\n")
            f.write("repo_url: https://github.com/tpmp-inra/ipso_phen\n")
            f.write("copyright: Copyright 2018-2020, INRA\n")
            f.write("theme:\n")
            f.write("  name: 'material'\n")
            f.write("markdown_extensions:\n")
            f.write("  - admonition\n")
            f.write("  - codehilite:\n")
            f.write("      linenums: true\n")
            f.write("\n")
            f.write("nav:\n")
            f.write("- Home: index.md\n")
            f.write("- Installation: installation.md\n")
            f.write("- First steps: first_steps.md\n")
            f.write("- Command line interface: command_line.md\n")
            f.write("- User interface: user_interface.md\n")
            f.write("- Tools:\n")
            f.write("  - Overview (by category): tools.md\n")
            f.write("  - Details (alphabetical):\n")
            for tool_doc in glob.glob("./docs/ipt_*.md", recursive=False):
                td = os.path.basename(tool_doc)
                text_ = td.replace("ipt_", "").replace("_", " ").replace(".md", "")
                link_ = td
                f.write(f"    - {text_}: {link_}\n")
            f.write("- Testing: testing.md\n")
            f.write("- Grid search: grid_search.md\n")
            f.write("- Pipelines: pipelines.md\n")
            f.write("- Pipeline processor: pipeline_processor.md\n")
            f.write("- Samples: samples.md\n")
            f.write("- Advanced features:\n")
            f.write("  - Creating custom tools: custom_tools.md\n")
            f.write("  - Class pipelines: class_pipelines.md\n")
            f.write("  - File handlers: file_handlers.md")

    def accept(self):
        pass

    def reject(self):
        pass

    def on_tv_pp_view_selection_changed(self, selected, deselected):
        model: PipelineModel = self.ui.tv_pp_view.model()
        if model is not None and len(selected.indexes()) > 0:
            for index in selected.indexes():
                current_node = index
                break
            else:
                current_node = None

            if current_node is not None:
                parent = current_node.parent().internalPointer()
                if parent is not None:
                    nd = model.get_item(current_node).node_data
                    if isinstance(nd, ModuleNode) or isinstance(nd, GroupNode):
                        self.ui.bt_pp_delete.setEnabled(True)
                        self.ui.bt_pp_up.setEnabled(current_node.row() > 0)
                        self.ui.bt_pp_down.setEnabled(
                            current_node.row() < len(parent.children) - 1
                        )
                        return

        self.ui.bt_pp_up.setEnabled(False)
        self.ui.bt_pp_down.setEnabled(False)
        self.ui.bt_pp_delete.setEnabled(False)

    def pp_callback(self, result, msg, data, current_step, total_steps):
        if result == "INFO":
            if msg:
                self.update_feedback(
                    status_message=msg, log_message=msg, log_level=logging.INFO
                )
            if isinstance(data, (GroupNode, ModuleNode)):
                display_name = (
                    f"Pipeline output for {data.root.parent.wrapper.luid}"
                    if data.is_root
                    else data.name
                )
                output_dict = {
                    "plant_name": data.root.parent.wrapper.plant,
                    "name": display_name,
                    "image": data.get_feedback_image(data.last_result),
                    "data": data.last_result.get("data", {}),
                    "luid": data.root.parent.wrapper.luid,
                }
                if isinstance(data, ModuleNode):
                    output_dict["params"] = data.tool.params_to_dict()
                self.ui.cb_available_outputs.addItem(
                    display_name,
                    output_dict,
                )
                self.ui.cb_available_outputs.setCurrentIndex(
                    self.ui.cb_available_outputs.count() - 1
                )
            elif isinstance(data, BaseImageProcessor):
                self.add_images_to_viewer(
                    wrapper=data,
                    data_dict=data.csv_data_holder.data_list,
                    avoid_duplicates=False,
                )
            elif isinstance(data, dict):
                self.ui.cb_available_outputs.addItem(data["name"], data)
                self.ui.cb_available_outputs.setCurrentIndex(
                    self.ui.cb_available_outputs.count() - 1
                )
        elif result == "ERROR":
            self.update_feedback(
                status_message=msg, log_message=msg, log_level=logging.ERROR
            )
        elif result == "WARNING":
            self.update_feedback(
                status_message=msg, log_message=msg, log_level=logging.WARNING
            )
        elif result == "GRID_SEARCH_START":
            self.update_feedback(
                status_message=f"Starting grid search with {total_steps} configurations",
                use_status_as_log=True,
            )
        elif result == "GRID_SEARCH_OK":
            self.ui.cb_available_outputs.addItem(data["name"], data)
            self.ui.cb_available_outputs.setCurrentIndex(
                self.ui.cb_available_outputs.count() - 1
            )
        elif result == "GRID_SEARCH_NOK":
            self.update_feedback(status_message=msg, use_status_as_log=True)
        elif result == "GRID_SEARCH_END":
            self.update_feedback(
                status_message="Ending grid search", use_status_as_log=True
            )
        else:
            logger.exception(f'Unknown result: "Unknown pipeline result {result}"')

        if current_step >= 0 and total_steps >= 0:
            if "GRID_SEARCH" in result:
                self.update_thread_counts(
                    thread_step=current_step, thread_total=total_steps, thread_waiting=0
                )
            else:
                self.ui.pb_pp_progress.setValue(
                    round((min(current_step, total_steps)) / total_steps * 100)
                )
        if not self.multithread:
            self.process_events()

    def pp_set_spanning(self):
        model: PipelineModel = self.ui.tv_pp_view.model()
        if model is not None:
            for index in model.iter_items(root=None):
                self.ui.tv_pp_view.setFirstColumnSpanned(
                    index.row(),
                    index.parent(),
                    not hasattr(index.internalPointer(), "run_button"),
                )

    def on_pp_data_changed(self, topleft, bottomright, roles):
        self.pp_set_spanning()

    def on_bt_pp_new(self):
        pp = LoosePipeline(name="None", description="Double click to edit description")
        self.pipeline = pp

    def on_bt_pp_load(self):
        file_name_ = QFileDialog.getOpenFileName(
            parent=self,
            caption="Load pipeline",
            dir=ipso_folders.get_path("pipeline"),
            filter=_PIPELINE_FILE_FILTER,
        )[0]
        if file_name_:
            ipso_folders.set_path(
                "pipeline", os.path.join(os.path.dirname(file_name_), "")
            )
            try:
                self.pipeline = LoosePipeline.load(file_name=file_name_)
            except Exception as e:
                logger.exception(f'Unable to load pipeline: "{repr(e)}"')
            else:
                self.last_pipeline_path = file_name_

    def on_bt_pp_save(self):
        file_name_ = QFileDialog.getSaveFileName(
            parent=self,
            caption="Save pipeline",
            dir=ipso_folders.get_path("pipeline"),
            filter=_PIPELINE_FILE_FILTER,
        )[0]
        if file_name_:
            ipso_folders.set_path(
                "pipeline", os.path.join(os.path.dirname(file_name_), "")
            )
            if not file_name_.lower().endswith(".json"):
                file_name_ += ".json"
            res = self.pipeline.save(file_name_)
            if res:
                self.update_feedback(
                    status_message=f'Saved pipeline to: "{file_name_}"',
                    use_status_as_log=True,
                )
                self.last_pipeline_path = file_name_
            else:
                self.update_feedback(
                    status_message="Failed to save pipline, cf. log for more details",
                    log_message="Failed to save pipline, unknown error",
                )

    def on_bt_pp_up(self):
        model: PipelineModel = self.ui.tv_pp_view.model()
        if model is not None:
            model.move_up(selected_items=self.ui.tv_pp_view.selectedIndexes())

    def on_bt_pp_down(self):
        model: PipelineModel = self.ui.tv_pp_view.model()
        if model is not None:
            model.move_down(selected_items=self.ui.tv_pp_view.selectedIndexes())

    def on_bt_pp_delete(self):
        model: PipelineModel = self.ui.tv_pp_view.model()
        if model is not None and self.ui.tv_pp_view.selectedIndexes():
            selected_node = self.ui.tv_pp_view.selectedIndexes()[0]
            model.removeRow(selected_node.row(), selected_node.parent())

    def on_bt_pp_add_tool(self, q):
        # Get model
        model: PipelineModel = self.ui.tv_pp_view.model()
        if model is None:
            self.pipeline = LoosePipeline(
                name="None",
                description="Double click to edit description",
            )
            model: PipelineModel = self.ui.tv_pp_view.model()
        # Get menu item text
        if hasattr(self.sender(), "text"):
            text = self.sender().text()
        else:
            text = q.text()
        # Get parent node
        indexes = self.ui.tv_pp_view.selectedIndexes()
        if indexes:
            index = indexes[0]
        else:
            index = model.createIndex(2, 0, model.rootNodes[2])
        if index.parent() is None:
            if index.row() != 2:
                index = model.createIndex(2, 0, model.rootNodes[2])
        else:
            if not isinstance(index.internalPointer().node_data, GroupNode):
                index = index.parent()
                while not isinstance(index.internalPointer().node_data, GroupNode):
                    index = index.parent()
        self.ui.tv_pp_view.selectionModel().selection().select(index, index)
        self.ui.tv_pp_view.expand(index)

        if text == "Default empty group":
            added_index = model.add_group(selected_items=index)
            self.ui.tv_pp_view.expand(added_index.parent())
        elif text == "Visualization helpers":
            added_index = model.add_group(
                selected_items=index,
                merge_mode=ipc.MERGE_MODE_NONE,
                name=text,
            )
            tool = self.find_tool_by_name("Visualization helper")
            if tool is not None:
                model.add_module(
                    selected_items=added_index,
                    module=tool.copy(copy_wrapper=False),
                    enabled=True,
                )
        elif text == "Fix exposure":
            added_index = model.add_group(
                selected_items=index,
                merge_mode=ipc.MERGE_MODE_CHAIN,
                name=text,
            )
            tool = self.find_tool_by_name("Simple white balance")
            if tool is not None:
                model.add_module(
                    selected_items=added_index,
                    module=tool.copy(copy_wrapper=False),
                    enabled=True,
                )
            tool = self.find_tool_by_name("Image transformations")
            if tool is not None:
                model.add_module(
                    selected_items=added_index,
                    module=tool.copy(copy_wrapper=False),
                    enabled=True,
                )
            self.ui.tv_pp_view.expand(added_index)
        elif text == "Pre process image":
            added_index = model.add_group(
                selected_items=index,
                merge_mode=ipc.MERGE_MODE_CHAIN,
                name=text,
            )
            tool = self.find_tool_by_name("Check exposure")
            if tool is not None:
                model.add_module(
                    selected_items=added_index,
                    module=tool.copy(copy_wrapper=False),
                    enabled=True,
                )
            tool = self.find_tool_by_name("Partial posterizer")
            if tool is not None:
                model.add_module(
                    selected_items=added_index,
                    module=tool.copy(copy_wrapper=False),
                    enabled=True,
                )
            self.ui.tv_pp_view.expand(added_index)
        elif text == "Threshold":
            added_index = model.add_group(
                selected_items=index,
                merge_mode=ipc.MERGE_MODE_AND,
                name=text,
            )
            tool = self.find_tool_by_name("Multi range threshold")
            if tool is not None:
                model.add_module(
                    selected_items=added_index,
                    module=tool.copy(copy_wrapper=False),
                    enabled=True,
                )
            self.ui.tv_pp_view.expand(added_index)
        elif text == "Mask cleanup":
            added_index = model.add_group(
                selected_items=index,
                merge_mode=ipc.MERGE_MODE_CHAIN,
                name=text,
            )
            tool = self.find_tool_by_name("Keep linked Contours")
            if tool is not None:
                model.add_module(
                    selected_items=added_index,
                    module=tool.copy(copy_wrapper=False),
                    enabled=True,
                )
            self.ui.tv_pp_view.expand(added_index)
        elif text == "Feature extraction":
            added_index = model.add_group(
                selected_items=index,
                merge_mode=ipc.MERGE_MODE_NONE,
                name=text,
            )
            tool = self.find_tool_by_name("Observation data")
            if tool is not None:
                model.add_module(
                    selected_items=added_index,
                    module=tool.copy(copy_wrapper=False),
                    enabled=True,
                )
            tool = self.find_tool_by_name("Analyze object")
            if tool is not None:
                model.add_module(
                    selected_items=added_index,
                    module=tool.copy(copy_wrapper=False),
                    enabled=True,
                )
            tool = self.find_tool_by_name("Analyze color")
            if tool is not None:
                model.add_module(
                    selected_items=added_index,
                    module=tool.copy(copy_wrapper=False),
                    enabled=True,
                )
            tool = self.find_tool_by_name("Analyze bound")
            if tool is not None:
                model.add_module(
                    selected_items=added_index,
                    module=tool.copy(copy_wrapper=False),
                    enabled=True,
                )
            tool = self.find_tool_by_name("Analyze chlorophyll")
            if tool is not None:
                model.add_module(
                    selected_items=added_index,
                    module=tool.copy(copy_wrapper=False),
                    enabled=True,
                )
            self.ui.tv_pp_view.expand(added_index)
        else:
            tool = self.find_tool_by_name(text)
            if tool is None:
                self.update_feedback(
                    status_message=f'Unable to add "{text}" to pipeline',
                    use_status_as_log=True,
                )
                return
            else:
                added_index = model.add_module(
                    selected_items=index,
                    module=tool.copy(copy_wrapper=False),
                    enabled=True,
                )
            self.ui.tv_pp_view.expand(added_index.parent())

    def on_bt_pp_run(self):
        self.run_process(wrapper=self._src_image_wrapper)

    def on_bt_pp_invalidate(self):
        pp = self.pipeline
        if pp is not None:
            self.pipeline.invalidate()
            self.update_feedback(
                status_message="Cleared pipeline cache", use_status_as_log=True
            )

    def on_bt_pp_reset(self):
        self.ui.le_pp_output_folder.setText(
            ipso_folders.get_path(
                "pp_output",
                force_creation=False,
            )
        )
        self.on_rb_pp_default_process()
        self.ui.cb_pp_overwrite.setChecked(False)
        self.ui.cb_pp_generate_series_id.setChecked(False)
        self.ui.cb_pp_append_experience_name.setChecked(True)
        self.ui.cb_pp_append_timestamp_to_output_folder.setChecked(False)
        self.ui.sl_pp_thread_count.setValue(0)
        if self._src_image_wrapper is not None:
            self.ui.edt_csv_file_name.setText(
                f"{self._src_image_wrapper.experiment}_raw_data"
            )
        else:
            self.ui.edt_csv_file_name.setText("unknown_experiment_raw_data")
        self.ui.sp_pp_time_delta.setValue(20)
        self._custom_csv_name = False

    def _update_pp_pipeline_state(self, default_process: bool, pipeline: bool):
        self.ui.rb_pp_default_process.setChecked(default_process)
        self.ui.rb_pp_load_script.setChecked(pipeline)

    def on_rb_pp_default_process(self):
        self._update_pp_pipeline_state(True, False)

    def on_rb_pp_load_script(self):
        if self.pipeline is None:
            self.on_bt_pp_load()
        else:
            self._update_pp_pipeline_state(False, True)

    def on_bt_pp_select_output_folder(self):
        if not os.path.isdir(self.ui.le_pp_output_folder.text()):
            force_directories(self.ui.le_pp_output_folder.text())

        sel_folder = str(
            QFileDialog.getExistingDirectory(
                parent=self,
                caption="Select output folder",
                dir=self.ui.le_pp_output_folder.text(),
            )
        )
        if os.path.isdir(sel_folder):
            self.ui.le_pp_output_folder.setText(sel_folder)

    def do_pp_progress(self, step: int, total: int):
        if threading.current_thread() is not threading.main_thread():
            logger.warning("do_pp_progress: NOT MAIN THREAD")
        self.global_progress_update(
            step=step,
            total=total,
            process_events=not self.multithread,
        )

    def do_pp_check_abort(self):
        return self._batch_stop_current

    def do_fp_start(self):
        self.update_feedback(
            status_message="Building CSV files",
            log_message=" --- Building CSV files ---",
            log_level=logging.INFO,
        )

    def do_fp_progress(self, step: int, total: int):
        self.global_progress_update(step, total)

    def do_fp_end(self):
        self.pp_pipeline = None
        self.set_global_enabled_state(new_state=True)
        self.global_progress_stop()
        self.update_feedback(
            status_message="Pipeline mass processing ended",
            log_message="Pipeline mass processing ended",
            log_level=logging.INFO,
        )

    def finalize_pipeline(self):
        rpp = IpsoCsvBuilder(
            # Global emitters
            on_start=self.do_fp_start,
            on_end=self.do_fp_end,
            on_progress=self.do_pp_progress,
            on_feedback_log_object=self.do_thread_feedback_log_object,
            on_feedback_log_str=self.do_thread_feedback_log_str,
            # Callbacks
            check_stop=self.do_pp_check_abort,
            # States
            root_csv_name=self.ui.edt_csv_file_name.text(),
            # Create pipeline
            pipeline=self.pp_pipeline,
        )
        if self.multithread:
            self.thread_pool.start(rpp)
        else:
            rpp.run()

    def do_pp_item_ended(self):
        if threading.current_thread() is not threading.main_thread():
            logger.warning("do_pp_item_ended: NOT MAIN THREAD")

        # Collect garbage if needed
        process: psutil.Process = psutil.Process(os.getpid())
        if (
            not self._collecting_garbage
            and (timer() - self._last_garbage_collected > 60)
            and (process.memory_percent() > 30)
        ):
            self._collecting_garbage = True
            try:
                old_mm_percent = process.memory_percent()
                gc.collect()
                logger.info(
                    f"Garbage collection freed {old_mm_percent - process.memory_percent():02.2f}% memory",
                )
            except Exception as e:
                logger.exception(f"Unable to collect garbage: {repr(e)}")
            finally:
                self._collecting_garbage = False
                self._last_garbage_collected = timer()

        if self._batch_stop_current:
            self.update_feedback(
                status_message="Stopping mass pipeline, please wait...",
                log_message="Stopping mass pipeline (user request), please wait...",
                log_level=logging.INFO,
            )
            self.pp_thread_pool.clear()
            self.pp_thread_pool.waitForDone(-1)
            self.set_global_enabled_state(new_state=True)
            self.global_progress_stop()
            self.update_feedback(
                status_message="Mass pipeline stopped",
                log_message="Mass pipeline stopped",
                log_level=logging.INFO,
            )
        else:
            self.pp_threads_step += 1
            self.global_progress_update(
                self.pp_threads_step,
                self.pp_threads_total,
                process_events=not self.multithread,
            )
            if self.pp_threads_step >= self.pp_threads_total:
                if self.pp_pipeline is not None:
                    self.finalize_pipeline()
                else:
                    self.update_feedback(
                        status_message="Failed to finalize mass processing",
                        log_message="Failed to finalize mass processing",
                        log_level=logging.CRITICAL,
                    )
                    self.set_global_enabled_state(new_state=True)
                    self.global_progress_stop()
                    self.update_feedback(
                        status_message="Pipeline mass processing ended",
                        log_message="Pipeline mass processing ended",
                        log_level=logging.INFO,
                    )

    def do_pp_log_item_event(
        self, item_luid: str, event_kind: str, log_data: str, auto_scroll: bool = True
    ):
        items = self.ui.lw_images_queue.findItems(item_luid, Qt.MatchExactly)
        for item in items:
            tooltip = item.toolTip()
            if log_data:
                tooltip += "\n\n" + str(log_data)
            item.setToolTip(tooltip)
            if event_kind == logging.INFO:
                item.setIcon(QIcon(":/annotation_level/resources/OK.png"))
            elif event_kind == logging.WARNING:
                item.setIcon(QIcon(":/annotation_level/resources/Warning.png"))
            elif event_kind == eh.ERR_LVL_EXCEPTION:
                item.setIcon(QIcon(":/annotation_level/resources/Problem.png"))
            elif event_kind in ["failure", logging.ERROR, logging.CRITICAL]:
                item.setIcon(QIcon(":/annotation_level/resources/Danger.png"))
            elif event_kind == "refresh":
                item.setIcon(QIcon(":/common/resources/Refresh.png"))
            else:
                item.setIcon(QIcon(":/annotation_level/resources/Help.png"))
            if auto_scroll and self.ui.cb_queue_auto_scroll.isChecked():
                self.ui.lw_images_queue.scrollToItem(
                    item, self.ui.lw_images_queue.EnsureVisible
                )
        if not self.multithread:
            self.process_events()

    def do_pp_item_image_ready(self, image):
        if self.ui.chk_pp_show_last_item.isChecked():
            self.gv_last_processed_item.main_image = image
            if not self.multithread:
                self.process_events()

    def do_pp_launching(self, total_count: int):
        if threading.current_thread() is not threading.main_thread():
            logger.warning("do_pp_launching: NOT MAIN THREAD")
        if total_count > 0:
            self.pp_threads_total = total_count
            self.pp_threads_step = 0
            self.update_feedback(
                status_message="Launching threads",
                log_message="--- Launching threads ---",
                log_level=logging.INFO,
            )
        else:
            self.finalize_pipeline()

    def on_pp_starting(self):
        if threading.current_thread() is not threading.main_thread():
            logger.warning(": NOT MAIN THREAD")
        self.update_feedback(
            status_message="Starting mass processor",
            log_message="   --- Starting mass processor ---",
            log_level=logging.INFO,
        )
        self.set_global_enabled_state(new_state=False)
        self.global_progress_start(add_stop_button=True)

    def do_pp_started(self, launch_state):
        if threading.current_thread() is not threading.main_thread():
            logger.warning("do_pp_started: NOT MAIN THREAD")
        if launch_state == "ok":
            self.update_feedback(
                status_message="",
                log_message="   --- All threads launched, terminating launcher thread ---<br>"
                "",
                log_level=logging.INFO,
            )
            self.update_feedback(
                status_message="Processing images",
                log_message="   --- Processing images ---<br>",
                log_level=logging.INFO,
            )
        elif launch_state == "abort":
            self.update_feedback(
                status_message="User stopped mass pipeline processing",
                log_message="User stopped mass pipeline processing",
                log_level=logging.INFO,
            )
            self.global_progress_stop()
            self.set_global_enabled_state(new_state=True)
        elif launch_state == "exception":
            self.update_feedback(
                status_message="Exception while launching mass processing",
                log_message="Exception while launching mass processing",
                log_level=eh.ERR_LVL_EXCEPTION,
            )
            self.global_progress_stop()
            self.set_global_enabled_state(new_state=True)

    def on_bt_pp_start(self):
        self._batch_stop_current = False
        model = self.get_image_model()
        if (model is None) or (model.rowCount() == 0):
            self.update_feedback(
                status_message="Pipeline start: nothing to process",
                log_message="Pipeline start - nothing to process",
                log_level=logging.WARNING,
            )
            return
        self.update_feedback(
            status_message="Starting pipeline mass processing",
            log_message="Starting pipeline mass processing",
            log_level=logging.INFO,
        )
        try:
            self.thread_pool.clear()
            self.thread_pool.waitForDone(-1)

            if self.ui.cb_pp_append_experience_name.isChecked():
                output_folder_ = os.path.join(
                    self.ui.le_pp_output_folder.text(),
                    model.get_cell_data(row_number=0, column_name="Experiment"),
                    "",
                )
            else:
                output_folder_ = os.path.join(self.ui.le_pp_output_folder.text(), "")

            # Collect images
            model.images = model.images.sort_values(
                by=["date_time"],
                axis=0,
                na_position="first",
            )
            image_list_ = list(model.images["FilePath"])

            if self.ui.rb_pp_default_process.isChecked():
                script_ = None
            elif self.ui.rb_pp_load_script.isChecked():
                script_ = self.pipeline.copy()
            else:
                self.update_feedback(
                    status_message="Unknown pipeline mode", use_status_as_log=True
                )
                return

            # self.pp_thread_pool.setMaxThreadCount(self.ui.sl_pp_thread_count.value())

            self.pp_pipeline = PipelineProcessor(
                dst_path=output_folder_,
                overwrite=self.ui.cb_pp_overwrite.isChecked(),
                seed_output=self.ui.cb_pp_append_timestamp_to_output_folder.isChecked(),
                group_by_series=self.ui.cb_pp_generate_series_id.isChecked(),
                store_images=True,
                database=self.current_database.copy(),
            )
            self.pp_pipeline.accepted_files = image_list_
            self.pp_pipeline.script = script_
            if script_ is not None:
                self.pp_pipeline.image_output_path = os.path.join(
                    self.ui.le_pp_output_folder.text(), ""
                )

            rpp = IpsoMassRunner(
                # Global emitters
                on_starting=self.on_pp_starting,
                on_launching=self.do_pp_launching,
                on_started=self.do_pp_started,
                on_progress=self.do_pp_progress,
                on_feedback_log_object=self.do_thread_feedback_log_object,
                on_feedback_log_str=self.do_thread_feedback_log_str,
                # Item emitters
                on_item_ended=self.do_pp_item_ended,
                on_log_item_event=self.do_pp_log_item_event,
                on_item_image_ready=self.do_pp_item_image_ready,
                # Callbacks
                check_stop=self.do_pp_check_abort,
                # States
                data_base=self.current_database.copy(),
                multithread=self.multithread,
                # Create pipeline
                pipeline=self.pp_pipeline,
                group_time_delta=self.ui.sp_pp_time_delta.value(),
                items_thread_pool=self.pp_thread_pool,
            )
            if self.multithread:
                self.thread_pool.start(rpp)
            else:
                rpp.run()
        except Exception as e:
            logger.exception(f'Unable to process pipeline: "{repr(e)}"')

    def on_sl_pp_thread_count_index_changed(self, value):
        self.pp_thread_pool.setMaxThreadCount(value)
        self.ui.lb_pp_thread_count.setText(
            f"{value}/{self.ui.sl_pp_thread_count.maximum()}"
        )

    def on_bt_launch_batch(self):
        self.run_process(wrapper=None)

    def on_bt_update_selection_stats(self):
        model = self.get_image_model()
        no_good = model is None
        if no_good is False:
            delegate = self.ui.tv_image_browser.itemDelegate()
            sel_ct = model.rowCount()
        else:
            delegate = None
            sel_ct = 0
        if no_good:
            self.ui.lv_stats.insertPlainText("No images selectted\n")
            self.ui.lv_stats.insertPlainText(
                "Please add images to selection to get statistics\n"
            )
            self.ui.lv_stats.insertPlainText("\n")
            self.ui.lv_stats.insertPlainText(
                "________________________________________________\n"
            )

        include_annotations = self.ui.cb_stat_include_annotations.isChecked()
        self.update_feedback(
            status_message="Building selection stats", use_status_as_log=True
        )
        self.global_progress_start(add_stop_button=True)
        try:
            self.ui.lv_stats.insertPlainText("\n")
            self.ui.lv_stats.insertPlainText(
                "________________________________________________\n"
            )
            self.ui.lv_stats.insertPlainText(f"Selected items count: {sel_ct}\n")
            self.ui.lv_stats.insertPlainText("\n")
            if include_annotations is True and delegate is not None:
                gbl_cpt = 0
                ann_counter = defaultdict(int)
                for i in range(0, model.rowCount()):
                    ann_ = delegate.get_annotation(row_number=i)
                    if ann_ is not None:
                        gbl_cpt += 1
                        ann_counter[ann_["kind"].lower()] += 1
                self.ui.lv_stats.insertPlainText(
                    f"Annotations: {gbl_cpt}, " f"{gbl_cpt / sel_ct * 100:.2f}%\n"
                )
                for k, v in ann_counter.items():
                    self.ui.lv_stats.insertPlainText(
                        f"  {k.ljust(13)}: {v}, {v / sel_ct * 100:.2f}%\n"
                    )
                self.ui.lv_stats.insertPlainText(
                    "________________________________________________\n"
                )
                self.ui.lv_stats.insertPlainText("\n")

            dataframe: pd.DataFrame = model.images
            for key in ["Experiment", "Plant", "Date", "Camera", "view_option"]:
                self.ui.lv_stats.insertPlainText(f"{key}s:\n")
                self.ui.lv_stats.insertPlainText(
                    "\n".join(
                        [
                            f"- {k}: {v}"
                            for k, v in dataframe.groupby(key)
                            .agg({key: "count"})
                            .iloc[:, 0]
                            .to_dict()
                            .items()
                        ]
                    )
                )
                self.ui.lv_stats.insertPlainText("\n")
                self.ui.lv_stats.insertPlainText("\n")
            self.ui.lv_stats.insertPlainText(
                "________________________________________________\n"
            )
        except Exception as e:
            logger.exception(f"Failed to update statistics: {repr(e)}")
        finally:
            self.global_progress_stop()

    def on_bt_stop_batch(self):
        if self.pp_pipeline is None:
            self.update_feedback(
                status_message="Stoping, please wait ...",
                log_message="User stopped process, waiting for last thread",
            )
            self.threads_step = self.threads_total
            self.thread_pool.clear()
            self.thread_pool.waitForDone(-1)
            self.update_feedback(status_message="Process stopped", use_status_as_log=True)
        self._batch_stop_current = True

    def on_bt_reset_op(self):
        if self._initializing:
            return
        self._updating_process_modes = True
        selected_mode = self.current_tool
        try:
            selected_mode.reset()
        except Exception as e:
            logger.exception(f"Failed to reset tool: {repr(e)}")
        finally:
            self._updating_process_modes = False
        if not self._initializing and selected_mode.real_time:
            self.run_process(wrapper=self._src_image_wrapper, ipt=selected_mode)

    def add_images_to_viewer(
        self,
        wrapper: BaseImageProcessor,
        avoid_duplicates: bool = False,
        data_dict: dict = None,
    ):
        if wrapper is None:
            return
        self._updating_available_images = len(wrapper.image_list) != 1
        try:
            for dic in wrapper.image_list:
                if (
                    avoid_duplicates
                    and self.ui.cb_available_outputs.findText(dic["name"]) >= 0
                ):
                    continue
                if dic["written"] is True:
                    continue
                if data_dict is not None:
                    dic["data"] = dict(**{"image_name": dic["name"]}, **data_dict)
                dic["written"] = True
                dic["plant_name"] = wrapper.plant
                dic["luid"] = wrapper.luid
                self.ui.cb_available_outputs.addItem(dic["name"], dic)
        except Exception as e:
            logger.exception(f"Unable to update available images because: {repr(e)}")
        finally:
            self._updating_available_images = False

        if self.ui.cb_available_outputs.count() > 1:
            self.ui.cb_available_outputs.setCurrentIndex(
                self.ui.cb_available_outputs.count() - 1
            )

    def on_bt_set_as_selected(self):
        self.select_image_from_luid(luid=self._selected_output_image_luid)

    def update_output_tab(self, data_dict):
        while self.ui.tw_script_sim_output.rowCount() > 0:
            self.ui.tw_script_sim_output.removeRow(0)
        for k, v in data_dict.items():
            insert_pos = self.ui.tw_script_sim_output.rowCount()
            self.ui.tw_script_sim_output.insertRow(insert_pos)
            twi = QTableWidgetItem(f"{k}")
            twi.setToolTip(f"{k}")
            self.ui.tw_script_sim_output.setItem(insert_pos, 0, twi)
            twi = QTableWidgetItem(f"{v}")
            twi.setToolTip(f"{v}")
            self.ui.tw_script_sim_output.setItem(insert_pos, 1, twi)

    def update_params_tab(self, data_dict):
        while self.ui.tw_params.rowCount() > 0:
            self.ui.tw_params.removeRow(0)
        for k, v in data_dict.items():
            insert_pos = self.ui.tw_params.rowCount()
            self.ui.tw_params.insertRow(insert_pos)
            twi = QTableWidgetItem(f"{k}")
            twi.setToolTip(f"{k}")
            self.ui.tw_params.setItem(insert_pos, 0, twi)
            twi = QTableWidgetItem(f"{v}")
            twi.setToolTip(f"{v}")
            self.ui.tw_params.setItem(insert_pos, 1, twi)

    def do_thread_started(self, mode: str, is_batch_process: bool):
        if mode == "param":
            pass
        elif mode == "ipt":
            pass
        elif mode == "script":
            if not is_batch_process:
                self.on_bt_clear_result()
            self.update_feedback(
                status_message="Executing current script, please wait..."
            )
        elif mode == "module":
            pass
        elif mode == "pipeline":
            if not is_batch_process:
                self.on_bt_clear_result()
            self.update_feedback(
                status_message="Executing current pipeline, please wait...",
                use_status_as_log=True,
                log_level=logging.INFO,
            )
        else:
            self.update_feedback(
                status_message=f"Unknown runnable mode {mode}",
                use_status_as_log=True,
                log_level=logging.ERROR,
            )

    def do_thread_ending(self, success: bool, status_msg: str, log_msg: str):
        if (
            self.threads_total > 1
            and self.threads_step < self.threads_total
            and status_msg
        ):
            status_msg += f" ({self.threads_step + 1}/{self.threads_total})"
        self.update_feedback(status_message=status_msg, log_message=log_msg)

    def do_thread_ended(self):
        self.update_thread_counts(
            thread_step=self.threads_step + 1,
            thread_total=self.threads_total,
            thread_waiting=self.threads_waiting - 1,
        )

    def do_thread_update_images(self, batch_process: bool, sender: object):
        if isinstance(sender, BaseImageProcessor):
            wrapper = sender
        elif isinstance(sender, IptParamHolder):
            wrapper = sender.wrapper
            if wrapper is None:
                logger.exception(
                    "Unable to update available images because: there's no wrapper inside the tool"
                )
                return
        else:
            logger.exception(
                "Unable to update available images because: unknown argument"
            )
            return

        if isinstance(sender, IptParamHolder):
            info_dict = dict(ipt=sender.name, ipt_class_name=type(sender).__name__)
        else:
            info_dict = {}
        info_dict = dict(
            **info_dict,
            **dict(
                experiment=wrapper.experiment,
                plant=wrapper.plant,
                date_time=wrapper.date_time,
                camera=wrapper.camera,
                view_option=wrapper.view_option,
                img_width=wrapper.width,
                img_height=wrapper.height,
            ),
        )
        if isinstance(sender, IptParamHolder):
            info_dict.update(sender.params_to_dict())
        if isinstance(sender, IptParamHolder) and hasattr(sender, "data_dict"):
            info_dict.update(sender.data_dict)
        elif len(wrapper.csv_data_holder.data_list) > 0:
            info_dict.update(
                {
                    k: v
                    for (k, v) in wrapper.csv_data_holder.data_list.items()
                    if v is not None
                    if k not in info_dict
                }
            )

        if batch_process:
            try:
                img_lst_ = wrapper.image_list
                if len(img_lst_) > 0:
                    dic = wrapper.retrieve_image_dict("mosaic_out")
                    if dic is None:
                        dic = wrapper.retrieve_image_dict("mosaic")
                        if dic is None:
                            dic = img_lst_[len(img_lst_) - 1]
                    dic["data"] = info_dict
                    dic["plant_name"] = wrapper.plant
                    dic["luid"] = wrapper.luid
                    self.ui.cb_available_outputs.addItem(wrapper.short_name, dic)
            except Exception as e:
                logger.exception(f"Unable to update available images because: {repr(e)}")
            self.ui.cb_available_outputs.setCurrentIndex(
                self.ui.cb_available_outputs.count() - 1
            )
        else:
            self.add_images_to_viewer(
                wrapper=wrapper, avoid_duplicates=False, data_dict=info_dict
            )

    def do_thread_update_data(self, csv_data: dict):
        self.update_output_tab(csv_data)

    def do_thread_feedback_log_object(self, status_message: str, sender: object):
        self.update_feedback(status_message=status_message, log_message=sender)

    def do_thread_feedback_log_str(
        self, status_message: str, log_message: str, use_status_as_log: bool
    ):
        self.update_feedback(
            status_message=status_message,
            log_message=log_message,
            use_status_as_log=use_status_as_log,
        )

    def update_thread_counts(
        self, thread_step: int, thread_total: int, thread_waiting: int
    ):
        self.threads_step = thread_step
        self.threads_waiting = thread_waiting
        self.threads_total = thread_total

        if thread_total > 1 and thread_step <= 0:
            self.global_progress_start(add_stop_button=True)
        elif thread_total > 1 and thread_step < thread_total:
            self.global_progress_update(self.threads_step, self.threads_total)
        elif (thread_step >= thread_total) or (thread_total < 1):
            self.global_progress_stop()
            self.set_global_enabled_state(new_state=True)

    def run_runnable(
        self,
        image_data: dict,
        is_batch_process: bool,
        ipt: IptParamHolder,
        pipeline: LoosePipeline,
        exec_param: int,
        target_module: str,
        grid_search_mode: bool = False,
    ):
        if self.ui.act_settings_sir_keep.isChecked():
            scale_factor = 1
        elif self.ui.act_settings_sir_2x.isChecked():
            scale_factor = 1 / 2
        elif self.ui.act_settings_sir_3x.isChecked():
            scale_factor = 1 / 3
        elif self.ui.act_settings_sir_4x.isChecked():
            scale_factor = 1 / 4
        elif self.ui.act_settings_sir_5x.isChecked():
            scale_factor = 1 / 5
        elif self.ui.act_settings_sir_6x.isChecked():
            scale_factor = 1 / 6
        else:
            scale_factor = 1

        runner_ = IpsoRunnable(
            on_started=self.do_thread_started,
            on_ending=self.do_thread_ending,
            on_ended=self.do_thread_ended,
            on_update_images=self.do_thread_update_images,
            on_update_data=self.do_thread_update_data,
            on_feedback_log_object=self.do_thread_feedback_log_object,
            on_feedback_log_str=self.do_thread_feedback_log_str,
            on_pipeline_progress=self.pp_callback,
            file_data=image_data,
            database=self.current_database.copy(),
            batch_process=is_batch_process,
            ipt=ipt,
            pipeline=pipeline,
            exec_param=exec_param,
            scale_factor=scale_factor,
            target_module=target_module,
            grid_search_mode=grid_search_mode,
        )
        self.threads_waiting += 1
        if self.multithread:
            self.thread_pool.start(runner_)
        else:
            runner_.run()

    def run_process(
        self,
        wrapper: BaseImageProcessor = None,
        ipt=None,
        exec_param=None,
        target_module: str = "",
        grid_search_mode: bool = False,
    ):
        if wrapper is None:
            # Collect images
            dataframe = self.get_image_dataframe()
            if dataframe is None:
                image_list_ = None
            else:
                skim_mode_ = self.ui.cb_batch_mode.currentText().lower()
                dff = dataframe[["Luid", "FilePath", "date_time"]]
                if skim_mode_ == "all":
                    pass
                elif skim_mode_ == "first n":
                    dff = dff.iloc[
                        0 : min(dataframe.shape[0], self.ui.sb_batch_count.value())
                    ]
                elif skim_mode_ == "random n":
                    dff = dff.sample(
                        n=min(dataframe.shape[0], self.ui.sb_batch_count.value())
                    )
                else:
                    self.update_feedback(
                        status_message="Run process: unknown filter mode",
                        use_status_as_log=True,
                    )
                    return False
                dff = dff.sort_values(by=["date_time"], axis=0, na_position="first")
                image_list_ = [
                    {"luid": k, "path": v}
                    for k, v in zip(list(dff["Luid"]), list(dff["FilePath"]))
                ]

                # Update "Last batch" data
                self.ui.lw_last_batch.clear()
                for img in reversed(image_list_):
                    new_item = QListWidgetItem()
                    new_item.setText(img["luid"])
                    self.ui.lw_last_batch.insertItem(0, new_item)
        else:
            image_list_ = [dict(path=wrapper.file_path, luid=wrapper.luid)]

        if not image_list_:
            self.update_feedback(
                status_message="Nothing to process", log_message="Nothing to process"
            )
            return

        pipeline_ = None
        ipt_ = None
        if self.selected_run_tab == _TAB_TOOLS:
            if ipt is None:
                ipt_ = self._current_tool.copy()
            else:
                ipt_ = ipt
        elif self.selected_run_tab == _TAB_PIPELINE_V2:
            pipeline_ = self.pipeline
            ipt_ = ipt
        else:
            logger.exception(err_str=f"Unknown active tab {self.selected_run_tab}")
            return

        try:
            if len(image_list_) > 1:
                new_enabled_state = False
            elif ipt_ is None:
                new_enabled_state = False
            elif ipt_.real_time:
                new_enabled_state = True
            else:
                new_enabled_state = False

            if ipt_ is not None and not ipt_.real_time:
                update_msg = f"Executing {ipt_.name}, please wait..."
            else:
                update_msg = ""
            if update_msg:
                self.update_feedback(status_message=update_msg)

            self.set_global_enabled_state(new_state=new_enabled_state)

            self.thread_pool.clear()
            self.update_thread_counts(
                thread_step=0, thread_total=len(image_list_), thread_waiting=0
            )

            batch_process = len(image_list_) > 1
            self._batch_stop_current = False
            for image_data in image_list_:
                if self._batch_stop_current is True:
                    break
                self.run_runnable(
                    image_data=image_data,
                    is_batch_process=batch_process,
                    ipt=ipt_,
                    pipeline=pipeline_,
                    exec_param=exec_param,
                    target_module=target_module,
                    grid_search_mode=grid_search_mode,
                )

        except Exception as e:
            logger.exception(f'Failed to initiate thread: "{repr(e)}"')

    def on_itemSelectionChanged(self):
        for item in self.ui.lw_last_batch.selectedItems():
            self.select_image_from_luid(item.text())
            break

    def on_bt_set_batch_as_selection(self):
        self.begin_edit_image_browser()
        try:
            self.update_feedback(
                status_message="Setting las batch as selected images",
                use_status_as_log=True,
            )
            luids = [
                self.ui.lw_last_batch.item(i).text()
                for i in range(0, self.ui.lw_last_batch.count())
            ]
            if luids:
                self.update_image_browser(
                    dataframe=pd.DataFrame(data=dict(Luid=luids)),
                    mode="keep",
                )
        finally:
            self.end_edit_image_browser()

    def on_bt_process_image(self):
        if self._src_image_wrapper is not None and self._src_image_wrapper.good_image:
            self.run_process(self._src_image_wrapper)

    def on_bt_tool_help(self):
        ShowTextDialog(
            title=f"Help for {self.current_tool.name}",
            text=self.current_tool.hint,
            pt=self.sender().mapToGlobal(
                QPoint(self.sender().width(), self.sender().height())
            ),
            use_html=False,
        ).exec_()

    def on_bt_tool_show_code(self):
        try:
            if self.ui.action_standard_object_oriented_call.isChecked():
                code_ = self.current_tool.code(
                    print_result=False,
                    use_with_clause=False,
                    build_wrapper=self.ui.action_create_wrapper_before.isChecked(),
                )
            elif self.ui.action_object_oriented_wrapped_with_a_with_clause.isChecked():
                code_ = self.current_tool.code(
                    print_result=False,
                    use_with_clause=True,
                    build_wrapper=self.ui.action_create_wrapper_before.isChecked(),
                )
            elif self.ui.action_functional_style.isChecked():
                code_ = call_ipt_code(
                    ipt=self.current_tool,
                    file_name=self.current_tool.file_name
                    if self.ui.action_create_wrapper_before.isChecked()
                    else "",
                )
            else:
                code_ = "Unknown code generation mode"
        except Exception as e:
            code_ = "Unable to generate code"
        ShowTextDialog(
            title=f"Code for {self.current_tool.name}",
            text=code_,
            use_html=False,
            pt=self.sender().mapToGlobal(
                QPoint(self.sender().width(), self.sender().height())
            ),
        ).exec_()

    def on_bt_clear_result(self):
        img_count = self.ui.cb_available_outputs.count()
        self._batch_is_active = False
        self.ui.cb_available_outputs.clear()
        if self._src_image_wrapper is not None:
            self._src_image_wrapper.image_list = []
            self.ui.gv_output_image.main_image = None
        while self.ui.tw_script_sim_output.rowCount() > 0:
            self.ui.tw_script_sim_output.removeRow(0)
        self.update_feedback(
            status_message=f"Cleared {img_count} images", use_status_as_log=True
        )
        self.ui.bt_set_as_selected.setEnabled(False)
        self._selected_output_image_luid = None

    def save_image(
        self,
        image_data,
        text: str = "",
        image_path: str = "",
        add_time_stamp: bool = False,
        index: int = -1,
    ):
        try:
            if not self._src_image_wrapper.good_image:
                self.update_feedback(
                    status_message="Bad image",
                    log_message=self._src_image_wrapper.error_holder,
                )
                return False

            if not text:
                if index >= 0:
                    text = make_safe_name(
                        f'{image_data["plant_name"]}_{str(index)}_{image_data["name"]}'
                    )
                else:
                    text = make_safe_name(
                        f'{image_data["plant_name"]}_{image_data["name"]}'
                    )
                if add_time_stamp:
                    text = text + "_" + dt.now().strftime("%Y%m%d_%H%M%S")

            if not image_path:
                force_directories(ipso_folders.get_path("image_output"))
                image_path = os.path.join(
                    ipso_folders.get_path("image_output"), f"{text}.jpg"
                )
            else:
                force_directories(image_path)
                image_path = os.path.join(image_path, f"{text}.jpg")
            cv2.imwrite(image_path, image_data["image"])
            image_data["written"] = True
        except Exception as e:
            logger.exception(f'Failed to save image: "{repr(e)}"')
            return False
        else:
            return True

    def on_bt_save_current_image(self):
        cb = self.ui.cb_available_outputs
        if cb.count():
            if self.save_image(
                image_data=cb.itemData(cb.currentIndex()), text="", add_time_stamp=True
            ):
                self.update_feedback(
                    status_message=f"Saved {cb.currentText()}", use_status_as_log=True
                )
                open_file((ipso_folders.get_path("image_output"), ""))

    def on_bt_save_all_images(self):
        cb = self.ui.cb_available_outputs
        image_name_root = dt.now().strftime("%Y%B%d_%H%M%S")
        for i in range(0, cb.count()):
            image_name = f"img_{image_name_root}_{i}.jpg"
            if self.save_image(
                image_data=cb.itemData(i), text="", add_time_stamp=True, index=i
            ):
                self.update_feedback(
                    status_message=f"Saved {image_name} -- {i + 1}/{cb.count()}"
                )
        self.update_feedback(
            status_message=f"Saved {cb.count()} images", use_status_as_log=True
        )
        open_file((ipso_folders.get_path("image_output"), ""))

    def on_video_frame_duration_changed(self):
        self.ui.action_video_1_24_second.setChecked(
            self.sender() == self.ui.action_video_1_24_second
        )
        self.ui.action_video_half_second.setChecked(
            self.sender() == self.ui.action_video_half_second
        )
        self.ui.action_video_1_second.setChecked(
            self.sender() == self.ui.action_video_1_second
        )
        self.ui.action_video_5_second.setChecked(
            self.sender() == self.ui.action_video_5_second
        )

    def on_video_resolution_changed(self):
        self.ui.action_video_res_first_image.setChecked(
            self.sender() == self.ui.action_video_res_first_image
        )
        self.ui.action_video_res_1080p.setChecked(
            self.sender() == self.ui.action_video_res_1080p
        )
        self.ui.action_video_res_720p.setChecked(
            self.sender() == self.ui.action_video_res_720p
        )
        self.ui.action_video_res_576p.setChecked(
            self.sender() == self.ui.action_video_res_576p
        )
        self.ui.action_video_res_480p.setChecked(
            self.sender() == self.ui.action_video_res_480p
        )
        self.ui.action_video_res_376p.setChecked(
            self.sender() == self.ui.action_video_res_376p
        )
        self.ui.action_video_res_240p.setChecked(
            self.sender() == self.ui.action_video_res_240p
        )

    def on_video_aspect_ratio_changed(self):
        self.ui.action_video_ar_16_9.setChecked(
            self.sender() == self.ui.action_video_ar_16_9
        )
        self.ui.action_video_ar_4_3.setChecked(
            self.sender() == self.ui.action_video_ar_4_3
        )
        self.ui.action_video_ar_1_1.setChecked(
            self.sender() == self.ui.action_video_ar_1_1
        )

    def on_action_video_bkg_color_changed(self):
        self.ui.action_video_bkg_color_black.setChecked(
            self.sender() == self.ui.action_video_bkg_color_black
        )
        self.ui.action_video_bkg_color_white.setChecked(
            self.sender() == self.ui.action_video_bkg_color_white
        )
        self.ui.action_video_bkg_color_silver.setChecked(
            self.sender() == self.ui.action_video_bkg_color_silver
        )

    def on_sis_changed(self):
        self.ui.act_settings_sir_keep.setChecked(
            self.sender() == self.ui.act_settings_sir_keep
        )
        self.ui.act_settings_sir_2x.setChecked(
            self.sender() == self.ui.act_settings_sir_2x
        )
        self.ui.act_settings_sir_3x.setChecked(
            self.sender() == self.ui.act_settings_sir_3x
        )
        self.ui.act_settings_sir_4x.setChecked(
            self.sender() == self.ui.act_settings_sir_4x
        )
        self.ui.act_settings_sir_5x.setChecked(
            self.sender() == self.ui.act_settings_sir_5x
        )
        self.ui.act_settings_sir_6x.setChecked(
            self.sender() == self.ui.act_settings_sir_6x
        )

    def get_de_model(self) -> QPandasModel:
        ret = self.ui.tb_ge_dataframe.model()
        return ret if isinstance(ret, QPandasModel) else None

    def get_de_dataframe(self) -> pd.DataFrame:
        model = self.get_de_model()
        return None if model is None else model.dataframe

    def has_de_dataframe(self) -> bool:
        return self.get_de_dataframe() is not None

    def get_de_delegate(self) -> QColorDelegate:
        ret = self.ui.tb_ge_dataframe.itemDelegate()
        return ret if isinstance(ret, QColorDelegate) else None

    def on_tb_ge_dataframe_selection_changed(self, selected, deselected):
        image = None
        brush_color = qApp.palette().window()

        qApp.palette().HighlightedText

        for index in selected.indexes():
            current_row = index.row()
            break
        else:
            self.gv_de_image.scene().setBackgroundBrush(brush_color)
            self.gv_de_image.main_image = image
            return

        dataframe = self.get_de_dataframe()
        if dataframe is None:
            self.gv_de_image.scene().setBackgroundBrush(brush_color)
            self.gv_de_image.main_image = image
            return

        # dataframe = self.get_image_dataframe()
        if "source_path" in dataframe:
            src_path = "source_path"
        elif "path" in dataframe:
            src_path = "path"
        elif "FilePath" in dataframe:
            src_path = "FilePath"
        else:
            src_path = ""
        color = QColor(*ipc.bgr_to_rgb(ipc.C_FUCHSIA))
        if src_path:
            col = -1
            for index in selected.indexes():
                col = index.column()
            if (col >= 0) and ("error" in dataframe.columns[col]):
                try:
                    val = int(dataframe.iloc[current_row, col])
                except ValueError:
                    pass
                else:
                    max_val = dataframe[dataframe.columns[col]].max()
                    colors = ipc.build_color_steps(step_count=max_val + 1)
                    color = QColor(*ipc.bgr_to_rgb(colors[val]))
            else:
                color = QColor(*ipc.bgr_to_rgb(ipc.C_WHITE))
            image = dataframe.iloc[current_row, dataframe.columns.get_loc(src_path)]
            image_columns = [
                dataframe.iloc[current_row, dataframe.columns.get_loc(c)]
                for c in list(dataframe.columns)
                if "image" in c
            ]
            if image_columns:
                image = ([image] + image_columns, color)
        else:
            image = None

        self.gv_de_image.scene().setBackgroundBrush(color)
        self.gv_de_image.main_image = image

    def init_data_editor(self, dataframe=None):
        self.ui.tb_ge_dataframe.setModel(QPandasModel(dataframe))
        self.ui.tb_ge_dataframe.setItemDelegate(
            QColorDelegate(parent=self.ui.tb_ge_dataframe, palette=qApp.palette())
        )
        self.ui.tb_ge_dataframe.setSortingEnabled(True)
        if dataframe is not None:
            selectionModel = self.ui.tb_ge_dataframe.selectionModel()
            selectionModel.selectionChanged.connect(
                self.ui.tb_ge_dataframe_selection_changed
            )
            self.de_fill_description(dataframe.describe(include="all"))
            self.de_fill_columns_info(dataframe)
        else:
            self.de_fill_description(None)
            self.de_fill_columns_info(None)
        self.gv_de_image.scene().setBackgroundBrush(qApp.palette().window())
        self.gv_de_image.main_image = None

    def de_fill_description(self, dataframe):
        self.tb_de_dataframe_info.setModel(None)
        if dataframe is not None:
            if dataframe.shape[0] == 8:
                dataframe.insert(
                    0, "", ["count", "mean", "std", "min", "25%", "50%", "75%", "max"]
                )
            elif dataframe.shape[0] == 11:
                dataframe.insert(
                    0,
                    "",
                    [
                        "count",
                        "top",
                        "freq",
                        "unique",
                        "mean",
                        "std",
                        "min",
                        "25%",
                        "50%",
                        "75%",
                        "max",
                    ],
                )
            elif dataframe.shape[0] == 4:
                dataframe.insert(0, "", ["count", "top", "freq", "unique"])

            self.tb_de_dataframe_info.setModel(QPandasModel(dataframe))

    def de_fill_columns_info(self, dataframe):
        self.tb_de_column_info.setModel(None)
        if dataframe is not None:
            self.tb_de_column_info.setModel(QPandasColumnsModel(dataframe))
            self.tb_de_column_info.horizontalHeader().setStretchLastSection(False)
            self.tb_de_column_info.horizontalHeader().setSectionResizeMode(
                0, QHeaderView.ResizeToContents
            )
            self.tb_de_column_info.horizontalHeader().setSectionResizeMode(
                1, QHeaderView.Stretch
            )

    def on_action_de_new_sheet(self):
        self.init_data_editor(None)
        self.update_feedback(
            status_message="Cleared dataframe",
            log_message="Cleared dataframe",
            log_level=logging.INFO,
        )

    def on_action_de_load_csv(self):
        file_name_ = QFileDialog.getOpenFileName(
            parent=self,
            caption="Load dataframe as CSV",
            dir=ipso_folders.get_path("csv"),
            filter="CSV(*.csv)",
        )[0]
        if file_name_:
            ipso_folders.set_path("csv", os.path.join(os.path.dirname(file_name_), ""))
            self.init_data_editor(pd.read_csv(file_name_))
            self.update_feedback(
                status_message="Dataframe loaded",
                log_message=f"Loaded dataframe from {file_name_}",
                log_level=logging.INFO,
            )

    def on_action_de_create_sheet_from_selection(self):
        dataframe = self.get_de_dataframe()
        if dataframe is not None:
            self.init_data_editor(dataframe.copy())

    def on_action_de_add_column(self):
        pass

    def on_action_de_delete_column(self):
        pass

    def on_action_de_save_csv(self):
        dataframe = self.get_de_dataframe()
        if dataframe is not None:
            file_name_ = QFileDialog.getSaveFileName(
                parent=self,
                caption="Save dataframe as CSV",
                dir=ipso_folders.get_path("csv"),
                filter="CSV(*.csv)",
            )[0]
            if file_name_:
                ipso_folders.set_path(
                    "csv", os.path.join(os.path.dirname(file_name_), "")
                )
                dataframe.to_csv(file_name_, index=False)
                self.update_feedback(
                    status_message="Dataframe saved",
                    log_message=f"Saved dataframe to {file_name_}",
                    log_level=logging.INFO,
                )
        else:
            self.update_feedback(
                status_message="No dataframe to save",
                log_message="No dataframe to save",
                log_level=logging.WARNING,
            )

    def on_action_build_video_from_images(self):
        if self.ui.cb_available_outputs.count() < 1:
            self.update_feedback(
                status_message="No images to build video from", use_status_as_log=True
            )
            return

        frame_rate = 24.0

        # Set frame duration
        if self.ui.action_video_1_24_second.isChecked():
            frame_duration = frame_rate / 24
        elif self.ui.action_video_half_second.isChecked():
            frame_duration = frame_rate / 2
        elif self.ui.action_video_1_second.isChecked():
            frame_duration = frame_rate
        elif self.ui.action_video_5_second.isChecked():
            frame_duration = frame_rate * 5
        else:
            frame_duration = frame_rate
        frame_duration = max(1, round(frame_duration))

        # Set resolution & aspect ratio
        if self.ui.action_video_res_first_image.isChecked():
            v_height, v_width = self.ui.cb_available_outputs.itemData(0)["image"].shape[
                :2
            ]
        else:
            if self.ui.action_video_res_720p.isChecked():
                v_height = 720
            elif self.ui.action_video_res_576p.isChecked():
                v_height = 576
            elif self.ui.action_video_res_480p.isChecked():
                v_height = 480
            elif self.ui.action_video_res_376p.isChecked():
                v_height = 376
            elif self.ui.action_video_res_240p.isChecked():
                v_height = 240
            else:
                v_height = 1080
            if self.ui.action_video_ar_4_3.isChecked():
                v_width = int(v_height * 4 / 3)
            elif self.ui.action_video_ar_1_1.isChecked():
                v_width = v_height
            else:
                v_width = int(v_height * 16 / 9)

        # Set background color
        if self.ui.action_video_bkg_color_white.isChecked():
            bkg_color = ipc.C_WHITE
        elif self.ui.action_video_bkg_color_silver.isChecked():
            bkg_color = ipc.C_SILVER
        else:
            bkg_color = ipc.C_BLACK

        selected_mode = self.current_tool
        total_ = self.ui.cb_available_outputs.count()
        vid_name = f'{make_safe_name(selected_mode.name)}_{dt.now().strftime("%Y%B%d_%H%M%S")}_{total_}.mp4'
        force_directories(ipso_folders.get_path("image_output"))
        v_output = os.path.join(ipso_folders.get_path("image_output"), vid_name)

        frame_rect = RectangleRegion(width=v_width, height=v_height)

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(v_output, fourcc, frame_rate, (v_width, v_height))

        self._batch_is_active = True
        self._batch_stop_current = False
        self.update_feedback(status_message="Building video", use_status_as_log=True)
        self.global_progress_start()
        try:
            canvas = np.full((v_height, v_width, 3), bkg_color, np.uint8)
            for i in range(0, self.ui.cb_available_outputs.count()):
                if self._batch_stop_current:
                    self._batch_stop_current = False
                    self.global_progress_update(0, 0)
                    break

                if self.ui.action_video_stack_and_jitter.isChecked() and (i < total_ - 1):
                    new_left = int(frame_rect.width * random.uniform(0, 0.7))
                    new_top = int(frame_rect.height * random.uniform(0, 0.7))
                    new_width = int(
                        (frame_rect.width - new_left) * random.uniform(0.5, 1)
                    )
                    new_height = int(
                        (frame_rect.height - new_top) * random.uniform(0.5, 1)
                    )
                    r = RectangleRegion(
                        left=new_left, width=new_width, top=new_top, height=new_height
                    )
                else:
                    if not self.ui.action_video_stack_and_jitter.isChecked():
                        canvas = np.full((v_height, v_width, 3), bkg_color, np.uint8)
                    r = RectangleRegion(
                        left=frame_rect.left,
                        right=frame_rect.right,
                        top=frame_rect.top,
                        bottom=frame_rect.bottom,
                    )
                img = ipc.enclose_image(
                    a_cnv=canvas,
                    img=self.ui.cb_available_outputs.itemData(i)["image"],
                    rect=RectangleRegion(
                        left=r.left, right=r.right, top=r.top, bottom=r.bottom
                    ),
                    frame_width=2
                    if self.ui.action_video_stack_and_jitter.isChecked()
                    else 0,
                )

                def write_image_times(out_writer, img_, times=12):
                    for _ in range(0, times):
                        out_writer.write(img_)

                write_image_times(out_writer=out, img_=img, times=frame_duration)

                self.global_progress_update(i + 1, total_)
                self.update_feedback(
                    status_message=f"Added image {i + 1}/{total_} to {vid_name}"
                )

                self.process_events()
        except Exception as e:
            logger.exception(f'Failed to generate video: "{repr(e)}"')
        else:
            self.update_feedback(
                status_message=f'Generated video "{vid_name}"', use_status_as_log=True
            )
            open_file((ipso_folders.get_path("image_output"), ""))
        finally:
            out.release()
            cv2.destroyAllWindows()
            self.global_progress_stop()

    def execute_current_query(self, **kwargs):
        sql_dict = {}

        for couple in (
            (self.ui.chk_experiment, self.ui.cb_experiment.currentText(), "Experiment"),
            (self.ui.chk_plant, self.ui.cb_plant.currentText(), "Plant"),
            (self.ui.chk_date, self.ui.cb_date.currentText(), "Date"),
            (self.ui.chk_camera, self.ui.cb_camera.currentText(), "Camera"),
            (
                self.ui.chk_view_option,
                self.ui.cb_view_option.currentText(),
                "view_option",
            ),
            (self.ui.chk_time, self.ui.cb_time.currentText(), "Time"),
        ):
            chk_box, cb_text, label_ = couple[0], couple[1], couple[2]
            override_param = kwargs.get(label_, "none")
            if override_param == "ignore":
                pass
            elif override_param != "none":
                sql_dict[label_] = override_param
            else:
                if chk_box.isChecked() and chk_box.isEnabled():
                    if label_.lower() == "date":
                        sql_dict[label_] = dt.strptime(cb_text, _DATE_FORMAT).date()
                    elif label_.lower() == "time":
                        sql_dict[label_] = dt.strptime(cb_text, _TIME_FORMAT).time()
                    else:
                        sql_dict[label_] = cb_text

        return self.query_current_database_as_pandas(
            command="SELECT",
            columns="Experiment, Plant, Date, Camera, view_option, Time, date_time, FilePath, Luid",
            additional="ORDER BY date_time ASC",
            **sql_dict,
        )

    def on_bt_delete_annotation(self):
        if self._src_image_wrapper is not None:
            id = self.get_image_delegate()
            if id is None:
                return
            id.set_annotation(
                luid=self._src_image_wrapper.luid,
                experiment=self._src_image_wrapper.experiment,
            )
            self.ui.cb_annotation_level.setCurrentIndex(0)
            self.ui.te_annotations.clear()
            self.ui.tw_tool_box.setTabIcon(0, QIcon())

    def on_bt_clear_selection(self):
        self.begin_edit_image_browser()
        try:
            self.update_image_browser(None, mode="clear")
        finally:
            self.end_edit_image_browser()

    def on_bt_remove_from_selection(self):
        self.begin_edit_image_browser()
        try:
            self.update_image_browser(
                dataframe=self.execute_current_query(), mode="remove"
            )
        finally:
            self.end_edit_image_browser()

    def do_exception(self):
        logger.info("Info")
        logger.warning("warning")
        logger.exception("exception")
        logger.error("error")
        logger.critical("Critical")
        try:
            print(1 / 0)
        except Exception as e:
            logger.exception(f"Add to selection failed: {repr(e)}")
        print(1 / 0)

    def on_bt_keep_annotated(self):
        self.begin_edit_image_browser()
        try:
            id = self.get_image_delegate()
            dataframe = self.get_image_dataframe()
            if id is None or dataframe is None:
                return
            dataframe = dataframe[["Experiment", "Luid"]]
            luids = []
            self.update_feedback(
                status_message="Keeping only tagged images", use_status_as_log=True
            )
            self.global_progress_start(add_stop_button=False)
            total_ = dataframe.shape[0]
            i = 1
            for _, row in dataframe.iterrows():
                if id.get_annotation(experiment=row[0], luid=row[1]) is None:
                    luids.append(row[1])
                self.global_progress_update(step=i, total=total_, process_events=True)
                i += 1
            self.global_progress_stop()
            if luids:
                self.update_image_browser(
                    dataframe=pd.DataFrame(data=dict(Luid=luids)), mode="remove"
                )
        finally:
            self.end_edit_image_browser()

    @log_method_execution_time
    def inner_add_to_selection(self, cull: bool):
        self.begin_edit_image_browser()
        self._batch_stop_current = False
        try:
            dataframe = self.execute_current_query()
            if cull:
                dataframe = dataframe.sample(n=self.ui.sp_add_random_count.value())
            self.update_image_browser(dataframe=dataframe, mode="add")
        except Exception as e:
            logger.exception(f"Add to selection failed: {repr(e)}")
        finally:
            self.end_edit_image_browser()

    def on_bt_add_random(self):
        self.inner_add_to_selection(cull=True)

    def on_bt_add_to_selection(self):
        self.inner_add_to_selection(cull=False)

    def cb_available_outputs_current_index_changed(self, idx):
        if not self._updating_available_images and (
            0 <= idx < self.ui.cb_available_outputs.count()
        ):
            self._image_dict = self.ui.cb_available_outputs.itemData(idx)
            self.ui.gv_output_image.main_image = self._image_dict["image"]
            self.update_params_tab(
                self._image_dict["params"] if "params" in self._image_dict else {}
            )
            self.update_output_tab(
                self._image_dict["data"] if "data" in self._image_dict else {}
            )
            if "luid" in self._image_dict:
                self.ui.bt_set_as_selected.setEnabled(True)
                self._selected_output_image_luid = self._image_dict["luid"]
            else:
                self.ui.bt_set_as_selected.setEnabled(False)
                self._selected_output_image_luid = None

    def cb_experiment_current_index_changed(self, _):
        if self._updating_combo_boxes or self._initializing:
            return
        self.clear_plant_combo_box()
        if self.ui.cb_experiment.count() > 0:
            self._current_exp = self.ui.cb_experiment.currentText()
            self.fill_plant_combo_box()
        self.ui.chk_experiment.setEnabled(self.ui.cb_experiment.count() > 0)

    def cb_plant_current_index_changed(self, _):
        if self._updating_combo_boxes or self._initializing:
            return
        self.clear_date_combo_box()
        if self.ui.cb_plant.count() > 0:
            self._current_plant = self.ui.cb_plant.currentText()
            self.fill_date_combo_box()
        self.ui.chk_plant.setEnabled(self.ui.cb_plant.count() > 0)

    def cb_date_current_index_changed(self, _):
        if self._updating_combo_boxes or self._initializing:
            return
        self.clear_camera_combo_box()
        if self.ui.cb_date.count() > 0:
            self._current_date = dt.strptime(
                self.ui.cb_date.currentText(), _DATE_FORMAT
            ).date()
            self.fill_camera_combo_box()
        self.ui.chk_date.setEnabled(self.ui.cb_date.count() > 0)

    def cb_camera_current_index_changed(self, _):
        if self._updating_combo_boxes or self._initializing:
            return
        self.clear_view_option_combo_box()
        if self.ui.cb_camera.count() > 0:
            self._current_camera = self.ui.cb_camera.currentText()
            self.fill_view_option_combo_box()
        self.ui.chk_camera.setEnabled(self.ui.cb_camera.count() > 0)

    def cb_view_option_current_index_changed(self, _):
        try:
            if self._updating_combo_boxes or self._initializing:
                return
            self.clear_time_combo_box()
            if self.ui.cb_view_option.count() > 0:
                self._current_view_option = self.ui.cb_view_option.currentText()
                self.fill_time_combo_box()
            self.ui.chk_view_option.setEnabled(self.ui.cb_view_option.count() > 0)
        except Exception as e:
            logger.exception(f"Selection failed: {repr(e)}")

    def cb_time_current_index_changed(self, _):
        if self.ui.cb_time.count() > 0 and not self._updating_combo_boxes:
            self._current_time = dt.strptime(
                self.ui.cb_time.currentText(), _TIME_FORMAT
            ).time()
            self.file_name = self.current_selected_image_path()

    def on_chk_pp_show_last_item(self):
        if not self.ui.chk_pp_show_last_item.isChecked():
            self.gv_last_processed_item.main_image = None

    def build_param_overrides(self, wrapper, tool):
        param_names_list = [p.kind for p in tool.gizmos]
        res = {}
        if "channel_selector" in param_names_list and wrapper is not None:
            res["channels"] = {
                ci[1]: ipc.get_hr_channel_name(ci[1])
                for ci in ipc.create_channel_generator(wrapper.file_handler.channels)
            }
        if "tool_target_selector" in param_names_list:
            res["ipt_list"] = {
                type(ipt).__name__: ipt.name for ipt in self._ip_tools_holder.ipt_list
            }
        return res

    def init_param_widget(self, tool, param, allow_real_time: bool = True):
        return build_widgets(
            tool=tool,
            param=param,
            allow_real_time=allow_real_time,
            call_backs=dict(
                set_text=self.widget_set_text,
                set_value=self.widget_set_value,
                add_items=self.widget_add_items,
                set_range=self.widget_set_range,
                set_checked=self.widget_set_checked,
                set_name=self.widget_set_name,
                set_tool_tip=self.widget_set_tool_tip,
                clear=self.widget_clear,
                update_table=self.widget_update_table,
                set_current_index=self.widget_set_current_index,
                connect_call_back=self.widget_connect,
            ),
            do_feedback=self.update_feedback,
        )

    def widget_connect(self, widget, param):
        if param.grid_search_mode:
            param.gs_input.textEdited.connect(self.on_grid_search_param_changed)
            param.gs_auto_fill.clicked.connect(self.on_grid_search_auto_fill_range)
            param.gs_copy_from_param.clicked.connect(
                self.on_grid_search_gs_copy_from_param
            )
            param.gs_reset.clicked.connect(self.on_grid_search_reset)
            return
        elif isinstance(param.allowed_values, dict):
            call_back = self.on_process_param_changed_cb
        elif isinstance(param.allowed_values, str):
            if param.allowed_values == "single_line_text_output":
                call_back = None
            elif param.allowed_values == "multi_line_text_output":
                call_back = None
            elif param.allowed_values == "label":
                call_back = None
            elif param.allowed_values == "table_output":
                call_back = None
            elif param.allowed_values == "single_line_text_input":
                call_back = self.on_text_input_param_changed
            elif param.allowed_values == "multi_line_text_input":
                call_back = self.on_text_browser_input_param_changed
            elif param.allowed_values == "input_button":
                call_back = self.on_process_param_clicked
            else:
                call_back = None
        elif isinstance(param.allowed_values, tuple) or isinstance(
            param.allowed_values, list
        ):
            pa = tuple(param.allowed_values)
            if pa == (0, 1):
                call_back = self.on_process_param_changed_chk
            elif len(pa) == 2:
                call_back = self.on_process_param_changed_sl
            else:
                call_back = None
        else:
            call_back = None
        if param.is_input and call_back is not None and widget is not None:
            if isinstance(param.allowed_values, dict):
                widget.currentIndexChanged.connect(call_back)
            elif isinstance(param.allowed_values, tuple):
                if param.allowed_values == (0, 1):
                    widget.stateChanged.connect(call_back)
                elif len(param.allowed_values) == 2:
                    widget.valueChanged.connect(call_back)
                else:
                    pass
            elif isinstance(param.allowed_values, str):
                if call_back is not None:
                    if hasattr(widget, "textEdited"):
                        widget.textEdited.connect(call_back)
                    elif hasattr(widget, "clicked"):
                        widget.clicked.connect(call_back)
                    elif hasattr(widget, "insertPlainText"):
                        widget.textChanged.connect(call_back)

    def widget_run_module(self):
        btn = self.sender()
        if hasattr(btn, "module"):
            btn.module.root.invalidate(btn.module)
            self.run_process(
                wrapper=self._src_image_wrapper,
                ipt=btn.module.tool,
                target_module=btn.module.uuid,
            )

    def widget_run_grid_search(self):
        btn = self.sender()
        if hasattr(btn, "module"):
            btn.module.root.invalidate(btn.module)
            self.run_process(
                wrapper=self._src_image_wrapper,
                ipt=btn.module.tool,
                target_module=btn.module.uuid,
                grid_search_mode=True,
            )

    def widget_set_text(self, widget, text):
        if widget is None:
            return
        if hasattr(widget, "insertPlainText"):
            widget.insertPlainText(str(text))
        elif hasattr(widget, "setText"):
            widget.setText(str(text))

    def widget_set_range(self, widget, min_val, max_val, default_val):
        widget.setMinimum(min_val)
        widget.setMaximum(max_val)
        if default_val is not None:
            widget.setValue(default_val)

    def widget_add_items(self, widget, items, default):
        for key, value in items.items():
            widget.addItem(value, key)
            if default == key:
                widget.setCurrentIndex(widget.count() - 1)

    def widget_set_checked(self, widget, new_check_state):
        widget.setChecked(new_check_state)

    def widget_set_name(self, widget, new_name):
        if widget is not None:
            widget.setObjectName(new_name)

    def widget_set_tool_tip(self, widget, tool_tip):
        if widget is not None:
            widget.setToolTip(tool_tip)

    def widget_set_value(self, widget, value):
        if widget is not None:
            widget.setValue(value)

    def widget_clear(self, widget):
        if widget is not None:
            if hasattr(widget, "rowCount"):
                while widget.rowCount() > 0:
                    widget.removeRow(0)
            elif hasattr(widget, "clear"):
                widget.clear()

    def widget_set_current_index(self, widget, index):
        if widget is not None:
            widget.setCurrentIndex(index)

    def widget_update_table(self, widget, items, ignore_list, invert_order):
        if widget is not None and isinstance(items, dict):
            for k, v in items.items():
                if ignore_list and (k in ignore_list):
                    continue
                if invert_order:
                    insert_pos = 0
                else:
                    insert_pos = widget.rowCount()
                widget.insertRow(insert_pos)
                widget.setItem(insert_pos, 0, QTableWidgetItem(f"{k}"))
                if isinstance(v, list) or isinstance(v, tuple):
                    for i, value in enumerate(v):
                        widget.setItem(insert_pos, i + 1, QTableWidgetItem(f"{value}"))
                else:
                    widget.setItem(insert_pos, 1, QTableWidgetItem(f"{v}"))

    def print_image_callback(self, image):
        self.ui.gv_output_image.main_image = image

    def do_after_process_param_changed(self, widget):
        tool = widget.tool
        if hasattr(tool, "owner") and isinstance(tool.owner, ModuleNode):
            tool.owner.root.invalidate(tool.owner)
            if widget.allow_real_time and tool.real_time and not tool.block_feedback:
                self.run_process(
                    wrapper=self._src_image_wrapper,
                    ipt=tool,
                    target_module=tool.owner.uuid,
                )
        elif isinstance(tool, IptBase):
            if widget.allow_real_time and tool.real_time and not tool.block_feedback:
                self.run_process(wrapper=self._src_image_wrapper, ipt=tool)

    def on_process_param_clicked(self):
        if self._updating_process_modes:
            return
        widget = self.sender()
        tool = widget.tool
        if isinstance(tool, IptBase):
            self.run_process(
                wrapper=self._src_image_wrapper, ipt=tool, exec_param=widget.param
            )

    def on_process_param_changed_sl(self, value):
        if self._updating_process_modes:
            return
        widget = self.sender()
        widget.param.value = value
        if widget.param.widget_type == "slider":
            widget.label.setText(f"{widget.param.desc}: {widget.param.value}")
        self.do_after_process_param_changed(widget=widget)

    def on_process_param_changed_cb(self, _):
        if self._updating_process_modes:
            return
        widget = self.sender()
        widget.param.value = widget.currentData()
        self.do_after_process_param_changed(widget=widget)

    def on_process_param_changed_chk(self, _):
        if self._updating_process_modes:
            return
        widget = self.sender()
        if widget.isChecked():
            widget.param.value = 1
        else:
            widget.param.value = 0
        self.do_after_process_param_changed(widget=widget)

    def on_grid_search_param_changed(self, new_text):
        if self._updating_process_modes:
            return
        widget = self.sender()
        widget.param.grid_search_options = new_text

    def on_grid_search_gs_copy_from_param(self):
        if self._updating_process_modes:
            return
        widget = self.sender()
        widget.param.grid_search_options = widget.param.str_value

    def on_grid_search_auto_fill_range(self):
        if self._updating_process_modes:
            return
        widget = self.sender()
        widget.param.grid_search_options = widget.param.auto_fill_grid_search()

    def on_grid_search_reset(self):
        if self._updating_process_modes:
            return
        widget = self.sender()
        widget.param.grid_search_options = str(widget.param.default_value)

    def on_text_input_param_changed(self, new_text):
        if self._updating_process_modes:
            return
        widget = self.sender()
        widget.param.value = new_text
        self.do_after_process_param_changed(widget=widget)

    def on_text_browser_input_param_changed(self):
        if self._updating_process_modes:
            return
        widget = self.sender()
        widget.param.value = self.sender().toPlainText()
        self.do_after_process_param_changed(widget=widget)

    def get_query_items(self, column: str, **kwargs):
        items = self.query_current_database(
            command="SELECT DISTINCT",
            columns=column,
            additional=f"ORDER BY {column} ASC",
            **kwargs,
        )
        return [item[0] for item in items]

    def fill_exp_combo_box(self):
        self.clear_exp_combo_box()
        exp_list = self.get_query_items(column="Experiment")
        self.ui.chk_experiment.setText(f"Experiment ({len(exp_list)}): ")
        self.ui.cb_experiment.addItems(exp_list)
        self.ui.cb_experiment.setEnabled(self.ui.cb_experiment.count() > 1)
        if self._updating_combo_boxes:
            target_index = self.ui.cb_experiment.findText(self._current_exp)
            if target_index < 0:
                target_index = 0
                self._current_exp = self.ui.cb_experiment.itemText(0)
            self.ui.cb_experiment.setCurrentIndex(target_index)

    def fill_plant_combo_box(self):
        self.clear_plant_combo_box()
        plant_lst = self.get_query_items(column="Plant", experiment=self._current_exp)
        self.ui.chk_plant.setText(f"Plant ({len(plant_lst)}): ")
        self.ui.cb_plant.addItems(sorted(plant_lst, key=lambda x: natural_keys(x)))
        self.ui.cb_plant.setEnabled(self.ui.cb_plant.count() > 1)
        if self._updating_combo_boxes:
            target_index = self.ui.cb_plant.findText(self._current_plant)
            if target_index < 0:
                target_index = 0
                self._current_plant = self.ui.cb_plant.itemText(0)
            self.ui.cb_plant.setCurrentIndex(target_index)

    def fill_date_combo_box(self):
        self.clear_date_combo_box()
        date_list = [
            item.replace("-", "/")
            if isinstance(item, str)
            else item.strftime(_DATE_FORMAT)
            for item in self.get_query_items(
                column="Date", experiment=self._current_exp, plant=self._current_plant
            )
        ]
        self.ui.chk_date.setText(f"Date ({len(date_list)}): ")
        self.ui.cb_date.addItems(date_list)
        self.ui.cb_date.setEnabled(self.ui.cb_date.count() > 1)
        if self._updating_combo_boxes and self.ui.cb_date.count() > 0:
            target_index = self.ui.cb_date.findText(
                self._current_date.strftime(_DATE_FORMAT)
            )
            if target_index < 0:
                target_index = 0
                self._current_date = dt.strptime(
                    self.ui.cb_date.itemText(0),
                    _DATE_FORMAT,
                ).date()
            self.ui.cb_date.setCurrentIndex(target_index)

    def fill_camera_combo_box(self):
        self.clear_camera_combo_box()
        cam_list = self.get_query_items(
            column="Camera",
            experiment=self._current_exp,
            plant=self._current_plant,
            date=self._current_date,
        )
        self.ui.chk_camera.setText(f"Camera ({len(cam_list)}): ")
        self.ui.cb_camera.addItems(cam_list)
        self.ui.cb_camera.setEnabled(self.ui.cb_camera.count() > 1)
        if self._updating_combo_boxes and self.ui.cb_camera.count() > 0:
            target_index = self.ui.cb_camera.findText(self._current_camera)
            if target_index < 0:
                target_index = 0
                self._current_camera = self.ui.cb_camera.itemText(0)
            self.ui.cb_camera.setCurrentIndex(target_index)

    def fill_view_option_combo_box(self):
        self.clear_view_option_combo_box()
        opt_lst = self.get_query_items(
            column="view_option",
            experiment=self._current_exp,
            plant=self._current_plant,
            date=self._current_date,
            camera=self._current_camera,
        )
        opt_lst.sort(key=lambda x: natural_keys(x))
        if "sw755" in opt_lst:
            opt_lst.remove("sw755")
            opt_lst.insert(0, "sw755")
        self.ui.chk_view_option.setText(f"View option ({len(opt_lst)}): ")
        self.ui.cb_view_option.addItems(opt_lst)
        self.ui.cb_view_option.setEnabled(self.ui.cb_view_option.count() > 1)
        if self._updating_combo_boxes and self.ui.cb_view_option.count() > 0:
            target_index = self.ui.cb_view_option.findText(self._current_view_option)
            if target_index < 0:
                target_index = 0
                self._current_view_option = self.ui.cb_view_option.itemText(0)
            self.ui.cb_view_option.setCurrentIndex(target_index)

    def fill_time_combo_box(self):
        try:
            self.clear_time_combo_box()
            time_lst = [
                item if isinstance(item, str) else item.strftime(_TIME_FORMAT)
                for item in self.get_query_items(
                    column="Time",
                    experiment=self._current_exp,
                    plant=self._current_plant,
                    date=self._current_date,
                    camera=self._current_camera,
                    view_option=self._current_view_option,
                )
            ]
            self.ui.chk_time.setText(f"Time ({len(time_lst)}): ")
            self.ui.cb_time.addItems(time_lst)
            self.ui.cb_time.setEnabled(self.ui.cb_time.count() > 1)
            if self._updating_combo_boxes and self.ui.cb_time.count() > 0:
                target_index = self.ui.cb_time.findText(
                    self._current_time.strftime(_TIME_FORMAT)
                )
                if target_index < 0:
                    target_index = 0
                    if len(time_lst) > 0:
                        self._current_time = dt.strptime(
                            self.ui.cb_time.itemText(0),
                            _TIME_FORMAT,
                        ).time()
                    self.ui.cb_time.setCurrentIndex(target_index)
        except Exception as e:
            logger.exception(f"Failed to fill time combobox: {repr(e)}")

    def clear_exp_combo_box(self):
        self.ui.cb_experiment.clear()
        if not self._updating_combo_boxes:
            self._current_exp = ""
        self.clear_plant_combo_box()

    def clear_plant_combo_box(self):
        self.ui.cb_plant.clear()
        if not self._updating_combo_boxes:
            self._current_plant = ""
        self.clear_date_combo_box()

    def clear_date_combo_box(self):
        self.ui.cb_date.clear()
        if not self._updating_combo_boxes:
            self._current_date = dt.now().date()
        self.clear_camera_combo_box()

    def clear_camera_combo_box(self):
        self.ui.cb_camera.clear()
        if not self._updating_combo_boxes:
            self._current_camera = ""
        self.clear_view_option_combo_box()

    def clear_view_option_combo_box(self):
        self.ui.cb_view_option.clear()
        if not self._updating_combo_boxes:
            self._current_view_option = ""
        self.clear_time_combo_box()

    def clear_time_combo_box(self):
        if not self._updating_combo_boxes:
            self._current_time = dt.now().time()
        self.ui.cb_time.clear()

    def current_selected_image_path(self):
        ret = self.query_current_database(
            command="SELECT",
            columns="FilePath",
            additional="ORDER BY date_time ASC",
            experiment=self._current_exp,
            plant=self._current_plant,
            date=self._current_date,
            camera=self._current_camera,
            view_option=self._current_view_option,
            time=self._current_time,
        )
        if len(ret) > 0:
            tmp_value = ret[0]
            return tmp_value[0]
        else:
            return ""

    def update_comboboxes(self, data: dict, reset_selection: bool = True):
        self._updating_combo_boxes = True
        try:
            if data or reset_selection:
                self._current_exp = data.get("Experiment", "")
                self._current_plant = data.get("Plant", "")
                self._current_date = data.get("Date", dt.now().date())
                self._current_time = data.get("Time", dt.now().time())
                self._current_camera = data.get("Camera", "")
                self._current_view_option = data.get("view_option", "")
            self.fill_exp_combo_box()
            self.fill_plant_combo_box()
            self.fill_date_combo_box()
            self.fill_camera_combo_box()
            self.fill_view_option_combo_box()
            self.fill_time_combo_box()
            self.file_name = self.current_selected_image_path()
        except Exception as e:
            logger.exception(f"Failed to update plant selectors: {repr(e)}")
        finally:
            self._updating_combo_boxes = False
        return True

    def select_image_from_luid(self, luid):
        if not luid:
            return self.update_comboboxes({}, reset_selection=True)
        columns = "Experiment, Plant, Date, Camera, view_option, Time"
        data = self.query_one_current_database(
            command="SELECT",
            columns=columns,
            Luid=luid,
        )
        if data is not None:
            return self.update_comboboxes(
                {k: v for k, v in zip(columns.replace(" ", "").split(","), data)}
            )
        else:
            return self.update_comboboxes({})

    def select_file(self):
        self.file_name, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select source image",
            os.path.join(os.path.expanduser("~"), "Pictures", "TPMP_input", ""),
        )

    def on_action_enable_annotations_checked(self):
        try:
            id = self.ui.tv_image_browser.itemDelegate()
            if id is None:
                return
            id.use_annotations = self.ui.actionEnable_annotations.isChecked()
        except Exception as e:
            logger.exception(f"Failed to add annotation data: {repr(e)}")

    def on_action_use_multithreading(self):
        self.multithread = self.ui.action_use_multithreading.isChecked()

    def on_action_save_pipeline_processor_state(self):
        database_data = (
            None
            if self.current_database is None
            else self.current_database.db_info.to_json()
        )
        if self.pipeline is not None:
            script_ = self.pipeline.copy()
        else:
            self.update_feedback(
                status_message="Pipeline state save: no script",
                log_message="Pipeline state save: no script",
                log_level=logging.ERROR,
            )
            return
        file_name_ = QFileDialog.getSaveFileName(
            parent=self,
            caption="Save pipeline processor state",
            dir=os.path.join(
                ipso_folders.get_path("pp_state"),
                f"{self._src_image_wrapper.experiment}.json",
            ),
            filter="JSON(*.json)",
        )[0]
        if not file_name_:
            return
        if database_data is not None and (
            database_data["target"] in ["phenoserre", "phenopsis"]
        ):
            with open(file_name_, "w") as jw:
                json.dump(
                    dict(
                        output_folder=self.ui.le_pp_output_folder.text(),
                        csv_file_name=self.ui.edt_csv_file_name.text(),
                        overwrite_existing=self.ui.cb_pp_overwrite.isChecked(),
                        sub_folder_name=database_data["display_name"],
                        append_time_stamp=self.ui.cb_pp_append_timestamp_to_output_folder.isChecked(),
                        script=script_.to_json(),
                        generate_series_id=self.ui.cb_pp_generate_series_id.isChecked(),
                        series_id_time_delta=self.ui.sp_pp_time_delta.value(),
                        thread_count=self.ui.sl_pp_thread_count.value(),
                        database_data=database_data,
                        experiment=database_data["display_name"],
                    ),
                    jw,
                    indent=2,
                )
                self.update_feedback(
                    status_message="Pipeline processor state saved",
                    log_message=f'Pipeline state saved to: "{file_name_}"',
                )
        else:
            model = self.get_image_model()
            if (model is None) or (model.rowCount() == 0):
                self.update_feedback(
                    status_message="Pipeline state save: no images",
                    log_message="Pipeline state save: no images",
                    log_level=logging.ERROR,
                )
                return
            dataframe = self.get_image_dataframe()
            if dataframe is None:
                self.update_feedback(
                    status_message="Pipeline state save: no images",
                    log_message="Pipeline state save: no images",
                    log_level=logging.ERROR,
                )
                return

            ipso_folders.set_path(
                "pp_state", os.path.join(os.path.dirname(file_name_), "")
            )
            append_experience_name = (
                model.get_cell_data(row_number=0, column_name="Experiment")
                if self.ui.cb_pp_append_experience_name.isChecked()
                else ""
            )
            with open(file_name_, "w") as jw:
                json.dump(
                    dict(
                        output_folder=self.ui.le_pp_output_folder.text(),
                        csv_file_name=self.ui.edt_csv_file_name.text(),
                        overwrite_existing=self.ui.cb_pp_overwrite.isChecked(),
                        sub_folder_name=append_experience_name,
                        append_time_stamp=self.ui.cb_pp_append_timestamp_to_output_folder.isChecked(),
                        script=script_.to_json(),
                        generate_series_id=self.ui.cb_pp_generate_series_id.isChecked(),
                        series_id_time_delta=self.ui.sp_pp_time_delta.value(),
                        images=list(dataframe["FilePath"]),
                        thread_count=self.ui.sl_pp_thread_count.value(),
                        database_data=database_data,
                    ),
                    jw,
                    indent=2,
                )
                self.update_feedback(
                    status_message="Pipeline processor state saved",
                    log_message=f'Pipeline state saved to: "{file_name_}"',
                )

    def find_tool_by_name(self, tool_name) -> Union[None, IptBase]:
        lst = self._ip_tools_holder.ipt_list
        for ipt_ in lst:
            if ipt_.name == tool_name:
                return ipt_
                break
        else:
            self.update_feedback(
                status_message=f'Unable to find "{tool_name}" operator',
                use_status_as_log=True,
            )
            return None

    def select_tool_from_name(self, tool_name):
        res = self.find_tool_by_name(tool_name=tool_name)
        if res is not None:
            self.current_tool = res

    def on_menu_tool_selection(self, q):
        self.select_tool_from_name(q.text())

    def tool_find_by_name(self, name: str):
        lst = self._ip_tools_holder.ipt_list
        for tool in lst:
            if tool.name == name:
                return tool
        return None

    # Properties
    @property
    def file_name(self):
        return self._file_name

    @file_name.setter
    def file_name(self, value):
        if value != self._file_name:
            # Backup annotation
            if self._src_image_wrapper is not None:
                id = self.get_image_delegate()
                if id is not None:
                    id.set_annotation(
                        luid=self._src_image_wrapper.luid,
                        experiment=self._src_image_wrapper.experiment,
                        kind=self.ui.cb_annotation_level.currentText(),
                        text=self.ui.te_annotations.toPlainText(),
                        auto_text="",
                    )

            if value:
                self._src_image_wrapper = ipo_factory(
                    file_path=value,
                    options=self._options,
                    force_abstract=False,
                    data_base=self.current_database,
                )
                try:
                    ci = self._src_image_wrapper.current_image
                    if ci is None:
                        self.update_feedback(status_message="Failed to load image")
                        self._src_image_wrapper = None
                    else:
                        self.ui.gv_source_image.main_image = ci
                    self.setWindowTitle(
                        f"{_PRAGMA_FULL_NAME} -- {self._src_image_wrapper.name}"
                    )
                except Exception as e:
                    self._src_image_wrapper = None
                    logger.exception(f"Failed to load image: {repr(e)}")
                    self.setWindowTitle(
                        f"{_PRAGMA_FULL_NAME} -- EXCEPTION WHILE LOADING IMAGE"
                    )
            else:
                self._src_image_wrapper = None
                self.setWindowTitle(f"{_PRAGMA_FULL_NAME} -- NO IMAGE")

            try:
                # Restore annotation
                self.ui.te_annotations.clear()
                if self.ui.actionEnable_annotations.isChecked() and (
                    self._src_image_wrapper is not None
                ):
                    self.restore_annotation(
                        self._src_image_wrapper, self._src_image_wrapper.experiment
                    )
            except Exception as e:
                self._src_image_wrapper = None
                logger.exception(f"Failed to load/save annotation: {repr(e)}")

            if self._src_image_wrapper is not None:
                self._updating_process_modes = True
                try:
                    self._file_name = value

                    self._image_dict = None
                    selected_mode = self.current_tool
                    if selected_mode is not None:
                        selected_mode.update_inputs(
                            update_values=self.build_param_overrides(
                                wrapper=self._src_image_wrapper, tool=selected_mode
                            )
                        )
                        if (
                            (selected_mode is not None)
                            and selected_mode.real_time
                            and self.selected_run_tab != _TAB_PIPELINE_V2
                        ):
                            self.run_process(
                                wrapper=self._src_image_wrapper, ipt=selected_mode
                            )
                        elif not self._batch_is_active:
                            img = self._src_image_wrapper.current_image
                            if self._src_image_wrapper.good_image:
                                self.ui.gv_output_image.main_image = img
                    self.ui.edt_csv_file_name.setText(
                        f"{self._src_image_wrapper.experiment}_raw_data"
                    )
                except Exception as e:
                    self._file_name = ""
                    self.setWindowTitle(f"{_PRAGMA_FULL_NAME} -- Select input file")
                    logger.exception(f"Failed to load/save annotation: {repr(e)}")
                finally:
                    self._updating_process_modes = False
            else:
                self._file_name = ""
                self.setWindowTitle(f"{_PRAGMA_FULL_NAME} -- Select input file")

    @property
    def current_tool(self):
        return self._current_tool

    @current_tool.setter
    def current_tool(self, value):
        if self._current_tool != value:
            self._current_tool = value
            self._updating_process_modes = True
            try:
                # Delete existing widgets
                lst = self._ip_tools_holder.ipt_list
                for ipt_ in lst:
                    if ipt_.name == value.name:
                        self.ui.bt_select_tool.setText(ipt_.name)
                    for p in ipt_.gizmos:
                        p.clear_widgets()
                for i in reversed(range(self.ui.gl_tool_params.count())):
                    self.ui.gl_tool_params.itemAt(i).widget().setParent(None)

                # Update script generator menu
                self.ui.action_add_exposure_fixer.setEnabled(
                    ipc.ToolFamily.EXPOSURE_FIXING in value.use_case
                )
                self.ui.action_add_white_balance_corrector.setEnabled(
                    ipc.ToolFamily.WHITE_BALANCE in value.use_case
                )
                self.ui.actionAdd_white_balance_fixer.setEnabled(
                    ipc.ToolFamily.PRE_PROCESSING in value.use_case
                )
                self.ui.actionAdd_channel_mask.setEnabled(
                    ipc.ToolFamily.THRESHOLD in value.use_case
                )
                self.ui.action_build_roi_with_raw_image.setEnabled(
                    bool(
                        set(value.use_case)
                        & {
                            ipc.ToolFamily.ROI,
                        }
                    )
                )
                self.ui.action_build_roi_with_pre_processed_image.setEnabled(
                    bool(
                        set(value.use_case)
                        & {
                            ipc.ToolFamily.ROI,
                        }
                    )
                )
                self.ui.actionSet_contour_cleaner.setEnabled(
                    ipc.ToolFamily.MASK_CLEANUP in value.use_case
                )
                self.ui.action_add_feature_extractor.setEnabled(
                    ipc.ToolFamily.FEATURE_EXTRACTION in value.use_case
                )
                self.ui.action_add_image_generator.setEnabled(
                    ipc.ToolFamily.IMAGE_GENERATOR in value.use_case
                )

                # Add new widgets
                for row_, param in enumerate(value.gizmos):
                    widget, label = self.init_param_widget(tool=value, param=param)
                    if label and widget:
                        self.ui.gl_tool_params.addWidget(label, row_, 0)
                        self.ui.gl_tool_params.addWidget(widget, row_, 1)
                    elif widget:
                        self.ui.gl_tool_params.addWidget(widget, row_, 0, 1, 2)
                    elif label:
                        self.ui.gl_tool_params.addWidget(label, row_, 0, 1, 2)
                    else:
                        pass

                    self.process_events()
                value.update_inputs(
                    update_values=self.build_param_overrides(
                        wrapper=self._src_image_wrapper, tool=value
                    )
                )

            except Exception as e:
                logger.exception(f"Failed to initialize tool: {repr(e)}")
            finally:
                self._updating_process_modes = False
            if (
                not self._initializing
                and value.real_time
                and self._src_image_wrapper is not None
            ):
                self.run_process(wrapper=self._src_image_wrapper, ipt=value)

    @property
    def selected_main_tab(self):
        return self.tabWidget.currentWidget().objectName()

    @selected_main_tab.setter
    def selected_main_tab(self, value):
        try:
            self.tabWidget.setCurrentWidget(self.tabWidget.findChild(QWidget, value))
        except TypeError as e:
            logger.exception(f'Unable to select tab "{value}": {repr(e)}')
            self.tabWidget.setCurrentIndex(0)
        except AttributeError as e:
            logger.exception(f'Unable to select tab "{value}": {repr(e)}')
            self.tabWidget.setCurrentIndex(0)

    @property
    def selected_run_tab(self):
        return self.ui.tb_tool_script.currentWidget().objectName()

    @selected_run_tab.setter
    def selected_run_tab(self, value):
        try:
            self.ui.tb_tool_script.setCurrentWidget(
                self.ui.tb_tool_script.findChild(QWidget, value)
            )
        except TypeError as e:
            logger.exception(f'Unable to select tab "{value}": {repr(e)}')
            self.ui.tb_tool_script.setCurrentIndex(0)
        except AttributeError as e:
            logger.exception(f'Unable to select tab "{value}": {repr(e)}')
            self.ui.tb_tool_script.setCurrentIndex(0)

    @property
    def pipeline(self) -> LoosePipeline:
        model = self.ui.tv_pp_view.model()
        if model is not None:
            return model.pipeline
        else:
            return None

    @pipeline.setter
    def pipeline(self, value: LoosePipeline):
        if value is not None and (
            not value.image_output_path or not os.path.isdir(value.image_output_path)
        ):
            value.image_output_path = ipso_folders.get_path("image_output")
        model = PipelineModel(
            pipeline=value,
            call_backs=dict(
                set_text=self.widget_set_text,
                set_value=self.widget_set_value,
                add_items=self.widget_add_items,
                set_range=self.widget_set_range,
                set_checked=self.widget_set_checked,
                set_name=self.widget_set_name,
                set_tool_tip=self.widget_set_tool_tip,
                clear=self.widget_clear,
                update_table=self.widget_update_table,
                set_current_index=self.widget_set_current_index,
                connect_call_back=self.widget_connect,
                run_callback=self.widget_run_module,
                run_grid_search_callback=self.widget_run_grid_search,
                run_grid_search=None,
            ),
            do_feedback=self.update_feedback,
        )
        model.dataChanged.connect(self.on_pp_data_changed)
        self.ui.tv_pp_view.setUniformRowHeights(False)
        self.ui.tv_pp_view.setModel(model)
        self.ui.tb_pp_desc.clear()
        if value is not None and model is not None:
            selectionModel = self.ui.tv_pp_view.selectionModel()
            selectionModel.selectionChanged.connect(self.on_tv_pp_view_selection_changed)
            self.ui.tv_pp_view.setItemDelegate(
                PipelineDelegate(parent=self.ui.tv_pp_view)
            )
            self.ui.tv_pp_view.header().setStretchLastSection(False)
            self.ui.tv_pp_view.header().setSectionResizeMode(0, QHeaderView.Stretch)
            self.ui.tv_pp_view.header().setSectionResizeMode(
                1, QHeaderView.ResizeToContents
            )
            self.ui.tv_pp_view.header().setSectionResizeMode(
                2, QHeaderView.ResizeToContents
            )
            self.ui.tv_pp_view.setColumnWidth(1, 12)
            self.ui.tv_pp_view.setColumnWidth(2, 12)

            index = model.createIndex(2, 0, model.rootNodes[2])
            self.ui.tv_pp_view.selectionModel().selection().select(index, index)
            self.ui.tv_pp_view.expand(index)
            self.ui.tb_pp_desc.insertPlainText(value.description)
            self._update_pp_pipeline_state(default_process=False, pipeline=True)
            self.pp_set_spanning()
        else:
            self._update_pp_pipeline_state(default_process=True, pipeline=False)

    @property
    def current_database(self) -> dbb.DbWrapper:
        return self._current_database

    @current_database.setter
    def current_database(self, value):
        if value is None:
            self._current_database = None
            self.clear_exp_combo_box()
        else:
            reset_selection = (
                self._current_database is not None
                and self._current_database.db_qualified_name != value.db_qualified_name
            )
            changed_ = self._current_database != value
            self._current_database = value.copy()
            if changed_:
                if self._current_database is None:
                    self.update_feedback(
                        status_message="Not connected to a database or file system",
                        use_status_as_log=True,
                    )
                elif self._current_database.db_qualified_name:
                    self.update_feedback(
                        status_message=f"Connected to {self._current_database.db_qualified_name}",
                        use_status_as_log=True,
                    )
                else:
                    self.update_feedback(
                        status_message=f"Displaying contents of {self._current_database.src_files_path}",
                        use_status_as_log=True,
                    )
            if not self._initializing:
                self.update_comboboxes(
                    {
                        k: v
                        for k, v in zip(
                            "Experiment, Plant, Date, Time, Camera, view_option".replace(
                                " ", ""
                            ).split(","),
                            ["", "", dt.now().date(), dt.now().time(), "", ""],
                        )
                    },
                    reset_selection=reset_selection,
                )
                if changed_:
                    logger.info("Removing old images in browser")
                    self.on_bt_clear_selection()
