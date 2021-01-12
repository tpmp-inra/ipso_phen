import os
from datetime import datetime as dt
from typing import Union
import logging

from PySide2.QtGui import QBrush, QColor, QIcon, QImage, QPalette, QPen, QPixmap
from PySide2.QtWidgets import (
    QApplication,
    QComboBox,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QGridLayout,
    QHeaderView,
    QItemDelegate,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QSpinBox,
    QStyle,
    QStyledItemDelegate,
    QTableView,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
    QGroupBox,
    QStyleOptionViewItem,
)
from PySide2.QtCore import QSize, QRect
from PySide2.QtCore import (
    QAbstractItemModel,
    QAbstractTableModel,
    QModelIndex,
    Qt,
    Signal,
)

from ipso_phen.ipapi.base.ipt_loose_pipeline import (
    GroupNode,
    ModuleNode,
    MosaicData,
    PipelineSettings,
)
from ipso_phen.ipapi.base.ipt_abstract import IptBase, IptParam, IptParamHolder
import ipso_phen.ipapi.base.ip_common as ipc
from ipso_phen.ui.qt_funct import build_widgets, cv2_to_qimage
import numpy as np
import pandas as pd
from ipso_phen.annotations.orm_annotations import OrmAnnotation, OrmAnnotationsDbWrapper
import cv2
from ipso_phen.ipapi.tools.regions import RectangleRegion

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))


class TreeNode(object):
    def __init__(self, node_data, parent, row, call_backs, do_feedback):
        self.parent = parent
        self.row = row
        self.call_backs = call_backs
        self.do_feedback = do_feedback
        self.widget_holder = None
        self.node_data = None
        self.children = []
        self.set_node_data(node_data)

    def set_node_data(self, new_data, **kwargs):
        raise NotImplementedError()

    def child(self, index: int):
        return self.children[index] if 0 <= index < len(self.children) else None

    def child_count(self):
        return len(self.children)

    def insert_children(self, row, data):
        raise NotImplementedError()

    def next_sibling(self):
        if self.parent is not None and (len(self.parent.children) > self.row):
            return self.parent.children[self.row + 1]
        else:
            return None

    def previous_sibling(self):
        if self.parent is not None and (self.row > 0):
            return self.parent.children[self.row - 1]
        else:
            return None

    def index(self):
        return 0 if self.parent is None else self.parent.index(self)


class PandasNode(TreeNode):
    def __init__(self, node_data, parent, row, call_backs, do_feedback):
        TreeNode.__init__(
            self,
            node_data=node_data,
            parent=parent,
            row=row,
            call_backs=call_backs,
            do_feedback=do_feedback,
        )

    def _getChildren(self):
        return None

    def set_node_data(self, new_data, **kwargs):
        try:
            self.node_data = new_data
        except Exception as e:
            logger.exception(f'Failed to process, because "{repr(e)}"')
            return False
        else:
            return True


class PipelineNode(TreeNode):
    def __init__(self, node_data, parent, row, call_backs, do_feedback):
        TreeNode.__init__(
            self,
            node_data=node_data,
            parent=parent,
            row=row,
            call_backs=call_backs,
            do_feedback=do_feedback,
        )

    def _getChildren(self):
        if isinstance(self.node_data, (str, tuple)):
            return []
        elif isinstance(self.node_data, dict) and "grid_search" in self.node_data:
            return [
                PipelineNode(
                    node_data=gizmo,
                    parent=self,
                    row=index + 1,
                    call_backs=self.call_backs,
                    do_feedback=self.do_feedback,
                )
                for index, gizmo in enumerate(self.node_data["grid_search"].tool.gizmos)
            ]
        elif isinstance(self.node_data, ModuleNode):
            tool_bar = [
                PipelineNode(
                    node_data={"name": "Grid search", "grid_search": self.node_data},
                    parent=self,
                    row=0,
                    call_backs=self.call_backs,
                    do_feedback=self.do_feedback,
                )
            ]
            widgets = [
                PipelineNode(
                    node_data=gizmo,
                    parent=self,
                    row=index + 1,
                    call_backs=self.call_backs,
                    do_feedback=self.do_feedback,
                )
                for index, gizmo in enumerate(self.node_data.tool.gizmos)
            ]
            return widgets + tool_bar
        elif isinstance(self.node_data, PipelineSettings):
            return [
                PipelineNode(
                    node_data=gizmo,
                    parent=self,
                    row=index,
                    call_backs=self.call_backs,
                    do_feedback=self.do_feedback,
                )
                for index, gizmo in enumerate(self.node_data.items())
            ]
        elif isinstance(self.node_data, IptParamHolder):
            return [
                PipelineNode(
                    node_data=gizmo,
                    parent=self,
                    row=index,
                    call_backs=self.call_backs,
                    do_feedback=self.do_feedback,
                )
                for index, gizmo in enumerate(self.node_data.gizmos)
            ]
        elif isinstance(self.node_data, IptParam):
            return []
        elif isinstance(self.node_data, GroupNode):
            if self.node_data.is_root:
                return [
                    PipelineNode(
                        node_data=node,
                        parent=self,
                        row=index + 1,
                        call_backs=self.call_backs,
                        do_feedback=self.do_feedback,
                    )
                    for index, node in enumerate(self.node_data.nodes)
                ]
            else:
                return [
                    PipelineNode(
                        node_data=node,
                        parent=self,
                        row=index + 1,
                        call_backs=self.call_backs,
                        do_feedback=self.do_feedback,
                    )
                    for index, node in enumerate(self.node_data.nodes)
                ]
        else:
            return []

    def set_node_data(self, new_data, **kwargs):
        try:
            self.node_data = new_data
            self.children = self._getChildren()
            if isinstance(new_data, IptParam):
                self.widget_holder = QWidget()
                layout = QHBoxLayout(self.widget_holder)
                layout.setContentsMargins(0, 0, 0, 0)
                nd = self.parent.node_data
                if isinstance(nd, ModuleNode):
                    tool = nd.tool
                elif isinstance(nd, PipelineSettings):
                    tool = nd
                elif isinstance(nd, dict):
                    tool = nd["grid_search"]
                else:
                    tool = None
                label, widget = build_widgets(
                    tool=tool,
                    param=new_data,
                    allow_real_time=not isinstance(tool, PipelineSettings),
                    do_feedback=self.do_feedback,
                    call_backs=self.call_backs,
                    grid_search_mode=isinstance(nd, dict),
                )
                if widget is not None:
                    layout.addWidget(widget)
                if label is not None:
                    layout.addWidget(label)
                if label and widget:
                    layout.setStretch(0, 2)
                    layout.setStretch(1, 3)
            elif isinstance(new_data, ModuleNode):
                run_call_back = self.call_backs.get("run_callback", None)
                self.run_button = QPushButton(
                    QIcon(":/image_process/resources/Play.png"), ""
                )
                self.run_button.setToolTip("Run to this module")
                self.run_button.setMinimumHeight(28)
                self.run_button.setIconSize(QSize(24, 24))
                if run_call_back is not None:
                    self.run_button.setEnabled(True)
                    self.run_button.module = new_data
                    self.run_button.clicked.connect(run_call_back)
                else:
                    self.run_button.setEnabled(False)
                self.reset_button = QPushButton(
                    QIcon(":/common/resources/Refresh.png"), ""
                )
                self.reset_button.setToolTip("Reset widgets to default values")
                self.reset_button.setMaximumWidth(200)
                self.reset_button.clicked.connect(self.on_reset_module)
            elif isinstance(new_data, dict) and "grid_search" in new_data:
                run_call_back = self.call_backs.get("run_grid_search_callback", None)
                self.run_button = QPushButton(
                    QIcon(":/image_process/resources/Play.png"), ""
                )
                self.run_button.setToolTip("Run to this module using grid search")
                self.run_button.setMinimumHeight(28)
                self.run_button.setIconSize(QSize(24, 24))
                if run_call_back is not None:
                    self.run_button.setEnabled(True)
                    self.run_button.module = new_data["grid_search"]
                    self.run_button.clicked.connect(run_call_back)
                else:
                    self.run_button.setEnabled(False)
            elif isinstance(new_data, MosaicData):
                self.widget_holder = QMosaicEditor(parent=None, data=new_data)
            elif isinstance(new_data, dict) and "widget" in new_data:
                self.widget_holder = new_data["widget"]
        except Exception as e:
            logger.exception(f'Failed to process, because "{repr(e)}"')
            return False
        else:
            return True

    def on_reset_module(self):
        self.node_data.tool.reset()
        self.node_data.root.invalidate(self.node_data)

    def insert_children(self, row, data):
        try:
            self.children.insert(
                row,
                PipelineNode(
                    node_data=data,
                    parent=self,
                    row=row,
                    call_backs=self.call_backs,
                    do_feedback=self.do_feedback,
                ),
            )
        except Exception as e:
            logger.exception(f'Failed to process, because "{repr(e)}"')
            return False
        else:
            return True

    def remove_children(self, index: int):
        try:
            node = self.children.pop(index)
            self.node_data.remove_node(node.node_data)
        except Exception as e:
            logger.exception(f'Failed to process, because "{repr(e)}"')
            return False
        else:
            return True

    def move_children(self, index: int, target_parent: object, target_index: int):
        try:
            node = self.children.pop(index)
            self.node_data.remove_node(index)
            target_parent.insert_children(target_index, node.node_data)
            # target_parent.node_data.insert_node(target_index, node.node_data)
            # target_parent.children.insert(target_index, node)
        except Exception as e:
            logger.exception(f'Failed to process, because "{repr(e)}"')
            return False
        else:
            return True

    @property
    def enabled(self):
        if isinstance(self.node_data, ModuleNode):
            return 2 if self.node_data.enabled != 0 else 0
        elif isinstance(self.node_data, GroupNode):
            return self.node_data.enabled
        else:
            return 2

    @enabled.setter
    def enabled(self, value):
        if hasattr(self.node_data, "enabled"):
            self.node_data.enabled = value


