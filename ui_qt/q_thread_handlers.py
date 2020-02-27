import os
from timeit import default_timer as timer
import csv

import numpy as np
import pandas as pd

from PyQt5.QtCore import pyqtSlot, Qt, pyqtSignal, QObject, QTimer, QRunnable, QThreadPool

import tools.error_holder as err
import ip_base.ip_common as ipc
from class_pipelines.ip_factory import ipo_factory
from tools.comand_line_wrapper import ArgWrapper
from tools.common_functions import format_time, force_directories
from file_handlers.fh_base import file_handler_factory
from ui_qt import ui_consts


class IpsoRunnableSignals(QObject):

    on_started = pyqtSignal(str, bool)
    on_ending = pyqtSignal(bool, str, str, object)
    on_ended = pyqtSignal()
    on_update_images = pyqtSignal(bool, object)
    on_update_data = pyqtSignal(dict)
    on_feedback_log_object = pyqtSignal(str, object)
    on_feedback_log_str = pyqtSignal(str, str, bool)
    on_pipeline_progress = pyqtSignal(str, str, object, int, int)


class IpsoRunnable(QRunnable):
    def __init__(self, **kwargs):
        super().__init__()
        # Signals
        self.signals_holder = IpsoRunnableSignals()
        self.signals_holder.on_started.connect(kwargs.get("on_started", None))
        self.signals_holder.on_ending.connect(kwargs.get("on_ending", None))
        self.signals_holder.on_ended.connect(kwargs.get("on_ended", None))
        self.signals_holder.on_update_images.connect(kwargs.get("on_update_images", None))
        self.signals_holder.on_update_data.connect(kwargs.get("on_update_data", None))
        self.signals_holder.on_feedback_log_object.connect(
            kwargs.get("on_feedback_log_object", None)
        )
        self.signals_holder.on_feedback_log_str.connect(kwargs.get("on_feedback_log_str", None))
        self.signals_holder.on_pipeline_progress.connect(kwargs.get("on_pipeline_progress", None))
        # Process data
        self.file_data = kwargs.get("file_data", {})
        self.data_base = kwargs.get("database", None)
        self.batch_process = kwargs.get("batch_process", False)
        self.scale_factor = kwargs.get("scale_factor", 1)
        self.target_module = kwargs.get("target_module", "")

        self.ipt = kwargs.get("ipt", None)
        self.exec_param = kwargs.get("exec_param", None)
        self.pipeline = kwargs.get("pipeline", None)

        # Error holder
        self.error_list = err.ErrorHolder(self)

    def _pipeline_progress_callback(
        self, result: bool, msg: str, sender: object, current_step: int, total_step: int
    ):
        self.signals_holder.on_pipeline_progress.emit(
            result, msg, sender, current_step, total_step
        )

    def _get_wrapper(self, image_dict):
        """Returns wrapper built from the image dictionnary passed

        Arguments:
            image_dict {dict} -- Contains image information

        Returns:
            AbstracImageWrapper -- Image wrapper
        """
        file_path = image_dict.get("path", None)
        if os.path.isfile(file_path):
            wrapper = ipo_factory(
                file_path,
                ArgWrapper(
                    dst_path="dst",
                    store_images=True,
                    write_images="none",
                    write_result_text=False,
                    overwrite=False,
                    seed_output=False,
                    threshold_only=False,
                ),
                data_base=self.data_base.copy(),
                scale_factor=self.scale_factor,
            )
            wrapper.lock = True

            if wrapper is None:
                self.error_list.add_error(
                    new_error_text="No image selected: Missing wrapper",
                    new_error_kind="wrapper_error",
                    new_error_level=err.ERR_LVL_CRITICAL,
                )
                self.on_log_error("No image selected: Missing wrapper", self.error_list)

            return wrapper
        else:
            return None

    def _execute_param(self, image_dict):
        wrapper = self._get_wrapper(image_dict=image_dict)
        if wrapper is None:
            return False
        if self.ipt is None:
            self.error_list.add_error(
                new_error_text="No ipt selected: Missing IPT",
                new_error_kind="ipt_error",
                new_error_level=err.ERR_LVL_ERROR,
            )
            self.signals_holder.on_feedback_log_object.emit(
                "No ipt selected: Missing IPT", self.error_list
            )
            return False
        try:
            act = self.ipt.execute(param=self.exec_param, wrapper=wrapper)
            if (act == "process_wrapper") and self.ipt.real_time:
                res = self.ipt.process_wrapper(wrapper=wrapper)
                self.signals_holder.on_update_images.emit(self.batch_process, self.ipt)
            elif act == "print_images":
                self.signals_holder.on_update_images.emit(self.batch_process, self.ipt)
        except Exception as e:
            res = False
            self.error_list.add_error(
                new_error_text="Unable to execute tool button",
                new_error_kind="exec_param",
                new_error_level=err.ERR_LVL_EXCEPTION,
            )
            self.error_list.add_error(
                new_error_text=repr(e),
                new_error_kind="grid_search_error",
                new_error_level=err.ERR_LVL_EXCEPTION,
            )
            self.signals_holder.on_feedback_log_object.emit(
                "Unable to execute tool button", self.error_list
            )
        else:
            res = True
        finally:
            return res

    def _process_image(self, image_dict):
        res = False
        status_message = ""
        log_message = ""
        param_list = ""
        log_object = self.error_list
        try:
            before = timer()
            wrapper = self._get_wrapper(image_dict=image_dict)
            if wrapper is None:
                self.error_list.add_error(
                    new_error_text="No image selected: Missing wrapper",
                    new_error_kind="wrapper_error",
                    new_error_level=err.ERR_LVL_CRITICAL,
                )
                status_message = "No image selected: Missing wrapper"
                return False
            if self.ipt is None:
                self.error_list.add_error(
                    new_error_text="No ipt selected: Missing IPT",
                    new_error_kind="ipt_error",
                    new_error_level=err.ERR_LVL_ERROR,
                )
                status_message = "No ipt selected: Missing IPT"
                return False

            param_list = self.ipt.input_params_as_html(
                exclude_defaults=False, excluded_params=("progress_callback",)
            )
            res = self.ipt.process_wrapper(wrapper=wrapper)

            self.signals_holder.on_update_images.emit(self.batch_process, self.ipt)

            after = timer()
            if res:
                status_message = (
                    f"Successfully processed {self.ipt.name} in {format_time(after - before)}"
                )
                log_message = f"""Successfully processed {self.ipt.name}
                for "{wrapper.name}" in {format_time(after - before)}"""
            else:
                status_message = (
                    f"{self.ipt.name} processing failed: in {format_time(after - before)}"
                )
                wrapper.error_holder.add_error(
                    f"Processing {self.ipt.name}",
                    new_error_kind="ipt_error",
                    new_error_level=err.ERR_LVL_ERROR,
                )
                wrapper.error_holder.add_error(
                    new_error_text=f"Param list; {param_list}",
                    new_error_kind="ipt_error",
                    new_error_level=err.ERR_LVL_ERROR,
                )
                log_object = wrapper.error_holder
        except Exception as e:
            self.error_list.add_error(
                new_error_text="Unable to process image",
                new_error_kind="ipt_error",
                new_error_level=err.ERR_LVL_EXCEPTION,
            )
            self.error_list.add_error(
                new_error_text=repr(e),
                new_error_kind="ipt_error",
                new_error_level=err.ERR_LVL_EXCEPTION,
            )
            if self.ipt is not None:
                self.error_list.add_error(
                    f"Processing {self.ipt.name}",
                    new_error_kind="ipt_error",
                    new_error_level=err.ERR_LVL_EXCEPTION,
                )
            if param_list:
                self.error_list.add_error(
                    f"Params: {param_list}",
                    new_error_kind="ipt_error",
                    new_error_level=err.ERR_LVL_EXCEPTION,
                )
            status_message = f"Exception while processing image, cf. log"
            self.signals_holder.on_feedback_log_object.emit(
                "Unable to process image", self.error_list
            )
        finally:
            if status_message:
                self.signals_holder.on_ending.emit(res, status_message, log_message, log_object)
            return res

    def _process_pipeline(self, image_dict):
        status_message = ""
        log_message = None
        res = False
        log_object = self.error_list
        try:
            before = timer()

            wrapper = self._get_wrapper(image_dict=image_dict)
            if wrapper is None:
                return
            if self.pipeline is None:
                self.error_list.add_error(
                    new_error_text="No pipeline selected",
                    new_error_kind="pipeline_process_error",
                    new_error_level=err.ERR_LVL_CRITICAL,
                )
                status_message = "No pipeline selected"
                return

            log_object = self.pipeline.last_error

            res = self.pipeline.execute(
                src_image=wrapper,
                call_back=self._pipeline_progress_callback,
                target_module=self.target_module,
                silent_mode=self.batch_process,
            )
            if not res:
                log_object.add_error(
                    new_error_text="Failed to process pipeline",
                    new_error_kind="pipeline_process_error",
                    new_error_level=err.ERR_LVL_ERROR,
                )
                status_message = f"Failed to process pipeline, cf. log"
        except Exception as e:
            log_object.add_error(
                new_error_text="Unable to process pipeline",
                new_error_kind="pipeline_process_error",
                new_error_level=err.ERR_LVL_EXCEPTION,
            )
            status_message = f"Exception while processing pipeline, cf. log"
            self.signals_holder.on_feedback_log_object.emit(
                "Unable to process pipeline", log_object
            )
        finally:
            if status_message and not self.target_module:
                self.signals_holder.on_ending.emit(res, status_message, log_message, log_object)
            return res

    @pyqtSlot()
    def run(self):
        try:
            if self.exec_param is not None:
                self.signals_holder.on_started.emit("param", self.batch_process)
                self._execute_param(self.file_data)
            elif self.pipeline is not None:
                if self.target_module:
                    self.signals_holder.on_started.emit("module", self.batch_process)
                else:
                    self.signals_holder.on_started.emit("pipeline", self.batch_process)
                self._process_pipeline(self.file_data)
            elif self.ipt is not None:
                self.signals_holder.on_started.emit("ipt", self.batch_process)
                self._process_image(self.file_data)
            else:
                raise NotImplementedError
        except Exception as e:
            self.error_list.add_error(
                new_error_text="Run process",
                new_error_kind="run_error",
                new_error_level=err.ERR_LVL_EXCEPTION,
            )
            self.error_list.add_error(
                new_error_text=repr(e),
                new_error_kind="run_error",
                new_error_level=err.ERR_LVL_EXCEPTION,
            )
            log_message = f'Exception "{repr(e)}" running process'
            self.signals_holder.on_feedback_log_object.emit("Run process", self.error_list)
        finally:
            self.signals_holder.on_ended.emit()


