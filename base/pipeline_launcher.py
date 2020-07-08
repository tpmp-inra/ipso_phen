import os
import json
from typing import Union


from timeit import default_timer as timer
from typing import Union
import pandas as pd
from tqdm import tqdm

import ipapi.tools.db_wrapper as dbw
from ipapi.tools.common_functions import force_directories, format_time
from ipapi.base.pipeline_processor import PipelineProcessor
from ipapi.base.ipt_strict_pipeline import IptStrictPipeline


g_log_file = ""

IS_LOG_DATA = True
IS_USE_MULTI_THREAD = False


def save_state(
    output_folder: str,
    csv_file_name: str,
    overwrite_existing: bool,
    sub_folder_name: str,
    append_time_stamp: bool,
    script,
    generate_series_id: bool,
    series_id_time_delta: int,
    images: list,
    database_data=None,
    thread_count: int = 1,
) -> dict:
    return dict(
        output_folder=output_folder,
        csv_file_name=csv_file_name,
        overwrite_existing=overwrite_existing,
        sub_folder_name=sub_folder_name,
        append_time_stamp=append_time_stamp,
        script=script,
        generate_series_id=generate_series_id,
        series_id_time_delta=series_id_time_delta,
        images=images,
        thread_count=thread_count,
        database_data=database_data,
    )


def restore_state(blob: Union[str, dict, None], overrides: dict = {}) -> dict:
    # Attempt to load state
    if isinstance(blob, str) and os.path.isfile(blob):
        with open(blob, "r") as f:
            res = json.load(f)
    elif isinstance(blob, dict):
        res = blob
    else:
        res = {}

    # Handle legacy states
    df = res.pop("data_frame", None)
    if df is not None:
        res["images"] = list(df["FilePath"])
    sf = res.pop("append_experience_name", None)
    if sf is not None:
        res["sub_folder_name"] = sf

    def _get_key(key, main_dict, overrides_dict, default=None):
        if overrides_dict.get(key, None) is not None:
            return overrides_dict[key]
        elif key in main_dict:
            return main_dict[key]
        else:
            return default

    # Build state dictionnary with overrides
    return dict(
        output_folder=_get_key("output_folder", res, overrides),
        csv_file_name=_get_key("csv_file_name", res, overrides),
        overwrite_existing=_get_key("overwrite_existing", res, overrides, False),
        sub_folder_name=_get_key("sub_folder_name", res, overrides, ""),
        append_time_stamp=_get_key("append_time_stamp", res, overrides, False),
        script=_get_key("script", res, overrides),
        generate_series_id=_get_key("generate_series_id", res, overrides, False),
        series_id_time_delta=_get_key("series_id_time_delta", res, overrides, 0),
        data_frame=_get_key("data_frame", res, overrides),
        database_data=_get_key("database_data", res, overrides),
        thread_count=_get_key("thread_count", res, overrides, 1),
    )


def log_event(event: Union[list, str], print_to_console: bool = False):
    global IS_LOG_DATA
    if IS_LOG_DATA is True:
        with open(g_log_file, "a+") as lf:
            if isinstance(event, str):
                lf.write("event\n")
            elif isinstance(event, object):
                lf.write(f"{str(event)}\n")
            else:
                lf.write("\n".join(event))
    if print_to_console:
        print(event)


def do_feed_back(status_msg: str, log_msg: str, obj: object, use_status_as_log: bool) -> bool:
    if obj is None:
        log_event(event=log_msg)
    else:
        log_event(event=obj)
    return True


