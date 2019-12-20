import sys
import os
import argparse
import json
from timeit import default_timer as timer

import pandas as pd

import tools.db_wrapper as dbw
from tools.common_functions import print_progress_bar, force_directories, format_time
from tools.pipeline_processor import PipelineProcessor
from ip_base.ipt_script_generator import IptScriptGenerator, decode_ipt


g_log_file = ""

IS_LOG_DATA = True
IS_USE_MULTI_THREAD = True


def log_event(event: [list, str], print_to_console: bool = False):
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


def do_pp_progress(step: int, total: int):
    print_progress_bar(iteration=step, total=total)


def do_feed_back(status_msg: str, log_msg: str, obj: object, use_status_as_log: bool) -> bool:
    if obj is None:
        log_event(event=log_msg)
    else:
        log_event(event=obj)
    return True


def main():
    start = timer()

    parser = argparse.ArgumentParser(description="Process a pipeline on images with stored state")
    parser.add_argument("-s", "--stored_state", required=True, help="Path to the stored state")
    parser.add_argument(
        "-p",
        "--process_count",
        required=False,
        help="Override number of concurrent processes",
        default=None,
    )

    args = vars(parser.parse_args())

    src = args["stored_state"]

    # src = "..\\..\\..\\ipso_phen_data\\pipeline_state\\18as_stress_1908.json"

    with open(src, "r") as f:
        res = json.load(f, object_hook=decode_ipt)

    # Build database
    db = dbw.db_info_to_database(dbw.DbInfo(*res["database_data"]))

    # Build dataframe
    df = pd.DataFrame.from_dict(res["data_frame"])

    # Retrieve output folder
    if res["append_experience_name"]:
        output_folder_ = os.path.join(res["output_folder"], res["append_experience_name"], "")
    else:
        output_folder_ = os.path.join(res["output_folder"], "")
    global g_log_file
    g_log_file = os.path.join(output_folder_, "log.txt")
    force_directories(output_folder_)
    csv_file_name = res["csv_file_name"]
    mpc = int(args.get("process_count", res["thread_count"])) if IS_USE_MULTI_THREAD else False

    log_event(
        event=[
            "Process summary",
            "_______________",
            f'database: {res["database_data"]}',
            f'Output folder: {res["output_folder"]}',
            f'CSV file name: {res["csv_file_name"]}',
            f'Overwrite data: {res["overwrite_existing"]}',
            f'Append experience name to root folder: {res["append_experience_name"]}',
            f'Append timestamp to root folder: {res["append_time_stamp"]}',
            f'Generate series ID: {res["generate_series_id"]}',
            f'Series ID time delta allowed: {res["series_id_time_delta"]}',
            f"Dataframe rows: {df.shape[1]}",
            f"Concurrent processes count: {mpc}",
            f'Script summary: {str(res["script"])}',
            "_______________",
            "",
        ],
        print_to_console=False,
    )

    # Retrieve images
    image_list_ = list(df["FilePath"])

    # Build pipeline processor
    pp = PipelineProcessor(
        dst_path=output_folder_,
        overwrite=res["overwrite_existing"],
        seed_output=res["append_time_stamp"],
        group_by_series=res["generate_series_id"],
        store_images=False,
    )
    pp.ensure_root_output_folder()
    # pp.progress_callback = do_pp_progress
    pp.log_callback = do_feed_back
    pp.accepted_files = image_list_
    pp.script = res["script"]

    # Process data
    if pp.accepted_files:
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
        step_ = 0
        step_ += 1
        do_pp_progress(step_, steps_)
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
                step_ += 1
                do_pp_progress(step_, steps_)
            if build_mean_df:
                df.groupby("series_id").mean().drop(["series_id"]).drop_duplicates().sort_values(
                    by=["plant", "date_time"]
                ).to_csv(os.path.join(pp.options.dst_path, f"{csv_sid_root_name}_mean.csv"))
                step_ += 1
                do_pp_progress(step_, steps_)
        if group_by_hour:
            csv_hour_root_name = csv_file_name + "_hour"
            if build_median_df:
                pass
                step_ += 1
                do_pp_progress(step_, steps_)
            if build_mean_df:
                pass
                step_ += 1
                do_pp_progress(step_, steps_)
        if group_by_day:
            csv_day_root_name = csv_file_name + "_day"
            if build_median_df:
                df.groupby("date").median().drop_duplicates().sort_values(
                    by=["plant", "date"]
                ).to_csv(os.path.join(pp.options.dst_path, f"{csv_day_root_name}_median.csv"))
                step_ += 1
                do_pp_progress(step_, steps_)
            if build_mean_df:
                df.groupby("date").mean().drop_duplicates().sort_values(
                    by=["plant", "date"]
                ).to_csv(os.path.join(pp.options.dst_path, f"{csv_day_root_name}_mean.csv"))
                step_ += 1
                do_pp_progress(step_, steps_)
        log_event(" --- Built additional CSV files ---", print_to_console=True)

    log_event(
        event=f"Processed {groups_to_process_count} groups/images in {format_time(timer() - start)}",
        print_to_console=True,
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