class IpsoGroupProcessorSignals(QObject):

    on_ended = pyqtSignal()
    on_log_event = pyqtSignal(str, str, str, bool)
    on_image_ready = pyqtSignal(object)


class IpsoGroupProcessor(QRunnable):
    def __init__(self, **kwargs):
        super().__init__()
        # Signals
        self.signals_holder = IpsoGroupProcessorSignals()
        on_ended = kwargs.get("on_ended", None)
        if on_ended is not None:
            self.signals_holder.on_ended.connect(on_ended)
        on_log_event = kwargs.get("on_log_event", None)
        if on_log_event is not None:
            self.signals_holder.on_log_event.connect(on_log_event)
        on_image_ready = kwargs.get("on_image_ready", None)
        if on_image_ready is not None:
            self.signals_holder.on_image_ready.connect(on_image_ready)

        self.file_path = kwargs.get("file_path")
        self.database = kwargs.get("database")
        self.options = kwargs.get("options")
        self.script = kwargs.get("script")

    def _run_process(self, file_name, luid: str = ""):
        start_time = timer()
        ipo = ipo_factory(
            file_name,
            self.options,
            force_abstract=self.script is not None,
            data_base=self.database,
        )
        if ipo is None:
            err_holder = err.ErrorHolder(self)
            err_holder.add_error(
                new_error_text=file_name,
                new_error_kind="process_error",
                new_error_level=err.ERR_LVL_ERROR,
            )
            err_holder.add_error(
                new_error_text="Unable to build wrapper from file",
                new_error_kind="process_error",
                new_error_level=err.ERR_LVL_ERROR,
            )
            self.signals_holder.on_log_event.emit(
                ipo.luid,
                "exception",
                f"{ui_consts.LOG_EXCEPTION_STR}: {err_holder.to_html()}",
                True,
            )
            err_holder = None
        elif not ipo.check_source_image():
            err_holder = err.ErrorHolder(self)
            err_holder.add_error(
                new_error_text=file_name,
                new_error_kind="process_error",
                new_error_level=err.ERR_LVL_ERROR,
            )
            err_holder.add_error(
                new_error_text="Image seems to be corrupted",
                new_error_kind="process_error",
                new_error_level=err.ERR_LVL_ERROR,
            )
            self.signals_holder.on_log_event.emit(
                ipo.luid,
                "exception",
                f"{ui_consts.LOG_EXCEPTION_STR}: {err_holder.to_html()}",
                True,
            )
            err_holder = None
        elif ipo is not None and ipo.good_image:
            ipo.store_images = False
            try:
                if self.script is None:
                    res = ipo.process_image(threshold_only=self.options.threshold_only)
                else:
                    self.script.image_output_path = ipo.dst_path
                    res = self.script.execute(
                        src_image=ipo, call_back=None, target_module=None, silent_mode=True,
                    )
            except Exception as e:
                if self.script is None:
                    err_holder = err.ErrorHolder(self)
                    err_holder.add_error(
                        new_error_text=file_name,
                        new_error_kind="process_error",
                        new_error_level=err.ERR_LVL_EXCEPTION,
                    )
                    err_holder.add_error(
                        new_error_text=f"Failed to process image because {repr(e)}",
                        new_error_kind="process_error",
                        new_error_level=err.ERR_LVL_EXCEPTION,
                    )
                    error_text = err_holder.to_html()
                    err_holder = None
                else:
                    self.script.last_error.add_error(
                        new_error_text=f"Failed to process image because {repr(e)}",
                        new_error_level=err.ERR_LVL_EXCEPTION,
                        new_error_kind="process_error",
                    )
                    error_text = self.script.last_error.to_html()

                if ipo is None or not ipo.good_image:
                    self.signals_holder.on_image_ready.emit(
                        np.full((100, 100, 3), ipc.C_FUCHSIA, np.uint8)
                    )
                else:
                    self.signals_holder.on_image_ready.emit(ipo.current_image)
                self.signals_holder.on_log_event.emit(
                    ipo.luid, "exception", f"{ui_consts.LOG_EXCEPTION_STR}: {error_text}", True,
                )
            else:
                if res:
                    try:
                        if luid:
                            ipo.csv_data_holder.update_csv_value("series_id", luid, True)
                        with open(ipo.csv_file_path, "w", newline="") as csv_file_:
                            wr = csv.writer(csv_file_, quoting=csv.QUOTE_NONE)
                            wr.writerow(ipo.csv_data_holder.header_to_list())
                            wr.writerow(ipo.csv_data_holder.data_to_list())
                        if self.script is not None:
                            self.signals_holder.on_image_ready.emit(self.script.mosaic)
                    except Exception as e:
                        if self.script is None:
                            err_holder = err.ErrorHolder(
                                self,
                                (
                                    dict(text=ipo.name, type="csv_write_error"),
                                    dict(
                                        text=f"Failed to write image data because {repr(e)}",
                                        type="csv_write_error",
                                    ),
                                ),
                            )
                            error_text = err_holder.to_html()
                            err_holder = None
                        else:
                            self.script.last_error.add_error(
                                new_error_text=f"Failed to process image because {repr(e)}",
                                new_error_level=err.ERR_LVL_EXCEPTION,
                                new_error_kind="process_error",
                            )
                            error_text = self.script.last_error.to_html()
                        self.signals_holder.on_log_event.emit(
                            ipo.luid,
                            "exception",
                            f"{ui_consts.LOG_EXCEPTION_STR}: {error_text}",
                            True,
                        )
                    else:
                        end_time = timer()
                        if self.script is None or self.script.last_error.error_count == 0:
                            self.signals_holder.on_log_event.emit(
                                ipo.luid,
                                "success",
                                f"Successfully processed {ipo.name} in {format_time(end_time - start_time)}",
                                True,
                            )
                        elif self.script is not None and self.script.last_error.error_count > 0:
                            self.signals_holder.on_log_event.emit(
                                ipo.luid, "warning", self.script.last_error.to_html(), True,
                            )
                else:
                    self.signals_holder.on_log_event.emit(
                        ipo.luid,
                        "failure",
                        f"{ui_consts.LOG_ERROR_STR}: {ipo.error_holder.to_html()}",
                        True,
                    )
            finally:
                ipo.image_list = None
                ipo = None
        else:
            err_holder = err.ErrorHolder(
                self, (dict(text=f'Unable to process "{file_name}"', type="unknown_error"),)
            )
            self.signals_holder.on_log_event.emit(
                "", "failure", f"{ui_consts.LOG_ERROR_STR}: {err_holder.to_html()}", True
            )
            res = False

    def run(self):
        if isinstance(self.file_path, list):
            luid = file_handler_factory(self.file_path[0]).luid
            for file_name_ in self.file_path:
                try:
                    self._run_process(file_name_, luid=luid)
                except Exception as e:
                    err_holder = err.ErrorHolder(
                        self,
                        (
                            dict(text=file_name_, type="process_error"),
                            dict(
                                text=f"Failed to process image because {repr(e)}",
                                type="process_error",
                            ),
                        ),
                    )
                    self.signals_holder.on_log_str.emit(
                        "", "exception", f"{ui_consts.LOG_EXCEPTION_STR}: {err_holder.to_html()}"
                    )
                    err_holder = None
            self.signals_holder.on_ended.emit()
        else:
            try:
                self._run_process(self.file_path)
            finally:
                self.signals_holder.on_ended.emit()
        self.script = None


