import os
from timeit import default_timer as timer
import logging

import numpy as np


logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from PySide2.QtCore import Slot, Signal, QObject, QRunnable

import ipso_phen.ipapi.base.ip_common as ipc
from ipso_phen.ipapi.class_pipelines.ip_factory import ipo_factory
from ipso_phen.ipapi.tools.comand_line_wrapper import ArgWrapper
from ipso_phen.ipapi.tools.common_functions import format_time, force_directories
from ipso_phen.ipapi.base.ipt_loose_pipeline import LoosePipeline


class IpsoRunnableSignals(QObject):

    on_started = Signal(str, bool)
    on_ending = Signal(bool, str, str)
    on_ended = Signal()
    on_update_images = Signal(bool, object)
    on_update_data = Signal(dict)
    on_feedback_log_str = Signal(str, str, bool)
    on_pipeline_progress = Signal(str, str, object, int, int)


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
        self.signals_holder.on_feedback_log_str.connect(
            kwargs.get("on_feedback_log_str", None)
        )
        self.signals_holder.on_pipeline_progress.connect(
            kwargs.get("on_pipeline_progress", None)
        )
        # Process data
        self.file_data = kwargs.get("file_data", {})
        self.data_base = kwargs.get("database", None)
        self.batch_process = kwargs.get("batch_process", False)
        self.scale_factor = kwargs.get("scale_factor", 1)
        self.target_module = kwargs.get("target_module", "")
        self.grid_search_mode = kwargs.get("grid_search_mode", False)

        self.ipt = kwargs.get("ipt", None)
        self.exec_param = kwargs.get("exec_param", None)
        self.pipeline = kwargs.get("pipeline", None)

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
            logger.critical("No image selected: Missing wrapper")

        return wrapper

    def _execute_param(self, image_dict):
        wrapper = self._get_wrapper(image_dict=image_dict)
        if wrapper is None:
            return False
        if self.ipt is None:
            logger.error("No ipt selected: Missing IPT")
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
            logger.exception("Unable to execute tool button")
        else:
            res = True
        finally:
            return res

    def _process_image(self, image_dict):
        res = False
        status_message = ""
        log_message = ""
        param_list = ""
        try:
            before = timer()
            wrapper = self._get_wrapper(image_dict=image_dict)
            if wrapper is None:
                logger.critical(
                    "No image selected: Missing wrapper",
                )
                status_message = "No image selected: Missing wrapper"
                return False
            if self.ipt is None:
                logger.error(
                    "No ipt selected: Missing IPT",
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
                status_message = f"Successfully processed {self.ipt.name} in {format_time(after - before)}"
                log_message = f"""Successfully processed {self.ipt.name}
                for "{wrapper.name}" in {format_time(after - before)}"""
            else:
                status_message = (
                    f"{self.ipt.name} processing failed: in {format_time(after - before)}"
                )
                logger.error(f"Processing {self.ipt.name} - Param list; {param_list}")
        except Exception as e:
            logger.exception("Unable to process image")
            status_message = "Exception while processing image, cf. log"
        finally:
            if status_message:
                self.signals_holder.on_ending.emit(res, status_message, log_message)
            return res

    def _process_pipeline(self, image_dict):
        status_message = ""
        log_message = None
        res = False
        try:
            before = timer()

            wrapper = self._get_wrapper(image_dict=image_dict)
            if wrapper is None:
                return
            if self.pipeline is None:
                logger.critical("No pipeline selected")
                return

            res = self.pipeline.execute(
                src_image=wrapper,
                call_back=self._pipeline_progress_callback,
                target_module=self.target_module,
                silent_mode=self.batch_process,
                grid_search_mode=self.grid_search_mode,
                target_data_base=self.data_base,
            )
            if not res:
                logger.error("Failed to process pipeline")
                status_message = "Failed to process pipeline, cf. log"
        except Exception as e:
            logger.exception("Unable to process pipeline")
            status_message = "Exception while processing pipeline, cf. log"
        finally:
            if status_message and not self.target_module:
                self.signals_holder.on_ending.emit(res, status_message, log_message)
            return res

    @Slot()
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
            logger.exception(f"Run process error {repr(e)}")
        finally:
            self.signals_holder.on_ended.emit()


class IpsoGroupProcessorSignals(QObject):

    on_ended = Signal()
    on_log_event = Signal(str, int, str, bool)
    on_image_ready = Signal(object)


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

        self.item = kwargs.get("item")
        self.database = kwargs.get("database")
        self.options = kwargs.get("options")
        self.script: LoosePipeline = kwargs.get("script")

        self.index = kwargs.get("index", -1)
        self.total = kwargs.get("total", -1)

    def _run_process(self, file_name, luid: str = ""):
        start_time = timer()

        try:
            res = self.script.execute(
                src_image=file_name,
                silent_mode=True,
                target_module="",
                additional_data={"luid": luid} if luid else {},
                write_data=True,
                target_data_base=self.database,
                overwrite_data=self.options.overwrite,
                store_images=False,
                options=self.options,
                call_back=None,
                index=self.index,
                total=self.total,
            )
        except Exception as e:
            logger.exception(f"Failed to process {file_name} because {repr(e)}")
            if self.script.wrapper is None or not self.script.wrapper.good_image:
                self.signals_holder.on_image_ready.emit(
                    np.full((100, 100, 3), ipc.C_FUCHSIA, np.uint8)
                )
            else:
                self.signals_holder.on_image_ready.emit(self.script.wrapper.current_image)
        else:
            if self.script is not None:
                self.signals_holder.on_image_ready.emit(self.script.mosaic)
            if res:
                self.signals_holder.on_log_event.emit(
                    self.script.wrapper.luid,
                    self.script.error_level,
                    f"Processed {self.script.wrapper.name} in {format_time(timer() - start_time)}",
                    True,
                )
            else:
                self.signals_holder.on_log_event.emit(
                    self.script.wrapper.luid,
                    logging.ERROR,
                    "Error detected while processing image, cf. log for more details",
                    True,
                )
        finally:
            if self.script.wrapper is not None:
                self.script.wrapper.image_list = None
                self.script.wrapper = None

    def run(self):
        try:
            if isinstance(self.item, tuple):
                self._run_process(self.item[0], luid=self.item[1])
            else:
                self._run_process(self.item)
        except Exception as e:
            logger.exception(f"Failed to process image because {repr(e)}")
        finally:
            self.signals_holder.on_ended.emit()
        self.script = None


class IpsoMassRunnerSignals(QObject):

    on_starting = Signal()
    on_launching = Signal(int)
    on_started = Signal(str)
    on_progress = Signal(int, int)
    on_feedback_log_str = Signal(str, str, bool)


class IpsoMassRunner(QRunnable):
    def __init__(self, **kwargs):
        super().__init__()
        # Signals
        self.signals_holder = IpsoMassRunnerSignals()
        self.signals_holder.on_starting.connect(kwargs.get("on_starting", None))
        self.signals_holder.on_launching.connect(kwargs.get("on_launching", None))
        self.signals_holder.on_started.connect(kwargs.get("on_started", None))
        self.signals_holder.on_progress.connect(kwargs.get("on_progress", None))
        self.signals_holder.on_feedback_log_str.connect(
            kwargs.get("on_feedback_log_str", None)
        )
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

                # Process all groups
                if not self.is_continue():
                    launch_state = "abort"
                    return
                groups_to_process_count = len(groups_to_process)
                self.signals_holder.on_launching.emit(groups_to_process_count)
                if groups_to_process_count > 0:
                    force_directories(self.pipeline.options.partials_path)
                    for i, item in enumerate(groups_to_process):
                        item_worker = IpsoGroupProcessor(
                            on_ended=self.on_item_ended,
                            on_log_event=self.on_log_item_event,
                            on_image_ready=self.on_item_image_ready,
                            item=item,
                            database=self._target_database,
                            options=self.pipeline.options,
                            script=None
                            if self.pipeline.script is None
                            else self.pipeline.script.copy(),
                            index=i,
                            total=groups_to_process_count,
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
                    "No images to process",
                    "No images to process",
                    log_level=logging.WARNING,
                )
        except Exception as e:
            logger.exception(f'Exception "{repr(e)}" while mass processing')
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
        self,
        status_msg: str,
        log_msg: str,
        use_status_as_log: bool,
    ) -> bool:
        self.signals_holder.on_feedback_log_str.emit(
            status_msg, log_msg, use_status_as_log
        )
        return self.is_continue()


