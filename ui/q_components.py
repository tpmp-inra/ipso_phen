import os
from datetime import datetime as dt

import numpy as np
import pandas as pd

from PyQt5.QtCore import Qt, pyqtSignal, QAbstractTableModel

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
    QStyle,
)
from PyQt5.QtGui import QImage, QPixmap, QBrush, QPen, QPalette, QColor

from ip_base import ip_common as ipc
from annotations.orm_annotations import OrmAnnotation, OrmAnnotationsDbWrapper


def scale(val, src, dst):
    return int(((val - src[0]) / float(src[1] - src[0])) * (dst[1] - dst[0]) + dst[0])


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
            else:
                qformat = QImage.Format_Indexed8
                if len(value.shape) == 3:
                    if value.shape[2] == 4:
                        qformat = QImage.Format_RGBA8888
                    else:
                        qformat = QImage.Format_RGB888
                    height_, width_, *_ = value.shape
                elif len(value.shape) == 2:
                    value = np.dstack((value, value, value))
                    qformat = QImage.Format_RGB888
                    height_, width_, *_ = value.shape
                else:
                    height_, width_ = value.shape

                q_pix = QPixmap.fromImage(
                    QImage(value, width_, height_, width_ * 3, qformat).rgbSwapped()
                )
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
        painter.drawText(option.rect, Qt.AlignVCenter | Qt.AlignCenter, str(index.data(Qt.DisplayRole)))

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
