from ipso_phen.ipapi.base.ipt_abstract_analyzer import IptBaseAnalyzer


import os
import logging

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))


class IptAnalyzeRoiData(IptBaseAnalyzer):
    def build_params(self):
        self.add_enabled_checkbox()

        self.add_text_input(
            name="target_roi", desc="Name of ROI to be used", default_value=""
        )
        self.add_roi_shape()

    def process_wrapper(self, **kwargs):
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            if self.get_value_of("enabled") == 1:
                img = wrapper.current_image
                roi = self.get_ipt_roi(
                    wrapper=wrapper,
                    roi_names=[self.get_value_of("target_roi")],
                )[0]
                if self.get_value_of("roi_shape") == "circle":
                    roi = roi.as_circle()
                else:
                    roi = roi.as_rect()

                for k, v in roi.to_dict().items():
                    self.add_value(key=k, value=v, force_add=True)

                # Write your code here
                wrapper.store_image(roi.draw_to(img, 4), "analyzed_roi")
                res = True
            else:
                wrapper.store_image(wrapper.current_image, "current_image")
                res = True
        except Exception as e:
            res = False
            logger.error(f"analyze_roi_data FAILED, exception: {repr(e)}")
        else:
            pass
        finally:
            return res

    @property
    def name(self):
        return "Analyze ROI data"

    @property
    def package(self):
        return "TPMP"

    @property
    def is_wip(self):
        return True

    @property
    def real_time(self):
        return False

    @property
    def result_name(self):
        "dictionary"

    @property
    def output_kind(self):
        "dictionary"

    @property
    def use_case(self):
        return ["Feature extraction"]

    @property
    def description(self):
        return """'Write your tool s description here. it will be used to generate documentation files"""
