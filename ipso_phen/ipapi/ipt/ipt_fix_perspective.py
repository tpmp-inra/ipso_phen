import numpy as np

import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from scipy.spatial import distance as dist
from skimage import measure
import cv2

from ipso_phen.ipapi.base.ipt_abstract import IptBase
import ipso_phen.ipapi.base.ip_common as ipc


def sort_contours(cnts, method="left-to-right"):
    # initialize the reverse flag and sort index
    reverse = False
    i = 0

    # handle if we need to sort in reverse
    if method == "right-to-left" or method == "bottom-to-top":
        reverse = True

    # handle if we are sorting against the y-coordinate rather than
    # the x-coordinate of the bounding box
    if method == "top-to-bottom" or method == "bottom-to-top":
        i = 1

    # construct the list of bounding boxes and sort them from top to
    # bottom
    boundingBoxes = [cv2.boundingRect(c) for c in cnts]
    (cnts, boundingBoxes) = zip(
        *sorted(zip(cnts, boundingBoxes), key=lambda b: b[1][i], reverse=reverse)
    )

    # return the list of sorted contours and bounding boxes
    return cnts, boundingBoxes


def min_distance(origin: tuple, points: list) -> tuple:
    if len(points) == 0:
        return None
    elif len(points) == 1:
        return points[0]
    else:
        res = points[0]
        min_dist = dist.euclidean(points[0], origin)
        for pt in points[1:]:
            cur_dist = dist.euclidean(pt, origin)
            if cur_dist < min_dist:
                res = pt
                min_dist = cur_dist
        return res


