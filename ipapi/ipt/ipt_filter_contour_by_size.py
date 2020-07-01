from base.ipt_abstract import IptBase
import numpy as np
import cv2
from base import ip_common as ipc


class IptFilterContourBySize(IptBase):
    def build_params(self):
        self.add_enabled_checkbox()
        self.add_combobox(
            name="mode",
            desc="Keep contours",
            default_value="big",
            values={"big": "Bigger than", "small": "Smaller than"},
        )
        self.add_spin_box(
            name="threshold", desc="Threshold", default_value=1000, minimum=0, maximum=100000
        )
        self.add_roi_selector()

    def process_wrapper(self, **kwargs):
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            if self.get_value_of("enabled") == 1:
                img = wrapper.current_image
                mask = self.get_mask()
                if mask is None:
                    wrapper.error_holder.add_error(
                        f"FAIL {self.name}: mask must be initialized"
                    )
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
                        rois_mask = roi.draw_to(dst_img=rois_mask, line_width=-1, color=255)
                    mask = np.logical_and(mask, rois_mask)
                wrapper.store_image(mask, "mask_after_roi")

                # Get source contours
                contours = ipc.get_contours(
                    mask=mask, retrieve_mode=cv2.RETR_LIST, method=cv2.CHAIN_APPROX_SIMPLE
                )
                dbg_mask = np.dstack(
                    (np.zeros_like(mask), np.zeros_like(mask), np.zeros_like(mask))
                )
                colors = ipc.build_color_steps(ipc.C_BLUE, ipc.C_YELLOW, len(contours))
                for clr, cnt in zip(colors, reversed(contours[:-1])):
                    # dbg_mask = np.dstack(
                    #     (np.zeros_like(mask), np.zeros_like(mask), np.zeros_like(mask))
                    # )
                    cv2.drawContours(dbg_mask, [cnt], 0, clr, -1)
                wrapper.store_image(image=dbg_mask, text="all_contours")

                t = self.get_value_of("threshold")
                m = self.get_value_of("mode")
                dbg_mask = np.dstack(
                    (np.zeros_like(mask), np.zeros_like(mask), np.zeros_like(mask))
                )
                fnt = (cv2.FONT_HERSHEY_SIMPLEX, 0.6)
                for cnt in contours:
                    area_ = cv2.contourArea(cnt)
                    if (area_ < t and m == "big") or (area_ > t and m == "small"):
                        cv2.drawContours(mask, [cnt], 0, 0, -1)
                        cv2.drawContours(dbg_mask, [cnt], 0, ipc.C_RED, -1)
                    else:
                        cv2.drawContours(dbg_mask, [cnt], 0, ipc.C_GREEN, -1)
                    x, y, w, h = cv2.boundingRect(cnt)
                    x += w // 2 - 10
                    y += h // 2
                    cv2.putText(
                        dbg_mask,
                        f"Area: {area_}",
                        (x, y),
                        fnt[0],
                        fnt[1],
                        ipc.C_FUCHSIA,
                        thickness=2,
                    )

                wrapper.store_image(image=mask, text="filtered_contours")
                wrapper.store_image(image=dbg_mask, text="tagged_contours")
                self.result = mask
                self.demo_image = dbg_mask
                res = True
            else:
                wrapper.store_image(wrapper.current_image, "current_image")
                res = True
        except Exception as e:
            res = False
            wrapper.error_holder.add_error(
                f"Filter contour by size FAILED, exception: {repr(e)}"
            )
        else:
            pass
        finally:
            return res

    @property
    def name(self):
        return "Filter contour by size (WIP)"

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
        return ["Mask cleanup"]

    @property
    def description(self):
        return """'Keep or descard contours according to their size"""
