# -*- coding: utf-8 -*-

################################################################################
#  Form generated from reading UI file 'new_tool.ui'
##
#  Created by: Qt User Interface Compiler version 5.15.0
##
#  WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import (
    QCoreApplication,
    QMetaObject,
)
from PySide2.QtGui import (
    QFont,
    QPixmap,
)

from PySide2.QtWidgets import (
    QGridLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QGroupBox,
    QRadioButton,
    QTextEdit,
    QCheckBox,
    QSpacerItem,
    QSizePolicy,
    QPushButton,
    QHBoxLayout,
)


class Ui_dlg_new_tool(object):
    def setupUi(self, dlg_new_tool):
        if not dlg_new_tool.objectName():
            dlg_new_tool.setObjectName(u"dlg_new_tool")
        dlg_new_tool.resize(570, 463)
        dlg_new_tool.setModal(True)
        self.gridLayout_2 = QGridLayout(dlg_new_tool)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.te_description = QTextEdit(dlg_new_tool)
        self.te_description.setObjectName(u"te_description")

        self.gridLayout.addWidget(self.te_description, 3, 0, 1, 6)

        self.label = QLabel(dlg_new_tool)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        self.lbl_file_exists = QLabel(dlg_new_tool)
        self.lbl_file_exists.setObjectName(u"lbl_file_exists")
        self.lbl_file_exists.setPixmap(QPixmap(u"../resources/OK.png"))

        self.gridLayout.addWidget(self.lbl_file_exists, 0, 5, 1, 1)

        self.label_5 = QLabel(dlg_new_tool)
        self.label_5.setObjectName(u"label_5")

        self.gridLayout.addWidget(self.label_5, 0, 3, 1, 1)

        self.chk_mask_required = QCheckBox(dlg_new_tool)
        self.chk_mask_required.setObjectName(u"chk_mask_required")

        self.gridLayout.addWidget(self.chk_mask_required, 5, 0, 1, 6)

        self.label_4 = QLabel(dlg_new_tool)
        self.label_4.setObjectName(u"label_4")

        self.gridLayout.addWidget(self.label_4, 0, 2, 1, 1)

        self.le_tool_name = QLineEdit(dlg_new_tool)
        self.le_tool_name.setObjectName(u"le_tool_name")

        self.gridLayout.addWidget(self.le_tool_name, 0, 1, 1, 1)

        self.label_3 = QLabel(dlg_new_tool)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout.addWidget(self.label_3, 1, 3, 1, 1)

        self.le_file_name = QLineEdit(dlg_new_tool)
        self.le_file_name.setObjectName(u"le_file_name")
        self.le_file_name.setReadOnly(True)

        self.gridLayout.addWidget(self.le_file_name, 0, 4, 1, 1)

        self.label_6 = QLabel(dlg_new_tool)
        self.label_6.setObjectName(u"label_6")
        font = QFont()
        font.setPointSize(8)
        self.label_6.setFont(font)

        self.gridLayout.addWidget(self.label_6, 1, 2, 1, 1)

        self.le_class_name = QLineEdit(dlg_new_tool)
        self.le_class_name.setObjectName(u"le_class_name")
        self.le_class_name.setReadOnly(True)

        self.gridLayout.addWidget(self.le_class_name, 1, 4, 1, 1)

        self.label_2 = QLabel(dlg_new_tool)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout.addWidget(self.label_2, 2, 0, 1, 6)

        self.label_7 = QLabel(dlg_new_tool)
        self.label_7.setObjectName(u"label_7")

        self.gridLayout.addWidget(self.label_7, 4, 0, 1, 1)

        self.le_package_name = QLineEdit(dlg_new_tool)
        self.le_package_name.setObjectName(u"le_package_name")

        self.gridLayout.addWidget(self.le_package_name, 4, 1, 1, 5)

        self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 2)

        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.groupBox = QGroupBox(dlg_new_tool)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setCheckable(False)
        self.verticalLayout = QVBoxLayout(self.groupBox)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.rb_output_image = QRadioButton(self.groupBox)
        self.rb_output_image.setObjectName(u"rb_output_image")
        self.rb_output_image.setChecked(True)

        self.verticalLayout.addWidget(self.rb_output_image)

        self.rb_output_mask = QRadioButton(self.groupBox)
        self.rb_output_mask.setObjectName(u"rb_output_mask")

        self.verticalLayout.addWidget(self.rb_output_mask)

        self.rb_output_data = QRadioButton(self.groupBox)
        self.rb_output_data.setObjectName(u"rb_output_data")

        self.verticalLayout.addWidget(self.rb_output_data)

        self.rb_output_none = QRadioButton(self.groupBox)
        self.rb_output_none.setObjectName(u"rb_output_none")

        self.verticalLayout.addWidget(self.rb_output_none)

        self.verticalLayout_4.addWidget(self.groupBox)

        self.gb_pipeline_tool_groups = QGroupBox(dlg_new_tool)
        self.gb_pipeline_tool_groups.setObjectName(u"gb_pipeline_tool_groups")

        self.verticalLayout_4.addWidget(self.gb_pipeline_tool_groups)

        self.verticalSpacer = QSpacerItem(
            20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding
        )

        self.verticalLayout_4.addItem(self.verticalSpacer)

        self.gridLayout_2.addLayout(self.verticalLayout_4, 1, 0, 1, 1)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.groupBox_2 = QGroupBox(dlg_new_tool)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.verticalLayout_2 = QVBoxLayout(self.groupBox_2)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.rb_rt_yes = QRadioButton(self.groupBox_2)
        self.rb_rt_yes.setObjectName(u"rb_rt_yes")

        self.verticalLayout_2.addWidget(self.rb_rt_yes)

        self.rb_rt_no = QRadioButton(self.groupBox_2)
        self.rb_rt_no.setObjectName(u"rb_rt_no")
        self.rb_rt_no.setChecked(True)

        self.verticalLayout_2.addWidget(self.rb_rt_no)

        self.rb_rt_widget = QRadioButton(self.groupBox_2)
        self.rb_rt_widget.setObjectName(u"rb_rt_widget")

        self.verticalLayout_2.addWidget(self.rb_rt_widget)

        self.rb_rt_property = QRadioButton(self.groupBox_2)
        self.rb_rt_property.setObjectName(u"rb_rt_property")

        self.verticalLayout_2.addWidget(self.rb_rt_property)

        self.verticalLayout_3.addWidget(self.groupBox_2)

        self.gb_no_pipeline_tool_groups = QGroupBox(dlg_new_tool)
        self.gb_no_pipeline_tool_groups.setObjectName(u"gb_no_pipeline_tool_groups")

        self.verticalLayout_3.addWidget(self.gb_no_pipeline_tool_groups)

        self.verticalSpacer_2 = QSpacerItem(
            20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding
        )

        self.verticalLayout_3.addItem(self.verticalSpacer_2)

        self.gridLayout_2.addLayout(self.verticalLayout_3, 1, 1, 1, 1)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum
        )

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.bt_save = QPushButton(dlg_new_tool)
        self.bt_save.setObjectName(u"bt_save")

        self.horizontalLayout.addWidget(self.bt_save)

        self.bt_cancel = QPushButton(dlg_new_tool)
        self.bt_cancel.setObjectName(u"bt_cancel")

        self.horizontalLayout.addWidget(self.bt_cancel)

        self.gridLayout_2.addLayout(self.horizontalLayout, 2, 1, 1, 1)

        self.gridLayout_2.setColumnStretch(0, 1)
        self.gridLayout_2.setColumnStretch(1, 1)

        self.retranslateUi(dlg_new_tool)

        QMetaObject.connectSlotsByName(dlg_new_tool)

    # setupUi

    def retranslateUi(self, dlg_new_tool):
        dlg_new_tool.setWindowTitle(
            QCoreApplication.translate("dlg_new_tool", u"New tool wizard", None)
        )
        self.te_description.setPlaceholderText(
            QCoreApplication.translate(
                "dlg_new_tool",
                u"Write your tool's description here.\\nYou can use HTML tags",
                None,
            )
        )
        self.label.setText(
            QCoreApplication.translate("dlg_new_tool", u"Tool name:", None)
        )
        self.lbl_file_exists.setText("")
        self.label_5.setText(
            QCoreApplication.translate("dlg_new_tool", u"File name:", None)
        )
        self.chk_mask_required.setText(
            QCoreApplication.translate("dlg_new_tool", u"Requires mask in input", None)
        )
        self.label_4.setText(u"\ud83e\udc62")
        self.label_6.setText(u"\ud83e\udc62")
        self.label_3.setText(
            QCoreApplication.translate("dlg_new_tool", u"Class name", None)
        )
        self.label_2.setText(
            QCoreApplication.translate("dlg_new_tool", u"Description:", None)
        )
        self.label_7.setText(
            QCoreApplication.translate("dlg_new_tool", u"Package:", None)
        )
        self.groupBox.setTitle(
            QCoreApplication.translate("dlg_new_tool", u"Output:", None)
        )
        self.rb_output_image.setText(
            QCoreApplication.translate("dlg_new_tool", u"Image", None)
        )
        self.rb_output_mask.setText(
            QCoreApplication.translate("dlg_new_tool", u"Mask", None)
        )
        self.rb_output_data.setText(
            QCoreApplication.translate("dlg_new_tool", u"Data", None)
        )
        self.rb_output_none.setText(
            QCoreApplication.translate("dlg_new_tool", u"None", None)
        )
        self.gb_pipeline_tool_groups.setTitle(
            QCoreApplication.translate(
                "dlg_new_tool", u"Groups that can be added to pipelines", None
            )
        )
        self.groupBox_2.setTitle(
            QCoreApplication.translate("dlg_new_tool", u"Real time:", None)
        )
        self.rb_rt_yes.setText(QCoreApplication.translate("dlg_new_tool", u"Yes", None))
        self.rb_rt_no.setText(QCoreApplication.translate("dlg_new_tool", u"No", None))
        self.rb_rt_widget.setText(
            QCoreApplication.translate("dlg_new_tool", u"Widget", None)
        )
        self.rb_rt_property.setText(
            QCoreApplication.translate("dlg_new_tool", u"Property", None)
        )
        self.gb_no_pipeline_tool_groups.setTitle(
            QCoreApplication.translate(
                "dlg_new_tool", u"Groups forbiden in pipelines", None
            )
        )
        self.bt_save.setText(QCoreApplication.translate("dlg_new_tool", u"Save", None))
        self.bt_cancel.setText(
            QCoreApplication.translate("dlg_new_tool", u"Close", None)
        )

    # retranslateUi
