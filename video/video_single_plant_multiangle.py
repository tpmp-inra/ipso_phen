import datetime
import multiprocessing as mp
import os
import sys

import cv2
import numpy as np

abspath = os.path.abspath(__file__)
fld_name = os.path.dirname(abspath)
sys.path.insert(0, fld_name)
sys.path.insert(0, os.path.dirname(fld_name))
sys.path.insert(0, os.path.join(os.path.dirname(fld_name), 'ipso_phen', ''))
os.chdir(fld_name)

import ipso_phen.tools.db_wrapper as dbw
from ipso_phen.ip_base.ip_abstract import AbstractImageProcessor
from ipso_phen.ip_base.ipt_functional import call_ipt
from ipso_phen.tools.common_functions import print_progress_bar

EXPERIMENT = '16AS_MAPPI3_1605'.lower()
DST_PATH = f'C:\\Users\\fmavianemac\\Videos\\TPMP_output\\{EXPERIMENT}\\'
VIDEO_WIDTH, VIDEO_HEIGHT = 1920, 1080

SELECTED_ANGLES = ['side0', 'side135', 'side270']

MOSAIC_DATA = np.array(SELECTED_ANGLES)

MAX_CORES = 1


def build_image(wrapper):
    return wrapper.current_image
    # return call_ipt(ipt_id="IptLinearTransformation",
    #                 source=wrapper,
    #                 method='alpha_beta_target',
    #                 target_brightness=150)


def build_video(arg):
    p_plant = arg

    p_output = os.path.join(DST_PATH, f'{p_plant}.mp4')
    if os.path.isfile(p_output):
        return f'Plant {p_plant} already handled'

    db_ = dbw.get_rw_dbw(dbw.DB_INFO_EXT_HD)
    ret = db_.query(command='SELECT',
                    columns='FilePath',
                    additional='ORDER BY DateTime ASC',
                    Experiment=EXPERIMENT,
                    Plant=p_plant,
                    ViewOption=SELECTED_ANGLES[0])
    main_angle_image_list_ = [item[0] for item in ret]

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(p_output, fourcc, 24.0, (VIDEO_WIDTH, VIDEO_HEIGHT))
    fnt = cv2.FONT_HERSHEY_DUPLEX

    for main_angle_image_ in main_angle_image_list_:
        main_angle_wrapper_side = AbstractImageProcessor(main_angle_image_)
        try:
            img_main_angle = build_image(main_angle_wrapper_side)
            main_angle_wrapper_side.store_image(img_main_angle, SELECTED_ANGLES[0])
        except Exception as e:
            print(f'Exception "{repr(e)}" while handling {str(main_angle_wrapper_side)}')

        current_date_time = main_angle_wrapper_side.date_time

        for secondary_angle in SELECTED_ANGLES[1:]:
            secondary_angle_image_ = db_.query_one(command='SELECT',
                                                   columns='FilePath',
                                                   additional='ORDER BY DateTime ASC',
                                                   Experiment=EXPERIMENT,
                                                   Plant=p_plant,
                                                   ViewOption=secondary_angle,
                                                   DateTime=dict(operator='BETWEEN',
                                                                 date_min=current_date_time - datetime.timedelta(hours=1),
                                                                 date_max=current_date_time + datetime.timedelta(hours=1)))
            if secondary_angle_image_:
                secondary_angle_image_ = secondary_angle_image_[0]
            if secondary_angle_image_ and os.path.isfile(secondary_angle_image_):
                secondary_angle_wrapper = AbstractImageProcessor(secondary_angle_image_)
                try:
                    secondary_angle_img = build_image(secondary_angle_wrapper)
                    main_angle_wrapper_side.store_image(secondary_angle_img, secondary_angle)
                except Exception as e:
                    print(f'Exception "{repr(e)}" while handling {str(secondary_angle_wrapper)}')

        mosaic = main_angle_wrapper_side.build_mosaic((VIDEO_HEIGHT, VIDEO_WIDTH, 3), MOSAIC_DATA)
        cv2.putText(mosaic,
                    current_date_time.strftime('%d/%m/%Y - %H:%M:%S'),
                    (10, 1000),
                    fnt,
                    1,
                    (255, 0, 255),
                    2,
                    cv2.LINE_AA)

        # cv2.imwrite(f'{os.path.dirname(p_output)}/{main_angle_wrapper_side.luid}.jpg', mosaic)

        def write_image_times(out_writer, img_, times=24):
            for _ in range(0, times):
                out_writer.write(img_)

        # Print source image
        write_image_times(out, mosaic)

    # Release everything if job is finished
    out.release()
    cv2.destroyAllWindows()

    return None


def main():
    if not os.path.exists(DST_PATH):
        os.makedirs(DST_PATH)

    ret = dbw.get_rw_dbw(dbw.DB_INFO_EXT_HD).query(command='SELECT DISTINCT',
                                               columns='Plant',
                                               Experiment=EXPERIMENT)
    plant_list_ = [item[0] for item in ret]

    num_cores = min([MAX_CORES, mp.cpu_count()])
    pool = mp.Pool(num_cores)
    chunky_size_ = 1
    total_ = len(plant_list_)
    print_progress_bar(0, total=total_, prefix='Building videos:', suffix=f' {0}/{total_} Complete')
    for i, _ in enumerate(pool.imap_unordered(build_video, (plant_ for plant_ in plant_list_), chunky_size_)):
        print_progress_bar(i + 1, total=total_, prefix='Building videos:', suffix=f' {i + 1}/{total_} Complete')
    print_progress_bar(1, total=1, prefix='Done:', suffix=f' {1}/{1} Complete')


if __name__ == '__main__':
    main()