class QColorDelegate(QItemDelegate):
    def __init__(self, parent=None, *args, **kwargs):
        QItemDelegate.__init__(self, parent, *args)
        self._palette: QPalette = kwargs.get("palette")

    def paint(self, painter, option, index):
        try:
            painter.save()

            dataframe: pd.DataFrame = self.parent().model().dataframe
            # set background color
            is_error_column = "error" in dataframe.columns[index.column()]
            painter.setPen(QPen(Qt.NoPen))
            if is_error_column:
                try:
                    num_val = int(index.data(Qt.DisplayRole))
                    max_val = dataframe[dataframe.columns[index.column()]].max()
                except ValueError:
                    num_val = None
                    max_val = None
                if (num_val is not None) and (max_val is not None):
                    colors = ipc.build_color_steps(step_count=max_val + 1)
                    painter.setBrush(QBrush(QColor(*ipc.bgr_to_rgb(colors[num_val]))))
            else:
                if option.state & QStyle.State_Selected:
                    painter.setBrush(self._palette.highlight())
                else:
                    painter.setBrush(self._palette.window())
            painter.drawRect(option.rect)

            # set text color
            value = index.data(Qt.DisplayRole)
            if option.state & QStyle.State_Selected:
                painter.setPen(QPen(self._palette.color(QPalette.HighlightedText)))
            else:
                painter.setPen(QPen(self._palette.color(QPalette.Text)))
            painter.drawText(option.rect, Qt.AlignCenter, str(value))

            painter.restore()
            painter.end()
        except Exception as e:
            logger.exception(f"Failed to paint in {self.__class__.__name__}")

    def set_palette(self, new_palette):
        self._palette: QPalette = new_palette


