import os
from typing import Optional
import streamlit as st
import datetime

import multiprocessing as mp
import sys

import pandas as pd
import paramiko

import cv2

abspath = os.path.abspath(__file__)
fld_name = os.path.dirname(abspath)
sys.path.insert(0, fld_name)
sys.path.insert(0, os.path.dirname(fld_name))
sys.path.insert(0, os.path.join(os.path.dirname(fld_name), "ipso_phen", ""))

from ipso_phen.ipapi import __init__

# os.chdir(fld_name)

from ipso_phen.ipapi.tools.common_functions import force_directories, make_safe_name

import ipso_phen.ipapi.database.db_initializer as dbi
import ipso_phen.ipapi.database.db_factory as dbf
from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
from ipso_phen.ipapi.base.ipt_functional import chain_ipt, call_ipt

# import ptvsd

# ptvsd.enable_attach(address=("localhost", 8501))
# ptvsd.wait_for_attach()  # Only include this line if you always want to attach the debugger


MAX_CORES = mp.cpu_count()
_DATE_FORMAT = "%Y/%m/%d"


def build_pass_through(wrapper):
    return wrapper.current_image


def build_dla(wrapper):
    return call_ipt(
        ipt_id="IptLinearTransformation",
        source=wrapper,
        return_type="result",
        method="alpha_beta_target",
        target_brightness=200,
    ).current_image


def build_tomato_gen(wrapper):
    return chain_ipt(
        ipt_id="IptLinearTransformation",
        source=chain_ipt(
            ipt_id="IptSimpleWhiteBalance",
            source=wrapper,
            return_type="result",
            min=0,
            max=3,
        ),
        method="alpha_beta_target",
        target_brightness=170,
    ).current_image


def build_atsys(wrapper):
    return chain_ipt(
        ipt_id="IptLinearTransformation",
        source=chain_ipt(
            ipt_id="IptSimpleWhiteBalance",
            source=chain_ipt(
                ipt_id="IptTemperatureTint",
                source=wrapper,
                return_type="result",
                clip_method="rescale",
                temperature_adjustment=-10,
                tint_adjustment=10,
            ),
            return_type="result",
        ),
        return_type="result",
        method="alpha_beta_target",
        target_brightness=65,
    ).current_image


def build_image(wrapper):
    return build_atsys(wrapper=wrapper)


def build_single_plant_video(args):
    plant, dst_folder_, db, dates_, experiment_, view_options_ = args

    p_output = os.path.join(dst_folder_, f"{plant}.mp4")
    if os.path.isfile(p_output):
        return f"Plant {plant} already handled"

    ret = db.query(
        command="SELECT",
        columns="FilePath",
        additional="ORDER BY date_time ASC",
        date=dict(operator="IN", values=dates_),
        experiment=experiment_,
        plant=plant,
        view_option=view_options_[0],
    )
    main_angle_image_list_ = [item[0] for item in ret]

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(p_output, fourcc, 24.0, (video_width, video_height))
    fnt = cv2.FONT_HERSHEY_DUPLEX

    for main_angle_image_ in main_angle_image_list_:
        main_angle_wrapper_side = BaseImageProcessor(
            main_angle_image_,
            db,
        )
        try:
            img_main_angle = build_image(main_angle_wrapper_side)
            if img_main_angle is None:
                continue
            main_angle_wrapper_side.store_image(
                image=img_main_angle, text=view_options_[0], force_store=True
            )
        except Exception as e:
            print(f'Exception "{repr(e)}" while handling {str(main_angle_wrapper_side)}')

        current_date_time = main_angle_wrapper_side.date_time

        for secondary_angle in view_options_[1:]:
            secondary_angle_image_ = db.query_one(
                command="SELECT",
                columns="FilePath",
                additional="ORDER BY date_time ASC",
                experiment=experiment_,
                plant=plant,
                view_option=secondary_angle,
                date_time=dict(
                    operator="BETWEEN",
                    date_min=current_date_time - datetime.timedelta(hours=1),
                    date_max=current_date_time + datetime.timedelta(hours=1),
                ),
            )
            if secondary_angle_image_:
                secondary_angle_image_ = secondary_angle_image_[0]
            if secondary_angle_image_ and os.path.isfile(secondary_angle_image_):
                secondary_angle_wrapper = BaseImageProcessor(secondary_angle_image_)
                try:
                    secondary_angle_img = build_image(secondary_angle_wrapper)
                    main_angle_wrapper_side.store_image(
                        image=secondary_angle_img, text=secondary_angle, force_store=True
                    )
                except Exception as e:
                    print(
                        f'Exception "{repr(e)}" while handling {str(secondary_angle_wrapper)}'
                    )

        mosaic = main_angle_wrapper_side.build_mosaic(
            (video_height, video_width, 3), view_options_
        )
        cv2.putText(
            mosaic,
            current_date_time.strftime("%d/%m/%Y - %H:%M:%S"),
            (10, 1000),
            fnt,
            1,
            (255, 0, 255),
            2,
            cv2.LINE_AA,
        )

        # cv2.imwrite(
        #     os.path.join(os.path.dirname(p_output), main_angle_wrapper_side.luid + ".jpg"), mosaic
        # )

        def write_image_times(out_writer, img_, times=24):
            for _ in range(0, times):
                out_writer.write(img_)

        # Print source image
        write_image_times(out, mosaic)

    # Release everything if job is finished
    out.release()
    cv2.destroyAllWindows()

    return None


