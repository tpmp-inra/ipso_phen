# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'c:\Users\fmavianemac\Documents\Felicia\ipso_phen\ui\about_form.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_about_dialog(object):
    def setupUi(self, about_dialog):
        about_dialog.setObjectName("about_dialog")
        about_dialog.resize(614, 513)
        about_dialog.setModal(True)
        self.gridLayout = QtWidgets.QGridLayout(about_dialog)
        self.gridLayout.setObjectName("gridLayout")
        self.lb_version = QtWidgets.QLabel(about_dialog)
        self.lb_version.setAlignment(QtCore.Qt.AlignCenter)
        self.lb_version.setObjectName("lb_version")
        self.gridLayout.addWidget(self.lb_version, 1, 0, 1, 2)
        self.lbl_authors = QtWidgets.QLabel(about_dialog)
        self.lbl_authors.setAlignment(QtCore.Qt.AlignCenter)
        self.lbl_authors.setObjectName("lbl_authors")
        self.gridLayout.addWidget(self.lbl_authors, 3, 0, 1, 2)
        self.lbl_image = QtWidgets.QLabel(about_dialog)
        self.lbl_image.setText("")
        self.lbl_image.setPixmap(QtGui.QPixmap("resources/leaf-24.ico"))
        self.lbl_image.setAlignment(QtCore.Qt.AlignCenter)
        self.lbl_image.setObjectName("lbl_image")
        self.gridLayout.addWidget(self.lbl_image, 0, 0, 1, 1)
        self.lbl_copyright = QtWidgets.QLabel(about_dialog)
        self.lbl_copyright.setAlignment(QtCore.Qt.AlignCenter)
        self.lbl_copyright.setObjectName("lbl_copyright")
        self.gridLayout.addWidget(self.lbl_copyright, 2, 0, 1, 2)
        self.lbl_title = QtWidgets.QLabel(about_dialog)
        font = QtGui.QFont()
        font.setPointSize(32)
        self.lbl_title.setFont(font)
        self.lbl_title.setObjectName("lbl_title")
        self.gridLayout.addWidget(self.lbl_title, 0, 1, 1, 1)
        self.buttonBox = QtWidgets.QDialogButtonBox(about_dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 7, 0, 1, 2)
        self.txt_brw_used_packages = QtWidgets.QTextBrowser(about_dialog)
        self.txt_brw_used_packages.setObjectName("txt_brw_used_packages")
        self.gridLayout.addWidget(self.txt_brw_used_packages, 6, 0, 1, 2)
        self.lbl_license_text = QtWidgets.QLabel(about_dialog)
        self.lbl_license_text.setWordWrap(True)
        self.lbl_license_text.setObjectName("lbl_license_text")
        self.gridLayout.addWidget(self.lbl_license_text, 5, 0, 1, 2)
        self.label = QtWidgets.QLabel(about_dialog)
        self.label.setText("")
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 4, 0, 1, 2)
        self.gridLayout.setColumnStretch(0, 1)
        self.gridLayout.setColumnStretch(1, 4)

        self.retranslateUi(about_dialog)
        self.buttonBox.accepted.connect(about_dialog.accept)
        self.buttonBox.rejected.connect(about_dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(about_dialog)

    def retranslateUi(self, about_dialog):
        _translate = QtCore.QCoreApplication.translate
        about_dialog.setWindowTitle(_translate("about_dialog", "About"))
        self.lb_version.setText(_translate("about_dialog", "version"))
        self.lbl_authors.setText(_translate("about_dialog", "Authors"))
        self.lbl_copyright.setText(_translate("about_dialog", "Copyright"))
        self.lbl_title.setText(_translate("about_dialog", "IPSO Phen"))
        self.lbl_license_text.setText(
            _translate(
                "about_dialog",
                "Used packages - Some packages may not be used, but are linked by used packages",
            )
        )
