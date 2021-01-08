import cv2

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ipt_abstract import IptBase


class IptRotate(IptBase):
    def build_params(self):
        self.add_enabled_checkbox()
        self.add_combobox(
            name="rotate_angle",
            desc="Rotation angle",
            default_value="a0",
            values=dict(a0="0°", a90="90°", a180="180°", a270="270°"),
            hint="Select the angle to rotate the image",
        )

    def process_wrapper(self, **kwargs):
        """
        Rotate:
        Rotates an image according to selected angle
        Real time: True

        Keyword Arguments (in parentheses, argument name):
            * Activate tool (enabled): Toggle whether or not tool is active
            * Rotation angle (rotate_angle): Select the angle to rotate the image
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            if self.get_value_of("enabled") == 1:
                img = wrapper.current_image

                # Get the value of the combo box
                rotation_angle = self.get_value_of("rotate_angle")

                # Apply transformation
                root_file_name = wrapper.file_handler.file_name_no_ext
                if rotation_angle == "a90":
                    self.result = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
                    image_name = f"{root_file_name}_r90"
                elif rotation_angle == "a180":
                    self.result = cv2.rotate(img, cv2.ROTATE_180)
                    image_name = f"{root_file_name}_r180"
                elif rotation_angle == "a270":
                    self.result = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
                    image_name = f"{root_file_name}_r270"
                else:
                    self.result = img
                    image_name = f"{root_file_name}_r0"

                # Store the image
                self.wrapper.store_image(self.result, image_name)
                res = True
            else:
                wrapper.store_image(wrapper.current_image, "current_image")
                res = True
        except Exception as e:
            res = False
            wrapper.error_holder.add_error(
                new_error_text=f'Failed to process {self. name}: "{repr(e)}"',
                new_error_level=35,
                target_logger=logger,
            )
        else:
            pass
        finally:
            return res

    @property
    def name(self):
        return "Rotate"

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
        return ["Exposure fixing", "Pre processing", "Visualization"]

    @property
    def description(self):
        return "Rotates an image according to selected angle"
