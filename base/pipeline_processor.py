import csv
import multiprocessing as mp
import os
from collections import Counter, defaultdict
from collections import namedtuple
import logging
from typing import Union

import pandas as pd
from tqdm import tqdm

from ipapi.class_pipelines.ip_factory import ipo_factory
from ipapi.file_handlers.fh_base import file_handler_factory
from ipapi.tools.comand_line_wrapper import ArgWrapper
from ipapi.tools.common_functions import time_method, force_directories
from ipapi.tools.image_list import ImageList

logger = logging.getLogger(__name__)

WorkerResult = namedtuple("WorkerResult", "result, name, message")


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

    try:
        bool_res = script.execute(
            src_image=file_path if isinstance(file_path, str) else file_path[0],
            silent_mode=True,
            target_module="",
            additional_data={"luid": file_path[1]} if isinstance(file_path, tuple) else {},
            write_data=True,
            target_data_base=db,
            overwrite_data=options.overwrite,
            store_images=False,
            options=options,
            call_back=None,
        )
    except Exception as e:
        return WorkerResult(False, file_path, repr(e))
    else:
        if script.wrapper is not None:
            return WorkerResult(bool_res, str(script.wrapper), "")
        else:
            return WorkerResult(bool_res, "Unknown", "")


class PipelineProcessor:
    """ Process image processing pipelines according to options

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

    def __init__(self, **kwargs):
        """ Initializes command line wrapper an properties """
        self.options = ArgWrapper(**kwargs)
        self._process_errors = 0
        self.accepted_files = []
        self._last_signature = ""
        self.progress_callback = None
        self.error_callback = None
        self.log_item = None
        self.script = None
        self._tqdm = None
        self._progress_total = 0
        self._progress_step = 0

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
            self.accepted_files = img_lst.filter(masks=self.masks, flat_list_out=flatten_list)
        else:
            self.accepted_files = []

        return len(self.accepted_files) > 0

    def ensure_root_output_folder(self):
        """Creates output folder if does not exist
        """

        if not os.path.exists(self.options.dst_path):
            os.makedirs(self.options.dst_path)

    def handle_result(self, wrapper_res, wrapper_index, total):
        if not wrapper_res:
            logger.error("Process error - UNKNOWN ERROR")
            self.report_error(logging.ERROR, "Process error - UNKNOWN ERROR")
            self._process_errors += 1
        else:
            spaces_ = len(str(total))
            msg_prefix = (
                f">>>> "
                + f'{"OK" if wrapper_res.result is True else "FAIL"}'
                + " - "
                + f"{(wrapper_index + 1):{spaces_}d}/{total} >>> "
            )
            msg_suffix = f" - {wrapper_res.message}" if wrapper_res.message else ""
            logger.info(f"{msg_prefix}{wrapper_res.name}{msg_suffix}")
            if wrapper_res.result is not True:
                self.report_error(logging.ERROR, f"{msg_prefix}{wrapper_res.name}{msg_suffix}")
            if wrapper_res.result is not True:
                self._process_errors += 1
        self.update_progress()

    def init_progress(self, total: int, desc: str = "") -> None:
        if self.progress_callback is None:
            self._tqdm = tqdm(total=total, desc=desc)
        else:
            self.progress_callback(step=0, total=total)
        self._progress_total = total
        self._progress_step = 0

    def update_progress(self):
        if self.progress_callback is None:
            self._tqdm.update(1)
        else:
            self.progress_callback(step=self._progress_step, total=self._progress_total)
            self._progress_step += 1

    def report_error(self, error_level, error_message):
        if self.error_callback is not None:
            self.error_callback(error_level, error_message)

    def close_progress(self):
        if self._tqdm is not None:
            self._tqdm.close()

    def group_by_series(self, time_delta: int):
        # Build dictionary
        self.init_progress(total=len(self.accepted_files), desc="Building plants dictionaries")
        plants_ = defaultdict(list)
        for item in self.accepted_files:
            self.update_progress()
            fh = file_handler_factory(item)
            plants_[fh.plant].append(fh)
        self.close_progress()

        # Sort all lists by timestamp
        self.init_progress(total=len(plants_), desc="Sorting observations")
        for v in plants_.values():
            self.update_progress()
            v.sort(key=lambda x: x.date_time)
        self.close_progress()

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
        self.close_progress()

        # Print stats
        stat_lst = [len(i) for i in files_to_process]
        logger.info("-- Series statistics  --")
        logger.info(f"Originale file count: {sum(stat_lst)}")
        logger.info(f"Group count: {len(stat_lst)}")
        for k, v in Counter(stat_lst).items():
            logger.info(f"Qtt: {k}, Mode frequency: {v}")
            logger.info(f"Min: {min(stat_lst)}, Max: {max(stat_lst)}")

        return files_to_process

    def merge_result_files(self, csv_file_name: str) -> Union[None, pd.DataFrame]:
        logger.info("   --- Starting file merging ---")
        csv_lst = ImageList.match_end(self.options.partials_path, "_result.csv")
        self.init_progress(total=len(csv_lst), desc="Merging CSV files")

        df = pd.DataFrame()
        for csv_file in csv_lst:
            try:
                df = df.append(pd.read_csv(csv_file))
            except Exception as e:
                logger.exception("Merge error")
            self.update_progress()

        def put_column_in_front(col_name: str, dataframe):
            df_cols = list(dataframe.columns)
            if col_name not in df_cols:
                return dataframe
            df_cols.pop(df_cols.index(col_name))
            return dataframe.reindex(columns=[col_name] + df_cols)

        df = put_column_in_front(col_name="area", dataframe=df)
        df = put_column_in_front(col_name="source_path", dataframe=df)
        df = put_column_in_front(col_name="luid", dataframe=df)
        df = put_column_in_front(col_name="view_option", dataframe=df)
        df = put_column_in_front(col_name="camera", dataframe=df)
        df = put_column_in_front(col_name="date_time", dataframe=df)
        df = put_column_in_front(col_name="condition", dataframe=df)
        df = put_column_in_front(col_name="genotype", dataframe=df)
        df = put_column_in_front(col_name="plant", dataframe=df)
        df = put_column_in_front(col_name="experiment", dataframe=df)

        sort_list = ["plant"] if "plant" in list(df.columns) else []
        sort_list = sort_list + ["date_time"] if "date_time" in list(df.columns) else sort_list
        if sort_list:
            df.sort_values(by=sort_list, axis=0, inplace=True, na_position="first")

        df.reset_index(drop=True, inplace=True)

        df.to_csv(path_or_buf=os.path.join(self.options.dst_path, csv_file_name), index=False)
        self.close_progress()
        logger.info("   --- Merged partial outputs ---<br>")

        return df

    def prepare_groups(self, time_delta: int):
        if self.options.group_by_series:
            return self.group_by_series(time_delta)
        else:
            return self.accepted_files[:]

    def process_groups(self, groups_list, target_database):
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
                                None if target_database is None else target_database.copy(),
                            )
                            for fl in groups_list
                        ),
                        chunky_size_,
                    )
                ):
                    self.handle_result(res, i, len(groups_list))
            else:
                for i, fl in enumerate(groups_list):
                    res = _pipeline_worker(
                        [
                            fl,
                            self.options,
                            self.script,
                            None if target_database is None else target_database.copy(),
                        ]
                    )
                    self.handle_result(res, i, len(groups_list))
            self.close_progress()
            logger.info("   --- Files processed ---")

    @time_method
    def run(self, target_database=None):
        """Processes all files stored in file list

        Keyword Arguments:
            target_database {DbWrapper} -- Database holding images data (default: {None})
        """
        if self.accepted_files:
            # build series
            files_to_process = self.prepare_groups(time_delta=20)

            # Build images and data
            self.process_groups(files_to_process, target_database)

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