class QImageDrawerDelegate(QItemDelegate):

    critical_base_color = QColor(200, 0, 0)
    error_base_color = QColor(200, 165, 0)
    warning_base_color = QColor(215, 215, 0)
    ok_base_color = QColor(0, 0, 200)
    info_base_color = QColor(200, 200, 255)
    source_issue_base_color = QColor(180, 180, 180)
    unknown_base_color = QColor(125, 125, 125)
    font_base_color = QColor(255, 255, 255)
    font_high_color = QColor(0, 0, 0)

    colors = {
        "critical": {
            "bgd": critical_base_color,
            "fnt": font_base_color,
            "s_bgd": critical_base_color.lighter(150),
            "s_fnt": font_high_color,
        },
        "error": {
            "bgd": error_base_color,
            "fnt": font_base_color,
            "s_bgd": error_base_color.lighter(150),
            "s_fnt": font_high_color,
        },
        "warning": {
            "bgd": warning_base_color,
            "fnt": font_base_color,
            "s_bgd": warning_base_color.lighter(150),
            "s_fnt": font_high_color,
        },
        "ok": {
            "bgd": ok_base_color,
            "fnt": font_base_color,
            "s_bgd": ok_base_color.lighter(150),
            "s_fnt": font_high_color,
        },
        "info": {
            "bgd": info_base_color,
            "fnt": font_base_color,
            "s_bgd": info_base_color.lighter(110),
            "s_fnt": font_high_color,
        },
        "source issue": {
            "bgd": source_issue_base_color,
            "fnt": font_base_color,
            "s_bgd": source_issue_base_color.lighter(120),
            "s_fnt": font_high_color,
        },
        "unknown": {
            "bgd": unknown_base_color,
            "fnt": font_base_color,
            "s_bgd": unknown_base_color.lighter(150),
            "s_fnt": font_high_color,
        },
    }

    def __init__(self, parent=None, *args, **kwargs):
        QItemDelegate.__init__(self, parent, *args)
        self.set_palette(kwargs.get("palette"))
        self._use_annotations = kwargs.get("use_annotations", True)
        self.annotations = {}

    def paint(self, painter, option, index):
        try:
            painter.save()

            # Try cache retrieval
            data = self.get_annotation(row_number=index.row())
            if data is not None:
                color_dict = self.colors.get(data["kind"].lower(), self._default_colors)
            else:
                color_dict = self._default_colors
            bg_color = color_dict[
                "s_bgd" if option.state & QStyle.State_Selected else "bgd"
            ]
            fg_color = color_dict[
                "s_fnt" if option.state & QStyle.State_Selected else "fnt"
            ]

            fnt = painter.font()
            fnt.setBold(option.state & QStyle.State_Selected)
            painter.setFont(fnt)

            # Draw
            painter.setPen(QPen(Qt.NoPen))
            painter.setBrush(QBrush(bg_color))
            painter.drawRect(option.rect)
            painter.setPen(QPen(fg_color))
            painter.drawText(
                option.rect,
                Qt.AlignVCenter | Qt.AlignCenter,
                str(index.data(Qt.DisplayRole)),
            )

            painter.restore()
        except Exception as e:
            logger.exception(f"Failed to paint in {self.__class__.__name__}")

    def get_annotation(self, **kwargs):
        if self.use_annotations is False:
            return None
        row_number = kwargs.get("row_number", None)
        if row_number is None:
            luid = kwargs.get("luid", None)
            experiment = kwargs.get("experiment", None)
        else:
            luid = self.parent().model().get_cell_data(row_number, "Luid")
            experiment = self.parent().model().get_cell_data(row_number, "Experiment")
        if experiment is None or luid is None:
            return None
        ret = self.annotations.get(luid, None)
        if ret is None:
            with OrmAnnotationsDbWrapper(experiment) as session_:
                data = (
                    session_.query(OrmAnnotation)
                    .filter(OrmAnnotation.idk == luid)
                    .first()
                )
                if data is not None:
                    ret = dict(
                        luid=data.idk,
                        kind=data.kind,
                        text=data.text,
                        auto_text=data.auto_text,
                    )
                else:
                    ret = None
            if ret is not None:
                self.annotations[luid] = ret
            else:
                self.annotations[luid] = "no_data"
        elif ret == "no_data":
            ret = None
        return ret

    def set_annotation(self, **kwargs):
        if self.use_annotations is False:
            return
        row_number = kwargs.get("row_number", None)
        if row_number is None:
            luid = kwargs.get("luid", None)
            experiment = kwargs.get("experiment", None)
        else:
            luid = self.parent().model().get_cell_data(row_number, "Luid")
            experiment = self.parent().model().get_cell_data(row_number, "Experiment")
        if experiment is None or luid is None:
            return None

        kind = kwargs.get("kind", "unknown")
        text = kwargs.get("text", "")
        auto_text = kwargs.get("auto_text", "")
        last_access = dt.now()

        with OrmAnnotationsDbWrapper(experiment) as session_:
            ann_ = session_.query(OrmAnnotation).filter(OrmAnnotation.idk == luid).first()
            if ann_ is not None:
                if not text and not auto_text:
                    session_.delete(ann_)
                    self.reset_cache(luid=luid)
                else:
                    ann_.kind = kind
                    ann_.text = text
                    ann_.auto_text = auto_text
                    ann_.last_access = last_access
                    self.annotations[luid] = dict(
                        luid=luid,
                        kind=ann_.kind,
                        text=ann_.text,
                        auto_text=ann_.auto_text,
                    )
            elif text or auto_text:
                session_.add(
                    OrmAnnotation(idk=luid, kind=kind, text=text, auto_text=auto_text)
                )
                self.annotations[luid] = dict(
                    luid=luid, kind=kind, text=text, auto_text=auto_text
                )

    def reset_cache(self, luid: str = ""):
        if not luid:
            self.annotations = {}
        else:
            self.annotations.pop(luid)

    def set_palette(self, new_palette):
        self._palette: QPalette = new_palette
        self._default_colors = {
            "bgd": self._palette.color(QPalette.Base),
            "fnt": self._palette.color(QPalette.Text),
            "s_bgd": self._palette.color(QPalette.Highlight),
            "s_fnt": self._palette.color(QPalette.HighlightedText),
        }

    @property
    def use_annotations(self):
        return self._use_annotations

    @use_annotations.setter
    def use_annotations(self, value):
        if self._use_annotations != value:
            self._use_annotations = value
            self.parent().model().layoutChanged.emit()


class PipelineDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, *args, **kwargs):
        QStyledItemDelegate.__init__(self, parent, *args)

    def paint(self, painter, option, index):
        try:
            if index.column() == 0:
                ip = index.internalPointer()
                if index.internalPointer().widget_holder is not None:
                    self.parent().setIndexWidget(
                        index,
                        index.internalPointer().widget_holder,
                    )
                elif isinstance(ip.node_data, (GroupNode, ModuleNode)):
                    option.palette.setColor(
                        QPalette.Text,
                        Qt.red
                        if ip is not None
                        and not ip.node_data.root.check_input(ip.node_data)
                        else painter.pen().color(),
                    )
                    option.font.setBold(isinstance(ip.node_data, GroupNode))
                    QStyledItemDelegate.paint(self, painter, option, index)
                else:
                    QStyledItemDelegate.paint(self, painter, option, index)
            elif index.column() == 1:
                node = index.internalPointer()
                if hasattr(node, "reset_button") and node.reset_button is not None:
                    self.parent().setIndexWidget(index, node.reset_button)
                else:
                    QStyledItemDelegate.paint(self, painter, option, index)
            elif index.column() == 2:
                node = index.internalPointer()
                if hasattr(node, "run_button") and node.run_button is not None:
                    self.parent().setIndexWidget(index, node.run_button)
                else:
                    QStyledItemDelegate.paint(self, painter, option, index)
        except Exception as e:
            logger.exception(f"Failed to paint in {self.__class__.__name__}")

    def createEditor(self, parent, option, index):
        nd = index.internalPointer().node_data
        if isinstance(nd, GroupNode) and index.column() == 0:
            # Create main widget
            widget = QWidget(parent)
            widget.setAutoFillBackground(True)
            vb_main = QVBoxLayout(widget)

            # Create main options widgets
            gb_main_options = QGroupBox(widget)
            gb_main_options.setTitle("Group settings")
            gl_main_options = QGridLayout(gb_main_options)

            gl_main_options.addWidget(QLabel("Name: ", gb_main_options), 0, 0, 1, 1)
            txt_group_name = QLineEdit(gb_main_options)
            txt_group_name.setEnabled(isinstance(nd.parent, GroupNode))
            txt_group_name.setObjectName("txt_group_name")
            gl_main_options.addWidget(txt_group_name, 0, 1, 1, 1)

            gl_main_options.addWidget(QLabel("Source: ", gb_main_options), 1, 0, 1, 1)
            cb_source = QComboBox(gb_main_options)
            cb_source.setObjectName("cb_source")
            cb_source.addItem("last_output", "last_output")
            cb_source.addItem("source", "source")
            model = self.parent().model()
            groups = model.as_pivot_list(index, allowed_classes=(GroupNode))
            previous_groups = groups.get("before", None)
            if len(previous_groups) > 0:
                for group in previous_groups[1:]:
                    nd = group.internalPointer().node_data
                    cb_source.addItem(nd.name, nd.uuid)
            gl_main_options.addWidget(cb_source, 1, 1, 1, 1)

            gl_main_options.addWidget(QLabel("Merge mode: ", gb_main_options), 2, 0, 1, 1)
            cb_merge_mode = QComboBox(gb_main_options)
            cb_merge_mode.setObjectName("cb_merge_mode")
            for merge_mode in [
                ipc.MERGE_MODE_AND,
                ipc.MERGE_MODE_OR,
                ipc.MERGE_MODE_CHAIN,
                ipc.MERGE_MODE_NONE,
            ]:
                cb_merge_mode.addItem(ipc.merge_mode_to_str(merge_mode), merge_mode)
            gl_main_options.addWidget(cb_merge_mode, 2, 1, 1, 1)

            vb_main.addWidget(gb_main_options)

            gb_filters = QGroupBox(widget)
            gb_filters.setTitle(
                "Filters: Select which plants this group will be applied to"
            )
            gl_filters = QGridLayout(gb_filters)
            for i, (k, _) in enumerate(nd.execute_filters.items()):
                gl_filters.addWidget(QLabel(k), i, 0, 1, 1)
                w = QLineEdit(gb_main_options)
                w.setObjectName(k)
                gl_filters.addWidget(w, i, 1, 1, 1)
            vb_main.addWidget(gb_filters)

            return widget
        elif isinstance(nd, tuple) and index.column() == 0:
            txt_pipeline_description = QLineEdit(parent)
            txt_pipeline_description.setObjectName("txt_pipeline_description")
            return txt_pipeline_description
        else:
            return QStyledItemDelegate.createEditor(self, parent, option, index)

    def updateEditorGeometry(
        self, editor: QWidget, option: QStyleOptionViewItem, index: QModelIndex
    ):
        nd = index.internalPointer().node_data
        r: QRect = option.rect
        if isinstance(nd, GroupNode) and index.column() == 0 and not nd.is_root:
            r.setHeight(editor.sizeHint().height())
        editor.setGeometry(r)

    def setEditorData(self, editor, index):
        nd = index.internalPointer().node_data
        if index.column() == 0 and isinstance(nd, GroupNode):
            txt_group_name: QLineEdit = editor.findChild(QLineEdit, "txt_group_name")
            if txt_group_name is not None:
                txt_group_name.setText(nd.name)

            cb_merge_mode: QComboBox = editor.findChild(QComboBox, "cb_merge_mode")
            if cb_merge_mode is not None:
                cb_merge_mode.setCurrentIndex(cb_merge_mode.findData(nd.merge_mode))

            cb_source: QComboBox = editor.findChild(QComboBox, "cb_source")
            if cb_source is not None:
                cb_source.setCurrentIndex(cb_source.findData(nd.source))

            for k, v in nd.execute_filters.items():
                txt_edt: QLineEdit = editor.findChild(QLineEdit, k)
                if txt_edt is not None:
                    txt_edt.setText(v)
        elif isinstance(nd, tuple) and index.column() == 0:
            if editor is not None:
                editor.setText(nd[1])
        else:
            return QStyledItemDelegate.setEditorData(self, editor, index)

    def setModelData(self, editor, model, index):
        nd = index.internalPointer().node_data
        if index.column() == 0 and isinstance(nd, GroupNode):
            value = {}

            txt_group_name: QLineEdit = editor.findChild(QLineEdit, "txt_group_name")
            if txt_group_name is not None and txt_group_name.isEnabled():
                value["name"] = txt_group_name.text()

            cb_merge_mode: QComboBox = editor.findChild(QComboBox, "cb_merge_mode")
            if cb_merge_mode is not None and cb_merge_mode.isEnabled():
                value["merge_mode"] = cb_merge_mode.currentData()

            cb_source: QComboBox = editor.findChild(QComboBox, "cb_source")
            if cb_source is not None and cb_source.isEnabled():
                value["source"] = cb_source.currentData()

            for k, v in nd.execute_filters.items():
                txt_edt: QLineEdit = editor.findChild(QLineEdit, k)
                if txt_edt is not None:
                    value[k] = txt_edt.text()

            model.setData(index, value, Qt.UserRole)
        else:
            return QStyledItemDelegate.setModelData(self, editor, model, index)


class MosaicDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, *args, **kwargs):
        QStyledItemDelegate.__init__(self, parent, *args)
        self.pipeline = kwargs["pipeline"]

    def paint(self, painter, option, index):
        try:
            QStyledItemDelegate.paint(self, painter, option, index)
        except Exception as e:
            logger.exception(f"Failed to paint in {self.__class__.__name__}")

    def createEditor(self, parent, option, index):
        cb = QComboBox(parent=parent)
        cb.view().setMinimumWidth(240)
        cb.addItems(
            [node.name for node in self.pipeline.root.iter_items()]
            + [
                "source",
                "current_image",
                "mask",
                "exp_fixed",
                "mask_on_exp_fixed_bw_with_morph",
                "mask_on_exp_fixed_bw",
                "mask_on_exp_fixed_bw_roi",
                "exp_fixed_roi",
                "exp_fixed_pseudo_on_bw",
            ]
        )
        cb.setObjectName("cb_select_image")
        return cb

    def setEditorData(self, editor, index):
        if editor is not None:
            editor.setCurrentIndex(editor.findText(str(index.data(Qt.DisplayRole))))

    def setModelData(self, editor, model, index):
        if editor is not None:
            model.setData(index, editor.currentText(), Qt.UserRole)


