import csv
import gc
import glob
import itertools
import json
import multiprocessing as mp
import os
import random
import string
import sys
import threading
import traceback
from collections import Counter, defaultdict, namedtuple
from datetime import datetime as dt
from timeit import default_timer as timer
from typing import Any
import shutil
import subprocess
from version import __version__

import cv2
import numpy as np
import pandas as pd
import pkg_resources
import psutil
from unidecode import unidecode

from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import (
    QObject,
    QRunnable,
    QSettings,
    Qt,
    QThread,
    QThreadPool,
    QTimer,
    pyqtSignal,
    QItemSelectionModel,
    pyqtSlot,
)
from PyQt5.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QIcon,
    QImage,
    QPalette,
    QPixmap,
    QShowEvent,
    QTextCursor,
    QTextOption,
)
from PyQt5.QtWidgets import (
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
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSlider,
    QSpinBox,
    QSplashScreen,
    QStyleFactory,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QGridLayout,
    QSplitter,
    QToolButton,
    QToolTip,
    QTreeWidgetItem,
    QTreeWidgetItemIterator,
    QVBoxLayout,
    QWidget,
    QListWidgetItem,
    QTextEdit,
    QTableView,
    qApp,
)

from ip_base.ip_abstract import AbstractImageProcessor
from ip_base.ipt_abstract import IptBase, IptParamHolder
from ip_base.ipt_abstract_analyzer import IptBaseAnalyzer
from ip_base.ipt_functional import call_ipt_code
from ip_base.ipt_holder import IptHolder
from ip_base.ipt_strict_pipeline import IptStrictPipeline
from ip_base.ipt_loose_pipeline import LoosePipeline, GroupNode, ModuleNode, pp_last_error
import ip_base.ip_common as ipc

from class_pipelines.ip_factory import ipo_factory

from file_handlers.fh_base import file_handler_factory

from tools.regions import RectangleRegion, AbstractRegion
from tools.comand_line_wrapper import ArgWrapper
from tools.common_functions import (
    force_directories,
    format_time,
    make_safe_name,
    natural_keys,
    open_file,
)
import tools.db_wrapper as dbw
from tools.error_holder import ErrorHolder
from tools.paths_factory import get_folders_paths
from tools.pipeline_processor import PipelineProcessor

from ui_qt import ui_consts
from ui_qt.about_form import Ui_about_dialog
from ui_qt.frm_folder_selector import Ui_folder_selector
from ui_qt.frm_new_tool import Ui_dlg_new_tool
from ui_qt.qt_mvc import (
    CTreeWidget,
    CTreeWidgetItem,
    QLineEditWthParam,
    QMouseGraphicsView,
    QPushButtonWthParam,
    build_widgets,
    QPandasModel,
    QPandasColumnsModel,
    QImageDatabaseModel,
    PipelineModel,
    QColorDelegate,
    QImageDrawerDelegate,
    PipelineDelegate,
)
from ui_qt.q_thread_handlers import IpsoCsvBuilder, IpsoMassRunner, IpsoRunnable


Ui_MainWindow, QtBaseClass = uic.loadUiType(
    uifile="./ui_qt/main_form.ui", from_imports=True, import_from="ui_qt"
)

_DATE_FORMAT = "%Y/%m/%d"
_TIME_FORMAT = "%H:%M:%S"

_TAB_TOOLS = "tab_tools"
_TAB_PIPELINE = "tab_pipeline"
_TAB_PIPELINE_V2 = "tb_pipeline_v2"
_TAB_SCRIPT = "tab_script"

_ACTIVE_SCRIPT_TAG = "Active script"

_IMAGE_LISTS_PATH = "./saved_data/image_lists.json"

_PRAGMA_NAME = "IPSO Phen"
_PIPELINE_FILE_FILTER = f"""{_PRAGMA_NAME} All available ( *.json *.tipp)
;;JSON compatible file (*.json);;pipelines (*.tipp)"""


def excepthook(excType, excValue, tracebackobj):
    """
    Global function to catch unhandled exceptions.

    @param excType exception type
    @param excValue exception value
    @param tracebackobj traceback object
    """
    print(f"{excType} - {excValue}")
    print("_________________")
    traceback.print_exception(excType, excValue, sys.last_traceback)
    print("_________________")


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
        args[0].update_feedback(
            status_message="",
            log_message=f"{ui_consts.LOG_TIMING_STR} Method {f.__name__} took {format_time(after - before)}",
        )
        return x

    return time_wrapper


class AboutDialog(Ui_about_dialog):
    def set_version(self):
        self.lb_version.setText(f"Version: {__version__}")

    def set_copyright(self):
        self.lbl_copyright.setText("Unpublished work (c) 2018-2019 INRA.")

    def set_authors(self):
        self.lbl_authors.setText("Authors: Felicià Antoni Maviane Macia")

    def set_used_packages(self):
        self.txt_brw_used_packages.clear()
        with open(os.path.join(os.getcwd(), "licenses.html")) as licenses_:
            self.txt_brw_used_packages.insertHtml(licenses_.read())
            self.txt_brw_used_packages.verticalScrollBar().setValue(
                self.txt_brw_used_packages.verticalScrollBar().minimum()
            )
        self.txt_brw_used_packages.moveCursor(QTextCursor.Start, 0)


