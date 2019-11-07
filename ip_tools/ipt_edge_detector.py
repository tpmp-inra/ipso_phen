import cv2
from skimage.feature import canny
from skimage.filters import sobel, sobel_h, sobel_v, roberts, prewitt

import ip_base.ip_common as ipc
from ip_base.ipt_abstract import IptBase


class IptEdgeDetector(IptBase):
    def build_params(self):
        self.add_checkbox(
            name="enabled",
            desc="Activate tool",
            default_value=1,
            hint="Toggle whether or not tool is active",
        )
        self.add_source_selector(default_value="source")
        self.add_channel_selector(default_value="l")
        self.add_edge_detector()
        self.add_text_overlay()

    def process_wrapper(self, **kwargs):
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        operator_ = self.get_value_of("operator")
        canny_sigma = self.get_value_of("canny_sigma")
        canny_first = self.get_value_of("canny_first")
        canny_second = self.get_value_of("canny_second")
        channel = self.get_value_of("channel")
        kernel_size = self.get_value_of("kernel_size")
        threshold = self.get_value_of("threshold")
        text_overlay = self.get_value_of("text_overlay") == 1
        res = False
        try:
            src_img = self.extract_source_from_args()
            if self.get_value_of("enabled") == 1:
                c = wrapper.get_channel(src_img, channel)
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
                if operator_ in [
                    "laplacian",
                    "sobel",
                    "sobel_v",
                    "sobel_h",
                    "roberts",
                    "prewitt",
                ] and self.get_value_of("apply_threshold", default_value=1):
                    edges[edges < threshold] = 0
                    edges[edges >= threshold] = 255
                self.result = edges

                img_name = f"edges_{self.input_params_as_str()}"
                if text_overlay:
                    wrapper.store_image(
                        self.result,
                        img_name,
                        text_overlay=self.input_params_as_str(
                            exclude_defaults=False, excluded_params=("progress_callback",)
                        ).replace(", ", "\n"),
                    )
                else:
                    wrapper.store_image(self.result, img_name, text_overlay=text_overlay)
            else:
                wrapper.store_image(src_img, "source")

            res = True
        except Exception as e:
            res = False
            wrapper.error_holder.add_error(f'Edge detector FAILED, exception: "{repr(e)}"')
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
        return [ipc.TOOL_GROUP_VISUALIZATION_STR, ipc.TOOL_GROUP_ANCILLARY_STR]

    @property
    def description(self):
        return (
            "Performs edge detection with various common operators.\nMostly used by other tools."
        )