class QPandasModel(QAbstractTableModel):
    def __init__(self, data):
        QAbstractTableModel.__init__(self)
        self._df = data

    def rowCount(self, parent=None):
        return 0 if self._df is None else self._df.shape[0]

    def columnCount(self, parnet=None):
        return 0 if self._df is None else self._df.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid() and (self._df is not None):
            if role == Qt.DisplayRole:
                return str(self._df.iloc[index.row(), index.column()])
            elif role == Qt.ToolTipRole:
                return str(self._df.iloc[index.row(), index.column()])
        return None

    def sort(self, column: int, order=Qt.AscendingOrder):
        if self._df is None:
            return
        self.layoutAboutToBeChanged.emit()
        sort_columns = [self._df.columns[column]]
        if ("date_time" in self._df.columns) and ("date_time" not in sort_columns):
            sort_columns.append("date_time")
        self._df.sort_values(
            by=sort_columns,
            inplace=True,
            ascending=order == Qt.AscendingOrder,
            na_position="first",
        )
        self.layoutChanged.emit()

    def setData(self, index, value, role):
        if (self._df is None) or not index.isValid() or (role != Qt.EditRole):
            return False
        row = index.row()
        if row < 0 or row >= len(self._df.values):
            return False
        column = index.column()
        if column < 0 or column >= self._df.columns.size:
            return False
        dt = self._df.iloc[:, column].dtypes
        if dt in [np.int64, np.int32, np.int16]:
            try:
                val = int(value)
            except ValueError:
                return False
        elif dt in [np.float64, np.float32, np.float16]:
            try:
                val = float(value)
            except ValueError:
                return False
        else:
            val = value
        self._df.iloc[[row], [column]] = val
        self.dataChanged.emit(index, index)
        return True

    def headerData(self, col, orientation, role):
        if (
            (self._df is not None)
            and (orientation == Qt.Horizontal)
            and (role == Qt.DisplayRole)
        ):
            return self._df.columns[col]
        return None

    def flags(self, index):
        flags = super(self.__class__, self).flags(index)
        flags |= Qt.ItemIsEditable
        flags |= Qt.ItemIsSelectable
        flags |= Qt.ItemIsEnabled
        flags |= Qt.ItemIsDragEnabled
        flags |= Qt.ItemIsDropEnabled
        return flags

    @property
    def dataframe(self):
        return self._df


class QPandasColumnsModel(QAbstractTableModel):
    def __init__(self, data):
        QAbstractTableModel.__init__(self)
        self._df = data

    def rowCount(self, parent=None):
        return 0 if self._df is None else len(list(self._df.columns))

    def columnCount(self, parnet=None):
        return 2

    def data(self, index, role=Qt.DisplayRole):
        if (
            index.isValid()
            and (self._df is not None)
            and (role == Qt.DisplayRole)
            or (role == Qt.ToolTipRole)
        ):
            if index.column() == 0:
                return self._df.columns[index.row()]
            elif index.column() == 1:
                return str(self._df[self._df.columns[index.row()]].dtypes)
        return None

    def headerData(self, col, orientation, role):
        if (
            (self._df is not None)
            and (orientation == Qt.Horizontal)
            and (role == Qt.DisplayRole)
        ):
            if col == 0:
                return "Name"
            elif col == 1:
                return "Type"
        return None

    def flags(self, index):
        flags = super(self.__class__, self).flags(index)
        flags |= Qt.ItemIsSelectable
        flags |= Qt.ItemIsEnabled
        return flags

    @property
    def dataframe(self):
        return self._df


class QImageDatabaseModel(QAbstractTableModel):
    def __init__(self, dataframe, **kwargs):
        QAbstractTableModel.__init__(self)
        self.images = dataframe
        self.annotations = {}
        self.group_by = []

    def rowCount(self, parent=None):
        return 0 if self.images is None else self.images.shape[0]

    def columnCount(self, parnet=None):
        return 0 if self.images is None else self.images.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid() and (self.images is not None):
            if role == Qt.DisplayRole:
                return str(self.images.iloc[index.row(), index.column()])
            elif role == Qt.ToolTipRole:
                return str(self.images.iloc[index.row(), index.column()])
        return None

    def headerData(self, col, orientation, role):
        if (self.images is not None) and (role == Qt.DisplayRole):
            if orientation == Qt.Horizontal:
                return self.images.columns[col]
            elif orientation == Qt.Vertical:
                return str(col)
        return None

    def flags(self, index):
        flags = super(self.__class__, self).flags(index)
        flags |= Qt.ItemIsSelectable
        flags |= Qt.ItemIsEnabled
        return flags

    def sort(self, column: int, order=Qt.AscendingOrder):
        if self.images is None:
            return
        self.layoutAboutToBeChanged.emit()
        sort_columns = [self.images.columns[column]]
        if ("date_time" in self.images.columns) and ("date_time" not in sort_columns):
            sort_columns.append("date_time")
        self.images.sort_values(
            by=sort_columns,
            inplace=True,
            ascending=order == Qt.AscendingOrder,
            na_position="first",
        )
        self.layoutChanged.emit()

    def set_images(self, dataframe):
        self.images = dataframe
        self.modelReset.emit()

    def append_images(self, dataframe):
        self.columnsInserted.emit(0, 0)

    def remove_images(self, luis: list = []):
        self.modelReset.emit()

    def clear_images(self):
        self.images.drop(self.images.index, inplace=True)
        self.modelReset.emit()

    def get_column_index_from_name(self, column_name):
        if self.images is None:
            return -1
        return self.images.columns.get_loc(column_name)

    def get_cell_data(self, row_number: int, column_name: str):
        col = self.get_column_index_from_name(column_name=column_name)
        if col < 0:
            return None
        return self.images.iloc[row_number, col]


class TreeModel(QAbstractItemModel):
    def __init__(self):
        QAbstractItemModel.__init__(self)
        self.rootNodes = self._getRootNodes()

    def _getRootNodes(self):
        raise NotImplementedError()

    def index(self, row, column, parent):
        if not parent.isValid():
            return self.createIndex(row, column, self.rootNodes[row])
        parentNode = parent.internalPointer()
        if 0 <= row < len(parentNode.children):
            return self.createIndex(row, column, parentNode.children[row])
        else:
            return QModelIndex()

    def get_item(self, index: QModelIndex) -> TreeNode:
        return (
            index.internalPointer()
            if index.isValid()
            else QModelIndex().internalPointer()
        )

    def parent(self, index):
        node = self.get_item(index)
        if not hasattr(node, "parent"):
            raise ValueError()
        elif node.parent is None:
            return QModelIndex()
        else:
            return self.createIndex(node.parent.row, 0, node.parent)

    def reset(self):
        self.rootNodes = self._getRootNodes()
        super().reset(self)

    def iter_items(self, root, allowed_classes: Union[None, tuple] = None):
        if root is None:
            stack = [
                self.createIndex(0, 0, self.rootNodes[i])
                for i in range(len(self.rootNodes))
            ]
        else:
            stack = [root]

        def parse_children_(parent):
            for row in range(self.rowCount(parent)):
                child = parent.child(row, 0)
                if not allowed_classes or isinstance(
                    child.internalPointer().node_data, allowed_classes
                ):
                    yield child
                if self.rowCount(child) > 0:
                    yield from parse_children_(child)

        for root in stack:
            if not allowed_classes or isinstance(
                root.internalPointer().node_data, allowed_classes
            ):
                yield root
            yield from parse_children_(root)

    def as_pivot_list(self, index, allowed_classes) -> dict:
        """Splits all nodes in three classes
        * before: all nodes before index
        * pivot: index
        * after: all nodes after index
        """
        item = self.get_item(index)
        matched_uuid = False
        item_uuid = item.node_data.uuid
        nodes = [node for node in self.iter_items(None, allowed_classes)]
        res = {
            "before": [],
            "pivot": index,
            "after": [],
        }
        for node in nodes:
            nd = self.get_item(node)
            if nd.node_data.uuid == item_uuid:
                matched_uuid = True
                continue
            if matched_uuid:
                res["after"].append(node)
            else:
                res["before"].append(node)
        return res


