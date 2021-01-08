import os
import cv2

from ipso_phen.ipapi.base.ipt_abstract import IptBase
from ipso_phen.ipapi.base import ip_common as ipc

import logging

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))


class IptCleanMaskBackward(IptBase):
    def build_params(self):
        self.add_enabled_checkbox()
        self.add_text_input(
            name="mask_search_path",
            desc="Target folder",
            default_value="",
            hint="Can be overridden at process call",
        )

    def process_wrapper(self, **kwargs):
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            if self.get_value_of("enabled") == 1:
                # Retrieve current image and mask
                img = wrapper.current_image
                mask = self.get_mask()
                if mask is None:
                    logger.error(
                        f"FAIL {self.name}: mask must be initialized",
                    )
                    return

                # Retrieve previous mask from database
                last_mask = None
                msk_path = os.path.join(
                    self.get_value_of("mask_search_path"), "masks", ""
                )
                if not os.path.isdir(msk_path):
                    logger.error(f"Warning {self.name}: no previous mask")
                    self.result = mask
                    res = True
                    return
                ret = wrapper.target_database.query(
                    command="SELECT",
                    columns="FilePath, date_time",
                    additional="ORDER BY date_time ASC",
                    experiment=wrapper.experiment,
                    plant=wrapper.plant,
                    camera=wrapper.camera,
                )
                for i, record in enumerate(ret):
                    if record[1] == wrapper.date_time:
                        break
                else:
                    i = -1
                if 0 < i < len(ret):
                    last_mask_path = os.path.join(
                        self.get_value_of("mask_search_path"),
                        "masks",
                        os.path.basename(ret[i - 1][0]),
                    )
                    if os.path.isfile(last_mask_path):
                        try:
                            last_mask = cv2.imread(last_mask_path)
                        except Exception as e:
                            logger.error(
                                f"{self.name}, unable to read previous mask, exception: {repr(e)}"
                            )
                            return
                elif i == 0:
                    logger.error(f"Info {self.name}: first image in series")
                    res = True
                    return
                elif i >= len(ret):
                    logger.error(f"FAIL {self.name}: unknown image")
                    return

                wrapper.store_image(image=last_mask, text="previous_mask")

                # Write your code here
                wrapper.store_image(img, "current_image")
                res = True
            else:
                wrapper.store_image(wrapper.current_image, "current_image")
                res = True
        except Exception as e:
            res = False
            logger.error(f'Failed to process {self. name}: "{repr(e)}"')
        else:
            pass
        finally:
            return res

    @property
    def name(self):
        return "Clean mask with previous mask"

    @property
    def is_wip(self):
        return True

    @property
    def package(self):
        return "TPMP"

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
        return [ipc.ToolFamily.MASK_CLEANUP]

    @property
    def needs_previous_mask(self):
        return True

    @property
    def description(self):
        return "Cleans a mask using the previous mask in a time series"
