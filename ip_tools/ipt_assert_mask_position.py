import cv2
import numpy as np

from ip_base.ipt_abstract import IptBase
import ip_base.ip_common as ipc


class IptAssertMaskPosition(IptBase):
    def build_params(self):
        self.add_enabled_checkbox()
        self.add_roi_selector()

    def process_wrapper(self, **kwargs):
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            if self.get_value_of("enabled") == 1:
                mask = self.get_mask()
                if mask is None:
                    wrapper.error_holder.add_error(f"FAIL {self.name}: mask must be initialized")
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
                wrapper.store_image(image=img, text=f"enforcers", force_store=True)

                self.result = None
            else:
                wrapper.store_image(wrapper.current_image, "current_image")
                res = True
        except Exception as e:
            res = False
            wrapper.error_holder.add_error(
                new_error_text=f'Failed to process {self. name}: "{repr(e)}"', new_error_level=3
            )
        else:
            pass
        finally:
            return res

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
        return ["Assert..."]

    @property
    def description(self):
        return "Check that the mask intersects with a named ROI"
