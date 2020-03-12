from ip_base.ipt_abstract import IptBase


class IptDummyThreshold(IptBase):
    def build_params(self):
        self.add_enabled_checkbox()

    def process_wrapper(self, **kwargs):
        """
            Dummy threshold (WIP):
            Dummy threshold.

                    Pass through threshold, expects binary mask as entry
            Real time: True

            Keyword Arguments (in parentheses, argument name):
                * Activate tool (enabled): Toggle whether or not tool is active
        """

        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            if self.get_value_of("enabled") == 1:
                img = wrapper.current_image
                if len(img.shape) == 2 or (len(img.shape) == 3 and img.shape[2] == 1):
                    self.result = img
                else:
                    self.result = wrapper.get_channel(src_img=img)

                res = True
                wrapper.store_image(img, "dummy_mask")
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
        return "Dummy threshold (WIP)"

    @property
    def package(self):
        return "TPMP"

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
        return ["Threshold"]

    @property
    def description(self):
        return """Dummy threshold.
        Pass through threshold, expects binary mask as entry"""
