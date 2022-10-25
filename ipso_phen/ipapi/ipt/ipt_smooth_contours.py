import os
import logging

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

import numpy as np
import cv2
from scipy.interpolate import splprep, splev

from ipso_phen.ipapi.base.ipt_abstract import IptBase
from ipso_phen.ipapi.base import ip_common as ipc


class IptSmoothContours(IptBase):
    def build_params(self):
        self.add_enabled_checkbox()

        self.add_spin_box(
            name="spline_degree",
            desc="Degree of spline curve",
            default_value=3,
            minimum=1,
            maximum=30,
            hint="Degree of the spline. Cubic splines are recommended. Even values of k should be avoided especially with a small s-value. 1 <= k <= 5, default is 3.",
        )

        self.add_spin_box(
            name="smoothing",
            desc="Smoothing condition",
            default_value=10,
            minimum=0,
            maximum=100,
            hint="Value will be divide by 10",
        )

    def process_wrapper(self, **kwargs):
        """
        Smooth contours:
        'Smooth contours
        Real time: True

        Keyword Arguments (in parentheses, argument name):
            * Activate tool (enabled): Toggle whether or not tool is active
            * Degree of spline curve (spline_degree): Degree of the spline. Cubic splines are recommended. Even values of k should be avoided especially with a small s-value. 1 <= k <= 5, default is 3.
            * Smoothing condition (smoothing): Value will be divide by 10"""

        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            if self.get_value_of("enabled") == 1:
                img = wrapper.current_image
                mask = self.get_mask()
                if mask is None:
                    logger.error("Failure Smooth contours: mask must be initialized")
                    return

                # Get source contours
                contours = [
                    c
                    for c in ipc.get_contours(
                        mask=mask,
                        retrieve_mode=cv2.RETR_LIST,
                        method=cv2.CHAIN_APPROX_SIMPLE,
                    )
                    if (cv2.contourArea(c, True) < 0)
                ]
                contours.sort(key=lambda x: cv2.contourArea(x), reverse=True)

                output = mask.copy()

                for contour in contours:
                    x, y = contour.T
                    # Convert from np arrays to normal arrays
                    tck, u, = splprep(
                        [x.tolist()[0], y.tolist()[0]],
                        u=None,
                        k=ipc.ensure_odd(self.get_value_of("spline_degree")),
                        s=self.get_value_of("smoothing") / 10,
                        per=1,
                    )
                    u_new = np.linspace(u.min(), u.max(), 1000)
                    x_new, y_new = splev(u_new, tck, der=0)

                    cv2.drawContours(
                        output,
                        [
                            np.asarray(
                                [[[int(i[0]), int(i[1])]] for i in zip(x_new, y_new)],
                                dtype=np.int32,
                            )
                        ],
                        0,
                        255,
                        -1,
                    )

                self.result = output

                # Write your code here
                wrapper.store_image(output, "current_image")
                res = True
            else:
                wrapper.store_image(wrapper.current_image, "current_image")
                res = True
        except Exception as e:
            res = False
            logger.error(f"Smooth contours FAILED, exception: {repr(e)}")
        else:
            pass
        finally:
            return res

    @property
    def name(self):
        return "Smooth contours"

    @property
    def package(self):
        return "TPMP"

    @property
    def is_wip(self):
        return True

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
        return ["Mask cleanup"]

    @property
    def description(self):
        return """'Smooth contours"""