class NewToolDialog(QDialog):
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
        for k, v in ipc.tool_group_hints.items():
            if k in ipc.tool_groups_pipeline:
                cb = QCheckBox(k)
                cb.setToolTip(v)
            else:
                continue
            self.check_boxes[k] = cb
            grp_layout.addWidget(cb)
        self.ui.gb_pipeline_tool_groups.setLayout(grp_layout)

        grp_layout = QVBoxLayout()
        for k, v in ipc.tool_group_hints.items():
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
        # Update icon
        if os.path.isfile(os.path.join("./ip_tools", file_name)):
            # self.ui.bt_save.setEnabled(False)
            self.ui.lbl_file_exists.setPixmap(QPixmap("./resources/Error.png"))
        else:
            # self.ui.bt_save.setEnabled(True)
            self.ui.lbl_file_exists.setPixmap(QPixmap("./resources/OK.png"))
        # Update file name
        self.ui.le_file_name.setText(file_name)
        # Update class name
        self.ui.le_class_name.setText("".join(x.capitalize() for x in base_name.split("_")))

    def build_file(self):
        def add_tab(sc: str) -> str:
            return sc + "    "

        def remove_tab(sc: str) -> str:
            return sc[4:]

        file_path = os.path.join("./ip_tools", self.ui.le_file_name.text())
        with open(file_path, "w", encoding="utf8") as f:
            spaces = ""

            # Imports
            if (
                self.check_boxes[ipc.TOOL_GROUP_FEATURE_EXTRACTION_STR].isChecked()
                or self.check_boxes[ipc.TOOL_GROUP_IMAGE_GENERATOR_STR].isChecked()
            ):
                f.write(f"{spaces}from ip_base.ipt_abstract_analyzer import IptBaseAnalyzer\n")
                inh_class_name_ = "IptBaseAnalyzer"
            else:
                f.write(f"{spaces}from ip_base.ipt_abstract import IptBase\n")
                inh_class_name_ = "IptBase"
            f.write(f"\n\n")

            # Class
            f.write(f"{spaces}class {self.ui.le_class_name.text()}({inh_class_name_}):\n")
            f.write(f"\n")

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
            if self.check_boxes[ipc.TOOL_GROUP_IMAGE_GENERATOR_STR].isChecked():
                f.write(f"{spaces}self.add_text_input(\n")
                spaces = add_tab(spaces)
                f.write(f'{spaces}name="path",\n')
                f.write(f'{spaces}desc="Target folder",\n')
                f.write(f'{spaces}default_value="",\n')
                f.write(f'{spaces}hint="Can be overridden at process call",\n')
                spaces = remove_tab(spaces)
                f.write(f"{spaces})\n")
            f.write(f"\n")

            # Process image
            spaces = add_tab("")
            f.write(f"{spaces}def process_wrapper(self, **kwargs):\n")
            spaces = add_tab(spaces)
            f.write(f"{spaces}wrapper = self.init_wrapper(**kwargs)\n")
            f.write(f"{spaces}if wrapper is None:\n")
            f.write(f"{spaces}    return False\n")
            f.write(f"\n")
            f.write(f"{spaces}res = False\n")
            f.write(f"{spaces}try:\n")
            spaces = add_tab(spaces)
            f.write(f"{spaces}if self.get_value_of('enabled') == 1:\n")
            spaces = add_tab(spaces)
            f.write(f"{spaces}img = wrapper.current_image\n")
            if self.ui.chk_mask_required.isChecked():
                f.write(f"{spaces}mask = wrapper.mask\n")
                f.write(f"{spaces}if mask is None:\n")
                f.write(
                    f"""{spaces}    wrapper.error_holder.add_error(
                        'Failure {self.ui.le_tool_name.text()}: mask must be initialized')\n"""
                )
                f.write(f"{spaces}    return\n")
            f.write(f"\n")
            f.write(f"{spaces}# Write your code here\n")
            f.write(f"{spaces}wrapper.store_image(img, 'current_image')\n")
            f.write(f"{spaces}res = True\n")
            spaces = remove_tab(spaces)
            f.write(f"{spaces}else:\n")
            f.write(f"{spaces}    wrapper.store_image(wrapper.current_image, 'current_image')\n")
            f.write(f"{spaces}    res = True\n")
            spaces = remove_tab(spaces)
            f.write(f"{spaces}except Exception as e:\n")
            f.write(f"{spaces}    res = False\n")
            f.write(
                f"{spaces}"
                + "    wrapper.error_holder.add_error("
                + "f"
                + f'"{self.ui.le_tool_name.text()} FAILED'
                + ', exception: {repr(e)}")\n'
            )
            f.write(f"{spaces}else:\n")
            f.write(f"{spaces}    pass\n")
            f.write(f"{spaces}finally:\n")
            f.write(f"{spaces}    return res\n")
            spaces = remove_tab(spaces)
            f.write(f"\n")

            # Properties
            spaces = add_tab("")
            f.write(f"{spaces}@property\n")
            f.write(f"{spaces}def name(self):\n")
            f.write(f"{spaces}    return '{self.ui.le_tool_name.text()} (WIP)'\n")
            f.write(f"\n")

            f.write(f"{spaces}@property\n")
            f.write(f"{spaces}def package(self):\n")
            f.write(f"{spaces}    return '{self.ui.le_package_name.text()}'\n")
            f.write(f"\n")

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
            f.write(f"\n")

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
            f.write(f"\n")

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
            f.write(f"\n")

            f.write(f"{spaces}@property\n")
            f.write(f"{spaces}def use_case(self):\n")
            use_cases_ = ", ".join(
                [
                    f"'{k}'"
                    for k, _ in ipc.tool_group_hints.items()
                    if k in self.check_boxes and self.check_boxes[k].isChecked()
                ]
            )
            f.write(f"{spaces}    return [{use_cases_}]\n")
            f.write(f"\n")

            f.write(f"{spaces}@property\n")
            f.write(f"{spaces}def description(self):\n")
            desc = self.ui.te_description.toPlainText().replace("'", " ").replace('"', " ")
            f.write(f"{spaces}    return '{desc}'\n")

        subprocess.run(args=("black", file_path))

    def cancel_tool(self):
        self.close()


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
        self.db_file_name = self.folder_path

    def on_db_name_changed(self, text):
        self._db_name_changed = True
        self.db_file_name = text

    def on_folder_selected(self):
        self.folder_path = str(
            QFileDialog.getExistingDirectory(
                parent=self, caption="Select folder containing images", directory=self.folder_path
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
                self.db_file_name = self.folder_path
        else:
            self.db_file_name = ""

    @property
    def db_file_name(self):
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

    @db_file_name.setter
    def db_file_name(self, value):
        if not self._db_name_changed:
            if self.dbms == "none":
                self.ui.edt_db_name.setText("NA")
                return
            elif self.dbms == "sqlite":
                value = make_safe_name(value)
            elif self.dbms == "psql":
                value = os.path.basename(os.path.normpath(value))
        val = "".join(c if c in string.ascii_letters or c in string.digits else "_" for c in value)
        if val != value:
            QToolTip.showText(
                self.ui.edt_db_name.mapToGlobal(self.ui.edt_db_name.rect().center()),
                "Only letters numbers and underscores are allowed",
            )
        self.ui.edt_db_name.setText(val)


class IpsoMainForm(QtWidgets.QMainWindow, Ui_MainWindow):
    @log_method_execution_time
    def __init__(self):

        self._reset_log_counts()

        self._initializing = True
        self._working = False
        self._updating_saved_image_lists = False
        self._process_in_progress = False
        self._current_database = None
        self._current_tool = None
        self._script_generator = None
        self._file_name = ""
        self.multithread = True
        self.use_pipeline_cache = True

        root_ipso_folder = "ipso_phen_data"
        self.dynamic_folders = {
            "pipeline": os.path.join(
                os.path.expanduser("~"), "Documents", root_ipso_folder, "pipelines", ""
            ),
            "csv": os.path.join(
                os.path.expanduser("~"), "Documents", root_ipso_folder, "saved_csv", ""
            ),
            "image_list": os.path.join(
                os.path.expanduser("~"), "Documents", root_ipso_folder, "image_lists", ""
            ),
            "pp_output": os.path.join(
                os.path.expanduser("~"), "Documents", root_ipso_folder, "pipeline_output", ""
            ),
            "pp_state": os.path.join(
                os.path.expanduser("~"), "Documents", root_ipso_folder, "pipeline_state", ""
            ),
            "db_image_folder": os.path.join(os.path.expanduser("~"), "Documents", ""),
        }
        force_directories(self.dynamic_folders["pipeline"])
        force_directories(self.dynamic_folders["csv"])
        force_directories(self.dynamic_folders["image_list"])
        force_directories(self.dynamic_folders["pp_output"])
        force_directories(self.dynamic_folders["pp_state"])
        self.static_folders = {
            "image_cache": os.path.join(
                os.path.expanduser("~"), "Pictures", root_ipso_folder, "cache", ""
            ),
            "image_output": os.path.join(
                os.path.expanduser("~"),
                "Pictures",
                root_ipso_folder,
                "saved_images",
                dt.now().strftime("%Y_%B_%d-%H%M%S"),
                "",
            ),
            "script": "./script_pipelines/",
            "saved_data": "./saved_data/",
            "stored_data": "./stored_data/",
            "sql_db": os.path.join(
                os.path.expanduser("~"), "Documents", root_ipso_folder, "sqlite_databases", ""
            ),
        }
        force_directories(self.static_folders["image_cache"])
        force_directories(self.static_folders["image_output"])
        force_directories(self.static_folders["saved_data"])
        force_directories(self.static_folders["stored_data"])
        force_directories(self.static_folders["script"])
        force_directories(self.static_folders["sql_db"])

        self._options = ArgWrapper(
            dst_path=self.static_folders["image_output"],
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

        self._batch_stop_current = False
        self._batch_is_in_progress = False
        self._batch_last_processed = False
        self._batch_is_active = False
        self.mnu_db_action_group = None

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

        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)

        # Start splash screen
        if not ui_consts.DISABLE_SPLASH_SCREEN:
            splash_pic_ = QPixmap("./resources/splash_600px.png")
            self._splash = QSplashScreen(self, splash_pic_, Qt.WindowStaysOnTopHint)
            self._pg_splash = QProgressBar(self._splash)
            self._pg_splash.setMaximum(100)
            self._pg_splash.setGeometry(
                10, splash_pic_.height() - 20, splash_pic_.width() - 20, 18
            )
            self._lbl_splash = QLabel(self._splash)
            self._lbl_splash.setText(f"{_PRAGMA_NAME}")
            self._lbl_splash.setFont(QFont("Times", 40, QFont.Bold))
            self._lbl_splash.setGeometry(
                splash_pic_.width() - 340, splash_pic_.height() - 150, splash_pic_.width() - 20, 80
            )
            self._splash.show()
        else:
            self._splash = None

        self.text_color = QColor(0, 0, 0)
        self.background_color = QColor(255, 255, 255)

        self.tv_queued_tools = CTreeWidget()
        self.tv_queued_tools.setHeaderHidden(True)
        self.tv_queued_tools.setHeaderLabels(["Key", "Value", "Action", "up", "down", "Delete"])
        self.gl_pipeline_data.addWidget(self.tv_queued_tools, 1, 0, 1, 7)

        self.gv_last_processed_item = QMouseGraphicsView(self)
        self.ver_layout_last_image.addWidget(self.gv_last_processed_item)

        self.gv_source_image = QMouseGraphicsView(self.spl_ver_main_tab_source)
        self.gv_output_image = QMouseGraphicsView(self.spl_ver_main_img_data)

        self.tw_script_sim_output = QtWidgets.QTableWidget(self.spl_ver_main_img_data)
        self.tw_script_sim_output.setFrameShadow(QtWidgets.QFrame.Plain)
        self.tw_script_sim_output.setAlternatingRowColors(True)
        self.tw_script_sim_output.setObjectName("tw_script_sim_output")
        self.tw_script_sim_output.setColumnCount(2)
        self.tw_script_sim_output.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.tw_script_sim_output.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.tw_script_sim_output.setHorizontalHeaderItem(1, item)
        self.tw_script_sim_output.horizontalHeader().setStretchLastSection(True)
        self.tw_script_sim_output.verticalHeader().setStretchLastSection(False)
        self.tw_script_sim_output.setSortingEnabled(False)
        item = self.tw_script_sim_output.horizontalHeaderItem(0)
        item.setText("Key")
        item = self.tw_script_sim_output.horizontalHeaderItem(1)
        item.setText("Value")
        self.tw_script_sim_output.horizontalHeader().setStretchLastSection(True)
        self.tw_script_sim_output.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Data editor
        self.gv_de_image = QMouseGraphicsView(self.spl_de_left)
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

        self.setWindowIcon(QIcon("./resources/leaf-24.ico"))

        self.statusBar().addWidget(self._status_label, stretch=0)

        # Build tools selectors
        def update_font_(op, act):
            if "(wip)" in op.name.lower():
                fnt = act.font()
                fnt.setBold(True)
                act.setFont(fnt)

        self._ip_tools_holder = IptHolder()
        try:
            if hasattr(self, "bt_select_tool"):
                tool_menu = QMenu()
                if ui_consts.FLAT_TOOLS_MENU:
                    lst = self._ip_tools_holder.ipt_list
                    for op in lst:
                        act = QAction(op.name, self)
                        act.setToolTip(op.hint)
                        update_font_(op, act)
                        tool_menu.addAction(act)
                else:
                    for use_case in self._ip_tools_holder.use_cases:
                        if use_case == "none":
                            continue
                        # Menu items
                        use_case_root = tool_menu.addMenu(use_case)
                        use_case_root.setToolTip(ipc.tool_group_hints.get(use_case, ""))
                        op_lst = self._ip_tools_holder.list_by_use_case(use_case)
                        for op in op_lst:
                            act = QAction(op.name, self)
                            act.setToolTip(op.hint)
                            update_font_(op, act)
                            use_case_root.addAction(act)
                        use_case_root.setToolTipsVisible(True)
                tool_menu.triggered[QAction].connect(self.on_menu_tool_selection)
                tool_menu.setToolTipsVisible(True)
                self.bt_select_tool.setMenu(tool_menu)

            if hasattr(self, "bt_pp_select_tool"):
                tool_menu = QMenu()
                # Image processing tools
                for use_case in self._ip_tools_holder.use_cases:
                    if use_case == "none":
                        continue
                    op_lst = [
                        op
                        for op in self._ip_tools_holder.list_by_use_case(use_case)
                        if bool(set(op.use_case).intersection(set(ipc.tool_groups_pipeline)))
                    ]
                    if op_lst:
                        use_case_root = tool_menu.addMenu(use_case)
                        for op in op_lst:
                            act = QAction(op.name, self)
                            act.setToolTip(op.hint)
                            update_font_(op, act)
                            use_case_root.addAction(act)
                        use_case_root.setToolTip(ipc.tool_group_hints.get(use_case, ""))
                        use_case_root.setToolTipsVisible(True)
                        use_case_root.triggered[QAction].connect(self.on_bt_pp_add_tool)
                # Groups
                tool_menu.addSeparator()
                act = QAction("Default empty group", self)
                act.setToolTip("Add an empty group with default settings")
                act.triggered.connect(self.on_bt_pp_add_tool)
                tool_menu.addAction(act)
                group_root = tool_menu.addMenu("Pre filled groups")
                for name, hint in zip(
                    [
                        "Fix exposure",
                        "Pre process image",
                        "Threshold",
                        "Mask cleanup",
                        "Feature extraction",
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
                    ],
                ):
                    act = QAction(name, self)
                    act.setToolTip(hint)
                    group_root.addAction(act)
                group_root.triggered[QAction].connect(self.on_bt_pp_add_tool)

                tool_menu.setToolTipsVisible(True)
                self.bt_pp_select_tool.setMenu(tool_menu)

            for use_case in self._ip_tools_holder.use_cases:
                if use_case == "none":
                    continue
                # Menu items
                use_case_root = self.mnu_tools_root.addMenu(use_case)
                use_case_root.setToolTip(ipc.tool_group_hints.get(use_case, ""))
                op_lst = self._ip_tools_holder.list_by_use_case(use_case)
                for op in op_lst:
                    act = QAction(op.name, self)
                    act.setToolTip(op.hint)
                    use_case_root.addAction(act)
                use_case_root.setToolTipsVisible(True)
            self.mnu_tools_root.setToolTipsVisible(True)
            self.mnu_tools_root.triggered[QAction].connect(self.on_menu_tool_selection)
        except Exception as e:
            self.log_exception(f"Failed to load tools: {repr(e)}")

        # Build database selectors
        self.current_database = None
        self.distant_databases = []
        self.local_databases = []
        self.recent_folders = []

        # Make the connections
        # SQL checkboxes
        self.cb_experiment.currentIndexChanged.connect(self.cb_experiment_current_index_changed)
        self.cb_plant.currentIndexChanged.connect(self.cb_plant_current_index_changed)
        self.cb_date.currentIndexChanged.connect(self.cb_date_current_index_changed)
        self.cb_camera.currentIndexChanged.connect(self.cb_camera_current_index_changed)
        self.cb_view_option.currentIndexChanged.connect(self.cb_view_option_current_index_changed)
        self.cb_time.currentIndexChanged.connect(self.cb_time_current_index_changed)

        self.cb_available_outputs.currentIndexChanged.connect(
            self.cb_available_outputs_current_index_changed
        )

        # Selection handler
        self.bt_add_to_selection.clicked.connect(self.on_bt_add_to_selection)
        self.bt_add_random.clicked.connect(self.on_bt_add_random)
        self.bt_clear_selection.clicked.connect(self.on_bt_clear_selection)
        self.bt_remove_from_selection.clicked.connect(self.on_bt_remove_from_selection)
        self.bt_keep_annotated.clicked.connect(self.on_bt_keep_annotated)

        # Toolbox
        self.bt_process_image.clicked.connect(self.on_bt_process_image)
        self.bt_reset_op.clicked.connect(self.on_bt_reset_op)
        self.bt_run_grid_search.clicked.connect(self.on_bt_run_grid_search)
        self.bt_reset_grid_search.clicked.connect(self.on_bt_reset_grid_search)
        self.bt_update_grid_search.clicked.connect(self.on_bt_update_grid_search)
        self.chk_use_pipeline_as_preprocessor.stateChanged.connect(
            self.on_chk_use_pipeline_as_preprocessor
        )

        self.bt_clear_result.clicked.connect(self.on_bt_clear_result)

        # Batches
        self.bt_launch_batch.clicked.connect(self.on_bt_launch_batch)
        self.lw_last_batch.itemSelectionChanged.connect(self.on_itemSelectionChanged)
        self.bt_set_batch_as_selection.clicked.connect(self.on_bt_set_batch_as_selection)

        # Images browser
        self.tv_image_browser.doubleClicked.connect(self.on_tv_image_browser_double_clicked)

        # Annotations
        self.bt_delete_annotation.clicked.connect(self.on_bt_delete_annotation)

        # Menu
        self.action_new_tool.triggered.connect(self.on_action_new_tool)
        self.actionSave_selected_image.triggered.connect(self.on_bt_save_current_image)
        self.actionSave_all_images.triggered.connect(self.on_bt_save_all_images)
        self.action_save_image_list.triggered.connect(self.on_action_save_image_list)
        self.action_load_image_list.triggered.connect(self.on_action_load_image_list)
        self.actionExit.triggered.connect(self.close_application)
        self.actionEnable_annotations.triggered.connect(self.on_action_enable_annotations_checked)
        self.act_parse_folder_memory.triggered.connect(self.on_action_parse_folder)
        self.action_build_video_from_images.triggered.connect(
            self.on_action_build_video_from_images
        )
        self.action_new_script.triggered.connect(self.on_bt_clear_pipeline)
        self.action_load_script.triggered.connect(self.on_bt_load_pipeline)
        self.action_save_script.triggered.connect(self.on_bt_save_pipeline)
        self.action_save_as_python_script.triggered.connect(self.on_action_save_as_python_script)
        self.action_create_wrapper_before.triggered.connect(self.on_action_create_wrapper_before)
        self.action_standard_object_oriented_call.triggered.connect(
            self.on_action_standard_object_oriented_call
        )
        self.action_object_oriented_wrapped_with_a_with_clause.triggered.connect(
            self.on_action_object_oriented_wrapped_with_a_with_clause
        )
        self.action_functional_style.triggered.connect(self.on_action_functional_style)
        self.action_about_form.triggered.connect(self.on_action_about_form)
        self.action_use_dark_theme.triggered.connect(self.on_color_theme_changed)
        self.action_use_multithreading.triggered.connect(self.on_action_use_multithreading)
        self.action_use_pipeline_cache.triggered.connect(self.on_action_use_pipeline_cache)
        self.action_save_pipeline_processor_state.triggered.connect(
            self.on_action_save_pipeline_processor_state
        )

        # Help
        self.action_show_read_me.triggered.connect(self.on_action_show_read_me)
        self.action_show_documentation.triggered.connect(self.on_action_show_documentation)
        self.action_build_tool_documentation.triggered.connect(
            self.on_action_build_tool_documentation
        )
        self.action_build_ipso_phen_documentation.triggered.connect(
            self.on_action_build_ipso_phen_documentation
        )
        self.action_build_test_files.triggered.connect(self.on_action_build_test_files)
        self.action_show_log.triggered.connect(self.on_action_show_log)

        # Video
        self.action_video_1_24_second.triggered.connect(self.on_video_frame_duration_changed)
        self.action_video_half_second.triggered.connect(self.on_video_frame_duration_changed)
        self.action_video_1_second.triggered.connect(self.on_video_frame_duration_changed)
        self.action_video_5_second.triggered.connect(self.on_video_frame_duration_changed)
        self.action_video_res_first_image.triggered.connect(self.on_video_resolution_changed)
        self.action_video_res_1080p.triggered.connect(self.on_video_resolution_changed)
        self.action_video_res_720p.triggered.connect(self.on_video_resolution_changed)
        self.action_video_res_576p.triggered.connect(self.on_video_resolution_changed)
        self.action_video_res_480p.triggered.connect(self.on_video_resolution_changed)
        self.action_video_res_376p.triggered.connect(self.on_video_resolution_changed)
        self.action_video_res_240p.triggered.connect(self.on_video_resolution_changed)
        self.action_video_ar_16_9.triggered.connect(self.on_video_aspect_ratio_changed)
        self.action_video_ar_4_3.triggered.connect(self.on_video_aspect_ratio_changed)
        self.action_video_ar_1_1.triggered.connect(self.on_video_aspect_ratio_changed)
        self.action_video_bkg_color_black.triggered.connect(self.on_action_video_bkg_color_changed)
        self.action_video_bkg_color_white.triggered.connect(self.on_action_video_bkg_color_changed)
        self.action_video_bkg_color_silver.triggered.connect(
            self.on_action_video_bkg_color_changed
        )

        # Pipeline builder
        self.act_settings_sir_keep.triggered.connect(self.on_sis_changed)
        self.act_settings_sir_2x.triggered.connect(self.on_sis_changed)
        self.act_settings_sir_3x.triggered.connect(self.on_sis_changed)
        self.act_settings_sir_4x.triggered.connect(self.on_sis_changed)
        self.act_settings_sir_5x.triggered.connect(self.on_sis_changed)
        self.act_settings_sir_6x.triggered.connect(self.on_sis_changed)

        # Data editor
        self.action_de_new_sheet.triggered.connect(self.on_action_de_new_sheet)
        self.action_de_load_csv.triggered.connect(self.on_action_de_load_csv)
        self.action_de_create_sheet_from_selection.triggered.connect(
            self.on_action_de_create_sheet_from_selection
        )
        self.action_de_add_column.triggered.connect(self.on_action_de_add_column)
        self.action_de_delete_column.triggered.connect(self.on_action_de_delete_column)
        self.action_de_save_csv.triggered.connect(self.on_action_de_save_csv)

        # Script generator
        self.actionAdd_white_balance_fixer.triggered.connect(
            self.on_action_add_white_balance_fixer
        )
        self.action_add_exposure_fixer.triggered.connect(self.on_action_add_exposure_fixer)
        self.action_add_white_balance_corrector.triggered.connect(
            self.on_action_add_white_balance_corrector
        )
        self.action_build_roi_with_raw_image.triggered.connect(
            self.on_action_build_roi_with_raw_image
        )
        self.action_build_roi_with_pre_processed_image.triggered.connect(
            self.on_action_build_roi_with_pre_processed_image
        )
        self.actionAdd_channel_mask.triggered.connect(self.on_actionAdd_channel_mask)
        self.actionSet_contour_cleaner.triggered.connect(self.on_action_set_contour_cleaner)
        self.action_add_feature_extractor.triggered.connect(self.on_action_add_feature_extractor)
        self.action_add_image_generator.triggered.connect(self.on_action_add_image_generator)
        self.bt_clear_pipeline.clicked.connect(self.on_bt_clear_pipeline)
        self.bt_load_pipeline.clicked.connect(self.on_bt_load_pipeline)
        self.bt_save_pipeline.clicked.connect(self.on_bt_save_pipeline)
        self.bt_script_gen_run.clicked.connect(self.on_bt_script_gen_run)
        self.chk_pp_show_last_item.stateChanged.connect(self.on_chk_pp_show_last_item)

        self.bt_update_selection_stats.clicked.connect(self.on_bt_update_selection_stats)

        # Pipeline processor
        self.sl_pp_thread_count.valueChanged.connect(self.on_sl_pp_thread_count_index_changed)
        self.bt_pp_select_output_folder.clicked.connect(self.on_bt_pp_select_output_folder)
        self.bt_pp_select_script.clicked.connect(self.on_bt_load_pipeline)
        self.bt_pp_clear_script.clicked.connect(self.on_bt_clear_pipeline)
        self.bt_pp_reset.clicked.connect(self.on_bt_pp_reset)
        self.bt_pp_start.clicked.connect(self.on_bt_pp_start)
        self.rb_pp_default_process.clicked.connect(self.on_rb_pp_default_process)
        self.rb_pp_active_script.clicked.connect(self.on_rb_pp_active_script)
        self.rb_pp_load_script.clicked.connect(self.on_rb_pp_load_script)

        # Pipeline editor V2
        self.bt_pp_up.setEnabled(False)
        self.bt_pp_down.setEnabled(False)
        self.bt_pp_delete.setEnabled(False)
        self.bt_pp_new.clicked.connect(self.on_bt_pp_new)
        self.bt_pp_load.clicked.connect(self.on_bt_pp_load)
        self.bt_pp_save.clicked.connect(self.on_bt_pp_save)
        self.bt_pp_up.clicked.connect(self.on_bt_pp_up)
        self.bt_pp_down.clicked.connect(self.on_bt_pp_down)
        self.bt_pp_delete.clicked.connect(self.on_bt_pp_delete)
        self.bt_pp_run.clicked.connect(self.on_bt_pp_run)
        self.bt_pp_invalidate.clicked.connect(self.on_bt_pp_invalidate)

        self.sl_pp_thread_count.setMaximum(mp.cpu_count())
        self.sl_pp_thread_count.setMinimum(1)
        self._custom_csv_name = False
        self.on_bt_pp_reset()

        self._settings_ref_count = 0
        self._settings = None
        self.load_settings()

    def _reset_log_counts(self):
        self._log_count_critical = 0
        self._log_count_exception = 0
        self._log_count_warning = 0
        self._log_count_timming = 0
        self._log_count_error = 0
        self._log_count_info = 0
        self._log_count_important = 0
        self._log_count_mass_process = 0
        self._log_count_unknown = 0

    def get_image_model(self) -> QImageDatabaseModel:
        ret = self.tv_image_browser.model()
        return ret if isinstance(ret, QImageDatabaseModel) else None

    def get_image_dataframe(self) -> pd.DataFrame:
        model = self.get_image_model()
        return None if model is None else model.images

    def has_image_dataframe(self) -> bool:
        return self.get_image_dataframe() is not None

    def get_image_delegate(self) -> QImageDrawerDelegate:
        ret = self.tv_image_browser.itemDelegate()
        return ret if isinstance(ret, QImageDrawerDelegate) else None

    def update_images_queue(self):
        df = self.get_image_dataframe()
        self.lw_images_queue.clear()
        if df is None:
            return
        df = df.sort_values(by=["date_time"], axis=0, na_position="first")
        for row in reversed(range(df.shape[0])):
            row_data = {
                k: v
                for k, v in zip(
                    list(df.columns), [str(df.iloc[row, ci]) for ci in range(df.shape[1])]
                )
            }
            new_item = QListWidgetItem()
            new_item.setText(row_data["Luid"])
            new_item.setToolTip("\n".join([f"{k}: {v}" for k, v in row_data.items()]))
            self.lw_images_queue.insertItem(0, new_item)

    def init_image_browser(self, dataframe):
        self.tv_image_browser.setModel(QImageDatabaseModel(dataframe))
        self.tv_image_browser.setItemDelegate(
            QImageDrawerDelegate(
                parent=self.tv_image_browser,
                palette=qApp.palette(),
                use_annotations=self.actionEnable_annotations.isChecked(),
            )
        )
        self.tv_image_browser.setSortingEnabled(True)
        selectionModel = self.tv_image_browser.selectionModel()
        selectionModel.selectionChanged.connect(self.on_tv_image_browser_selection_changed)
        self.update_images_queue()

        model = self.get_image_model()
        if model is not None:
            hh: QHeaderView = self.tv_image_browser.horizontalHeader()
            hh.setMaximumSectionSize(150)
            hh.setMinimumSectionSize(70)
            if model.rowCount() <= 0:
                for i in range(0, hh.count()):
                    hh.resizeSection(i, hh.sectionSizeHint(i))
            else:
                for i in range(0, hh.count()):
                    hh.resizeSection(
                        i, self.tv_image_browser.sizeHintForIndex(model.createIndex(0, i)).width()
                    )
            hh.setMaximumSectionSize(-1)
            self.tv_image_browser.setHorizontalHeader(hh)
            vh: QHeaderView = self.tv_image_browser.verticalHeader()
            vh.setSectionResizeMode(QHeaderView.Fixed)
            self.tv_image_browser.setVerticalHeader(vh)

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
                self.get_image_model().get_cell_data(row_number=current_row, column_name="Luid")
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
                model.rowsInserted.emit(old_row_count, new_row_count)
                self.update_images_queue()
                self.update_feedback(
                    status_message=f"Added {new_row_count - old_row_count} items to image browser",
                    use_status_as_log=True,
                )
        elif mode == "remove":
            if not self.has_image_dataframe():
                return
            else:
                model = self.get_image_model()
                df = model.images
                old_row_count = model.rowCount()
                model.images = df[~df["Luid"].isin(dataframe["Luid"])]
                new_row_count = model.rowCount()
                self.update_images_queue()
                self.update_feedback(
                    status_message=f"Removed {old_row_count - new_row_count} items to image browser",
                    use_status_as_log=True,
                )
        elif mode == "keep":
            if not self.has_image_dataframe():
                return
            else:
                model = self.get_image_model()
                df = model.images
                old_row_count = model.rowCount()
                model.images = df[df["Luid"].isin(dataframe["Luid"])]
                new_row_count = model.rowCount()
                self.update_images_queue()
                self.update_feedback(
                    status_message=f"Removed {old_row_count - new_row_count} items to image browser",
                    use_status_as_log=True,
                )
        elif mode == "clear":
            self.init_image_browser(None)
        else:
            self.log_exception(f'Failed to update image browser, unknown mode "{mode}"')

    def on_action_save_image_list(self):
        file_name_ = QFileDialog.getSaveFileName(
            parent=self,
            caption="Save image list as CSV",
            directory=self.dynamic_folders["image_list"],
            filter="CSV(*.csv)",
        )[0]
        if file_name_:
            self.dynamic_folders["image_list"] = os.path.join(os.path.dirname(file_name_), "")
            model = self.get_image_model()
            if model is not None and model.images.shape[0] > 0:
                model.images.to_csv(file_name_, index=False)

    def on_action_load_image_list(self):
        file_name_ = QFileDialog.getOpenFileName(
            parent=self,
            caption="Load image list from CSV",
            directory=self.dynamic_folders["image_list"],
            filter="CSV(*.csv)",
        )[0]
        if file_name_:
            self.dynamic_folders["image_list"] = os.path.join(os.path.dirname(file_name_), "")
            self.init_image_browser(pd.read_csv(file_name_))

    def build_recent_folders_menu(self, new_folder: str = ""):
        self.mnu_recent_parsed_folders.clear()
        if new_folder:
            if new_folder in self.recent_folders:
                self.recent_folders.remove(new_folder)
            self.recent_folders.insert(0, new_folder)
            if len(self.recent_folders) > 10:
                self.recent_folders.pop()
        act = QAction("Clear", self, checkable=False)
        act.triggered.connect(self.on_recent_folder_clear)
        self.mnu_recent_parsed_folders.addAction(act)
        self.mnu_recent_parsed_folders.addSeparator()
        for fld in self.recent_folders:
            act = QAction(fld, self, checkable=False)
            act.setEnabled(os.path.isdir(fld))
            act.triggered.connect(self.on_recent_folder_select)
            self.mnu_recent_parsed_folders.addAction(act)

    def add_folder_database(
        self, display_name: str, hint: str, enabled: bool, selected: bool = False
    ):
        # Connect action
        act = QAction(display_name, self, checkable=True)
        act.setEnabled(enabled)
        act.setChecked(selected)
        act.setToolTip(hint)
        act.triggered.connect(self.on_local_database_connect)
        self.mnu_connect_to_db.addAction(self.mnu_db_action_group.addAction(act))

    def build_database_menu(self, add_external=False, selected: str = ""):
        self.mnu_connect_to_db.clear()
        self.mnu_db_action_group = QActionGroup(self)
        self.mnu_db_action_group.setExclusive(True)
        for ldb in self.local_databases:
            self.add_folder_database(
                display_name=ldb.display_name,
                hint=f"{ldb.display_name}\n{ldb.db_folder_name}",
                enabled=os.path.isdir(ldb.src_files_path),
                selected=selected == ldb.db_file_name,
            )
        if add_external:
            self.mnu_connect_to_db.addSeparator()
            self.distant_databases = []
            ddb_list = dbw.ReadOnlyDbWrapper(
                user="fmavianemac",
                port=5432,
                password="",
                db_file_name="ipso_db_experiments",
                main_table="TABLE_EXPERIMENTS",
            )
            if ddb_list is not None:
                qr = ddb_list.query(
                    command="SELECT",
                    table="TABLE_EXPERIMENTS",
                    columns="db_file_name, experiment, robot",
                )
                if qr is not None:
                    for ddb in qr:
                        self.distant_databases.append(
                            dbw.DbInfo(
                                display_name=ddb[1],
                                db_file_name=ddb[0],
                                src_files_path="",
                                dbms="psql",
                            )
                        )
                        act = QAction(ddb[1], self, checkable=True)
                        act.setEnabled(True)
                        act.setToolTip(f"Experiment: {ddb[1]}\nRobot:{ddb[2]}")
                        act.triggered.connect(self.on_distant_database_selected)
                        self.mnu_connect_to_db.addAction(self.mnu_db_action_group.addAction(act))

    def do_parse_folder(self, folder_path):
        self.build_recent_folders_menu(new_folder=folder_path)
        self.current_database = dbw.db_info_to_database(
            dbw.DbInfo(
                display_name="Memory database",
                db_file_name=":memory:",
                src_files_path=folder_path,
                dbms="sqlite",
                db_folder_name=self.static_folders["sql_db"],
            ),
        )

    def on_action_parse_folder(self):
        dlg = FrmSelectFolder(self)
        res = dlg.show_modal(default_path=self.dynamic_folders["db_image_folder"])
        if (res == 1) and os.path.isdir(dlg.folder_path):
            if dlg.dbms == "none":
                self.do_parse_folder(dlg.folder_path)
            else:
                ldb = None
                for ldb in self.local_databases:
                    if ldb.src_files_path == dlg.folder_path:
                        self.update_feedback(
                            status_message="Database already exists",
                            log_message=f"""{ui_consts.LOG_WARNING_STR}
                            There's already a database named {ldb.display_name}
                            pointing to {ldb.src_files_path} using {ldb.dbms}.<br>
                            Existing database will be used.""",
                        )
                        self.current_database = dbw.db_info_to_database(ldb)
                        return
                self.dynamic_folders["db_image_folder"] = dlg.folder_path
                new_db = dbw.DbInfo(
                    display_name=dlg.db_file_name,
                    db_file_name=f"{dlg.db_file_name}.db",
                    src_files_path=dlg.folder_path,
                    dbms=dlg.dbms,
                    db_folder_name=self.static_folders["sql_db"],
                )
                self.current_database = dbw.db_info_to_database(new_db)
                self.local_databases.append(new_db)
                self.build_database_menu(
                    add_external=dbw.LOAD_DISTANT_DATABASES, selected=dlg.db_file_name
                )

    def on_distant_database_selected(self, q):
        for ddb in self.distant_databases:
            if ddb.name == self.sender().text():
                print(f"Connecting to experiment {ddb.name} in database {ddb.db_file_name}")
                self.current_database = dbw.ReadOnlyDbWrapper(
                    user=dbw.DB_USER,
                    port=dbw.DB_DEFAULT_PORT,
                    password="",
                    db_file_name=ddb.db_file_name,
                    src_files_path=self.static_folders["image_cache"],
                )
                break

    def on_local_database_connect(self, q):
        for ldb in self.local_databases:
            if ldb.display_name == self.sender().text():
                db = dbw.db_info_to_database(ldb)
                if isinstance(db, str):
                    self.log_exception(f"Unknown DBMS: {db}")
                else:
                    self.current_database = db
                break

    def on_recent_folder_select(self):
        self.do_parse_folder(self.sender().text())

    def on_recent_folder_clear(self):
        self.recent_folders = []
        self.build_recent_folders_menu()

    def update_database(self, db_wrapper: dbw.DbWrapper):
        if db_wrapper is None or not isinstance(db_wrapper, dbw.DbWrapper):
            return False
        self.update_feedback(
            status_message="Building image database",
            log_message=f"Building image database for {repr(db_wrapper)}",
        )
        self.global_progress_start(add_stop_button=True)
        db_wrapper.progress_call_back = self.global_progress_update
        self.set_global_enabled_state(new_state=False, force_enabled=("global_stop_button",))
        self.process_events()
        try:
            db_wrapper.update()
        except Exception as e:
            self.log_exception(f"Failed query database because: {repr(e)}")
            ret = False
        else:
            ret = True
        finally:
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
                command=command, table=table, columns=columns, additional=additional, **kwargs
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
                command=command, table=table, columns=columns, additional=additional, **kwargs
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
            command=command, table=table, columns=columns, additional=additional, **kwargs
        )
        if (ret is not None) and (len(ret) > 0):
            return ret[0]
        else:
            return None

    def set_enabled_database_controls(self, new_state: bool):
        self.cb_experiment.setEnabled(new_state)
        self.cb_plant.setEnabled(new_state)
        self.cb_date.setEnabled(new_state)
        self.cb_camera.setEnabled(new_state)
        self.cb_view_option.setEnabled(new_state)
        self.cb_time.setEnabled(new_state)

        self.chk_experiment.setEnabled(new_state)
        self.chk_plant.setEnabled(new_state)
        self.chk_date.setEnabled(new_state)
        self.chk_camera.setEnabled(new_state)
        self.chk_view_option.setEnabled(new_state)
        self.chk_time.setEnabled(new_state)

        self.bt_add_to_selection.setEnabled(new_state)
        self.bt_add_random.setEnabled(new_state)
        self.bt_remove_from_selection.setEnabled(new_state)

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
            self.log_exception(f"Failed to init global progress bar: {repr(e)}")

    def global_progress_update(self, step, total, process_events: bool = False):
        if timer() - self._last_progress_update > 0.2:
            if self._splash is not None:
                if total == 0:
                    self._pg_splash.setValue(0)
                else:
                    self._pg_splash.setValue(step / total * 100)
            elif self._global_progress_bar is not None:
                if step == 0 and total == 0:
                    self._global_progress_bar.setFormat("Starting")
                    self._global_progress_bar.setValue(0)
                elif step == 1 and total == 1:
                    self._global_progress_bar.setFormat("Done")
                    self._global_progress_bar.setValue(100)
                else:
                    self._global_progress_bar.setFormat(f"{step}/{total}")
                    self._global_progress_bar.setValue(round((min(step, total)) / total * 100))
            self._last_progress_update = timer()
            if process_events:
                self.process_events()

    def global_progress_stop(self):
        self.global_progress_update(1, 1)
        if self._global_stop_button is not None:
            self.statusbar.removeWidget(self._global_stop_button)
        if self._global_progress_bar is not None:
            self.statusbar.removeWidget(self._global_progress_bar)
        if self._global_pb_label is not None:
            self.statusbar.removeWidget(self._global_pb_label)

    def begin_edit_image_browser(self):
        self._updating_image_browser = True
        self.tv_image_browser.setSortingEnabled(False)

    def end_edit_image_browser(self):
        self.tv_image_browser.setSortingEnabled(True)
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
        if isinstance(tag, AbstractImageProcessor):
            luid = tag.luid
        elif isinstance(tag, str):
            luid = tag
        else:
            self.update_feedback(
                status_message="Failed to retrieve annotation data",
                log_message=f"unable to retrieve annotation data for {str(tag)}",
            )
            self.bt_delete_annotation.setEnabled(False)
            return
        data = id.get_annotation(luid=luid, experiment=experiment)
        self.bt_delete_annotation.setEnabled(data is not None)
        if data:
            self.te_annotations.insertPlainText(data.get("text", ""))
            data_kind = data.get("kind", "oops").lower()
            if data_kind == "info":
                self.cb_annotation_level.setCurrentIndex(0)
                icon_ = QIcon(":/annotation_level/resources/Info.png")
            elif data_kind == "ok":
                self.cb_annotation_level.setCurrentIndex(1)
                icon_ = QIcon(":/annotation_level/resources/OK.png")
            elif data_kind == "warning":
                self.cb_annotation_level.setCurrentIndex(2)
                icon_ = QIcon(":/annotation_level/resources/Warning.png")
            elif data_kind == "error":
                self.cb_annotation_level.setCurrentIndex(3)
                icon_ = QIcon(":/annotation_level/resources/Error.png")
            elif data_kind == "critical":
                self.cb_annotation_level.setCurrentIndex(4)
                icon_ = QIcon(":/annotation_level/resources/Danger.png")
            elif data_kind == "source issue":
                self.cb_annotation_level.setCurrentIndex(5)
                icon_ = QIcon(":/annotation_level/resources/Problem.png")
            else:
                self.cb_annotation_level.setCurrentIndex(6)
                icon_ = QIcon(":/annotation_level/resources/Help.png")
        else:
            self.cb_annotation_level.setCurrentIndex(0)
            self.te_annotations.clear()
            icon_ = QIcon()

        self.tw_tool_box.setTabIcon(1, icon_)

    def get_image_list_name(self):
        table = self.tv_image_browser
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
            if "tv_pp_view" in widget.objectName():
                continue
            if widget.objectName() in force_enabled:
                widget.setEnabled(True)
            elif widget.objectName() in force_disabled:
                widget.setEnabled(False)
            else:
                widget.setEnabled(new_state)

        for tab_name_ in [_TAB_TOOLS, _TAB_PIPELINE, _TAB_SCRIPT]:
            tab_widget_ = self.tb_tool_script.findChild(QWidget, tab_name_)
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
                palette.setColor(QPalette.Text, QColor(*ipc.bgr_to_rgb(ipc.C_BLUE_VIOLET)))
                palette.setColor(QPalette.ToolTipText, QColor(*ipc.bgr_to_rgb(ipc.C_CABIN_BLUE)))
                palette.setColor(QPalette.ButtonText, QColor(*ipc.bgr_to_rgb(ipc.C_CYAN)))
                palette.setColor(
                    QPalette.BrightText, QColor(*ipc.bgr_to_rgb(ipc.C_LIGHT_STEEL_BLUE))
                )
                palette.setColor(QPalette.HighlightedText, QColor(*ipc.bgr_to_rgb(ipc.C_PURPLE)))
                palette.setColor(QPalette.Window, QColor(*ipc.bgr_to_rgb(ipc.C_MAROON)))
                palette.setColor(QPalette.Base, QColor(*ipc.bgr_to_rgb(ipc.C_BLACK)))
                palette.setColor(QPalette.AlternateBase, QColor(*ipc.bgr_to_rgb(ipc.C_GREEN)))
                palette.setColor(QPalette.ToolTipBase, QColor(*ipc.bgr_to_rgb(ipc.C_LIME)))
                palette.setColor(QPalette.Button, QColor(*ipc.bgr_to_rgb(ipc.C_ORANGE)))
                palette.setColor(QPalette.Link, QColor(*ipc.bgr_to_rgb(ipc.C_WHITE)))
                palette.setColor(QPalette.Highlight, QColor(*ipc.bgr_to_rgb(ipc.C_SILVER)))
                palette.setColor(QPalette.Highlight, QColor(*ipc.bgr_to_rgb(ipc.C_RED)))
            else:
                self.update_feedback(
                    status_message="Unknown theme",
                    log_message=f'{ui_consts.LOG_ERROR_STR} Unknown theme "{theme}" ignored',
                )
                return

            self.text_color = palette.color(QPalette.Text)
            self.background_color = palette.color(QPalette.Base)
            qApp.setPalette(palette)

            item_delegate = self.tb_ge_dataframe.itemDelegate()
            if item_delegate is not None and hasattr(item_delegate, "set_palette"):
                item_delegate.set_palette(new_palette=qApp.palette())

            item_delegate = self.tv_image_browser.itemDelegate()
            if item_delegate is not None and hasattr(item_delegate, "set_palette"):
                item_delegate.set_palette(new_palette=qApp.palette())

            if self.actionEnable_annotations.isChecked():
                self.on_action_enable_annotations_checked()

        except Exception as e:
            self.log_exception(f"Failed to load set theme: {repr(e)}")
        else:
            self.update_feedback(
                status_message=f"Changed theme to: {style} ({theme})", use_status_as_log=True
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
        settings_ = self.lock_settings()
        try:
            res = True

            # Theme
            self._selected_theme = settings_.value("selected_theme", "dark")
            act_grp = QActionGroup(self)
            act_grp.setExclusive(True)
            # Dark
            act = QAction("dark", self, checkable=True)
            act.setChecked("dark" == self._selected_theme)
            act.triggered.connect(self.on_color_theme_changed)
            self.menu_theme.addAction(act_grp.addAction(act))
            # Light
            act = QAction("default", self, checkable=True)
            act.setChecked("default" == self._selected_theme)
            act.triggered.connect(self.on_color_theme_changed)
            self.menu_theme.addAction(act_grp.addAction(act))
            # Joke
            act = QAction("random !!!", self, checkable=True)
            act.setChecked("random !!!" == self._selected_theme)
            act.triggered.connect(self.on_color_theme_changed)
            self.menu_theme.addAction(act_grp.addAction(act))
            # Test
            act = QAction(f"Demo", self, checkable=True)
            act.setChecked(f"Demo" == self._selected_theme)
            act.triggered.connect(self.on_color_theme_changed)
            self.menu_theme.addAction(act_grp.addAction(act))

            self.menu_theme.addSeparator()

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
                self.menu_theme.addAction(act_grp.addAction(act))

            self.apply_theme(style=self._selected_style, theme=self._selected_theme)

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
                self.dk_log.setGeometry(frame_rect)
            state = settings_.value("log_state", None)
            if state is not None:
                self.dk_log.restoreState(state)
            self.action_show_log.setChecked(self.dk_log.isVisible())

            spl_state = settings_.value("spl_ver_main", None)
            if spl_state is not None:
                self.spl_ver_main.restoreState(spl_state)
            else:
                w = (available_width - 50) // 7
                self.spl_ver_main.setSizes((w * 3, w * 4))

            spl_state = settings_.value("spl_ver_main_img_data", None)
            if spl_state is not None:
                self.spl_ver_main_img_data.restoreState(spl_state)
            else:
                w = (available_width - 50) // 7
                self.spl_ver_main_img_data.setSizes((w * 5, w * 2))

            spl_state = settings_.value("spl_hor_main_left", None)
            if spl_state is not None:
                self.spl_hor_main_left.restoreState(spl_state)
            else:
                h = (available_height - 50) // 5
                self.spl_hor_main_left.setSizes((h * 1, h * 1, h * 2))

            spl_state = settings_.value("spl_ver_main_tab_source", None)
            if spl_state is not None:
                self.spl_ver_main_tab_source.restoreState(spl_state)
            else:
                w = (available_width - 50) // 7 * 3 // 3
                self.spl_ver_main_tab_source.setSizes((w * 2, w * 1))

            # Data editor splitters
            spl_state = settings_.value("spl_de_left", None)
            if spl_state is not None:
                self.spl_de_left.restoreState(spl_state)
            else:
                w = (available_width - 50) // 5
                self.spl_de_left.setSizes((w, w * 4))

            spl_state = settings_.value("spl_de_right", None)
            if spl_state is not None:
                self.spl_de_right.restoreState(spl_state)
            else:
                w = (available_width - 50) // 5
                self.spl_de_right.setSizes((w * 4, w))

            spl_state = settings_.value("spl_de_hor", None)
            if spl_state is not None:
                self.spl_de_hor.restoreState(spl_state)
            else:
                h = (available_height - 50) // 5
                self.spl_de_hor.setSizes((h * 4, h))

            self.selected_main_tab = settings_.value("global_tab_name", "")
            self.tw_tool_box.setCurrentIndex(int(settings_.value("toolbox_tab_index", 0)))

            for k, v in self.dynamic_folders.items():
                self.dynamic_folders[k] = settings_.value(k, self.dynamic_folders[k])

            # Fill main menu
            self.actionEnable_annotations.setChecked(
                settings_.value("actionEnable_annotations", "false").lower() == "true"
            )
            self.actionEnable_log.setChecked(
                settings_.value("actionEnable_log", "true").lower() == "true"
            )
            self.multithread = settings_.value("multithread", "true").lower() == "true"
            self.action_use_multithreading.setChecked(self.multithread)
            self.use_pipeline_cache = (
                settings_.value("use_pipeline_cache", "true").lower() == "true"
            )
            self.action_use_pipeline_cache.setChecked(self.use_pipeline_cache)

            # Retrieve last active database
            last_db = dbw.DbInfo(
                display_name=settings_.value("current_data_base/display_name", ""),
                db_file_name=settings_.value("current_data_base/db_file_name", ""),
                src_files_path=settings_.value("current_data_base/src_files_path", ""),
                dbms=settings_.value("current_data_base/dbms", ""),
                db_folder_name=settings_.value("current_data_base/db_folder_name", ""),
            )
            if last_db.db_file_name == "":
                last_db = None
            elif (
                last_db.dbms == "sqlite"
                and last_db.db_file_name != ":memory:"
                and not os.path.isfile(os.path.join(last_db.db_full_file_path))
            ):
                last_db = None

            # Load saved databases
            settings_.beginGroup("local_databases")
            for ldb_name in settings_.childGroups():
                db_info = dbw.DbInfo(
                    display_name=settings_.value(f"{ldb_name}/display_name", ""),
                    db_file_name=settings_.value(f"{ldb_name}/db_file_name", ""),
                    src_files_path=settings_.value(f"{ldb_name}/src_files_path", ""),
                    dbms=settings_.value(f"{ldb_name}/dbms", ""),
                    db_folder_name=settings_.value(f"{ldb_name}/db_folder_name", ""),
                )
                # Remove from databases if dead link
                if db_info.dbms == "sqlite" and not os.path.isfile(db_info.db_full_file_path):
                    continue
                self.local_databases.append(db_info)
            settings_.endGroup()

            # Add default postgress databases if missing and enabled
            if len(self.local_databases) == 0 and ui_consts.ENABLE_POSTGRES:
                self.local_databases = [dbw.DB_INFO_LOCAL_SAMPLES, dbw.DB_INFO_EXT_HD]

            if last_db is not None and last_db.db_file_name and last_db.db_file_name != ":memory:":
                for db in self.local_databases:
                    if db.db_file_name == last_db.db_file_name:
                        break
                else:
                    self.local_databases.append(last_db)

            # Load data bases
            self.build_database_menu(
                add_external=dbw.LOAD_DISTANT_DATABASES,
                selected="" if last_db is None else last_db.db_file_name,
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
                ldb = dbw.db_info_to_database(last_db)
                if isinstance(ldb, str):
                    self.log_exception(f"Unable to restore database: {ldb}")
                else:
                    self.current_database = ldb

            # Fill check options
            self.chk_experiment.setChecked(
                settings_.value("checkbox_status/experiment_checkbox_state", "true").lower()
                == "true"
            )
            self.chk_plant.setChecked(
                settings_.value("checkbox_status/plant_checkbox_state", "true").lower() == "true"
            )
            self.chk_date.setChecked(
                settings_.value("checkbox_status/date_checkbox_state", "true").lower() == "true"
            )
            self.chk_camera.setChecked(
                settings_.value("checkbox_status/camera_checkbox_state", "true").lower() == "true"
            )
            self.chk_view_option.setChecked(
                settings_.value("checkbox_status/view_option_checkbox_state", "true").lower()
                == "true"
            )
            self.chk_time.setChecked(
                settings_.value("checkbox_status/time_checkbox_state", "true").lower() == "true"
            )

            # Fill batch options
            self.cb_batch_mode.setCurrentIndex(
                int(settings_.value("batch_configuration/mode", self.cb_batch_mode.currentIndex()))
            )
            self.sb_batch_count.setValue(
                int(settings_.value("batch_configuration/skim_count", self.sb_batch_count.value()))
            )

            # Fill image list
            file_path_ = settings_.value("last_image_browser_state", "")
            if file_path_ and os.path.isfile(file_path_):
                self.init_image_browser(pd.read_csv(file_path_))

            # Fill process modes
            lst = self._ip_tools_holder.ipt_list
            target_process = str(settings_.value("process_Mode", "Default"))
            process_name = ""
            for i, ip_t in enumerate(lst):
                for p in ip_t.gizmos:
                    if p.is_input:
                        p.value = settings_.value(f"tools/{ip_t.name}/{p.name}", p.default_value)
                        p.grid_search_options = settings_.value(
                            f"tools/{ip_t.name}/{p.name}_gso", str(p.default_value)
                        )
                if ip_t.name.lower() == target_process.lower():
                    process_name = ip_t.name

            if not process_name:
                process_name = lst[0].name
            self.select_tool_from_name(process_name)

            # Fill pipeline processor
            self.le_pp_output_folder.setText(
                settings_.value(
                    "pipeline_processor/output_folder", self.le_pp_output_folder.text()
                )
            )
            self.cb_pp_overwrite.setChecked(
                settings_.value("pipeline_processor/overwrite", "true").lower() == "true"
            )
            self.cb_pp_generate_series_id.setChecked(
                settings_.value("pipeline_processor/generate_series_id", "true").lower() == "true"
            )
            self.cb_pp_append_experience_name.setChecked(
                settings_.value("pipeline_processor/append_experience_name", "true").lower()
                == "true"
            )
            self.cb_pp_append_timestamp_to_output_folder.setChecked(
                settings_.value("pipeline_processor/append_timestamp", "true").lower() == "true"
            )
            self.sl_pp_thread_count.setValue(
                int(
                    settings_.value(
                        "pipeline_processor/thread_count", self.sl_pp_thread_count.value()
                    )
                )
            )
            self.pp_thread_pool.setMaxThreadCount(self.sl_pp_thread_count.value())
            self.sp_pp_time_delta.setValue(
                int(
                    settings_.value(
                        "pipeline_processor/sp_pp_time_delta", self.sp_pp_time_delta.value()
                    )
                )
            )

            self.on_bt_clear_pipeline()

            # Fill selected plant
            self.select_image_from_luid(settings_.value("selected_plant_luid", ""))

        except Exception as e:
            self.log_exception(f"Failed to load settings because: {repr(e)}")
            res = False
        else:
            self.update_feedback(
                status_message="Settings loaded, ready to play", use_status_as_log=True
            )
        finally:
            self.unlock_settings()
            self._initializing = False
        return res

    def save_settings(self):
        settings_ = self.lock_settings()
        try:
            settings_.setValue("settings_exists", True)

            settings_.setValue("main_geometry", self.saveGeometry())
            settings_.setValue("main_state", self.saveState())

            settings_.setValue("global_tab_name", self.selected_main_tab)
            settings_.setValue("toolbox_tab_index", self.tw_tool_box.currentIndex())
            settings_.setValue(
                "actionEnable_annotations", self.actionEnable_annotations.isChecked()
            )
            settings_.setValue("actionEnable_log", self.actionEnable_log.isChecked())
            settings_.setValue("dimension", self.geometry())
            settings_.setValue("spl_ver_main_tab_source", self.spl_ver_main_tab_source.saveState())
            settings_.setValue("spl_ver_main", self.spl_ver_main.saveState())
            settings_.setValue("spl_ver_main_img_data", self.spl_ver_main_img_data.saveState())
            settings_.setValue("spl_hor_main_left", self.spl_hor_main_left.saveState())
            settings_.setValue("process_mode", self.current_tool.name)
            settings_.setValue("selected_style", self._selected_style)
            settings_.setValue("selected_theme", self._selected_theme)
            settings_.setValue("multithread", self.action_use_multithreading.isChecked())
            settings_.setValue("use_pipeline_cache", self.action_use_pipeline_cache.isChecked())
            settings_.setValue("log_geometry", self.dk_log.geometry())

            # Data editor
            settings_.setValue("spl_de_left", self.spl_de_left.saveState())
            settings_.setValue("spl_de_right", self.spl_de_right.saveState())
            settings_.setValue("spl_de_hor", self.spl_de_hor.saveState())

            for k, v in self.dynamic_folders.items():
                settings_.setValue(k, v)

            settings_.beginGroup("checkbox_status")
            settings_.setValue("experiment_checkbox_state", self.chk_experiment.isChecked())
            settings_.setValue("plant_checkbox_state", self.chk_plant.isChecked())
            settings_.setValue("date_checkbox_state", self.chk_date.isChecked())
            settings_.setValue("camera_checkbox_state", self.chk_camera.isChecked())
            settings_.setValue("view_option_checkbox_state", self.chk_view_option.isChecked())
            settings_.setValue("time_checkbox_state", self.chk_time.isChecked())
            settings_.endGroup()

            settings_.beginGroup("batch_configuration")
            settings_.setValue("mode", self.cb_batch_mode.currentIndex())
            settings_.setValue("skim_count", self.sb_batch_count.value())
            settings_.endGroup()

            if self._src_image_wrapper is not None:
                settings_.setValue("selected_plant_luid", self._src_image_wrapper.luid)

            if self.current_database is not None:
                settings_.beginGroup("current_data_base")
                settings_.setValue("display_name", self.current_database.display_name)
                settings_.setValue("db_file_name", self.current_database.db_file_name)
                settings_.setValue("src_files_path", self.current_database.src_files_path)
                settings_.setValue("dbms", self.current_database.dbms)
                settings_.setValue("db_folder_name", self.current_database.db_folder_name)
                settings_.endGroup()
            else:
                settings_.remove("current_data_base")

            if len(self.local_databases) > 0:
                for ldb in self.local_databases:
                    settings_.beginGroup(f"local_databases/{ldb.display_name}")
                    settings_.setValue("display_name", ldb.display_name)
                    settings_.setValue("db_file_name", ldb.db_file_name)
                    settings_.setValue("src_files_path", ldb.src_files_path)
                    settings_.setValue("dbms", ldb.dbms)
                    settings_.setValue("db_folder_name", ldb.db_folder_name)
                    settings_.endGroup()
            else:
                settings_.remove("local_databases")

            settings_.beginGroup("recent_folders")
            for i, fld in enumerate(self.recent_folders):
                settings_.setValue(str(i), fld)
            settings_.endGroup()

            settings_.beginGroup("pipeline_processor")
            settings_.setValue("output_folder", self.le_pp_output_folder.text())
            settings_.setValue("overwrite", self.cb_pp_overwrite.isChecked())
            settings_.setValue("generate_series_id", self.cb_pp_generate_series_id.isChecked())
            settings_.setValue(
                "append_experience_name", self.cb_pp_append_experience_name.isChecked()
            )
            settings_.setValue(
                "append_timestamp", self.cb_pp_append_timestamp_to_output_folder.isChecked()
            )
            settings_.setValue("thread_count", self.sl_pp_thread_count.value())
            settings_.setValue("sp_pp_time_delta", self.sp_pp_time_delta.value())
            settings_.endGroup()

            lst = self._ip_tools_holder.ipt_list
            for data_ in lst:
                settings_.beginGroup(f"tools/{data_.name}")
                for param in data_.gizmos:
                    if param.is_input:
                        settings_.setValue(param.name, param.value)
                        settings_.setValue(f"{param.name}_gso", param.grid_search_options)
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

            if save_lst_ is True:
                model.images.to_csv("./saved_data/last_image_browser_state.csv", index=False)
                settings_.setValue(
                    "last_image_browser_state", "./saved_data/last_image_browser_state.csv"
                )
            else:
                settings_.setValue("last_image_browser_state", "")

        except Exception as e:
            self.log_exception(f"Failed to save settings because: {repr(e)}")
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
            self._splash.finish(self)
            self._splash = None
            self._pg_splash = None

    def update_feedback(
        self,
        status_message: str = "",
        log_message: Any = None,
        use_status_as_log: bool = False,
        collect_garbage: bool = True,
    ):
        process = psutil.Process(os.getpid())
        mem_data = f"""[Memory: Used/Free%
        {process.memory_percent():02.2f}/{100 - psutil.virtual_memory().percent:02.2f}%]"""

        self.setWindowTitle(f"{_PRAGMA_NAME} -- {mem_data}")

        prefix_ = f'[{dt.now().strftime("%Y_%B_%d %H-%M-%S")}]-{mem_data}'

        # Update status bar
        if status_message:
            self._status_label.setText(status_message)
        else:
            self._status_label.setText("")

        # Update log
        if self.actionEnable_log.isChecked():
            self.lv_log.moveCursor(QTextCursor.End, 0)
            if log_message is not None:
                if isinstance(log_message, str):
                    log_msg = f"{prefix_} -- {log_message}<br>"
                elif isinstance(log_message, ErrorHolder):
                    log_msg = (
                        f"{prefix_} -- {ui_consts.LOG_ERROR_STR}: {log_message.to_html()}<br>"
                    )
                else:
                    log_msg = f"{prefix_} -- {ui_consts.LOG_UNK_STR}: {str(log_message)}<br>"
            elif use_status_as_log and status_message:
                log_msg = f"{prefix_} -- {ui_consts.LOG_INFO_STR}: {status_message}<br>"
            else:
                log_msg = ""
            if log_msg:
                self.lv_log.insertHtml(log_msg)
                self.lv_log.verticalScrollBar().setValue(self.lv_log.verticalScrollBar().maximum())
                log_title = "IPSO Phen - Log: "
                # Add to proper category
                if ui_consts.LOG_CRITICAL_STR in log_msg:
                    self._log_count_critical += 1
                elif ui_consts.LOG_ERROR_STR in log_msg:
                    self._log_count_error += 1
                elif ui_consts.LOG_EXCEPTION_STR in log_msg:
                    self._log_count_exception += 1
                elif ui_consts.LOG_WARNING_STR in log_msg:
                    self._log_count_warning += 1
                elif ui_consts.LOG_IMPORTANT_STR in log_msg:
                    self._log_count_important += 1
                elif ui_consts.LOG_PIPELINE_PROCESSOR_STR in log_msg:
                    self._log_count_mass_process += 1
                elif ui_consts.LOG_INFO_STR in log_msg:
                    self._log_count_info += 1
                elif ui_consts.LOG_TIMING_STR in log_msg:
                    self._log_count_timming += 1
                else:
                    self._log_count_unknown += 1
                # Update tab title
                if self._log_count_critical > 0:
                    log_title += f" [Critical:{self._log_count_critical}]"
                if self._log_count_error > 0:
                    log_title += f" [Error:{self._log_count_error}]"
                if self._log_count_exception > 0:
                    log_title += f" [Exception:{self._log_count_exception}]"
                if self._log_count_warning > 0:
                    log_title += f" [Warning:{self._log_count_warning}]"
                if self._log_count_important > 0:
                    log_title += f" [Imp:{self._log_count_important}]"
                if self._log_count_mass_process > 0:
                    log_title += f" [MP:{self._log_count_mass_process}]"
                if self._log_count_info > 0:
                    log_title += f" [Info:{self._log_count_info}]"
                if self._log_count_timming > 0:
                    log_title += f" [Timming:{self._log_count_timming}]"
                if self._log_count_unknown > 0:
                    log_title += f" [Other:{self._log_count_unknown}]"
                if len(log_title) < 7:
                    log_title += " No log messages"
                self.dk_log.setWindowTitle(log_title)

        if not self.multithread:
            self.process_events()

        if (
            not self._collecting_garbage
            and (timer() - self._last_garbage_collected > 60)
            and collect_garbage
            and (process.memory_percent() > 30)
        ):
            self._collecting_garbage = True
            try:
                old_mm_percent = process.memory_percent()
                self.update_feedback(status_message="Collecting garbage...", collect_garbage=False)
                gc.collect()
                self.update_feedback(
                    status_message="Garbage collected",
                    log_message=f"""{ui_consts.LOG_IMPORTANT_STR}:
                    Garbage collection freed {old_mm_percent - process.memory_percent():02.2f}% memory""",
                    collect_garbage=False,
                )
            except Exception as e:
                self.log_exception(f"Unable to collect garbage: {repr(e)}")
            finally:
                self._collecting_garbage = False
                self._last_garbage_collected = timer()

    def log_exception(self, err_str: str):
        st_msg, *_ = err_str.split(": ")
        self.update_feedback(
            status_message=st_msg, log_message=f"{ui_consts.LOG_EXCEPTION_STR}: {err_str}"
        )

    def on_action_create_wrapper_before(self):
        self.update_tool_code()

    def on_action_standard_object_oriented_call(self):
        self.action_standard_object_oriented_call.setChecked(True)
        self.action_object_oriented_wrapped_with_a_with_clause.setChecked(False)
        self.action_functional_style.setChecked(False)
        self.update_tool_code()

    def on_action_object_oriented_wrapped_with_a_with_clause(self):
        self.action_standard_object_oriented_call.setChecked(False)
        self.action_object_oriented_wrapped_with_a_with_clause.setChecked(True)
        self.action_functional_style.setChecked(False)
        self.update_tool_code()

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
        open_file((os.getcwd(), "readme.html"))

    def on_action_show_documentation(self):
        open_file((os.getcwd(), "site/index.html"))

    def build_tool_documentation(self, tool, tool_name):
        with open(os.path.join("docs", f"{tool_name}.md"), "w") as f:
            f.write(f"# {tool.name}\n\n")
            f.write("## Description\n\n")
            f.write(tool.description.replace("\n", "  \n") + "\n")
            f.write(f"**Real time**: {str(tool.real_time)}\n\n")
            f.write("## Usage\n\n")
            for use_case in tool.use_case:
                f.write(f"- **{use_case}**: {ipc.tool_group_hints[use_case]}\n")
            f.write("\n## Parameters\n\n")
            if tool.has_input:
                for p in tool.gizmos:
                    if p.is_input:
                        f.write(f"- {p.desc} ({p.name}): {p.hint} (default: {p.default_value})\n")
            f.write("\n")
            f.write("## Example\n\n")
            f.write("### Source\n\n")
            f.write(f"![Source image](images/{self._src_image_wrapper.name}.jpg)\n")
            if not os.path.isfile(
                os.path.join(".", "docs", "images", f"{self._src_image_wrapper.name}.jpg")
            ):
                shutil.copyfile(
                    src=self._src_image_wrapper.file_path,
                    dst=os.path.join(".", "docs", "images", f"{self._src_image_wrapper.name}.jpg"),
                )
            f.write("\n")
            f.write("### Parameters/Code\n\n")
            f.write("Default values are not needed when calling function\n\n")
            f.write("```python\n")
            f.write(
                call_ipt_code(
                    ipt=self.current_tool, file_name=f"{self._src_image_wrapper.name}.jpg"
                )
            )
            f.write("```\n\n")
            if hasattr(tool, "data_dict"):
                f.write("### Result image\n\n")
            else:
                f.write("### Result\n\n")
            self.save_image(
                image_data=self.cb_available_outputs.itemData(
                    self.cb_available_outputs.currentIndex()
                ),
                text=tool_name,
                image_path="./docs/images/",
            )
            f.write(f"![Result image](images/{tool_name}.jpg)\n")
            if hasattr(tool, "data_dict"):
                f.write("\n### Result data\n\n")
                f.write("|         key         |        Value        |\n")
                f.write("|:-------------------:|:-------------------:|\n")
                for r in range(self.tw_script_sim_output.rowCount()):
                    f.write(
                        f"|{self.tw_script_sim_output.item(r, 0).text()}|{self.tw_script_sim_output.item(r, 1).text()}|\n"
                    )

    def on_action_build_tool_documentation(self):
        self.build_tool_documentation(
            tool=self.current_tool, tool_name=f'ipt_{self.current_tool.name.replace(" ", "_")}'
        )

    def on_action_build_test_files(self):
        tmp_ip_holder = IptHolder()
        self.update_feedback(
            status_message="Building test scripts",
            log_message=f"""{ui_consts.LOG_IMPORTANT_STR}:
            Building test scripts""",
        )
        tmp_ip_holder.build_test_files(log_callback=self.update_feedback)
        self.update_feedback(
            status_message="Test scripts built",
            log_message=f"{ui_consts.LOG_IMPORTANT_STR}: Test scripts built",
        )

    def on_action_show_log(self):
        self.dk_log.setVisible(not self.dk_log.isVisible())
        self.action_show_log.setChecked(self.dk_log.isVisible())

    def on_action_build_ipso_phen_documentation(self):
        # Build tools overview
        with open(os.path.join("docs", "tools.md"), "w", encoding="utf8") as f:
            f.write("# Tools overview by category\n")
            f.write("!!! info\n")
            f.write("    Some tools may be in more than one category\n")
            lst = self._ip_tools_holder.ipt_list
            for use_case in self._ip_tools_holder.use_cases:
                if use_case == "none":
                    continue
                f.write(f"## {use_case}\n\n")
                f.write(ipc.tool_group_hints[use_case] + "\n\n")
                op_lst = self._ip_tools_holder.list_by_use_case(use_case)
                for ipt_ in op_lst:
                    tool_name = f'ipt_{ipt_.name.replace(" ", "_")}'
                    if os.path.isfile(os.path.join("docs", f"{tool_name}.md")):
                        f.write(f"### {ipt_.name}\n")
                        f.write(ipt_.description.replace("\n", "<br>") + "<br>\n")
                        f.write(f"Details [here]({tool_name}.md)\n\n")

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
            f.write("- Samples: samples.md\n")
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
            f.write("- Using the grid search: grid_search.md\n")
            f.write("- Tutorial - Pipelines: pipelines.md\n")
            f.write("- Pipeline processor: pipeline_processor.md\n")
            f.write("- Advanced features:\n")
            f.write("  - Creating custom tools: custom_tools.md\n")
            f.write("  - Script pipelines: script_pipelines.md\n")
            f.write("  - Class pipelines: class_pipelines.md\n")
            f.write("  - File handlers: file_handlers.md")

    def accept(self):
        pass

    def reject(self):
        pass

    def on_action_functional_style(self):
        self.action_standard_object_oriented_call.setChecked(False)
        self.action_object_oriented_wrapped_with_a_with_clause.setChecked(False)
        self.action_functional_style.setChecked(True)
        self.update_tool_code()

    def update_tool_code(self):
        self.txtb_code.clear()
        try:
            if self.action_standard_object_oriented_call.isChecked():
                self.txtb_code.insertPlainText(
                    self.current_tool.code(
                        print_result=False,
                        use_with_clause=False,
                        build_wrapper=self.action_create_wrapper_before.isChecked(),
                    )
                )
            elif self.action_object_oriented_wrapped_with_a_with_clause.isChecked():
                self.txtb_code.insertPlainText(
                    self.current_tool.code(
                        print_result=False,
                        use_with_clause=True,
                        build_wrapper=self.action_create_wrapper_before.isChecked(),
                    )
                )
            elif self.action_functional_style.isChecked():
                self.txtb_code.insertPlainText(
                    call_ipt_code(
                        ipt=self.current_tool,
                        file_name=self.current_tool.file_name
                        if self.action_create_wrapper_before.isChecked()
                        else "",
                    )
                )
        except Exception as e:
            self.log_exception(f"Unable to output code: {repr(e)}")

    def on_tv_pp_view_selection_changed(self, selected, deselected):
        model: PipelineModel = self.tv_pp_view.model()
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
                        self.bt_pp_delete.setEnabled(True)
                        self.bt_pp_up.setEnabled(index.row() > 0)
                        self.bt_pp_down.setEnabled(index.row() < len(parent.children) - 1)
                        return

        self.bt_pp_up.setEnabled(False)
        self.bt_pp_down.setEnabled(False)
        self.bt_pp_delete.setEnabled(False)

    def pp_callback(self, result, msg, data, current_step, total_steps):
        if result == "OK":
            if msg and data is not None:
                self.update_feedback(status_message=msg, log_message=msg)
            if isinstance(data, (GroupNode, ModuleNode)):
                self.cb_available_outputs.addItem(
                    data.name,
                    {
                        "plant_name": self._src_image_wrapper.plant,
                        "name": data.name,
                        "image": data.get_relevant_image(),
                        "data": data.last_result.get("data", {}),
                    },
                )
                self.cb_available_outputs.setCurrentIndex(self.cb_available_outputs.count() - 1)
            elif isinstance(data, AbstractImageProcessor):
                self.add_images_to_viewer(
                    wrapper=data, data_dict=data.csv_data_holder.data_list, avoid_duplicates=False
                )
            elif isinstance(data, dict):
                self.cb_available_outputs.addItem(data["name"], data)
                self.cb_available_outputs.setCurrentIndex(self.cb_available_outputs.count() - 1)
        elif result == "ERROR":
            self.update_feedback(
                status_message=msg, log_message=f"{ui_consts.LOG_ERROR_STR}: {msg}"
            )
        elif result == "WARNING":
            self.update_feedback(
                status_message=msg, log_message=f"{ui_consts.LOG_WARNING_STR}: {msg}"
            )
        else:
            self.log_exception(f'Unknown result: "Unknown pipeline result {result}"')

        if current_step >= 0 and total_steps >= 0:
            self.pb_pp_progress.setValue(
                round((min(current_step, total_steps)) / total_steps * 100)
            )
        if not self.multithread:
            self.process_events()

    def on_bt_pp_new(self):
        pp = LoosePipeline(name="None", description="Double click to edit description")
        self.pipeline = pp

    def on_bt_pp_load(self):
        file_name_ = QFileDialog.getOpenFileName(
            parent=self,
            caption="Load pipeline",
            directory=self.dynamic_folders["pipeline"],
            filter=_PIPELINE_FILE_FILTER,
        )[0]
        if file_name_:
            self.dynamic_folders["pipeline"] = os.path.join(os.path.dirname(file_name_), "")
            try:
                self.pipeline = LoosePipeline.load(file_name=file_name_)
            except Exception as e:
                self.log_exception(f'Unable to load pipeline: "{repr(e)}"')

    def on_bt_pp_save(self):
        file_name_ = QFileDialog.getSaveFileName(
            parent=self,
            caption="Save pipeline",
            directory=self.dynamic_folders["pipeline"],
            filter=_PIPELINE_FILE_FILTER,
        )[0]
        if file_name_:
            self.dynamic_folders["pipeline"] = os.path.join(os.path.dirname(file_name_), "")
            if not file_name_.lower().endswith(".tipp") and not file_name_.lower().endswith(
                ".json"
            ):
                file_name_ += ".tipp"
            res = self.pipeline.save(file_name_)
            if res:
                self.update_feedback(
                    status_message=f'Saved pipeline to: "{file_name_}"', use_status_as_log=True
                )
            else:
                self.update_feedback(
                    status_message="Failed to save pipline, cf. log for more details",
                    log_message=pp_last_error.to_html(),
                )

    def on_bt_pp_up(self):
        model: PipelineModel = self.tv_pp_view.model()
        if model is not None:
            model.move_up(selected_items=self.tv_pp_view.selectedIndexes())

    def on_bt_pp_down(self):
        model: PipelineModel = self.tv_pp_view.model()
        if model is not None:
            model.move_down(selected_items=self.tv_pp_view.selectedIndexes())

    def on_bt_pp_delete(self):
        model: PipelineModel = self.tv_pp_view.model()
        if model is not None and self.tv_pp_view.selectedIndexes():
            selected_node = self.tv_pp_view.selectedIndexes()[0]
            model.removeRow(selected_node.row(), selected_node.parent())

    def on_bt_pp_add_tool(self, q):
        # Get model
        model: PipelineModel = self.tv_pp_view.model()
        if model is None:
            self.pipeline = LoosePipeline(
                name="None", description="Double click to edit description",
            )
            model: PipelineModel = self.tv_pp_view.model()
        # Get menu item text
        if hasattr(self.sender(), "text"):
            text = self.sender().text()
        else:
            text = q.text()
        # Get parent node
        indexes = self.tv_pp_view.selectedIndexes()
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
        self.tv_pp_view.selectionModel().selection().select(index, index)
        self.tv_pp_view.expand(index)

        if text == "Default empty group":
            added_index = model.add_group(selected_items=index)
            self.tv_pp_view.expand(added_index.parent())
        elif text == "Fix exposure":
            added_index = model.add_group(
                selected_items=index, merge_mode=ipc.MERGE_MODE_CHAIN, name=text,
            )
            model.add_module(
                selected_items=added_index,
                module=self.find_tool_by_name("Simple white balance"),
                enabled=True,
            )
            model.add_module(
                selected_items=added_index,
                module=self.find_tool_by_name("Image transformations"),
                enabled=True,
            )
            self.tv_pp_view.expand(added_index)
        elif text == "Pre process image":
            added_index = model.add_group(
                selected_items=index, merge_mode=ipc.MERGE_MODE_CHAIN, name=text,
            )
            model.add_module(
                selected_items=added_index,
                module=self.find_tool_by_name("Check exposure"),
                enabled=True,
            )
            model.add_module(
                selected_items=added_index,
                module=self.find_tool_by_name("Partial posterizer"),
                enabled=True,
            )
            self.tv_pp_view.expand(added_index)
        elif text == "Threshold":
            added_index = model.add_group(
                selected_items=index, merge_mode=ipc.MERGE_MODE_AND, name=text,
            )
            model.add_module(
                selected_items=added_index,
                module=self.find_tool_by_name("Multi range threshold"),
                enabled=True,
            )
            self.tv_pp_view.expand(added_index)
        elif text == "Mask cleanup":
            added_index = model.add_group(
                selected_items=index, merge_mode=ipc.MERGE_MODE_CHAIN, name=text,
            )
            model.add_module(
                selected_items=added_index,
                module=self.find_tool_by_name("Keep linked Contours"),
                enabled=True,
            )
            self.tv_pp_view.expand(added_index)
        elif text == "Feature extraction":
            added_index = model.add_group(
                selected_items=index, merge_mode=ipc.MERGE_MODE_NONE, name=text,
            )
            model.add_module(
                selected_items=added_index,
                module=self.find_tool_by_name("Observation data"),
                enabled=True,
            )
            model.add_module(
                selected_items=added_index,
                module=self.find_tool_by_name("Analyze object"),
                enabled=True,
            )
            model.add_module(
                selected_items=added_index,
                module=self.find_tool_by_name("Analyze color"),
                enabled=True,
            )
            model.add_module(
                selected_items=added_index,
                module=self.find_tool_by_name("Analyze bound"),
                enabled=True,
            )
            model.add_module(
                selected_items=added_index,
                module=self.find_tool_by_name("Analyze chlorophyll"),
                enabled=True,
            )
            self.tv_pp_view.expand(added_index)
        else:
            tool = self.find_tool_by_name(text)
            if tool is None:
                self.update_feedback(
                    status_message=f'Unable to add "{text}" to pipeline', use_status_as_log=True
                )
                return
            else:
                added_index = model.add_module(selected_items=index, module=tool, enabled=True,)
            self.tv_pp_view.expand(added_index.parent())

    def on_bt_pp_run(self):
        self.run_process(wrapper=self._src_image_wrapper)

    def on_bt_pp_invalidate(self):
        pp = self.pipeline
        if pp is not None:
            self.pipeline.invalidate()
            self.update_feedback(status_message="Cleared pipeline cache", use_status_as_log=True)

    @pyqtSlot()
    def on_bt_pp_reset(self):
        self.le_pp_output_folder.setText(self.dynamic_folders["pp_output"])
        self.on_rb_pp_default_process()
        self.le_pp_selected_pipeline.setText("")
        self.lbl_pipeline_name.setText("")
        self.cb_pp_overwrite.setChecked(False)
        self.cb_pp_generate_series_id.setChecked(False)
        self.cb_pp_append_experience_name.setChecked(True)
        self.cb_pp_append_timestamp_to_output_folder.setChecked(False)
        self.sl_pp_thread_count.setValue(0)
        if self._src_image_wrapper is not None:
            self.edt_csv_file_name.setText(f"{self._src_image_wrapper.experiment}_raw_data")
        else:
            self.edt_csv_file_name.setText("unknown_experiment_raw_data")
        self.sp_pp_time_delta.setValue(20)
        self._custom_csv_name = False

    def _update_pp_pipeline_state(self, default_process: bool, active: bool, load_script: bool):
        self.rb_pp_default_process.setChecked(default_process)
        self.rb_pp_active_script.setChecked(active)
        self.rb_pp_load_script.setChecked(load_script)

    def on_rb_pp_default_process(self):
        self._update_pp_pipeline_state(True, False, False)

    def on_rb_pp_active_script(self):
        if self.script_generator.is_functional:
            self._update_pp_pipeline_state(False, True, False)
        else:
            self._update_pp_pipeline_state(True, False, False)
            self.update_feedback(
                status_message="No active pipeline found, reverting to default process",
                use_status_as_log=True,
            )

    def on_rb_pp_load_script(self):
        if self.le_pp_selected_pipeline.text() in ["", _ACTIVE_SCRIPT_TAG]:
            self.on_bt_load_pipeline()
        else:
            self._update_pp_pipeline_state(False, False, True)

    @pyqtSlot()
    def on_bt_pp_select_output_folder(self):
        if not os.path.isdir(self.le_pp_output_folder.text()):
            force_directories(self.le_pp_output_folder.text())

        sel_folder = str(
            QFileDialog.getExistingDirectory(
                parent=self,
                caption="Select output folder",
                directory=self.le_pp_output_folder.text(),
            )
        )
        if os.path.isdir(sel_folder):
            self.le_pp_output_folder.setText(sel_folder)

    def do_pp_progress(self, step: int, total: int):
        if threading.current_thread() is not threading.main_thread():
            print("do_pp_progress: NOT MAIN THREAD")
        self.global_progress_update(step=step, total=total, process_events=not self.multithread)

    def do_pp_check_abort(self):
        # if threading.current_thread() is not threading.main_thread():
        #     print('do_pp_check_abort: NOT MAIN THREAD')
        return self._batch_stop_current

    def do_fp_start(self):
        self.update_feedback(
            status_message="Building CSV files", log_message=" --- Building CSV files ---"
        )

    def do_fp_progress(self, step: int, total: int):
        self.global_progress_update(step, total)

    def do_fp_end(self):
        self.pp_pipeline = None
        self.set_global_enabled_state(new_state=True)
        self.global_progress_stop()
        self.update_feedback(
            status_message="Pipeline mass processing ended",
            log_message=f"""{ui_consts.LOG_IMPORTANT_STR} {ui_consts.LOG_PIPELINE_PROCESSOR_STR}:
            Pipeline mass processing ended""",
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
            root_csv_name=self.edt_csv_file_name.text(),
            # Create pipeline
            pipeline=self.pp_pipeline,
        )
        if self.multithread:
            self.thread_pool.start(rpp)
        else:
            rpp.run()

    def do_pp_item_ended(self):
        if threading.current_thread() is not threading.main_thread():
            print("do_pp_item_ended: NOT MAIN THREAD")
        if self._batch_stop_current:
            self.update_feedback(
                status_message="Stopping mass pipeline, please wait...",
                log_message=f"""{ui_consts.LOG_IMPORTANT_STR} {ui_consts.LOG_PIPELINE_PROCESSOR_STR}:
                Stopping mass pipeline (user request), please wait...""",
            )
            self.pp_thread_pool.clear()
            self.pp_thread_pool.waitForDone(-1)
            self.set_global_enabled_state(new_state=True)
            self.global_progress_stop()
            self.update_feedback(
                status_message="Mass pipeline stopped",
                log_message=f"""{ui_consts.LOG_IMPORTANT_STR} {ui_consts.LOG_PIPELINE_PROCESSOR_STR}:
                Mass pipeline stopped""",
            )
        else:
            self.pp_threads_step += 1
            self.global_progress_update(
                self.pp_threads_step, self.pp_threads_total, process_events=not self.multithread
            )
            if self.pp_threads_step >= self.pp_threads_total:
                if self.pp_pipeline is not None:
                    self.finalize_pipeline()
                else:
                    self.update_feedback(
                        status_message="Failed to finalize mass processing",
                        log_message=f"""{ui_consts.LOG_CRITICAL_STR} {ui_consts.LOG_UNK_STR}
                        {ui_consts.LOG_PIPELINE_PROCESSOR_STR}: Failed to finalize mass processing""",
                    )
                    self.set_global_enabled_state(new_state=True)
                    self.global_progress_stop()
                    self.update_feedback(
                        status_message="Pipeline mass processing ended",
                        log_message=f"""{ui_consts.LOG_IMPORTANT_STR} {ui_consts.LOG_PIPELINE_PROCESSOR_STR}:
                        Pipeline mass processing ended""",
                    )

    def do_pp_log_item_event(
        self, item_luid: str, event_kind: str, log_data: str, auto_scroll: bool = True
    ):
        if log_data:
            self.update_feedback(log_message=log_data)
        items = self.lw_images_queue.findItems(item_luid, Qt.MatchExactly)
        for item in items:
            item.setToolTip(item.toolTip() + "\n\n" + str(log_data))
            if event_kind == "success":
                item.setIcon(QIcon(":/annotation_level/resources/OK.png"))
            elif event_kind == "warning":
                item.setIcon(QIcon(":/annotation_level/resources/Warning.png"))
            elif event_kind == "exception":
                item.setIcon(QIcon(":/annotation_level/resources/Problem.png"))
            elif event_kind == "failure":
                item.setIcon(QIcon(":/annotation_level/resources/Danger.png"))
            elif event_kind == "refresh":
                item.setIcon(QIcon(":/common/resources/Refresh.png"))
            else:
                item.setIcon(QIcon(":/annotation_level/resources/Help.png"))
            if auto_scroll and self.cb_queue_auto_scroll.isChecked():
                self.lw_images_queue.scrollToItem(item, self.lw_images_queue.EnsureVisible)
        if not self.multithread:
            self.process_events()

    def do_pp_item_image_ready(self, image):
        if self.chk_pp_show_last_item.isChecked():
            self.gv_last_processed_item.main_image = image
            if not self.multithread:
                self.process_events()

    def do_pp_launching(self, total_count: int):
        if threading.current_thread() is not threading.main_thread():
            print("do_pp_launching: NOT MAIN THREAD")
        if total_count > 0:
            self.pp_threads_total = total_count
            self.pp_threads_step = 0
            self.update_feedback(
                status_message="Launching threads",
                log_message=f"{ui_consts.LOG_PIPELINE_PROCESSOR_STR}   --- Launching threads ---",
            )
        else:
            self.finalize_pipeline()

    def on_pp_starting(self):
        if threading.current_thread() is not threading.main_thread():
            print(": NOT MAIN THREAD")
        self.update_feedback(
            status_message="Starting mass processor",
            log_message=f"{ui_consts.LOG_PIPELINE_PROCESSOR_STR}   --- Starting mass processor ---",
        )
        self.set_global_enabled_state(new_state=False)
        self.global_progress_start(add_stop_button=True)

    def do_pp_started(self, launch_state):
        if threading.current_thread() is not threading.main_thread():
            print("do_pp_started: NOT MAIN THREAD")
        if launch_state == "ok":
            self.update_feedback(
                status_message="",
                log_message=f"""{ui_consts.LOG_PIPELINE_PROCESSOR_STR}   ---
                 All threads launched, terminating launcher thread ---<br>""",
            )
            self.update_feedback(
                status_message="Processing images",
                log_message=f"{ui_consts.LOG_PIPELINE_PROCESSOR_STR}   --- Processing images ---<br>",
            )
        elif launch_state == "abort":
            self.update_feedback(
                status_message="User stopped mass pipeline processing",
                log_message=f"{ui_consts.LOG_PIPELINE_PROCESSOR_STR} User stopped mass pipeline processing",
            )
            self.global_progress_stop()
            self.set_global_enabled_state(new_state=True)
        elif launch_state == "exception":
            self.update_feedback(
                status_message="Exception while launching mass processing",
                log_message=f"""{ui_consts.LOG_EXCEPTION_STR} {ui_consts.LOG_PIPELINE_PROCESSOR_STR}
                 Exception while launching mass processing""",
            )
            self.global_progress_stop()
            self.set_global_enabled_state(new_state=True)

    @pyqtSlot()
    def on_bt_pp_start(self):
        self._batch_stop_current = False
        model = self.get_image_model()
        if (model is None) or (model.rowCount() == 0):
            self.update_feedback(
                status_message="Pipeline start: nothing to process",
                log_message=f"{ui_consts.LOG_WARNING_STR}: Pipeline start - nothing to process",
            )
            return
        self.update_feedback(
            status_message="Starting pipeline mass processing",
            log_message=f"""{ui_consts.LOG_IMPORTANT_STR} {ui_consts.LOG_PIPELINE_PROCESSOR_STR}:
             Starting pipeline mass processing""",
        )
        try:
            self.thread_pool.clear()
            self.thread_pool.waitForDone(-1)

            if self.cb_pp_append_experience_name.isChecked():
                output_folder_ = os.path.join(
                    self.le_pp_output_folder.text(),
                    model.get_cell_data(row_number=0, column_name="Experiment"),
                    "",
                )
            else:
                output_folder_ = os.path.join(self.le_pp_output_folder.text(), "")

            # Collect images
            model.images.sort_values(by=["date_time"], axis=0, inplace=True, na_position="first")
            image_list_ = list(model.images["FilePath"])

            if self.rb_pp_default_process.isChecked():
                script_ = None
            elif self.rb_pp_active_script.isChecked():
                script_ = self.script_generator.copy()
            elif self.rb_pp_load_script.isChecked():
                script_ = self.script_generator.copy()
            else:
                self.update_feedback(
                    status_message="Unknown pipeline mode", use_status_as_log=True
                )
                return

            # self.pp_thread_pool.setMaxThreadCount(self.sl_pp_thread_count.value())

            self.pp_pipeline = PipelineProcessor(
                dst_path=output_folder_,
                overwrite=self.cb_pp_overwrite.isChecked(),
                seed_output=self.cb_pp_append_timestamp_to_output_folder.isChecked(),
                group_by_series=self.cb_pp_generate_series_id.isChecked(),
                store_images=True,
            )
            self.pp_pipeline.accepted_files = image_list_
            self.pp_pipeline.script = script_
            if script_ is not None:
                self.pp_pipeline.options.store_images = False
                self.pp_pipeline.script.image_output_path = os.path.join(
                    self.le_pp_output_folder.text(), ""
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
                group_time_delta=self.sp_pp_time_delta.value(),
                items_thread_pool=self.pp_thread_pool,
            )
            if self.multithread:
                self.thread_pool.start(rpp)
            else:
                rpp.run()
        except Exception as e:
            self.log_exception(f'Unable to process pipeline: "{repr(e)}"')

    def on_sl_pp_thread_count_index_changed(self, value):
        self.pp_thread_pool.setMaxThreadCount(value)
        self.lb_pp_thread_count.setText(f"{value}/{self.sl_pp_thread_count.maximum()}")

    @pyqtSlot()
    def on_bt_launch_batch(self):
        self.run_process(wrapper=None)

    @pyqtSlot()
    def on_bt_update_selection_stats(self):
        model = self.get_image_model()
        no_good = model is None
        if no_good is False:
            delegate = self.tv_image_browser.itemDelegate()
            sel_ct = model.rowCount()
        else:
            sel_ct = 0
        if no_good:
            self.lv_stats.insertPlainText("No images selectted\n")
            self.lv_stats.insertPlainText("Please add images to selection to get statistics\n")
            self.lv_stats.insertPlainText("\n")
            self.lv_stats.insertPlainText("________________________________________________\n")

        include_annotations = self.cb_stat_include_annotations.isChecked()
        self.update_feedback(status_message="Building selection stats", use_status_as_log=True)
        self.global_progress_start(add_stop_button=True)
        try:
            self.lv_stats.insertPlainText("\n")
            self.lv_stats.insertPlainText("________________________________________________\n")
            self.lv_stats.insertPlainText(f"Selected items count: {sel_ct}\n")
            self.lv_stats.insertPlainText("\n")
            if include_annotations is True:
                gbl_cpt = 0
                ann_counter = defaultdict(int)
                for i in range(0, model.rowCount()):
                    ann_ = delegate.get_annotation(row_number=i)
                    if ann_ is not None:
                        gbl_cpt += 1
                        ann_counter[ann_["kind"].lower()] += 1
                self.lv_stats.insertPlainText(
                    f"Annotations: {gbl_cpt}, " f"{gbl_cpt / sel_ct * 100:.2f}%\n"
                )
                for k, v in ann_counter.items():
                    self.lv_stats.insertPlainText(
                        f"  {k.ljust(13)}: {v}, {v / sel_ct * 100:.2f}%\n"
                    )
                self.lv_stats.insertPlainText("________________________________________________\n")
                self.lv_stats.insertPlainText("\n")

            df: pd.DataFrame = model.images
            for key in ["experiment", "plant", "date", "camera", "view_option"]:
                self.lv_stats.insertPlainText(f"{key}:\n")
                self.lv_stats.insertPlainText("\n".join(df[key].unique()))
                self.lv_stats.insertPlainText(df.group(key).agg({key: "count"}))
                self.lv_stats.insertPlainText("________________________________________________\n")
        except Exception as e:
            self.log_exception(f"Failed to update statistics: {repr(e)}")
        finally:
            self.global_progress_stop()

    @pyqtSlot()
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

    @pyqtSlot()
    def on_bt_reset_op(self):
        if self._initializing:
            return
        self._updating_process_modes = True
        selected_mode = self.current_tool
        try:
            selected_mode.reset()
            self.update_tool_code()
        except Exception as e:
            self.log_exception(f"Failed to reset tool: {repr(e)}")
        finally:
            self._updating_process_modes = False
        if not self._initializing and selected_mode.real_time:
            self.run_process(wrapper=self._src_image_wrapper, ipt=selected_mode)

    @pyqtSlot()
    def on_bt_reset_grid_search(self):
        if self._initializing:
            return
        self._updating_process_modes = True
        selected_mode = self.current_tool
        try:
            selected_mode.reset_grid_search()
        except Exception as e:
            self.log_exception(f"Failed to reset tool grid search: {repr(e)}")
        finally:
            self._updating_process_modes = False

    @pyqtSlot()
    def on_bt_update_grid_search(self):
        if self._initializing:
            return
        self._updating_process_modes = True
        selected_mode = self.current_tool
        try:
            selected_mode.update_grid_search()
        except Exception as e:
            self.log_exception(f"Failed to reset tool grid search: {repr(e)}")
        finally:
            self._updating_process_modes = False

    def add_images_to_viewer(
        self, wrapper, avoid_duplicates: bool = False, data_dict: dict = None
    ):
        if wrapper is None:
            return
        self._updating_available_images = len(wrapper.image_list) != 1
        try:
            for dic in wrapper.image_list:
                if avoid_duplicates and self.cb_available_outputs.findText(dic["name"]) >= 0:
                    continue
                if data_dict is not None:
                    dic["data"] = dict(**{"image_name": dic["name"]}, **data_dict)
                dic["plant_name"] = wrapper.plant
                self.cb_available_outputs.addItem(dic["name"], dic)
        except Exception as e:
            self.log_exception(f"Unable to update available images because: {repr(e)}")
        finally:
            self._updating_available_images = False

        if self.cb_available_outputs.count() > 1:
            self.cb_available_outputs.setCurrentIndex(self.cb_available_outputs.count() - 1)

    def update_output_tab(self, data_dict):
        while self.tw_script_sim_output.rowCount() > 0:
            self.tw_script_sim_output.removeRow(0)
        for k, v in data_dict.items():
            insert_pos = self.tw_script_sim_output.rowCount()
            self.tw_script_sim_output.insertRow(insert_pos)
            twi = QTableWidgetItem(f"{k}")
            twi.setToolTip(f"{k}")
            self.tw_script_sim_output.setItem(insert_pos, 0, twi)
            twi = QTableWidgetItem(f"{v}")
            twi.setToolTip(f"{v}")
            self.tw_script_sim_output.setItem(insert_pos, 1, twi)

    def do_thread_started(self, mode: str, is_batch_process: bool):
        if mode == "param":
            pass
        elif mode == "ipt":
            pass
        elif mode == "script":
            if not is_batch_process:
                self.on_bt_clear_result()
            self.update_feedback(status_message="Executing current script, please wait...")
        elif mode == "module":
            pass
        elif mode == "pipeline":
            if not is_batch_process:
                self.on_bt_clear_result()
            self.update_feedback(status_message="Executing current pipeline, please wait...")
        else:
            self.update_feedback(
                status_message=f"Unknown runnable mode {mode}",
                log_message=f"{ui_consts.LOG_ERROR_STR}: Unknown runnable mode {mode}",
            )

    def do_thread_ending(self, success: bool, status_msg: str, log_msg: str, sender: object):
        if self.threads_total > 1 and self.threads_step < self.threads_total and status_msg:
            status_msg += f" ({self.threads_step + 1}/{self.threads_total})"
        if len(sender.error_list) > 0:
            self.update_feedback(
                status_message=status_msg, log_message=sender, use_status_as_log=False
            )
        else:
            self.update_feedback(status_message=status_msg, log_message=log_msg)

    def do_thread_ended(self):
        self.update_thread_counts(
            thread_step=self.threads_step + 1,
            thread_total=self.threads_total,
            thread_waiting=self.threads_waiting - 1,
        )

    def on_thread_script_progress(self, step, total, msg, wrapper):
        self.pb_script_gen_progress.setFormat(f"{msg} {step}/{total}")
        self.pb_script_gen_progress.setValue(round((min(step + 1, total)) / total * 100))
        self.add_images_to_viewer(wrapper=wrapper, avoid_duplicates=True)
        if not self.multithread:
            self.process_events()

    def do_thread_update_images(self, batch_process: bool, sender: object):
        if isinstance(sender, AbstractImageProcessor):
            wrapper = sender
        elif isinstance(sender, IptParamHolder):
            wrapper = sender.wrapper
            if wrapper is None:
                self.log_exception(
                    "Unable to update available images because: there's no wrapper inside the tool"
                )
                return
        else:
            self.log_exception("Unable to update available images because: unknown argument")
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
                    self.cb_available_outputs.addItem(wrapper.short_name, dic)
            except Exception as e:
                self.log_exception(f"Unable to update available images because: {repr(e)}")
            self.cb_available_outputs.setCurrentIndex(self.cb_available_outputs.count() - 1)
        else:
            self.add_images_to_viewer(wrapper=wrapper, avoid_duplicates=False, data_dict=info_dict)

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

    def update_thread_counts(self, thread_step: int, thread_total: int, thread_waiting: int):
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
        script: IptStrictPipeline,
        pipeline: LoosePipeline,
        exec_param: int,
        target_module: str,
    ):
        if self.act_settings_sir_keep.isChecked():
            scale_factor = 1
        elif self.act_settings_sir_2x.isChecked():
            scale_factor = 1 / 2
        elif self.act_settings_sir_3x.isChecked():
            scale_factor = 1 / 3
        elif self.act_settings_sir_4x.isChecked():
            scale_factor = 1 / 4
        elif self.act_settings_sir_5x.isChecked():
            scale_factor = 1 / 5
        elif self.act_settings_sir_6x.isChecked():
            scale_factor = 1 / 6
        else:
            scale_factor = 1

        runner_ = IpsoRunnable(
            on_started=self.do_thread_started,
            on_ending=self.do_thread_ending,
            on_ended=self.do_thread_ended,
            on_script_progress=self.on_thread_script_progress,
            on_update_images=self.do_thread_update_images,
            on_update_data=self.do_thread_update_data,
            on_feedback_log_object=self.do_thread_feedback_log_object,
            on_feedback_log_str=self.do_thread_feedback_log_str,
            on_pipeline_progress=self.pp_callback,
            file_data=image_data,
            database=self.current_database.copy(),
            batch_process=is_batch_process,
            ipt=ipt,
            script=script,
            pipeline=pipeline,
            exec_param=exec_param,
            scale_factor=scale_factor,
            target_module=target_module,
        )
        self.threads_waiting += 1
        if self.multithread:
            self.thread_pool.start(runner_)
        else:
            runner_.run()

    def run_process(
        self,
        wrapper: AbstractImageProcessor = None,
        ipt=None,
        exec_param=None,
        target_module: str = "",
    ):
        if wrapper is None:
            # Collect images
            df = self.get_image_dataframe()
            if df is None:
                image_list_ = None
            else:
                skim_mode_ = self.cb_batch_mode.currentText().lower()
                dff = df[["Luid", "FilePath", "date_time"]]
                if skim_mode_ == "all":
                    pass
                elif skim_mode_ == "first n":
                    dff = dff.iloc[0 : min(df.shape[0], self.sb_batch_count.value())]
                elif skim_mode_ == "random n":
                    dff = dff.sample(n=min(df.shape[0], self.sb_batch_count.value()))
                else:
                    self.update_feedback(
                        status_message="Run process: unknown filter mode", use_status_as_log=True
                    )
                    return False
                dff = dff.sort_values(by=["date_time"], axis=0, na_position="first")
                image_list_ = [
                    {"luid": k, "path": v}
                    for k, v in zip(list(dff["Luid"]), list(dff["FilePath"]))
                ]

                # Update "Last batch" data
                self.lw_last_batch.clear()
                for img in reversed(image_list_):
                    new_item = QListWidgetItem()
                    new_item.setText(img["luid"])
                    self.lw_last_batch.insertItem(0, new_item)
        else:
            image_list_ = [dict(path=wrapper.file_path, luid=wrapper.luid)]

        if not image_list_:
            self.update_feedback(
                status_message="Nothing to process", log_message="Nothing to process"
            )
            return

        pipeline_ = None
        script_ = None
        ipt_ = None
        if self.selected_run_tab == _TAB_TOOLS:
            if ipt is None:
                ipt_ = self._current_tool.copy()
            if self.chk_use_pipeline_as_preprocessor.isChecked():
                script_ = self.script_generator
        elif self.selected_run_tab == _TAB_PIPELINE:
            if ipt is None:
                script_ = self.script_generator
            ipt_ = ipt
        elif self.selected_run_tab == _TAB_PIPELINE_V2:
            pipeline_ = self.pipeline
            ipt_ = ipt
        else:
            self.log_exception(err_str=f"Unknown active tab {self.selected_run_tab}")
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

            if script_ is not None:
                update_msg = ""
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
                    script=script_,
                    pipeline=pipeline_,
                    exec_param=exec_param,
                    target_module=target_module,
                )

        except Exception as e:
            self.log_exception(f'Failed to initiate thread: "{repr(e)}"')

    def on_itemSelectionChanged(self):
        for item in self.lw_last_batch.selectedItems():
            self.select_image_from_luid(item.text())
            break

    def on_bt_set_batch_as_selection(self):
        self.begin_edit_image_browser()
        try:
            self.update_feedback(
                status_message="Setting las batch as selected images", use_status_as_log=True
            )
            luids = [
                self.lw_last_batch.item(i).text() for i in range(0, self.lw_last_batch.count())
            ]
            if luids:
                self.update_image_browser(
                    dataframe=pd.DataFrame(data=dict(Luid=luids)), mode="keep"
                )
        finally:
            self.end_edit_image_browser()

    @pyqtSlot()
    def on_chk_use_pipeline_as_preprocessor(self):
        if (
            (self._src_image_wrapper is not None)
            and self._src_image_wrapper.good_image
            and (self.current_tool is not None)
            and self.current_tool.real_time
        ):
            self.run_process(self._src_image_wrapper)

    @pyqtSlot()
    def on_bt_process_image(self):
        if self._src_image_wrapper is not None and self._src_image_wrapper.good_image:
            self.run_process(self._src_image_wrapper)

    @pyqtSlot()
    def on_bt_run_grid_search(self):
        if not self.multithread:
            self.update_feedback(
                status_message="WARNING - Grid search in single thread mode",
                log_message=f"""{ui_consts.LOG_EXCEPTION_STR}:
                Launching grid search in single thread mode, this will end badly""",
            )
        try:
            self.set_global_enabled_state(new_state=False)
            self.process_events()
            self.thread_pool.clear()

            # Init script for preprocessing if needed
            if self.chk_use_pipeline_as_preprocessor.isChecked():
                script_ = self.script_generator
            else:
                script_ = None

            # build tools list
            self.update_feedback(
                status_message="Bulding tools for grid search, please wait...",
                use_status_as_log=True,
            )
            param_settings_list = [
                p.decode_grid_search_options() for p in self.current_tool.gizmos
            ]
            procs = list(itertools.product(*param_settings_list))
            if self.chk_random_grid_search.isChecked():
                random.shuffle(procs)
            keys = [p.name for p in self.current_tool.gizmos]

            self.update_thread_counts(thread_step=0, thread_total=len(procs), thread_waiting=0)

            # Launch grid search
            self.update_feedback(
                status_message=f"Launching grid search for {len(procs)} items",
                use_status_as_log=True,
            )
            image_data = dict(
                path=self._src_image_wrapper.file_path, luid=self._src_image_wrapper.luid
            )
            for p in procs:
                if self._batch_stop_current is True:
                    break
                self.run_runnable(
                    image_data=image_data,
                    is_batch_process=True,
                    ipt=self.current_tool.__class__(
                        **{k: (int(v) if str.isdigit(v) else v) for k, v in zip(keys, p)}
                    ),
                    script=script_,
                    exec_param=None,
                )
        except Exception as e:
            self.log_exception(f'Error while launching grid search: "{repr(e)}"')
        else:
            self.update_feedback(
                status_message="All grid search threads launched", use_status_as_log=True
            )

    @pyqtSlot()
    def on_bt_clear_result(self):
        img_count = self.cb_available_outputs.count()
        self._batch_is_active = False
        self.cb_available_outputs.clear()
        if self._src_image_wrapper is not None:
            self._src_image_wrapper.image_list = []
            self.gv_output_image.main_image = None
        while self.tw_script_sim_output.rowCount() > 0:
            self.tw_script_sim_output.removeRow(0)
        self.pb_script_gen_progress.setFormat(f"Empty")
        self.pb_script_gen_progress.setValue(0)
        self.update_feedback(status_message=f"Cleared {img_count} images", use_status_as_log=True)

    def save_image(
        self,
        image_data,
        text: str = "",
        image_path: str = "",
        add_time_stamp: bool = False,
        index: int = -1,
    ):
        if not self._src_image_wrapper.good_image:
            self.update_feedback(
                status_message="Bad image", log_message=self._src_image_wrapper.error_holder
            )
            return False

        if not text:
            if index >= 0:
                text = make_safe_name(
                    f'{image_data["plant_name"]}_{str(index)}_{image_data["name"]}'
                )
            else:
                text = make_safe_name(f'{image_data["plant_name"]}_{image_data["name"]}')
            if add_time_stamp:
                text = text + "_" + dt.now().strftime("%Y%m%d_%H%M%S")

        if not image_path:
            image_path = os.path.join(self.static_folders["image_output"], f"{text}.jpg")
        else:
            image_path = os.path.join(image_path, f"{text}.jpg")
        cv2.imwrite(image_path, image_data["image"])
        image_data["written"] = True

    @pyqtSlot()
    def on_bt_save_current_image(self):
        cb = self.cb_available_outputs
        if cb.count():
            self.save_image(
                image_data=cb.itemData(cb.currentIndex()), text="", add_time_stamp=True
            )
            self.update_feedback(
                status_message=f"Saved {cb.currentText()}", use_status_as_log=True
            )
            open_file((self.static_folders["image_output"], ""))

    @pyqtSlot()
    def on_bt_save_all_images(self):
        cb = self.cb_available_outputs
        image_name_root = dt.now().strftime("%Y%B%d_%H%M%S")
        for i in range(0, cb.count()):
            image_name = f"img_{image_name_root}_{i}.jpg"
            self.save_image(image_data=cb.itemData(i), text="", add_time_stamp=True, index=i)
            self.update_feedback(status_message=f"Saved {image_name} -- {i + 1}/{cb.count()}")
        self.update_feedback(status_message=f"Saved {cb.count()} images", use_status_as_log=True)
        open_file((self.static_folders["image_output"], ""))

    def on_video_frame_duration_changed(self):
        self.action_video_1_24_second.setChecked(self.sender() == self.action_video_1_24_second)
        self.action_video_half_second.setChecked(self.sender() == self.action_video_half_second)
        self.action_video_1_second.setChecked(self.sender() == self.action_video_1_second)
        self.action_video_5_second.setChecked(self.sender() == self.action_video_5_second)

    def on_video_resolution_changed(self):
        self.action_video_res_first_image.setChecked(
            self.sender() == self.action_video_res_first_image
        )
        self.action_video_res_1080p.setChecked(self.sender() == self.action_video_res_1080p)
        self.action_video_res_720p.setChecked(self.sender() == self.action_video_res_720p)
        self.action_video_res_576p.setChecked(self.sender() == self.action_video_res_576p)
        self.action_video_res_480p.setChecked(self.sender() == self.action_video_res_480p)
        self.action_video_res_376p.setChecked(self.sender() == self.action_video_res_376p)
        self.action_video_res_240p.setChecked(self.sender() == self.action_video_res_240p)

    def on_video_aspect_ratio_changed(self):
        self.action_video_ar_16_9.setChecked(self.sender() == self.action_video_ar_16_9)
        self.action_video_ar_4_3.setChecked(self.sender() == self.action_video_ar_4_3)
        self.action_video_ar_1_1.setChecked(self.sender() == self.action_video_ar_1_1)

    def on_action_video_bkg_color_changed(self):
        self.action_video_bkg_color_black.setChecked(
            self.sender() == self.action_video_bkg_color_black
        )
        self.action_video_bkg_color_white.setChecked(
            self.sender() == self.action_video_bkg_color_white
        )
        self.action_video_bkg_color_silver.setChecked(
            self.sender() == self.action_video_bkg_color_silver
        )

    def on_sis_changed(self):
        self.act_settings_sir_keep.setChecked(self.sender() == self.act_settings_sir_keep)
        self.act_settings_sir_2x.setChecked(self.sender() == self.act_settings_sir_2x)
        self.act_settings_sir_3x.setChecked(self.sender() == self.act_settings_sir_3x)
        self.act_settings_sir_4x.setChecked(self.sender() == self.act_settings_sir_4x)
        self.act_settings_sir_5x.setChecked(self.sender() == self.act_settings_sir_5x)
        self.act_settings_sir_6x.setChecked(self.sender() == self.act_settings_sir_6x)

    def get_de_model(self) -> QPandasModel:
        ret = self.tb_ge_dataframe.model()
        return ret if isinstance(ret, QPandasModel) else None

    def get_de_dataframe(self) -> pd.DataFrame:
        model = self.get_de_model()
        return None if model is None else model.df

    def has_de_dataframe(self) -> bool:
        return self.get_de_dataframe() is not None

    def get_de_delegate(self) -> QColorDelegate:
        ret = self.tb_ge_dataframe.itemDelegate()
        return ret if isinstance(ret, QColorDelegate) else None

    def on_tb_ge_dataframe_selection_changed(self, selected, deselected):
        image = None
        color = qApp.palette().window()

        qApp.palette().HighlightedText

        for index in selected.indexes():
            current_row = index.row()
            break
        else:
            self.gv_de_image.scene().setBackgroundBrush(color)
            self.gv_de_image.main_image = image
            return

        df = self.get_de_dataframe()
        if df is None:
            self.gv_de_image.scene().setBackgroundBrush(color)
            self.gv_de_image.main_image = image
            return

        # df = self.get_image_dataframe()
        if "source_path" in df:
            src_path = "source_path"
        elif "path" in df:
            src_path = "path"
        elif "FilePath" in df:
            src_path = "FilePath"
        else:
            src_path = ""
        if src_path:
            col = -1
            for index in selected.indexes():
                col = index.column()
            if (col >= 0) and ("error" in df.columns[col]):
                try:
                    val = int(df.iloc[current_row, col])
                except ValueError:
                    pass
                else:
                    max_val = df[df.columns[col]].max()
                    colors = ipc.build_color_steps(
                        start_color=ipc.C_LIME, stop_color=ipc.C_RED, step_count=max_val + 1
                    )
                    color = QColor(*ipc.bgr_to_rgb(colors[val]))
            image = df.iloc[current_row, df.columns.get_loc(src_path)]
            image_columns = [
                df.iloc[current_row, df.columns.get_loc(c)]
                for c in list(df.columns)
                if "image" in c
            ]
            if image_columns:
                image = ([image] + image_columns, color)
        else:
            image = None

        self.gv_de_image.scene().setBackgroundBrush(color)
        self.gv_de_image.main_image = image

    def init_data_editor(self, dataframe=None):
        self.tb_ge_dataframe.setModel(QPandasModel(dataframe))
        self.tb_ge_dataframe.setItemDelegate(
            QColorDelegate(parent=self.tb_ge_dataframe, palette=qApp.palette())
        )
        self.tb_ge_dataframe.setSortingEnabled(True)
        if dataframe is not None:
            selectionModel = self.tb_ge_dataframe.selectionModel()
            selectionModel.selectionChanged.connect(self.on_tb_ge_dataframe_selection_changed)
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
            self.tb_de_column_info.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

    def on_action_de_new_sheet(self):
        self.init_data_editor(None)
        self.update_feedback(
            status_message="Cleared dataframe",
            log_message=f"{ui_consts.LOG_INFO_STR} Cleared dataframe",
        )

    def on_action_de_load_csv(self):
        file_name_ = QFileDialog.getOpenFileName(
            parent=self,
            caption="Load dataframe as CSV",
            directory=self.dynamic_folders["csv"],
            filter="CSV(*.csv)",
        )[0]
        if file_name_:
            self.dynamic_folders["csv"] = os.path.join(os.path.dirname(file_name_), "")
            self.init_data_editor(pd.read_csv(file_name_))
            self.update_feedback(
                status_message="Dataframe loaded",
                log_message=f"{ui_consts.LOG_INFO_STR} Loaded dataframe from {file_name_}",
            )

    def on_action_de_create_sheet_from_selection(self):
        df = self.get_de_dataframe()
        if df is not None:
            self.init_data_editor(df.copy())

    def on_action_de_add_column(self):
        pass

    def on_action_de_delete_column(self):
        pass

    def on_action_de_save_csv(self):
        df = self.get_de_dataframe()
        if df is not None:
            file_name_ = QFileDialog.getSaveFileName(
                parent=self,
                caption="Save dataframe as CSV",
                directory=self.dynamic_folders["csv"],
                filter="CSV(*.csv)",
            )[0]
            if file_name_:
                self.dynamic_folders["csv"] = os.path.join(os.path.dirname(file_name_), "")
                df.to_csv(file_name_, index=False)
                self.update_feedback(
                    status_message="Dataframe saved",
                    log_message=f"{ui_consts.LOG_INFO_STR} Saved dataframe to {file_name_}",
                )
        else:
            self.update_feedback(
                status_message="No dataframe to save",
                log_message=f"{ui_consts.LOG_WARNING_STR} No dataframe to save",
            )

    def on_action_build_video_from_images(self):
        if self.cb_available_outputs.count() < 1:
            self.update_feedback(
                status_message="No images to build video from", use_status_as_log=True
            )
            return

        frame_rate = 24.0

        # Set frame duration
        if self.action_video_1_24_second.isChecked():
            frame_duration = frame_rate / 24
        elif self.action_video_half_second.isChecked():
            frame_duration = frame_rate / 2
        elif self.action_video_1_second.isChecked():
            frame_duration = frame_rate
        elif self.action_video_5_second.isChecked():
            frame_duration = frame_rate * 5
        else:
            frame_duration = frame_rate
        frame_duration = max(1, round(frame_duration))

        # Set resolution & aspect ratio
        if self.action_video_res_first_image.isChecked():
            v_height, v_width = self.cb_available_outputs.itemData(0)["image"].shape[:2]
        else:
            if self.action_video_res_720p.isChecked():
                v_height = 720
            elif self.action_video_res_576p.isChecked():
                v_height = 576
            elif self.action_video_res_480p.isChecked():
                v_height = 480
            elif self.action_video_res_376p.isChecked():
                v_height = 376
            elif self.action_video_res_240p.isChecked():
                v_height = 240
            else:
                v_height = 1080
            if self.action_video_ar_4_3.isChecked():
                v_width = int(v_height * 4 / 3)
            elif self.action_video_ar_1_1.isChecked():
                v_width = v_height
            else:
                v_width = int(v_height * 16 / 9)

        # Set background color
        if self.action_video_bkg_color_white.isChecked():
            bkg_color = ipc.C_WHITE
        elif self.action_video_bkg_color_silver.isChecked():
            bkg_color = ipc.C_SILVER
        else:
            bkg_color = ipc.C_BLACK

        selected_mode = self.current_tool
        total_ = self.cb_available_outputs.count()
        vid_name = f'{make_safe_name(selected_mode.name)}_{dt.now().strftime("%Y%B%d_%H%M%S")}_{total_}.mp4'
        v_output = os.path.join(self.static_folders["image_output"], vid_name)

        frame_rect = RectangleRegion(width=v_width, height=v_height)

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(v_output, fourcc, frame_rate, (v_width, v_height))

        self._batch_is_active = True
        self._batch_stop_current = False
        self.update_feedback(status_message="Building video", use_status_as_log=True)
        self.global_progress_start()
        try:
            canvas = np.full((v_height, v_width, 3), bkg_color, np.uint8)
            for i in range(0, self.cb_available_outputs.count()):
                if self._batch_stop_current:
                    self._batch_stop_current = False
                    self.global_progress_update(0, 0)
                    break

                if self.action_video_stack_and_jitter.isChecked() and (i < total_ - 1):
                    new_left = int(frame_rect.width * random.uniform(0, 0.7))
                    new_top = int(frame_rect.height * random.uniform(0, 0.7))
                    new_width = int((frame_rect.width - new_left) * random.uniform(0.5, 1))
                    new_height = int((frame_rect.height - new_top) * random.uniform(0.5, 1))
                    r = RectangleRegion(
                        left=new_left, width=new_width, top=new_top, height=new_height
                    )
                else:
                    if not self.action_video_stack_and_jitter.isChecked():
                        canvas = np.full((v_height, v_width, 3), bkg_color, np.uint8)
                    r = RectangleRegion(
                        left=frame_rect.left,
                        right=frame_rect.right,
                        top=frame_rect.top,
                        bottom=frame_rect.bottom,
                    )
                img = ipc.enclose_image(
                    a_cnv=canvas,
                    img=self.cb_available_outputs.itemData(i)["image"],
                    rect=RectangleRegion(left=r.left, right=r.right, top=r.top, bottom=r.bottom),
                    frame_width=2 if self.action_video_stack_and_jitter.isChecked() else 0,
                )

                def write_image_times(out_writer, img_, times=12):
                    for _ in range(0, times):
                        out_writer.write(img_)

                write_image_times(out_writer=out, img_=img, times=frame_duration)

                self.global_progress_update(i + 1, total_)
                self.update_feedback(status_message=f"Added image {i + 1}/{total_} to {vid_name}")

                self.process_events()
        except Exception as e:
            self.log_exception(f'Failed to generate video: "{repr(e)}"')
        else:
            self.update_feedback(
                status_message=f'Generated video "{vid_name}"', use_status_as_log=True
            )
            open_file((self.static_folders["image_output"], ""))
        finally:
            out.release()
            cv2.destroyAllWindows()
            self.global_progress_stop()

    def execute_current_query(self, **kwargs):
        sql_dict = {}

        for couple in (
            (self.chk_experiment, self.cb_experiment.currentText(), "Experiment"),
            (self.chk_plant, self.cb_plant.currentText(), "Plant"),
            (self.chk_date, self.cb_date.currentText(), "Date"),
            (self.chk_camera, self.cb_camera.currentText(), "Camera"),
            (self.chk_view_option, self.cb_view_option.currentText(), "view_option"),
            (self.chk_time, self.cb_time.currentText(), "Time"),
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
            additional="ORDER BY Time ASC",
            **sql_dict,
        )

    @pyqtSlot()
    def on_bt_delete_annotation(self):
        if self._src_image_wrapper is not None:
            id = self.get_image_delegate()
            if id is None:
                return
            id.set_annotation(
                luid=self._src_image_wrapper.luid, experiment=self._src_image_wrapper.experiment
            )
            self.cb_annotation_level.setCurrentIndex(0)
            self.te_annotations.clear()
            self.tw_tool_box.setTabIcon(1, QIcon())

    @pyqtSlot()
    def on_bt_clear_selection(self):
        self.begin_edit_image_browser()
        try:
            self.update_image_browser(None, mode="clear")
        finally:
            self.end_edit_image_browser()

    @pyqtSlot()
    def on_bt_remove_from_selection(self):
        self.begin_edit_image_browser()
        try:
            self.update_image_browser(dataframe=self.execute_current_query(), mode="remove")
        finally:
            self.end_edit_image_browser()

    @pyqtSlot()
    def on_bt_keep_annotated(self):
        self.begin_edit_image_browser()
        try:
            id = self.get_image_delegate()
            df = self.get_image_dataframe()
            if id is None or df is None:
                return
            df = df[["Experiment", "Luid"]]
            luids = []
            self.update_feedback(
                status_message="Keeping only tagged images", use_status_as_log=True
            )
            self.global_progress_start(add_stop_button=False)
            total_ = df.shape[0]
            i = 1
            for _, row in df.iterrows():
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
        self.update_feedback(
            status_message="Adding observations to selection", use_status_as_log=True
        )
        self._batch_stop_current = False
        self.global_progress_start(add_stop_button=False)
        try:
            dataframe = self.execute_current_query()
            if cull:
                dataframe = dataframe.sample(n=self.sp_add_random_count.value())
            self.update_image_browser(dataframe=dataframe, mode="add")
        except Exception as e:
            self.log_exception(f"Add to selection failed: {repr(e)}")
        finally:
            self.global_progress_stop()
            self.end_edit_image_browser()

    @pyqtSlot()
    def on_bt_add_random(self):
        self.inner_add_to_selection(cull=True)

    @pyqtSlot()
    def on_bt_add_to_selection(self):
        self.inner_add_to_selection(cull=False)

    def cb_available_outputs_current_index_changed(self, idx):
        if not self._updating_available_images and (0 <= idx < self.cb_available_outputs.count()):
            self._image_dict = self.cb_available_outputs.itemData(idx)
            self.gv_output_image.main_image = self._image_dict["image"]
            if "data" in self._image_dict:
                self.update_output_tab(self._image_dict["data"])
            else:
                self.update_output_tab({})

    def cb_experiment_current_index_changed(self, _):
        if self._updating_combo_boxes or self._initializing:
            return
        self.clear_plant_combo_box()
        if self.cb_experiment.count() > 0:
            self._current_exp = self.cb_experiment.currentText()
            self.fill_plant_combo_box()
        self.chk_experiment.setEnabled(self.cb_experiment.count() > 0)

    def cb_plant_current_index_changed(self, _):
        if self._updating_combo_boxes or self._initializing:
            return
        self.clear_date_combo_box()
        if self.cb_plant.count() > 0:
            self._current_plant = self.cb_plant.currentText()
            self.fill_date_combo_box()
        self.chk_plant.setEnabled(self.cb_plant.count() > 0)

    def cb_date_current_index_changed(self, _):
        if self._updating_combo_boxes or self._initializing:
            return
        self.clear_camera_combo_box()
        if self.cb_date.count() > 0:
            self._current_date = dt.strptime(self.cb_date.currentText(), _DATE_FORMAT).date()
            self.fill_camera_combo_box()
        self.chk_date.setEnabled(self.cb_date.count() > 0)

    def cb_camera_current_index_changed(self, _):
        if self._updating_combo_boxes or self._initializing:
            return
        self.clear_view_option_combo_box()
        if self.cb_camera.count() > 0:
            self._current_camera = self.cb_camera.currentText()
            self.fill_view_option_combo_box()
        self.chk_camera.setEnabled(self.cb_camera.count() > 0)

    def cb_view_option_current_index_changed(self, _):
        try:
            if self._updating_combo_boxes or self._initializing:
                return
            self.clear_time_combo_box()
            if self.cb_view_option.count() > 0:
                self._current_view_option = self.cb_view_option.currentText()
                self.fill_time_combo_box()
            self.chk_view_option.setEnabled(self.cb_view_option.count() > 0)
        except Exception as e:
            self.log_exception(f"Selection failed: {repr(e)}")

    def cb_time_current_index_changed(self, _):
        if self.cb_time.count() > 0 and not self._updating_combo_boxes:
            self._current_time = dt.strptime(self.cb_time.currentText(), _TIME_FORMAT).time()
            self.file_name = self.current_selected_image_path()

    def delete_pipeline_operator(self):
        if self._updating_process_modes:
            return
        self.script_generator.delete_operators(constraints=dict(uuid=self.sender().param))
        self.update_pipeline_display()

    def run_pipeline_operator(self):
        if self._updating_process_modes:
            return
        self.run_process(wrapper=self._src_image_wrapper, ipt=self.sender().tool)

    def display_pipeline_setting_feedback(self):
        if self._updating_process_modes or (self._src_image_wrapper is None):
            return
        self.script_generator.update_settings_feedback(
            src_wrapper=self._src_image_wrapper,
            param=self.sender().param,
            call_back=self.print_image_callback,
        )

    def move_pipeline_item_up(self):
        src = self.script_generator.get_something(key=self.sender().param)
        src_idx = self.script_generator.ip_operators.index(src)
        for i in reversed(range(0, src_idx)):
            dst = self.script_generator.ip_operators[i]
            if dst["kind"] == src["kind"]:
                self.script_generator.swap_operators(indexes=[(i, src_idx)])
                self.update_pipeline_display()
                return

    def move_pipeline_item_down(self):
        src = self.script_generator.get_something(key=self.sender().param)
        src_idx = self.script_generator.ip_operators.index(src)
        for i in range(src_idx + 1, len(self.script_generator.ip_operators)):
            dst = self.script_generator.ip_operators[i]
            if dst["kind"] == src["kind"]:
                self.script_generator.swap_operators(indexes=[(i, src_idx)])
                self.update_pipeline_display()
                return

    def on_action_add_white_balance_fixer(self):
        selected_mode = self.current_tool.copy(copy_wrapper=False)
        self.script_generator.add_operator(
            operator=selected_mode, kind=ipc.TOOL_GROUP_PRE_PROCESSING_STR
        )
        self.update_pipeline_display()

    def on_action_build_roi_with_raw_image(self):
        selected_mode = self.current_tool.copy(copy_wrapper=False)
        self.script_generator.add_operator(
            operator=selected_mode, kind=ipc.TOOL_GROUP_ROI_RAW_IMAGE_STR
        )
        self.update_pipeline_display()

    def on_action_build_roi_with_pre_processed_image(self):
        selected_mode = self.current_tool.copy(copy_wrapper=False)
        self.script_generator.add_operator(
            operator=selected_mode, kind=ipc.TOOL_GROUP_ROI_PP_IMAGE_STR
        )
        self.update_pipeline_display()

    def on_action_add_exposure_fixer(self):
        selected_mode = self.current_tool.copy(copy_wrapper=False)
        self.script_generator.add_operator(
            operator=selected_mode, kind=ipc.TOOL_GROUP_EXPOSURE_FIXING_STR
        )
        self.update_pipeline_display()

    def on_action_add_white_balance_corrector(self):
        selected_mode = self.current_tool.copy(copy_wrapper=False)
        self.script_generator.add_operator(
            operator=selected_mode, kind=ipc.TOOL_GROUP_WHITE_BALANCE_STR
        )
        self.update_pipeline_display()

    def update_pipeline_display(self):
        def add_button(
            node, tool, param, ressource_path, column, hint, call_back, enabled_state=True
        ):
            bt = QPushButtonWthParam(tool=tool, param=param, allow_real_time=False)
            bt.setFlat(True)
            bt.setEnabled(enabled_state)
            bt.setIcon(QIcon(ressource_path))
            bt.clicked.connect(call_back)
            self.tv_queued_tools.setItemWidget(node, column, bt)
            node.setToolTip(column, hint)

        def add_params_as_nodes(tool, root_node, allow_real_time: bool = False):
            if isinstance(tool, dict):
                param_list = tool["tool"].all_params()
                tool_ = tool["tool"]
            else:
                param_list = tool.all_params()
                tool_ = tool
            for p in param_list:
                line = QTreeWidgetItem(root_node, [])
                widget, label = self.init_param_widget(
                    tool=tool, param=p, allow_real_time=allow_real_time
                )
                if widget and hasattr(tool, "lock_once_added") and tool.lock_once_added:
                    widget.setEnabled(False)
                if label and widget:
                    self.tv_queued_tools.setItemWidget(line, 0, label)
                    self.tv_queued_tools.setItemWidget(line, 1, widget)
                elif widget:
                    self.tv_queued_tools.setItemWidget(line, 0, widget)
                elif label:
                    self.tv_queued_tools.setItemWidget(line, 0, label)
                else:
                    line.setText(0, str(p))
                if (
                    widget
                    and hasattr(tool, "update_feedback_items")
                    and (p.name in tool.update_feedback_items)
                ):
                    # Add display button
                    add_button(
                        node=line,
                        tool=tool,
                        param=p,
                        ressource_path=":/image_process/resources/Play.png",
                        column=2,
                        hint=f"Display {p.desc}",
                        call_back=self.display_pipeline_setting_feedback,
                    )
            tool_.update_inputs(
                update_values=self.build_param_overrides(
                    wrapper=self._src_image_wrapper, tool=tool_
                )
            )

        def add_nodes(root_name: str, item_list: list, is_expand_root: bool):
            rc = (
                len(item_list[0].gizmos)
                if (len(item_list) > 0) and isinstance(item_list[0], IptParamHolder)
                else len(item_list)
            )
            root_ = QTreeWidgetItem(self.tv_queued_tools, [f"{root_name} ({rc})"])
            root_.setExpanded(is_expand_root)
            item_count = len(item_list)
            for j, item in enumerate(item_list):
                if isinstance(item, dict):
                    if item.get("tool", None) is not None:
                        # Initialise
                        param_text = item["tool"].input_params_as_str(
                            exclude_defaults=True,
                            excluded_params=("progress_callback",),
                            forced_params=("channel",),
                        )
                        node_ = CTreeWidgetItem(root_, [item["tool"].name, param_text])
                        node_.setCheckState(
                            0, Qt.Checked if item["enabled"] is True else Qt.Unchecked
                        )
                        node_.setData(0, Qt.UserRole, item["uuid"])
                        node_.setToolTip(1, param_text.replace(",", "\n"))
                        # Add buttons
                        if item["kind"] in [
                            ipc.TOOL_GROUP_EXPOSURE_FIXING_STR,
                            ipc.TOOL_GROUP_WHITE_BALANCE_STR,
                            ipc.TOOL_GROUP_PRE_PROCESSING_STR,
                            ipc.TOOL_GROUP_THRESHOLD_STR,
                            ipc.TOOL_GROUP_ROI_RAW_IMAGE_STR,
                            ipc.TOOL_GROUP_ROI_PP_IMAGE_STR,
                        ]:
                            add_button(
                                node=node_,
                                tool=item["tool"],
                                param=item["uuid"],
                                ressource_path=":/image_process/resources/Play.png",
                                column=2,
                                hint=f'Run {item["tool"].name}',
                                call_back=self.run_pipeline_operator,
                            )
                        add_button(
                            node=node_,
                            tool=item["tool"],
                            param=item["uuid"],
                            ressource_path=":/common/resources/Up.png",
                            column=3,
                            hint=f'Move {item["tool"].name} up',
                            call_back=self.move_pipeline_item_up,
                            enabled_state=j > 0,
                        )
                        add_button(
                            node=node_,
                            tool=item["tool"],
                            param=item["uuid"],
                            ressource_path=":/common/resources/Down.png",
                            column=4,
                            hint=f'Move {item["tool"].name} down',
                            call_back=self.move_pipeline_item_down,
                            enabled_state=j < item_count - 1,
                        )
                        add_button(
                            node=node_,
                            tool=item["tool"],
                            param=item["uuid"],
                            ressource_path=":/annotation_level/resources/Delete.png",
                            column=5,
                            hint=f'Delete {item["tool"].name}',
                            call_back=self.delete_pipeline_operator,
                        )
                        # Add params
                        add_params_as_nodes(
                            item,
                            node_,
                            item["kind"]
                            in [ipc.TOOL_GROUP_ROI_PP_IMAGE_STR, ipc.TOOL_GROUP_ROI_RAW_IMAGE_STR],
                        )
                    elif item.get("feature", None) is not None:
                        node_ = CTreeWidgetItem(root_, [item["feature"]])
                        node_.setCheckState(
                            0, Qt.Checked if item["enabled"] is True else Qt.Unchecked
                        )
                        node_.setData(0, Qt.UserRole, item["feature"])
                elif isinstance(item, str):
                    node_ = QTreeWidgetItem(root_, [item])
                    node_.setToolTip(1, item)
                elif isinstance(item, tuple):
                    node_ = QTreeWidgetItem(root_, [item[0], item[1]])
                    node_.setToolTip(1, f"{item[0]}: {item[1]}")
                elif isinstance(item, IptParamHolder):
                    add_params_as_nodes(item, root_)
                elif isinstance(item, AbstractRegion):
                    node_ = QTreeWidgetItem(root_, [repr(item)])
                    node_.setToolTip(1, repr(item))
                else:
                    QTreeWidgetItem(root_, ["Unknown node"])

        # Update pipeline
        self._updating_process_modes = True
        try:
            # Update queued tools
            self.tv_queued_tools.clear()
            nodes_dict = {
                ipc.TOOL_GROUP_ROI_RAW_IMAGE_STR: ipc.TOOL_GROUP_ROI_RAW_IMAGE_STR,
                ipc.TOOL_GROUP_EXPOSURE_FIXING_STR: ipc.TOOL_GROUP_EXPOSURE_FIXING_STR,
                ipc.TOOL_GROUP_PRE_PROCESSING_STR: ipc.TOOL_GROUP_PRE_PROCESSING_STR,
                ipc.TOOL_GROUP_ROI_PP_IMAGE_STR: ipc.TOOL_GROUP_ROI_PP_IMAGE_STR,
                ipc.TOOL_GROUP_THRESHOLD_STR: ipc.TOOL_GROUP_THRESHOLD_STR,
                ipc.TOOL_GROUP_MASK_CLEANUP_STR: ipc.TOOL_GROUP_MASK_CLEANUP_STR,
                ipc.TOOL_GROUP_FEATURE_EXTRACTION_STR: ipc.TOOL_GROUP_FEATURE_EXTRACTION_STR,
                ipc.TOOL_GROUP_IMAGE_GENERATOR_STR: ipc.TOOL_GROUP_IMAGE_GENERATOR_STR,
            }
            for k, v in nodes_dict.items():
                add_nodes(
                    root_name=v,
                    item_list=self.script_generator.get_operators(dict(kind=k)),
                    is_expand_root=True,
                )
            add_nodes(
                root_name="Settings",
                item_list=[self.script_generator.settings],
                is_expand_root=False,
            )

            self.tv_queued_tools.header().setStretchLastSection(False)
            self.tv_queued_tools.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
            self.tv_queued_tools.header().setSectionResizeMode(1, QHeaderView.Stretch)
            self.tv_queued_tools.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
            self.tv_queued_tools.header().setSectionResizeMode(3, QHeaderView.ResizeToContents)
            self.tv_queued_tools.setColumnWidth(2, 16)
            self.tv_queued_tools.setColumnWidth(3, 16)
            self.tv_queued_tools.setColumnWidth(4, 16)
            self.tv_queued_tools.setColumnWidth(5, 16)

            # Update others
            self.rb_pp_active_script.setEnabled(self.script_generator.is_functional)
        except Exception as e:
            self.log_exception(f"Unable to update pipeline: {str(e)}")
        finally:
            self._updating_process_modes = False

        # Update script
        self.update_script_display()

    def update_script_display(self):
        try:
            self.txtb_script.clear()
            self.txtb_script.insertPlainText(self.script_generator.code())
        except Exception as e:
            self.log_exception(f"Unable to update pipeline: {str(e)}")
        finally:
            self._updating_process_modes = False

    def on_actionAdd_channel_mask(self):
        selected_mode = self.current_tool.copy(copy_wrapper=False)
        self.script_generator.add_operator(
            operator=selected_mode, kind=ipc.TOOL_GROUP_THRESHOLD_STR
        )
        self.update_pipeline_display()

    def on_action_set_contour_cleaner(self):
        selected_mode = self.current_tool.copy(copy_wrapper=False)
        self.script_generator.add_operator(
            operator=selected_mode, kind=ipc.TOOL_GROUP_MASK_CLEANUP_STR
        )
        self.update_pipeline_display()

    def on_action_add_feature_extractor(self):
        selected_mode = self.current_tool.copy(copy_wrapper=False)
        self.script_generator.add_operator(
            operator=selected_mode, kind=ipc.TOOL_GROUP_FEATURE_EXTRACTION_STR
        )
        self.update_pipeline_display()

    def on_action_add_image_generator(self):
        selected_mode = self.current_tool.copy(copy_wrapper=False)
        self.script_generator.add_operator(
            operator=selected_mode, kind=ipc.TOOL_GROUP_IMAGE_GENERATOR_STR
        )
        self.update_pipeline_display()

    def on_bt_clear_pipeline(self):
        if self.script_generator is not None:
            self.script_generator.reset()
        self.tv_queued_tools.clear()
        self.le_pp_selected_pipeline.setText("")
        self.lbl_pipeline_name.setText("")
        if self.rb_pp_active_script.isChecked:
            self._update_pp_pipeline_state(default_process=True, active=False, load_script=False)
        self.rb_pp_active_script.setEnabled(False)

    def on_bt_load_pipeline(self):
        file_name_ = QFileDialog.getOpenFileName(
            parent=self,
            caption="Load pipeline",
            directory=self.dynamic_folders["pipeline"],
            filter=_PIPELINE_FILE_FILTER,
        )[0]
        if file_name_:
            self.dynamic_folders["pipeline"] = os.path.join(os.path.dirname(file_name_), "")
            self.on_bt_clear_pipeline()
            try:
                script_ = IptStrictPipeline.load(file_name_)
                if isinstance(script_, IptStrictPipeline):
                    self.script_generator = script_
                    if self.script_generator.last_error.error_count > 0:
                        self.update_feedback(
                            status_message="Errors while loading pipeline (cf. log)",
                            log_message=f"{ui_consts.LOG_WARNING_STR}: {self.script_generator.last_error.to_html()}",
                        )
                    self.update_pipeline_display()
                elif isinstance(script_, Exception):
                    self.log_exception(f"Error while loading pipeline: {str(script_)}")
                    self._update_pp_pipeline_state(
                        default_process=True, active=False, load_script=False
                    )
                    return
                else:
                    self.log_exception(f"Unknown error while loading pipeline:  {str(script_)}")
                    self._update_pp_pipeline_state(
                        default_process=True, active=False, load_script=False
                    )
                    return
            except AttributeError as e:
                self.log_exception(f"This pipeline was pickle with an older version: {str(e)}")
                self._update_pp_pipeline_state(
                    default_process=True, active=False, load_script=False
                )
            except ValueError as e:
                self.log_exception(f"Unable to load json pipeline: {str(e)}")
                self._update_pp_pipeline_state(
                    default_process=True, active=False, load_script=False
                )
            except Exception as e:
                self.log_exception(f"Unable to unpickle pipeline: {str(e)}")
                self._update_pp_pipeline_state(
                    default_process=True, active=False, load_script=False
                )
            else:
                self.update_feedback(
                    status_message=f'Loaded pipeline from "{file_name_}"', use_status_as_log=True
                )
                self.le_pp_selected_pipeline.setText(file_name_)
                if hasattr(self.script_generator, "name"):
                    self.lbl_pipeline_name.setText(self.script_generator.name)
                else:
                    font_metrics = QFontMetrics(self.lbl_pipeline_name.font())
                    elided_fn = font_metrics.elidedText(file_name_, Qt.ElideLeft, 200)
                    self.lbl_pipeline_name.setText(elided_fn)
                self._update_pp_pipeline_state(
                    default_process=False, active=False, load_script=True
                )
            finally:
                pass

    def on_bt_save_pipeline(self):
        file_name_ = QFileDialog.getSaveFileName(
            parent=self,
            caption="Save pipeline",
            directory=self.dynamic_folders["pipeline"],
            filter=_PIPELINE_FILE_FILTER,
        )[0]
        if file_name_:
            self.dynamic_folders["pipeline"] = os.path.join(os.path.dirname(file_name_), "")
            if not file_name_.lower().endswith(".tipp") and not file_name_.lower().endswith(
                ".json"
            ):
                file_name_ += ".tipp"
            res = self.script_generator.save(file_name_)
            if res is None:
                self.update_feedback(
                    status_message=f'Saved pipeline to: "{file_name_}"', use_status_as_log=True
                )
            else:
                self.log_exception(f"Unable to save pipeline: {str(res)}")

    def on_action_save_as_python_script(self):
        file_name_ = QFileDialog.getSaveFileName(
            parent=self,
            caption="Save script",
            directory=self.dynamic_folders["script"],
            filter="Python script (*.py)",
        )[0]
        if file_name_:
            self.dynamic_folders["script"] = os.path.join(os.path.dirname(file_name_), "")
            res = self.script_generator.save_as_script(file_name_)
            if res is None:
                self.update_feedback(
                    status_message=f'Saved pipeline as script to: "{file_name_}"',
                    use_status_as_log=True,
                )
            else:
                self.log_exception(f"Unable to save pipeline as script: {str(res)}")

    def script_sim_progress_callback(self, step, total, msg):
        self.pb_script_gen_progress.setFormat(f"{msg} {step}/{total}")
        self.pb_script_gen_progress.setValue(round((step + 1) / total * 100))

    def on_bt_script_gen_run(self):
        self.run_process(wrapper=self._src_image_wrapper)

    def on_chk_pp_show_last_item(self):
        if not self.chk_pp_show_last_item.isChecked():
            self.gv_last_processed_item.main_image = None

    def build_param_overrides(self, wrapper, tool):
        param_names_list = [p.kind for p in tool.gizmos]
        res = {}
        if "channel_selector" in param_names_list and wrapper is not None:
            res["channels"] = {
                ci[1]: ipc.get_hr_channel_name(ci[1])
                for ci in ipc.create_channel_generator(wrapper.available_channels)
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
        if isinstance(param.allowed_values, dict):
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
        elif isinstance(param.allowed_values, tuple) or isinstance(param.allowed_values, list):
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
                wrapper=self._src_image_wrapper, ipt=btn.module.tool, target_module=btn.module.uuid
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
        self.gv_output_image.main_image = image

    def do_after_process_param_changed(self, widget):
        tool = widget.tool
        if hasattr(tool, "owner") and isinstance(tool.owner, ModuleNode):
            tool.owner.root.invalidate(tool.owner)
            if widget.allow_real_time and tool.real_time and not tool.block_feedback:
                self.run_process(
                    wrapper=self._src_image_wrapper, ipt=tool, target_module=tool.owner.uuid
                )
        elif isinstance(tool, IptBase):
            if widget.allow_real_time and tool.real_time and not tool.block_feedback:
                self.run_process(wrapper=self._src_image_wrapper, ipt=tool)
            self.update_tool_code()
        elif isinstance(tool, dict):
            ipt = tool.get("tool", None)
            if ipt is not None:
                if widget.allow_real_time and ipt.real_time and not ipt.block_feedback:
                    self.run_process(wrapper=self._src_image_wrapper, ipt=ipt)
                self.script_generator.invalidate(tool["uuid"])
            self.update_script_display()
        elif type(tool).__name__ == "SettingsHolder":
            self.script_generator.update_settings_feedback(
                src_wrapper=self._src_image_wrapper,
                param=widget.param,
                call_back=self.print_image_callback,
            )
            self.update_script_display()

    def on_process_param_clicked(self):
        if self._updating_process_modes:
            return
        widget = self.sender()
        tool = widget.tool
        if isinstance(tool, IptBase):
            self.run_process(wrapper=self._src_image_wrapper, ipt=tool, exec_param=widget.param)

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
        self.chk_experiment.setText(f"Experiment ({len(exp_list)}): ")
        self.cb_experiment.addItems(exp_list)
        self.cb_experiment.setEnabled(self.cb_experiment.count() > 1)
        if self._updating_combo_boxes:
            target_index = self.cb_experiment.findText(self._current_exp)
            if target_index < 0:
                target_index = 0
                self._current_exp = self.cb_experiment.itemText(0)
            self.cb_experiment.setCurrentIndex(target_index)

    def fill_plant_combo_box(self):
        self.clear_plant_combo_box()
        plant_lst = self.get_query_items(column="Plant", experiment=self._current_exp)
        self.chk_plant.setText(f"Plant ({len(plant_lst)}): ")
        self.cb_plant.addItems(sorted(plant_lst, key=lambda x: natural_keys(x)))
        self.cb_plant.setEnabled(self.cb_plant.count() > 1)
        if self._updating_combo_boxes:
            target_index = self.cb_plant.findText(self._current_plant)
            if target_index < 0:
                target_index = 0
                self._current_plant = self.cb_plant.itemText(0)
            self.cb_plant.setCurrentIndex(target_index)

    def fill_date_combo_box(self):
        self.clear_date_combo_box()
        date_list = [
            item.replace("-", "/") if isinstance(item, str) else item.strftime(_DATE_FORMAT)
            for item in self.get_query_items(
                column="Date", experiment=self._current_exp, plant=self._current_plant
            )
        ]
        self.chk_date.setText(f"Date ({len(date_list)}): ")
        self.cb_date.addItems(date_list)
        self.cb_date.setEnabled(self.cb_date.count() > 1)
        if self._updating_combo_boxes:
            target_index = self.cb_date.findText(self._current_date.strftime(_DATE_FORMAT))
            if target_index < 0:
                target_index = 0
                self._current_date = dt.strptime(self.cb_date.itemText(0), _DATE_FORMAT).date()
            self.cb_date.setCurrentIndex(target_index)

    def fill_camera_combo_box(self):
        self.clear_camera_combo_box()
        cam_list = self.get_query_items(
            column="Camera",
            experiment=self._current_exp,
            plant=self._current_plant,
            date=self._current_date,
        )
        self.chk_camera.setText(f"Camera ({len(cam_list)}): ")
        self.cb_camera.addItems(cam_list)
        self.cb_camera.setEnabled(self.cb_camera.count() > 1)
        if self._updating_combo_boxes:
            target_index = self.cb_camera.findText(self._current_camera)
            if target_index < 0:
                target_index = 0
                self._current_camera = self.cb_camera.itemText(0)
            self.cb_camera.setCurrentIndex(target_index)

    def fill_view_option_combo_box(self):
        self.clear_view_option_combo_box()
        opt_lst = self.get_query_items(
            column="view_option",
            experiment=self._current_exp,
            plant=self._current_plant,
            date=self._current_date,
            camera=self._current_camera,
        )
        self.chk_view_option.setText(f"View option ({len(opt_lst)}): ")
        self.cb_view_option.addItems(sorted(opt_lst, key=lambda x: natural_keys(x)))
        self.cb_view_option.setEnabled(self.cb_view_option.count() > 1)
        if self._updating_combo_boxes:
            target_index = self.cb_view_option.findText(self._current_view_option)
            if target_index < 0:
                target_index = 0
                self._current_view_option = self.cb_view_option.itemText(0)
            self.cb_view_option.setCurrentIndex(target_index)

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
            self.chk_time.setText(f"Time ({len(time_lst)}): ")
            self.cb_time.addItems(time_lst)
            self.cb_time.setEnabled(self.cb_time.count() > 1)
            if self._updating_combo_boxes:
                target_index = self.cb_time.findText(self._current_time.strftime(_TIME_FORMAT))
                if target_index < 0:
                    target_index = 0
                    if len(time_lst) > 0:
                        self._current_time = dt.strptime(
                            self.cb_time.itemText(0), _TIME_FORMAT
                        ).time()
                    self.cb_time.setCurrentIndex(target_index)
        except Exception as e:
            self.log_exception(f"Failed to fill time combobox: {repr(e)}")

    def clear_exp_combo_box(self):
        self.cb_experiment.clear()
        if not self._updating_combo_boxes:
            self._current_exp = ""
        self.clear_plant_combo_box()

    def clear_plant_combo_box(self):
        self.cb_plant.clear()
        if not self._updating_combo_boxes:
            self._current_plant = ""
        self.clear_date_combo_box()

    def clear_date_combo_box(self):
        self.cb_date.clear()
        if not self._updating_combo_boxes:
            self._current_date = dt.now().date()
        self.clear_camera_combo_box()

    def clear_camera_combo_box(self):
        self.cb_camera.clear()
        if not self._updating_combo_boxes:
            self._current_camera = ""
        self.clear_view_option_combo_box()

    def clear_view_option_combo_box(self):
        self.cb_view_option.clear()
        if not self._updating_combo_boxes:
            self._current_view_option = ""
        self.clear_time_combo_box()

    def clear_time_combo_box(self):
        if not self._updating_combo_boxes:
            self._current_time = dt.now().time()
        self.cb_time.clear()

    def current_selected_image_path(self):
        ret = self.query_current_database(
            command="SELECT",
            columns="FilePath",
            additional="ORDER BY Time ASC",
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

    def current_selected_image_luid(self):
        ret = self.query_current_database(
            command="SELECT",
            columns="Luid",
            additional="ORDER BY Time ASC",
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

    def select_image_from_luid(self, luid):
        if not luid:
            data = None
        else:
            data = self.query_one_current_database(
                command="SELECT",
                columns="Experiment, Plant, Date, Camera, view_option, Time",
                Luid=luid,
            )
        if data is not None:
            self._updating_combo_boxes = True
            try:
                self._current_exp = data[0]
                self._current_plant = data[1]
                self._current_date = data[2]
                self._current_camera = data[3]
                self._current_view_option = data[4]
                self._current_time = data[5]
                self.fill_exp_combo_box()
                self.fill_plant_combo_box()
                self.fill_date_combo_box()
                self.fill_camera_combo_box()
                self.fill_view_option_combo_box()
                self.fill_time_combo_box()
                self.file_name = self.current_selected_image_path()
            finally:
                self._updating_combo_boxes = False
            return True
        else:
            return False

    def select_file(self):
        self.file_name, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select source image",
            os.path.join(os.path.expanduser("~"), "Pictures", "TPMP_input", ""),
        )

    def on_action_enable_annotations_checked(self):
        try:
            id = self.tv_image_browser.itemDelegate()
            if id is None:
                return
            id.use_annotations = self.actionEnable_annotations.isChecked()
        except Exception as e:
            self.log_exception(f"Failed to add annotation data: {repr(e)}")

    def on_action_use_multithreading(self):
        self.multithread = self.action_use_multithreading.isChecked()

    def on_action_use_pipeline_cache(self):
        self.use_pipeline_cache = self.action_use_pipeline_cache.isChecked()
        self.script_generator.use_cache = self.use_pipeline_cache

    def on_action_save_pipeline_processor_state(self):
        model = self.get_image_model()
        if (model is None) or (model.rowCount() == 0):
            self.update_feedback(
                status_message="Pipeline state save: no images",
                log_message=f"{ui_consts.LOG_ERROR_STR}: Pipeline state save: no images",
            )
            return
        if (self.script_generator is not None) and not self.script_generator.is_empty:
            script_ = self.script_generator.copy()
        else:
            self.update_feedback(
                status_message="Pipeline state save: no script",
                log_message=f"{ui_consts.LOG_ERROR_STR}: Pipeline state save: no script",
            )
            return
        file_name_ = QFileDialog.getSaveFileName(
            parent=self,
            caption="Save pipeline processor state",
            directory=self.dynamic_folders["pp_state"],
            filter="JSON(*.json)",
        )[0]
        if file_name_:
            self.dynamic_folders["pp_state"] = os.path.join(os.path.dirname(file_name_), "")
            append_experience_name = (
                model.get_cell_data(row_number=0, column_name="Experiment")
                if self.cb_pp_append_experience_name.isChecked()
                else ""
            )
            database_data = (
                None if self.current_database is None else self.current_database.db_info
            )
            with open(file_name_, "w") as jw:
                json.dump(
                    dict(
                        output_folder=self.le_pp_output_folder.text(),
                        csv_file_name=self.edt_csv_file_name.text(),
                        overwrite_existing=self.cb_pp_overwrite.isChecked(),
                        append_experience_name=append_experience_name,
                        append_time_stamp=self.cb_pp_append_timestamp_to_output_folder.isChecked(),
                        script=script_.to_json(),
                        generate_series_id=self.cb_pp_generate_series_id.isChecked(),
                        series_id_time_delta=self.sp_pp_time_delta.value(),
                        data_frame=model.images.to_dict(orient="list"),
                        database_data=database_data,
                        thread_count=self.sl_pp_thread_count.value(),
                    ),
                    jw,
                    indent=2,
                )
                self.update_feedback(
                    status_message="Pipeline processor state saved",
                    log_message=f'Pipeline state saved to: "{file_name_}"',
                )

    def find_tool_by_name(self, tool_name):
        lst = self._ip_tools_holder.ipt_list
        for ipt_ in lst:
            if ipt_.name == tool_name:
                return ipt_
                break
        else:
            self.update_feedback(
                status_message=f'Unable to find "{tool_name}" operator', use_status_as_log=True
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
            try:
                # Backup annotation
                if self._src_image_wrapper is not None:
                    id = self.get_image_delegate()
                    if id is not None:
                        id.set_annotation(
                            luid=self._src_image_wrapper.luid,
                            experiment=self._src_image_wrapper.experiment,
                            kind=self.cb_annotation_level.currentText(),
                            text=self.te_annotations.toPlainText(),
                            auto_text="",
                        )

                if os.path.isfile(value):
                    self._src_image_wrapper = ipo_factory(
                        file_path=value,
                        options=self._options,
                        force_abstract=False,
                        data_base=self.current_database,
                    )
                    self.gv_source_image.main_image = self._src_image_wrapper.current_image
                else:
                    self._src_image_wrapper = None

                # Restore annotation
                self.te_annotations.clear()
                if self.actionEnable_annotations.isChecked() and (
                    self._src_image_wrapper is not None
                ):
                    self.restore_annotation(
                        self._src_image_wrapper, self._src_image_wrapper.experiment
                    )
            except Exception as e:
                self._src_image_wrapper = None
                self.log_exception(f"Failed to load/save annotation: {repr(e)}")

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
                        if (selected_mode is not None) and selected_mode.real_time:
                            self.run_process(wrapper=self._src_image_wrapper, ipt=selected_mode)
                        elif not self._batch_is_active:
                            img = self._src_image_wrapper.current_image
                            if self._src_image_wrapper.good_image:
                                self.gv_output_image.main_image = img
                    self.edt_csv_file_name.setText(
                        f"{self._src_image_wrapper.experiment}_raw_data"
                    )
                except Exception as e:
                    self._file_name = ""
                    self.setWindowTitle(f"{_PRAGMA_NAME} -- Select input file")
                    self.log_exception(f"Failed to load/save annotation: {repr(e)}")
                finally:
                    self._updating_process_modes = False
            else:
                self._file_name = ""
                self.setWindowTitle(f"{_PRAGMA_NAME} -- Select input file")

    @property
    def current_tool(self):
        return self._current_tool

    @current_tool.setter
    def current_tool(self, value):
        if self._current_tool != value:
            self._current_tool = value

            # if self._initializing:
            #     return
            self._updating_process_modes = True
            try:
                # Delete existing widgets
                lst = self._ip_tools_holder.ipt_list
                for ipt_ in lst:
                    if ipt_.name == value.name:
                        self.bt_select_tool.setText(ipt_.name)
                    for p in ipt_.gizmos:
                        p.clear_widgets()
                for i in reversed(range(self.gl_tool_params.count())):
                    self.gl_tool_params.itemAt(i).widget().setParent(None)
                for i in reversed(range(self.gl_grid_search_params.count())):
                    self.gl_grid_search_params.itemAt(i).widget().setParent(None)

                # Update help browser
                self.txtb_tool_help.clear()
                doc_ = value.hint
                self.txtb_tool_help.insertPlainText(doc_)
                icon_ = QIcon(":/annotation_level/resources/Help.png")
                self.tw_tool_box.setTabIcon(0, icon_)

                # Update script generator menu
                self.action_add_exposure_fixer.setEnabled(
                    ipc.TOOL_GROUP_EXPOSURE_FIXING_STR in value.use_case
                )
                self.action_add_white_balance_corrector.setEnabled(
                    ipc.TOOL_GROUP_WHITE_BALANCE_STR in value.use_case
                )
                self.actionAdd_white_balance_fixer.setEnabled(
                    ipc.TOOL_GROUP_PRE_PROCESSING_STR in value.use_case
                )
                self.actionAdd_channel_mask.setEnabled(
                    ipc.TOOL_GROUP_THRESHOLD_STR in value.use_case
                )
                self.action_build_roi_with_raw_image.setEnabled(
                    bool(
                        set(value.use_case)
                        & {ipc.TOOL_GROUP_ROI_RAW_IMAGE_STR, ipc.TOOL_GROUP_ROI_PP_IMAGE_STR}
                    )
                )
                self.action_build_roi_with_pre_processed_image.setEnabled(
                    bool(
                        set(value.use_case)
                        & {ipc.TOOL_GROUP_ROI_RAW_IMAGE_STR, ipc.TOOL_GROUP_ROI_PP_IMAGE_STR}
                    )
                )
                self.actionSet_contour_cleaner.setEnabled(
                    ipc.TOOL_GROUP_MASK_CLEANUP_STR in value.use_case
                )
                self.action_add_feature_extractor.setEnabled(
                    ipc.TOOL_GROUP_FEATURE_EXTRACTION_STR in value.use_case
                )
                self.action_add_image_generator.setEnabled(
                    ipc.TOOL_GROUP_IMAGE_GENERATOR_STR in value.use_case
                )

                # Add new widgets
                for row_, param in enumerate(value.gizmos):
                    widget, label = self.init_param_widget(tool=value, param=param)
                    if label and widget:
                        self.gl_tool_params.addWidget(label, row_, 0)
                        self.gl_tool_params.addWidget(widget, row_, 1)
                    elif widget:
                        self.gl_tool_params.addWidget(widget, row_, 0, 1, 2)
                    elif label:
                        self.gl_tool_params.addWidget(label, row_, 0, 1, 2)
                    else:
                        pass
                    # Fill grid search controls
                    if param.is_input and not param.allowed_values == "input_button":
                        # Build label
                        param.gs_label = QLabel(param.desc)
                        self.gl_grid_search_params.addWidget(param.gs_label, row_, 0)
                        # Build text input
                        widget = QLineEditWthParam(tool=value, param=param)
                        widget.setText(param.grid_search_options)
                        param.gs_input = widget
                        widget.textEdited.connect(self.on_grid_search_param_changed)
                        self.gl_grid_search_params.addWidget(widget, row_, 1)
                        # Build auto filler
                        bt_af = QPushButtonWthParam(tool=value, param=param, allow_real_time=False)
                        bt_af.setIcon(QIcon(":/common/resources/Lightning.png"))
                        bt_af.clicked.connect(self.on_grid_search_auto_fill_range)
                        bt_af.setToolTip("Autofill range")
                        self.gl_grid_search_params.addWidget(bt_af, row_, 2)
                        # Build rest
                        bt_reset = QPushButtonWthParam(
                            tool=value, param=param, allow_real_time=False
                        )
                        bt_reset.setIcon(QIcon(":/common/resources/Refresh.png"))
                        bt_reset.clicked.connect(self.on_grid_search_reset)
                        bt_reset.setToolTip("Reset to default value")
                        self.gl_grid_search_params.addWidget(bt_reset, row_, 3)

                    self.process_events()
                value.update_inputs(
                    update_values=self.build_param_overrides(
                        wrapper=self._src_image_wrapper, tool=value
                    )
                )

                # Update code browser
                self.update_tool_code()

            except Exception as e:
                self.log_exception(f"Failed to initialize tool: {repr(e)}")
            finally:
                self._updating_process_modes = False
            if not self._initializing and value.real_time and self._src_image_wrapper is not None:
                self.run_process(wrapper=self._src_image_wrapper, ipt=value)

    @property
    def selected_main_tab(self):
        return self.tabWidget.currentWidget().objectName()

    @selected_main_tab.setter
    def selected_main_tab(self, value):
        try:
            self.tabWidget.setCurrentWidget(self.tabWidget.findChild(QWidget, value))
        except TypeError as e:
            self.log_exception(f'Unable to select tab "{value}": {repr(e)}')
            self.tabWidget.setCurrentIndex(0)
        except AttributeError as e:
            self.log_exception(f'Unable to select tab "{value}": {repr(e)}')
            self.tabWidget.setCurrentIndex(0)

    @property
    def selected_run_tab(self):
        return self.tb_tool_script.currentWidget().objectName()

    @selected_run_tab.setter
    def selected_run_tab(self, value):
        try:
            self.tb_tool_script.setCurrentWidget(self.tb_tool_script.findChild(QWidget, value))
        except TypeError as e:
            self.log_exception(f'Unable to select tab "{value}": {repr(e)}')
            self.tb_tool_script.setCurrentIndex(0)
        except AttributeError as e:
            self.log_exception(f'Unable to select tab "{value}": {repr(e)}')
            self.tb_tool_script.setCurrentIndex(0)

    @property
    def script_generator(self):
        if self._script_generator is None:
            self._script_generator = IptStrictPipeline(use_cache=self.use_pipeline_cache)
        self._script_generator.image_output_path = self.static_folders["image_output"]
        self._script_generator.use_cache = self.use_pipeline_cache
        return self._script_generator

    @script_generator.setter
    def script_generator(self, value):
        self._script_generator = value
        self.tv_queued_tools.script_generator = value

    @property
    def pipeline(self) -> LoosePipeline:
        model = self.tv_pp_view.model()
        if model is not None:
            return model.pipeline
        else:
            return None

    @pipeline.setter
    def pipeline(self, value: LoosePipeline):
        self.tv_pp_view.setModel(
            PipelineModel(
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
                ),
                do_feedback=self.update_feedback,
            )
        )
        if value is not None:
            model = self.tv_pp_view.model()
            if model is not None:
                selectionModel = self.tv_pp_view.selectionModel()
                selectionModel.selectionChanged.connect(self.on_tv_pp_view_selection_changed)
                self.tv_pp_view.setItemDelegate(PipelineDelegate(parent=self.tv_pp_view))
            self.tv_pp_view.header().setStretchLastSection(False)
            self.tv_pp_view.header().setSectionResizeMode(0, QHeaderView.Stretch)
            self.tv_pp_view.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
            self.tv_pp_view.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
            self.tv_pp_view.setColumnWidth(1, 16)
            self.tv_pp_view.setColumnWidth(2, 16)

            index = model.createIndex(2, 0, model.rootNodes[2])
            self.tv_pp_view.selectionModel().selection().select(index, index)
            self.tv_pp_view.expand(index)

    @property
    def current_database(self):
        return self._current_database

    @current_database.setter
    def current_database(self, value):
        if value is None:
            self._current_database = None
            self.clear_exp_combo_box()
        else:
            reset_selection = (
                self._current_database is not None
                and self._current_database.db_file_name != value.db_file_name
            )
            changed_ = self._current_database != value
            self._current_database = value.copy()
            if changed_:
                if self._current_database is None:
                    self.update_feedback(
                        status_message="Not connected to a database or file system",
                        use_status_as_log=True,
                    )
                elif self._current_database.db_file_name:
                    self.update_feedback(
                        status_message=f"Connected to {self._current_database.db_file_name}",
                        use_status_as_log=True,
                    )
                else:
                    self.update_feedback(
                        status_message=f"Displaying contents of {self._current_database.src_files_path}",
                        use_status_as_log=True,
                    )
            self._updating_combo_boxes = True
            if not self._initializing:
                try:
                    self.set_enabled_database_controls(True)
                    if reset_selection:
                        self._current_exp = ""
                        self._current_plant = ""
                        self._current_date = dt.now().date()
                        self._current_time = dt.now().time()
                        self._current_camera = ""
                        self._current_view_option = ""
                    self.fill_exp_combo_box()
                    self.fill_plant_combo_box()
                    self.fill_date_combo_box()
                    self.fill_camera_combo_box()
                    self.fill_view_option_combo_box()
                    self.fill_time_combo_box()
                    self.file_name = self.current_selected_image_path()
                except Exception as e:
                    self.log_exception(f"Failed to select plant because: {repr(e)}")
                else:
                    pass
                finally:
                    self._updating_combo_boxes = False