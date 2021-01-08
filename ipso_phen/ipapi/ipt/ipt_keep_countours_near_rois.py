import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

import numpy as np
import cv2

from ipso_phen.ipapi.base.ipt_abstract import IptBase
from ipso_phen.ipapi.base import ip_common as ipc


class IptKeepCountoursNearRois(IptBase):
    def build_params(self):
        self.add_enabled_checkbox()
        self.add_roi_selector()
        self.add_separator(name="sp_1")
        self.add_label(name="lbl_init_phase", desc="Initialization phase")
        self.add_spin_box(
            name="init_max_distance",
            desc="Maximum distance to ROI",
            default_value=0,
            minimum=0,
            maximum=10000,
            hint="""Maximum distance to add a contour on initialization phase.
            If distance is >0, ROIs will dilated with a kernel of size distance.""",
        )
        self.add_spin_box(
            name="init_min_size",
            desc="Minimum contour size",
            default_value=100,
            minimum=0,
            maximum=10000,
            hint="Minimum accepted size for a contour on initialization phase",
        )
        self.add_spin_box(
            name="delete_all_bellow",
            desc="Delete all contours smaller than",
            default_value=0,
            minimum=0,
            maximum=50000,
            hint="""All contours below this size will be permanently ignored.
            The more smaller contours are delete, the faster the algorithm""",
        )
        self.add_separator(name="sp_2")
        self.add_label(name="lbl_agg_phase", desc="Aggregation phase")
        self.add_spin_box(
            name="root_merge_distance",
            desc="Merge distance for root contours",
            default_value=100,
            minimum=0,
            maximum=50000,
        )
        self.add_spin_box(
            name="small_contours_distance_tolerance",
            desc="Aggregate small contours inside ROIs distance",
            default_value=100,
            minimum=0,
            maximum=5000,
            hint="""Aggregate small contours inside ROIs if closer than x to any root contour.
            Any aggregated contour is considered as a root one.""",
        )
        self.add_spin_box(
            name="unk_contours_distance_tolerance",
            desc="Aggregate unknown contours distance",
            default_value=100,
            minimum=0,
            maximum=5000,
            hint="""Aggregate unknown contours if closer than x to any root contour.
            Any aggregated contour is considered as a root one.""",
        )

    def draw_contours(self, canvas, contours, image_name, contours_data):
        fnt = (cv2.FONT_HERSHEY_SIMPLEX, 0.6)
        for cnt_data in contours_data:
            labels = [item["label"] for item in contours[cnt_data["name"]]]
            if not labels:
                continue
            colors = ipc.build_color_steps(
                step_count=max(labels) + 1,
            )
            for item in contours[cnt_data["name"]]:
                cv2.drawContours(
                    image=canvas,
                    contours=[item["cnt"]],
                    contourIdx=-1,
                    color=colors[item["label"]],
                    thickness=-1,
                )
                if cnt_data["print_label"] is True:
                    x, y, _, _ = cv2.boundingRect(item["cnt"])
                    cv2.putText(
                        img=canvas,
                        text=f"{item['label']}",
                        org=(x - 4, y - 4),
                        fontFace=fnt[0],
                        fontScale=fnt[1],
                        color=colors[item["label"]],
                        thickness=2,
                    )

        self.wrapper.store_image(canvas, image_name)
        return canvas

    def process_wrapper(self, **kwargs):
        """
        Keep countours near ROIs:
        Keep big contours inside a series of ROIs.
        Small contours inside ROIs may be added on conditions.
        Contours outsside ROIs may be added to root contours if close enough
        Real time: False

        Keyword Arguments (in parentheses, argument name):
            * Activate tool (enabled): Toggle whether or not tool is active
            * Name of ROI to be used (roi_names): Operation will only be applied inside of ROI
            * ROI selection mode (roi_selection_mode):
            * Maximum distance to ROI (init_max_distance):
                    Maximum distance to add a contour on initialization phase.
                    If distance is >0, ROIs will dilated with a kernel of size distance.
            * Minimum contour size (init_min_size): Minimum accepted size for a contour on initialization phase
            * Delete all contours smaller than (delete_all_bellow):
                    All contours below this size will be permanently ignored.
                    The more smaller contours are delete, the faster the algorithm
            * Merge distance for root contours (root_merge_distance):
            * Aggregate small contours inside ROIs distance (small_contours_distance_tolerance):
                    Aggregate small contours inside ROIs if closer than x to any root contour.
                    Any aggregated contour is considered as a root one.
            * Aggregate unknown contours distance (unk_contours_distance_tolerance):
                    Aggregate unknown contours if closer than x to any root contour.
                    Any aggregated contour is considered as a root one.
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            if self.get_value_of("enabled") == 1:
                img = wrapper.current_image
                mask = self.get_mask()
                if mask is None:
                    logger.error(f"FAIL {self.name}: mask must be initialized")
                    return

                # Get ROIs as mask
                rois = self.get_ipt_roi(
                    wrapper=wrapper,
                    roi_names=self.get_value_of("roi_names").replace(" ", "").split(","),
                    selection_mode=self.get_value_of("roi_selection_mode"),
                )
                if rois:
                    rois_mask = np.zeros_like(mask)
                    for roi in rois:
                        rois_mask = roi.draw_to(
                            dst_img=rois_mask, line_width=-1, color=255
                        )
                else:
                    self.result = mask
                    logger.error(f"Warning {self.name}: must have at least one ROI")
                    res = True
                    return
                wrapper.store_image(rois_mask, "rois_as_mask")

                # Get source contours
                contours = ipc.get_contours(
                    mask=mask,
                    retrieve_mode=cv2.RETR_LIST,
                    method=cv2.CHAIN_APPROX_SIMPLE,
                )

                # Dilate ROIs
                init_max_distance = self.get_value_of("init_max_distance")
                if init_max_distance > 0:
                    rois_mask = wrapper.dilate(
                        image=rois_mask,
                        kernel_size=ipc.ensure_odd(i=init_max_distance, min_val=3),
                    )
                    wrapper.store_image(rois_mask, "dilated_rois")

                # Remove smaller contours
                delete_all_bellow = self.get_value_of("delete_all_bellow")
                if delete_all_bellow > 0:
                    fnt = (cv2.FONT_HERSHEY_SIMPLEX, 0.6)
                    small_img = mask.copy()
                    small_img = np.dstack((small_img, small_img, small_img))
                    for cnt in contours:
                        area_ = cv2.contourArea(cnt)
                        if area_ < delete_all_bellow:
                            # Delete
                            cv2.drawContours(mask, [cnt], 0, (0, 0, 0), -1)
                            # Print debug image
                            x, y, w, h = cv2.boundingRect(cnt)
                            x += w // 2 - 10
                            y += h // 2
                            cv2.drawContours(small_img, [cnt], -1, ipc.C_RED, -1)
                            cv2.putText(
                                small_img,
                                f"Area: {area_}",
                                (x, y),
                                fnt[0],
                                fnt[1],
                                ipc.C_FUCHSIA,
                                2,
                            )
                        else:
                            cv2.drawContours(small_img, [cnt], -1, ipc.C_GREEN, -1)
                    wrapper.store_image(small_img, "small_removed_mask")

                # Find root contours
                root_cnts = []
                small_cnts = []
                unk_cnts = []
                init_min_size = self.get_value_of("init_min_size")
                tmp_img = np.zeros_like(mask)
                for i, cnt in enumerate(contours):
                    cv2.drawContours(
                        image=tmp_img,
                        contours=[cnt],
                        contourIdx=0,
                        color=255,
                        thickness=-1,
                    )
                    intersection = cv2.bitwise_and(tmp_img, rois_mask)
                    cv2.drawContours(
                        image=tmp_img,
                        contours=[cnt],
                        contourIdx=0,
                        color=0,
                        thickness=-1,
                    )
                    if np.sum(intersection[intersection != 0]) > 0:
                        if cv2.contourArea(cnt) > init_min_size:
                            root_cnts.append(cnt)
                        else:
                            small_cnts.append(cnt)
                    else:
                        unk_cnts.append(cnt)
                # approx_eps = self.get_value_of("approx_eps") / 10000
                cnt_approx = {
                    "root": [{"cnt": cnt, "label": i} for i, cnt in enumerate(root_cnts)],
                    "small": [
                        {"cnt": cnt, "label": i + len(root_cnts)}
                        for i, cnt in enumerate(small_cnts)
                    ],
                    "unk": [
                        {"cnt": cnt, "label": i + len(root_cnts) + len(small_cnts)}
                        for i, cnt in enumerate(unk_cnts)
                    ],
                    "discarded": [],
                }
                cnt_data = [
                    {
                        "name": "root",
                        "start_color": (0, 50, 0),
                        "stop_color": (0, 255, 0),
                        "print_label": True,
                    },
                    {
                        "name": "small",
                        "start_color": (50, 0, 0),
                        "stop_color": (255, 0, 0),
                        "print_label": False,
                    },
                    {
                        "name": "unk",
                        "start_color": (0, 0, 50),
                        "stop_color": (0, 0, 255),
                        "print_label": False,
                    },
                ]
                bck_img = wrapper.current_image
                for roi in rois:
                    bck_img = roi.draw_to(
                        dst_img=bck_img, line_width=2, color=ipc.C_WHITE
                    )
                self.draw_contours(
                    canvas=bck_img,
                    contours=cnt_approx,
                    image_name="contours_after_init",
                    contours_data=cnt_data,
                )

                # Merge root contours by label
                root_merge_distance = self.get_value_of("root_merge_distance")
                stable = False
                step = 1
                while not stable and step < 100:
                    stable = True
                    for left_index, left in enumerate(cnt_approx["root"]):
                        for right_index, right in enumerate(cnt_approx["root"]):
                            if left_index == right_index:
                                continue
                            if (
                                left["label"] != right["label"]
                                and wrapper.contours_min_distance(
                                    left["cnt"], right["cnt"]
                                )
                                < root_merge_distance
                            ):
                                right["label"] = left["label"]
                                stable = False
                    self.draw_contours(
                        canvas=wrapper.current_image,
                        contours=cnt_approx,
                        image_name=f"merging_root_{step}",
                        contours_data=cnt_data,
                    )
                    step += 1
                self.draw_contours(
                    canvas=wrapper.current_image,
                    contours=cnt_approx,
                    image_name="root_labels_merged",
                    contours_data=cnt_data,
                )

                # Merge small contours
                small_contours_distance_tolerance = self.get_value_of(
                    "small_contours_distance_tolerance"
                )
                stable = False
                step = 1
                while not stable and step < 100:
                    stable = True
                    for root in cnt_approx["root"]:
                        i = 0
                        while i < len(cnt_approx["small"]):
                            small = cnt_approx["small"][i]
                            if (
                                wrapper.contours_min_distance(root["cnt"], small["cnt"])
                                < small_contours_distance_tolerance
                            ):
                                new_root = cnt_approx["small"].pop(i)
                                new_root["label"] = root["label"]
                                cnt_approx["root"].append(new_root)
                                stable = False
                            else:
                                i += 1
                    if not stable:
                        self.draw_contours(
                            canvas=wrapper.current_image,
                            contours=cnt_approx,
                            image_name=f"merging_small_{step}",
                            contours_data=cnt_data,
                        )
                    step += 1
                self.draw_contours(
                    canvas=wrapper.current_image,
                    contours=cnt_approx,
                    image_name="small_labels_merged",
                    contours_data=cnt_data,
                )

                # Merge unknown contours
                unk_contours_distance_tolerance = self.get_value_of(
                    "unk_contours_distance_tolerance"
                )
                stable = False
                step = 1
                while not stable and step < 100:
                    stable = True
                    for root in cnt_approx["root"]:
                        i = 0
                        while i < len(cnt_approx["unk"]):
                            unk = cnt_approx["unk"][i]
                            if (
                                wrapper.contours_min_distance(root["cnt"], unk["cnt"])
                                < unk_contours_distance_tolerance
                            ):
                                new_root = cnt_approx["unk"].pop(i)
                                new_root["label"] = root["label"]
                                cnt_approx["root"].append(new_root)
                                stable = False
                            else:
                                i += 1
                    if not stable:
                        self.draw_contours(
                            canvas=wrapper.current_image,
                            contours=cnt_approx,
                            image_name=f"merging_unk_{step}",
                            contours_data=cnt_data,
                        )
                    step += 1
                self.demo_image = self.draw_contours(
                    canvas=wrapper.current_image,
                    contours=cnt_approx,
                    image_name="unk_labels_merged",
                    contours_data=cnt_data,
                )

                # Clean mask
                contours = ipc.get_contours(
                    mask=mask,
                    retrieve_mode=cv2.RETR_LIST,
                    method=cv2.CHAIN_APPROX_SIMPLE,
                )
                src_image = wrapper.current_image
                for cnt in contours:
                    is_good_one = False
                    for root in cnt_approx["root"]:
                        if wrapper.contours_min_distance(root["cnt"], cnt) <= 0:
                            is_good_one = True
                            break
                    if is_good_one:
                        cv2.drawContours(src_image, [cnt], 0, (0, 255, 0), 2)
                    else:
                        cv2.drawContours(src_image, [cnt], 0, (0, 0, 255), 2)
                        cv2.drawContours(mask, [cnt], 0, 0, -1)
                wrapper.store_image(src_image, "kcnr_img_wth_tagged_cnt")
                wrapper.store_image(mask, "kcnr_final")

                self.result = mask

                res = True
            else:
                wrapper.store_image(wrapper.current_image, "current_image")
                res = True
        except Exception as e:
            res = False
            wrapper.error_holder.add_error(
                new_error_text=f'Failed to process {self. name}: "{repr(e)}"',
                new_error_level=35,
                target_logger=logger,
            )
        else:
            pass
        finally:
            return res

    @property
    def name(self):
        return "Keep countours near ROIs"

    @property
    def package(self):
        return "TPMP"

    @property
    def real_time(self):
        return False

    @property
    def result_name(self):
        return "mask"

    @property
    def output_kind(self):
        return "mask"

    @property
    def use_case(self):
        return [ipc.ToolFamily.MASK_CLEANUP]

    @property
    def description(self):
        return """Keep big contours inside a series of ROIs.
Small contours inside ROIs may be added on conditions.
Contours outsside ROIs may be added to root contours if close enough"""
