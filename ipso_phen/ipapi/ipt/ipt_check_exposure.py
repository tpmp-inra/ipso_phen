import cv2
import numpy as np
import os

import logging

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ip_common import all_colors_dict
from ipso_phen.ipapi.base.ipt_abstract_analyzer import IptBaseAnalyzer
from ipso_phen.ipapi.base.ip_common import ToolFamily
import ipso_phen.ipapi.tools.regions as regions


class IptExposureChecker(IptBaseAnalyzer):
    def build_params(self):
        self.add_checkbox(
            name="enabled",
            desc="Activate tool",
            default_value=1,
            hint="Toggle whether or not tool is active",
        )
        self.add_spin_box(
            name="overexposed_limit",
            desc="Overexposed if over: ",
            default_value=255,
            minimum=0,
            maximum=255,
        )
        self.add_color_selector(
            name="over_color",
            desc="Color for overexposed parts",
            default_value="red",
            enable_none=True,
        )
        self.add_spin_box(
            name="underexposed_limit",
            desc="Underexposed if under: ",
            default_value=0,
            minimum=0,
            maximum=255,
        )
        self.add_color_selector(
            name="under_color",
            desc="Color for underexposed parts",
            default_value="orange",
            enable_none=True,
        )
        self.add_checkbox(
            name="show_grey_zones", desc="Display grey zones", default_value=0
        )
        self.add_spin_box(
            name="grey_zone_limit",
            desc="Grey if more than x apart: ",
            default_value=0,
            minimum=0,
            maximum=255,
            hint="How little different must the 3 components be to be considered grey",
        )
        self.add_color_selector(
            name="grey_zone_color", desc="Color for grey parts", default_value="fuchsia"
        )

        self.add_separator(name="sep_1")
        self.add_source_selector(
            name="source_brightness",
            desc="Calculate source brightness on",
            default_value="source",
        )
        self.add_combobox(
            name="brg_calc",
            desc="Source brightness calculation mode",
            default_value="std",
            values=dict(
                none="none",
                std="Luminance (standard, objective)",
                p1="Luminance (perceived option 1)",
                p2="Luminance (perceived option 2, slower to calculate)",
            ),
        )
        self.add_combobox(
            name="average_as",
            desc="Use average brightness as:",
            default_value="none",
            values=dict(
                none="Nothing",
                average_as_lower="Use average brightness as underexposed threshold",
                average_as_upper="Use average brightness as overexposed threshold",
            ),
        )
        self.add_spin_box(
            name="avg_weight",
            desc="Apply x factor to auto threshold",
            default_value=100,
            minimum=0,
            maximum=200,
        )

        self.add_roi_selector()

        self.add_text_overlay()

    def process_wrapper(self, **kwargs):
        """
        Check exposure:
        Displays over/under exposed parts of the image
        Also displays average brightness of the image
        Real time: True

        Keyword Arguments (in parentheses, argument name):
            * Activate tool (enabled): Toggle whether or not tool is active
            * Overexposed if over:  (overexposed_limit):
            * Color for overexposed parts (over_color):
            * Underexposed if under:  (underexposed_limit):
            * Color for underexposed parts (under_color):
            * Display grey zones (show_grey_zones):
            * Grey if more than x apart:  (grey_zone_limit): How little different must the 3 components be to be considered grey
            * Color for grey parts (grey_zone_color):
            * Calculate source brightness on (source_brightness): no clue
            * Source brightness calculation mode (brg_calc):
            * Use average brightness as: (average_as):
            * Apply x factor to auto threshold (avg_weight):
            * Name of ROI to be used (roi_names): Operation will only be applied inside of ROI
            * ROI selection mode (roi_selection_mode):
            * Overlay text on top of images (text_overlay): Draw description text on top of images
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            self.data_dict = {}
            img = self.wrapper.current_image
            text_overlay = self.get_value_of("text_overlay") == 1
            br_dict = None
            if self.get_value_of("enabled") != 1:
                res = True
                wrapper.store_image(image=img, text="unaltered_image")
                return
            overexposed_limit = self.get_value_of(
                key="overexposed_limit", default_value=255
            )
            over_color = self.get_value_of(key="over_color", default_value="red")
            underexposed_limit = self.get_value_of(
                key="underexposed_limit", default_value=0
            )
            under_color = self.get_value_of(key="under_color", default_value="orange")

            show_grey_zones = self.get_value_of("show_grey_zones", default_value=0) == 1
            grey_zone_limit = self.get_value_of("grey_zone_limit", default_value=0)
            grey_zone_color = self.get_value_of("grey_zone_color", default_value="blue")
            brg_calc = self.get_value_of("brg_calc")
            text_overlay = self.get_value_of("text_overlay") == 1

            b, g, r = cv2.split(img.copy())

            # Calculate image brightness
            if brg_calc != "none":
                calc_img = wrapper.current_image
                wrapper.store_image(
                    calc_img, f'calc_image_{self.get_value_of("source_brightness")}'
                )
                bs, gs, rs = cv2.split(calc_img)
                if brg_calc == "std":
                    s = rs * 0.2126 + gs * 0.7152 + bs * 0.0722
                elif brg_calc == "p1":
                    s = rs * 0.299 + gs * 0.587 + bs * 0.114
                elif brg_calc == "p2":
                    s = np.sqrt(
                        0.241 * np.power(rs.astype(np.float), 2)
                        + 0.691 * np.power(gs.astype(np.float), 2)
                        + 0.068 * np.power(bs.astype(np.float), 2)
                    )
                else:
                    wrapper.error_list.add_error(
                        "Unknown brightness mode", target_logger=logger
                    )
                    return
                wrapper.store_image(
                    self.to_uint8(s),
                    f'brightness_{self.get_value_of("source_brightness")}',
                )
                s_tuple = cv2.meanStdDev(s.reshape(s.shape[1] * s.shape[0]))
                self.add_value("src_brightness", f"{s_tuple[0][0][0]:.2f}", True)
                self.add_value("src_contrast", f"{s_tuple[1][0][0]:.2f}", True)

                average_as = self.get_value_of("average_as")
                avg_weight = self.get_value_of("avg_weight")
                if average_as == "average_as_lower":
                    underexposed_limit = int(s_tuple[0][0][0] / 100 * avg_weight)
                elif average_as == "average_as_upper":
                    overexposed_limit = int(s_tuple[0][0][0] / 100 * avg_weight)
            else:
                br_dict = None

            # Handle grey areas
            if show_grey_zones:
                avg = (b.astype(np.int32) + g.astype(np.int32) + r.astype(np.int32)) / 3
                b_abs_diff = np.absolute(b - avg).astype(np.int32)
                g_abs_diff = np.absolute(g - avg).astype(np.int32)
                r_abs_diff = np.absolute(r - avg).astype(np.int32)
                abs_avg_diff = (
                    (b_abs_diff + g_abs_diff + r_abs_diff).astype(np.int32) / 3
                ).astype(np.uint8)

                mask_grey = cv2.inRange(abs_avg_diff, 0, grey_zone_limit)
            else:
                mask_grey = None

            # Handle over & under exposure
            mask_over = cv2.inRange(
                img,
                (overexposed_limit, overexposed_limit, overexposed_limit),
                (255, 255, 255),
            )
            mask_under = cv2.inRange(
                img,
                (0, 0, 0),
                (underexposed_limit, underexposed_limit, underexposed_limit),
            )

            if show_grey_zones and (mask_grey is not None):
                img[mask_grey > 0] = all_colors_dict[grey_zone_color]
            if over_color != "none":
                img[mask_over > 0] = all_colors_dict[over_color]
            if under_color != "none":
                img[mask_under > 0] = all_colors_dict[under_color]

            rois = self.get_ipt_roi(
                wrapper=wrapper,
                roi_names=self.get_value_of("roi_names").replace(" ", "").split(","),
                selection_mode=self.get_value_of("roi_selection_mode"),
            )
            if len(rois) > 0:
                self.result = regions.copy_rois(
                    rois=rois, src=img, dst=self.wrapper.current_image
                )
            else:
                self.result = img

            if text_overlay and (br_dict is not None):
                wrapper.store_image(
                    self.result,
                    f"exposure_{self.input_params_as_str()}",
                    text_overlay="\n".join(
                        [f'{k.replace("_", " ")}: {v}' for k, v in br_dict.items()]
                    ),
                )
            else:
                wrapper.store_image(
                    self.result,
                    f"exposure_{self.input_params_as_str()}",
                    text_overlay=False,
                )

            self.demo_image = self.result
            if len(rois) > 0:
                for roi in rois:
                    self.demo_image = roi.draw_to(self.demo_image, line_width=2)

            res = True

        except Exception as e:
            logger.error(f'Failed to process {self. name}: "{repr(e)}"')
            res = False
        else:
            pass
        finally:
            return res

    @property
    def name(self):
        return "Check exposure"

    @property
    def real_time(self):
        return self.get_value_of("calculate_brightness") != 1

    @property
    def result_name(self):
        return "image"

    @property
    def output_kind(self):
        return "image"

    @property
    def use_case(self):
        return [ToolFamily.PRE_PROCESSING]

    @property
    def description(self):
        return "Displays over/under exposed parts of the image\nAlso displays average brightness of the image"