def launch(**kwargs):
    start = timer()

    # Script
    script = kwargs.get("script", None)
    if script is not None and os.path.isfile(script):
        with open(script, "r") as f:
            script = json.load(f)
    kwargs["script"] = script

    # Image(s)
    image = kwargs.get("image", None)
    images = kwargs.get("images", None)
    if image is not None and images is not None:
        kwargs["images"] = images + [image]
    elif image is None and images is not None:
        kwargs["images"] = images
    elif image is not None and images is None:
        kwargs["images"] = [image]

    # State
    stored_state = kwargs.pop("stored_state", None)

    res = restore_state(blob=stored_state, overrides=kwargs)

    # Retrieve images
    image_list_ = res.get("images", None)
    if image_list_ is None or not isinstance(image_list_, list) or len(image_list_) < 1:
        print("No images to precess")
        return 1

    # Build database
    db_data = res.get("database_data", None)
    db = dbw.db_info_to_database(dbw.DbInfo(**db_data)) if db_data is not None else None

    # Retrieve output folder
    output_folder_ = res.get("output_folder", None)
    if not output_folder_:
        print("Missing output folder")
        return 1
    elif res.get("sub_folder_name", ""):
        output_folder_ = os.path.join(output_folder_, res["sub_folder_name"], "")
    else:
        output_folder_ = os.path.join(output_folder_, "")
    global g_log_file
    g_log_file = os.path.join(output_folder_, "log.txt")
    force_directories(output_folder_)
    csv_file_name = res.get("csv_file_name", None)
    if not csv_file_name:
        print("Missing output file name")
        return 1
    if IS_USE_MULTI_THREAD and "thread_count" in res:
        try:
            mpc = int(res["thread_count"])
        except:
            mpc = False
    else:
        mpc = False

    try:
        script = IptStrictPipeline.from_json(json_data=res["script"])
    except Exception as e:
        print("Failed to load script: {repr(e)}")
        return 1

    log_event(
        event=[
            "Process summary",
            "_______________",
            f'database: {res.get("database_data", None)}',
            f'Output folder: {res["output_folder"]}',
            f'CSV file name: {res["csv_file_name"]}',
            f'Overwrite data: {res["overwrite_existing"]}',
            f'Subfolder name: {res["sub_folder_name"]}',
            f'Append timestamp to root folder: {res["append_time_stamp"]}',
            f'Generate series ID: {res["generate_series_id"]}',
            f'Series ID time delta allowed: {res["series_id_time_delta"]}',
            f"Dataframe rows: {len(image_list_)}",
            f"Concurrent processes count: {mpc}",
            f"Script summary: {str(script)}",
            "_______________",
            "",
        ],
        print_to_console=False,
    )

    # Build pipeline processor
    pp = PipelineProcessor(
        dst_path=output_folder_,
        overwrite=res["overwrite_existing"],
        seed_output=res["append_time_stamp"],
        group_by_series=res["generate_series_id"],
        store_images=False,
    )
    pp.ensure_root_output_folder()
    pp.log_callback = do_feed_back
    pp.accepted_files = image_list_
    pp.script = script
    if not pp.accepted_files:
        print("Nothing to precess")
        return 1

    # Process data
    groups_to_process = pp.prepare_groups(res["series_id_time_delta"])
    groups_to_process = pp.handle_existing_data(groups_to_process)
    groups_to_process_count = len(groups_to_process)
    if groups_to_process_count > 0:
        log_event(
            f"Starting {groups_to_process_count} groups processing", print_to_console=True
        )
        pp.multi_thread = mpc
        pp.process_groups(groups_list=groups_to_process, target_database=db)

    # Merge dataframe
    df = pp.merge_result_files(csv_file_name=csv_file_name + ".csv")

    group_by_series_id = False
    group_by_hour = False
    group_by_day = False
    build_median_df = False
    build_mean_df = False

    steps_ = 0
    if group_by_series_id:
        if build_median_df:
            steps_ += 1
        if build_mean_df:
            steps_ += 1
    if group_by_hour:
        if build_median_df:
            steps_ += 1
        if build_mean_df:
            steps_ += 1
    if group_by_day:
        if build_median_df:
            steps_ += 1
        if build_mean_df:
            steps_ += 1
    if steps_ > 0:
        log_event(" --- Building additional CSV files ---", print_to_console=True)
        pb = tqdm(total=steps_, desc="Building additional CSV files:")
        if "_raw_data" in csv_file_name:
            csv_file_name = csv_file_name.replace("_raw_data", "")
        if csv_file_name.endswith(".csv"):
            csv_file_name = csv_file_name.replace(".csv", "")
        df = df.drop("view_option", axis=1)
        if group_by_series_id:
            csv_sid_root_name = csv_file_name + "_sid"
            if build_median_df:
                df.groupby("series_id").median().merge(df).drop(
                    ["series_id"], axis=1
                ).drop_duplicates().sort_values(by=["plant", "date_time"]).to_csv(
                    os.path.join(pp.options.dst_path, f"{csv_sid_root_name}_median.csv")
                )
                pb.update(1)
            if build_mean_df:
                df.groupby("series_id").mean().drop(
                    ["series_id"]
                ).drop_duplicates().sort_values(by=["plant", "date_time"]).to_csv(
                    os.path.join(pp.options.dst_path, f"{csv_sid_root_name}_mean.csv")
                )
                pb.update(1)
        if group_by_hour:
            csv_hour_root_name = csv_file_name + "_hour"
            if build_median_df:
                pass
                pb.update(1)
            if build_mean_df:
                pass
                pb.update(1)
        if group_by_day:
            csv_day_root_name = csv_file_name + "_day"
            if build_median_df:
                df.groupby("date").median().drop_duplicates().sort_values(
                    by=["plant", "date"]
                ).to_csv(os.path.join(pp.options.dst_path, f"{csv_day_root_name}_median.csv"))
                pb.update(1)
            if build_mean_df:
                df.groupby("date").mean().drop_duplicates().sort_values(
                    by=["plant", "date"]
                ).to_csv(os.path.join(pp.options.dst_path, f"{csv_day_root_name}_mean.csv"))
                pb.update(1)
        pb.close()
        log_event(" --- Built additional CSV files ---", print_to_console=True)

    log_event(
        event=f"Processed {groups_to_process_count} groups/images in {format_time(timer() - start)}",
        print_to_console=True,
    )

    return 0
