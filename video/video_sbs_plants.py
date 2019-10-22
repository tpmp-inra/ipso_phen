import datetime
import os
import sys

import cv2
import numpy as np

abspath = os.path.abspath(__file__)
fld_name = os.path.dirname(abspath)
sys.path.insert(0, fld_name)
sys.path.insert(0, os.path.dirname(fld_name))
sys.path.insert(0, os.path.join(os.path.dirname(fld_name), "ipso_phen", ""))

import tools.db_wrapper as dbw
from ip_base.ip_abstract import AbstractImageProcessor
from ip_base.ipt_functional import call_ipt
from ip_base.ipt_script_generator import IptScriptGenerator
from ip_base import ip_common as ipc
from tools.common_functions import print_progress_bar


_EXPERIMENT = "13as_19tp01_1904".lower()
# PLANTS = ["13a0007_su_ww_xx", "13a0024_su_wd_xx"]
PLANTS = ["13a0014_w3_wd_xx", "13a0022_w3_wd_xx"]
# PLANTS = ["13a0019_hr_ww_xx", "13a0020_hr_wd_xx"]
PLANTS_STORED_NAME = [f"{p}_output" for p in PLANTS]
MOSAIC_HEIGHT = 1
MOSAIC_WIDTH = 2

VIEW_OPTION = "side90"
CAMERA = "vis"
MOSAIC_DATA = np.array(PLANTS_STORED_NAME)
MOSAIC_DATA = np.reshape(MOSAIC_DATA, (MOSAIC_HEIGHT, MOSAIC_WIDTH))

SCRIPT_PATH = "C:/Users/fmavianemac/Documents/tpmp_pipelines/13as_19tp01_1904_v2.tipp"

DST_PATH = f"C:\\Users\\fmavianemac\\Videos\\TPMP_output\\{_EXPERIMENT}_side\\"

BACKGROUND_COLOR, FONT_COLOR = (0, 0, 0), (255, 255, 255)


def build_image(
    image_path: str,
    main_wrapper: AbstractImageProcessor = None,
    index: tuple = (0,),
    script: IptScriptGenerator = None,
):
    wrapper = AbstractImageProcessor(image_path)
    ret = script.process_image(wrapper=wrapper)
    if main_wrapper is not None:
        w = main_wrapper
    else:
        w = wrapper
    if ret:
        w.store_image(
            image=wrapper.draw_image(
                src_image=wrapper.retrieve_stored_image("exposure_fixed"),
                src_mask=wrapper.mask,
                background="bw",
                foreground="source",
                bck_grd_luma=120,
            ),
            text=PLANTS_STORED_NAME[index[0]],
            force_store=True,
            text_overlay=f"{wrapper.plant} - {wrapper.date_time.strftime('%d/%b/%Y')}",
            font_color=ipc.C_WHITE,
            position="TOP",
        )
    else:
        w.store_image(image=wrapper.current_image, text=PLANTS_STORED_NAME[index[0]])
    return w


def main():
    vid_width, vid_height = 1920, 1080

    db_ = dbw.get_pg_dbw(dbw.DB_INFO_EXT_HD)

    if not os.path.exists(DST_PATH):
        os.makedirs(DST_PATH)

    ret = db_.query(
        command="SELECT",
        columns="FilePath",
        additional="ORDER BY date_time ASC",
        experiment=_EXPERIMENT,
        plant=PLANTS[0],
        camera=CAMERA,
        view_option=VIEW_OPTION,
    )
    file_list_ = [item[0] for item in ret]

    output = os.path.join(DST_PATH, f'output_{"_".join(PLANTS)}_84_cnt_bw.mp4')
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output, fourcc, 24.0, (vid_width, vid_height))

    fnt = cv2.FONT_HERSHEY_DUPLEX

    script_ = IptScriptGenerator.load(SCRIPT_PATH)
    script_.threshold_only = True
    script_.build_mosaic = False
    script_.display_images = False

    time_counter = 1
    total = len(file_list_)
    print_progress_bar(0, total=total, prefix="Building video:", suffix=f" {0}/{total} Complete")
    for i, source_vis_plant in enumerate(file_list_):
        if not (source_vis_plant and os.path.isfile(source_vis_plant)):
            continue
        # Handle first image
        main_wrapper = build_image(
            image_path=source_vis_plant, main_wrapper=None, index=(0,), script=script_.copy()
        )
        current_date_time = main_wrapper.date_time

        # Handle the rest
        has_missing_ = False
        for counter, ancillary_plant in enumerate(PLANTS[1:]):
            file_name_ = db_.query_one(
                command="SELECT",
                columns="FilePath",
                additional="ORDER BY date_time ASC",
                experiment=_EXPERIMENT,
                plant=ancillary_plant,
                camera=CAMERA,
                view_option=VIEW_OPTION,
                date_time=dict(
                    operator="BETWEEN",
                    date_min=current_date_time - datetime.timedelta(hours=2),
                    date_max=current_date_time + datetime.timedelta(hours=2),
                ),
            )
            if file_name_:
                file_name_ = file_name_[0]
            if file_name_ and os.path.isfile(file_name_):
                build_image(
                    image_path=file_name_,
                    main_wrapper=main_wrapper,
                    index=(counter + 1,),
                    script=script_.copy(),
                )
            else:
                has_missing_ = True
        if has_missing_:
            continue

        mosaic = main_wrapper.build_mosaic(
            (vid_height, vid_width, 3), MOSAIC_DATA, BACKGROUND_COLOR
        )
        time_counter += 1

        cv2.imwrite(f"{DST_PATH}{main_wrapper.plant}_{time_counter}.jpg", mosaic)

        def write_image_times(out_writer, img_, times=12):
            for _ in range(0, times):
                out_writer.write(img_)

        # Print source image
        write_image_times(out, mosaic)

        print_progress_bar(
            i, total=total, prefix="Building video:", suffix=f" {i}/{total} Complete"
        )

    # Release everything if job is finished
    out.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
