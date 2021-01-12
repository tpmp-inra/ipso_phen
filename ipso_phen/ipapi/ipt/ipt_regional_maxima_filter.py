import cv2
from scipy.ndimage import gaussian_filter
from skimage import img_as_float
from skimage.morphology import reconstruction

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ipt_abstract import IptBase
from ipso_phen.ipapi.base.ip_common import ToolFamily


class IptRegionalMaximaFiltering(IptBase):
    def build_params(self):
        self.add_checkbox(
            name="enabled",
            desc="Activate tool",
            default_value=1,
            hint="Toggle whether or not tool is active",
        )
        self.add_source_selector(default_value="source")
        self.add_channel_selector(default_value="l")
        self.add_slider(
            name="brightness_offset",
            desc="Offset for uneven image border",
            default_value=0,
            minimum=0,
            maximum=100,
            hint="Use when image border perimeter has uneven brightness",
        )
        self.add_text_overlay(0)
        self.add_label(name="lbl_disp", desc="Display options:")
        self.add_color_map_selector(name="color_map", default_value="c_2")
        self.add_checkbox(
            name="use_palette",
            desc="use color palette",
            default_value=0,
            hint="Use color palette in postprocessing",
        )
        self.add_checkbox(name="normalize", desc="Normalize channel", default_value=0)
        self.add_checkbox(
            name="real_time",
            desc="Real time",
            default_value=0,
            hint="Set if tool reacts in real time",
        )

    def process_wrapper(self, **kwargs):
        """
        Filtering regional maxima:

        From scikit image - Filtering regional maxima: Perform a morphological reconstruction of an image.

        Morphological reconstruction by dilation is similar to basic morphological dilation: high-intensity values will
        replace nearby low-intensity values. The basic dilation operator, however, uses a structuring element to
        determine how far a value in the input image can spread. In contrast, reconstruction uses two images: a “seed”
        image, which specifies the values that spread, and a “mask” image, which gives the maximum allowed value at
        each pixel. The mask image, like the structuring element, limits the spread of high-intensity values.
        Reconstruction by erosion is simply the inverse: low-intensity values spread from the seed image and are
        limited by the mask image, which represents the minimum allowed value.

        Alternatively, you can think of reconstruction as a way to isolate the connected regions of an image.
        For dilation, reconstruction connects regions marked by local maxima in the seed image: neighboring pixels
        less-than-or-equal-to those seeds are connected to the seeded region.
        Local maxima with values larger than the seed image will get truncated to the seed value.
        Real time : True

        Keyword Arguments (in parentheses, argument name):
            * Select source file type (source_file):
            * Channel (channel):
            * Offset for uneven image border (brightness_offset): Use when image border perimeter has uneven brightness
            * Overlay text on top of images (text_overlay): Draw description text on top of images
            * Activate tool (enabled): Toggle whether or not tool is active
            * Select pseudo color map (color_map):
            * use color palette (use_palette): Use color palette in postprocessing
            * Normalize channel (normalize):
            * Real time (real_time): Set if tool reacts in real time
        """

        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            if self.get_value_of("enabled") == 1:
                brightness_offset = self.get_value_of("brightness_offset") / 100
                channel = self.get_value_of("channel")
                text_overlay = self.get_value_of("text_overlay") == 1
                color_map = self.get_value_of("color_map")
                _, color_map = color_map.split("_")
                normalize = self.get_value_of("normalize") == 1

                img = self.wrapper.current_image
                c = wrapper.get_channel(img, channel)
                if c is None:
                    self.do_channel_failure(channel)
                    return

                image = img_as_float(c)
                image = gaussian_filter(image, 1)

                seed = image - brightness_offset
                seed[1:-1, 1:-1] = image.min()
                mask = image

                dilated = reconstruction(seed, mask, method="dilation")
                dilated = self.to_uint8(dilated, normalize=normalize)
                if self.get_value_of("use_palette") == 1:
                    dilated = cv2.applyColorMap(dilated, int(color_map))

                self.result = dilated

                img_name = f"frm_{self.input_params_as_str()}"
                if text_overlay:
                    wrapper.store_image(
                        self.result,
                        img_name,
                        text_overlay=self.input_params_as_str(
                            exclude_defaults=False,
                            excluded_params=("progress_callback",),
                        ).replace(", ", "\n"),
                    )
                else:
                    wrapper.store_image(self.result, img_name, text_overlay=text_overlay)
            else:
                wrapper.store_image(wrapper.current_image, "source")

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

    @property
    def name(self):
        return "Filtering regional maxima"

    @property
    def real_time(self):
        return self.get_value_of("real_time") == 1

    @property
    def result_name(self):
        return "image"

    @property
    def output_kind(self):
        return "channel"

    @property
    def use_case(self):
        return [ToolFamily.PRE_PROCESSING]

    @property
    def description(self):
        return (
            "From scikit image - Filtering regional maxima: Perform a morphological reconstruction of an image.\n"
            + "Morphological reconstruction by dilation is similar to basic morphological dilation: high-intensity values will"
            + "replace nearby low-intensity values. The basic dilation operator, however, uses a structuring element to"
            + 'determine how far a value in the input image can spread. In contrast, reconstruction uses two images: a "seed"'
            + 'image, which specifies the values that spread, and a "mask" image, which gives the maximum allowed value at'
            + "each pixel. The mask image, like the structuring element, limits the spread of high-intensity values."
            + "Reconstruction by erosion is simply the inverse: low-intensity values spread from the seed image and are"
            + "limited by the mask image, which represents the minimum allowed value.\n"
            + "Alternatively, you can think of reconstruction as a way to isolate the connected regions of an image."
            + "For dilation, reconstruction connects regions marked by local maxima in the seed image: neighboring pixels"
            + "less-than-or-equal-to those seeds are connected to the seeded region.\n"
            + "Local maxima with values larger than the seed image will get truncated to the seed value."
        )