def build_sbs_video():
    p_output = os.path.join(dst_folder, f'output_{"_".join(plants)}_.mp4')
    if os.path.isfile(p_output):
        return f"Plants {'_'.join(plants)} already handled"

    ret = current_database.query(
        command="SELECT",
        columns="FilePath",
        additional="ORDER BY date_time ASC",
        date=dict(operator="IN", values=dates),
        experiment=experiment,
        plant=plants[0],
        view_option=view_option,
    )
    file_list_ = [item[0] for item in ret]

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(p_output, fourcc, 24.0, (video_width, video_height))
    fnt = cv2.FONT_HERSHEY_DUPLEX

    total = len(file_list_)
    current_progress = st.progress(0)
    time_counter = 1
    for i, source_vis_plant in enumerate(file_list_):
        if not (source_vis_plant and os.path.isfile(source_vis_plant)):
            continue
        # Handle first image
        main_wrapper = BaseImageProcessor(source_vis_plant)
        try:
            img_main = build_image(main_wrapper)
            main_wrapper.store_image(image=img_main, text=plants[0], force_store=True)
        except Exception as e:
            print(f'Exception "{repr(e)}" while handling {str(source_vis_plant)}')

        current_date_time = main_wrapper.date_time

        # Handle the rest
        has_missing_ = False
        for counter, ancillary_plant in enumerate(plants[1:]):
            file_name_ = current_database.query_one(
                command="SELECT",
                columns="FilePath",
                additional="ORDER BY date_time ASC",
                experiment=experiment,
                plant=ancillary_plant,
                view_option=view_option,
                date_time=dict(
                    operator="BETWEEN",
                    date_min=current_date_time - datetime.timedelta(hours=10),
                    date_max=current_date_time + datetime.timedelta(hours=10),
                ),
            )
            if file_name_:
                file_name_ = file_name_[0]
            if file_name_ and os.path.isfile(file_name_):
                try:
                    main_wrapper.store_image(
                        image=build_image(BaseImageProcessor(file_name_)),
                        text=plants[counter + 1],
                        force_store=True,
                    )
                except Exception as e:
                    print(f'Exception "{repr(e)}" while handling {str(file_name_)}')
            else:
                has_missing_ = True

        mosaic = main_wrapper.build_mosaic((video_height, video_width, 3), plants)

        # cv2.imwrite(
        #     os.path.join(os.path.dirname(p_output), f"{main_wrapper.plant}_{time_counter}.jpg"),
        #     mosaic,
        # )
        time_counter += 1

        def write_image_times(out_writer, img_, times=12):
            for _ in range(0, times):
                out_writer.write(img_)

        # Print source image
        write_image_times(out, mosaic)

        current_progress.progress((i + 1) / total)

    # Release everything if job is finished
    out.release()
    cv2.destroyAllWindows()