class IpsoMassRunnerSignals(QObject):

    on_starting = pyqtSignal()
    on_launching = pyqtSignal(int)
    on_started = pyqtSignal(str)
    on_progress = pyqtSignal(int, int)
    on_feedback_log_object = pyqtSignal(str, object)
    on_feedback_log_str = pyqtSignal(str, str, bool)


class IpsoMassRunner(QRunnable):
    def __init__(self, **kwargs):
        super().__init__()
        # Error holder
        self.error_list = err.ErrorHolder(self)
        # Signals
        self.signals_holder = IpsoMassRunnerSignals()
        self.signals_holder.on_starting.connect(kwargs.get("on_starting", None))
        self.signals_holder.on_launching.connect(kwargs.get("on_launching", None))
        self.signals_holder.on_started.connect(kwargs.get("on_started", None))
        self.signals_holder.on_progress.connect(kwargs.get("on_progress", None))
        self.signals_holder.on_feedback_log_object.connect(
            kwargs.get("on_feedback_log_object", None)
        )
        self.signals_holder.on_feedback_log_str.connect(kwargs.get("on_feedback_log_str", None))
        # Callbacks
        self.check_stop = kwargs.get("check_stop", None)
        # States
        self._is_continue = False
        self._reported_stop = False
        self._target_database = kwargs.get("data_base")
        self._multithread = kwargs.get("multithread", True)
        # Create pipeline
        self.pipeline = kwargs.get("pipeline")
        self.group_time_delta = kwargs.get("group_time_delta")

        # Emitters for the items
        self.on_item_ended = kwargs.get("on_item_ended")
        self.on_log_item_event = kwargs.get("on_log_item_event")
        self.on_item_image_ready = kwargs.get("on_item_image_ready")

        # Process
        self.pipeline.ensure_root_output_folder()
        self.pipeline.log_callback = self.do_feedback
        self.pipeline.progress_callback = self.do_progress
        self.pipeline.log_item = self.on_log_item_event

        self.item_thread_pool = kwargs.get("items_thread_pool")

    def run(self):
        self.signals_holder.on_starting.emit()
        launch_state = "ok"
        try:
            if self.pipeline.accepted_files:
                # build series
                if not self.is_continue():
                    launch_state = "abort"
                    return
                groups_to_process = self.pipeline.prepare_groups(self.group_time_delta)

                # If overwrite is disabled remove all files already analysed
                if not self.is_continue():
                    launch_state = "abort"
                    return
                groups_to_process = self.pipeline.handle_existing_data(groups_to_process)

                # Process all groups
                if not self.is_continue():
                    launch_state = "abort"
                    return
                groups_to_process_count = len(groups_to_process)
                self.signals_holder.on_launching.emit(groups_to_process_count)
                if groups_to_process_count > 0:
                    force_directories(self.pipeline.options.partials_path)
                    for i, group in enumerate(groups_to_process):
                        item_worker = IpsoGroupProcessor(
                            on_ended=self.on_item_ended,
                            on_log_event=self.on_log_item_event,
                            on_image_ready=self.on_item_image_ready,
                            file_path=group,
                            database=self._target_database,
                            options=self.pipeline.options,
                            script=None
                            if self.pipeline.script is None
                            else self.pipeline.script.copy(),
                        )
                        if not self.is_continue():
                            launch_state = "abort"
                            return
                        self.signals_holder.on_progress.emit(i, len(groups_to_process))
                        if self._multithread:
                            self.item_thread_pool.start(item_worker)
                        else:
                            item_worker.run()
            else:
                self.signals_holder.on_feedback_log_str.emit(
                    "No images to process", f"{ui_consts.LOG_WARNING_STR}: No images to process"
                )
        except Exception as e:
            self.error_list.add_error(
                new_error_text="Mass processing",
                new_error_kind="mass_process_error",
                new_error_level=err.ERR_LVL_EXCEPTION,
            )
            self.error_list.add_error(
                new_error_text=repr(e),
                new_error_kind="mass_process_error",
                new_error_level=err.ERR_LVL_EXCEPTION,
            )
            log_message = f'Exception "{repr(e)}" while mass processing'
            self.signals_holder.on_feedback_log_object.emit("Mass processing", self.error_list)
            launch_state = "exception"
        finally:
            if launch_state != "ok":
                self.signals_holder.on_feedback_log_str.emit(
                    "Failed to launch mass process, cf. log",
                    "Failed to launch mass process, cancelling queued jobs",
                    False,
                )
                self.item_thread_pool.clear()
                self.item_thread_pool.waitForDone(-1)
            self.signals_holder.on_started.emit(launch_state)

    def is_continue(self):
        self._is_continue = (self.check_stop is None) or not self.check_stop()
        if not self._is_continue and not self._reported_stop:
            self.signals_holder.on_feedback_log_str.emit(
                "Stopping mass process, please wait...", "", True
            )
            self._reported_stop = True
        return self._is_continue

    def do_progress(self, step: int, total: int) -> bool:
        self.signals_holder.on_progress.emit(step, total)
        return self.is_continue()

    def do_feedback(
        self, status_msg: str, log_msg: str, obj: object, use_status_as_log: bool
    ) -> bool:
        if obj is None:
            self.signals_holder.on_feedback_log_str.emit(status_msg, log_msg, use_status_as_log)
        else:
            self.signals_holder.on_feedback_log_object.emit(status_msg, obj)
        return self.is_continue()


