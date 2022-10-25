import numpy as np
from skimage.filters import threshold_sauvola

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ipt_abstract import IptBase
from ipso_phen.ipapi.base.ip_common import ToolFamily


class IptSauvola(IptBase):
    def build_params(self):
        self.add_channel_selector(default_value="l")
        self.add_checkbox(
            name="invert_mask",
            desc="Invert mask",
            default_value=0,
            hint="Invert result",
        )
        self.add_slider(
            name="window_size",
            desc="Window size",
            default_value=25,
            minimum=3,
            maximum=100,
        )
        self.add_slider(
            name="k",
            desc="k threshold formula",
            default_value=20,
            minimum=0,
            maximum=100,
        )
        self.add_morphology_operator()
        self.add_text_overlay(0)

    def process_wrapper(self, **kwargs):
        """
        Sauvola binarization: From skimage - Applies Sauvola local threshold to an array. Sauvola is a modification of Niblack technique.

        In the original method a threshold T is calculated for every pixel in the image using the following formula:

        T = m(x,y) * (1 + k * ((s(x,y) / R) - 1))
        where m(x,y) and s(x,y) are the mean and standard deviation of pixel (x,y)
        neighborhood defined by a rectangular window with size w times w centered around the pixel.
        k is a configurable parameter that weights the effect of standard deviation. R is the maximum standard deviation
        of a greyscale image.

        Real time : True

        Keyword Arguments (in parentheses, argument name):
            * Channel (channel):
            * Invert mask (invert_mask): Invert result
            * Window size (window_size):
            * k threshold formula (k):
            * Overlay text on top of images (text_overlay): Draw description text on top of images
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        window_size = self.get_value_of("window_size")
        k = self.get_value_of("k") / 100
        channel = self.get_value_of("channel")
        invert_mask = self.get_value_of("invert_mask") == 1
        text_overlay = self.get_value_of("text_overlay") == 1

        if window_size % 2 == 0:
            window_size += 1

        res = False
        try:
            img = self.wrapper.current_image
            c = wrapper.get_channel(img, channel)
            thresh_sauvola = threshold_sauvola(c, window_size=window_size, k=k)
            binary_sauvola = (c > thresh_sauvola).astype(np.uint8)
            binary_sauvola[binary_sauvola != 0] = 255
            if invert_mask:
                binary_sauvola = 255 - binary_sauvola

            self.result = self.apply_morphology_from_params(binary_sauvola)
            wrapper.store_image(
                self.result,
                f"sauvola_binarization_{self.input_params_as_str(exclude_defaults=True)}",
                text_overlay=text_overlay,
            )
        except Exception as e:
            res = False
            wrapper.error_holder.add_error(
                new_error_text=f'Failed to process {self. name}: "{repr(e)}"',
                new_error_level=35,
                target_logger=logger,
            )
        else:
            res = True
        finally:
            return res

    @property
    def name(self):
        return "Sauvola binarization"

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
        return [ToolFamily.THRESHOLD]

    @property
    def description(self):
        return (
            "Sauvola binarization: From skimage - Applies Sauvola local threshold to an array.\n"
            + "Sauvola is a modification of Niblack technique."
            + "In the original method a threshold T is calculated for every pixel in the image using the following formula:"
            + "T = m(x,y) * (1 + k * ((s(x,y) / R) - 1))"
            + "where m(x,y) and s(x,y) are the mean and standard deviation of pixel (x,y)"
            + "neighborhood defined by a rectangular window with size w times w centered around the pixel."
            + "k is a configurable parameter that weights the effect of standard deviation. R is the maximum standard deviation"
            + "of a greyscale image."
        )