def query_current_database(
    command: str,
    table: str = "snapshots",
    columns: str = "*",
    additional: str = "",
    **kwargs,
):
    return current_database.query(
        command=command, table=table, columns=columns, additional=additional, **kwargs
    )


def get_query_items(column: str, **kwargs):
    items = query_current_database(
        command="SELECT DISTINCT",
        columns=column,
        additional=f"ORDER BY {column} ASC",
        **kwargs,
    )
    return [item[0] for item in items]


def progress_update(step, total, process_events: bool = False):
    current_progress.progress(step / total)


st.title("Video tools")

st.subheader("Initialize")

num_cores = st.slider("Thread count", 1, MAX_CORES, 1)
video_resolution = st.selectbox("Video resolution", ["1080p", "720p", "576p", "480p"])
video_aspect_ratio = st.selectbox("Video aspect ratio", ["16/9", "4/3", "1/1"])

video_height = int(video_resolution[0:-1])
video_width = int(video_height * eval(video_aspect_ratio))

databases_group = st.selectbox(
    label="Database group",
    options=[k for k in dbi.available_db_dicts],
    format_func=lambda x: x.value,
)
experiment_dbi = st.selectbox(
    label="Experiment",
    options=[db for db in dbi.available_db_dicts[databases_group]],
    format_func=lambda x: x.db_qualified_name,
)

job_choice = st.selectbox(
    "Select what kind of video to make",
    ["Please make your choice...", "Single plant", "Side by side comparison"],
)


if job_choice != "Please make your choice...":
    st.subheader("Connect to database")
    current_progress = st.progress(0)
    current_database = dbf.db_info_to_database(
        experiment_dbi,
        progress_call_back=progress_update,
    )
    current_progress.progress(1 / 1)
    st.write("Database OK")

    st.subheader("Filter")
    exp_list = get_query_items(column="Experiment")
    experiment = st.selectbox("Experiment", exp_list)
    dst_folder = st.text_input(
        "Destination folder: ",
        os.path.join(
            os.path.expanduser("~"),
            "Videos",
            "TPMP",
            experiment,
            "single_plant" if job_choice == "Single plant" else "sbs",
            "",
        ),
    )
    plant_lst = get_query_items(column="Plant", experiment=experiment)
    view_option_lst = get_query_items(column="view_option", experiment=experiment)
    date_list = [
        item.replace("-", "/") if isinstance(item, str) else item.strftime(_DATE_FORMAT)
        for item in get_query_items(column="Date", experiment=experiment)
    ]
    plants = st.multiselect(
        "Plants", plant_lst, plant_lst if job_choice == "Single plant" else []
    )
    dates = st.multiselect("Dates", date_list, date_list)
    num_cores = min([MAX_CORES, num_cores])
    if job_choice == "Single plant":
        view_options = st.multiselect("View options", view_option_lst, view_option_lst)
        if st.button("Build videos"):
            force_directories(dst_folder)
            st.write(f"Building {len(plants)} videos using {num_cores} cores")
            current_progress = st.progress(0)
            total_ = len(plants)
            if num_cores > 1:
                pool = mp.Pool(num_cores)
                chunky_size_ = 1
                for i, _ in enumerate(
                    pool.imap_unordered(
                        build_single_plant_video,
                        (
                            (
                                plant_,
                                dst_folder,
                                current_database.copy(),
                                dates,
                                experiment,
                                view_options,
                            )
                            for plant_ in plants
                        ),
                        chunky_size_,
                    )
                ):
                    current_progress.progress((i + 1) / total_)
            else:
                for i, plant in enumerate(plants):
                    build_single_plant_video(
                        (
                            plant,
                            dst_folder,
                            current_database.copy(),
                            dates,
                            experiment,
                            view_options,
                        )
                    )
                    current_progress.progress((i + 1) / total_)

            current_progress.progress(1 / 1)
            st.subheader("Done")
            st.balloons()

    elif job_choice == "Side by side comparison":
        view_option = st.selectbox("View option", view_option_lst)
        if st.button("Build video"):
            force_directories(dst_folder)
            st.write(
                f"Building sbs video for  {','.join(plants)} using {num_cores} cores"
            )

            build_sbs_video()

            current_progress.progress(1 / 1)
            st.subheader("Done")
            st.balloons()