class IpsoCsvBuilderSignals(QObject):

    on_start = pyqtSignal()
    on_progress = pyqtSignal(int, int)
    on_feedback_log_object = pyqtSignal(str, object)
    on_feedback_log_str = pyqtSignal(str, str, bool)
    on_end = pyqtSignal()


class IpsoCsvBuilder(QRunnable):
    def __init__(self, **kwargs):
        super().__init__()
        # Signals
        self.signals_holder = IpsoCsvBuilderSignals()
        self.signals_holder.on_start.connect(kwargs.get("on_start", None))
        self.signals_holder.on_progress.connect(kwargs.get("on_progress", None))
        self.signals_holder.on_feedback_log_object.connect(
            kwargs.get("on_feedback_log_object", None)
        )
        self.signals_holder.on_feedback_log_str.connect(kwargs.get("on_feedback_log_str", None))
        self.signals_holder.on_end.connect(kwargs.get("on_end", None))
        # Callbacks
        self.check_stop = kwargs.get("check_stop", None)
        # States
        self.root_csv_name = kwargs.get("root_csv_name")
        self.group_by_series_id = False and kwargs.get("group_by_series_id")
        self.group_by_hour = False and kwargs.get("group_by_hour")
        self.group_by_day = False and kwargs.get("group_by_day")
        self.build_median_df = False and kwargs.get("build_median_df")
        self.build_mean_df = False and kwargs.get("build_mean_df")
        self._is_continue = True
        self._reported_stop = False
        self._last_process_events = timer()
        # Data
        self.pipeline = kwargs.get("pipeline")
        self.pipeline.ensure_root_output_folder()
        self.pipeline.log_callback = self.do_feedback
        self.pipeline.progress_callback = self.do_progress

    def is_continue(self):
        in_time = timer()
        if in_time - self._last_process_events > 1:
            self._last_process_events = in_time
            self._is_continue = self.check_stop is None or not self.check_stop()
            if not self._is_continue and not self._reported_stop:
                self.signals_holder.on_feedback_log_str.emit(
                    "Stopping mass process, please wait...", "", True
                )
                self._reported_stop = True
        return self._is_continue

    def do_progress(self, step: int, total: int) -> bool:
        self.signals_holder.on_progress.emit(step, total)
        return self.is_continue()

    def do_feedback(
        self, status_msg: str, log_msg: str, obj: object, use_status_as_log: bool
    ) -> bool:
        if obj is None:
            self.signals_holder.on_feedback_log_str.emit(status_msg, log_msg, use_status_as_log)
        else:
            self.signals_holder.on_feedback_log_object.emit(status_msg, obj)
        return self.is_continue()

    def run(self):
        self.signals_holder.on_start.emit()
        try:
            # Build text merged file
            if (
                self.pipeline.options.write_result_text
                and not self.pipeline.options.threshold_only
            ):
                df = self.pipeline.merge_result_files(csv_file_name=self.root_csv_name + ".csv")
            if df is None:
                return
            # Get the total number of steps
            steps_ = 0
            if self.group_by_series_id:
                if self.build_median_df:
                    steps_ += 1
                if self.build_mean_df:
                    steps_ += 1
            if self.group_by_hour:
                if self.build_median_df:
                    steps_ += 1
                if self.build_mean_df:
                    steps_ += 1
            if self.group_by_day:
                if self.build_median_df:
                    steps_ += 1
                if self.build_mean_df:
                    steps_ += 1
            if steps_ > 0:
                self.signals_holder.on_feedback_log_str.emit(
                    "Building additional CSV files",
                    " --- Building additional CSV files ---",
                    False,
                )
                step_ = 0
                step_ += 1
                self.signals_holder.on_progress.emit(step_, steps_)
                csv_root_name = self.root_csv_name
                if "_raw_data" in csv_root_name:
                    csv_root_name = csv_root_name.replace("_raw_data", "")
                if csv_root_name.endswith(".csv"):
                    csv_root_name = csv_root_name.replace(".csv", "")
                df = df.drop("view_option", axis=1)
                if self.group_by_series_id:
                    csv_sid_root_name = csv_root_name + "_sid"
                    if self.build_median_df:
                        df.groupby("series_id").median().merge(df).drop(
                            ["series_id"], axis=1
                        ).drop_duplicates().sort_values(by=["plant", "date_time"]).to_csv(
                            os.path.join(
                                self.pipeline.options.dst_path, f"{csv_sid_root_name}_median.csv"
                            )
                        )
                        step_ += 1
                        self.signals_holder.on_progress.emit(step_, steps_)
                    if self.build_mean_df:
                        df.groupby("series_id").mean().drop(
                            ["series_id"]
                        ).drop_duplicates().sort_values(by=["plant", "date_time"]).to_csv(
                            os.path.join(
                                self.pipeline.options.dst_path, f"{csv_sid_root_name}_mean.csv"
                            )
                        )
                        step_ += 1
                        self.signals_holder.on_progress.emit(step_, steps_)
                if self.group_by_hour:
                    csv_hour_root_name = csv_root_name + "_hour"
                    if self.build_median_df:
                        pass
                        step_ += 1
                        self.signals_holder.on_progress.emit(step_, steps_)
                    if self.build_mean_df:
                        pass
                        step_ += 1
                        self.signals_holder.on_progress.emit(step_, steps_)
                if self.group_by_day:
                    csv_day_root_name = csv_root_name + "_day"
                    if self.build_median_df:
                        df.groupby("date").median().drop_duplicates().sort_values(
                            by=["plant", "date"]
                        ).to_csv(
                            os.path.join(
                                self.pipeline.options.dst_path, f"{csv_day_root_name}_median.csv"
                            )
                        )
                        step_ += 1
                        self.signals_holder.on_progress.emit(step_, steps_)
                    if self.build_mean_df:
                        df.groupby("date").mean().drop_duplicates().sort_values(
                            by=["plant", "date"]
                        ).to_csv(
                            os.path.join(
                                self.pipeline.options.dst_path, f"{csv_day_root_name}_mean.csv"
                            )
                        )
                        step_ += 1
                        self.signals_holder.on_progress.emit(step_, steps_)
                self.signals_holder.on_feedback_log_str.emit(
                    "Built additional CSV files", " --- Built additional CSV files ---"
                )
        except Exception as e:
            err_holder = err.ErrorHolder(
                self,
                (
                    dict(text="Unable to finalize pipeline", type="csv_error"),
                    dict(text=f"{repr(e)}", type="csv_error"),
                ),
            )
            self.signals_holder.on_feedback_log_str.emit(
                "", f"{ui_consts.LOG_EXCEPTION_STR}: {err_holder.to_html()}", False
            )
            err_holder = None
        finally:
            self.signals_holder.on_end.emit()
