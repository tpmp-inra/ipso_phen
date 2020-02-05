import os
from datetime import datetime as dt

import numpy as np
import pandas as pd

import cv2

from PyQt5.QtCore import Qt, pyqtSignal, QAbstractTableModel, QAbstractItemModel, QModelIndex

from PyQt5.QtWidgets import (
    QCheckBox,
    QSlider,
    QComboBox,
    QLabel,
    QPushButton,
    QLineEdit,
    QTreeWidgetItem,
    QTreeWidget,
    QTextBrowser,
    QSpinBox,
    QApplication,
    QGraphicsView,
    QGraphicsScene,
    QFileDialog,
    QTableView,
    QItemDelegate,
    QStyledItemDelegate,
    QStyle,
    QWidget,
    QHBoxLayout,
    QTableWidget,
    QHeaderView,
    QTextEdit,
)
from PyQt5.QtGui import QImage, QPixmap, QBrush, QPen, QPalette, QColor

from ip_base import ip_common as ipc
from ip_base.ipt_loose_pipeline import LoosePipeline, GroupNode, ModuleNode, PipelineSettings
from ip_base.ipt_abstract import IptParam, IptParamHolder, IptBase
from annotations.orm_annotations import OrmAnnotation, OrmAnnotationsDbWrapper
from tools.regions import RectangleRegion


def scale(val, src, dst):
    return int(((val - src[0]) / float(src[1] - src[0])) * (dst[1] - dst[0]) + dst[0])


def cv2_to_qimage(img):
    qformat = QImage.Format_Indexed8
    if len(img.shape) == 3:
        if img.shape[2] == 4:
            qformat = QImage.Format_RGBA8888
        else:
            qformat = QImage.Format_RGB888
        height_, width_, *_ = img.shape
    elif len(img.shape) == 2:
        img = np.dstack((img, img, img))
        qformat = QImage.Format_RGB888
        height_, width_, *_ = img.shape
    else:
        height_, width_ = img.shape

    return QPixmap.fromImage(
        QImage(img, width_, height_, width_ * 3, qformat).rgbSwapped()
    )


def build_widgets(tool, param, allow_real_time: bool, call_backs: dict, do_feedback=None):
    widget = None
    if isinstance(param.allowed_values, dict):
        label = QLabel(param.desc)
        widget = QComboBoxWthParam(
            tool=tool, param=param, label=label, allow_real_time=allow_real_time
        )
    elif isinstance(param.allowed_values, str):
        if param.allowed_values == "single_line_text_output":
            label = QLabel(param.desc)
            widget = QLineEdit()
            widget.setReadOnly(True)
        elif param.allowed_values == "multi_line_text_output":
            label = QLabel(param.desc)
            widget = QTextBrowser()
            widget.setMaximumHeight(72)
        elif param.allowed_values == "label":
            label = QLabel(param.desc)
            widget = None
        elif param.allowed_values == "table_output":
            label = None
            widget = QTableWidget()
            widget.setColumnCount(len(param.desc))
            widget.setHorizontalHeaderLabels(param.desc)
            widget.horizontalHeader().setStretchLastSection(True)
            widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        elif param.allowed_values == "single_line_text_input":
            label = QLabel(param.desc)
            widget = QLineEditWthParam(tool=tool, param=param, allow_real_time=allow_real_time)
        elif param.allowed_values == "multi_line_text_input":
            label = QLabel(param.desc)
            widget = QTextBrowserWthParam(tool=tool, param=param, allow_real_time=allow_real_time)
            widget.setLineWrapMode(QTextEdit.NoWrap)
            widget.setReadOnly(False)
            widget.setMaximumHeight(72)
        elif param.allowed_values == "input_button":
            label = None
            widget = QPushButtonWthParam(tool=tool, param=param, allow_real_time=allow_real_time)
        else:
            if do_feedback is not None:
                do_feedback(
                    status_message="Widget initialization: unknown param",
                    log_message=f"Widget initialization: unknown param {param.name}, allowed values {param.allowed_values}",
                )
            return None, None
    elif isinstance(param.allowed_values, tuple) or isinstance(param.allowed_values, list):
        pa = tuple(param.allowed_values)
        if pa == (0, 1):
            label = None
            widget = QCheckBoxWthParam(
                tool=tool, param=param, label=label, allow_real_time=allow_real_time
            )
        elif len(pa) == 2:
            label = QLabel(param.desc)
            if param.widget_type == "slider":
                widget = QSliderWthParam(
                    tool=tool, param=param, label=label, allow_real_time=allow_real_time
                )
            elif param.widget_type == "spin_box":
                widget = QSpinnerWthParam(
                    tool=tool, param=param, label=label, allow_real_time=allow_real_time
                )
        else:
            if do_feedback is not None:
                do_feedback(
                    status_message="Widget initialization: unknown param",
                    log_message=f"Widget initialization: unknown param {param.name}, allowed values {param.allowed_values}",
                )
            return None, None
    else:
        if do_feedback is not None:
            do_feedback(
                status_message="Widget initialization: unknown param", 
                log_message=f"Widget initialization: unknown param {param.name}, allowed values {param.allowed_values}",
            )
        return None, None

    if isinstance(tool, dict):
        tool_name = tool["uuid"]
    elif type(tool).__name__ in ("SettingsHolder", "PipelineSettings"):
        tool_name = "settings_holder"
    else:
        tool_name = tool.name
    param.init(
        tool_name=tool_name, label=label, widget=widget, **call_backs,
    )

    return widget, label