class IpsoCsvBuilderSignals(QObject):

    on_start = Signal()
    on_progress = Signal(int, int)
    on_feedback_log_str = Signal(str, str, bool)
    on_end = Signal()


class IpsoCsvBuilder(QRunnable):
    def __init__(self, **kwargs):
        super().__init__()
        # Signals
        self.signals_holder = IpsoCsvBuilderSignals()
        self.signals_holder.on_start.connect(kwargs.get("on_start", None))
        self.signals_holder.on_progress.connect(kwargs.get("on_progress", None))
        self.signals_holder.on_feedback_log_str.connect(
            kwargs.get("on_feedback_log_str", None)
        )
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
        self,
        status_msg: str,
        log_msg: str,
        use_status_as_log: bool,
    ) -> bool:
        self.signals_holder.on_feedback_log_str.emit(
            status_msg, log_msg, use_status_as_log
        )
        return self.is_continue()

    def run(self):
        self.signals_holder.on_start.emit()
        try:
            # Build text merged file
            if (
                self.pipeline.options.write_result_text
                and not self.pipeline.options.threshold_only
            ):
                dataframe = self.pipeline.merge_result_files(
                    csv_file_name=self.root_csv_name + ".csv"
                )
            else:
                dataframe = None
            if dataframe is None:
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
                dataframe = dataframe.drop("view_option", axis=1)
                if self.group_by_series_id:
                    csv_sid_root_name = csv_root_name + "_sid"
                    if self.build_median_df:
                        dataframe.groupby("series_id").median().merge(dataframe).drop(
                            ["series_id"], axis=1
                        ).drop_duplicates().sort_values(by=["plant", "date_time"]).to_csv(
                            os.path.join(
                                self.pipeline.options.dst_path,
                                f"{csv_sid_root_name}_median.csv",
                            )
                        )
                        step_ += 1
                        self.signals_holder.on_progress.emit(step_, steps_)
                    if self.build_mean_df:
                        dataframe.groupby("series_id").mean().drop(
                            ["series_id"]
                        ).drop_duplicates().sort_values(by=["plant", "date_time"]).to_csv(
                            os.path.join(
                                self.pipeline.options.dst_path,
                                f"{csv_sid_root_name}_mean.csv",
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
                        dataframe.groupby("date").median().drop_duplicates().sort_values(
                            by=["plant", "date"]
                        ).to_csv(
                            os.path.join(
                                self.pipeline.options.dst_path,
                                f"{csv_day_root_name}_median.csv",
                            )
                        )
                        step_ += 1
                        self.signals_holder.on_progress.emit(step_, steps_)
                    if self.build_mean_df:
                        dataframe.groupby("date").mean().drop_duplicates().sort_values(
                            by=["plant", "date"]
                        ).to_csv(
                            os.path.join(
                                self.pipeline.options.dst_path,
                                f"{csv_day_root_name}_mean.csv",
                            )
                        )
                        step_ += 1
                        self.signals_holder.on_progress.emit(step_, steps_)
                self.signals_holder.on_feedback_log_str.emit(
                    "Built additional CSV files", " --- Built additional CSV files ---"
                )
        except Exception as e:
            logger.exception("Unable to finalize pipeline")
        finally:
            self.signals_holder.on_end.emit()