class IptFixPerspective(IptBase):
    def build_params(self):
        self.add_enabled_checkbox()

        self.add_combobox(
            name="mode",
            desc="Module mode",
            default_value="threshold",
            values=dict(
                threshold="Threshold only",
                dot_detection="Detect dots",
                fix_perspective="Fix perspective",
            ),
        )

        self.add_label(name="lbl1", desc="Multi range threshold")
        self.add_channel_selector(default_value="h", name="c1", desc="Channel 1")
        self.add_spin_box(
            name="c1_low",
            desc="Min threshold for channel 1",
            default_value=0,
            minimum=0,
            maximum=255,
        )
        self.add_spin_box(
            name="c1_high",
            desc="Max threshold for channel 1",
            default_value=255,
            minimum=0,
            maximum=255,
        )
        self.add_channel_selector(
            default_value="none", name="c2", desc="Channel 2", enable_none=True
        )
        self.add_spin_box(
            name="c2_low",
            desc="Min threshold for channel 2",
            default_value=0,
            minimum=0,
            maximum=255,
        )
        self.add_spin_box(
            name="c2_high",
            desc="Max threshold for channel 2",
            default_value=255,
            minimum=0,
            maximum=255,
        )
        self.add_channel_selector(
            default_value="none", name="c3", desc="Channel 3", enable_none=True
        )
        self.add_spin_box(
            name="c3_low",
            desc="Min threshold for channel 3",
            default_value=0,
            minimum=0,
            maximum=255,
        )
        self.add_spin_box(
            name="c3_high",
            desc="Max threshold for channel 3",
            default_value=255,
            minimum=0,
            maximum=255,
        )
        self.add_combobox(
            name="merge_mode",
            desc="How to merge thresholds",
            default_value="multi_and",
            values=dict(multi_and="Logical AND", multi_or="Logical OR"),
        )
        self.add_morphology_operator()

        self.add_label(name="lbl2", desc="Dot detection")
        self.add_spin_box(
            name="min_dot_size",
            desc="Minimal dot size (surface)",
            default_value=30,
            minimum=10,
            maximum=1000000,
        )
        self.add_spin_box(
            name="max_dot_size",
            desc="Maximal dot size (surface)",
            default_value=3000,
            minimum=10,
            maximum=1000000,
        )

        self.add_label(name="lbl3", desc="Destination size")
        self.add_spin_box(
            name="dst_width",
            desc="Destination width",
            default_value=800,
            minimum=10,
            maximum=10000,
        )
        self.add_spin_box(
            name="dst_height",
            desc="Destination height",
            default_value=600,
            minimum=10,
            maximum=10000,
        )
        # self.add_spin_box(
        #     name='pad_hor',
        #     desc='Horizontal padding',
        #     default_value=0,
        #     minimum=-100,
        #     maximum=100
        # )
        # self.add_spin_box(
        #     name='pad_ver',
        #     desc='Vertical padding',
        #     default_value=0,
        #     minimum=-100,
        #     maximum=100
        # )

    def process_wrapper(self, **kwargs):
        """
        Fix perspective:
        Fixes perspective using four dots to detect rectangle boundary.
        Use the included threshold utility to detect the dots.
        Real time: True

        Keyword Arguments (in parentheses, argument name):
            * Activate tool (enabled): Toggle whether or not tool is active
            * Module mode (mode):
            * Channel 1 (c1):
            * Min threshold for channel 1 (c1_low):
            * Max threshold for channel 1 (c1_high):
            * Channel 2 (c2):
            * Min threshold for channel 2 (c2_low):
            * Max threshold for channel 2 (c2_high):
            * Channel 3 (c3):
            * Min threshold for channel 3 (c3_low):
            * Max threshold for channel 3 (c3_high):
            * How to merge thresholds (merge_mode):
            * Morphology operator (morph_op):
            * Kernel size (kernel_size):
            * Kernel shape (kernel_shape):
            * Iterations (proc_times):
            * Minimal dot size (surface) (min_dot_size):
            * Maximal dot size (surface) (max_dot_size):
            * Destination width (dst_width):
            * Destination height (dst_height):
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            if self.get_value_of("enabled") == 1:
                img = wrapper.current_image
                pm = self.get_value_of("mode")

                channels = []
                stored_names = []
                for i in [1, 2, 3]:
                    c = self.get_value_of(f"c{i}")
                    if c == "none":
                        continue
                    msk, stored_name = wrapper.get_mask(
                        src_img=img,
                        channel=c,
                        min_t=self.get_value_of(f"c{i}_low"),
                        max_t=self.get_value_of(f"c{i}_high"),
                    )
                    channels.append(msk)
                    stored_names.append(stored_name)
                    wrapper.store_image(image=msk, text=stored_name)

                wrapper.store_image(
                    image=wrapper.build_mosaic(
                        shape=(wrapper.height // len(stored_names), wrapper.width, 3),
                        image_names=np.array(stored_names),
                    ),
                    text="partial_thresholds",
                )

                func = getattr(wrapper, self.get_value_of("merge_mode"), None)
                if func:
                    mask = self.apply_morphology_from_params(
                        func([mask for mask in channels if mask is not None])
                    )
                    wrapper.store_image(image=mask, text="merged_mask")
                else:
                    logger.error("Unable to merge partial masks")
                    res = False
                    return

                if pm == "threshold":
                    self.result = mask
                    res = True
                    return

                # Clean mask if needed
                labels = measure.label(input=mask, neighbors=8, background=0)
                dots_mask = np.zeros(mask.shape, dtype="uint8")
                min_dot_size = self.get_value_of("min_dot_size")
                max_dot_size = self.get_value_of("max_dot_size")
                # loop over the unique components
                for label in np.unique(labels):
                    # if this is the background label, ignore it
                    if label == 0:
                        continue

                    # otherwise, construct the label mask and count the
                    # number of pixels
                    labelMask = np.zeros(mask.shape, dtype="uint8")
                    labelMask[labels == label] = 255
                    numPixels = cv2.countNonZero(labelMask)

                    # if the number of pixels in the component is sufficiently
                    # large, then add it to our mask of "large blobs"
                    if min_dot_size <= numPixels <= max_dot_size:
                        dots_mask = cv2.add(dots_mask, labelMask)
                wrapper.store_image(image=dots_mask, text="mask_cleaned")

                # Find dots' positions
                mask = dots_mask
                # find the contours in the mask, then sort them from left to
                # right
                cnts = ipc.get_contours(
                    mask=mask,
                    retrieve_mode=cv2.RETR_EXTERNAL,
                    method=cv2.CHAIN_APPROX_SIMPLE,
                )
                cnts = sort_contours(cnts)[0]

                # loop over the contours
                dots = []
                for (i, c) in enumerate(cnts):
                    # draw the bright spot on the image
                    (x, y, w, h) = cv2.boundingRect(c)
                    ((cX, cY), radius) = cv2.minEnclosingCircle(c)
                    dots.append((int(cX), int(cY)))

                # Reorder dots
                top_left = min_distance(origin=(0, 0), points=dots)
                cv2.circle(img, top_left, 20, (0, 0, 255), 3)
                cv2.putText(
                    img,
                    f"top_left - {top_left}",
                    top_left,
                    cv2.FONT_HERSHEY_SIMPLEX,
                    2,
                    (255, 0, 255),
                    6,
                )
                top_right = min_distance(origin=(wrapper.width, 0), points=dots)
                cv2.circle(img, top_right, 20, (0, 0, 255), 3)
                cv2.putText(
                    img,
                    f"top_right - {top_right}",
                    top_right,
                    cv2.FONT_HERSHEY_SIMPLEX,
                    2,
                    (255, 0, 255),
                    6,
                )
                bottom_left = min_distance(origin=(0, wrapper.height), points=dots)
                cv2.circle(img, bottom_left, 20, (0, 0, 255), 3)
                cv2.putText(
                    img,
                    f"bottom_left - {bottom_left}",
                    bottom_left,
                    cv2.FONT_HERSHEY_SIMPLEX,
                    2,
                    (255, 0, 255),
                    6,
                )
                bottom_right = min_distance(
                    origin=(wrapper.width, wrapper.height), points=dots
                )
                cv2.circle(img, bottom_right, 20, (0, 0, 255), 3)
                cv2.putText(
                    img,
                    f"bottom_right - {bottom_right}",
                    bottom_right,
                    cv2.FONT_HERSHEY_SIMPLEX,
                    2,
                    (255, 0, 255),
                    6,
                )
                wrapper.store_image(image=img, text="dotted_image")

                if pm == "dot_detection":
                    self.result = img
                    res = True
                    return

                # pad_hor = self.get_value_of('pad_hor')
                # pad_ver = self.get_value_of('pad_ver')
                # top_left = (top_left[0] - pad_hor, top_left[1] - pad_ver)
                # top_right = (top_right[0] + pad_hor, top_right[1] - pad_ver)
                # bottom_left = (bottom_left[0] - pad_hor, bottom_left[1] + pad_ver)
                # bottom_right = (bottom_right[0] + pad_hor, bottom_right[1] + pad_ver)

                # Transform the image
                mat = cv2.getPerspectiveTransform(
                    src=np.array(
                        [top_left, top_right, bottom_right, bottom_left],
                        dtype="float32",
                    ),
                    dst=np.array(
                        [
                            [0, 0],
                            [self.get_value_of("dst_width") - 1, 0],
                            [
                                self.get_value_of("dst_width") - 1,
                                self.get_value_of("dst_height") - 1,
                            ],
                            [0, self.get_value_of("dst_height") - 1],
                        ],
                        dtype="float32",
                    ),
                )
                self.result = cv2.warpPerspective(
                    src=wrapper.current_image,
                    M=mat,
                    dsize=(
                        self.get_value_of("dst_width"),
                        self.get_value_of("dst_height"),
                    ),
                )
                wrapper.store_image(image=self.result, text="warped_image")

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
        return "Fix perspective"

    @property
    def package(self):
        return "Kornia"

    @property
    def real_time(self):
        return True

    @property
    def result_name(self):
        return "image"

    @property
    def output_kind(self):
        return "image"

    @property
    def use_case(self):
        return ["Exposure fixing", "Pre processing"]

    @property
    def description(self):
        return """Fixes perspective using four dots to detect rectangle boundary.
        Use the included threshold utility to detect the dots."""

    @property
    def short_test_script(self):
        return True
