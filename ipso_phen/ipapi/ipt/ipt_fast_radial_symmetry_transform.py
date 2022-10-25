import os
import logging

import cv2
import numpy as np

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ipt_abstract_analyzer import IptBaseAnalyzer


def gradx(img):
    img = img.astype("int")
    rows, cols = img.shape
    # Use hstack to add back in the columns that were dropped as zeros
    return np.hstack(
        (np.zeros((rows, 1)), (img[:, 2:] - img[:, :-2]) / 2.0, np.zeros((rows, 1)))
    )


def grady(img):
    img = img.astype("int")
    rows, cols = img.shape
    # Use vstack to add back the rows that were dropped as zeros
    return np.vstack(
        (np.zeros((1, cols)), (img[2:, :] - img[:-2, :]) / 2.0, np.zeros((1, cols)))
    )


class IptFastRadialSymmetryTransform(IptBaseAnalyzer):
    def build_params(self):
        self.add_enabled_checkbox()

        self.add_combobox(
            name="source_selector",
            desc="Select source",
            default_value="current_image",
            values={"current_image": "Current image", "mask": "Mask"},
            hint="Select which image will be used as source",
        )
        self.add_channel_selector(default_value="l")

        self.add_spin_box(
            name="radii",
            desc="Radii",
            default_value=3,
            minimum=1,
            maximum=100,
            hint="value for radius size in pixels (n in the original paper); also used to size gaussian kernel",
        )
        self.add_spin_box(
            name="alpha",
            desc="Alpha",
            default_value=2,
            minimum=1,
            maximum=100,
            hint="Strictness of symmetry transform (higher=more strict; 2 is good place to start)",
        )
        self.add_spin_box(
            name="beta",
            desc="Beta",
            default_value=3,
            minimum=0,
            maximum=100,
            hint="gradient threshold parameter, float in [0,1], value will be divided by 100",
        )
        self.add_spin_box(
            name="sigma",
            desc="Sigma",
            default_value=50,
            minimum=1,
            maximum=100,
            hint="Standard deviation factor for gaussian kernel, value will be divided by 100",
        )
        self.add_combobox(
            name="mode",
            desc="Mode",
            default_value="both",
            values={
                "bright": "bright",
                "dark": "dark",
                "both": "both",
            },
            hint="bright, dark, or both",
        )
        self.add_spin_box(
            name="thresh_low",
            desc="Min threshold",
            default_value=0,
            minimum=0,
            maximum=255,
        )
        self.add_spin_box(
            name="thresh_high",
            desc="Max threshold",
            default_value=255,
            minimum=0,
            maximum=255,
        )

    def process_wrapper(self, **kwargs):
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            if self.get_value_of("enabled") == 1:

                input_kind = self.get_value_of("source_selector")
                if input_kind == "mask":
                    img = self.get_mask()
                elif input_kind == "current_image":
                    img = wrapper.get_channel(
                        src_img=wrapper.current_image,
                        channel=self.get_value_of("channel"),
                    )
                else:
                    img = None
                    logger.error(f"Unknown source: {input_kind}")
                    self.result = None
                    return

                radii = self.get_value_of("radii")
                alpha = self.get_value_of("alpha")
                beta = self.get_value_of("beta") / 100
                sigma = self.get_value_of("sigma") / 100
                mode = self.get_value_of("mode")
                thresh_low = self.get_value_of("thresh_low")
                thresh_high = self.get_value_of("thresh_high")

                dark = mode == "dark" or mode == "both"
                bright = mode == "bright" or mode == "both"

                workingDims = tuple((e + 2 * radii) for e in img.shape)

                # Set up output and M and O working matrices
                output = np.zeros(img.shape, np.uint8)
                O_n = np.zeros(workingDims, np.int16)
                M_n = np.zeros(workingDims, np.int16)

                # Calculate gradients
                gx = gradx(img)
                wrapper.store_image(
                    image=self.to_uint8(
                        gx, normalize=self.get_value_of("normalize") == 1
                    ),
                    text="gx",
                )
                gy = grady(img)
                wrapper.store_image(
                    image=self.to_uint8(
                        gy, normalize=self.get_value_of("normalize") == 1
                    ),
                    text="gy",
                )

                # Find gradient vector magnitude
                gnorms = np.sqrt(np.add(np.multiply(gx, gx), np.multiply(gy, gy)))

                # Use beta to set threshold - speeds up transform significantly
                gthresh = np.amax(gnorms) * beta

                # Find x/y distance to affected pixels
                gpx = (
                    np.multiply(
                        np.divide(gx, gnorms, out=np.zeros(gx.shape), where=gnorms != 0),
                        radii,
                    )
                    .round()
                    .astype(int)
                )
                wrapper.store_image(
                    image=self.to_uint8(
                        gpx, normalize=self.get_value_of("normalize") == 1
                    ),
                    text="gpx",
                )
                gpy = (
                    np.multiply(
                        np.divide(gy, gnorms, out=np.zeros(gy.shape), where=gnorms != 0),
                        radii,
                    )
                    .round()
                    .astype(int)
                )
                wrapper.store_image(
                    image=self.to_uint8(
                        gpy, normalize=self.get_value_of("normalize") == 1
                    ),
                    text="gpy",
                )

                # Iterate over all pixels (w/ gradient above threshold)
                for coords, gnorm in np.ndenumerate(gnorms):
                    if gnorm > gthresh:
                        i, j = coords
                        # Positively affected pixel
                        if bright:
                            ppve = (i + gpx[i, j], j + gpy[i, j])
                            O_n[ppve] += 1
                            M_n[ppve] += gnorm
                        # Negatively affected pixel
                        if dark:
                            pnve = (i - gpx[i, j], j - gpy[i, j])
                            O_n[pnve] -= 1
                            M_n[pnve] -= gnorm

                # Abs and normalize O matrix
                O_n = np.abs(O_n)
                O_n = O_n / float(np.amax(O_n))

                # Normalize M matrix
                M_max = float(np.amax(np.abs(M_n)))
                M_n = M_n / M_max

                # Elementwise multiplication
                F_n = np.multiply(np.power(O_n, alpha), M_n)

                wrapper.store_image(
                    image=self.to_uint8(
                        O_n, normalize=self.get_value_of("normalize") == 1
                    ),
                    text="O_n",
                )
                wrapper.store_image(
                    image=self.to_uint8(
                        M_n, normalize=self.get_value_of("normalize") == 1
                    ),
                    text="M_n",
                )

                # Gaussian blur
                kSize = int(np.ceil(radii / 2))
                kSize = kSize + 1 if kSize % 2 == 0 else kSize

                self.result = self.to_uint8(
                    img=cv2.GaussianBlur(F_n, (kSize, kSize), int(radii * sigma)),
                    normalize=self.get_value_of("normalize") == 1,
                )
                if thresh_low > 0 or thresh_high < 255:
                    thresh_low, thresh_high = min(thresh_low, thresh_high), max(
                        thresh_low, thresh_high
                    )
                    self.result = cv2.inRange(self.result, thresh_low, thresh_high)

                wrapper.store_image(self.result, "frst")
                res = True
            else:
                wrapper.store_image(wrapper.current_image, "current_image")
                res = True
        except Exception as e:
            res = False
            logger.error(f"Fast Radial Symmetry Transform FAILED, exception: {repr(e)}")
        else:
            pass
        finally:
            return res

    @property
    def name(self):
        return "Fast Radial Symmetry Transform"

    @property
    def package(self):
        return "Me"

    @property
    def is_wip(self):
        return True

    @property
    def real_time(self):
        return False

    @property
    def result_name(self):
        return "image"

    @property
    def output_kind(self):
        return "image"

    @property
    def use_case(self):
        return ["Feature extraction", "Pre processing", "Visualization"]

    @property
    def description(self):
        return """'Fast Radial Symmetry Transform
Implementation of fast radial symmetry transform in pure Python using OpenCV and numpy.
Based on: Loy, G., & Zelinsky, A. (2002). A fast radial symmetry transform for detecting points of interest. Computer Vision, ECCV 2002."""
