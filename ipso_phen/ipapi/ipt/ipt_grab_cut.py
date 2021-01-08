import cv2
import numpy as np


import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ipt_abstract import IptBase
from ipso_phen.ipapi.base.ip_common import ToolFamily, C_BLACK, ensure_odd


class IptGrabCut(IptBase):
    def build_params(self):
        self.add_roi_selector()
        self.add_spin_box(
            name="prob_dilate_size",
            desc="Size of dilation's kernel",
            default_value=0,
            minimum=0,
            maximum=101,
            hint="Size of kernel for the morphology operator applied to grow the source mask to set a probable mask",
        )
        self.add_spin_box(
            name="sure_erode_size",
            desc="Size of errode's kernel",
            default_value=0,
            minimum=0,
            maximum=101,
            hint="Size of kernel for the morphology operator applied to shrink the source mask to set a sure mask",
        )
        self.add_color_map_selector()
        self.add_spin_box(
            name="gc_iter_count",
            desc="GraphCut iterations allowed",
            default_value=5,
            minimum=1,
            maximum=100,
        )
        self.add_checkbox(name="build_mosaic", desc="Build mosaic", default_value=0)
        self.add_roi_selector()

    def process_wrapper(self, **kwargs):
        """
        Grab cut:
        Implementation of OpenCV grab cut function.

                Better if used with a ROI.

                Better if ROI is extracted from mask.

                Even better if used after keep linked contours builds a ROI & and a mask.
        Real time: False

        Keyword Arguments (in parentheses, argument name):
            * Name of ROI to be used (roi_names): Operation will only be applied inside of ROI
            * ROI selection mode (roi_selection_mode):
            * Size of dilation's kernel (prob_dilate_size): Size of kernel for the morphology operator applied to grow the source mask to set a probable mask
            * Size of errode's kernel (sure_erode_size): Size of kernel for the morphology operator applied to shrink the source mask to set a sure mask
            * Select pseudo color map (color_map):
            * GraphCut iterations allowed (gc_iter_count):
            * Build mosaic (build_mosaic):
            * Name of ROI to be used (roi_names): Operation will only be applied inside of ROI
            * ROI selection mode (roi_selection_mode):
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            # Get Source image
            img = wrapper.current_image
            # Get starting mask
            mask = self.get_mask()
            if mask is None:
                logger.error(f"FAIL {self.name}: mask must be initialized")
                return

            # Get ROI
            rois = self.get_ipt_roi(
                wrapper=wrapper,
                roi_names=self.get_value_of("roi_names").replace(" ", "").split(","),
                selection_mode=self.get_value_of("roi_selection_mode"),
            )
            if len(rois) > 0:
                roi = rois[0]
            else:
                roi = None

            # Initialize mask
            gc_in_mask = np.full_like(mask, cv2.GC_BGD)
            if roi is not None:
                gc_in_mask = roi.draw_to(gc_in_mask, line_width=-1, color=cv2.GC_PR_BGD)

            # Apply dilation
            dks = self.get_value_of("prob_dilate_size")
            0 if dks == 1 else ensure_odd(dks)
            if dks > 0:
                d_mask = wrapper.dilate(image=mask, kernel_size=dks)
                gc_in_mask[d_mask != 0] = cv2.GC_PR_FGD

            # Apply erosion
            eks = self.get_value_of("sure_erode_size")
            0 if eks == 1 else ensure_odd(eks)
            if eks > 0:
                e_mask = wrapper.erode(image=mask, kernel_size=eks)
                gc_in_mask[e_mask != 0] = cv2.GC_FGD
            else:
                gc_in_mask[mask != 0] = cv2.GC_FGD

            color_map = self.get_value_of("color_map")
            _, color_map = color_map.split("_")
            dbg_img = cv2.applyColorMap(
                self.to_uint8(gc_in_mask, normalize=True), int(color_map)
            )
            if roi is not None:
                dbg_img = roi.draw_to(dbg_img, line_width=wrapper.width // 200)
            wrapper.store_image(dbg_img, "grabcut_initialized_mask")

            # Initialize the other ones
            bgd_model = np.zeros((1, 65), np.float64)
            fgd_model = np.zeros((1, 65), np.float64)

            # Grab the cut
            cv2.grabCut(
                img=img,
                mask=gc_in_mask,
                rect=None if roi is None else roi.to_opencv(),
                bgdModel=bgd_model,
                fgdModel=fgd_model,
                iterCount=self.get_value_of("gc_iter_count"),
                mode=cv2.GC_INIT_WITH_MASK,
            )

            wrapper.store_image(
                cv2.applyColorMap(
                    self.to_uint8(gc_in_mask, normalize=True), int(color_map)
                ),
                "grabcut_false_color_mask",
            )

            self.result = np.where(gc_in_mask == cv2.GC_FGD, 255, 0).astype("uint8")
            wrapper.store_image(self.result, "grabcut_mask")

            wrapper.store_image(
                image=self.wrapper.draw_image(
                    src_image=img,
                    src_mask=self.result,
                    background="bw",
                    foreground="source",
                ),
                text="result_on_bw",
            )

            res = True

            if self.get_value_of("build_mosaic") == 1:
                canvas = wrapper.build_mosaic(
                    image_names=np.array(
                        [
                            [
                                "current_image",
                                "grabcut_initialized_mask",
                                "grabcut_false_color_mask",
                            ],
                            ["grabcut_mask", "", "result_on_bw"],
                        ]
                    )
                )
                wrapper.store_image(canvas, "mosaic")

        except Exception as e:
            logger.error(f'Failed to process {self. name}: "{repr(e)}"')
            res = False
        else:
            pass
        finally:
            return res

    @property
    def name(self):
        return "Grab cut"

    @property
    def is_wip(self):
        return True

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
        return [ToolFamily.MASK_CLEANUP]

    @property
    def description(self):
        return """Implementation of OpenCV grab cut function.\n
        Better if used with a ROI.\n
        Better if ROI is extracted from mask.\n
        Even better if used after keep linked contours builds a ROI & and a mask."""
