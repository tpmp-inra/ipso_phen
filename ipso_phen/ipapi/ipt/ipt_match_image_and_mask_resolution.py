from ipso_phen.ipapi.base.ipt_abstract import IptBase


import os
import logging

import ipso_phen.ipapi.base.ip_common as ipc

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))


class IptMatchImageAndMaskResolution(IptBase):
    def build_params(self):
        self.add_enabled_checkbox()
        self.add_combobox(
            name="match_to",
            desc="Match resolution to",
            default_value="mask",
            values={
                "mask": "Mask",
                "image": "Image",
            },
        )

    def process_wrapper(self, **kwargs):
        """
        Match image and mask resolution:
        'Matches mask and current image resolution
        Real time: True

        Keyword Arguments (in parentheses, argument name):
            * Activate tool (enabled): Toggle whether or not tool is active
            * Match resolution to (match_to):"""

        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            if self.get_value_of("enabled") == 1:
                img = wrapper.current_image
                mask = self.get_mask()
                if mask is None:
                    logger.error(
                        "Failure Match image and mask resolution: mask must be initialized"
                    )
                    return
                match_to = self.get_value_of("match_to")

                if match_to == "mask":
                    wrapper.current_image = ipc.resize_image(
                        src_img=img,
                        width=mask.shape[1],
                        height=mask.shape[0],
                        keep_aspect_ratio=False,
                    )
                    self.result = wrapper.current_image
                elif match_to == "image":
                    wrapper.mask = ipc.resize_image(
                        src_img=mask,
                        width=img.shape[1],
                        height=img.shape[0],
                        keep_aspect_ratio=False,
                        output_as_bgr=False,
                    )
                    wrapper.mask[wrapper.mask != 0] = 255
                    self.result = wrapper.mask

                self.demo_image = wrapper.build_mosaic(
                    shape=(
                        wrapper.current_image.shape[0] * 2,
                        wrapper.current_image.shape[1],
                        wrapper.current_image.shape[2],
                    ),
                    image_names=[[wrapper.current_image], [wrapper.mask]],
                )

                # Write your code here
                wrapper.store_image(img, "current_image")
                res = True
            else:
                wrapper.store_image(wrapper.current_image, "current_image")
                res = True
        except Exception as e:
            res = False
            logger.error(f"Match image and mask resolution FAILED, exception: {repr(e)}")
        else:
            pass
        finally:
            return res

    @property
    def name(self):
        return "Match image and mask resolution"

    @property
    def package(self):
        return "TPMP"

    @property
    def is_wip(self):
        return False

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
        return ["Mask cleanup"]

    @property
    def description(self):
        return """'Matches mask and current image resolution"""

    @property
    def output_type(self):
        return ipc.IO_MASK if self.get_value_of("match_to") == "image" else ipc.IO_IMAGE
