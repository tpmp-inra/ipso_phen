import cv2
import os
import logging
import subprocess
import platform

from ipso_phen.ipapi.base.ipt_abstract import IptBase
from ipso_phen.ipapi.tools.folders import ipso_folders
from ipso_phen.ipapi.base import ip_common as ipc

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))


class IptIlastikInference(IptBase):
    def build_params(self):
        self.add_enabled_checkbox()
        self.add_text_input(
            name="ilastik_path",
            desc="Path to Ilastik folder",
            default_value="",
        )
        self.add_text_input(
            name="ilastik_model",
            desc="Ilastik model name",
            default_value="",
            hint="Full path to an Ilastik project",
        )
        self.add_checkbox(
            name="abort_if_missing",
            desc="Raise error if mask is not in cache",
            default_value=0,
        )

        self.add_separator(name="sep1")
        self.add_label(desc="Source")
        self.add_file_naming(global_prefix="src_")

        self.add_separator(name="sep2")
        self.add_label(desc="Destination")
        self.add_file_naming(global_prefix="dst_")
        self.add_checkbox(
            name="overwrite",
            desc="Overwrite existing mask",
            default_value=0,
        )

    def process_wrapper(self, **kwargs):
        """
        Ilastik inference:
        'Use an Ilastik project to generate a mask for the current image or an image loaded from harddrive
        Real time: False

        Keyword Arguments (in parentheses, argument name):
            * Activate tool (enabled): Toggle whether or not tool is active
            * Path to Ilastik folder (ilastik_path):
            * Path to Ilastik project (project_path): Full path to an Ilastik project
            * Image output format (src_output_format):
            * Subfolders (src_subfolders): Subfolder names separated byt ","
            * Output naming convention (src_output_name):
            * Prefix (src_prefix): Use text as prefix
            * Suffix (src_suffix): Use text as suffix
            * Replace unsafe caracters (src_make_safe_name): Will replace *"/\[]:;|=,<> with "_"
            * Image output format (dst_output_format):
            * Subfolders (dst_subfolders): Subfolder names separated byt ","
            * Output naming convention (dst_output_name):
            * Prefix (dst_prefix): Use text as prefix
            * Suffix (dst_suffix): Use text as suffix
            * Replace unsafe caracters (dst_make_safe_name): Will replace *"/\[]:;|=,<> with "_"
            * Overwrite existing mask (overwrite):
        """

        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            if self.get_value_of("enabled") == 1:
                dst_path = self.build_path(file_prefix="dst_")
                if os.path.isfile(dst_path) and self.get_value_of("overwrite") == 0:
                    logger.info("Retrived already inferred mask")
                elif self.get_value_of("abort_if_missing") == 1:
                    logger.error("Missing cached mask, abort")
                    return
                else:
                    subprocess.run(
                        [
                            os.path.join(
                                self.get_value_of("ilastik_path"),
                                f"run-ilastik.{'bat' if platform.system() == 'Windows' else 'sh'}",
                            ),
                            "--headless",
                            f'--project={os.path.join(ipso_folders.get_path("ilastik_models"), self.get_value_of("ilastik_model"))}',
                            f'--output_format={self.get_value_of("dst_output_format")}',
                            "--export_source=simple segmentation",
                            f"--output_filename_format={self.build_path(file_prefix='dst_')}",
                            "--pipeline_result_drange=(1.0,2.0)",
                            "--export_drange=(0,255)",
                            self.build_path(file_prefix="src_"),
                        ]
                    )

                mask = cv2.imread(filename=dst_path)
                if len(mask.shape) == 3 and mask.shape[2] == 3:
                    _, _, mask = cv2.split(cv2.cvtColor(mask, cv2.COLOR_BGR2HSV))
                mask[mask != 0] = 255
                self.result = mask
                res = True

            else:
                wrapper.store_image(wrapper.current_image, "current_image")
                res = True
        except Exception as e:
            res = False
            logger.error(f"Ilastik inference FAILED, exception: {repr(e)}")
        else:
            pass
        finally:
            return res

    @property
    def name(self):
        return "Ilastik inference"

    @property
    def package(self):
        return "TPMP"

    @property
    def is_wip(self):
        return False

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
        return ["Threshold"]

    @property
    def description(self):
        return """'Use an Ilastik project to generate a mask for the current image or an image loaded from harddrive"""

    @property
    def skip_tests(self):
        return [ipc.TEST_IMG_IN_MSK_OUT]
