import os
import logging

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

import cv2

from ipso_phen.ipapi.base.ipt_abstract_analyzer import IptBaseAnalyzer
from ipso_phen.ipapi.base import ip_common as ipc


class IptImageSlicerDim(IptBaseAnalyzer):
    def build_params(self):
        self.add_enabled_checkbox()
        self.add_checkbox(name="save_image", desc="Save generated image", default_value=0)
        self.add_text_input(name="img_name", desc="Name in csv", default_value="img")
        self.add_file_naming()
        self.add_spin_box(
            name="width",
            desc="width",
            default_value=256,
            minimum=0,
            maximum=10000,
        )
        self.add_spin_box(
            name="height",
            desc="height",
            default_value=256,
            minimum=0,
            maximum=10000,
        )
        self.add_spin_box(
            name="step_x",
            desc="X step",
            default_value=256,
            minimum=0,
            maximum=10000,
        )
        self.add_spin_box(
            name="step_y",
            desc="Y step",
            default_value=256,
            minimum=0,
            maximum=10000,
        )

    def process_wrapper(self, **kwargs):
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            if self.get_value_of("enabled") == 1:
                img = wrapper.current_image
                dbg_img = img.copy()

                slice_width = self.get_value_of(("width"))
                slice_height = self.get_value_of(("height"))

                for left in range(0, wrapper.width, self.get_value_of("step_x")):
                    for top in range(0, wrapper.height, self.get_value_of("step_y")):
                        right = left + slice_width
                        bottom = top + slice_height
                        if right >= wrapper.width or bottom >= wrapper.height:
                            continue
                        slice_ = img[top:bottom, left:right]
                        dbg_img = cv2.rectangle(
                            dbg_img,
                            (left, top),
                            (right, bottom),
                            ipc.C_FUCHSIA,
                            thickness=2,
                        )
                        if self.get_value_of("save_image") != 0:
                            file_name = self.build_path(salt=f"_{left}_{top}")
                            cv2.imwrite(filename=file_name, img=slice_)
                        wrapper.store_image(slice_, f"slice_{left}_{top}")

                self.result = dbg_img
                self.demo_image = dbg_img

                # Write your code here
                wrapper.store_image(img, "current_image")
                res = True
            else:
                wrapper.store_image(wrapper.current_image, "current_image")
                res = True
        except Exception as e:
            res = False
            logger.error(f"Image slicer dim FAILED, exception: {repr(e)}")
        else:
            pass
        finally:
            return res

    @property
    def name(self):
        return "Image slicer dim"

    @property
    def package(self):
        return "Me"

    @property
    def is_wip(self):
        return True

    @property
    def real_time(self):
        return False

    @property
    def result_name(self):
        return "image"

    @property
    def output_kind(self):
        return "image"

    @property
    def use_case(self):
        return ["Image generator"]

    @property
    def description(self):
        return """'Slice image into multiple ones using a target width and height"""