class PipelineModel(TreeModel):
    def __init__(self, pipeline, call_backs, do_feedback):
        self.pipeline = pipeline
        self.call_backs = call_backs
        self.do_feedback = do_feedback
        TreeModel.__init__(self)

    def _getRootNodes(self):
        return [
            PipelineNode(
                node_data=("Description:", self.pipeline.description),
                parent=None,
                row=0,
                call_backs=self.call_backs,
                do_feedback=self.do_feedback,
            ),
            PipelineNode(
                node_data=self.pipeline.settings,
                parent=None,
                row=1,
                call_backs=self.call_backs,
                do_feedback=self.do_feedback,
            ),
            PipelineNode(
                node_data=self.pipeline.root,
                parent=None,
                row=2,
                call_backs=self.call_backs,
                do_feedback=self.do_feedback,
            ),
        ]

    def rowCount(self, parent):
        data: TreeNode = parent.internalPointer()
        return 3 if data is None else data.child_count()

    def columnCount(self, parent):
        return 3

    def data(self, index, role):
        if index.column() == 0:
            node = self.get_item(index)
            if role == Qt.DisplayRole:
                nd = node.node_data
                if isinstance(nd, str):
                    return nd
                elif isinstance(nd, tuple):
                    return "\n".join(nd)
                elif isinstance(nd, PipelineSettings):
                    return "Settings"
                elif isinstance(nd, IptBase):
                    return nd.name
                elif isinstance(nd, IptParam):
                    return None  # str(nd)
                elif isinstance(nd, GroupNode):
                    merge = ipc.merge_mode_to_str(nd.merge_mode)
                    src_group = nd.root.find_by_uuid(nd.source)
                    source = nd.source if src_group is None else src_group.name
                    in_t = ipc.io_type_to_str(nd.input_type)
                    out = ipc.io_type_to_str(nd.output_type)
                    return f"{nd.name}, src: {source}, merge: {merge} - ({in_t} -> {out})"
                elif isinstance(nd, ModuleNode):
                    in_t = ipc.io_type_to_str(nd.input_type)
                    out = ipc.io_type_to_str(nd.output_type)
                    return f"{nd.name}, {in_t} -> {out}"
                elif isinstance(nd, dict) and "name" in nd.keys():
                    return nd["name"]
                else:
                    return "no data"
            elif role == Qt.ToolTipRole:
                nd = node.node_data
                if isinstance(nd, str):
                    return f"{nd}\n\nDouble click to edit."
                elif isinstance(nd, tuple):
                    return f"{nd}\n\nDouble click to edit."
                elif isinstance(nd, PipelineSettings):
                    return "Settings: Set pipeline behavior"
                elif isinstance(nd, IptBase):
                    return nd.hint
                elif isinstance(nd, IptParam):
                    return nd.hint
                elif isinstance(nd, GroupNode):
                    in_t = ipc.io_type_to_str(nd.input_type)
                    out = ipc.io_type_to_str(nd.output_type)
                    merge = ipc.merge_mode_to_str(nd.merge_mode)
                    src_group = nd.root.find_by_uuid(nd.source)
                    source = nd.source if src_group is None else src_group.name
                    return f"{nd.name}\nsrc: {source}\n{in_t} ->{out}\nmerge: {merge}\nDouble click to edit"
                elif isinstance(nd, ModuleNode):
                    return nd.tool.hint
                elif (
                    isinstance(nd, dict)
                    and "name" in nd.keys()
                    and nd["name"] == "Grid search"
                ):
                    return "\n".join(
                        [
                            "Grid search:",
                            "Perform an exhaustive test within the selected params",
                            "- Single values will generate one value",
                            "- Comma separated values will generate a value for each combination",
                            "- To explore a range write the first and las values separated by '|' then a ';' and finally the step value.",
                            "  For example '0|30;10' will generate 'O,10,20,30'",
                            "One output will be generated for every possible combination.",
                        ]
                    )
                elif isinstance(nd, dict) and "name" in nd.keys():
                    return nd["name"]
                else:
                    return "no data"
            elif role == Qt.CheckStateRole:
                nd = node.node_data
                if node.parent is not None and (
                    isinstance(nd, ModuleNode) or isinstance(nd, GroupNode)
                ):
                    return node.enabled
                elif isinstance(nd, dict) and "checked" in nd:
                    return nd["checked"]
            else:
                return None
        return None

    def setData(self, index, value, role=Qt.EditRole):
        if index.column() == 0:
            if role == Qt.CheckStateRole:
                item = self.get_item(index)
                if isinstance(item.node_data, (GroupNode, ModuleNode)):
                    item.enabled = value
                    item.node_data.root.invalidate(item.node_data)
                    self.dataChanged.emit(index, index)
                elif isinstance(item.node_data, dict) and "checked" in item.node_data:
                    item.node_data["checked"] = value
                    item.parent.parent.node_data.grid_search_mode = value
                    self.dataChanged.emit(
                        index.parent().parent(), index.parent().parent()
                    )
                self.layoutChanged.emit()
                return True
            elif role == Qt.EditRole:
                item = self.get_item(index)
                if isinstance(item.node_data, GroupNode):
                    if isinstance(value, str):
                        item.node_data.name = value
                    elif isinstance(value, GroupNode):
                        item.set_node_data(value)
                elif isinstance(item.node_data, tuple):
                    if isinstance(value, str):
                        self.pipeline.description = value
                        item.set_node_data(("Description:", value))
                self.layoutChanged.emit()
                return True
            elif role == Qt.UserRole:
                item = self.get_item(index)
                nd = item.node_data
                if isinstance(nd, GroupNode) and isinstance(value, dict):
                    nd.name = value.pop("name", nd.name)
                    nd.merge_mode = value.pop("merge_mode", nd.merge_mode)
                    nd.source = value.pop("source", nd.source)
                    nd.execute_filters = value

                    self.dataChanged.emit(index, index)
                    return True

        return super(TreeModel, self).setData(index, value, role)

    def get_parent_group_node(self, selected_items, allow_wandering: bool = False):
        if isinstance(selected_items, QModelIndex):
            return selected_items
        elif isinstance(selected_items, list) and selected_items:
            root = selected_items[0]
            parent = root.parent()
            if parent is None:
                return self.createIndex(1, 0, self.rootNodes[2])
            else:
                nd = root.internalPointer().node_data
                while not isinstance(nd, GroupNode):
                    root = root.parent()
                    if root is None or root.internalPointer() is None:
                        return self.createIndex(1, 0, self.rootNodes[2])
                    nd = root.internalPointer().node_data
                return root
        else:
            return self.createIndex(1, 0, self.rootNodes[2])

    def add_module(self, selected_items, module: IptBase, enabled: bool):
        root = self.get_parent_group_node(selected_items=selected_items)
        if root is not None:
            node: PipelineNode = root.internalPointer()
            nd = node.node_data
            insert_index = nd.node_count
            self.insertRow(insert_index, root)
            added_index = self.index(insert_index, 0, root)
            self.get_item(added_index).set_node_data(
                nd.add_module(tool=module, enabled=enabled), call_backs=self.call_backs
            )
            self.dataChanged.emit(root, root)
            self.layoutChanged.emit()
            return added_index

    def add_group(
        self, selected_items, merge_mode: str = ipc.MERGE_MODE_CHAIN, name: str = ""
    ):
        root = self.get_parent_group_node(selected_items=selected_items)
        if root is not None:
            node: PipelineNode = root.internalPointer()
            nd = node.node_data
            insert_index = nd.node_count
            self.insertRow(insert_index, root)
            added_index = self.index(insert_index, 0, root)
            self.get_item(added_index).set_node_data(
                nd.add_group(merge_mode=merge_mode, name=name)
            )
            return added_index

    def insertRows(self, row, count, parent=QModelIndex()):
        self.beginInsertRows(parent, row, row + count - 1)
        res = True
        for _ in range(count):
            res = parent.internalPointer().insert_children(row=row, data=None) and res
        self.endInsertRows()
        return res

    def removeRows(self, row, count, parent):
        self.beginRemoveRows(parent, row, row + count - 1)
        res = True
        for _ in range(count):
            res = parent.internalPointer().remove_children(row) and res
        self.endRemoveRows()
        # self.layoutChanged.emit()
        return res

    def move_row(
        self, selected_items, target_index: int, target_parent: QModelIndex = None
    ):
        if len(selected_items) != 1:
            return False
        root = selected_items[0]
        self.beginMoveRows(
            root.parent(), root.row(), root.row(), target_parent, target_index
        )
        self.moveRow(root.parent(), root.row(), target_parent, target_index)
        self.endMoveRows()
        # nd = root.internalPointer().node_data
        # if not (isinstance(nd, ModuleNode) or isinstance(nd, GroupNode)):
        #     return False
        # parent: PipelineNode = root.parent().internalPointer()
        # target_parent_node: PipelineNode = target_parent.internalPointer()
        # self.beginMoveRows(root.parent(), root.row(), root.row(), target_parent, target_index)
        # parent.move_children(
        #     index=root.row(), target_parent=target_parent_node, target_index=target_index
        # )
        # self.endMoveRows()
        self.layoutChanged.emit()

    def move_down(self, selected_items):
        if len(selected_items) != 1:
            return False
        root = selected_items[0]
        self.move_row(
            selected_items=selected_items,
            target_index=root.row() + 1,
            target_parent=root.parent(),
        )

    def move_up(self, selected_items):
        if len(selected_items) != 1:
            return False
        root = selected_items[0]
        self.move_row(
            selected_items=selected_items,
            target_index=root.row() - 1,
            target_parent=root.parent(),
        )

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole and section == 0:
            return f"Pipeline: {self.pipeline.name}"
        return None

    def invalidate(self):
        self.layoutChanged.emit()

    def flags(self, index):
        flags = super(self.__class__, self).flags(index)
        flags |= Qt.ItemIsSelectable
        flags |= Qt.ItemIsEnabled
        flags |= Qt.ItemIsUserCheckable
        if index.column() == 0:
            nd = self.get_item(index).node_data
            if isinstance(nd, (str, tuple)):
                flags |= Qt.ItemIsEditable
            if isinstance(nd, GroupNode) and not nd.is_root:
                flags |= Qt.ItemIsEditable
            if isinstance(nd, (ModuleNode, GroupNode)):
                flags |= Qt.ItemIsUserCheckable
                if isinstance(nd, GroupNode):
                    flags |= Qt.ItemIsTristate
            if isinstance(nd, dict) and "widget" not in nd:
                flags |= Qt.ItemIsUserCheckable
        return flags


