import os
import json

# from collections import named_tuples


def save_state(
    output_folder: str,
    csv_file_name: str,
    overwrite_existing: bool,
    append_experience_name: str,
    append_time_stamp: bool,
    script,
    generate_series_id: bool,
    series_id_time_delta: int,
    data_frame: dict,
    database_data,
    thread_count: int,
) -> dict:
    return dict(
        output_folder=output_folder,
        csv_file_name=csv_file_name,
        overwrite_existing=overwrite_existing,
        append_experience_name=append_experience_name,
        append_time_stamp=append_time_stamp,
        script=script,
        generate_series_id=generate_series_id,
        series_id_time_delta=series_id_time_delta,
        data_frame=data_frame,
        database_data=database_data,
        thread_count=thread_count,
    )


def restore_state(file_path: str, overrides: dict = {}) -> dict:
    if os.path.isfile(file_path):
        with open(file_path, "r") as f:
            res = json.load(f)
    else:
        res = {}

    def _get_key(key, main_dict, overrides_dict, default=None):
        if key in overrides_dict:
            return overrides_dict[key]
        elif key in main_dict:
            return main_dict[key]
        else:
            return default

    return dict(
        output_folder=_get_key("output_folder", res, overrides),
        csv_file_name=_get_key("csv_file_name", res, overrides),
        overwrite_existing=_get_key("overwrite_existing", res, overrides, False),
        append_experience_name=_get_key("append_experience_name", res, overrides, False),
        append_time_stamp=_get_key("append_time_stamp", res, overrides, False),
        script=_get_key("script", res, overrides),
        generate_series_id=_get_key("generate_series_id", res, overrides, False),
        series_id_time_delta=_get_key("series_id_time_delta", res, overrides, 0),
        data_frame=_get_key("data_frame", res, overrides),
        database_data=_get_key("database_data", res, overrides),
        thread_count=_get_key("thread_count", res, overrides, 1),
    )
