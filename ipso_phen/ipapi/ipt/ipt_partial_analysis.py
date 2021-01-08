import numpy as np
import cv2

from ipso_phen.ipapi.base.ipt_abstract_analyzer import IptBaseAnalyzer
import ipso_phen.ipapi.base.ip_common as ipc


import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))


class IptPartialAnalysis(IptBaseAnalyzer):
    def build_params(self):
        self.add_enabled_checkbox()
        self.add_channel_selector(default_value="h")
        self.add_checkbox(name="invert", desc="Invert mask", default_value=0)
        self.add_binary_threshold()
        self.add_separator(name="sep1")
        self.add_text_input(
            name="channels_to_analyse",
            desc="Channels to analyze",
            default_value="",
            hint=f"""Select channels to be analyzed, possible values are:
            {', '.join([channel_info[1] for channel_info in ipc.create_channel_generator(include_msp=True)])}
            channels must be separated by ','""",
        )
        self.add_checkbox(
            name="ratio",
            desc="Ratio between parts of the mask",
            default_value=1,
        )
        self.add_text_input(
            name="csv_prefix",
            desc="CSV prefix",
            default_value="partial",
        )

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
                    logger.error("Failure Partial Analysis: mask must be initialized")
                    return

                partial_source = wrapper.draw_image(
                    src_image=wrapper.current_image,
                    src_mask=mask,
                    foreground="source",
                    background=ipc.C_BLACK,
                )
                wrapper.store_image(partial_source, "partial_source")

                partial_mask = self.apply_binary_threshold(
                    wrapper=wrapper,
                    img=partial_source,
                    channel=self.get_value_of("channel"),
                )
                wrapper.store_image(partial_mask, "partial_mask")

                self.demo_image = wrapper.draw_image(
                    src_image=partial_source,
                    src_mask=partial_mask,
                    foreground="false_colour",
                    background="source",
                    # contour_thickness=6,
                )

                prefix = self.get_value_of("csv_prefix")

                # Ratio
                if self.get_value_of("ratio") == 1:
                    src_area = np.count_nonzero(mask)
                    partial_area = np.count_nonzero(partial_mask)
                    if src_area != 0:
                        ratio_area = partial_area / src_area
                    else:
                        ratio_area = ""
                    self.add_value(
                        f"{prefix}_ratio",
                        ratio_area,
                        True,
                    )

                # color
                for c in ipc.create_channel_generator(
                    self.get_value_of("channels_to_analyse").replace(" ", "").split(",")
                ):
                    channel = wrapper.get_channel(
                        src_img=wrapper.current_image,
                        channel=c[1],
                    )
                    channel = cv2.bitwise_and(channel, channel, mask=partial_mask)
                    tmp_tuple = cv2.meanStdDev(
                        src=channel.flatten(), mask=partial_mask.flatten()
                    )
                    seed_ = f"{c[0]}_{c[1]}"
                    self.add_value(
                        key=f"{prefix}_{seed_}_std_dev",
                        value=tmp_tuple[1][0][0],
                        force_add=True,
                    )
                    self.add_value(
                        key=f"{prefix}_{seed_}_mean",
                        value=tmp_tuple[0][0][0],
                        force_add=True,
                    )

                # Write your code here
                wrapper.store_image(self.demo_image, "current_image")
                res = True
            else:
                wrapper.store_image(wrapper.current_image, "current_image")
                res = True
        except Exception as e:
            res = False
            logger.error(f"Partial Analysis FAILED, exception: {repr(e)}")
        else:
            pass
        finally:
            return res

    @property
    def name(self):
        return "Partial Analysis"

    @property
    def is_wip(self):
        return True

    @property
    def package(self):
        return "TPMP"

    @property
    def real_time(self):
        return True

    @property
    def result_name(self):
        return "mask"

    @property
    def output_kind(self):
        return "mask"

    @property
    def use_case(self):
        return ["Feature extraction"]

    @property
    def description(self):
        return """'Analyse a part of the mask"""
