import argparse
import csv
import cv2
import numpy as np
import os
import sys

abspath = os.path.abspath(__file__)
fld_name = os.path.dirname(abspath)
sys.path.insert(0, fld_name)
sys.path.insert(0, os.path.dirname(fld_name))

from ip_base.ip_abstract import AbstractImageProcessor
from ip_base.ipt_functional import call_ipt, call_ipt_func
from tools.csv_writer import AbstractCsvWriter


def main():
    # Get the file
    # ____________
    # Set working folder
    old_wd = os.getcwd()
    abspath = os.path.abspath(__file__)
    fld_name = os.path.dirname(abspath)
    os.chdir(fld_name)

    # Construct the argument parser and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--image", required=True, help="Path to the image")
    ap.add_argument("-d", "--destination", required=False, help="Destination folder")
    args = vars(ap.parse_args())
    file_name = args["image"]
    dst_folder = args.get("destination", "")

    # Restore working folder
    os.chdir(old_wd)

    # Build wrapper
    # _____________
    wrapper = AbstractImageProcessor(file_name)
    wrapper.lock = True
    wrapper.store_image(wrapper.current_image, "true_source_image")
    wrapper.write_images = "plot"

    # Fix exposure
    # ____________________
    wrapper.current_image = call_ipt(
        ipt_id="IptLinearTransformation",
        source=wrapper,
        method="alpha_beta_target",
        target_brightness=90,
    )

    # Store image name for analysis
    wrapper.store_image(wrapper.current_image, "exposure_fixed")
    analysis_image = "exposure_fixed"

    # Build dynamic ROIs
    # __________________
    roi = call_ipt_func(
        ipt_id="IptHoughCircles",
        source=wrapper,
        function_name="generate_roi",
        roi_name="keep_roi",
        roi_shape="circle",
        min_radius=700,
        max_radius=750,
        keep_only_one=1,
        target_position="MIDDLE_CENTER",
        expand_circle=-170,
        operator="sobel",
        threshold=132,
    )
    if roi is not None:
        wrapper.add_roi(new_roi=roi)

    # Pre process image (make segmentation easier)
    # ____________________________________________
    wrapper.current_image = call_ipt(
        ipt_id="IptExposureChecker",
        source=wrapper,
        overexposed_limit=200,
        over_color="blue_cabin",
        underexposed_limit=27,
        under_color="blue_cabin",
    )

    # Build coarse masks
    # __________________
    mask_list = []
    current_mask_ = call_ipt(
        ipt_id="IptThreshold", source=wrapper, min_t=10, max_t=60, morph_op="open", proc_times=2
    )
    mask_list.append(current_mask_)

    # Merge masks
    func = getattr(wrapper, "multi_and", None)
    if func:
        wrapper.mask = func([mask for mask in mask_list if mask is not None])
        wrapper.store_image(wrapper.mask, f"mask_multi_and")
    else:
        wrapper.error_holder.add_error("Unable to merge coarse masks")
        return

    # ROIs to be applied after mask merging
    # _____________________________________
    handled_rois = ["keep", "delete", "erode", "dilate", "open", "close"]
    rois_list = [
        roi
        for roi in wrapper.rois_list
        if roi.tag in handled_rois and not (roi.target and roi.target != "none")
    ]
    wrapper.mask = wrapper.apply_roi_list(img=wrapper.mask, rois=rois_list, print_dbg=True)

    # Clean merged mask
    # _________________
    wrapper.mask = call_ipt(
        ipt_id="IptKeepLinkedContours",
        source=wrapper,
        tolerance_distance=10,
        root_position="MIDDLE_CENTER",
        delete_all_bellow=100,
    )
    if wrapper.mask is None:
        return

    # Check that the mask is where it belongs
    # _______________________________________
    res = True
    enforcers_list = wrapper.get_rois({"enforce"})
    for i, enforcer in enumerate(enforcers_list):
        mask = wrapper.mask.copy()
        mask = wrapper.keep_roi(mask, enforcer)
        partial_ok = np.count_nonzero(mask) > 0
        res = partial_ok and res
        if partial_ok:
            roi_img = np.dstack((np.zeros_like(mask), mask, np.zeros_like(mask)))
        else:
            roi_img = np.dstack((np.zeros_like(mask), np.zeros_like(mask), mask))
        background_img = cv2.bitwise_and(wrapper.mask, wrapper.mask, mask=255 - mask)
        img = cv2.bitwise_or(
            roi_img, np.dstack((background_img, background_img, background_img))
        )
        enforcer.draw_to(img, line_width=4)
        wrapper.store_image(img, f"enforcer_{i}_{enforcer.name}")
    if not res:
        return

    # Extract features
    # ________________
    wrapper.current_image = wrapper.retrieve_stored_image("exposure_fixed")
    wrapper.csv_data_holder = AbstractCsvWriter()
    current_data = call_ipt(ipt_id="IptAnalyseObservation", source=wrapper,)
    if isinstance(current_data, dict):
        wrapper.csv_data_holder.data_list.update(current_data)
    else:
        wrapper.error_holder.add_error("Failed to add extracted data")

    current_data = call_ipt(ipt_id="IptAnalyzeColor", source=wrapper,)
    if isinstance(current_data, dict):
        wrapper.csv_data_holder.data_list.update(current_data)
    else:
        wrapper.error_holder.add_error("Failed to add extracted data")

    current_data = call_ipt(ipt_id="IptAnalyzeObject", source=wrapper,)
    if isinstance(current_data, dict):
        wrapper.csv_data_holder.data_list.update(current_data)
    else:
        wrapper.error_holder.add_error("Failed to add extracted data")

    # Save CSV
    if dst_folder and (len(wrapper.csv_data_holder) > 0):
        with open(
            os.path.join(dst_folder, "", wrapper.file_handler.file_name_no_ext + ".csv"),
            "w",
            newline="",
        ) as csv_file_:
            wr = csv.writer(csv_file_, quoting=csv.QUOTE_NONE)
            wr.writerow(wrapper.csv_data_holder.header_to_list())
            wr.writerow(wrapper.csv_data_holder.data_to_list())

    print("Done.")


if __name__ == "__main__":
    main()
