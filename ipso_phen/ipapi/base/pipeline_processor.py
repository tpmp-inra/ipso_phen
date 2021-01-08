import multiprocessing as mp
import os
import sys
from collections import Counter, defaultdict
from collections import namedtuple
import logging
from time import sleep
from timeit import default_timer as timer
from typing import Union
import threading
import gc

import pandas as pd
from tqdm import tqdm

from ipso_phen.ipapi.file_handlers.fh_base import file_handler_factory
from ipso_phen.ipapi.tools.comand_line_wrapper import ArgWrapper
from ipso_phen.ipapi.tools.common_functions import (
    time_method,
    force_directories,
    format_time,
)
from ipso_phen.ipapi.tools.image_list import ImageList
from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor

USE_TQDM = True

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))
if USE_TQDM is False:
    logger.addHandler(logging.StreamHandler(sys.stdout))


def _dummy_worker(args):
    return args


def _pipeline_worker(arg):
    """Creates an ip object and executs

    Arguments:
        arg {list} -- file_path, log_timings, options

    Returns:
        boolean -- is return successful
        string -- wrapper name
        string -- error message
    """

    # Extract parameters
    file_path, options, script, db = arg

    start_time = timer()
    try:
        bool_res = script.execute(
            src_image=file_path if isinstance(file_path, str) else file_path[0],
            silent_mode=True,
            target_module="",
            additional_data={"luid": file_path[1]}
            if isinstance(file_path, tuple)
            else {},
            write_data=True,
            target_data_base=db,
            overwrite_data=options.overwrite,
            store_images=False,
            options=options,
            call_back=None,
        )
    except Exception as e:
        return {
            "result": False,
            "result_as_text": "",
            "image_name": file_path,
            "error_message": repr(e),
            "time_spent": format_time(timer() - start_time),
        }
    else:
        return {
            "result": bool_res,
            # "result_as_text": "",
            "result_as_text": script.text_result,
            "image_name": "Unknown" if script.wrapper is None else str(script.wrapper),
            "error_message": "",
            "time_spent": format_time(timer() - start_time),
        }


