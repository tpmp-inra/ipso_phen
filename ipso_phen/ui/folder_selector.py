# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'folder_selector.ui'
##
## Created by: Qt User Interface Compiler version 5.15.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import (
    QCoreApplication,
    QDate,
    QDateTime,
    QMetaObject,
    QObject,
    QPoint,
    QRect,
    QSize,
    QTime,
    QUrl,
    Qt,
)
from PySide2.QtGui import (
    QBrush,
    QColor,
    QConicalGradient,
    QCursor,
    QFont,
    QFontDatabase,
    QIcon,
    QKeySequence,
    QLinearGradient,
    QPalette,
    QPainter,
    QPixmap,
    QRadialGradient,
)
from PySide2.QtWidgets import *


class Ui_folder_selector(object):
    def setupUi(self, folder_selector):
        if not folder_selector.objectName():
            folder_selector.setObjectName(u"folder_selector")
        folder_selector.resize(615, 193)
        folder_selector.setSizeGripEnabled(True)
        folder_selector.setModal(True)
        self.gridLayout = QGridLayout(folder_selector)
        self.gridLayout.setObjectName(u"gridLayout")
        self.edt_fld_name = QLineEdit(folder_selector)
        self.edt_fld_name.setObjectName(u"edt_fld_name")
        self.edt_fld_name.setReadOnly(True)

        self.gridLayout.addWidget(self.edt_fld_name, 1, 1, 1, 3)

        self.btn_box = QDialogButtonBox(folder_selector)
        self.btn_box.setObjectName(u"btn_box")
        self.btn_box.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)

        self.gridLayout.addWidget(self.btn_box, 4, 2, 1, 1)

        self.bt_select_folder = QPushButton(folder_selector)
        self.bt_select_folder.setObjectName(u"bt_select_folder")
        self.bt_select_folder.setMaximumSize(QSize(26, 16777215))
        icon = QIcon()
        icon.addFile(u"../resources/folder_blue.png", QSize(), QIcon.Normal, QIcon.Off)
        self.bt_select_folder.setIcon(icon)

        self.gridLayout.addWidget(self.bt_select_folder, 1, 4, 1, 1)

        self.label_3 = QLabel(folder_selector)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout.addWidget(self.label_3, 3, 0, 1, 1)

        self.edt_db_name = QLineEdit(folder_selector)
        self.edt_db_name.setObjectName(u"edt_db_name")

        self.gridLayout.addWidget(self.edt_db_name, 3, 1, 1, 4)

        self.cb_dbms = QComboBox(folder_selector)
        self.cb_dbms.addItem("")
        self.cb_dbms.addItem("")
        self.cb_dbms.setObjectName(u"cb_dbms")

        self.gridLayout.addWidget(self.cb_dbms, 2, 1, 1, 4)

        self.label = QLabel(folder_selector)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 1, 0, 1, 1)

        self.label_4 = QLabel(folder_selector)
        self.label_4.setObjectName(u"label_4")

        self.gridLayout.addWidget(self.label_4, 2, 0, 1, 1)

        self.label_2 = QLabel(folder_selector)
        self.label_2.setObjectName(u"label_2")
        font = QFont()
        font.setPointSize(10)
        self.label_2.setFont(font)

        self.gridLayout.addWidget(self.label_2, 0, 1, 1, 2)

        self.retranslateUi(folder_selector)

        QMetaObject.connectSlotsByName(folder_selector)

    # setupUi

    def retranslateUi(self, folder_selector):
        folder_selector.setWindowTitle(
            QCoreApplication.translate(
                "folder_selector", u"Select folder and options", None
            )
        )
        self.bt_select_folder.setText("")
        self.label_3.setText(
            QCoreApplication.translate("folder_selector", u"Database name:", None)
        )
        self.cb_dbms.setItemText(
            0,
            QCoreApplication.translate(
                "folder_selector", u"None - Won't be serialized", None
            ),
        )
        self.cb_dbms.setItemText(
            1, QCoreApplication.translate("folder_selector", u"Sqlite", None)
        )

        self.label.setText(
            QCoreApplication.translate("folder_selector", u"Folder:", None)
        )
        # if QT_CONFIG(tooltip)
        self.label_4.setToolTip(
            QCoreApplication.translate(
                "folder_selector", u"Database management system", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.label_4.setText(
            QCoreApplication.translate("folder_selector", u"DBMS:", None)
        )
        self.label_2.setText(
            QCoreApplication.translate(
                "folder_selector",
                u"<b>WARNING</b>: Folder parsing is recusrsive !!!",
                None,
            )
        )

    # retranslateUi
