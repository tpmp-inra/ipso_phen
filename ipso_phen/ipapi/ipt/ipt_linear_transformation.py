import cv2
import numpy as np

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ip_common import C_WHITE, C_FUCHSIA, C_ORANGE
from ipso_phen.ipapi.base.ipt_abstract_analyzer import IptBaseAnalyzer
from ipso_phen.ipapi.base.ip_common import ToolFamily
from ipso_phen.ipapi.base.ip_common import ToolFamily


class IptLinearTransformation(IptBaseAnalyzer):
    def build_params(self):
        self.add_checkbox(
            name="enabled",
            desc="Activate tool",
            default_value=1,
            hint="Toggle whether or not tool is active",
        )
        self.add_combobox(
            name="method",
            desc="Select transformation",
            default_value="alpha_beta",
            values=dict(
                alpha_beta="Simple brightness and contrast",
                gamma="Gamma correction",
                alpha_beta_target="Reach target brightness using linear transformation",
                gamma_target="Reach target brightness using gamma correction",
                smart_target_brightness="Intelligent brightness fit",
            ),
        )
        self.add_combobox(
            name="apply_case",
            desc="Apply smart transformation if",
            default_value="always",
            values=dict(
                never="Never",
                always="Always",
                if_under="If image brightness is below target",
                if_over="If image brightness is over target",
            ),
        )
        self.add_spin_box(
            name="alpha_gamma",
            desc="Alpha/Gamma",
            default_value=100,
            minimum=1,
            maximum=400,
            hint="Alpha value for linear transformation, gamma for gamma correction",
        )
        self.add_spin_box(
            name="beta",
            desc="Beta (brightness)",
            default_value=0,
            minimum=-255,
            maximum=255,
        )
        self.add_spin_box(
            name="target_brightness",
            desc="Target brightness",
            default_value=0,
            minimum=0,
            maximum=255,
        )
        self.add_spin_box(
            name="max_delta_for_brightness",
            desc="Limit brightness fixing",
            default_value=255,
            minimum=0,
            maximum=255,
        )
        self.add_roi_selector()
        self.add_exposure_viewer_switch()
        self.add_combobox(
            name="brg_calc",
            desc="Brightness calculation mode",
            default_value="std",
            values=dict(
                none="none",
                std="Luminance (standard, objective)",
                p1="Luminance (perceived option 1)",
                p2="Luminance (perceived option 2, slower to calculate)",
            ),
        )
        self.add_text_overlay()

    @staticmethod
    def apply_gamma(img, gamma):
        if gamma != 1:
            inv_gamma = 1.0 / gamma
            table = np.array(
                [((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]
            ).astype("uint8")
            return cv2.LUT(src=img, lut=table)
        else:
            return img

    def process_wrapper(self, **kwargs):
        """
        Image transformations:
        Performs various linear transformations on the image
        Real time : True

        Keyword Arguments (in parentheses, argument name):
            * Activate tool (enabled): Toggle whether or not tool is active
            * Select transformation (method):
            * Apply smart transformation if (apply_case):
            * Alpha/Gamma (alpha_gamma): Alpha value for linear transformation, gamma for gamma correction
            * Beta (brightness) (beta):
            * Target brightness (target_brightness):
            * Limit brightness fixing (max_delta_for_brightness):
            * Show over an under exposed parts (show_over_under):
            * Brightness calculation mode (brg_calc):
            * Overlay text on top of images (text_overlay): Draw description text on top of images
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            self.data_dict = {}
            img = self.wrapper.current_image
            if self.get_value_of("enabled") == 1:
                method = self.get_value_of("method")
                brg_calc = self.get_value_of("brg_calc")
                br_dict = {}
                if method == "alpha_beta":
                    alpha = self.get_value_of("alpha_gamma") / 100
                    beta = self.get_value_of("beta")
                    self.result = cv2.convertScaleAbs(src=img, alpha=alpha, beta=beta)
                elif method == "gamma":
                    self.result = self.apply_gamma(
                        img=img, gamma=self.get_value_of("alpha_gamma") / 100
                    )
                elif method in [
                    "smart_target_brightness",
                    "alpha_beta_target",
                    "gamma_target",
                ]:
                    # First get the source brightness
                    target_brightness = self.get_value_of("target_brightness")
                    if brg_calc != "none":
                        avg_src, _ = wrapper.avg_brightness_contrast(
                            img=img, mode=brg_calc
                        )
                    else:
                        logger.error("Please select brightness calculation method")
                        res = False
                        return

                    delta_b = target_brightness - avg_src
                    max_delta = self.get_value_of("max_delta_for_brightness")
                    if delta_b > 0:
                        target_brightness = min(avg_src + max_delta, target_brightness)
                    else:
                        target_brightness = max(avg_src - max_delta, target_brightness)
                    apply_case = self.get_value_of("apply_case")
                    if (
                        (avg_src > target_brightness)
                        and (apply_case in ["always", "if_over"])
                    ) or (
                        (avg_src < target_brightness)
                        and (apply_case in ["always", "if_under"])
                    ):
                        if (method == "gamma_target") or (
                            (method == "smart_target_brightness")
                            and (avg_src > target_brightness)
                        ):
                            self.result = self.apply_gamma(
                                img=img, gamma=target_brightness / avg_src
                            )
                        elif (method == "alpha_beta_target") or (
                            (method == "smart_target_brightness")
                            and (avg_src < target_brightness)
                        ):
                            beta = (target_brightness - avg_src) / 2
                            alpha = (target_brightness + avg_src) / (2 * avg_src)
                            self.result = cv2.convertScaleAbs(
                                src=img, alpha=alpha, beta=beta
                            )
                        else:
                            self.result = img
                    else:
                        self.result = img

                if brg_calc != "none":
                    bs, gs, rs = cv2.split(img)
                    br, gr, rr = cv2.split(self.result)
                    if brg_calc == "std":
                        s = rs * 0.2126 + gs * 0.7152 + bs * 0.0722
                        r = rr * 0.2126 + gr * 0.7152 + br * 0.0722
                    elif brg_calc == "p1":
                        s = rs * 0.299 + gs * 0.587 + bs * 0.114
                        r = rr * 0.299 + gr * 0.587 + br * 0.114
                    elif brg_calc == "p2":
                        s = np.sqrt(
                            0.241 * np.power(rs.astype(np.float), 2)
                            + 0.691 * np.power(gs.astype(np.float), 2)
                            + 0.068 * np.power(bs.astype(np.float), 2)
                        )
                        r = np.sqrt(
                            0.241 * np.power(rr.astype(np.float), 2)
                            + 0.691 * np.power(gr.astype(np.float), 2)
                            + 0.068 * np.power(br.astype(np.float), 2)
                        )
                    else:
                        r = None
                        s = None

                    s_tuple = cv2.meanStdDev(s.reshape(s.shape[1] * s.shape[0]))
                    r_tuple = cv2.meanStdDev(r.reshape(s.shape[1] * r.shape[0]))
                    br_dict = dict(
                        **br_dict,
                        **dict(
                            source_raw=(
                                f"{s_tuple[0][0][0]:.2f}",
                                f"{s_tuple[1][0][0]:.2f}",
                                f"{round(s.min())}/{round(s.max())}",
                            ),
                            result=(
                                f"{r_tuple[0][0][0]:.2f}",
                                f"{r_tuple[1][0][0]:.2f}",
                                f"{round(r.min())}/{round(r.max())}",
                            ),
                        ),
                    )
                    self.add_value("raw_brightness", s_tuple[0][0][0], True)
                    self.add_value("raw_contrast", s_tuple[1][0][0], True)
                    self.add_value("raw_brightness_min_max", (s.min(), s.max()), True)
                    self.add_value("mod_brightness", r_tuple[0][0][0], True)
                    self.add_value("mod_contrast", r_tuple[1][0][0], True)
                    self.add_value("mod_brightness_min_max", (r.min(), r.max()), True)
                else:
                    br_dict = None

                if self.get_value_of("show_over_under") == 1:
                    mask_over = cv2.inRange(self.result, (255, 255, 255), (255, 255, 255))
                    mask_under = cv2.inRange(self.result, (0, 0, 0), (0, 0, 0))
                    self.result[mask_over > 0] = C_FUCHSIA
                    self.result[mask_under > 0] = C_ORANGE

                rois = self.get_ipt_roi(
                    wrapper=wrapper,
                    roi_names=self.get_value_of("roi_names").replace(" ", "").split(","),
                    selection_mode=self.get_value_of("roi_selection_mode"),
                )
                if len(rois) > 0:
                    self.result = cv2.bitwise_or(
                        wrapper.delete_rois(wrapper.current_image, rois),
                        wrapper.keep_rois(self.result, rois),
                    )

                if (self.get_value_of("text_overlay") == 1) and (br_dict is not None):
                    wrapper.store_image(
                        self.result,
                        method,
                        text_overlay="\n".join(
                            [f'{k.replace("_", " ")}: {v}' for k, v in br_dict.items()]
                        ),
                    )
                else:
                    self.wrapper.store_image(self.result, method)

                res = True
            else:
                wrapper.store_image(img, "source", text_overlay=False)
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
        return "Image transformations"

    @property
    def real_time(self):
        return True

    @property
    def result_name(self):
        return "image"

    @property
    def output_kind(self):
        return "image"

    @property
    def use_case(self):
        return [
            ToolFamily.PRE_PROCESSING,
            ToolFamily.EXPOSURE_FIXING,
        ]

    @property
    def description(self):
        return "Performs various transformations on the image"