class CTreeWidgetItem(QTreeWidgetItem):
    def setData(self, column, role, value):
        state = self.checkState(column)
        QTreeWidgetItem.setData(self, column, role, value)
        if (role == Qt.CheckStateRole) and (state != self.checkState(column)):
            tree_widget = self.treeWidget()
            if tree_widget is not None:
                tree_widget.itemChecked.emit(self, column)


class CTreeWidget(QTreeWidget):
    itemChecked = pyqtSignal(object, int)

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


class QComboBoxWthParam(QComboBox):
    def __init__(self, tool, param, label, allow_real_time: bool = True, parent=None):
        QComboBox.__init__(self, parent)
        self._param = param
        self._label = label
        self._tool = tool
        self._allow_real_time = allow_real_time

    @property
    def param(self):
        return self._param

    @property
    def label(self):
        return self._label

    @property
    def tool(self):
        return self._tool

    @property
    def allow_real_time(self):
        return self._allow_real_time


class QSliderWthParam(QSlider):
    def __init__(self, tool, param, label, allow_real_time: bool = True):
        QSlider.__init__(self, Qt.Horizontal)
        self._param = param
        self._label = label
        self._tool = tool
        self._allow_real_time = allow_real_time

    @property
    def param(self):
        return self._param

    @property
    def label(self):
        return self._label

    @property
    def tool(self):
        return self._tool

    @property
    def allow_real_time(self):
        return self._allow_real_time


class QSpinnerWthParam(QSpinBox):
    def __init__(self, tool, param, label, allow_real_time: bool = True):
        QSpinBox.__init__(self)
        self._param = param
        self._label = label
        self._tool = tool
        self._allow_real_time = allow_real_time

    @property
    def param(self):
        return self._param

    @property
    def label(self):
        return self._label

    @property
    def tool(self):
        return self._tool

    @property
    def allow_real_time(self):
        return self._allow_real_time


class QCheckBoxWthParam(QCheckBox):
    def __init__(self, tool, param, label, allow_real_time: bool = True, parent=None):
        QCheckBox.__init__(self, parent)
        self._param = param
        self._label = label
        self._tool = tool
        self._allow_real_time = allow_real_time

    @property
    def param(self):
        return self._param

    @property
    def label(self):
        return self._label

    @property
    def tool(self):
        return self._tool

    @property
    def allow_real_time(self):
        return self._allow_real_time


class QLineEditWthParam(QLineEdit):
    def __init__(self, tool, param, allow_real_time: bool = True, parent=None):
        QLineEdit.__init__(self, parent)
        self._param = param
        self._tool = tool
        self._allow_real_time = allow_real_time

    @property
    def param(self):
        return self._param

    @property
    def tool(self):
        return self._tool

    @property
    def allow_real_time(self):
        return self._allow_real_time


class QTextBrowserWthParam(QTextBrowser):
    def __init__(self, tool, param, allow_real_time: bool = True, parent=None):
        QTextBrowser.__init__(self, parent)
        self._param = param
        self._tool = tool
        self._allow_real_time = allow_real_time

    @property
    def param(self):
        return self._param

    @property
    def tool(self):
        return self._tool

    @property
    def allow_real_time(self):
        return self._allow_real_time