class MosaicModel(QPandasModel):
    def __init__(self, pipeline, *kwargs):
        self.pipeline = pipeline
        self._is_changing = False
        QPandasModel.__init__(self, self.from_pipeline(pipeline))

    def setData(self, index, value, role=Qt.EditRole):
        if (self._df is None) or not index.isValid() or (role != Qt.UserRole):
            return False
        self._df.iloc[[index.row()], [index.column()]] = value
        self._update_model()
        self.dataChanged.emit(index, index)
        return True

    def _update_model(self):
        self.pipeline.settings.mosaic.images = self.to_list()

    def from_pipeline(self, pipeline):
        lst = self.pipeline.settings.mosaic.images
        if not lst:
            return pd.DataFrame([], columns=[])
        else:
            return pd.DataFrame(lst, columns=[i for i in range(len(lst[0]))])

    def to_list(self):
        return self.dataframe.values.tolist()

    def to_string(self):
        return "\n".join([",".join(i) for i in self.to_list()])

    def set_row_count(self, row_count):
        if row_count > self.rowCount():
            self.insertRows(self.rowCount(), row_count - self.rowCount())
        elif row_count < self.rowCount() and self.rowCount() >= 0:
            self.removeRows(self.rowCount() - 1, self.rowCount() - row_count)
        else:
            pass

    def insertRows(self, row, count, parent=QModelIndex()):
        self.beginInsertRows(parent, row, row + count - 1)
        new_df = pd.DataFrame(
            [["source" for _ in range(self.columnCount())] for _ in range(count)],
            columns=[i for i in range(self.columnCount())],
        )
        self._df = self.dataframe.append(new_df).reset_index(drop=True)
        self._update_model()
        self.endInsertRows()
        return True

    def removeRows(self, row, count, parent=QModelIndex()):
        self.beginRemoveRows(parent, row, row + count - 1)
        for _ in range(count):
            self._df = self._df.drop(self._df.index[-1]).reset_index(drop=True)
        self._update_model()
        self.endRemoveRows()
        return True

    def set_column_count(self, column_count):
        if column_count > self.columnCount():
            self.insertColumns(self.columnCount(), column_count - self.columnCount())
        elif column_count < self.columnCount():
            self.removeColumns(self.columnCount() - 1, self.columnCount() - column_count)
        else:
            pass

    def insertColumns(self, column, count, parent=QModelIndex()):
        self.beginInsertColumns(parent, column, column + count - 1)
        for i in range(column, column + count):
            self._df[i] = "source"
        self._update_model()
        self.endInsertColumns()
        return True

    def removeColumns(self, column, count, parent=QModelIndex()):
        self.beginRemoveColumns(parent, column, column + count - 1)
        for _ in range(count):
            self._df = self._df.drop(column, axis=1)
        self._update_model()
        self.endRemoveColumns()
        return True

    def flags(self, index):
        flags = QAbstractTableModel.flags(self, index)
        flags |= Qt.ItemIsEnabled
        flags |= Qt.ItemIsEditable
        flags |= Qt.ItemIsSelectable
        return flags


