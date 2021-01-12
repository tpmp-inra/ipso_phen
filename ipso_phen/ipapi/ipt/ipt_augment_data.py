import os
import cv2
import numpy as np

import logging

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ipt_abstract_analyzer import IptBaseAnalyzer
from ipso_phen.ipapi.tools.common_functions import force_directories
from ipso_phen.ipapi.base.ip_common import ToolFamily


class IptAugmentData(IptBaseAnalyzer):
    def build_params(self):
        self.add_checkbox(
            name="add_sub_folder",
            desc="Put image in subfolder with experiment as its name",
            default_value=0,
        )
        self.add_combobox(
            name="output_format",
            desc="Image output format",
            default_value="source",
            values=dict(source="As source image", jpg="JPEG", png="PNG", tiff="TIFF"),
        )
        self.add_checkbox(
            name="test_only", desc="Test only, do not actually copy", default_value=1
        )
        self.add_separator(name="s1")
        self.add_checkbox(name="original", desc="Source image", default_value=1)
        self.add_checkbox(name="r90", desc="Rotate 90 degres", default_value=0)
        self.add_checkbox(name="r180", desc="Rotate 180 degres", default_value=0)
        self.add_checkbox(name="r270", desc="Rotate 270 degres", default_value=0)
        self.add_checkbox(name="flip_h", desc="flip horizontally", default_value=0)
        self.add_checkbox(name="flip_v", desc="flip vertically", default_value=0)
        self.add_separator(name="s2")
        self.add_text_input(
            name="gamma_values",
            desc="Gamma values (same syntax as grid search)",
            default_value="1",
        )

    def save_image(self, image, gamma, path):
        test_only = self.get_value_of("test_only") == 1
        if self.get_value_of("add_sub_folder") == 1:
            path = os.path.join(path, self.wrapper.file_handler.experiment, "")
            force_directories(path)

        file_ext = self.get_value_of("output_format")
        if file_ext == "source":
            file_ext = self.wrapper.file_handler.file_ext
        else:
            file_ext = f".{file_ext}"

        if gamma != 1:
            inv_gamma = 1.0 / gamma
            table = np.array(
                [((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]
            ).astype("uint8")
            img = cv2.LUT(src=image, lut=table)
            root_file_name = f"{self.wrapper.file_handler.file_name_no_ext}_{gamma:.2f}"
        else:
            img = image.copy()
            root_file_name = self.wrapper.file_handler.file_name_no_ext

        for is_write, image, text in zip(
            [
                self.get_value_of("original") == 1,
                self.get_value_of("r90") == 1,
                self.get_value_of("r180") == 1,
                self.get_value_of("r270") == 1,
                self.get_value_of("flip_h") == 1,
                self.get_value_of("flip_v") == 1,
            ],
            [
                img.copy(),
                cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE),
                cv2.rotate(img, cv2.ROTATE_180),
                cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE),
                cv2.flip(img, +1),
                cv2.flip(cv2.transpose(img), 0),
            ],
            ["", "_r90", "_r180", "_r270", "_flip_h", "_flip_v"],
        ):
            if is_write:
                new_name = f"{root_file_name}{text}.{file_ext}"
                self.add_value(key=f"img{text}", value=new_name, force_add=True)
                if test_only:
                    self.wrapper.store_image(image, new_name)
                else:
                    cv2.imwrite(filename=os.path.join(path, new_name), img=image)

    def process_wrapper(self, **kwargs):
        """
        Augment Data:
        Copies image to target folder after modifying it
        Can have a ROI as a pre-processor
        Real time : False

        Keyword Arguments (in parentheses, argument name):
            * Target folder (target_folder):
            * Put image in subfolder with experiment as its name (add_sub_folder):
            * Image output format (output_format):
            * Test only, do not actually copy (test_only):
            * Source image (original):
            * Rotate 90 degres (r90):
            * Rotate 180 degres (r180):
            * Rotate 270 degres (r270):
            * flip horizontally (flip_h):
            * flip vertically (flip_v):
            * Gamma values (same syntax as grid search) (gamma_values):
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            self.data_dict = {}
            p = self.find_by_name(name="gamma_values")
            gsl = None if p is None else p.decode_string(p.value)
            src_img = wrapper.current_image
            if self.get_value_of("test_only") == 0:
                try:
                    force_directories(self.output_path)
                except Exception as e:
                    logger.error(f"Unable to create folder: {repr(e)}")
            if not self.output_path:
                logger.error("Failed : Missing folder parameter")
            elif gsl:
                self.add_value(key="source_name", value=wrapper.name, force_add=True)
                for gamma_value in gsl:
                    self.save_image(
                        image=src_img, gamma=float(gamma_value), path=self.output_path
                    )
                res = True
            else:
                self.add_value(key="source_name", value=wrapper.name, force_add=True)
                self.save_image(image=src_img, gamma=1, path=self.output_path)
                res = True
        except Exception as e:
            logger.error(
                f'Failed to process {self. name}: "{repr(e)}"',
            )
            res = False
        else:
            pass
        finally:
            self.result = len(self.data_dict) > 0
            return res

    @property
    def name(self):
        return "Augment data"

    @property
    def real_time(self):
        return False

    @property
    def result_name(self):
        return "none"

    def apply_test_values_overrides(self, use_cases: tuple = ()):
        self.output_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "test",
            "output_files",
            "",
        )

    @property
    def output_kind(self):
        return ""

    @property
    def use_case(self):
        return [ToolFamily.IMAGE_GENERATOR]

    @property
    def description(self):
        return """Copies image to target folder after modifying it
        Can have a ROI as a pre-processor"""
