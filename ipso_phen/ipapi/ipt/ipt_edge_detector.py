import cv2
from skimage.feature import canny
from skimage.filters import sobel, sobel_h, sobel_v, roberts, prewitt

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

import ipso_phen.ipapi.base.ip_common as ipc
from ipso_phen.ipapi.base.ipt_abstract import IptBase


class IptEdgeDetector(IptBase):
    def build_params(self):
        self.add_checkbox(
            name="enabled",
            desc="Activate tool",
            default_value=1,
            hint="Toggle whether or not tool is active",
        )
        self.add_combobox(
            name="source_selector",
            desc="Select source",
            default_value="current_image",
            values={"current_image": "Current image", "mask": "Mask"},
            hint="Select which image will be used as source",
        )
        self.add_channel_selector(default_value="l")
        self.add_checkbox(
            name="normalize",
            desc="Normalize channel",
            default_value=0,
            hint="Normalize channel before edge detection",
        )
        self.add_slider(
            name="median_filter_size",
            desc="Median filter size (odd values only)",
            default_value=0,
            minimum=0,
            maximum=51,
        )
        self.add_edge_detector()
        self.add_text_overlay()

    def process_wrapper(self, **kwargs):
        """
        Edge detectors:
        Performs edge detection with various common operators.
        Mostly used by other tools.
        Real time: True

        Keyword Arguments (in parentheses, argument name):
            * Activate tool (enabled): Toggle whether or not tool is active
            * Select source file type (source_file): no clue
            * Channel (channel):
            * Normalize channel (normalize): Normalize channel before edge detection
            * Median filter size (odd values only) (median_filter_size):
            * Select edge detection operator (operator):
            * Canny's sigma for scikit, aperture for OpenCV (canny_sigma): Sigma.
            * Canny's first Threshold (canny_first): First threshold for the hysteresis procedure.
            * Canny's second Threshold (canny_second): Second threshold for the hysteresis procedure.
            * Kernel size (kernel_size):
            * Threshold (threshold): Threshold for kernel based operators
            * Apply threshold (apply_threshold):
            * Overlay text on top of images (text_overlay): Draw description text on top of images
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            operator_ = self.get_value_of("operator")
            canny_sigma = self.get_value_of("canny_sigma")
            canny_first = self.get_value_of("canny_first")
            canny_second = self.get_value_of("canny_second")
            channel = self.get_value_of("channel")
            kernel_size = self.get_value_of("kernel_size")
            threshold = self.get_value_of("threshold")
            text_overlay = self.get_value_of("text_overlay") == 1
            input_kind = self.get_value_of("source_selector")

            if input_kind == "mask":
                src_img = self.get_mask()
            elif input_kind == "current_image":
                src_img = wrapper.current_image
            else:
                src_img = None
                logger.error(f"Unknown source: {input_kind}")
                self.result = None
                return

            if self.get_value_of("enabled") == 1:
                c = wrapper.get_channel(
                    src_img=src_img,
                    channel=channel,
                    normalize=self.get_value_of("normalize") == 1,
                    median_filter_size=self.get_value_of("median_filter_size"),
                )
                if c is None:
                    self.do_channel_failure(channel)
                    return
                # Crop if channel is msp
                ch, cw, *_ = c.shape
                sh, sw, *_ = src_img.shape
                if ((ch != sh) or (cw != sh)) and (
                    self.get_value_of("source_file", "source") == "cropped_source"
                ):
                    c = wrapper.crop_to_keep_roi(c)

                if operator_ == "canny_scik":
                    edges = canny(
                        c,
                        sigma=canny_sigma,
                        low_threshold=canny_first,
                        high_threshold=canny_second,
                    )
                elif operator_ == "canny_opcv":
                    edges = cv2.Canny(
                        c,
                        threshold1=canny_first,
                        threshold2=canny_second,
                        apertureSize=ipc.ensure_odd(i=canny_sigma, min_val=3, max_val=7),
                    )
                elif operator_ == "laplacian":
                    if kernel_size == 1:
                        kernel_size = 0
                    elif (kernel_size > 0) and (kernel_size % 2 == 0):
                        kernel_size += 1
                    if kernel_size >= 3:
                        gauss = cv2.GaussianBlur(c, (kernel_size, kernel_size), 0)
                        wrapper.store_image(
                            gauss,
                            f"filtered_image_{self.input_params_as_str()}",
                            text_overlay=True,
                        )
                        edges = cv2.Laplacian(gauss, cv2.CV_64F)
                    else:
                        edges = cv2.Laplacian(c, cv2.CV_64F)
                elif operator_ == "sobel":
                    edges = sobel(c)
                elif operator_ == "sobel_v":
                    edges = sobel_v(c)
                elif operator_ == "sobel_h":
                    edges = sobel_h(c)
                elif operator_ == "roberts":
                    edges = roberts(c)
                elif operator_ == "prewitt":
                    edges = prewitt(c)
                else:
                    edges = c.copy()

                edges = self.to_uint8(edges)
                if (
                    operator_
                    in [
                        "laplacian",
                        "sobel",
                        "sobel_v",
                        "sobel_h",
                        "roberts",
                        "prewitt",
                    ]
                    and self.get_value_of("apply_threshold", default_value=1)
                ):
                    edges[edges < threshold] = 0
                    edges[edges >= threshold] = 255
                self.result = edges

                img_name = f"edges_{self.input_params_as_str()}"
                if text_overlay:
                    wrapper.store_image(
                        self.result,
                        img_name,
                        text_overlay=self.input_params_as_str(
                            exclude_defaults=False,
                            excluded_params=("progress_callback",),
                        ).replace(", ", "\n"),
                    )
                else:
                    wrapper.store_image(self.result, img_name, text_overlay=text_overlay)
            else:
                wrapper.store_image(src_img, "source")

            self.demo_image = self.result
            res = True
        except Exception as e:
            res = False
            logger.error(f'Failed to process {self. name}: "{repr(e)}"')
        else:
            pass
        finally:
            return res

    @property
    def name(self):
        return "Edge detectors"

    @property
    def real_time(self):
        return self.get_value_of("operator") != "canny_scik"

    @property
    def result_name(self):
        return "raw_edges"

    @property
    def output_kind(self):
        return "data_image"

    @property
    def use_case(self):
        return [
            ipc.ToolFamily.VISUALIZATION,
            ipc.ToolFamily.ANCILLARY,
            ipc.ToolFamily.PRE_PROCESSING,
        ]

    @property
    def description(self):
        return "Performs edge detection with various common operators.\nMostly used by other tools."
