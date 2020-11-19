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

from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
from ipso_phen.ipapi.base.ipt_functional import call_ipt, call_ipt_func
import ipso_phen.ipapi.base.ip_common as ipc
from ipso_phen.ipapi.tools.csv_writer import AbstractCsvWriter


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
    ap.add_argument("-p", "--print_images", required=False, help="Print images, y or n")
    ap.add_argument("-m", "--print_mosaic", required=False, help="Print mosaic, y or n")
    args = vars(ap.parse_args())
    file_name = args["image"]
    print_images = args.get("print_images", "n") == "y"
    print_mosaic = args.get("print_mosaic", "n") == "y"
    dst_folder = args.get("destination", "")

    # Restore working folder
    os.chdir(old_wd)

    # Build wrapper
    # _____________
    wrapper = BaseImageProcessor(file_name)
    wrapper.lock = True
    wrapper.store_image(wrapper.current_image, "true_source_image")
    if print_images or print_mosaic:
        wrapper.store_images = True
    if print_images:
        wrapper.write_images = "plot"
    if print_mosaic:
        wrapper.write_mosaic = "plot"

    # Fix exposure
    # ____________________
    wrapper.current_image = call_ipt(
        ipt_id="IptLinearTransformation",
        source=wrapper,
        return_type="result",
        method="gamma_target",
        target_brightness=145,
        text_overlay=1,
    )

    # Store image name for analysis
    wrapper.store_image(wrapper.current_image, "exposure_fixed")
    analysis_image = "exposure_fixed"

    if print_mosaic:
        wrapper.store_image(wrapper.current_image, "fixed_source")
    # Build static ROIs
    # _________________
    roi = call_ipt_func(
        ipt_id="IptRoiManager",
        source=wrapper,
        function_name="generate_roi",
        roi_name="check_exp_pot_top",
        roi_type="other",
        tool_target="IptExposureChecker",
        left=394,
        width=1317,
        top=1990,
        height=70,
    )
    if roi is not None:
        wrapper.add_roi(new_roi=roi)

    roi = call_ipt_func(
        ipt_id="IptRoiManager",
        source=wrapper,
        function_name="generate_roi",
        roi_name="check_exp_pot_bottom",
        roi_type="other",
        tool_target="IptExposureChecker",
        left=394,
        width=1317,
        top=2049,
        height=320,
    )
    if roi is not None:
        wrapper.add_roi(new_roi=roi)

    roi = call_ipt_func(
        ipt_id="IptRoiManager",
        source=wrapper,
        function_name="generate_roi",
        roi_name="check_exp_top",
        roi_type="other",
        tool_target="IptExposureChecker",
        left=1583,
        width=461,
        height=90,
    )
    if roi is not None:
        wrapper.add_roi(new_roi=roi)

    roi = call_ipt_func(
        ipt_id="IptRoiManager",
        source=wrapper,
        function_name="generate_roi",
        roi_name="open_pot_top",
        roi_type="open",
        left=500,
        width=1100,
        top=1940,
        height=200,
    )
    if roi is not None:
        wrapper.add_roi(new_roi=roi)

    roi = call_ipt_func(
        ipt_id="IptRoiManager",
        source=wrapper,
        function_name="generate_roi",
        roi_name="erode_pot_bottom",
        roi_type="erode",
        left=500,
        width=1100,
        top=2140,
        height=240,
    )
    if roi is not None:
        wrapper.add_roi(new_roi=roi)

    roi = call_ipt_func(
        ipt_id="IptRoiManager",
        source=wrapper,
        function_name="generate_roi",
        roi_name="keep_roi",
        left=200,
        width=1600,
        height=2350,
    )
    if roi is not None:
        wrapper.add_roi(new_roi=roi)

    roi = call_ipt_func(
        ipt_id="IptRoiManager",
        source=wrapper,
        function_name="generate_roi",
        roi_name="erode_top_right",
        roi_type="erode",
        left=1606,
        width=279,
        top=2,
        height=376,
    )
    if roi is not None:
        wrapper.add_roi(new_roi=roi)

    roi = call_ipt_func(
        ipt_id="IptRoiManager",
        source=wrapper,
        function_name="generate_roi",
        roi_name="open_left_leg",
        roi_type="open",
        left=527,
        width=140,
        top=2050,
        height=381,
    )
    if roi is not None:
        wrapper.add_roi(new_roi=roi)

    roi = call_ipt_func(
        ipt_id="IptRoiManager",
        source=wrapper,
        function_name="generate_roi",
        roi_name="open_right_leg",
        roi_type="open",
        left=1390,
        width=140,
        top=2050,
        height=381,
    )
    if roi is not None:
        wrapper.add_roi(new_roi=roi)

    roi = call_ipt_func(
        ipt_id="IptRoiManager",
        source=wrapper,
        function_name="generate_roi",
        roi_name="split_threshold_inside_bottom",
        tool_target="IptSplittedRangeThreshold",
        left=489,
        width=1071,
        top=2019,
        height=427,
    )
    if roi is not None:
        wrapper.add_roi(new_roi=roi)

    roi = call_ipt_func(
        ipt_id="IptRoiManager",
        source=wrapper,
        function_name="generate_roi",
        roi_name="split_threshold_inside_top_right",
        tool_target="IptSplittedRangeThreshold",
        left=1593,
        width=453,
        height=370,
    )
    if roi is not None:
        wrapper.add_roi(new_roi=roi)

    roi = call_ipt_func(
        ipt_id="IptRoiManager",
        source=wrapper,
        function_name="generate_roi",
        roi_name="split_threshold_inside_right",
        tool_target="IptSplittedRangeThreshold",
        left=1920,
        width=125,
        top=351,
        height=2088,
    )
    if roi is not None:
        wrapper.add_roi(new_roi=roi)

    # Pre process image (make segmentation easier)
    # ____________________________________________
    wrapper.current_image = call_ipt(
        ipt_id="IptPartialPosterizer",
        source=wrapper,
        return_type="result",
        blue_color="black",
        post_blue_value=41,
    )

    wrapper.current_image = call_ipt(
        ipt_id="IptExposureChecker",
        source=wrapper,
        return_type="result",
        overexposed_limit=200,
        over_color="black",
        underexposed_limit=40,
        under_color="black",
        show_grey_zones=1,
        grey_zone_limit=2,
        grey_zone_color="black",
        roi_names="check_exp_pot_top,check_exp_top",
    )

    wrapper.current_image = call_ipt(
        ipt_id="IptExposureChecker",
        source=wrapper,
        return_type="result",
        overexposed_limit=180,
        over_color="black",
        underexposed_limit=20,
        under_color="black",
        show_grey_zones=1,
        grey_zone_limit=6,
        grey_zone_color="black",
        roi_names="check_exp_pot_bottom",
    )

    if print_mosaic:
        wrapper.store_image(wrapper.current_image, "pre_processed_image")
    # Build coarse masks
    # __________________
    mask_list = []
    current_mask_ = call_ipt(
        ipt_id="IptThreshold", source=wrapper, return_type="result", channel="l", min_t=15
    )
    mask_list.append(current_mask_)

    current_mask_ = call_ipt(
        ipt_id="IptSplittedRangeThreshold",
        source=wrapper,
        return_type="result",
        channel="b",
        roi_names="split_threshold_inside_bottom,split_threshold_inside_top_right,split_threshold_inside_right",
        min_inside_t=135,
        min_outside_t=120,
        kernel_size=4,
        build_mosaic=1,
    )
    mask_list.append(current_mask_)

    # Merge masks
    func = getattr(wrapper, "multi_and", None)
    if func:
        wrapper.mask = func([mask for mask in mask_list if mask is not None])
        wrapper.store_image(wrapper.mask, f"mask_multi_and")
        if print_mosaic:
            wrapper.store_image(wrapper.mask, "coarse_mask")
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
    wrapper.mask = wrapper.apply_roi_list(
        img=wrapper.mask, rois=rois_list, print_dbg=True
    )
    if print_mosaic:
        wrapper.store_image(wrapper.mask, "mask_after_roi")

    # Clean merged mask
    # _________________
    wrapper.mask = call_ipt(
        ipt_id="IptKeepLinkedContours",
        source=wrapper,
        return_type="result",
        tolerance_distance=50,
        tolerance_area=500,
        root_position="MIDDLE_CENTER",
    )
    if wrapper.mask is None:
        return

    if print_mosaic:
        wrapper.store_image(wrapper.mask, "clean_mask")

    # Check that the mask is where it belongs
    # _______________________________________
    mask = None
    if print_images:
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
    else:
        enforcers_list = wrapper.get_rois({"enforce"})
        for i, enforcer in enumerate(enforcers_list):
            mask = wrapper.mask.copy()
            mask = wrapper.keep_roi(mask, enforcer)
            if np.count_nonzero(mask) == 0:
                return

    # Print selection as color on bw background
    # ____________________________________________
    id_objects, obj_hierarchy = ipc.get_contours_and_hierarchy(
        mask=mask, retrieve_mode=cv2.RETR_TREE, method=cv2.CHAIN_APPROX_NONE
    )
    wrapper.object_composition(wrapper.current_image, id_objects, obj_hierarchy)

    # Build mosaic
    # ____________
    if print_mosaic:
        wrapper.store_mosaic = "result"
        wrapper.mosaic_data = np.array(
            [
                ["fixed_source", "pre_processed_image", "coarse_mask"],
                [
                    "mask_after_roi",
                    "clean_mask",
                    wrapper.draw_image(
                        src_image=wrapper.current_image,
                        src_mask=wrapper.mask,
                        background="bw",
                        foreground="source",
                        bck_grd_luma=120,
                        contour_thickness=6,
                        hull_thickness=6,
                        width_thickness=6,
                        height_thickness=6,
                        centroid_width=20,
                        centroid_line_width=8,
                    ),
                ],
            ]
        )
        wrapper.print_mosaic(padding=4)

    print("Done.")


if __name__ == "__main__":
    main()
