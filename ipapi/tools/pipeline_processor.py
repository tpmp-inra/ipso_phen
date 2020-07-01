import csv
import datetime
import json
import multiprocessing as mp
import os
from collections import Counter, defaultdict
from collections import namedtuple
from timeit import default_timer as timer

import pandas as pd

from class_pipelines.ip_factory import ipo_factory
from file_handlers.fh_base import file_handler_factory
from base.image_wrapper import ImageWrapper
from tools.comand_line_wrapper import ArgWrapper
from tools.common_functions import time_method, print_progress_bar, force_directories
from tools.error_holder import ErrorHolder
from tools.image_list import ImageList

WorkerResult = namedtuple("WorkerResult", "result, name, error")


def _run_process(file_path, script, options, list_res, data_base):
    res = WorkerResult(False, "None", "")
    ipo = ipo_factory(
        file_path, options, force_abstract=script is not None, data_base=data_base
    )
    if ipo:
        if script is None:
            bool_res = ipo.process_image(threshold_only=options.threshold_only)
            res = WorkerResult(bool_res, str(ipo), ipo.error_holder)
        else:
            script.image_output_path = ipo.dst_path
            bool_res = script.process_image(progress_callback=None, wrapper=ipo)
            res = WorkerResult(bool_res, str(ipo), script.last_error)
        list_res.append(res)

    return dict(wrapper=ipo, res=res)


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
    file_path, _, options, script, db = arg
    list_res = []

    try:
        if isinstance(file_path, list):
            fh = file_handler_factory(file_path[0])
            series_id_ = f'{fh.camera}_{fh.date_time.strftime("%Y%m%d%H%M%S")}_{fh.plant}'
            csv_file_path_ = ""
            csv_header_ = ""
            csv_data_ = []
            is_write_csv_ = False
            for file_name_ in file_path:
                res = _run_process(
                    file_path=file_name_,
                    script=script,
                    options=options,
                    data_base=db,
                    list_res=list_res,
                )
                if res["res"].result:
                    ipo = res["wrapper"]
                    if csv_file_path_ == "":
                        csv_file_path_ = ipo.csv_file_path
                    if options.write_result_text:
                        ipo.csv_data_holder.update_csv_value("series_id", series_id_, True)
                        if csv_header_ == "":
                            csv_header_ = ipo.csv_data_holder.header_to_list()
                        csv_data_.append(ipo.csv_data_holder.data_to_list())
                    is_write_csv_ = True

            if is_write_csv_ and options.write_result_text and csv_header_ and csv_file_path_:
                with open(csv_file_path_, "w", newline="") as csv_file_:
                    wr = csv.writer(csv_file_, quoting=csv.QUOTE_NONE)
                    wr.writerow(csv_header_)
                    for row_ in csv_data_:
                        wr.writerow(row_)
        else:
            res = _run_process(
                file_path=file_path,
                script=script,
                options=options,
                data_base=db,
                list_res=list_res,
            )
            if res["res"].result and options.write_result_text:
                ipo = res["wrapper"]
                with open(ipo.csv_file_path, "w", newline="") as csv_file_:
                    wr = csv.writer(csv_file_, quoting=csv.QUOTE_NONE)
                    wr.writerow(ipo.csv_data_holder.header_to_list())
                    wr.writerow(ipo.csv_data_holder.data_to_list())
    except Exception as e:
        list_res.append(WorkerResult(False, file_path, repr(e)))
    finally:
        return list_res


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
        self.log_callback = None
        self.log_item = None
        self.script = None
        self._last_update = timer()

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

    def handle_result(self, process_result, wrapper_index, total):
        res = False
        if not process_result:
            res = self.log_state(
                status_message="Process error",
                error_holder=ErrorHolder(
                    self, (dict(text="UNKNOWN ERROR", type="unknown_error"),)
                ),
            )
            self._process_errors += 1
        else:
            spaces_ = len(str(total))
            for wrapper_res in process_result:
                if wrapper_res.result is True:
                    res = self.log_state(
                        log_message=f'{(wrapper_index + 1):{spaces_}d}/{total} OK - "{wrapper_res.name}"'
                    )
                else:
                    res = self.log_state(error_holder=wrapper_res.error)
                    self._process_errors += 1
            if self.options.group_by_series:
                res = self.log_state(log_message="____________________________________________")

        if self._process_errors > 0:
            suffix_ = f" {wrapper_index + 1}/{total} Complete, {self._process_errors} errors"
        else:
            suffix_ = f" {wrapper_index + 1}/{total} Complete"
        self.update_progress(
            wrapper_index + 1, total=total, prefix="Processing images:", suffix=suffix_
        )

        return res

    def log_state(
        self,
        status_message: str = "",
        log_message: str = "",
        error_holder: ErrorHolder = None,
        use_status_as_log: bool = False,
    ):
        if self.log_callback is not None:
            return self.log_callback(
                status_message, log_message, error_holder, use_status_as_log
            )
        else:
            return True

    def update_progress(
        self,
        iteration,
        total,
        prefix="",
        suffix="",
        bar_length=50,
        fill="#",
        forced_update=False,
    ):
        if self.progress_callback is None:
            time_now_ = timer()
            if forced_update or (time_now_ - self._last_update > 0.5) or (iteration == total):
                print_progress_bar(
                    iteration=iteration,
                    total=total,
                    prefix=prefix,
                    suffix=suffix,
                    bar_length=bar_length,
                    fill=fill,
                )
                self._last_update = timer()
        else:
            self.progress_callback(step=iteration, total=total)

    def group_by_series(self, time_delta: int):
        json_file = f"./saved_data/{self._last_signature}.json"
        if False and self.last_signature and os.path.isfile(json_file):
            with open(json_file, "r") as f:
                files_to_process = json.load(f)
        else:
            self.update_progress(iteration=0, total=1)
            # Build dictionary
            total = len(self.accepted_files)
            plants_ = defaultdict(list)
            for i, item in enumerate(self.accepted_files):
                self.update_progress(
                    iteration=i,
                    total=total,
                    prefix="Building plants dictionaries:",
                    suffix="Complete",
                )
                fh = file_handler_factory(item)
                plants_[fh.plant].append(fh)
            self.update_progress(
                iteration=total,
                total=total,
                prefix="Building plants dictionaries:",
                suffix="Finished",
                forced_update=True,
            )

            # Sort all lists by timestamp
            total = len(plants_)
            for i, v in enumerate(plants_.values()):
                self.update_progress(
                    iteration=i, total=total, prefix="Sorting observations:", suffix="Complete"
                )
                v.sort(key=lambda x: x.date_time)
            self.update_progress(
                iteration=total,
                total=total,
                prefix="Sorting observations:",
                suffix="Finished",
                forced_update=True,
            )

            # Consume
            files_to_process = []
            for i, v in enumerate(plants_.values()):
                self.update_progress(
                    iteration=i, total=total, prefix="Grouping by series:", suffix="Complete"
                )
                while len(v) > 0:
                    main = v.pop(0)
                    file_list_ = [main.file_path]
                    while (len(v) > 0) and (
                        (v[0].date_time - main.date_time).total_seconds() / 60 < time_delta
                    ):
                        file_list_.append(v.pop(0).file_path)
                    files_to_process.append(file_list_)
            self.update_progress(
                1, total=1, prefix="Grouping by series:", suffix="Finished", forced_update=True
            )

            if self.last_signature:
                with open(json_file, "w") as f:
                    json.dump(files_to_process, f, indent=2)

        # Print stats
        stat_lst = [len(i) for i in files_to_process]
        self.log_state(log_message="-- Series statistics  --")
        self.log_state(log_message=f"Originale file count: {sum(stat_lst)}")
        self.log_state(log_message=f"Group count: {len(stat_lst)}")
        for k, v in Counter(stat_lst).items():
            self.log_state(log_message=f"Qtt: {k}, Mode frequency: {v}")
            self.log_state(log_message=f"Min: {min(stat_lst)}, Max: {max(stat_lst)}")

        if self.log_state(log_message="--"):
            return files_to_process
        else:
            return None

    def remove_already_processed_images(self, files_to_process):
        if not self.log_state(
            status_message="Checking completed files",
            log_message=f"   --- Checking completed files ---",
        ):
            return None
        i = 0
        cpt = 1
        total = len(files_to_process)
        print("")
        results_list_ = []

        self.update_progress(iteration=0, total=1)
        while i < len(files_to_process):
            if isinstance(files_to_process[i], list):
                fl = files_to_process[i][0]
            elif isinstance(files_to_process[i], str):
                fl = files_to_process[i]
            else:
                print(f"Unable to handle {files_to_process[i]}")
                continue
            img_wrapper = ImageWrapper(fl)
            fn = os.path.join(self.options.partials_path, img_wrapper.csv_file_name)
            if os.path.isfile(fn):
                del files_to_process[i]
                results_list_.append(fl)
                if self.log_item is not None:
                    self.log_item(img_wrapper.luid, "success", "", False)
            else:
                if self.log_item is not None:
                    self.log_item(img_wrapper.luid, "refresh", "", False)
                i += 1
            self.update_progress(
                iteration=cpt,
                total=total,
                prefix="Checking completed tasks:",
                suffix="Complete",
            )
            cpt += 1
        # self.update_progress(1, total=1, prefix="Checking completed tasks:", suffix="Finished")
        if len(results_list_) > 0:
            res = self.log_state(
                log_message="Already analyzed files: <ul>"
                + "".join(f"<li>{s}</li>" for s in results_list_)
                + "</ul>"
            )
        else:
            res = self.log_state(
                status_message="Completed files checked",
                log_message=f"   --- Completed files checked ---<br>",
            )
        if res:
            return files_to_process
        else:
            return None

    def merge_result_files(self, csv_file_name: str) -> [None, pd.DataFrame]:
        if self.log_state(
            status_message="Merging partial outputs",
            log_message=f"   --- Starting file merging ---",
        ):
            csv_lst = ImageList.match_end(self.options.partials_path, "_result.csv")
            total = len(csv_lst)
            start_idx = 0
            self.update_progress(iteration=0, total=1)

            df = pd.DataFrame()
            for i, csv_file in enumerate(csv_lst):
                try:
                    df = df.append(pd.read_csv(csv_file))
                except Exception as e:
                    self.log_state(status_message="", log_message=f"")
                    self.log_state(
                        status_message="Merge error",
                        error_holder=ErrorHolder(
                            self,
                            (
                                dict(
                                    text=f'Failed to merge text for : "{csv_file}" because {repr(e)}',
                                    type="merge_error",
                                ),
                            ),
                        ),
                    )
                self.update_progress(
                    iteration=i + start_idx,
                    total=total,
                    prefix="Merging CSV files:",
                    suffix="Complete",
                )

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
            sort_list = (
                sort_list + ["date_time"] if "date_time" in list(df.columns) else sort_list
            )
            if sort_list:
                df.sort_values(by=sort_list, axis=0, inplace=True, na_position="first")

            df.reset_index(drop=True, inplace=True)

            df.to_csv(
                path_or_buf=os.path.join(self.options.dst_path, csv_file_name), index=False
            )
            self.update_progress(
                iteration=total,
                total=total,
                prefix="Merging CSV files:",
                suffix="Finished",
                forced_update=True,
            )
            self.log_state(
                status_message="Merged partial outputs",
                log_message="   --- Merged partial outputs ---<br>",
            )

            return df

    def prepare_groups(self, time_delta: int):
        if self.options.group_by_series:
            return self.group_by_series(time_delta)
        else:
            return self.accepted_files[:]

    def handle_existing_data(self, groups_list):
        if (groups_list is not None) and not self.options.overwrite:
            return self.remove_already_processed_images(groups_list)
        else:
            return groups_list

    def process_groups(self, groups_list, target_database):
        # Build images and data
        is_user_abort = False
        if groups_list:
            force_directories(self.options.partials_path)
            handled_class = "groups" if self.options.group_by_series else "files"
            if not self.log_state(
                status_message="Processing files",
                log_message=f"   --- Processing {len(groups_list)} {handled_class} ---",
            ):
                return
            self.update_progress(0, total=1, prefix="Processing images:")

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
                                False,
                                self.options,
                                self.script,
                                None if target_database is None else target_database.copy(),
                            )
                            for fl in groups_list
                        ),
                        chunky_size_,
                    )
                ):
                    if not self.handle_result(res, i, len(groups_list)):
                        is_user_abort = True
                        break
            else:
                for i, fl in enumerate(groups_list):
                    res = _pipeline_worker(
                        [
                            fl,
                            self.log_times,
                            self.options,
                            self.script,
                            None if target_database is None else target_database.copy(),
                        ]
                    )
                    if not self.handle_result(res, i, len(groups_list)):
                        is_user_abort = True
                        break
            if is_user_abort:
                suffix_ = "User abort"
            elif self._process_errors > 0:
                suffix_ = f"Complete, {self._process_errors} errors"
            else:
                suffix_ = "Complete"
            self.update_progress(
                1, total=1, prefix="Processing images:", suffix=suffix_, forced_update=True
            )
            self.log_state(
                status_message="Files processed", log_message=f"   --- Files processed ---<br>"
            )

    @time_method
    def run(self, target_database=None):
        """Processes all files stored in file list

        Keyword Arguments:
            target_database {DbWrapper} -- Database holding images data (default: {None})
        """
        if self.accepted_files:
            # build series
            files_to_process = self.prepare_groups()

            # If overwrite is disabled remove all files already analysed
            files_to_process = self.handle_existing_data(files_to_process)

            # Build images and data
            self.process_groups(files_to_process, target_database)

            # Build text merged file
            self.merge_result_files("raw_output_data.csv")
        else:
            self.log_state(
                status_message="Nothing to do", log_message=f"   --- Nothing to do ---<br>"
            )
            print("Nothing to do")

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