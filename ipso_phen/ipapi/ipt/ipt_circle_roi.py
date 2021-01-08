import cv2

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ip_common import resize_image
from ipso_phen.ipapi.base.ipt_abstract import IptBase
from ipso_phen.ipapi.tools.regions import CircleRegion, EmptyRegion
import ipso_phen.ipapi.base.ip_common as ipc


class IptCircleRoi(IptBase):
    def build_params(self):
        self.add_roi_settings(default_name="unnamed_roi", default_type="keep")
        self.add_spin_box(
            name="cx",
            desc="Center x coordinate",
            default_value=0,
            minimum=-10000,
            maximum=10000,
        )
        self.add_spin_box(
            name="cy",
            desc="Center y coordinate",
            default_value=0,
            minimum=-10000,
            maximum=10000,
        )
        self.add_spin_box(
            name="radius", desc="Radius", default_value=0, minimum=-10000, maximum=10000
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

                self.set_value_of(key="cx", value=r[0] + r[2] // 2, update_widgets=True)
                self.set_value_of(key="cy", value=r[1] + r[2] // 2, update_widgets=True)
                self.set_value_of(key="radius", value=r[2] // 2, update_widgets=True)

                res = True
            else:
                res = False
        except Exception as e:
            logger.error(f'Failed to process {self. name}: "{repr(e)}"')
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
        Circle ROI:
        Create circle ROIs
        Real time: True

        Keyword Arguments (in parentheses, argument name):
            * ROI name (roi_name):
            * Select action linked to ROI (roi_type): no clue
            * Target IPT (tool_target): no clue
            * Center x coordinate (cx):
            * Center y coordinate (cy):
            * Radius (radius):
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
            logger.error(f'Failed : "{repr(e)}"')
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
        cx = self.get_value_of("cx")
        cy = self.get_value_of("cy")
        radius = self.get_value_of("radius")

        if radius == 0:
            return EmptyRegion()

        return CircleRegion(
            cx=cx,
            cy=cy,
            radius=radius,
            name=roi_name,
            tag=roi_type,
            target=tool_target,
        )

    @property
    def name(self):
        return "Circle ROI"

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
        return "Create circle ROIs"