class PipelineProcessor:
    """Process image processing pipelines according to options

    script_path: calling script path (use __file__), required = true

    kwargs (only used if no command line is present):
    - src_path: filename or folder, required=True
    - dst_path: Output directory for image files, required=False.
    - store_images: Store debug images while processing, required= False, default=False)
    - write_images: Write/print debug images, required= False, default=False)
    - write_result: Write output images, required= False, default=True)
    - write_result_text: Write result text file, required= False, default=False
    - write_mosaic: Write mosaic image in a separate folder
    - overwrite: Overwrite already analysed files, required= False, default=False
    - seed_output: Suffix output folder with date, required= False, default=False
    - threshold_only: if true no analysis will be performed after threshold, required=False, default=False
    """

    def __init__(self, database, **kwargs):
        """ Initializes command line wrapper an properties """
        self._report_progress = kwargs.pop("report_progress", True)
        self.options = ArgWrapper(**kwargs)
        self._target_database = database
        self._process_errors = 0
        self.accepted_files = []
        self._last_signature = ""
        self.progress_callback = None
        self.error_callback = None
        self.abort_callback = None
        self.log_item = None
        self.script = None
        self._tqdm = None
        self._progress_total = 0
        self._progress_step = 0
        self._last_garbage_collected = timer()

    def build_files_list(self, src_path: str, flatten_list=True, **kwargs):
        """Build a list containing all the files that will be parsed

        Returns:
            int -- number of files kept
        """
        accepted_extensions_ = (".jpg", ".tiff", ".png", ".bmp")

        if os.path.isfile(src_path):  # File passed as argument
            self.accepted_files = [src_path]
        elif os.path.isdir(src_path):  # Folder passed as argument
            img_lst = ImageList(accepted_extensions_)
            if type(src_path) is list:
                img_lst.add_folders(src_path)
            else:
                img_lst.add_folder(src_path)
            self.accepted_files = img_lst.filter(
                masks=self.masks, flat_list_out=flatten_list
            )
        else:
            self.accepted_files = []

        return len(self.accepted_files) > 0

    def ensure_root_output_folder(self):
        """Creates output folder if does not exist"""

        if not os.path.exists(self.options.dst_path):
            os.makedirs(self.options.dst_path)

    def log_result(self, wrapper_res: dict, wrapper_index, total, separator):
        spaces_ = len(str(total))
        if wrapper_res["result_as_text"]:
            rat = wrapper_res["result_as_text"]
        else:
            rat = "OK" if wrapper_res["result"] is True else "FAIL"
            rat += f" (TC: {threading.active_count()})"
        if timer() - self._last_garbage_collected > 60:
            self._last_garbage_collected = timer()
            gc.collect()
            rat += " (GC)"
        msg = (
            f"{(wrapper_index + 1):{spaces_}d}/{total}"
            + " - "
            + rat
            + f"{separator}"
            + wrapper_res["image_name"]
            + (
                f" - {wrapper_res['error_message']}"
                if wrapper_res["error_message"]
                else ""
            )
            + f"{separator}"
            + f"Image processed in: {wrapper_res['time_spent']}"
        )
        logger.info(msg)
        if wrapper_res["result"] is not True:
            self.report_error(logging.ERROR, msg)
        if wrapper_res["result"] is not True:
            self._process_errors += 1
        return msg

    def handle_result(self, wrapper_res: dict, wrapper_index, total):
        if not wrapper_res:
            logger.error("Process error - UNKNOWN ERROR")
            self.report_error(logging.ERROR, "Process error - UNKNOWN ERROR")
            self._process_errors += 1
        else:
            self.log_result(
                wrapper_res=wrapper_res,
                wrapper_index=wrapper_index,
                total=total,
                separator=" >>> ",
            )
        self.update_progress()

    def yield_handle_result(self, wrapper_res: dict, wrapper_index, total):
        if not wrapper_res:
            msg = "Process error - UNKNOWN ERROR"
            logger.error(msg)
            self.report_error(logging.ERROR, "Process error - UNKNOWN ERROR")
            self._process_errors += 1
        else:
            msg = self.log_result(
                wrapper_res=wrapper_res,
                wrapper_index=wrapper_index,
                total=total,
                separator="<br>",
            )
        yield {
            "step": self._progress_step,
            "total": self._progress_total,
            "message": msg,
        }
        self._progress_step += 1

    def init_progress(
        self,
        total: int,
        desc: str = "",
        yield_mode: bool = False,
    ) -> None:
        if self._report_progress is False:
            pass
        elif yield_mode is True:
            pass
        elif self.progress_callback is None:
            if USE_TQDM:
                self._tqdm = tqdm(total=total, desc=desc)
        else:
            self.progress_callback(step=0, total=total)
        self._progress_total = total
        self._progress_step = 0

    def update_progress(self):
        if self._report_progress is False:
            pass
        elif self.progress_callback is None:
            if USE_TQDM:
                self._tqdm.update(1)
        else:
            self.progress_callback(step=self._progress_step, total=self._progress_total)
            self._progress_step += 1

    def report_error(self, error_level, error_message):
        if self.error_callback is not None:
            self.error_callback(error_level, error_message)

    def log_and_update_progress(
        self, error_level: int, message: str, step: int, total: int
    ):
        if self.progress_and_log_callback is not None:
            self.progress_and_log_callback(
                error_level,
                message,
                step,
                total,
            )

    def close_progress(self):
        if USE_TQDM and self._tqdm is not None:
            self._tqdm.close()

    def check_abort(self):
        if self.abort_callback is None:
            return False
        else:
            return self.abort_callback()

    def grab_files_from_data_base(self, experiment, **kwargs):
        files = self._target_database.query(
            command="SELECT",
            columns="FilePath",
            additional="ORDER BY date_time ASC",
            experiment=experiment,
            **kwargs,
        )
        if files is not None:
            self.accepted_files = [f[0] for f in files]
        else:
            self.accepted_files = []

    def group_by_series(self, time_delta: int):
        # Build dictionary
        self.init_progress(
            total=len(self.accepted_files), desc="Building plants dictionaries"
        )
        plants_ = defaultdict(list)
        for item in self.accepted_files:
            self.update_progress()
            fh = file_handler_factory(item, self._target_database)
            plants_[fh.plant].append(fh)

        # Sort all lists by timestamp
        self.init_progress(total=len(plants_), desc="Sorting observations")
        for v in plants_.values():
            self.update_progress()
            v.sort(key=lambda x: x.date_time)

        # Consume
        files_to_process = []
        self.init_progress(total=len(plants_.values()), desc="Grouping by series")
        for v in plants_.values():
            self.update_progress()
            while len(v) > 0:
                main = v.pop(0)
                main_luid = main.luid
                files_to_process.append((main.file_path, main_luid))
                while (len(v) > 0) and (
                    (v[0].date_time - main.date_time).total_seconds() / 60 < time_delta
                ):
                    files_to_process.append((v.pop(0).file_path, main_luid))

        # Print stats
        stat_lst = [len(i) for i in files_to_process]
        logger.info("-- Series statistics  --")
        logger.info(f"Originale file count: {sum(stat_lst)}")
        logger.info(f"Group count: {len(stat_lst)}")
        for k, v in Counter(stat_lst).items():
            logger.info(f"Qtt: {k}, Mode frequency: {v}")
            logger.info(f"Min: {min(stat_lst)}, Max: {max(stat_lst)}")

        return files_to_process

    def yield_group_by_series(self, time_delta: int):
        # Build dictionary
        self.init_progress(
            total=len(self.accepted_files),
            desc="Building plants dictionaries",
            yield_mode=True,
        )
        plants_ = defaultdict(list)
        total = len(self.accepted_files)
        for i, item in enumerate(self.accepted_files):
            yield {"step": i, "total": total}
            fh = file_handler_factory(item, self._target_database)
            plants_[fh.plant].append(fh)

        self.close_progress()

        # Sort all lists by timestamp
        self.init_progress(
            total=len(plants_),
            desc="Sorting observations",
            yield_mode=True,
        )
        total = len(plants_.values())
        for i, v in enumerate(plants_.values()):
            yield {"step": i, "total": total}
            v.sort(key=lambda x: x.date_time)

        self.close_progress()

        # Consume
        files_to_process = []
        self.init_progress(
            total=len(plants_.values()),
            desc="Grouping by series",
            yield_mode=True,
        )
        total = len(plants_.values())
        for i, v in enumerate(plants_.values()):
            yield {"step": i, "total": total}
            while len(v) > 0:
                main = v.pop(0)
                main_luid = main.luid
                files_to_process.append((main.file_path, main_luid))
                while (len(v) > 0) and (
                    (v[0].date_time - main.date_time).total_seconds() / 60 < time_delta
                ):
                    files_to_process.append((v.pop(0).file_path, main_luid))
        self.close_progress()

        # Print stats
        stat_lst = [len(i) for i in files_to_process]
        logger.info("-- Series statistics  --")
        logger.info(f"Originale file count: {sum(stat_lst)}")
        logger.info(f"Group count: {len(stat_lst)}")
        for k, v in Counter(stat_lst).items():
            logger.info(f"Qtt: {k}, Mode frequency: {v}")
            logger.info(f"Min: {min(stat_lst)}, Max: {max(stat_lst)}")

        self.groups_to_process = files_to_process

    def merge_result_files(self, csv_file_name: str) -> Union[None, pd.DataFrame]:
        logger.info("   --- Starting file merging ---")
        csv_lst = ImageList.match_end(self.options.partials_path, "_result.csv")
        self.init_progress(total=len(csv_lst), desc="Merging CSV files")

        dataframe = pd.DataFrame()
        merge_errors_count = 0
        for csv_file in csv_lst:
            try:
                dataframe = dataframe.append(pd.read_csv(csv_file))
            except Exception as e:
                merge_errors_count += 1
            self.update_progress()
        if merge_errors_count > 0:
            logger.warning(f"{merge_errors_count} merge errors")

        def put_column_in_front(col_name: str, dataframe):
            df_cols = list(dataframe.columns)
            if col_name not in df_cols:
                return dataframe
            df_cols.pop(df_cols.index(col_name))
            return dataframe.reindex(columns=[col_name] + df_cols)

        dataframe = put_column_in_front(col_name="area", dataframe=dataframe)
        dataframe = put_column_in_front(col_name="source_path", dataframe=dataframe)
        dataframe = put_column_in_front(col_name="luid", dataframe=dataframe)
        dataframe = put_column_in_front(col_name="view_option", dataframe=dataframe)
        dataframe = put_column_in_front(col_name="camera", dataframe=dataframe)
        dataframe = put_column_in_front(col_name="date_time", dataframe=dataframe)
        dataframe = put_column_in_front(col_name="condition", dataframe=dataframe)
        dataframe = put_column_in_front(col_name="genotype", dataframe=dataframe)
        dataframe = put_column_in_front(col_name="plant", dataframe=dataframe)
        dataframe = put_column_in_front(col_name="experiment", dataframe=dataframe)

        sort_list = ["plant"] if "plant" in list(dataframe.columns) else []
        sort_list = (
            sort_list + ["date_time"]
            if "date_time" in list(dataframe.columns)
            else sort_list
        )
        if sort_list:
            dataframe = dataframe.sort_values(by=sort_list, axis=0, na_position="first")

        dataframe = dataframe.reset_index(drop=True)

        dataframe.to_csv(
            path_or_buf=os.path.join(self.options.dst_path, csv_file_name), index=False
        )
        self.close_progress()
        logger.info("   --- Merged partial outputs ---<br>")

        return dataframe

    def yield_merge_result_files(self, csv_file_name: str) -> Union[None, pd.DataFrame]:
        logger.info("   --- Starting file merging ---")
        csv_lst = ImageList.match_end(self.options.partials_path, "_result.csv")
        self.init_progress(
            total=len(csv_lst),
            desc="Merging CSV files",
            yield_mode=True,
        )

        dataframe = pd.DataFrame()
        total = len(csv_lst)
        for i, csv_file in enumerate(csv_lst):
            try:
                dataframe = dataframe.append(pd.read_csv(csv_file))
            except pd.errors.EmptyDataError:
                pass
            except Exception as e:
                logger.exception("Merge error")
            yield {"step": i, "total": total}

        def put_column_in_front(col_name: str, dataframe):
            df_cols = list(dataframe.columns)
            if col_name not in df_cols:
                return dataframe
            df_cols.pop(df_cols.index(col_name))
            return dataframe.reindex(columns=[col_name] + df_cols)

        dataframe = put_column_in_front(col_name="area", dataframe=dataframe)
        dataframe = put_column_in_front(col_name="source_path", dataframe=dataframe)
        dataframe = put_column_in_front(col_name="luid", dataframe=dataframe)
        dataframe = put_column_in_front(col_name="view_option", dataframe=dataframe)
        dataframe = put_column_in_front(col_name="camera", dataframe=dataframe)
        dataframe = put_column_in_front(col_name="date_time", dataframe=dataframe)
        dataframe = put_column_in_front(col_name="condition", dataframe=dataframe)
        dataframe = put_column_in_front(col_name="genotype", dataframe=dataframe)
        dataframe = put_column_in_front(col_name="plant", dataframe=dataframe)
        dataframe = put_column_in_front(col_name="experiment", dataframe=dataframe)

        sort_list = ["plant"] if "plant" in list(dataframe.columns) else []
        sort_list = (
            sort_list + ["date_time"]
            if "date_time" in list(dataframe.columns)
            else sort_list
        )
        if sort_list:
            dataframe = dataframe.sort_values(by=sort_list, axis=0, na_position="first")

        dataframe = dataframe.reset_index(drop=True)

        dataframe.to_csv(
            path_or_buf=os.path.join(self.options.dst_path, csv_file_name), index=False
        )
        self.close_progress()
        logger.info("   --- Merged partial outputs ---<br>")

        return dataframe

    def prepare_groups(self, time_delta: int):
        if self.options.group_by_series:
            return self.group_by_series(time_delta, False)
        else:
            return self.accepted_files[:]

    def yield_groups(self, time_delta: int):
        if self.options.group_by_series:
            yield from self.group_by_series(time_delta, True)
        else:
            yield {"step": 1, "total": 1}
        self.groups_to_process = self.accepted_files[:]

    def process_groups(self, groups_list):
        # Build images and data
        if groups_list:
            force_directories(self.options.partials_path)
            logger.info(f"   --- Processing {len(groups_list)} files ---")
            self.init_progress(total=len(groups_list), desc="Processing images")

            max_cores = min([10, mp.cpu_count()])
            if isinstance(self.multi_thread, int):
                num_cores = min(self.multi_thread, max_cores)
            elif isinstance(self.multi_thread, bool):
                if self.multi_thread:
                    num_cores = max_cores
                else:
                    num_cores = 1
            else:
                num_cores = 1
            if (num_cores > 1) and len(groups_list) > 1:
                pool = mp.Pool(num_cores)
                chunky_size_ = num_cores
                for i, res in enumerate(
                    pool.imap_unordered(
                        _pipeline_worker,
                        (
                            (
                                fl,
                                self.options,
                                self.script,
                                None
                                if self._target_database is None
                                else self._target_database.copy(),
                            )
                            for fl in groups_list
                        ),
                        chunky_size_,
                    )
                ):
                    if self.check_abort():
                        logger.info("User stopped process")
                        break
                    self.handle_result(res, i, len(groups_list))
            else:
                for i, fl in enumerate(groups_list):
                    res = _pipeline_worker(
                        [
                            fl,
                            self.options,
                            self.script,
                            None
                            if self._target_database is None
                            else self._target_database.copy(),
                        ]
                    )
                    if self.check_abort():
                        logger.info("User stopped process")
                        break
                    self.handle_result(res, i, len(groups_list))
            self.close_progress()
            logger.info("   --- Files processed ---")

    def yield_test_process_groups(self, groups_list):
        # Build images and data
        if groups_list:
            force_directories(self.options.partials_path)
            logger.info(f"   --- Processing {len(groups_list)} files ---")
            self.init_progress(
                total=len(groups_list),
                desc="Processing images",
                yield_mode=True,
            )

            max_cores = min([10, mp.cpu_count()])
            if isinstance(self.multi_thread, int):
                num_cores = min(self.multi_thread, max_cores)
            elif isinstance(self.multi_thread, bool):
                if self.multi_thread:
                    num_cores = max_cores
                else:
                    num_cores = 1
            else:
                num_cores = 1
            if (num_cores > 1) and len(groups_list) > 1:
                pool = mp.Pool(num_cores)
                chunky_size_ = num_cores
                total = len(groups_list)
                for i, res in enumerate(
                    pool.imap_unordered(
                        _dummy_worker,
                        ((fl) for fl in groups_list),
                        chunky_size_,
                    )
                ):
                    if self.check_abort():
                        logger.info("User stopped process")
                        break
                    yield {"step": i, "total": total}
                    logger.info(f"Test process (multi thread): {res}")
                    sleep(0.1)
            else:
                total = len(groups_list)
                for i, fl in enumerate(groups_list):
                    if self.check_abort():
                        logger.info("User stopped process")
                        break
                    yield {"step": i, "total": total}
                    logger.info(f"Test process (single thread): {fl}")
                    sleep(0.1)

            self.close_progress()
            logger.info("   --- Files processed ---")

    def yield_process_groups(self, groups_list):
        # Build images and data
        if groups_list:
            force_directories(self.options.partials_path)
            logger.info(f"   --- Processing {len(groups_list)} files ---")
            self.init_progress(
                total=len(groups_list),
                desc="Processing images",
                yield_mode=True,
            )

            max_cores = min([10, mp.cpu_count()])
            if isinstance(self.multi_thread, int):
                num_cores = min(self.multi_thread, max_cores)
            elif isinstance(self.multi_thread, bool):
                if self.multi_thread:
                    num_cores = max_cores
                else:
                    num_cores = 1
            else:
                num_cores = 1
            if (num_cores > 1) and len(groups_list) > 1:
                pool = mp.Pool(num_cores)
                chunky_size_ = num_cores
                for i, res in enumerate(
                    pool.imap_unordered(
                        _pipeline_worker,
                        (
                            (
                                fl,
                                self.options,
                                self.script,
                                None
                                if self._target_database is None
                                else self._target_database.copy(),
                            )
                            for fl in groups_list
                        ),
                        chunky_size_,
                    )
                ):
                    if self.check_abort():
                        logger.info("User stopped process")
                        break
                    yield from self.yield_handle_result(
                        res,
                        i,
                        len(groups_list),
                    )
            else:
                for i, fl in enumerate(groups_list):
                    res = _pipeline_worker(
                        [
                            fl,
                            self.options,
                            self.script,
                            None
                            if self._target_database is None
                            else self._target_database.copy(),
                        ]
                    )
                    if self.check_abort():
                        logger.info("User stopped process")
                        break
                    yield from self.yield_handle_result(
                        res,
                        i,
                        len(groups_list),
                    )
            self.close_progress()
            logger.info("   --- Files processed ---")

    @time_method
    def run(self):
        """Processes all files stored in file list"""
        if self.accepted_files:
            # build series
            files_to_process = self.prepare_groups(time_delta=20)

            # Build images and data
            self.process_groups(files_to_process)

            # Build text merged file
            self.merge_result_files("raw_output_data.csv")
        else:
            logger.info("   --- Nothing to do ---")

    @property
    def last_signature(self):
        return self._last_signature

    @last_signature.setter
    def last_signature(self, value):
        self._last_signature = value

    def _get_options(self):
        return self._options

    def _set_options(self, value):
        self._options = value

    def _get_log_times(self):
        return self.options.log_times

    def _set_log_times(self, value):
        self.options.log_times = value

    def _get_masks(self):
        return self.options.masks

    def _set_masks(self, value):
        self.options.masks = value

    def _get_multi_thread(self):
        return self.options.multi_thread

    def _set_multi_thread(self, value):
        self.options.multi_thread = value

    def _get_result_csv_file(self):
        return f"{self.options.dst_path}global_results.csv"

    def _get_success_text_file(self):
        return f"{self.options.dst_path}success.txt"

    options = property(_get_options, _set_options)
    log_times = property(_get_log_times, _set_log_times)
    masks = property(_get_masks, _set_masks)
    multi_thread = property(_get_multi_thread, _set_multi_thread)
    result_csv_file = property(_get_result_csv_file)
    success_text_file = property(_get_success_text_file)
