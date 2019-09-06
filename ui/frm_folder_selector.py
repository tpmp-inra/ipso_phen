# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'c:\Users\fmavianemac\Documents\Felicia\ipso_phen\ui\frm_folder_selector.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_folder_selector(object):
    def setupUi(self, folder_selector):
        folder_selector.setObjectName("folder_selector")
        folder_selector.resize(615, 193)
        folder_selector.setSizeGripEnabled(True)
        folder_selector.setModal(True)
        self.gridLayout = QtWidgets.QGridLayout(folder_selector)
        self.gridLayout.setObjectName("gridLayout")
        self.edt_fld_name = QtWidgets.QLineEdit(folder_selector)
        self.edt_fld_name.setReadOnly(True)
        self.edt_fld_name.setObjectName("edt_fld_name")
        self.gridLayout.addWidget(self.edt_fld_name, 1, 1, 1, 3)
        self.btn_box = QtWidgets.QDialogButtonBox(folder_selector)
        self.btn_box.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.btn_box.setObjectName("btn_box")
        self.gridLayout.addWidget(self.btn_box, 4, 2, 1, 1)
        self.bt_select_folder = QtWidgets.QPushButton(folder_selector)
        self.bt_select_folder.setMaximumSize(QtCore.QSize(26, 16777215))
        self.bt_select_folder.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("../resources/folder_blue.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.bt_select_folder.setIcon(icon)
        self.bt_select_folder.setObjectName("bt_select_folder")
        self.gridLayout.addWidget(self.bt_select_folder, 1, 4, 1, 1)
        self.label_3 = QtWidgets.QLabel(folder_selector)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 3, 0, 1, 1)
        self.edt_db_name = QtWidgets.QLineEdit(folder_selector)
        self.edt_db_name.setObjectName("edt_db_name")
        self.gridLayout.addWidget(self.edt_db_name, 3, 1, 1, 4)
        self.cb_dbms = QtWidgets.QComboBox(folder_selector)
        self.cb_dbms.setObjectName("cb_dbms")
        self.cb_dbms.addItem("")
        self.cb_dbms.addItem("")
        self.gridLayout.addWidget(self.cb_dbms, 2, 1, 1, 4)
        self.label = QtWidgets.QLabel(folder_selector)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 1, 0, 1, 1)
        self.label_4 = QtWidgets.QLabel(folder_selector)
        self.label_4.setObjectName("label_4")
        self.gridLayout.addWidget(self.label_4, 2, 0, 1, 1)
        self.label_2 = QtWidgets.QLabel(folder_selector)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 0, 1, 1, 2)

        self.retranslateUi(folder_selector)
        QtCore.QMetaObject.connectSlotsByName(folder_selector)

    def retranslateUi(self, folder_selector):
        _translate = QtCore.QCoreApplication.translate
        folder_selector.setWindowTitle(_translate("folder_selector", "Select folder and options"))
        self.label_3.setText(_translate("folder_selector", "Database name:"))
        self.cb_dbms.setItemText(0, _translate("folder_selector", "None - Won\'t be serialized"))
        self.cb_dbms.setItemText(1, _translate("folder_selector", "Sqlite"))
        self.label.setText(_translate("folder_selector", "Folder:"))
        self.label_4.setToolTip(_translate("folder_selector", "Database management system"))
        self.label_4.setText(_translate("folder_selector", "DBMS:"))
        self.label_2.setText(_translate("folder_selector", "<b>WARNING</b>: Folder parsing is recusrsive !!!"))

