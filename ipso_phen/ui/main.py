# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import QCoreApplication, QMetaObject, QRect, QSize, Qt
from PySide2.QtGui import QFont, QIcon
from PySide2.QtWidgets import (
    QAction,
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QHBoxLayout,
    QCheckBox,
    QComboBox,
    QSpacerItem,
    QGridLayout,
    QFrame,
    QSplitter,
    QPushButton,
    QTableView,
    QSizePolicy,
    QAbstractItemView,
    QLabel,
    QSpinBox,
    QTextEdit,
    QToolButton,
    QListWidget,
    QProgressBar,
    QTreeView,
    QScrollArea,
    QGroupBox,
    QTextBrowser,
    QSlider,
    QRadioButton,
    QLineEdit,
    QMenuBar,
    QMenu,
    QDockWidget,
    QStatusBar,
)

import ipso_phen.ui.main_rc


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1045, 902)
        font = QFont()
        font.setFamily(u"Consolas")
        MainWindow.setFont(font)
        icon = QIcon()
        icon.addFile(u":/icons/resources/leaf-24.ico", QSize(), QIcon.Normal, QIcon.Off)
        MainWindow.setWindowIcon(icon)
        MainWindow.setToolTipDuration(-4)
        self.actionTPMP = QAction(MainWindow)
        self.actionTPMP.setObjectName(u"actionTPMP")
        self.actionTPMP.setCheckable(False)
        self.actionTPMP.setChecked(False)
        self.actionTPMP_sample = QAction(MainWindow)
        self.actionTPMP_sample.setObjectName(u"actionTPMP_sample")
        self.actionTPMP_sample.setCheckable(False)
        self.action_switch_db_new = QAction(MainWindow)
        self.action_switch_db_new.setObjectName(u"action_switch_db_new")
        self.action_switch_db_new.setCheckable(False)
        self.actionSelect = QAction(MainWindow)
        self.actionSelect.setObjectName(u"actionSelect")
        self.actionExit = QAction(MainWindow)
        self.actionExit.setObjectName(u"actionExit")
        self.actionEnable_annotations = QAction(MainWindow)
        self.actionEnable_annotations.setObjectName(u"actionEnable_annotations")
        self.actionEnable_annotations.setCheckable(True)
        self.actionEnable_log = QAction(MainWindow)
        self.actionEnable_log.setObjectName(u"actionEnable_log")
        self.actionEnable_log.setCheckable(True)
        self.actionEnable_log.setChecked(True)
        self.actionSave_selected_image = QAction(MainWindow)
        self.actionSave_selected_image.setObjectName(u"actionSave_selected_image")
        self.actionSave_all_images = QAction(MainWindow)
        self.actionSave_all_images.setObjectName(u"actionSave_all_images")
        self.action_parse_folder = QAction(MainWindow)
        self.action_parse_folder.setObjectName(u"action_parse_folder")
        self.actionAdd_channel_mask = QAction(MainWindow)
        self.actionAdd_channel_mask.setObjectName(u"actionAdd_channel_mask")
        self.actionAdd_white_balance_fixer = QAction(MainWindow)
        self.actionAdd_white_balance_fixer.setObjectName(u"actionAdd_white_balance_fixer")
        self.action_script_merge_select_and = QAction(MainWindow)
        self.action_script_merge_select_and.setObjectName(
            u"action_script_merge_select_and"
        )
        self.action_script_merge_select_and.setCheckable(True)
        self.action_script_merge_select_and.setChecked(True)
        self.action_script_merge_select_or = QAction(MainWindow)
        self.action_script_merge_select_or.setObjectName(u"action_script_merge_select_or")
        self.action_script_merge_select_or.setCheckable(True)
        self.actionSet_contour_cleaner = QAction(MainWindow)
        self.actionSet_contour_cleaner.setObjectName(u"actionSet_contour_cleaner")
        self.actionDisplay_images = QAction(MainWindow)
        self.actionDisplay_images.setObjectName(u"actionDisplay_images")
        self.actionDisplay_images.setCheckable(True)
        self.actionDisplay_images.setChecked(True)
        self.actionUse_file_name = QAction(MainWindow)
        self.actionUse_file_name.setObjectName(u"actionUse_file_name")
        self.actionUse_file_name.setCheckable(True)
        self.actionUse_file_name.setChecked(True)
        self.action_data_output_none = QAction(MainWindow)
        self.action_data_output_none.setObjectName(u"action_data_output_none")
        self.action_data_output_none.setCheckable(True)
        self.action_data_output_stdio = QAction(MainWindow)
        self.action_data_output_stdio.setObjectName(u"action_data_output_stdio")
        self.action_data_output_stdio.setCheckable(True)
        self.action_data_output_file = QAction(MainWindow)
        self.action_data_output_file.setObjectName(u"action_data_output_file")
        self.action_data_output_file.setCheckable(True)
        self.action_execute_script = QAction(MainWindow)
        self.action_execute_script.setObjectName(u"action_execute_script")
        self.actionAll = QAction(MainWindow)
        self.actionAll.setObjectName(u"actionAll")
        self.actionNone = QAction(MainWindow)
        self.actionNone.setObjectName(u"actionNone")
        self.action_build_video_from_images = QAction(MainWindow)
        self.action_build_video_from_images.setObjectName(
            u"action_build_video_from_images"
        )
        self.action_new_script = QAction(MainWindow)
        self.action_new_script.setObjectName(u"action_new_script")
        icon1 = QIcon()
        icon1.addFile(
            u":/common/resources/New document.png", QSize(), QIcon.Normal, QIcon.Off
        )
        self.action_new_script.setIcon(icon1)
        self.action_load_script = QAction(MainWindow)
        self.action_load_script.setObjectName(u"action_load_script")
        icon2 = QIcon()
        icon2.addFile(u":/common/resources/Load.png", QSize(), QIcon.Normal, QIcon.Off)
        self.action_load_script.setIcon(icon2)
        self.action_save_script = QAction(MainWindow)
        self.action_save_script.setObjectName(u"action_save_script")
        icon3 = QIcon()
        icon3.addFile(u":/common/resources/Save.png", QSize(), QIcon.Normal, QIcon.Off)
        self.action_save_script.setIcon(icon3)
        self.action_add_roi_execute_after_pre_processing = QAction(MainWindow)
        self.action_add_roi_execute_after_pre_processing.setObjectName(
            u"action_add_roi_execute_after_pre_processing"
        )
        self.action_roi_execute_before_pre_processing = QAction(MainWindow)
        self.action_roi_execute_before_pre_processing.setObjectName(
            u"action_roi_execute_before_pre_processing"
        )
        self.action_roi_execute_after_pre_processing = QAction(MainWindow)
        self.action_roi_execute_after_pre_processing.setObjectName(
            u"action_roi_execute_after_pre_processing"
        )
        self.action_roi_execute_after_mask_merger = QAction(MainWindow)
        self.action_roi_execute_after_mask_merger.setObjectName(
            u"action_roi_execute_after_mask_merger"
        )
        self.act_view_anno_all = QAction(MainWindow)
        self.act_view_anno_all.setObjectName(u"act_view_anno_all")
        self.act_view_anno_none = QAction(MainWindow)
        self.act_view_anno_none.setObjectName(u"act_view_anno_none")
        self.act_view_anno_empty = QAction(MainWindow)
        self.act_view_anno_empty.setObjectName(u"act_view_anno_empty")
        self.act_view_anno_empty.setCheckable(True)
        self.act_view_anno_empty.setChecked(True)
        self.act_view_anno_info = QAction(MainWindow)
        self.act_view_anno_info.setObjectName(u"act_view_anno_info")
        self.act_view_anno_info.setCheckable(True)
        self.act_view_anno_info.setChecked(True)
        self.act_view_anno_ok = QAction(MainWindow)
        self.act_view_anno_ok.setObjectName(u"act_view_anno_ok")
        self.act_view_anno_ok.setCheckable(True)
        self.act_view_anno_ok.setChecked(True)
        self.act_view_anno_warning = QAction(MainWindow)
        self.act_view_anno_warning.setObjectName(u"act_view_anno_warning")
        self.act_view_anno_warning.setCheckable(True)
        self.act_view_anno_warning.setChecked(True)
        self.act_view_anno_error = QAction(MainWindow)
        self.act_view_anno_error.setObjectName(u"act_view_anno_error")
        self.act_view_anno_error.setCheckable(True)
        self.act_view_anno_error.setChecked(True)
        self.act_view_anno_critical = QAction(MainWindow)
        self.act_view_anno_critical.setObjectName(u"act_view_anno_critical")
        self.act_view_anno_critical.setCheckable(True)
        self.act_view_anno_critical.setChecked(True)
        self.act_view_anno_source_issue = QAction(MainWindow)
        self.act_view_anno_source_issue.setObjectName(u"act_view_anno_source_issue")
        self.act_view_anno_source_issue.setCheckable(True)
        self.act_view_anno_source_issue.setChecked(True)
        self.act_view_anno_unknown = QAction(MainWindow)
        self.act_view_anno_unknown.setObjectName(u"act_view_anno_unknown")
        self.act_view_anno_unknown.setCheckable(True)
        self.act_view_anno_unknown.setChecked(True)
        self.action_save_as_python_script = QAction(MainWindow)
        self.action_save_as_python_script.setObjectName(u"action_save_as_python_script")
        self.actionMerge_script_and_toolbox_panels = QAction(MainWindow)
        self.actionMerge_script_and_toolbox_panels.setObjectName(
            u"actionMerge_script_and_toolbox_panels"
        )
        self.actionPut_tools_widgets_in_scroll_panel = QAction(MainWindow)
        self.actionPut_tools_widgets_in_scroll_panel.setObjectName(
            u"actionPut_tools_widgets_in_scroll_panel"
        )
        self.actionAdd_auto_fill_in_grid_search = QAction(MainWindow)
        self.actionAdd_auto_fill_in_grid_search.setObjectName(
            u"actionAdd_auto_fill_in_grid_search"
        )
        self.actionAdd_buttons_to_add_tool_to_script_next_to_reset_button = QAction(
            MainWindow
        )
        self.actionAdd_buttons_to_add_tool_to_script_next_to_reset_button.setObjectName(
            u"actionAdd_buttons_to_add_tool_to_script_next_to_reset_button"
        )
        self.actionAdd_roi_to_check_mask_positioning = QAction(MainWindow)
        self.actionAdd_roi_to_check_mask_positioning.setObjectName(
            u"actionAdd_roi_to_check_mask_positioning"
        )
        self.actionFix_ROI_display_color_issue_for_rectangles = QAction(MainWindow)
        self.actionFix_ROI_display_color_issue_for_rectangles.setObjectName(
            u"actionFix_ROI_display_color_issue_for_rectangles"
        )
        self.actionAdd_more_colors_for_ROI = QAction(MainWindow)
        self.actionAdd_more_colors_for_ROI.setObjectName(u"actionAdd_more_colors_for_ROI")
        self.action_create_wrapper_before = QAction(MainWindow)
        self.action_create_wrapper_before.setObjectName(u"action_create_wrapper_before")
        self.action_create_wrapper_before.setCheckable(True)
        self.action_standard_object_oriented_call = QAction(MainWindow)
        self.action_standard_object_oriented_call.setObjectName(
            u"action_standard_object_oriented_call"
        )
        self.action_standard_object_oriented_call.setCheckable(True)
        self.action_object_oriented_wrapped_with_a_with_clause = QAction(MainWindow)
        self.action_object_oriented_wrapped_with_a_with_clause.setObjectName(
            u"action_object_oriented_wrapped_with_a_with_clause"
        )
        self.action_object_oriented_wrapped_with_a_with_clause.setCheckable(True)
        self.action_object_oriented_wrapped_with_a_with_clause.setChecked(False)
        self.action_functional_style = QAction(MainWindow)
        self.action_functional_style.setObjectName(u"action_functional_style")
        self.action_functional_style.setCheckable(True)
        self.action_functional_style.setChecked(True)
        self.action_functional_style.setEnabled(True)
        self.action_video_1_second = QAction(MainWindow)
        self.action_video_1_second.setObjectName(u"action_video_1_second")
        self.action_video_1_second.setCheckable(True)
        self.action_video_1_second.setChecked(True)
        self.action_video_1_24_second = QAction(MainWindow)
        self.action_video_1_24_second.setObjectName(u"action_video_1_24_second")
        self.action_video_1_24_second.setCheckable(True)
        self.action_video_1_24_second.setChecked(False)
        self.action_video_5_second = QAction(MainWindow)
        self.action_video_5_second.setObjectName(u"action_video_5_second")
        self.action_video_5_second.setCheckable(True)
        self.action_video_stack_and_jitter = QAction(MainWindow)
        self.action_video_stack_and_jitter.setObjectName(u"action_video_stack_and_jitter")
        self.action_video_stack_and_jitter.setCheckable(True)
        self.action_video_stack_and_jitter.setChecked(False)
        self.action_video_half_second = QAction(MainWindow)
        self.action_video_half_second.setObjectName(u"action_video_half_second")
        self.action_video_half_second.setCheckable(True)
        self.action_video_res_first_image = QAction(MainWindow)
        self.action_video_res_first_image.setObjectName(u"action_video_res_first_image")
        self.action_video_res_first_image.setCheckable(True)
        self.action_video_res_first_image.setChecked(True)
        self.action_video_res_1080p = QAction(MainWindow)
        self.action_video_res_1080p.setObjectName(u"action_video_res_1080p")
        self.action_video_res_1080p.setCheckable(True)
        self.action_video_res_720p = QAction(MainWindow)
        self.action_video_res_720p.setObjectName(u"action_video_res_720p")
        self.action_video_res_720p.setCheckable(True)
        self.action_video_res_576p = QAction(MainWindow)
        self.action_video_res_576p.setObjectName(u"action_video_res_576p")
        self.action_video_res_576p.setCheckable(True)
        self.action_video_res_480p = QAction(MainWindow)
        self.action_video_res_480p.setObjectName(u"action_video_res_480p")
        self.action_video_res_480p.setCheckable(True)
        self.action_video_res_376p = QAction(MainWindow)
        self.action_video_res_376p.setObjectName(u"action_video_res_376p")
        self.action_video_res_376p.setCheckable(True)
        self.action_video_res_240p = QAction(MainWindow)
        self.action_video_res_240p.setObjectName(u"action_video_res_240p")
        self.action_video_res_240p.setCheckable(True)
        self.action_video_ar_16_9 = QAction(MainWindow)
        self.action_video_ar_16_9.setObjectName(u"action_video_ar_16_9")
        self.action_video_ar_16_9.setCheckable(True)
        self.action_video_ar_16_9.setChecked(True)
        self.action_video_ar_4_3 = QAction(MainWindow)
        self.action_video_ar_4_3.setObjectName(u"action_video_ar_4_3")
        self.action_video_ar_4_3.setCheckable(True)
        self.action_video_ar_1_1 = QAction(MainWindow)
        self.action_video_ar_1_1.setObjectName(u"action_video_ar_1_1")
        self.action_video_ar_1_1.setCheckable(True)
        self.action_video_bkg_color_black = QAction(MainWindow)
        self.action_video_bkg_color_black.setObjectName(u"action_video_bkg_color_black")
        self.action_video_bkg_color_black.setCheckable(True)
        self.action_video_bkg_color_black.setChecked(True)
        self.action_video_bkg_color_white = QAction(MainWindow)
        self.action_video_bkg_color_white.setObjectName(u"action_video_bkg_color_white")
        self.action_video_bkg_color_white.setCheckable(True)
        self.action_video_bkg_color_silver = QAction(MainWindow)
        self.action_video_bkg_color_silver.setObjectName(u"action_video_bkg_color_silver")
        self.action_video_bkg_color_silver.setCheckable(True)
        self.act_parse_folder_memory = QAction(MainWindow)
        self.act_parse_folder_memory.setObjectName(u"act_parse_folder_memory")
        self.act_clean_parsed_folders = QAction(MainWindow)
        self.act_clean_parsed_folders.setObjectName(u"act_clean_parsed_folders")
        self.actionplace_holder = QAction(MainWindow)
        self.actionplace_holder.setObjectName(u"actionplace_holder")
        self.actionplace_holder_2 = QAction(MainWindow)
        self.actionplace_holder_2.setObjectName(u"actionplace_holder_2")
        self.action_add_exposure_fixer = QAction(MainWindow)
        self.action_add_exposure_fixer.setObjectName(u"action_add_exposure_fixer")
        self.action_add_feature_extractor = QAction(MainWindow)
        self.action_add_feature_extractor.setObjectName(u"action_add_feature_extractor")
        self.action_about_form = QAction(MainWindow)
        self.action_about_form.setObjectName(u"action_about_form")
        self.action_show_documentation = QAction(MainWindow)
        self.action_show_documentation.setObjectName(u"action_show_documentation")
        self.action_use_dark_theme = QAction(MainWindow)
        self.action_use_dark_theme.setObjectName(u"action_use_dark_theme")
        self.action_use_dark_theme.setCheckable(True)
        self.action_use_dark_theme.setChecked(True)
        self.action_build_tool_documentation = QAction(MainWindow)
        self.action_build_tool_documentation.setObjectName(
            u"action_build_tool_documentation"
        )
        self.action_build_ipso_phen_documentation = QAction(MainWindow)
        self.action_build_ipso_phen_documentation.setObjectName(
            u"action_build_ipso_phen_documentation"
        )
        self.action_show_read_me = QAction(MainWindow)
        self.action_show_read_me.setObjectName(u"action_show_read_me")
        self.action_build_missing_tools_documentation = QAction(MainWindow)
        self.action_build_missing_tools_documentation.setObjectName(
            u"action_build_missing_tools_documentation"
        )
        self.action_new_tool = QAction(MainWindow)
        self.action_new_tool.setObjectName(u"action_new_tool")
        self.action_use_multithreading = QAction(MainWindow)
        self.action_use_multithreading.setObjectName(u"action_use_multithreading")
        self.action_use_multithreading.setCheckable(True)
        self.action_use_multithreading.setChecked(True)
        self.action_use_pipeline_cache = QAction(MainWindow)
        self.action_use_pipeline_cache.setObjectName(u"action_use_pipeline_cache")
        self.action_use_pipeline_cache.setCheckable(True)
        self.action_use_pipeline_cache.setChecked(True)
        self.action_show_log = QAction(MainWindow)
        self.action_show_log.setObjectName(u"action_show_log")
        self.action_show_log.setCheckable(True)
        self.action_show_log.setChecked(True)
        self.action_de_load_csv = QAction(MainWindow)
        self.action_de_load_csv.setObjectName(u"action_de_load_csv")
        self.action_de_new_sheet = QAction(MainWindow)
        self.action_de_new_sheet.setObjectName(u"action_de_new_sheet")
        self.action_de_create_sheet_from_selection = QAction(MainWindow)
        self.action_de_create_sheet_from_selection.setObjectName(
            u"action_de_create_sheet_from_selection"
        )
        self.action_de_create_sheet_from_query = QAction(MainWindow)
        self.action_de_create_sheet_from_query.setObjectName(
            u"action_de_create_sheet_from_query"
        )
        self.action_de_add_column = QAction(MainWindow)
        self.action_de_add_column.setObjectName(u"action_de_add_column")
        self.action_de_delete_column = QAction(MainWindow)
        self.action_de_delete_column.setObjectName(u"action_de_delete_column")
        self.action_de_save_csv = QAction(MainWindow)
        self.action_de_save_csv.setObjectName(u"action_de_save_csv")
        self.action_save_image_list = QAction(MainWindow)
        self.action_save_image_list.setObjectName(u"action_save_image_list")
        self.action_load_image_list = QAction(MainWindow)
        self.action_load_image_list.setObjectName(u"action_load_image_list")
        self.act_settings_sir_keep = QAction(MainWindow)
        self.act_settings_sir_keep.setObjectName(u"act_settings_sir_keep")
        self.act_settings_sir_keep.setCheckable(True)
        self.act_settings_sir_keep.setChecked(True)
        self.act_settings_sir_2x = QAction(MainWindow)
        self.act_settings_sir_2x.setObjectName(u"act_settings_sir_2x")
        self.act_settings_sir_2x.setCheckable(True)
        self.act_settings_sir_3x = QAction(MainWindow)
        self.act_settings_sir_3x.setObjectName(u"act_settings_sir_3x")
        self.act_settings_sir_3x.setCheckable(True)
        self.act_settings_sir_4x = QAction(MainWindow)
        self.act_settings_sir_4x.setObjectName(u"act_settings_sir_4x")
        self.act_settings_sir_4x.setCheckable(True)
        self.act_settings_sir_5x = QAction(MainWindow)
        self.act_settings_sir_5x.setObjectName(u"act_settings_sir_5x")
        self.act_settings_sir_5x.setCheckable(True)
        self.act_settings_sir_6x = QAction(MainWindow)
        self.act_settings_sir_6x.setObjectName(u"act_settings_sir_6x")
        self.act_settings_sir_6x.setCheckable(True)
        self.action_save_pipeline_processor_state = QAction(MainWindow)
        self.action_save_pipeline_processor_state.setObjectName(
            u"action_save_pipeline_processor_state"
        )
        self.action_add_image_generator = QAction(MainWindow)
        self.action_add_image_generator.setObjectName(u"action_add_image_generator")
        self.action_build_test_files = QAction(MainWindow)
        self.action_build_test_files.setObjectName(u"action_build_test_files")
        self.action_add_white_balance_corrector = QAction(MainWindow)
        self.action_add_white_balance_corrector.setObjectName(
            u"action_add_white_balance_corrector"
        )
        self.action_build_roi_with_raw_image = QAction(MainWindow)
        self.action_build_roi_with_raw_image.setObjectName(
            u"action_build_roi_with_raw_image"
        )
        self.action_build_roi_with_pre_processed_image = QAction(MainWindow)
        self.action_build_roi_with_pre_processed_image.setObjectName(
            u"action_build_roi_with_pre_processed_image"
        )
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout_2 = QVBoxLayout(self.centralwidget)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setTabPosition(QTabWidget.North)
        self.tabWidget.setTabShape(QTabWidget.Rounded)
        self.tab_pipeline_builder = QWidget()
        self.tab_pipeline_builder.setObjectName(u"tab_pipeline_builder")
        self.verticalLayout_3 = QVBoxLayout(self.tab_pipeline_builder)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.chk_experiment = QCheckBox(self.tab_pipeline_builder)
        self.chk_experiment.setObjectName(u"chk_experiment")
        font1 = QFont()
        font1.setBold(False)
        font1.setWeight(50)
        self.chk_experiment.setFont(font1)
        self.chk_experiment.setLayoutDirection(Qt.RightToLeft)
        self.chk_experiment.setChecked(True)

        self.horizontalLayout_5.addWidget(self.chk_experiment)

        self.cb_experiment = QComboBox(self.tab_pipeline_builder)
        self.cb_experiment.setObjectName(u"cb_experiment")
        self.cb_experiment.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.horizontalLayout_5.addWidget(self.cb_experiment)

        self.chk_plant = QCheckBox(self.tab_pipeline_builder)
        self.chk_plant.setObjectName(u"chk_plant")
        self.chk_plant.setFont(font1)
        self.chk_plant.setLayoutDirection(Qt.RightToLeft)
        self.chk_plant.setChecked(True)

        self.horizontalLayout_5.addWidget(self.chk_plant)

        self.cb_plant = QComboBox(self.tab_pipeline_builder)
        self.cb_plant.setObjectName(u"cb_plant")
        self.cb_plant.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.horizontalLayout_5.addWidget(self.cb_plant)

        self.chk_date = QCheckBox(self.tab_pipeline_builder)
        self.chk_date.setObjectName(u"chk_date")
        self.chk_date.setFont(font1)
        self.chk_date.setLayoutDirection(Qt.RightToLeft)
        self.chk_date.setChecked(True)

        self.horizontalLayout_5.addWidget(self.chk_date)

        self.cb_date = QComboBox(self.tab_pipeline_builder)
        self.cb_date.setObjectName(u"cb_date")
        self.cb_date.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.horizontalLayout_5.addWidget(self.cb_date)

        self.chk_camera = QCheckBox(self.tab_pipeline_builder)
        self.chk_camera.setObjectName(u"chk_camera")
        self.chk_camera.setFont(font1)
        self.chk_camera.setLayoutDirection(Qt.RightToLeft)
        self.chk_camera.setChecked(True)

        self.horizontalLayout_5.addWidget(self.chk_camera)

        self.cb_camera = QComboBox(self.tab_pipeline_builder)
        self.cb_camera.setObjectName(u"cb_camera")
        self.cb_camera.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.horizontalLayout_5.addWidget(self.cb_camera)

        self.chk_angle = QCheckBox(self.tab_pipeline_builder)
        self.chk_angle.setObjectName(u"chk_angle")
        self.chk_angle.setFont(font1)
        self.chk_angle.setLayoutDirection(Qt.RightToLeft)
        self.chk_angle.setChecked(True)

        self.horizontalLayout_5.addWidget(self.chk_angle)

        self.cb_angle = QComboBox(self.tab_pipeline_builder)
        self.cb_angle.setObjectName(u"cb_angle")
        self.cb_angle.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.horizontalLayout_5.addWidget(self.cb_angle)

        self.chk_wavelength = QCheckBox(self.tab_pipeline_builder)
        self.chk_wavelength.setObjectName(u"chk_wavelength")
        self.chk_wavelength.setLayoutDirection(Qt.RightToLeft)
        self.chk_wavelength.setChecked(True)

        self.horizontalLayout_5.addWidget(self.chk_wavelength)

        self.cb_wavelength = QComboBox(self.tab_pipeline_builder)
        self.cb_wavelength.setObjectName(u"cb_wavelength")
        self.cb_wavelength.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.horizontalLayout_5.addWidget(self.cb_wavelength)

        self.chk_time = QCheckBox(self.tab_pipeline_builder)
        self.chk_time.setObjectName(u"chk_time")
        self.chk_time.setMinimumSize(QSize(0, 0))
        self.chk_time.setFont(font1)
        self.chk_time.setLayoutDirection(Qt.RightToLeft)
        self.chk_time.setChecked(True)

        self.horizontalLayout_5.addWidget(self.chk_time)

        self.cb_time = QComboBox(self.tab_pipeline_builder)
        self.cb_time.setObjectName(u"cb_time")
        self.cb_time.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.horizontalLayout_5.addWidget(self.cb_time)

        self.horizontalSpacer_2 = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum
        )

        self.horizontalLayout_5.addItem(self.horizontalSpacer_2)

        self.verticalLayout_3.addLayout(self.horizontalLayout_5)

        self.spl_pb_ver_main = QSplitter(self.tab_pipeline_builder)
        self.spl_pb_ver_main.setObjectName(u"spl_pb_ver_main")
        self.spl_pb_ver_main.setOrientation(Qt.Horizontal)
        self.frame_5 = QFrame(self.spl_pb_ver_main)
        self.frame_5.setObjectName(u"frame_5")
        self.frame_5.setFrameShape(QFrame.NoFrame)
        self.frame_5.setFrameShadow(QFrame.Plain)
        self.frame_5.setLineWidth(1)
        self.horizontalLayout_7 = QHBoxLayout(self.frame_5)
        self.horizontalLayout_7.setSpacing(0)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.horizontalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.spl_hor_pb_left = QSplitter(self.frame_5)
        self.spl_hor_pb_left.setObjectName(u"spl_hor_pb_left")
        self.spl_hor_pb_left.setFrameShape(QFrame.NoFrame)
        self.spl_hor_pb_left.setOrientation(Qt.Vertical)
        self.spl_hor_pb_left.setOpaqueResize(True)
        self.frame_4 = QFrame(self.spl_hor_pb_left)
        self.frame_4.setObjectName(u"frame_4")
        self.frame_4.setFrameShape(QFrame.NoFrame)
        self.frame_4.setFrameShadow(QFrame.Raised)
        self.frame_4.setLineWidth(0)
        self.gridLayout_18 = QGridLayout(self.frame_4)
        self.gridLayout_18.setSpacing(0)
        self.gridLayout_18.setObjectName(u"gridLayout_18")
        self.gridLayout_18.setContentsMargins(0, 4, 8, 4)
        self.bt_add_random = QPushButton(self.frame_4)
        self.bt_add_random.setObjectName(u"bt_add_random")

        self.gridLayout_18.addWidget(self.bt_add_random, 0, 7, 1, 1)

        self.tv_image_browser = QTableView(self.frame_4)
        self.tv_image_browser.setObjectName(u"tv_image_browser")
        self.tv_image_browser.setAlternatingRowColors(False)
        self.tv_image_browser.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tv_image_browser.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.tv_image_browser.verticalHeader().setProperty("showSortIndicator", False)

        self.gridLayout_18.addWidget(self.tv_image_browser, 1, 0, 1, 10)

        self.bt_remove_from_selection = QPushButton(self.frame_4)
        self.bt_remove_from_selection.setObjectName(u"bt_remove_from_selection")

        self.gridLayout_18.addWidget(self.bt_remove_from_selection, 0, 2, 1, 1)

        self.bt_keep_annotated = QPushButton(self.frame_4)
        self.bt_keep_annotated.setObjectName(u"bt_keep_annotated")

        self.gridLayout_18.addWidget(self.bt_keep_annotated, 0, 3, 1, 1)

        self.lbl_selection = QLabel(self.frame_4)
        self.lbl_selection.setObjectName(u"lbl_selection")
        self.lbl_selection.setFont(font1)

        self.gridLayout_18.addWidget(self.lbl_selection, 0, 0, 1, 1)

        self.bt_add_to_selection = QPushButton(self.frame_4)
        self.bt_add_to_selection.setObjectName(u"bt_add_to_selection")

        self.gridLayout_18.addWidget(self.bt_add_to_selection, 0, 1, 1, 1)

        self.bt_clear_selection = QPushButton(self.frame_4)
        self.bt_clear_selection.setObjectName(u"bt_clear_selection")

        self.gridLayout_18.addWidget(self.bt_clear_selection, 0, 5, 1, 1)

        self.horizontalSpacer_3 = QSpacerItem(
            190, 20, QSizePolicy.Expanding, QSizePolicy.Minimum
        )

        self.gridLayout_18.addItem(self.horizontalSpacer_3, 0, 6, 1, 1)

        self.sp_add_random_count = QSpinBox(self.frame_4)
        self.sp_add_random_count.setObjectName(u"sp_add_random_count")
        self.sp_add_random_count.setMaximum(10000)

        self.gridLayout_18.addWidget(self.sp_add_random_count, 0, 8, 1, 1)

        self.pushButton = QPushButton(self.frame_4)
        self.pushButton.setObjectName(u"pushButton")

        self.gridLayout_18.addWidget(self.pushButton, 0, 4, 1, 1)

        self.spl_hor_pb_left.addWidget(self.frame_4)
        self.frame_3 = QFrame(self.spl_hor_pb_left)
        self.frame_3.setObjectName(u"frame_3")
        self.frame_3.setFrameShape(QFrame.NoFrame)
        self.frame_3.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.frame_3)
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 4, 4, 4)
        self.tw_tool_box = QTabWidget(self.frame_3)
        self.tw_tool_box.setObjectName(u"tw_tool_box")
        self.tw_tool_box.setMinimumSize(QSize(0, 0))
        self.tw_tool_box.setMaximumSize(QSize(16777215, 16777215))
        self.tw_tool_box.setTabShape(QTabWidget.Rounded)
        self.tw_tool_box.setDocumentMode(False)
        self.tw_tool_box.setTabBarAutoHide(False)
        self.tb_annotations = QWidget()
        self.tb_annotations.setObjectName(u"tb_annotations")
        self.gridLayout_4 = QGridLayout(self.tb_annotations)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.label_3 = QLabel(self.tb_annotations)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout_4.addWidget(self.label_3, 1, 0, 1, 1)

        self.te_annotations = QTextEdit(self.tb_annotations)
        self.te_annotations.setObjectName(u"te_annotations")

        self.gridLayout_4.addWidget(self.te_annotations, 5, 0, 1, 4)

        self.cb_annotation_level = QComboBox(self.tb_annotations)
        icon4 = QIcon()
        icon4.addFile(
            u":/annotation_level/resources/Info.png", QSize(), QIcon.Normal, QIcon.On
        )
        self.cb_annotation_level.addItem(icon4, "")
        icon5 = QIcon()
        icon5.addFile(
            u":/annotation_level/resources/OK.png", QSize(), QIcon.Normal, QIcon.On
        )
        self.cb_annotation_level.addItem(icon5, "")
        icon6 = QIcon()
        icon6.addFile(
            u":/annotation_level/resources/Warning.png", QSize(), QIcon.Normal, QIcon.On
        )
        self.cb_annotation_level.addItem(icon6, "")
        icon7 = QIcon()
        icon7.addFile(
            u":/annotation_level/resources/Error.png", QSize(), QIcon.Normal, QIcon.On
        )
        self.cb_annotation_level.addItem(icon7, "")
        icon8 = QIcon()
        icon8.addFile(
            u":/annotation_level/resources/Danger.png", QSize(), QIcon.Normal, QIcon.On
        )
        self.cb_annotation_level.addItem(icon8, "")
        icon9 = QIcon()
        icon9.addFile(
            u":/annotation_level/resources/Problem.png", QSize(), QIcon.Normal, QIcon.On
        )
        self.cb_annotation_level.addItem(icon9, "")
        icon10 = QIcon()
        icon10.addFile(
            u":/annotation_level/resources/Help.png", QSize(), QIcon.Normal, QIcon.On
        )
        self.cb_annotation_level.addItem(icon10, "")
        self.cb_annotation_level.setObjectName(u"cb_annotation_level")
        self.cb_annotation_level.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.gridLayout_4.addWidget(self.cb_annotation_level, 1, 1, 1, 1)

        self.bt_delete_annotation = QToolButton(self.tb_annotations)
        self.bt_delete_annotation.setObjectName(u"bt_delete_annotation")
        icon11 = QIcon()
        icon11.addFile(
            u":/annotation_level/resources/Delete.png", QSize(), QIcon.Normal, QIcon.On
        )
        self.bt_delete_annotation.setIcon(icon11)
        self.bt_delete_annotation.setIconSize(QSize(24, 24))

        self.gridLayout_4.addWidget(self.bt_delete_annotation, 1, 3, 1, 1)

        self.horizontalSpacer = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum
        )

        self.gridLayout_4.addItem(self.horizontalSpacer, 1, 2, 1, 1)

        self.tw_tool_box.addTab(self.tb_annotations, "")
        self.tb_last_batch = QWidget()
        self.tb_last_batch.setObjectName(u"tb_last_batch")
        self.gridLayout_9 = QGridLayout(self.tb_last_batch)
        self.gridLayout_9.setObjectName(u"gridLayout_9")
        self.horizontalSpacer_10 = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum
        )

        self.gridLayout_9.addItem(self.horizontalSpacer_10, 1, 1, 1, 1)

        self.bt_set_batch_as_selection = QPushButton(self.tb_last_batch)
        self.bt_set_batch_as_selection.setObjectName(u"bt_set_batch_as_selection")

        self.gridLayout_9.addWidget(self.bt_set_batch_as_selection, 1, 0, 1, 1)

        self.lw_last_batch = QListWidget(self.tb_last_batch)
        self.lw_last_batch.setObjectName(u"lw_last_batch")

        self.gridLayout_9.addWidget(self.lw_last_batch, 0, 0, 1, 2)

        self.tw_tool_box.addTab(self.tb_last_batch, "")
        self.tb_statistics = QWidget()
        self.tb_statistics.setObjectName(u"tb_statistics")
        self.gridLayout_8 = QGridLayout(self.tb_statistics)
        self.gridLayout_8.setObjectName(u"gridLayout_8")
        self.lv_stats = QTextBrowser(self.tb_statistics)
        self.lv_stats.setObjectName(u"lv_stats")
        font2 = QFont()
        font2.setFamily(u"Courier")
        self.lv_stats.setFont(font2)

        self.gridLayout_8.addWidget(self.lv_stats, 0, 0, 1, 4)

        self.bt_update_selection_stats = QPushButton(self.tb_statistics)
        self.bt_update_selection_stats.setObjectName(u"bt_update_selection_stats")

        self.gridLayout_8.addWidget(self.bt_update_selection_stats, 1, 0, 1, 1)

        self.bt_clear_statistics = QPushButton(self.tb_statistics)
        self.bt_clear_statistics.setObjectName(u"bt_clear_statistics")

        self.gridLayout_8.addWidget(self.bt_clear_statistics, 1, 3, 1, 1)

        self.horizontalSpacer_5 = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum
        )

        self.gridLayout_8.addItem(self.horizontalSpacer_5, 1, 2, 1, 1)

        self.cb_stat_include_annotations = QCheckBox(self.tb_statistics)
        self.cb_stat_include_annotations.setObjectName(u"cb_stat_include_annotations")

        self.gridLayout_8.addWidget(self.cb_stat_include_annotations, 1, 1, 1, 1)

        self.tw_tool_box.addTab(self.tb_statistics, "")

        self.horizontalLayout_2.addWidget(self.tw_tool_box)

        self.spl_hor_pb_left.addWidget(self.frame_3)
        self.frame_2 = QFrame(self.spl_hor_pb_left)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setFrameShape(QFrame.NoFrame)
        self.frame_2.setFrameShadow(QFrame.Raised)
        self.horizontalLayout = QHBoxLayout(self.frame_2)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 4, 4, 4)
        self.gridLayout_16 = QGridLayout()
        self.gridLayout_16.setObjectName(u"gridLayout_16")
        self.label = QLabel(self.frame_2)
        self.label.setObjectName(u"label")
        font3 = QFont()
        font3.setBold(True)
        font3.setWeight(75)
        self.label.setFont(font3)
        self.label.setAlignment(Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter)

        self.gridLayout_16.addWidget(self.label, 1, 0, 1, 1)

        self.sb_batch_count = QSpinBox(self.frame_2)
        self.sb_batch_count.setObjectName(u"sb_batch_count")
        self.sb_batch_count.setMaximumSize(QSize(50, 16777215))
        self.sb_batch_count.setMaximum(62735)

        self.gridLayout_16.addWidget(self.sb_batch_count, 1, 2, 1, 1)

        self.cb_batch_mode = QComboBox(self.frame_2)
        self.cb_batch_mode.addItem("")
        self.cb_batch_mode.addItem("")
        self.cb_batch_mode.addItem("")
        self.cb_batch_mode.setObjectName(u"cb_batch_mode")
        self.cb_batch_mode.setMaximumSize(QSize(200, 16777215))

        self.gridLayout_16.addWidget(self.cb_batch_mode, 1, 1, 1, 1)

        self.bt_launch_batch = QToolButton(self.frame_2)
        self.bt_launch_batch.setObjectName(u"bt_launch_batch")
        icon12 = QIcon()
        icon12.addFile(
            u":/image_process/resources/Play.png", QSize(), QIcon.Normal, QIcon.On
        )
        self.bt_launch_batch.setIcon(icon12)
        self.bt_launch_batch.setIconSize(QSize(24, 24))

        self.gridLayout_16.addWidget(self.bt_launch_batch, 1, 3, 1, 1)

        self.tb_tool_script = QTabWidget(self.frame_2)
        self.tb_tool_script.setObjectName(u"tb_tool_script")
        self.tb_pipeline_v2 = QWidget()
        self.tb_pipeline_v2.setObjectName(u"tb_pipeline_v2")
        self.gridLayout_15 = QGridLayout(self.tb_pipeline_v2)
        self.gridLayout_15.setObjectName(u"gridLayout_15")
        self.bt_pp_new = QPushButton(self.tb_pipeline_v2)
        self.bt_pp_new.setObjectName(u"bt_pp_new")
        self.bt_pp_new.setIcon(icon1)

        self.gridLayout_15.addWidget(self.bt_pp_new, 0, 0, 1, 1)

        self.bt_pp_load = QPushButton(self.tb_pipeline_v2)
        self.bt_pp_load.setObjectName(u"bt_pp_load")
        self.bt_pp_load.setIcon(icon2)

        self.gridLayout_15.addWidget(self.bt_pp_load, 0, 1, 1, 1)

        self.bt_pp_save = QPushButton(self.tb_pipeline_v2)
        self.bt_pp_save.setObjectName(u"bt_pp_save")
        self.bt_pp_save.setIcon(icon3)

        self.gridLayout_15.addWidget(self.bt_pp_save, 0, 2, 1, 1)

        self.horizontalSpacer_8 = QSpacerItem(
            13, 20, QSizePolicy.Fixed, QSizePolicy.Minimum
        )

        self.gridLayout_15.addItem(self.horizontalSpacer_8, 0, 3, 1, 1)

        self.bt_pp_up = QPushButton(self.tb_pipeline_v2)
        self.bt_pp_up.setObjectName(u"bt_pp_up")
        icon13 = QIcon()
        icon13.addFile(u":/common/resources/Up.png", QSize(), QIcon.Normal, QIcon.Off)
        self.bt_pp_up.setIcon(icon13)

        self.gridLayout_15.addWidget(self.bt_pp_up, 0, 4, 1, 1)

        self.bt_pp_down = QPushButton(self.tb_pipeline_v2)
        self.bt_pp_down.setObjectName(u"bt_pp_down")
        icon14 = QIcon()
        icon14.addFile(u":/common/resources/Down.png", QSize(), QIcon.Normal, QIcon.Off)
        self.bt_pp_down.setIcon(icon14)

        self.gridLayout_15.addWidget(self.bt_pp_down, 0, 5, 1, 1)

        self.horizontalSpacer_15 = QSpacerItem(
            13, 20, QSizePolicy.Fixed, QSizePolicy.Minimum
        )

        self.gridLayout_15.addItem(self.horizontalSpacer_15, 0, 6, 1, 1)

        self.bt_pp_delete = QPushButton(self.tb_pipeline_v2)
        self.bt_pp_delete.setObjectName(u"bt_pp_delete")
        icon15 = QIcon()
        icon15.addFile(
            u":/annotation_level/resources/Delete.png", QSize(), QIcon.Normal, QIcon.Off
        )
        self.bt_pp_delete.setIcon(icon15)

        self.gridLayout_15.addWidget(self.bt_pp_delete, 0, 7, 1, 1)

        self.horizontalSpacer_14 = QSpacerItem(
            13, 20, QSizePolicy.Fixed, QSizePolicy.Minimum
        )

        self.gridLayout_15.addItem(self.horizontalSpacer_14, 0, 8, 1, 1)

        self.bt_pp_select_tool = QPushButton(self.tb_pipeline_v2)
        self.bt_pp_select_tool.setObjectName(u"bt_pp_select_tool")
        self.bt_pp_select_tool.setMaximumSize(QSize(28, 16777215))
        self.bt_pp_select_tool.setContextMenuPolicy(Qt.DefaultContextMenu)
        icon16 = QIcon()
        icon16.addFile(u":/common/resources/Add.png", QSize(), QIcon.Normal, QIcon.Off)
        self.bt_pp_select_tool.setIcon(icon16)
        self.bt_pp_select_tool.setFlat(False)

        self.gridLayout_15.addWidget(self.bt_pp_select_tool, 0, 9, 1, 1)

        self.horizontalSpacer_13 = QSpacerItem(
            13, 20, QSizePolicy.Fixed, QSizePolicy.Minimum
        )

        self.gridLayout_15.addItem(self.horizontalSpacer_13, 0, 10, 1, 1)

        self.bt_pp_invalidate = QPushButton(self.tb_pipeline_v2)
        self.bt_pp_invalidate.setObjectName(u"bt_pp_invalidate")
        icon17 = QIcon()
        icon17.addFile(
            u":/common/resources/Refresh.png", QSize(), QIcon.Normal, QIcon.Off
        )
        self.bt_pp_invalidate.setIcon(icon17)

        self.gridLayout_15.addWidget(self.bt_pp_invalidate, 0, 11, 1, 1)

        self.bt_pp_run = QToolButton(self.tb_pipeline_v2)
        self.bt_pp_run.setObjectName(u"bt_pp_run")
        self.bt_pp_run.setIcon(icon12)
        self.bt_pp_run.setIconSize(QSize(24, 24))

        self.gridLayout_15.addWidget(self.bt_pp_run, 0, 12, 1, 1)

        self.pb_pp_progress = QProgressBar(self.tb_pipeline_v2)
        self.pb_pp_progress.setObjectName(u"pb_pp_progress")
        self.pb_pp_progress.setMinimumSize(QSize(0, 0))
        self.pb_pp_progress.setMaximumSize(QSize(16777215, 16777215))
        self.pb_pp_progress.setValue(0)
        self.pb_pp_progress.setTextVisible(False)
        self.pb_pp_progress.setTextDirection(QProgressBar.BottomToTop)

        self.gridLayout_15.addWidget(self.pb_pp_progress, 0, 13, 1, 1)

        self.tv_pp_view = QTreeView(self.tb_pipeline_v2)
        self.tv_pp_view.setObjectName(u"tv_pp_view")
        self.tv_pp_view.setAlternatingRowColors(False)
        self.tv_pp_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tv_pp_view.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.tv_pp_view.setAnimated(False)
        self.tv_pp_view.header().setVisible(False)

        self.gridLayout_15.addWidget(self.tv_pp_view, 1, 0, 1, 14)

        self.tb_tool_script.addTab(self.tb_pipeline_v2, "")
        self.tab_tools = QWidget()
        self.tab_tools.setObjectName(u"tab_tools")
        self.gridLayout_3 = QGridLayout(self.tab_tools)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.bt_process_image = QPushButton(self.tab_tools)
        self.bt_process_image.setObjectName(u"bt_process_image")
        self.bt_process_image.setIcon(icon12)
        self.bt_process_image.setIconSize(QSize(24, 24))

        self.gridLayout_3.addWidget(self.bt_process_image, 0, 7, 1, 1)

        self.bt_reset_op = QPushButton(self.tab_tools)
        self.bt_reset_op.setObjectName(u"bt_reset_op")
        self.bt_reset_op.setIcon(icon17)
        self.bt_reset_op.setIconSize(QSize(24, 24))

        self.gridLayout_3.addWidget(self.bt_reset_op, 0, 5, 1, 1)

        self.bt_select_tool = QPushButton(self.tab_tools)
        self.bt_select_tool.setObjectName(u"bt_select_tool")
        self.bt_select_tool.setFlat(False)

        self.gridLayout_3.addWidget(self.bt_select_tool, 0, 1, 1, 1)

        self.horizontalSpacer_11 = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum
        )

        self.gridLayout_3.addItem(self.horizontalSpacer_11, 0, 4, 1, 1)

        self.scrollArea_2 = QScrollArea(self.tab_tools)
        self.scrollArea_2.setObjectName(u"scrollArea_2")
        self.scrollArea_2.setFrameShape(QFrame.HLine)
        self.scrollArea_2.setFrameShadow(QFrame.Plain)
        self.scrollArea_2.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scrollArea_2.setWidgetResizable(True)
        self.scrollAreaWidgetContents_4 = QWidget()
        self.scrollAreaWidgetContents_4.setObjectName(u"scrollAreaWidgetContents_4")
        self.scrollAreaWidgetContents_4.setGeometry(QRect(0, 0, 692, 148))
        self.gridLayout_17 = QGridLayout(self.scrollAreaWidgetContents_4)
        self.gridLayout_17.setObjectName(u"gridLayout_17")
        self.gl_tool_params = QGridLayout()
        self.gl_tool_params.setObjectName(u"gl_tool_params")

        self.gridLayout_17.addLayout(self.gl_tool_params, 0, 0, 1, 1)

        self.verticalSpacer = QSpacerItem(
            20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding
        )

        self.gridLayout_17.addItem(self.verticalSpacer, 1, 0, 1, 1)

        self.scrollArea_2.setWidget(self.scrollAreaWidgetContents_4)

        self.gridLayout_3.addWidget(self.scrollArea_2, 1, 0, 1, 8)

        self.bt_tool_help = QPushButton(self.tab_tools)
        self.bt_tool_help.setObjectName(u"bt_tool_help")
        icon18 = QIcon()
        icon18.addFile(
            u":/annotation_level/resources/Help.png", QSize(), QIcon.Normal, QIcon.Off
        )
        self.bt_tool_help.setIcon(icon18)

        self.gridLayout_3.addWidget(self.bt_tool_help, 0, 2, 1, 1)

        self.bt_tool_show_code = QPushButton(self.tab_tools)
        self.bt_tool_show_code.setObjectName(u"bt_tool_show_code")

        self.gridLayout_3.addWidget(self.bt_tool_show_code, 0, 3, 1, 1)

        self.tb_tool_script.addTab(self.tab_tools, "")

        self.gridLayout_16.addWidget(self.tb_tool_script, 0, 0, 1, 4)

        self.horizontalLayout.addLayout(self.gridLayout_16)

        self.spl_hor_pb_left.addWidget(self.frame_2)

        self.horizontalLayout_7.addWidget(self.spl_hor_pb_left)

        self.spl_pb_ver_main.addWidget(self.frame_5)
        self.frame = QFrame(self.spl_pb_ver_main)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.NoFrame)
        self.frame.setFrameShadow(QFrame.Plain)
        self.verticalLayout = QVBoxLayout(self.frame)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.bt_clear_result = QPushButton(self.frame)
        self.bt_clear_result.setObjectName(u"bt_clear_result")
        self.bt_clear_result.setMaximumSize(QSize(100, 16777215))

        self.horizontalLayout_6.addWidget(self.bt_clear_result)

        self.cb_available_outputs = QComboBox(self.frame)
        self.cb_available_outputs.setObjectName(u"cb_available_outputs")
        self.cb_available_outputs.setMaxVisibleItems(30)
        self.cb_available_outputs.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.horizontalLayout_6.addWidget(self.cb_available_outputs)

        self.bt_set_as_selected = QPushButton(self.frame)
        self.bt_set_as_selected.setObjectName(u"bt_set_as_selected")
        self.bt_set_as_selected.setMaximumSize(QSize(140, 16777215))

        self.horizontalLayout_6.addWidget(self.bt_set_as_selected)

        self.verticalLayout.addLayout(self.horizontalLayout_6)

        self.spl_ver_src_res_data = QSplitter(self.frame)
        self.spl_ver_src_res_data.setObjectName(u"spl_ver_src_res_data")
        self.spl_ver_src_res_data.setOrientation(Qt.Horizontal)
        self.frm_src_and_data = QFrame(self.spl_ver_src_res_data)
        self.frm_src_and_data.setObjectName(u"frm_src_and_data")
        self.frm_src_and_data.setFrameShape(QFrame.StyledPanel)
        self.frm_src_and_data.setFrameShadow(QFrame.Raised)
        self.frm_src_and_data.setLineWidth(1)
        self.verticalLayout_5 = QVBoxLayout(self.frm_src_and_data)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.spl_hor_src_data_params = QSplitter(self.frm_src_and_data)
        self.spl_hor_src_data_params.setObjectName(u"spl_hor_src_data_params")
        self.spl_hor_src_data_params.setOrientation(Qt.Vertical)
        self.frm_src_img = QFrame(self.spl_hor_src_data_params)
        self.frm_src_img.setObjectName(u"frm_src_img")
        self.frm_src_img.setFrameShape(QFrame.StyledPanel)
        self.frm_src_img.setFrameShadow(QFrame.Raised)
        self.spl_hor_src_data_params.addWidget(self.frm_src_img)
        self.frm_data = QFrame(self.spl_hor_src_data_params)
        self.frm_data.setObjectName(u"frm_data")
        self.frm_data.setFrameShape(QFrame.StyledPanel)
        self.frm_data.setFrameShadow(QFrame.Raised)
        self.spl_hor_src_data_params.addWidget(self.frm_data)
        self.frm_params = QFrame(self.spl_hor_src_data_params)
        self.frm_params.setObjectName(u"frm_params")
        self.frm_params.setFrameShape(QFrame.StyledPanel)
        self.frm_params.setFrameShadow(QFrame.Raised)
        self.spl_hor_src_data_params.addWidget(self.frm_params)

        self.verticalLayout_5.addWidget(self.spl_hor_src_data_params)

        self.spl_ver_src_res_data.addWidget(self.frm_src_and_data)
        self.frm_res_img = QFrame(self.spl_ver_src_res_data)
        self.frm_res_img.setObjectName(u"frm_res_img")
        self.frm_res_img.setFrameShape(QFrame.StyledPanel)
        self.frm_res_img.setFrameShadow(QFrame.Raised)
        self.spl_ver_src_res_data.addWidget(self.frm_res_img)

        self.verticalLayout.addWidget(self.spl_ver_src_res_data)

        self.spl_pb_ver_main.addWidget(self.frame)

        self.verticalLayout_3.addWidget(self.spl_pb_ver_main)

        self.tabWidget.addTab(self.tab_pipeline_builder, "")
        self.tab_pipeline_processor = QWidget()
        self.tab_pipeline_processor.setObjectName(u"tab_pipeline_processor")
        self.horizontalLayout_4 = QHBoxLayout(self.tab_pipeline_processor)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.splitter = QSplitter(self.tab_pipeline_processor)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Horizontal)
        self.layoutWidget = QWidget(self.splitter)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.verticalLayout_4 = QVBoxLayout(self.layoutWidget)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.groupBox_2 = QGroupBox(self.layoutWidget)
        self.groupBox_2.setObjectName(u"groupBox_2")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox_2.sizePolicy().hasHeightForWidth())
        self.groupBox_2.setSizePolicy(sizePolicy)
        self.groupBox_2.setFont(font3)
        self.groupBox_2.setFlat(False)
        self.gridLayout_5 = QGridLayout(self.groupBox_2)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.bt_pp_select_script = QToolButton(self.groupBox_2)
        self.bt_pp_select_script.setObjectName(u"bt_pp_select_script")
        self.bt_pp_select_script.setFont(font1)
        icon19 = QIcon()
        icon19.addFile(u":/common/resources/List.png", QSize(), QIcon.Normal, QIcon.Off)
        self.bt_pp_select_script.setIcon(icon19)

        self.gridLayout_5.addWidget(self.bt_pp_select_script, 1, 2, 1, 1)

        self.lb_pp_thread_count = QLabel(self.groupBox_2)
        self.lb_pp_thread_count.setObjectName(u"lb_pp_thread_count")
        self.lb_pp_thread_count.setFont(font1)

        self.gridLayout_5.addWidget(self.lb_pp_thread_count, 2, 2, 1, 1)

        self.sl_pp_thread_count = QSlider(self.groupBox_2)
        self.sl_pp_thread_count.setObjectName(u"sl_pp_thread_count")
        self.sl_pp_thread_count.setOrientation(Qt.Horizontal)

        self.gridLayout_5.addWidget(self.sl_pp_thread_count, 2, 1, 1, 1)

        self.label_9 = QLabel(self.groupBox_2)
        self.label_9.setObjectName(u"label_9")
        sizePolicy1 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.label_9.sizePolicy().hasHeightForWidth())
        self.label_9.setSizePolicy(sizePolicy1)
        self.label_9.setFont(font1)

        self.gridLayout_5.addWidget(self.label_9, 2, 0, 1, 1)

        self.rb_pp_load_script = QRadioButton(self.groupBox_2)
        self.rb_pp_load_script.setObjectName(u"rb_pp_load_script")
        self.rb_pp_load_script.setFont(font1)

        self.gridLayout_5.addWidget(self.rb_pp_load_script, 1, 0, 1, 1)

        self.rb_pp_default_process = QRadioButton(self.groupBox_2)
        self.rb_pp_default_process.setObjectName(u"rb_pp_default_process")
        self.rb_pp_default_process.setFont(font1)

        self.gridLayout_5.addWidget(self.rb_pp_default_process, 0, 0, 1, 4)

        self.tb_pp_desc = QTextBrowser(self.groupBox_2)
        self.tb_pp_desc.setObjectName(u"tb_pp_desc")
        self.tb_pp_desc.setMaximumSize(QSize(16777215, 64))
        self.tb_pp_desc.setFont(font1)

        self.gridLayout_5.addWidget(self.tb_pp_desc, 1, 1, 1, 1)

        self.verticalLayout_4.addWidget(self.groupBox_2)

        self.groupBox = QGroupBox(self.layoutWidget)
        self.groupBox.setObjectName(u"groupBox")
        sizePolicy.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy)
        self.groupBox.setFont(font3)
        self.gridLayout_11 = QGridLayout(self.groupBox)
        self.gridLayout_11.setObjectName(u"gridLayout_11")
        self.edt_csv_file_name = QLineEdit(self.groupBox)
        self.edt_csv_file_name.setObjectName(u"edt_csv_file_name")

        self.gridLayout_11.addWidget(self.edt_csv_file_name, 1, 1, 1, 1)

        self.lbl_csv_file_name = QLabel(self.groupBox)
        self.lbl_csv_file_name.setObjectName(u"lbl_csv_file_name")
        self.lbl_csv_file_name.setFont(font1)

        self.gridLayout_11.addWidget(self.lbl_csv_file_name, 1, 0, 1, 1)

        self.bt_pp_select_output_folder = QToolButton(self.groupBox)
        self.bt_pp_select_output_folder.setObjectName(u"bt_pp_select_output_folder")
        icon20 = QIcon()
        icon20.addFile(
            u":/common/resources/folder_blue.png", QSize(), QIcon.Normal, QIcon.Off
        )
        self.bt_pp_select_output_folder.setIcon(icon20)

        self.gridLayout_11.addWidget(self.bt_pp_select_output_folder, 0, 2, 1, 1)

        self.horizontalLayout_11 = QHBoxLayout()
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.cb_pp_generate_series_id = QCheckBox(self.groupBox)
        self.cb_pp_generate_series_id.setObjectName(u"cb_pp_generate_series_id")
        sizePolicy2 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(
            self.cb_pp_generate_series_id.sizePolicy().hasHeightForWidth()
        )
        self.cb_pp_generate_series_id.setSizePolicy(sizePolicy2)
        self.cb_pp_generate_series_id.setFont(font1)

        self.horizontalLayout_11.addWidget(self.cb_pp_generate_series_id)

        self.horizontalSpacer_7 = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum
        )

        self.horizontalLayout_11.addItem(self.horizontalSpacer_7)

        self.label_4 = QLabel(self.groupBox)
        self.label_4.setObjectName(u"label_4")
        sizePolicy.setHeightForWidth(self.label_4.sizePolicy().hasHeightForWidth())
        self.label_4.setSizePolicy(sizePolicy)
        self.label_4.setFont(font1)

        self.horizontalLayout_11.addWidget(self.label_4)

        self.sp_pp_time_delta = QSpinBox(self.groupBox)
        self.sp_pp_time_delta.setObjectName(u"sp_pp_time_delta")
        sizePolicy2.setHeightForWidth(
            self.sp_pp_time_delta.sizePolicy().hasHeightForWidth()
        )
        self.sp_pp_time_delta.setSizePolicy(sizePolicy2)
        self.sp_pp_time_delta.setFont(font1)
        self.sp_pp_time_delta.setMaximum(10080)
        self.sp_pp_time_delta.setValue(20)

        self.horizontalLayout_11.addWidget(self.sp_pp_time_delta)

        self.label_5 = QLabel(self.groupBox)
        self.label_5.setObjectName(u"label_5")
        sizePolicy.setHeightForWidth(self.label_5.sizePolicy().hasHeightForWidth())
        self.label_5.setSizePolicy(sizePolicy)
        self.label_5.setFont(font1)

        self.horizontalLayout_11.addWidget(self.label_5)

        self.gridLayout_11.addLayout(self.horizontalLayout_11, 6, 0, 1, 3)

        self.le_pp_output_folder = QLineEdit(self.groupBox)
        self.le_pp_output_folder.setObjectName(u"le_pp_output_folder")
        self.le_pp_output_folder.setFont(font1)
        self.le_pp_output_folder.setReadOnly(True)

        self.gridLayout_11.addWidget(self.le_pp_output_folder, 0, 1, 1, 1)

        self.label_2 = QLabel(self.groupBox)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setFont(font1)

        self.gridLayout_11.addWidget(self.label_2, 0, 0, 1, 1)

        self.cb_pp_append_timestamp_to_output_folder = QCheckBox(self.groupBox)
        self.cb_pp_append_timestamp_to_output_folder.setObjectName(
            u"cb_pp_append_timestamp_to_output_folder"
        )
        self.cb_pp_append_timestamp_to_output_folder.setFont(font1)

        self.gridLayout_11.addWidget(
            self.cb_pp_append_timestamp_to_output_folder, 4, 0, 1, 3
        )

        self.cb_pp_append_experience_name = QCheckBox(self.groupBox)
        self.cb_pp_append_experience_name.setObjectName(u"cb_pp_append_experience_name")
        self.cb_pp_append_experience_name.setFont(font1)

        self.gridLayout_11.addWidget(self.cb_pp_append_experience_name, 3, 0, 1, 3)

        self.cb_pp_overwrite = QCheckBox(self.groupBox)
        self.cb_pp_overwrite.setObjectName(u"cb_pp_overwrite")
        self.cb_pp_overwrite.setFont(font1)

        self.gridLayout_11.addWidget(self.cb_pp_overwrite, 2, 0, 1, 3)

        self.cb_pp_save_mosaics = QCheckBox(self.groupBox)
        self.cb_pp_save_mosaics.setObjectName(u"cb_pp_save_mosaics")
        self.cb_pp_save_mosaics.setFont(font1)

        self.gridLayout_11.addWidget(self.cb_pp_save_mosaics, 5, 0, 1, 1)

        self.verticalLayout_4.addWidget(self.groupBox)

        self.gridLayout_10 = QGridLayout()
        self.gridLayout_10.setObjectName(u"gridLayout_10")
        self.label_6 = QLabel(self.layoutWidget)
        self.label_6.setObjectName(u"label_6")

        self.gridLayout_10.addWidget(self.label_6, 0, 0, 1, 1)

        self.cb_queue_auto_scroll = QCheckBox(self.layoutWidget)
        self.cb_queue_auto_scroll.setObjectName(u"cb_queue_auto_scroll")
        self.cb_queue_auto_scroll.setChecked(True)

        self.gridLayout_10.addWidget(self.cb_queue_auto_scroll, 0, 1, 1, 1)

        self.lw_images_queue = QListWidget(self.layoutWidget)
        self.lw_images_queue.setObjectName(u"lw_images_queue")

        self.gridLayout_10.addWidget(self.lw_images_queue, 1, 0, 1, 2)

        self.verticalLayout_4.addLayout(self.gridLayout_10)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.bt_pp_reset = QPushButton(self.layoutWidget)
        self.bt_pp_reset.setObjectName(u"bt_pp_reset")
        self.bt_pp_reset.setFont(font1)
        self.bt_pp_reset.setIcon(icon17)

        self.horizontalLayout_3.addWidget(self.bt_pp_reset)

        self.horizontalSpacer_6 = QSpacerItem(
            944, 20, QSizePolicy.Expanding, QSizePolicy.Minimum
        )

        self.horizontalLayout_3.addItem(self.horizontalSpacer_6)

        self.bt_pp_start = QPushButton(self.layoutWidget)
        self.bt_pp_start.setObjectName(u"bt_pp_start")
        self.bt_pp_start.setMinimumSize(QSize(100, 0))
        font4 = QFont()
        font4.setPointSize(16)
        font4.setBold(True)
        font4.setWeight(75)
        self.bt_pp_start.setFont(font4)
        icon21 = QIcon()
        icon21.addFile(
            u":/image_process/resources/Play.png", QSize(), QIcon.Normal, QIcon.Off
        )
        self.bt_pp_start.setIcon(icon21)
        self.bt_pp_start.setIconSize(QSize(24, 24))

        self.horizontalLayout_3.addWidget(self.bt_pp_start)

        self.verticalLayout_4.addLayout(self.horizontalLayout_3)

        self.splitter.addWidget(self.layoutWidget)
        self.layoutWidget1 = QWidget(self.splitter)
        self.layoutWidget1.setObjectName(u"layoutWidget1")
        self.ver_layout_last_image = QVBoxLayout(self.layoutWidget1)
        self.ver_layout_last_image.setObjectName(u"ver_layout_last_image")
        self.ver_layout_last_image.setContentsMargins(0, 0, 0, 0)
        self.chk_pp_show_last_item = QCheckBox(self.layoutWidget1)
        self.chk_pp_show_last_item.setObjectName(u"chk_pp_show_last_item")

        self.ver_layout_last_image.addWidget(self.chk_pp_show_last_item)

        self.splitter.addWidget(self.layoutWidget1)

        self.horizontalLayout_4.addWidget(self.splitter)

        self.tabWidget.addTab(self.tab_pipeline_processor, "")
        self.tab_data_editor = QWidget()
        self.tab_data_editor.setObjectName(u"tab_data_editor")
        self.gridLayout_13 = QGridLayout(self.tab_data_editor)
        self.gridLayout_13.setObjectName(u"gridLayout_13")
        self.spl_de_right = QSplitter(self.tab_data_editor)
        self.spl_de_right.setObjectName(u"spl_de_right")
        self.spl_de_right.setOrientation(Qt.Horizontal)
        self.spl_de_left = QSplitter(self.spl_de_right)
        self.spl_de_left.setObjectName(u"spl_de_left")
        self.spl_de_left.setOrientation(Qt.Horizontal)
        self.tb_de_column_info = QTableView(self.spl_de_left)
        self.tb_de_column_info.setObjectName(u"tb_de_column_info")
        self.tb_de_column_info.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tb_de_column_info.setDragDropOverwriteMode(False)
        self.tb_de_column_info.setAlternatingRowColors(True)
        self.tb_de_column_info.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.spl_de_left.addWidget(self.tb_de_column_info)
        self.tb_de_column_info.horizontalHeader().setStretchLastSection(False)
        self.spl_de_hor = QSplitter(self.spl_de_left)
        self.spl_de_hor.setObjectName(u"spl_de_hor")
        self.spl_de_hor.setOrientation(Qt.Vertical)
        self.tb_ge_dataframe = QTableView(self.spl_de_hor)
        self.tb_ge_dataframe.setObjectName(u"tb_ge_dataframe")
        self.tb_ge_dataframe.setSelectionMode(QAbstractItemView.SingleSelection)
        self.spl_de_hor.addWidget(self.tb_ge_dataframe)
        self.tb_ge_dataframe.horizontalHeader().setProperty("showSortIndicator", True)
        self.tb_de_dataframe_info = QTableView(self.spl_de_hor)
        self.tb_de_dataframe_info.setObjectName(u"tb_de_dataframe_info")
        self.tb_de_dataframe_info.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tb_de_dataframe_info.setDragDropOverwriteMode(False)
        self.tb_de_dataframe_info.setAlternatingRowColors(True)
        self.tb_de_dataframe_info.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.spl_de_hor.addWidget(self.tb_de_dataframe_info)
        self.spl_de_left.addWidget(self.spl_de_hor)
        self.spl_de_right.addWidget(self.spl_de_left)

        self.gridLayout_13.addWidget(self.spl_de_right, 0, 0, 1, 1)

        self.tabWidget.addTab(self.tab_data_editor, "")

        self.verticalLayout_2.addWidget(self.tabWidget)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1045, 21))
        self.menu_file = QMenu(self.menubar)
        self.menu_file.setObjectName(u"menu_file")
        self.mnu_recent_parsed_folders = QMenu(self.menu_file)
        self.mnu_recent_parsed_folders.setObjectName(u"mnu_recent_parsed_folders")
        self.mnu_connect_to_db = QMenu(self.menu_file)
        self.mnu_connect_to_db.setObjectName(u"mnu_connect_to_db")
        self.menuImage_lists = QMenu(self.menu_file)
        self.menuImage_lists.setObjectName(u"menuImage_lists")
        self.menu_settings = QMenu(self.menubar)
        self.menu_settings.setObjectName(u"menu_settings")
        self.menuVideo = QMenu(self.menu_settings)
        self.menuVideo.setObjectName(u"menuVideo")
        self.menuVideo.setToolTipsVisible(True)
        self.menuFrame_duration = QMenu(self.menuVideo)
        self.menuFrame_duration.setObjectName(u"menuFrame_duration")
        self.menuResolution = QMenu(self.menuVideo)
        self.menuResolution.setObjectName(u"menuResolution")
        self.menuAspect_ratio = QMenu(self.menuVideo)
        self.menuAspect_ratio.setObjectName(u"menuAspect_ratio")
        self.menuBackground_color = QMenu(self.menuVideo)
        self.menuBackground_color.setObjectName(u"menuBackground_color")
        self.menu_theme = QMenu(self.menu_settings)
        self.menu_theme.setObjectName(u"menu_theme")
        self.menuCode_generation_mode = QMenu(self.menu_settings)
        self.menuCode_generation_mode.setObjectName(u"menuCode_generation_mode")
        self.mnu_debug = QMenu(self.menu_settings)
        self.mnu_debug.setObjectName(u"mnu_debug")
        self.menuPipeline_builder = QMenu(self.menu_settings)
        self.menuPipeline_builder.setObjectName(u"menuPipeline_builder")
        self.menu_source_image_scale_factor = QMenu(self.menuPipeline_builder)
        self.menu_source_image_scale_factor.setObjectName(
            u"menu_source_image_scale_factor"
        )
        self.menu_help = QMenu(self.menubar)
        self.menu_help.setObjectName(u"menu_help")
        self.menu_view = QMenu(self.menubar)
        self.menu_view.setObjectName(u"menu_view")
        self.menu_data_editor = QMenu(self.menubar)
        self.menu_data_editor.setObjectName(u"menu_data_editor")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        self.statusbar.setFont(font3)
        MainWindow.setStatusBar(self.statusbar)
        self.dk_log = QDockWidget(MainWindow)
        self.dk_log.setObjectName(u"dk_log")
        self.dk_log.setFeatures(QDockWidget.AllDockWidgetFeatures)
        self.dockWidgetContents = QWidget()
        self.dockWidgetContents.setObjectName(u"dockWidgetContents")
        self.horizontalLayout_12 = QHBoxLayout(self.dockWidgetContents)
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.dk_log.setWidget(self.dockWidgetContents)
        MainWindow.addDockWidget(Qt.BottomDockWidgetArea, self.dk_log)

        self.menubar.addAction(self.menu_file.menuAction())
        self.menubar.addAction(self.menu_settings.menuAction())
        self.menubar.addAction(self.menu_data_editor.menuAction())
        self.menubar.addAction(self.menu_view.menuAction())
        self.menubar.addAction(self.menu_help.menuAction())
        self.menu_file.addAction(self.act_parse_folder_memory)
        self.menu_file.addAction(self.mnu_recent_parsed_folders.menuAction())
        self.menu_file.addAction(self.mnu_connect_to_db.menuAction())
        self.menu_file.addAction(self.menuImage_lists.menuAction())
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.actionSave_selected_image)
        self.menu_file.addAction(self.actionSave_all_images)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.action_save_pipeline_processor_state)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.action_build_video_from_images)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.action_new_tool)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.actionExit)
        self.mnu_recent_parsed_folders.addAction(self.act_clean_parsed_folders)
        self.menuImage_lists.addAction(self.action_save_image_list)
        self.menuImage_lists.addAction(self.action_load_image_list)
        self.menu_settings.addAction(self.actionEnable_annotations)
        self.menu_settings.addAction(self.actionEnable_log)
        self.menu_settings.addAction(self.menuVideo.menuAction())
        self.menu_settings.addAction(self.menu_theme.menuAction())
        self.menu_settings.addSeparator()
        self.menu_settings.addAction(self.menuPipeline_builder.menuAction())
        self.menu_settings.addSeparator()
        self.menu_settings.addAction(self.menuCode_generation_mode.menuAction())
        self.menu_settings.addSeparator()
        self.menu_settings.addAction(self.mnu_debug.menuAction())
        self.menuVideo.addAction(self.menuResolution.menuAction())
        self.menuVideo.addAction(self.menuAspect_ratio.menuAction())
        self.menuVideo.addAction(self.menuBackground_color.menuAction())
        self.menuVideo.addAction(self.menuFrame_duration.menuAction())
        self.menuVideo.addAction(self.action_video_stack_and_jitter)
        self.menuFrame_duration.addAction(self.action_video_1_24_second)
        self.menuFrame_duration.addAction(self.action_video_half_second)
        self.menuFrame_duration.addAction(self.action_video_1_second)
        self.menuFrame_duration.addAction(self.action_video_5_second)
        self.menuResolution.addAction(self.action_video_res_first_image)
        self.menuResolution.addAction(self.action_video_res_1080p)
        self.menuResolution.addAction(self.action_video_res_720p)
        self.menuResolution.addAction(self.action_video_res_576p)
        self.menuResolution.addAction(self.action_video_res_480p)
        self.menuResolution.addAction(self.action_video_res_376p)
        self.menuResolution.addAction(self.action_video_res_240p)
        self.menuAspect_ratio.addAction(self.action_video_ar_16_9)
        self.menuAspect_ratio.addAction(self.action_video_ar_4_3)
        self.menuAspect_ratio.addAction(self.action_video_ar_1_1)
        self.menuBackground_color.addAction(self.action_video_bkg_color_black)
        self.menuBackground_color.addAction(self.action_video_bkg_color_white)
        self.menuBackground_color.addAction(self.action_video_bkg_color_silver)
        self.menuCode_generation_mode.addAction(self.action_create_wrapper_before)
        self.menuCode_generation_mode.addSeparator()
        self.menuCode_generation_mode.addAction(self.action_functional_style)
        self.menuCode_generation_mode.addAction(
            self.action_object_oriented_wrapped_with_a_with_clause
        )
        self.menuCode_generation_mode.addAction(self.action_standard_object_oriented_call)
        self.mnu_debug.addAction(self.action_use_multithreading)
        self.menuPipeline_builder.addAction(
            self.menu_source_image_scale_factor.menuAction()
        )
        self.menu_source_image_scale_factor.addAction(self.act_settings_sir_keep)
        self.menu_source_image_scale_factor.addAction(self.act_settings_sir_2x)
        self.menu_source_image_scale_factor.addAction(self.act_settings_sir_3x)
        self.menu_source_image_scale_factor.addAction(self.act_settings_sir_4x)
        self.menu_source_image_scale_factor.addAction(self.act_settings_sir_5x)
        self.menu_source_image_scale_factor.addAction(self.act_settings_sir_6x)
        self.menu_help.addAction(self.action_show_read_me)
        self.menu_help.addAction(self.action_show_documentation)
        self.menu_help.addSeparator()
        self.menu_help.addAction(self.action_build_tool_documentation)
        self.menu_help.addAction(self.action_build_ipso_phen_documentation)
        self.menu_help.addAction(self.action_build_test_files)
        self.menu_help.addSeparator()
        self.menu_help.addAction(self.action_about_form)
        self.menu_view.addAction(self.action_show_log)
        self.menu_data_editor.addAction(self.action_de_new_sheet)
        self.menu_data_editor.addSeparator()
        self.menu_data_editor.addAction(self.action_de_load_csv)
        self.menu_data_editor.addAction(self.action_de_create_sheet_from_selection)
        self.menu_data_editor.addSeparator()
        self.menu_data_editor.addAction(self.action_de_save_csv)
        self.menu_data_editor.addSeparator()
        self.menu_data_editor.addAction(self.action_de_add_column)
        self.menu_data_editor.addAction(self.action_de_delete_column)

        self.retranslateUi(MainWindow)
        self.bt_clear_statistics.clicked.connect(self.lv_stats.clear)

        self.tabWidget.setCurrentIndex(0)
        self.tw_tool_box.setCurrentIndex(1)
        self.tb_tool_script.setCurrentIndex(0)
        self.bt_process_image.setDefault(True)

        QMetaObject.connectSlotsByName(MainWindow)

    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(
            QCoreApplication.translate("MainWindow", u"<b>IPSO</b>", None)
        )
        # if QT_CONFIG(statustip)
        MainWindow.setStatusTip("")
        # endif // QT_CONFIG(statustip)
        self.actionTPMP.setText(QCoreApplication.translate("MainWindow", u"TPMP", None))
        self.actionTPMP_sample.setText(
            QCoreApplication.translate("MainWindow", u"TPMP sample", None)
        )
        self.action_switch_db_new.setText(
            QCoreApplication.translate("MainWindow", u"New DB", None)
        )
        self.actionSelect.setText(
            QCoreApplication.translate("MainWindow", u"Select ...", None)
        )
        self.actionExit.setText(QCoreApplication.translate("MainWindow", u"Exit", None))
        self.actionEnable_annotations.setText(
            QCoreApplication.translate("MainWindow", u"Enable annotations", None)
        )
        self.actionEnable_log.setText(
            QCoreApplication.translate("MainWindow", u"Enable log", None)
        )
        self.actionSave_selected_image.setText(
            QCoreApplication.translate("MainWindow", u"Save selected image", None)
        )
        self.actionSave_all_images.setText(
            QCoreApplication.translate("MainWindow", u"Save all images", None)
        )
        self.action_parse_folder.setText(
            QCoreApplication.translate("MainWindow", u"Parse folder", None)
        )
        self.actionAdd_channel_mask.setText(
            QCoreApplication.translate("MainWindow", u"Add Threshold", None)
        )
        self.actionAdd_white_balance_fixer.setText(
            QCoreApplication.translate("MainWindow", u"Add Pre-processing", None)
        )
        self.action_script_merge_select_and.setText(
            QCoreApplication.translate("MainWindow", u"And", None)
        )
        self.action_script_merge_select_or.setText(
            QCoreApplication.translate("MainWindow", u"Or", None)
        )
        self.actionSet_contour_cleaner.setText(
            QCoreApplication.translate("MainWindow", u"Add Mask cleanup", None)
        )
        self.actionDisplay_images.setText(
            QCoreApplication.translate("MainWindow", u"Display images", None)
        )
        self.actionUse_file_name.setText(
            QCoreApplication.translate("MainWindow", u"Use file name", None)
        )
        self.action_data_output_none.setText(
            QCoreApplication.translate("MainWindow", u"None", None)
        )
        self.action_data_output_stdio.setText(
            QCoreApplication.translate("MainWindow", u"Std IO", None)
        )
        self.action_data_output_file.setText(
            QCoreApplication.translate("MainWindow", u"File", None)
        )
        self.action_execute_script.setText(
            QCoreApplication.translate("MainWindow", u"Execute", None)
        )
        self.actionAll.setText(QCoreApplication.translate("MainWindow", u"All", None))
        self.actionNone.setText(QCoreApplication.translate("MainWindow", u"None", None))
        self.action_build_video_from_images.setText(
            QCoreApplication.translate("MainWindow", u"Build video from images", None)
        )
        self.action_new_script.setText(
            QCoreApplication.translate("MainWindow", u"New", None)
        )
        self.action_load_script.setText(
            QCoreApplication.translate("MainWindow", u"Load...", None)
        )
        self.action_save_script.setText(
            QCoreApplication.translate("MainWindow", u"Save...", None)
        )
        self.action_add_roi_execute_after_pre_processing.setText(
            QCoreApplication.translate(
                "MainWindow", u"Add ROI (execute after pre-processing", None
            )
        )
        self.action_roi_execute_before_pre_processing.setText(
            QCoreApplication.translate(
                "MainWindow", u"Execute before pre-processing", None
            )
        )
        self.action_roi_execute_after_pre_processing.setText(
            QCoreApplication.translate(
                "MainWindow", u"Execute after pre-processing", None
            )
        )
        self.action_roi_execute_after_mask_merger.setText(
            QCoreApplication.translate("MainWindow", u"Execute after mask merger", None)
        )
        self.act_view_anno_all.setText(
            QCoreApplication.translate("MainWindow", u"All", None)
        )
        self.act_view_anno_none.setText(
            QCoreApplication.translate("MainWindow", u"None", None)
        )
        self.act_view_anno_empty.setText(
            QCoreApplication.translate("MainWindow", u"No annotation", None)
        )
        self.act_view_anno_info.setText(
            QCoreApplication.translate("MainWindow", u"Info", None)
        )
        self.act_view_anno_ok.setText(
            QCoreApplication.translate("MainWindow", u"OK", None)
        )
        self.act_view_anno_warning.setText(
            QCoreApplication.translate("MainWindow", u"Warning", None)
        )
        self.act_view_anno_error.setText(
            QCoreApplication.translate("MainWindow", u"Error", None)
        )
        self.act_view_anno_critical.setText(
            QCoreApplication.translate("MainWindow", u"Critical", None)
        )
        self.act_view_anno_source_issue.setText(
            QCoreApplication.translate("MainWindow", u"Source issue", None)
        )
        self.act_view_anno_unknown.setText(
            QCoreApplication.translate("MainWindow", u"Unknown", None)
        )
        self.action_save_as_python_script.setText(
            QCoreApplication.translate("MainWindow", u"Save as Python script...", None)
        )
        self.actionMerge_script_and_toolbox_panels.setText(
            QCoreApplication.translate(
                "MainWindow", u"Merge script and toolbox panels", None
            )
        )
        self.actionPut_tools_widgets_in_scroll_panel.setText(
            QCoreApplication.translate(
                "MainWindow", u"Put tools widgets in scroll panel", None
            )
        )
        self.actionAdd_auto_fill_in_grid_search.setText(
            QCoreApplication.translate(
                "MainWindow", u"Add auto fill in grid search", None
            )
        )
        self.actionAdd_buttons_to_add_tool_to_script_next_to_reset_button.setText(
            QCoreApplication.translate(
                "MainWindow",
                u"Add buttons to add tool to script next to reset button",
                None,
            )
        )
        self.actionAdd_roi_to_check_mask_positioning.setText(
            QCoreApplication.translate(
                "MainWindow", u"Add roi to check mask positioning", None
            )
        )
        self.actionFix_ROI_display_color_issue_for_rectangles.setText(
            QCoreApplication.translate(
                "MainWindow", u"Fix ROI display color issue for rectangles", None
            )
        )
        self.actionAdd_more_colors_for_ROI.setText(
            QCoreApplication.translate("MainWindow", u"Add more colors for ROI", None)
        )
        self.action_create_wrapper_before.setText(
            QCoreApplication.translate("MainWindow", u"Create wrapper before", None)
        )
        self.action_standard_object_oriented_call.setText(
            QCoreApplication.translate(
                "MainWindow", u"Standard object oriented call", None
            )
        )
        self.action_object_oriented_wrapped_with_a_with_clause.setText(
            QCoreApplication.translate(
                "MainWindow", u'Object oriented wrapped with a "with" clause', None
            )
        )
        self.action_functional_style.setText(
            QCoreApplication.translate("MainWindow", u"Functional style", None)
        )
        self.action_video_1_second.setText(
            QCoreApplication.translate("MainWindow", u"1 second", None)
        )
        self.action_video_1_24_second.setText(
            QCoreApplication.translate("MainWindow", u"1/24 second", None)
        )
        self.action_video_5_second.setText(
            QCoreApplication.translate("MainWindow", u"5 seconds", None)
        )
        self.action_video_stack_and_jitter.setText(
            QCoreApplication.translate("MainWindow", u"Stack & jitter", None)
        )
        self.action_video_half_second.setText(
            QCoreApplication.translate("MainWindow", u"0.5 seconds", None)
        )
        self.action_video_res_first_image.setText(
            QCoreApplication.translate("MainWindow", u"First image", None)
        )
        self.action_video_res_1080p.setText(
            QCoreApplication.translate("MainWindow", u"1080p", None)
        )
        self.action_video_res_720p.setText(
            QCoreApplication.translate("MainWindow", u"720p", None)
        )
        self.action_video_res_576p.setText(
            QCoreApplication.translate("MainWindow", u"576p", None)
        )
        self.action_video_res_480p.setText(
            QCoreApplication.translate("MainWindow", u"480p", None)
        )
        self.action_video_res_376p.setText(
            QCoreApplication.translate("MainWindow", u"376p", None)
        )
        self.action_video_res_240p.setText(
            QCoreApplication.translate("MainWindow", u"240p", None)
        )
        self.action_video_ar_16_9.setText(
            QCoreApplication.translate("MainWindow", u"16/9", None)
        )
        self.action_video_ar_4_3.setText(
            QCoreApplication.translate("MainWindow", u"4/3", None)
        )
        self.action_video_ar_1_1.setText(
            QCoreApplication.translate("MainWindow", u"1/1", None)
        )
        self.action_video_bkg_color_black.setText(
            QCoreApplication.translate("MainWindow", u"Black", None)
        )
        self.action_video_bkg_color_white.setText(
            QCoreApplication.translate("MainWindow", u"White", None)
        )
        self.action_video_bkg_color_silver.setText(
            QCoreApplication.translate("MainWindow", u"Silver", None)
        )
        self.act_parse_folder_memory.setText(
            QCoreApplication.translate("MainWindow", u"Parse folder", None)
        )
        # if QT_CONFIG(tooltip)
        self.act_parse_folder_memory.setToolTip(
            QCoreApplication.translate(
                "MainWindow", u"Parse folder and create memory database", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.act_clean_parsed_folders.setText(
            QCoreApplication.translate("MainWindow", u"Clear", None)
        )
        self.actionplace_holder.setText(
            QCoreApplication.translate("MainWindow", u"place_holder", None)
        )
        self.actionplace_holder_2.setText(
            QCoreApplication.translate("MainWindow", u"place_holder", None)
        )
        self.action_add_exposure_fixer.setText(
            QCoreApplication.translate("MainWindow", u"Add Exposure fixing", None)
        )
        self.action_add_feature_extractor.setText(
            QCoreApplication.translate("MainWindow", u"Add Feature extraction", None)
        )
        self.action_about_form.setText(
            QCoreApplication.translate("MainWindow", u"About IPSO Phen", None)
        )
        self.action_show_documentation.setText(
            QCoreApplication.translate("MainWindow", u"Documentation", None)
        )
        self.action_use_dark_theme.setText(
            QCoreApplication.translate("MainWindow", u"Dark theme", None)
        )
        self.action_build_tool_documentation.setText(
            QCoreApplication.translate("MainWindow", u"Build tool documentation", None)
        )
        self.action_build_ipso_phen_documentation.setText(
            QCoreApplication.translate(
                "MainWindow", u"Build IPSO Phen documentation", None
            )
        )
        self.action_show_read_me.setText(
            QCoreApplication.translate("MainWindow", u"Read me", None)
        )
        self.action_build_missing_tools_documentation.setText(
            QCoreApplication.translate(
                "MainWindow", u"Build missing tools documentation", None
            )
        )
        self.action_new_tool.setText(
            QCoreApplication.translate("MainWindow", u"New tool", None)
        )
        self.action_use_multithreading.setText(
            QCoreApplication.translate("MainWindow", u"Use multithreading", None)
        )
        # if QT_CONFIG(tooltip)
        self.action_use_multithreading.setToolTip(
            QCoreApplication.translate("MainWindow", u"Do not change !!!", None)
        )
        # endif // QT_CONFIG(tooltip)
        self.action_use_pipeline_cache.setText(
            QCoreApplication.translate("MainWindow", u"Use pipeline cache", None)
        )
        self.action_show_log.setText(
            QCoreApplication.translate("MainWindow", u"Log", None)
        )
        self.action_de_load_csv.setText(
            QCoreApplication.translate("MainWindow", u"Load CSV", None)
        )
        self.action_de_new_sheet.setText(
            QCoreApplication.translate("MainWindow", u"New sheet", None)
        )
        self.action_de_create_sheet_from_selection.setText(
            QCoreApplication.translate("MainWindow", u"Create sheet from selection", None)
        )
        self.action_de_create_sheet_from_query.setText(
            QCoreApplication.translate("MainWindow", u"Create sheet from query", None)
        )
        self.action_de_add_column.setText(
            QCoreApplication.translate("MainWindow", u"Add column", None)
        )
        self.action_de_delete_column.setText(
            QCoreApplication.translate("MainWindow", u"Delete column", None)
        )
        self.action_de_save_csv.setText(
            QCoreApplication.translate("MainWindow", u"Save CSV...", None)
        )
        self.action_save_image_list.setText(
            QCoreApplication.translate("MainWindow", u"Save", None)
        )
        self.action_load_image_list.setText(
            QCoreApplication.translate("MainWindow", u"Load", None)
        )
        self.act_settings_sir_keep.setText(
            QCoreApplication.translate("MainWindow", u"Keep original", None)
        )
        self.act_settings_sir_2x.setText(
            QCoreApplication.translate("MainWindow", u"2x", None)
        )
        self.act_settings_sir_3x.setText(
            QCoreApplication.translate("MainWindow", u"3x", None)
        )
        self.act_settings_sir_4x.setText(
            QCoreApplication.translate("MainWindow", u"4x", None)
        )
        self.act_settings_sir_5x.setText(
            QCoreApplication.translate("MainWindow", u"5x", None)
        )
        self.act_settings_sir_6x.setText(
            QCoreApplication.translate("MainWindow", u"6x", None)
        )
        self.action_save_pipeline_processor_state.setText(
            QCoreApplication.translate(
                "MainWindow", u"Save pipeline processor state", None
            )
        )
        self.action_add_image_generator.setText(
            QCoreApplication.translate("MainWindow", u"Add Image Generator", None)
        )
        self.action_build_test_files.setText(
            QCoreApplication.translate("MainWindow", u"Build test files", None)
        )
        self.action_add_white_balance_corrector.setText(
            QCoreApplication.translate("MainWindow", u"Add white balance corrector", None)
        )
        self.action_build_roi_with_raw_image.setText(
            QCoreApplication.translate("MainWindow", u"Build with raw image", None)
        )
        self.action_build_roi_with_pre_processed_image.setText(
            QCoreApplication.translate(
                "MainWindow", u"Build with pre processed image", None
            )
        )
        self.chk_experiment.setText(
            QCoreApplication.translate("MainWindow", u"Experiment:", None)
        )
        self.chk_plant.setText(QCoreApplication.translate("MainWindow", u"Plant:", None))
        self.chk_date.setText(QCoreApplication.translate("MainWindow", u"Date:", None))
        self.chk_camera.setText(
            QCoreApplication.translate("MainWindow", u"Camera:", None)
        )
        self.chk_angle.setText(QCoreApplication.translate("MainWindow", u"Angle:", None))
        self.chk_wavelength.setText(
            QCoreApplication.translate("MainWindow", u"wavelength", None)
        )
        self.chk_time.setText(QCoreApplication.translate("MainWindow", u"Time:", None))
        # if QT_CONFIG(tooltip)
        self.bt_add_random.setToolTip(
            QCoreApplication.translate(
                "MainWindow",
                u"Add to image browser n random images matching the current query",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.bt_add_random.setText(
            QCoreApplication.translate("MainWindow", u"Add random", None)
        )
        # if QT_CONFIG(tooltip)
        self.bt_remove_from_selection.setToolTip(
            QCoreApplication.translate(
                "MainWindow",
                u"Remove from image browser images matching the current query",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.bt_remove_from_selection.setText(
            QCoreApplication.translate("MainWindow", u"Remove", None)
        )
        # if QT_CONFIG(tooltip)
        self.bt_keep_annotated.setToolTip(
            QCoreApplication.translate(
                "MainWindow",
                u"Remove from image brawser all images that are not tagged with an annotation",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.bt_keep_annotated.setText(
            QCoreApplication.translate("MainWindow", u"Keep tagged", None)
        )
        self.lbl_selection.setText(
            QCoreApplication.translate("MainWindow", u"Selection:", None)
        )
        # if QT_CONFIG(tooltip)
        self.bt_add_to_selection.setToolTip(
            QCoreApplication.translate(
                "MainWindow",
                u"Add to image browser images matching the current query",
                None,
            )
        )
        # endif // QT_CONFIG(tooltip)
        self.bt_add_to_selection.setText(
            QCoreApplication.translate("MainWindow", u"Add", None)
        )
        self.bt_clear_selection.setText(
            QCoreApplication.translate("MainWindow", u"Clear", None)
        )
        self.pushButton.setText(
            QCoreApplication.translate("MainWindow", u"PushButton", None)
        )
        self.label_3.setText(
            QCoreApplication.translate("MainWindow", u"Annotation level:", None)
        )
        self.cb_annotation_level.setItemText(
            0, QCoreApplication.translate("MainWindow", u"Info", None)
        )
        self.cb_annotation_level.setItemText(
            1, QCoreApplication.translate("MainWindow", u"OK", None)
        )
        self.cb_annotation_level.setItemText(
            2, QCoreApplication.translate("MainWindow", u"Warning", None)
        )
        self.cb_annotation_level.setItemText(
            3, QCoreApplication.translate("MainWindow", u"Error", None)
        )
        self.cb_annotation_level.setItemText(
            4, QCoreApplication.translate("MainWindow", u"Critical", None)
        )
        self.cb_annotation_level.setItemText(
            5, QCoreApplication.translate("MainWindow", u"Source issue", None)
        )
        self.cb_annotation_level.setItemText(
            6, QCoreApplication.translate("MainWindow", u"Unknown", None)
        )

        self.bt_delete_annotation.setText("")
        self.tw_tool_box.setTabText(
            self.tw_tool_box.indexOf(self.tb_annotations),
            QCoreApplication.translate("MainWindow", u"Annotations", None),
        )
        self.bt_set_batch_as_selection.setText(
            QCoreApplication.translate("MainWindow", u"Set as selection", None)
        )
        self.tw_tool_box.setTabText(
            self.tw_tool_box.indexOf(self.tb_last_batch),
            QCoreApplication.translate("MainWindow", u"Last batch", None),
        )
        self.bt_update_selection_stats.setText(
            QCoreApplication.translate("MainWindow", u"Build statistics", None)
        )
        self.bt_clear_statistics.setText(
            QCoreApplication.translate("MainWindow", u"Clear", None)
        )
        self.cb_stat_include_annotations.setText(
            QCoreApplication.translate("MainWindow", u"Include annotations", None)
        )
        self.tw_tool_box.setTabText(
            self.tw_tool_box.indexOf(self.tb_statistics),
            QCoreApplication.translate("MainWindow", u"Statistics", None),
        )
        self.label.setText(
            QCoreApplication.translate("MainWindow", u"Batch process:", None)
        )
        self.cb_batch_mode.setItemText(
            0, QCoreApplication.translate("MainWindow", u"All", None)
        )
        self.cb_batch_mode.setItemText(
            1, QCoreApplication.translate("MainWindow", u"First n", None)
        )
        self.cb_batch_mode.setItemText(
            2, QCoreApplication.translate("MainWindow", u"Random n", None)
        )

        self.bt_launch_batch.setText("")
        # if QT_CONFIG(tooltip)
        self.bt_pp_new.setToolTip(
            QCoreApplication.translate("MainWindow", u"New pipeline", None)
        )
        # endif // QT_CONFIG(tooltip)
        self.bt_pp_new.setText("")
        # if QT_CONFIG(tooltip)
        self.bt_pp_load.setToolTip(
            QCoreApplication.translate("MainWindow", u"Load pipeline...", None)
        )
        # endif // QT_CONFIG(tooltip)
        self.bt_pp_load.setText("")
        # if QT_CONFIG(tooltip)
        self.bt_pp_save.setToolTip(
            QCoreApplication.translate("MainWindow", u"Save pipeline...", None)
        )
        # endif // QT_CONFIG(tooltip)
        self.bt_pp_save.setText("")
        # if QT_CONFIG(tooltip)
        self.bt_pp_up.setToolTip(
            QCoreApplication.translate("MainWindow", u"Move item up", None)
        )
        # endif // QT_CONFIG(tooltip)
        self.bt_pp_up.setText("")
        # if QT_CONFIG(tooltip)
        self.bt_pp_down.setToolTip(
            QCoreApplication.translate("MainWindow", u"Move item down", None)
        )
        # endif // QT_CONFIG(tooltip)
        self.bt_pp_down.setText("")
        # if QT_CONFIG(tooltip)
        self.bt_pp_delete.setToolTip(
            QCoreApplication.translate("MainWindow", u"Delete item", None)
        )
        # endif // QT_CONFIG(tooltip)
        self.bt_pp_delete.setText("")
        # if QT_CONFIG(tooltip)
        self.bt_pp_select_tool.setToolTip(
            QCoreApplication.translate("MainWindow", u"Add module/group", None)
        )
        # endif // QT_CONFIG(tooltip)
        self.bt_pp_select_tool.setText("")
        # if QT_CONFIG(tooltip)
        self.bt_pp_invalidate.setToolTip(
            QCoreApplication.translate("MainWindow", u"Clear cache pipeline cache", None)
        )
        # endif // QT_CONFIG(tooltip)
        self.bt_pp_invalidate.setText("")
        # if QT_CONFIG(tooltip)
        self.bt_pp_run.setToolTip(
            QCoreApplication.translate("MainWindow", u"Run pipeline", None)
        )
        # endif // QT_CONFIG(tooltip)
        self.bt_pp_run.setText("")
        self.tb_tool_script.setTabText(
            self.tb_tool_script.indexOf(self.tb_pipeline_v2),
            QCoreApplication.translate("MainWindow", u"Pipeline", None),
        )
        self.bt_process_image.setText("")
        self.bt_reset_op.setText("")
        self.bt_select_tool.setText(
            QCoreApplication.translate("MainWindow", u"Selected tool: ", None)
        )
        self.bt_tool_help.setText("")
        self.bt_tool_show_code.setText(
            QCoreApplication.translate("MainWindow", u"Show code", None)
        )
        self.tb_tool_script.setTabText(
            self.tb_tool_script.indexOf(self.tab_tools),
            QCoreApplication.translate("MainWindow", u"Standalone tools", None),
        )
        self.bt_clear_result.setText(
            QCoreApplication.translate("MainWindow", u"Clear", None)
        )
        self.bt_set_as_selected.setText(
            QCoreApplication.translate("MainWindow", u"Set as selected", None)
        )
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.tab_pipeline_builder),
            QCoreApplication.translate("MainWindow", u"Pipeline builder", None),
        )
        self.groupBox_2.setTitle(
            QCoreApplication.translate("MainWindow", u"Pipeline:", None)
        )
        self.bt_pp_select_script.setText(
            QCoreApplication.translate("MainWindow", u"...", None)
        )
        self.lb_pp_thread_count.setText(
            QCoreApplication.translate("MainWindow", u"0", None)
        )
        self.label_9.setText(
            QCoreApplication.translate("MainWindow", u"Thread count:", None)
        )
        self.rb_pp_load_script.setText(
            QCoreApplication.translate("MainWindow", u"Pipeline", None)
        )
        self.rb_pp_default_process.setText(
            QCoreApplication.translate(
                "MainWindow", u"Default process (script pipeline)", None
            )
        )
        self.groupBox.setTitle(
            QCoreApplication.translate("MainWindow", u"Output options:", None)
        )
        self.lbl_csv_file_name.setText(
            QCoreApplication.translate("MainWindow", u"CSV file name:", None)
        )
        self.bt_pp_select_output_folder.setText(
            QCoreApplication.translate("MainWindow", u"...", None)
        )
        self.cb_pp_generate_series_id.setText(
            QCoreApplication.translate("MainWindow", u"Generate series id", None)
        )
        self.label_4.setText(
            QCoreApplication.translate(
                "MainWindow", u"max delta from first image in series:", None
            )
        )
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"minutes", None))
        self.label_2.setText(
            QCoreApplication.translate("MainWindow", u"Output folder:", None)
        )
        self.cb_pp_append_timestamp_to_output_folder.setText(
            QCoreApplication.translate(
                "MainWindow", u"Append timestamp to output folder", None
            )
        )
        self.cb_pp_append_experience_name.setText(
            QCoreApplication.translate(
                "MainWindow", u"Append experience name to output folder", None
            )
        )
        self.cb_pp_overwrite.setText(
            QCoreApplication.translate("MainWindow", u"Overwrite existing files?", None)
        )
        self.cb_pp_save_mosaics.setText(
            QCoreApplication.translate("MainWindow", u"Save mosaics", None)
        )
        self.label_6.setText(
            QCoreApplication.translate(
                "MainWindow", u"Images in queue (hover for more info)", None
            )
        )
        self.cb_queue_auto_scroll.setText(
            QCoreApplication.translate("MainWindow", u"Auto scroll", None)
        )
        self.bt_pp_reset.setText(QCoreApplication.translate("MainWindow", u"Reset", None))
        self.bt_pp_start.setText(QCoreApplication.translate("MainWindow", u"Start", None))
        self.chk_pp_show_last_item.setText(
            QCoreApplication.translate(
                "MainWindow", u"Show last processed item (performance hit)", None
            )
        )
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.tab_pipeline_processor),
            QCoreApplication.translate("MainWindow", u"Pipeline processor", None),
        )
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.tab_data_editor),
            QCoreApplication.translate("MainWindow", u"Data editor", None),
        )
        self.menu_file.setTitle(QCoreApplication.translate("MainWindow", u"File", None))
        self.mnu_recent_parsed_folders.setTitle(
            QCoreApplication.translate("MainWindow", u"Recent folders", None)
        )
        self.mnu_connect_to_db.setTitle(
            QCoreApplication.translate("MainWindow", u"Databases", None)
        )
        self.menuImage_lists.setTitle(
            QCoreApplication.translate("MainWindow", u"Image lists", None)
        )
        self.menu_settings.setTitle(
            QCoreApplication.translate("MainWindow", u"Settings", None)
        )
        # if QT_CONFIG(tooltip)
        self.menuVideo.setToolTip("")
        # endif // QT_CONFIG(tooltip)
        self.menuVideo.setTitle(QCoreApplication.translate("MainWindow", u"Video", None))
        self.menuFrame_duration.setTitle(
            QCoreApplication.translate("MainWindow", u"Frame duration", None)
        )
        self.menuResolution.setTitle(
            QCoreApplication.translate("MainWindow", u"Resolution", None)
        )
        self.menuAspect_ratio.setTitle(
            QCoreApplication.translate("MainWindow", u"Aspect ratio", None)
        )
        self.menuBackground_color.setTitle(
            QCoreApplication.translate("MainWindow", u"Background color", None)
        )
        self.menu_theme.setTitle(QCoreApplication.translate("MainWindow", u"Theme", None))
        self.menuCode_generation_mode.setTitle(
            QCoreApplication.translate("MainWindow", u"Code generation", None)
        )
        self.mnu_debug.setTitle(QCoreApplication.translate("MainWindow", u"Debug", None))
        self.menuPipeline_builder.setTitle(
            QCoreApplication.translate("MainWindow", u"Pipeline builder", None)
        )
        self.menu_source_image_scale_factor.setTitle(
            QCoreApplication.translate(
                "MainWindow", u"Source image down scale factor", None
            )
        )
        self.menu_help.setTitle(QCoreApplication.translate("MainWindow", u"Help", None))
        self.menu_view.setTitle(QCoreApplication.translate("MainWindow", u"View", None))
        self.menu_data_editor.setTitle(
            QCoreApplication.translate("MainWindow", u"Data editor", None)
        )

    # retranslateUi
