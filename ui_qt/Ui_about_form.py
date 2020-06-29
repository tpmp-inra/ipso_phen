# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'c:\Users\fmavianemac\Documents\Felicia\Python\ipso_phen\about_form.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(400, 457)
        self.gridLayout = QtWidgets.QGridLayout(Dialog)
        self.gridLayout.setObjectName("gridLayout")
        self.lb_version = QtWidgets.QLabel(Dialog)
        self.lb_version.setAlignment(QtCore.Qt.AlignCenter)
        self.lb_version.setObjectName("lb_version")
        self.gridLayout.addWidget(self.lb_version, 1, 0, 1, 2)
        self.lbl_image = QtWidgets.QLabel(Dialog)
        self.lbl_image.setAlignment(QtCore.Qt.AlignCenter)
        self.lbl_image.setObjectName("lbl_image")
        self.gridLayout.addWidget(self.lbl_image, 0, 0, 1, 1)
        self.lbl_authors = QtWidgets.QLabel(Dialog)
        self.lbl_authors.setAlignment(QtCore.Qt.AlignCenter)
        self.lbl_authors.setObjectName("lbl_authors")
        self.gridLayout.addWidget(self.lbl_authors, 3, 0, 1, 2)
        self.lbl_copyright = QtWidgets.QLabel(Dialog)
        self.lbl_copyright.setAlignment(QtCore.Qt.AlignCenter)
        self.lbl_copyright.setObjectName("lbl_copyright")
        self.gridLayout.addWidget(self.lbl_copyright, 2, 0, 1, 2)
        self.lbl_license_text = QtWidgets.QLabel(Dialog)
        self.lbl_license_text.setObjectName("lbl_license_text")
        self.gridLayout.addWidget(self.lbl_license_text, 5, 0, 1, 1)
        self.lbl_title = QtWidgets.QLabel(Dialog)
        font = QtGui.QFont()
        font.setPointSize(32)
        self.lbl_title.setFont(font)
        self.lbl_title.setObjectName("lbl_title")
        self.gridLayout.addWidget(self.lbl_title, 0, 1, 1, 1)
        self.listWidget = QtWidgets.QListWidget(Dialog)
        self.listWidget.setObjectName("listWidget")
        self.gridLayout.addWidget(self.listWidget, 6, 0, 1, 2)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 7, 0, 1, 2)
        spacerItem = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 4, 0, 1, 2)
        self.gridLayout.setColumnStretch(0, 1)
        self.gridLayout.setColumnStretch(1, 3)

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.lb_version.setText(_translate("Dialog", "version"))
        self.lbl_image.setText(_translate("Dialog", "Image"))
        self.lbl_authors.setText(_translate("Dialog", "Authors"))
        self.lbl_copyright.setText(_translate("Dialog", "Copyright"))
        self.lbl_license_text.setText(_translate("Dialog", "Used packages:"))
        self.lbl_title.setText(_translate("Dialog", "IPSO Phen"))

