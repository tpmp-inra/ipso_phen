import multiprocessing as mp
import os

import cv2
import numpy as np

import db_tools as dbm
from ip_base.ip_abstract import AbstractImageProcessor
from ipt_tools import call_ipt
from tools.common_functions import print_progress_bar

EXPERIMENT = '10ac_mpo1_1904'.lower()
DST_PATH = f'C:\\Users\\fmavianemac\\Videos\\TPMP_output\\{EXPERIMENT}\\'
VIDEO_WIDTH, VIDEO_HEIGHT = 1920, 1080

SELECTED_VIEW_OPTION = 'sw755'

MAX_CORES = 1


def build_image(wrapper):
    # return wrapper.current_image
    return call_ipt(ipt_id="IptLinearTransformation",
                    source=wrapper,
                    method='alpha_beta_target',
                    target_brightness=70)


def build_video(arg):
    p_plant = arg

    p_output = os.path.join(DST_PATH, f'{p_plant}.mp4')
    if os.path.isfile(p_output):
        return f'Plant {p_plant} already handled'

    db_ = dbm.get_rw_dbw(dbm.DB_INFO_EXT_HD)
    ret = db_.query(command='SELECT',
                    columns='FilePath',
                    additional='ORDER BY DateTime ASC',
                    Experiment=EXPERIMENT,
                    Plant=p_plant,
                    ViewOption=SELECTED_VIEW_OPTION)
    main_angle_image_list_ = [item[0] for item in ret][1:]

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(p_output, fourcc, 24.0, (VIDEO_WIDTH, VIDEO_HEIGHT))
    fnt = cv2.FONT_HERSHEY_DUPLEX

    for main_angle_image_ in main_angle_image_list_:
        wrapper = AbstractImageProcessor(main_angle_image_)
        try:
            wrapper.store_image(build_image(wrapper=wrapper), 'built_image')
        except Exception as e:
            print(f'Exception "{repr(e)}" while handling {str(wrapper)}')
            continue

        frame = wrapper.build_mosaic((VIDEO_HEIGHT, VIDEO_WIDTH, 3), np.array(['built_image']))
        cv2.putText(frame,
                    wrapper.date_time.strftime('%d/%m/%Y - %H:%M:%S'),
                    (10, 1000),
                    fnt,
                    1,
                    (255, 0, 255),
                    2,
                    cv2.LINE_AA)

        # cv2.imwrite(f'{os.path.dirname(p_output)}/{wrapper.luid}.jpg', frame)

        def write_image_times(out_writer, img_, times=24):
            for _ in range(0, times):
                out_writer.write(img_)

        # Print source image
        write_image_times(out, frame)

    # Release everything if job is finished
    out.release()
    cv2.destroyAllWindows()

    return None


def main():
    if not os.path.exists(DST_PATH):
        os.makedirs(DST_PATH)

    ret = dbm.get_rw_dbw(dbm.DB_INFO_EXT_HD).query(command='SELECT DISTINCT',
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
