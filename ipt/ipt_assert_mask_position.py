import numpy as np

import logging

logger = logging.getLogger(__name__)

from base.ipt_abstract import IptBase
import base.ip_common as ipc


class IptAssertMaskPosition(IptBase):
    def __init__(self, wrapper=None, **kwargs):
        super().__init__(wrapper=wrapper, **kwargs)
        self._create_test_mask = False

    def build_params(self):
        self.add_enabled_checkbox()
        self.add_roi_selector()

    def process_wrapper(self, **kwargs):
        """
        Assert mask position:
        Check that the mask intersects with a named ROI
        Real time: True

        Keyword Arguments (in parentheses, argument name):
            * Activate tool (enabled): Toggle whether or not tool is active
            * Name of ROI to be used (roi_names): Operation will only be applied inside of ROI
            * ROI selection mode (roi_selection_mode):
        """

        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            if self.get_value_of("enabled") == 1:
                mask = self.get_mask()
                if mask is None and self._create_test_mask:
                    mask = wrapper.get_mask(
                        src_img=wrapper.current_image, channel="h", min_t=10, max_t=100,
                    )
                elif mask is None:
                    wrapper.error_holder.add_error(
                        f"FAIL {self.name}: mask must be initialized", target_logger=logger
                    )
                    return

                # Retrieve ROIs
                enforcers = self.get_ipt_roi(
                    wrapper=wrapper,
                    roi_names=self.get_value_of("roi_names").replace(" ", "").split(","),
                    selection_mode=self.get_value_of("roi_selection_mode"),
                )

                # Check
                res = True
                img = wrapper.retrieve_stored_image(img_name="exp_fixed_pseudo_on_bw")
                for i, enforcer in enumerate(enforcers):
                    intersection = enforcer.keep(mask)
                    partial_ok = np.count_nonzero(intersection) > 0
                    res = partial_ok and res
                    if partial_ok:
                        img = enforcer.draw_to(dst_img=img, line_width=2, color=ipc.C_GREEN)
                    else:
                        img = enforcer.draw_to(dst_img=img, line_width=2, color=ipc.C_RED)
                        wrapper.error_holder.add_error(
                            new_error_text=f'{self. name}: check failed for ROI "{enforcer.name}""',
                            new_error_level=2,
                            target_logger=logger,
                        )
                self.demo_image = img
                wrapper.store_image(image=img, text=f"enforcers")

                self.result = res
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

    def apply_test_values_overrides(self, use_cases: tuple = ()):
        if ipc.TOOL_GROUP_ASSERT_STR in use_cases:
            self._create_test_mask = True

    @property
    def name(self):
        return "Assert mask position"

    @property
    def package(self):
        return "TPMP"

    @property
    def real_time(self):
        return True

    @property
    def result_name(self):
        return "None"

    @property
    def output_kind(self):
        return "None"

    @property
    def use_case(self):
        return [ipc.TOOL_GROUP_ASSERT_STR]

    @property
    def description(self):
        return "Check that the mask intersects with a named ROI"
