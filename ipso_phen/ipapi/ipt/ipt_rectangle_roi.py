import cv2

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ip_common import resize_image
from ipso_phen.ipapi.base.ipt_abstract import IptBase
from ipso_phen.ipapi.tools.regions import RectangleRegion, EmptyRegion
import ipso_phen.ipapi.base.ip_common as ipc


class IptRectangleRoi(IptBase):
    def build_params(self):
        self.add_roi_settings(default_name="unnamed_roi", default_type="keep")
        self.add_spin_box(
            name="left", desc="Left", default_value=0, minimum=-10000, maximum=10000
        )
        self.add_spin_box(
            name="width",
            desc="Width",
            default_value=0,
            minimum=-10000,
            maximum=10000,
        )
        self.add_spin_box(
            name="top", desc="Top", default_value=0, minimum=-10000, maximum=10000
        )
        self.add_spin_box(
            name="height", desc="Height", default_value=0, minimum=-10000, maximum=10000
        )
        self.add_text_input(
            name="apply_case",
            desc="Apply to images that match",
            default_value="",
            hint="List of key values pairs separated by |, to use list as value separate with ','",
        )
        self.add_button(
            name="draw_roi",
            desc="Launch ROI draw form",
            index=0,
            hint="Launch OpenCV window to select a ROI",
        )

    def execute(self, param, **kwargs):
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            if param.name == "draw_roi":
                img = wrapper.current_image
                ori_height, ori_width = img.shape[:2]
                factor = ori_width / 800
                img = resize_image(
                    img,
                    width=ori_width // factor,
                    height=ori_height // factor,
                    keep_aspect_ratio=True,
                )
                r = cv2.selectROI(windowName="Draw ROI", img=img)
                cv2.destroyAllWindows()
                r = (
                    int(r[0] * factor),
                    int(r[1] * factor),
                    int(r[2] * factor),
                    int(r[3] * factor),
                )

                self.set_value_of(key="left", value=r[0], update_widgets=True)
                self.set_value_of(key="width", value=r[2], update_widgets=True)
                self.set_value_of(key="top", value=r[1], update_widgets=True)
                self.set_value_of(key="height", value=r[3], update_widgets=True)

                res = True
            else:
                res = False
        except Exception as e:
            wrapper.error_holder.add_error(
                f'Failed to execute: "{repr(e)}"', target_logger=logger
            )
            res = False
        else:
            pass
        finally:
            if res:
                return "process_wrapper"
            else:
                return ""

    def process_wrapper(self, **kwargs):
        """
        Rectangle ROI:
        Create rectangle ROIs
        Real time: True

        Keyword Arguments (in parentheses, argument name):
            * ROI name (roi_name):
            * Select action linked to ROI (roi_type): no clue
            * Target IPT (tool_target): no clue
            * Left (left):
            * Width (width):
            * Top (top):
            * Height (height):
            * Launch ROI draw form (draw_roi): Launch OpenCV window to select a ROI
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            self.result = self.generate_roi()
            if self.result is not None:
                img = self.result.draw_to(
                    dst_img=wrapper.current_image, line_width=wrapper.width // 200
                )
            else:
                img = wrapper.current_image
            wrapper.store_image(image=img, text="image_with_roi")

            res = True
        except Exception as e:
            wrapper.error_holder.add_error(
                new_error_text=f'Failed to process {self. name}: "{repr(e)}"',
                new_error_level=35,
                target_logger=logger,
            )
            res = False
        else:
            pass
        finally:
            return res

    def generate_roi(self, **kwargs):
        roi_shape = self.get_value_of("roi_shape")
        roi_type = self.get_value_of("roi_type")
        roi_name = self.get_value_of("roi_name")
        tool_target = self.get_value_of("tool_target")
        left = self.get_value_of("left")
        width = self.get_value_of("width")
        top = self.get_value_of("top")
        height = self.get_value_of("height")

        if (width == 0) or (height == 0):
            return EmptyRegion()

        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return EmptyRegion()

        if width < 0:
            left = EmptyRegion()
        if height < 0:
            top = EmptyRegion()

        d = {}
        kv = self.get_value_of("apply_case")
        if kv:
            pairs = kv.split("|")
            for pair in pairs:
                k, v = pair.split("=")
                v = v.split(",")
                if k is not None and v is not None:
                    d.update({k: v})

        return RectangleRegion(
            source_width=wrapper.width,
            source_height=wrapper.height,
            left=left,
            width=width,
            top=top,
            height=height,
            name=roi_name,
            tag=roi_type,
            target=tool_target,
            apply_case=d,
        )

    @property
    def name(self):
        return "Rectangle ROI"

    @property
    def package(self):
        return "IPSO Phen"

    @property
    def real_time(self):
        return True

    @property
    def result_name(self):
        return "none"

    @property
    def output_kind(self):
        return "none"

    @property
    def use_case(self):
        return [ipc.ToolFamily.ROI]

    @property
    def description(self):
        return "Create rectangle ROIs"