class QPushButtonWthParam(QPushButton):
    def __init__(self, tool, param, allow_real_time: bool = False, parent=None):
        QPushButton.__init__(self, parent)
        self._param = param
        self._tool = tool
        self._allow_real_time = allow_real_time

    @property
    def param(self):
        return self._param

    @property
    def tool(self):
        return self._tool

    @property
    def allow_real_time(self):
        return self._allow_real_time


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
                q_pix = cv2_to_qimage(images)
            self._main_image = self.scene().addPixmap(q_pix)
            self.setSceneRect(self._main_image.boundingRect())
            self.fit_to_canvas()


class QColorDelegate(QItemDelegate):
    def __init__(self, parent=None, *args, **kwargs):
        QItemDelegate.__init__(self, parent, *args)
        self._palette: QPalette = kwargs.get("palette")

    def paint(self, painter, option, index):
        painter.save()

        df: pd.DataFrame = self.parent().model().df
        # set background color
        is_error_column = "error" in df.columns[index.column()]
        painter.setPen(QPen(Qt.NoPen))
        if is_error_column:
            try:
                num_val = int(index.data(Qt.DisplayRole))
                max_val = df[df.columns[index.column()]].max()
            except ValueError:
                num_val = None
                max_val = None
            if (num_val is not None) and (max_val is not None):
                colors = ipc.build_color_steps(
                    start_color=ipc.C_LIME, stop_color=ipc.C_RED, step_count=max_val + 1
                )
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

    def set_palette(self, new_palette):
        self._palette: QPalette = new_palette


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
        if (self._df is not None) and (orientation == Qt.Horizontal) and (role == Qt.DisplayRole):
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
    def df(self):
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
        if (self._df is not None) and (orientation == Qt.Horizontal) and (role == Qt.DisplayRole):
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
    def df(self):
        return self._df


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
        painter.save()

        df: pd.DataFrame = self.parent().model().images

        # Try cache retrieval
        data = self.get_annotation(row_number=index.row())
        if data is not None:
            color_dict = self.colors.get(data["kind"].lower(), self._default_colors)
        else:
            color_dict = self._default_colors
        bg_color = color_dict["s_bgd" if option.state & QStyle.State_Selected else "bgd"]
        fg_color = color_dict["s_fnt" if option.state & QStyle.State_Selected else "fnt"]

        fnt = painter.font()
        fnt.setBold(option.state & QStyle.State_Selected)
        painter.setFont(fnt)

        # Draw
        painter.setPen(QPen(Qt.NoPen))
        painter.setBrush(QBrush(bg_color))
        painter.drawRect(option.rect)
        painter.setPen(QPen(fg_color))
        painter.drawText(
            option.rect, Qt.AlignVCenter | Qt.AlignCenter, str(index.data(Qt.DisplayRole))
        )

        painter.restore()

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
                data = session_.query(OrmAnnotation).filter(OrmAnnotation.idk == luid).first()
                if data is not None:
                    ret = dict(
                        luid=data.idk, kind=data.kind, text=data.text, auto_text=data.auto_text
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
                        luid=luid, kind=ann_.kind, text=ann_.text, auto_text=ann_.auto_text
                    )
            elif text or auto_text:
                session_.add(OrmAnnotation(idk=luid, kind=kind, text=text, auto_text=auto_text))
                self.annotations[luid] = dict(luid=luid, kind=kind, text=text, auto_text=auto_text)

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


class TreeNode(object):
    def __init__(self, node_data, parent, row, call_backs, do_feedback):
        self.parent = parent
        self.row = row
        self.tag = 0
        self.call_backs = call_backs
        self.do_feedback = do_feedback
        self.widget_holder = None
        self.set_node_data(node_data)

    def set_node_data(self, new_data):
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
        return index.internalPointer() if index.isValid() else QModelIndex().internalPointer()

    def parent(self, index):
        node = self.get_item(index)
        if node.parent is None:
            return QModelIndex()
        else:
            return self.createIndex(node.parent.row, 0, node.parent)

    def reset(self):
        self.rootNodes = self._getRootNodes()
        super().reset(self)

    def iter_items(self, root, allowed_classes: [None, tuple] = None):
        if root is None:
            stack = [self.createIndex(0, 0, self.rootNodes[i]) for i in range(len(self.rootNodes))]
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


class PipelineDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, *args, **kwargs):
        QStyledItemDelegate.__init__(self, parent, *args)
        self.widget = None

    def paint(self, painter, option, index):
        ip = index.internalPointer()
        if isinstance(ip.node_data, IptParam):
            self.parent().setIndexWidget(
                index, index.internalPointer().widget_holder,
            )
        else:
            option.font.setBold(
                ip is not None
                and isinstance(ip.node_data, (ModuleNode, GroupNode))
                and ip.tag == 1
            )
            option.palette.setColor(
                QPalette.Text,
                Qt.red
                if ip is not None
                and isinstance(ip.node_data, (ModuleNode, GroupNode))
                and not ip.node_data.root.check_input(ip.node_data)
                else Qt.black,
            )
            QStyledItemDelegate.paint(self, painter, option, index)

    def createEditor(self, parent, option, index):
        ip = index.internalPointer()
        if isinstance(ip.node_data, GroupNode):
            self.widget = QWidget(parent)
            self.widget.setAutoFillBackground(True)
            self.horizontalLayout = QHBoxLayout(self.widget)
            self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
            self.horizontalLayout.addWidget(QLabel("Name: ", self.widget))

            self.txt_group_name = QLineEdit(self.widget)
            self.txt_group_name.setText(ip.node_data.name)
            self.horizontalLayout.addWidget(self.txt_group_name)

            self.horizontalLayout.addWidget(QLabel("Source: ", self.widget))
            self.cb_source = QComboBox(self.widget)
            self.cb_source.addItem("last_output", "last_output")
            self.cb_source.addItem("source", "source")
            self.cb_source.setCurrentIndex(1)
            model = self.parent().model()
            groups = model.as_pivot_list(index, allowed_classes=(GroupNode))
            previous_groups = groups.get("before", None)
            for group in previous_groups[1:]:
                nd = group.internalPointer().node_data
                self.cb_source.addItem(nd.name, nd.uuid)
                if nd.uuid == index.internalPointer().node_data.source:
                    self.cb_source.setCurrentIndex(self.cb_source.count() - 1)
            self.horizontalLayout.addWidget(self.cb_source)

            self.horizontalLayout.addWidget(QLabel("Merge mode: ", self.widget))
            self.cb_merge_mode = QComboBox(self.widget)
            for merge_mode in [
                ipc.MERGE_MODE_AND,
                ipc.MERGE_MODE_OR,
                ipc.MERGE_MODE_CHAIN,
                ipc.MERGE_MODE_NONE,
            ]:
                self.cb_merge_mode.addItem(ipc.merge_mode_to_str(merge_mode), merge_mode)
                if merge_mode == index.internalPointer().node_data.merge_mode:
                    self.cb_merge_mode.setCurrentIndex(self.cb_merge_mode.count() - 1)
            self.horizontalLayout.addWidget(self.cb_merge_mode)
            return self.widget
        else:
            return QStyledItemDelegate.createEditor(self, parent, option, index)


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
        if isinstance(self.node_data, str):
            return []
        elif isinstance(self.node_data, ModuleNode):
            return [
                PipelineNode(
                    node_data=gizmo,
                    parent=self,
                    row=index,
                    call_backs=self.call_backs,
                    do_feedback=self.do_feedback,
                )
                for index, gizmo in enumerate(self.node_data.tool.gizmos)
            ]
        elif isinstance(self.node_data, PipelineSettings):
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
            return [
                PipelineNode(
                    node_data=node,
                    parent=self,
                    row=index,
                    call_backs=self.call_backs,
                    do_feedback=self.do_feedback,
                )
                for index, node in enumerate(self.node_data.nodes)
            ]
        else:
            return []

    def set_node_data(self, new_data):
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
                label, widget = build_widgets(
                    tool=tool,
                    param=new_data,
                    call_backs=self.call_backs,
                    allow_real_time=False,  # not isinstance(tool, PipelineSettings),
                    do_feedback=self.do_feedback,
                )
                if widget is not None:
                    layout.addWidget(widget)
                if label is not None:
                    layout.addWidget(label)
                if label and widget:
                    layout.setStretch(0, 2)
                    layout.setStretch(1, 3)
        except Exception as e:
            print(f'Failed to process, because "{repr(e)}"')
            return False
        else:
            return True

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
            print(f'Failed to process, because "{repr(e)}"')
            return False
        else:
            return True

    def remove_children(self, index: int):
        try:
            node = self.children.pop(index)
            self.node_data.remove_node(node.node_data)
        except Exception as e:
            print(f'Failed to process, because "{repr(e)}"')
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
            print(f'Failed to process, because "{repr(e)}"')
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