class CTreeWidgetItem(QTreeWidgetItem):
    def setData(self, column, role, value):
        state = self.checkState(column)
        QTreeWidgetItem.setData(self, column, role, value)
        if (role == Qt.CheckStateRole) and (state != self.checkState(column)):
            tree_widget = self.treeWidget()
            if tree_widget is not None:
                tree_widget.itemChecked.emit(self, column)


class CTreeWidget(QTreeWidget):
    itemChecked = Signal(object, int)

    def __init__(self):
        QTreeWidget.__init__(self)
        self.itemChecked.connect(self.handle_item_checked)
        self.initializing_tree = False
        self.script_generator = None

    def handle_item_checked(self, item, column):
        if not self.initializing_tree and (self.script_generator is not None):
            data = item.data(0, Qt.UserRole)
            if data is not None:
                self.script_generator.toggle_enabled_state(key=data)


class QMouseGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super(QMouseGraphicsView, self).__init__(parent)
        self.auto_fit = True

        self.setScene(QGraphicsScene())
        self.zoom_in_factor = 1.1
        self.zoom_out_factor = 0.9
        self._main_image = None

        # self.setDragMode(QGraphicsView.ScrollHandDrag)

    def wheelEvent(self, event):
        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.ControlModifier:
            self.auto_fit = False

            # Set Anchors
            self.setTransformationAnchor(QGraphicsView.NoAnchor)
            self.setResizeAnchor(QGraphicsView.NoAnchor)

            # Save the scene pos
            oldPos = self.mapToScene(event.pos())

            # Zoom
            if event.angleDelta().y() > 0:
                zoomFactor = self.zoom_in_factor
            else:
                zoomFactor = self.zoom_out_factor
            self.scale(zoomFactor, zoomFactor)

            # Get the new position
            newPos = self.mapToScene(event.pos())

            # Move scene to old position
            delta = newPos - oldPos
            self.translate(delta.x(), delta.y())
        else:
            super(QMouseGraphicsView, self).wheelEvent(event)

    def resizeEvent(self, event):
        if self.auto_fit:
            self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)
        else:
            super(QMouseGraphicsView, self).resizeEvent(event)

    def mouseDoubleClickEvent(self, event):
        self.fit_to_canvas()

    def mousePressEvent(self, event):
        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.ControlModifier:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
        super(QMouseGraphicsView, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.setDragMode(QGraphicsView.NoDrag)
        super(QMouseGraphicsView, self).mouseReleaseEvent(event)

    def fit_to_canvas(self):
        self.auto_fit = True
        self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)

    def zoom_by_factor(self, factor):
        self.auto_fit = False
        self.scale(factor, factor)

    def zoom_in(self):
        self.zoom_by_factor(self.zoom_in_factor)

    def zoom_out(self):
        self.zoom_by_factor(self.zoom_out_factor)

    @property
    def main_image(self):
        return self._main_image

    @main_image.setter
    def main_image(self, value):
        if self._main_image is not None:
            self.scene().removeItem(self._main_image)
            self._main_image = None
        if value is not None:
            if isinstance(value, str):
                q_pix = QPixmap(value)
            elif isinstance(value, tuple):
                images = value[0]
                color = value[1].blue(), value[1].green(), value[1].red()
                i = cv2.imread(filename=images[0])
                w = i.shape[1]
                shape = (i.shape[0], (i.shape[1] + 2) * len(images), i.shape[2])
                canvas = np.full(shape, color, np.uint8)
                for c, image_path in enumerate(images):
                    i = cv2.imread(filename=image_path)
                    if i is None:
                        continue
                    r = RectangleRegion(
                        left=int((shape[1] / len(images)) * c),
                        width=w,
                        top=0,
                        height=shape[0],
                    )
                    canvas = ipc.enclose_image(canvas, i, r)
                q_pix = cv2_to_qimage(canvas)
            else:
                q_pix = cv2_to_qimage(value)
            self._main_image = self.scene().addPixmap(q_pix)
            self.setSceneRect(self._main_image.boundingRect())
            self.fit_to_canvas()


class QMosaicEditor(QGroupBox):
    def __init__(self, parent, data):
        super().__init__(parent)

        self.data = data

        self.setCheckable(True)
        self.setChecked(data.enabled)
        self.setTitle("Enable mosaic")
        self.toggled.connect(self.on_toggled)

        self.table = QTableView(self)
        self.table.setModel(MosaicModel(data.pipeline))
        self.table.setItemDelegate(MosaicDelegate(pipeline=data.pipeline))
        self.table.horizontalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.sb_row_count = QSpinBox(self)
        self.sb_row_count.setMinimum(1)
        self.sb_row_count.setMaximum(20)
        self.sb_row_count.setValue(self.table.model().rowCount())
        self.sb_row_count.valueChanged.connect(self.on_sb_row_count_changed)

        self.sb_column_count = QSpinBox(self)
        self.sb_column_count.setMinimum(1)
        self.sb_column_count.setMaximum(20)
        self.sb_column_count.setValue(self.table.model().columnCount())
        self.sb_column_count.valueChanged.connect(self.on_sb_column_count_changed)

        hl = QHBoxLayout()
        hl.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        hl.addWidget(QLabel("Row count", self))
        hl.addWidget(self.sb_row_count)
        hl.addWidget(QLabel("Column count", self))
        hl.addWidget(self.sb_column_count)

        vl = QVBoxLayout(self)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.addLayout(hl)
        vl.addWidget(self.table)

    def on_toggled(self, on):
        self.data.enabled = on
        self.table.setEnabled(on)
        self.sb_row_count.setEnabled(on)
        self.sb_column_count.setEnabled(on)

    def on_sb_row_count_changed(self):
        self.table.model().set_row_count(self.sb_row_count.value())

    def on_sb_column_count_changed(self):
        self.table.model().set_column_count(self.sb_column_count.value())
