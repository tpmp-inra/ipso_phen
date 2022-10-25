# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'about.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_about_dialog(object):
    def setupUi(self, about_dialog):
        if not about_dialog.objectName():
            about_dialog.setObjectName(u"about_dialog")
        about_dialog.resize(1200, 745)
        icon = QIcon()
        icon.addFile(u"resources/leaf-24.ico", QSize(), QIcon.Normal, QIcon.Off)
        about_dialog.setWindowIcon(icon)
        about_dialog.setModal(True)
        self.gridLayout = QGridLayout(about_dialog)
        self.gridLayout.setObjectName(u"gridLayout")
        self.lb_version = QLabel(about_dialog)
        self.lb_version.setObjectName(u"lb_version")
        self.lb_version.setAlignment(Qt.AlignCenter)

        self.gridLayout.addWidget(self.lb_version, 1, 0, 1, 2)

        self.lbl_authors = QLabel(about_dialog)
        self.lbl_authors.setObjectName(u"lbl_authors")
        self.lbl_authors.setAlignment(Qt.AlignCenter)

        self.gridLayout.addWidget(self.lbl_authors, 3, 0, 1, 2)

        self.lbl_image = QLabel(about_dialog)
        self.lbl_image.setObjectName(u"lbl_image")
        self.lbl_image.setPixmap(QPixmap(u"resources/leaf-24.ico"))
        self.lbl_image.setAlignment(Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter)

        self.gridLayout.addWidget(self.lbl_image, 0, 0, 1, 1)

        self.lbl_copyright = QLabel(about_dialog)
        self.lbl_copyright.setObjectName(u"lbl_copyright")
        self.lbl_copyright.setAlignment(Qt.AlignCenter)

        self.gridLayout.addWidget(self.lbl_copyright, 2, 0, 1, 2)

        self.lbl_title = QLabel(about_dialog)
        self.lbl_title.setObjectName(u"lbl_title")
        font = QFont()
        font.setPointSize(32)
        self.lbl_title.setFont(font)

        self.gridLayout.addWidget(self.lbl_title, 0, 1, 1, 1)

        self.buttonBox = QDialogButtonBox(about_dialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Ok)

        self.gridLayout.addWidget(self.buttonBox, 7, 0, 1, 2)

        self.txt_brw_used_packages = QTextBrowser(about_dialog)
        self.txt_brw_used_packages.setObjectName(u"txt_brw_used_packages")

        self.gridLayout.addWidget(self.txt_brw_used_packages, 6, 0, 1, 2)

        self.lbl_license_text = QLabel(about_dialog)
        self.lbl_license_text.setObjectName(u"lbl_license_text")
        self.lbl_license_text.setWordWrap(True)

        self.gridLayout.addWidget(self.lbl_license_text, 5, 0, 1, 2)

        self.label = QLabel(about_dialog)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 4, 0, 1, 2)

        self.gridLayout.setColumnStretch(0, 1)
        self.gridLayout.setColumnStretch(1, 4)

        self.retranslateUi(about_dialog)
        self.buttonBox.accepted.connect(about_dialog.accept)
        self.buttonBox.rejected.connect(about_dialog.reject)

        QMetaObject.connectSlotsByName(about_dialog)

    # setupUi

    def retranslateUi(self, about_dialog):
        about_dialog.setWindowTitle(
            QCoreApplication.translate("about_dialog", u"About", None)
        )
        self.lb_version.setText(
            QCoreApplication.translate("about_dialog", u"version", None)
        )
        self.lbl_authors.setText(
            QCoreApplication.translate("about_dialog", u"Authors", None)
        )
        self.lbl_image.setText("")
        self.lbl_copyright.setText(
            QCoreApplication.translate("about_dialog", u"Copyright", None)
        )
        self.lbl_title.setText(
            QCoreApplication.translate("about_dialog", u"IPSO Phen", None)
        )
        self.lbl_license_text.setText(
            QCoreApplication.translate("about_dialog", u"Used packages", None)
        )
        self.label.setText("")

    # retranslateUi