class PipelineModel(TreeModel):
    def __init__(self, pipeline, call_backs, do_feedback):
        self.pipeline = pipeline
        self.call_backs = call_backs
        self.do_feedback = do_feedback
        TreeModel.__init__(self)

    def _getRootNodes(self):
        return [
            PipelineNode(
                node_data=f"Description:\n{self.pipeline.description}",
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
        return 1

    def data(self, index, role):
        if index.column() == 0:
            node = self.get_item(index)
            if role == Qt.DisplayRole:
                nd = node.node_data
                if isinstance(nd, str):
                    return nd
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
                    return f"{nd.name} - Src: {source}, {in_t} -> {out}, merge: {merge}"
                elif isinstance(nd, ModuleNode):
                    in_t = ipc.io_type_to_str(nd.input_type)
                    out = ipc.io_type_to_str(nd.output_type)
                    return f"{nd.name}, {in_t} -> {out}"
                else:
                    return "no data"
            elif role == Qt.ToolTipRole:
                nd = node.node_data
                if isinstance(nd, str):
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
                    return f"{nd.name} - src: {source}, {in_t} ->{out}, merge: {merge}, Double click to edit"
                elif isinstance(nd, ModuleNode):
                    return nd.tool.hint
                else:
                    return "no data"
            elif role == Qt.CheckStateRole:
                nd = node.node_data
                if node.parent is not None and (
                    isinstance(nd, ModuleNode) or isinstance(nd, GroupNode)
                ):
                    return node.enabled
            else:
                return None
        return None

    def setData(self, index, value, role=Qt.EditRole):
        if index.column() == 0:
            if role == Qt.CheckStateRole:
                item = self.get_item(index)
                item.enabled = value
                item.tag = 1
                nodes = self.as_pivot_list(index, (GroupNode, ModuleNode,))
                for node in nodes["before"]:
                    self.get_item(node).tag = 0
                for node in nodes["after"]:
                    self.get_item(node).tag = 1
                self.dataChanged.emit(index, index)
                self.layoutChanged.emit()
                return True
            elif role == Qt.EditRole:
                item = self.get_item(index)
                if isinstance(item.node_data, GroupNode):
                    if isinstance(value, str):
                        item.node_data.name = value
                    elif isinstance(value, GroupNode):
                        item.set_node_data(value)
                self.layoutChanged.emit()
                return True

        return super(TreeModel, self).setData(index, value, role)

    def get_parent_group_node(self, selected_items, allow_wandering: bool = False):
        if selected_items:
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
            self.get_item(added_index).set_node_data(nd.add_module(tool=module, enabled=enabled))
            self.dataChanged.emit(root, root)
            self.layoutChanged.emit()
            return added_index

    def add_group(self, selected_items, merge_mode: str = ipc.MERGE_MODE_CHAIN, name: str = ""):
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

    def move_row(self, selected_items, target_index: int, target_parent: QModelIndex = None):
        if len(selected_items) != 1:
            return False
        root = selected_items[0]
        self.beginMoveRows(root.parent(), root.row(), root.row(), target_parent, target_index)
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
            selected_items=selected_items, target_index=root.row() + 1, target_parent=root.parent()
        )

    def move_up(self, selected_items):
        if len(selected_items) != 1:
            return False
        root = selected_items[0]
        self.move_row(
            selected_items=selected_items, target_index=root.row() - 1, target_parent=root.parent()
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
        nd = self.get_item(index).node_data
        if isinstance(nd, (GroupNode, str)):
            flags |= Qt.ItemIsEditable
        if isinstance(nd, (ModuleNode, GroupNode)):
            flags |= Qt.ItemIsUserCheckable
            if isinstance(nd, GroupNode):
                flags |= Qt.ItemIsTristate
        return flags
