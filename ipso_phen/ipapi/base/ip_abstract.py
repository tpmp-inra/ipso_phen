import os
from typing import Any, Union
import logging

import math
import matplotlib
from matplotlib import pyplot as plt
import numpy as np
import cv2

from ipso_phen.ipapi.file_handlers.fh_base import file_handler_factory
from ipso_phen.ipapi.base.image_wrapper import ImageWrapper
import ipso_phen.ipapi.base.ip_common as ipc
from ipso_phen.ipapi.tools.comand_line_wrapper import ArgWrapper
from ipso_phen.ipapi.tools.regions import (
    CircleRegion,
    RectangleRegion,
    EmptyRegion,
    Point,
    AbstractRegion,
)
from ipso_phen.ipapi.tools.common_functions import force_directories

matplotlib.use("agg")

KLC_FULLY_INSIDE = dict(val=0, color=ipc.C_GREEN)
KLC_OVERLAPS = dict(val=1, color=ipc.C_BLUE)
KLC_PROTECTED_DIST_OK = dict(val=2, color=ipc.C_LIGHT_STEEL_BLUE)
KLC_PROTECTED_SIZE_OK = dict(val=3, color=ipc.C_CABIN_BLUE)
KLC_OK_TOLERANCE = dict(val=4, color=ipc.C_TEAL)
KLC_NO_BIG_ENOUGH = dict(val=5, color=ipc.C_FUCHSIA)
KLC_NO_CLOSE_ENOUGH = dict(val=6, color=ipc.C_ORANGE)
KLC_OUTSIDE = dict(val=7, color=ipc.C_RED)
KLC_BIG_ENOUGH_TO_IGNORE_DISTANCE = dict(val=8, color=ipc.C_LIME)

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))


class ImageListHolder:
    def __init__(self, file_list, database):
        self.image_list = [
            file_handler_factory(file_path_, database=database)
            for file_path_ in file_list
        ]

    def __len__(self):
        return len(self.image_list)

    def retrieve_image(self, key, value, transformations: dict):
        """Return an image based on key value

        :param key: one of the wrapper properties
        :param value: value
        :return: image
        """
        for fh in self.image_list:
            if value in fh.value_of(key):
                img = fh.load_source_file()
                for t in transformations:
                    if t["action"] == "crop":
                        img = t["roi"].crop(
                            src_image=img,
                            fixed_width=t["fixed_width"],
                            fixed_height=t["fixed_height"],
                        )
                    elif t["action"] == "scale":
                        img = ipc.scale_image(
                            src_img=img,
                            scale_factor=t["scale_factor"],
                        )
                return img
        return None


class BaseImageProcessor(ImageWrapper):
    process_dict = None

    def __init__(
        self,
        file_path: str,
        options: ArgWrapper = None,
        database=None,
        scale_factor=1,
    ) -> None:
        super().__init__(file_path, database)

        if options is None:
            self._options = {}
        else:
            self._options = dict(options.__dict__)

        self.target_database = database
        self.scale_factor = scale_factor

        self._source_image = None
        self._current_image = None
        self.mask = None

        self.lock = False

        self.image_list = []
        self.forced_storage_images_list = []
        self._rois_list = []
        self._mosaic_data = None
        self.data_output = {}
        self.image_transformations = []

        self.good_image = False
        self.owner = None
        self.linked_images_holder = None

        self._built_channels = {}

        self.csv_data_holder = self.init_csv_writer()

    def init_data_holder(self):
        self.csv_data_holder.clear()
        self.csv_data_holder.update_csv_value("experiment", self.experiment)
        self.csv_data_holder.update_csv_value("plant", self.plant)
        self.csv_data_holder.update_csv_value("date_time", self.date_time)
        self.csv_data_holder.update_csv_value("camera", self.camera)
        self.csv_data_holder.update_csv_value("view_option", self.view_option)

    def reset(self):
        if self.lock:
            return
        self.init_data_holder()
        self._rois_list = []
        self.image_list = []
        self.data_output = {}
        self._mosaic_data = None
        self.store_mosaic = "none"
        self.image_transformations = []
        self._current_image = self.source_image

    def init_csv_writer(self):
        """Creates a csv writer with the variables specified in the class
        child classes should override this method

        :return: Csv writer
        """
        return ipc.AbstractCsvWriter()

    @staticmethod
    def can_process(dict_data: dict) -> bool:
        """
        Checks if the class can process the image
        :param dict_data: Dictionnary containing filter data
        :return: True if current class can process data
        """
        return False

    def load_source_image(self, store_source=False):
        """
        Loads source image and applies corrections if needed

        :param store_source: if true image will be stores in image_list
        :return:numpy array -- Fixed source image
        """
        src_img = self.file_handler.load_source_file()
        self.good_image = src_img is not None

        if self.good_image:
            src_img = self._fix_source_image(src_img)
            if self.scale_factor != 1:
                src_img = ipc.scale_image(src_img=src_img, scale_factor=self.scale_factor)
            if store_source:
                self.store_image(src_img, "source")
        else:
            logger.error("Unable to load source image")

        return src_img

    def retrieve_linked_images(self):
        """On first call builds the wrappers corresponding to MSP images linked to observation

        :return: Number of MSP images available
        """
        if self.linked_images_holder is None:
            self.linked_images_holder = ImageListHolder(
                self.file_handler.linked_images,
                self.target_database,
            )
        if self.linked_images_holder is None:
            return 0
        else:
            return len(self.linked_images_holder)

    @staticmethod
    def draw_text(
        img: Any,
        text: str,
        fnt_color: tuple = ipc.C_RED,
        background_color: Union[None, tuple] = None,
    ) -> None:
        """Draw text into img, always draws on bottom left portion of the image
        Modifies source image

        :param img: target image
        :param text: text
        """
        fnt_face = cv2.FONT_HERSHEY_DUPLEX
        fnt_scale = img.shape[0] / 1000
        fnt_thickness = max(round(img.shape[0] / 1080), 1)
        y = img.shape[0] - 20
        for line in reversed(list(text.split("\n"))):
            text_size, _ = cv2.getTextSize(line, fnt_face, fnt_scale, fnt_thickness)
            if background_color is not None:
                cv2.rectangle(
                    img,
                    (10, y - text_size[1] - 4),
                    (text_size[0], y + 4),
                    background_color,
                    -1,
                )
            cv2.putText(
                img,
                line,
                (10, y),
                fnt_face,
                fnt_scale,
                fnt_color,
                fnt_thickness,
                cv2.LINE_AA,
            )
            y -= text_size[1] + 8

    def draw_image(self, **kwargs):
        """Build pseudo color image

        Keyword Arguments:
            * normalize_before: Normalize channel
            * src_image: Source image
            * channel: Channel to transform into pseudo color
            * src_mask: Mask
            * background: Background selection either 'img' or color tuple
            * color_map: color map used
            * roi: ignore everything outside ROI
            * contour_thickness
            * hull_thickness
            * straight_bounding_rec_thickness
            * enclosing_circle_thickness
            * centroid_width
            * height_thickness
            * width_thickness
        :return: drawn image
        """
        src = kwargs.get("src_image", self.current_image)
        mask = kwargs.get("src_mask", self.mask)
        obj = kwargs.get("objects", None)
        channel = kwargs.get("channel", "l")
        background = kwargs.get("background", "source")
        if background == "color":
            background = kwargs.get("bcg_color", ipc.C_BLACK)
        foreground = kwargs.get("foreground", "source")
        if foreground == "color":
            foreground = kwargs.get("fore_color", ipc.C_WHITE)
        bck_grd_luma = kwargs.get("bck_grd_luma", 100)
        normalize_before = bool(kwargs.get("normalize_before", False))
        color_map = kwargs.get("color_map", ipc.DEFAULT_COLOR_MAP)
        if isinstance(color_map, str):
            _, color_map = color_map.split("_")
            color_map = int(color_map)
        roi = kwargs.get("roi", None)
        contour_thickness = kwargs.get("contour_thickness", 0)
        hull_thickness = kwargs.get("hull_thickness", 0)
        bounding_rec_thickness = kwargs.get("bounding_rec_thickness", 0)
        straight_bounding_rec_thickness = kwargs.get("straight_bounding_rec_thickness", 0)
        enclosing_circle_thickness = kwargs.get("enclosing_circle_thickness", 0)
        centroid_width = kwargs.get("centroid_width", 0)
        centroid_line_width = kwargs.get("centroid_line_width", 4)
        height_thickness = kwargs.get("height_thickness", 0)
        width_thickness = kwargs.get("width_thickness", 0)

        # Apply roi to mask
        if (roi is not None) and (mask is not None):
            mask_ = roi.keep(mask)
        elif mask is not None:
            mask_ = mask.copy()
        else:
            mask_ = None

        fnt = (cv2.FONT_HERSHEY_SIMPLEX, 0.6)
        fnt_scale = src.shape[0] / 1000
        fnt_thickness = max(round(src.shape[1] / 1080) * 2, 1)

        # Build foreground
        if len(src.shape) == 2 or (len(src.shape) == 3 and src.shape[2] == 1):
            foreground_img = np.dstack((src, src, src))
        elif isinstance(foreground, tuple):
            foreground_img = np.full(src.shape, foreground, np.uint8)
        elif foreground == "source":
            foreground_img = src.copy()
        elif foreground == "false_colour":
            if isinstance(channel, str):
                c = self.get_channel(src, channel)
            else:
                c = channel.copy()
            if mask_ is not None:
                c = cv2.bitwise_and(c, c, mask=mask_)
            if normalize_before:
                c = cv2.equalizeHist(c)
            foreground_img = cv2.applyColorMap(c, color_map)
        elif foreground == "bw":
            foreground_img = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
            foreground_img = np.dstack((foreground_img, foreground_img, foreground_img))
        elif isinstance(foreground, tuple):
            foreground_img = np.full(src.shape, foreground, np.uint8)
        elif isinstance(foreground, str):
            foreground_img = np.full(src.shape, ipc.all_colors_dict[foreground], np.uint8)
        else:
            logger.error(f"Unknown foreground {background}")
            return np.full(src.shape, ipc.C_FUCHSIA, np.uint8)

        if mask_ is None:
            img = foreground_img.copy()
        else:
            # Build background
            if background == "white":
                background_img = np.full(foreground_img.shape, ipc.C_WHITE, np.uint8)
            elif background == "black":
                background_img = np.full(foreground_img.shape, ipc.C_BLACK, np.uint8)
            elif background == "silver":
                background_img = np.full(foreground_img.shape, ipc.C_SILVER, np.uint8)
            elif background == "bw":
                background_img = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
                background_img = np.dstack(
                    (background_img, background_img, background_img)
                )
            elif background == "source":
                if len(src.shape) == 2 or (len(src.shape) == 3 and src.shape[2] == 1):
                    background_img = np.dstack((src, src, src))
                else:
                    background_img = np.copy(src)
            elif isinstance(background, tuple):
                if len(background) == 3:
                    background_img = np.full(foreground_img.shape, background, np.uint8)
                elif len(background) == 1:
                    background_img = np.full(
                        foreground_img.shape,
                        (background, background, background),
                        np.uint8,
                    )
                else:
                    logger.error(f"Unknown color: {background}")
                    return np.full(foreground_img.shape, ipc.C_FUCHSIA, np.uint8)
            else:
                logger.error(f"Unknown background {background}")
                return np.full(foreground_img.shape, ipc.C_FUCHSIA, np.uint8)
            if bck_grd_luma != 100:
                bck_grd_luma /= 100
                lum, a, b = cv2.split(cv2.cvtColor(background_img, cv2.COLOR_BGR2LAB))
                lum = (lum * bck_grd_luma).astype(np.uint)
                lum[lum >= 255] = 255
                lum = lum.astype(np.uint8)
                background_img = cv2.merge((lum, a, b))
                background_img = cv2.cvtColor(background_img, cv2.COLOR_LAB2BGR)
            # Merge foreground & background
            foreground_img = cv2.bitwise_and(foreground_img, foreground_img, mask=mask_)
            background_img = cv2.bitwise_and(
                background_img, background_img, mask=255 - mask_
            )
            img = cv2.bitwise_or(foreground_img, background_img)
            # Draw contour
            if (np.count_nonzero(mask_) > 0) and (
                (contour_thickness > 0)
                or (hull_thickness > 0)
                or (bounding_rec_thickness > 0)
                or (straight_bounding_rec_thickness > 0)
                or (enclosing_circle_thickness > 0)
                or (centroid_width > 0)
                or (height_thickness > 0)
                or (width_thickness > 0)
            ):
                if obj is None:
                    id_objects, obj_hierarchy = ipc.get_contours_and_hierarchy(
                        mask=mask_,
                        retrieve_mode=cv2.RETR_TREE,
                        method=cv2.CHAIN_APPROX_NONE,
                    )
                    obj, _ = self.object_composition(img, id_objects, obj_hierarchy)
                if contour_thickness > 0:
                    cv2.drawContours(img, obj, -1, ipc.C_FUCHSIA, contour_thickness)
                if hull_thickness > 0:
                    hull = cv2.convexHull(obj)
                    cv2.drawContours(img, [hull], 0, ipc.C_LIME, hull_thickness)
                if bounding_rec_thickness > 0:
                    rect = cv2.minAreaRect(obj)
                    box = cv2.boxPoints(rect)
                    box = np.int0(box)
                    cv2.drawContours(img, [box], 0, ipc.C_RED, bounding_rec_thickness)
                if straight_bounding_rec_thickness > 0:
                    x, y, w, h = cv2.boundingRect(obj)
                    cv2.rectangle(
                        img,
                        (x, y),
                        (x + w, y + h),
                        ipc.C_PURPLE,
                        bounding_rec_thickness,
                    )
                if enclosing_circle_thickness > 0:
                    (x, y), radius = cv2.minEnclosingCircle(obj)
                    center = (int(x), int(y))
                    radius = int(radius)
                    cv2.circle(
                        img, center, radius, ipc.C_YELLOW, enclosing_circle_thickness
                    )
                if (
                    (centroid_width > 0)
                    or (height_thickness > 0)
                    or (width_thickness > 0)
                ):
                    moments = cv2.moments(mask_, binaryImage=True)
                    if moments["m00"] != 0:
                        cmx, cmy = (
                            moments["m10"] / moments["m00"],
                            moments["m01"] / moments["m00"],
                        )
                        x_, y_, width_, height_ = cv2.boundingRect(obj)
                        if height_thickness > 0:
                            cv2.line(
                                img,
                                (int(cmx), y_),
                                (int(cmx), y_ + height_),
                                ipc.C_CYAN,
                                height_thickness,
                            )
                        if width_thickness > 0:
                            cv2.line(
                                img,
                                (x_, int(cmy)),
                                (x_ + width_, int(cmy)),
                                ipc.C_CYAN,
                                width_thickness,
                            )
                        if centroid_width > 0:
                            cv2.circle(
                                img,
                                (int(cmx), int(cmy)),
                                centroid_width,
                                ipc.C_BLUE,
                                centroid_line_width,
                            )
                            if bool(kwargs.get("cy_num", False)) is True:
                                cv2.line(
                                    img,
                                    (int(cmx), 0),
                                    (int(cmx), int(cmy)),
                                    ipc.C_BLUE,
                                    centroid_line_width,
                                )
                                cv2.putText(
                                    img,
                                    f"cy: {cmy:.2f}",
                                    (int(cmx) + 5, int(cmy / 2)),
                                    fnt[0],
                                    fnt_scale,
                                    ipc.C_BLUE,
                                    fnt_thickness,
                                )

        if roi is not None:
            src_ = src.copy()
            src_[roi.top : roi.bottom, roi.left : roi.right] = img[
                roi.top : roi.bottom, roi.left : roi.right
            ]
            return src_
        else:
            return img

    def store_image(
        self,
        image: Any,
        text: str,
        rois: Any = (),
        mosaic_list: list = None,
        text_overlay: Any = False,
        force_store: bool = False,
        font_color: tuple = ipc.C_RED,
        **kwargs,
    ) -> dict:
        """
        Store image for debug or result

        :param image: Source image
        :param text: Image name, used as key
        :param rois: Regions of interest, will be printed on image
        :param mosaic_list: if present add image name to list
        :param text_overlay: Text to be printed on top of stored image
        :param force_store: Bypass storage options
        :return: Dictionary containing stored image data
        """

        if self.owner is not None:
            target = self.owner
            text = f"{self.view_option}_{text}"
        else:
            target = self

        for dic in target.image_list:
            if dic["name"].lower() == text:
                target.image_list.remove(dic)

        if (
            (text and (target.store_images or (text.lower() == "mosaic")))
            or force_store
            or (text in self.forced_storage_images_list)
        ):
            # Create dummy image if issue
            if image is not None:
                cp = image.copy()
            else:
                cp = np.full((100, 100, 3), ipc.C_FUCHSIA, np.uint8)

            # Ensure image is 3D
            if (rois or text_overlay) and (
                len(cp.shape) == 2 or (len(cp.shape) == 3 and cp.shape[2] == 1)
            ):
                cp = np.dstack((cp, cp, cp))

            # Print ROIs if needed
            if isinstance(rois, bool) and rois:
                rois = self.rois_list
            if rois:
                for roi in rois:
                    cp = roi.draw_to(cp, line_width=2)

            # Print text if needed
            if isinstance(text_overlay, str):
                self.draw_text(
                    img=cp,
                    text=text_overlay,
                    fnt_color=font_color,
                )
            elif text_overlay:
                self.draw_text(
                    img=cp,
                    text=text.replace(", ", "\n"),
                    fnt_color=font_color,
                )

            new_dict = dict(name=text, image=cp, written=False)
            target.image_list.append(new_dict)
            if target.write_images == "plot":
                target.plot_image(img_dict=new_dict, destroy_window=True)
            if mosaic_list is not None and text:
                mosaic_list.append(text)
            return new_dict
        else:
            return dict()

    def image_path_from_name(self, name: str):
        """Calculates target image saving path from name

        :param name: name of the image in the dictionary cf. image_list
        :return: destination file path
        """
        image_dict = self.retrieve_image_dict(name)
        if image_dict is not None:
            return self.image_storage_path(image_dict)
        else:
            return ""

    def image_storage_path(
        self,
        dic: dict,
        index: str = "",
        ext: str = "jpg",
        is_force_output: bool = False,
        is_force_fullname: bool = False,
    ) -> str:
        """returns path to which an image will be written

        Arguments:
            dic {dictionary} -- image info: 'mode', 'text', 'image'

        Keyword Arguments:
            index {str} -- image index to be printed as a prefix (default: {''})
            ext {str} -- extension format (default: {'jpg'})

        Returns:
            str -- destination file path
        """

        store_ = is_force_output or self.is_store_image(dic["name"])
        if not store_:
            return ""

        if dic["name"] == "use_source_name":
            return f"{self.dst_path}{self.name}.{ext}"

        if is_force_fullname:
            if index:
                return f'{self.dst_path}{index}_{self.name}_{dic["name"]}.{ext}'
            else:
                return f'{self.dst_path}{self.name}_{dic["name"]}.{ext}'
        else:
            if self.is_plot_image(dic["name"]):
                return ""
            elif self.is_save_image(dic["name"]):
                if dic["name"] == "mosaic":
                    tmp_path = "{}{}".format(self.dst_path, "mosaics")
                    tmp_path = os.path.join(tmp_path, "")
                    force_directories(tmp_path)
                    return "{}{}.jpg".format(tmp_path, self.name)
                else:
                    tmp_path = f"{self.dst_path}{self.name}"
                    tmp_path = os.path.join(tmp_path, "")
                    force_directories(tmp_path)
                    return f'{tmp_path}{index}_{dic["name"]}.{ext}'
            else:
                return ""

    def save_image(self, img: Any, idx: int = -1) -> None:
        if idx >= 0:
            str_idx = str(idx)
        else:
            str_idx = ""
        tmp_path = self.image_storage_path(img, index=str_idx)
        if tmp_path:
            cv2.imwrite(tmp_path, img["image"])
            img["written"] = True

    def plot_image(self, img_dict: dict, destroy_window: bool = False) -> bool:
        res = False
        try:
            cv2.imshow(
                img_dict["name"],
                ipc.resize_image(
                    img_dict["image"].copy(),
                    target_rect=RectangleRegion(left=0, width=800, top=0, height=600),
                    keep_aspect_ratio=True,
                ),
            )
            cv2.waitKey(0)
            if destroy_window:
                cv2.destroyAllWindows()
        except Exception as e:
            logger.exception(f'Unable to plot {img_dict["name"]}: "{repr(e)}"')
            res = False
        else:
            res = True
        finally:
            return res

    def print_image(self, img: Any, idx: int = -1) -> None:
        """
        Print image according to options

        :param img: numpy array
        :param idx: int
        :return:
        """
        if img["written"] is not True:
            if self.is_plot_image(img["name"]):
                self.plot_image(img_dict=img)
            elif self.is_save_image(img["name"]):
                self.save_image(img=img, idx=idx)

    def retrieve_image_dict(self, dict_name: str):
        """Retrieve image dictionary from the name key

        :rtype: bool, dict
        :param dict_name: key
        :return: success, image dictionary
        """
        if dict_name.lower() == "":
            return None
        else:
            for dic in self.image_list:
                if dic["name"].lower() == dict_name.lower():
                    return dic
            if dict_name.lower() == "source":
                return self.store_image(self.source_image, "source")
            if dict_name.lower() == "mask":
                return self.store_image(self.mask, "mask")
        return None

    def print_mosaic(self, padding: 2):
        if (self.store_mosaic.lower() != "none") or (self.write_mosaic.lower() != "none"):
            if self._mosaic_data is None:
                if self.store_mosaic.lower() == "debug":
                    self._mosaic_data = np.array(
                        ["source", "img_wth_tagged_cnt", "shapes"]
                    )
                elif self.store_mosaic.lower() == "result":
                    img_lst = ["!n", "!n", "!n", "!n"]
                    available_images = [dic["name"] for dic in self.image_list]
                    if "true_source_image" in available_images:
                        img_lst[0] = "true_source_image"
                    else:
                        img_lst[0] = "source"
                    if "mask" in available_images:
                        img_lst[1] = "mask"
                    if "pseudo_on" in available_images:
                        img_lst[2] = "pseudo_on"
                    if "shapes" in available_images:
                        img_lst[3] = "shapes"

                    for img_name in reversed(available_images):
                        if img_lst.count("!n") == 0:
                            break
                        if not (img_name in img_lst) and (img_name != "histogram"):
                            try:
                                idx = len(img_lst) - 1 - img_lst[::-1].index("!n")
                            except ValueError as _:
                                break
                            img_lst[idx] = img_name
                    self._mosaic_data = np.array(
                        [[img_lst[0], img_lst[1]], [img_lst[2], img_lst[3]]]
                    )
                else:
                    raise NotImplementedError

            try:
                canvas = self.build_mosaic(padding=padding)
                mosaic_ = self.store_image(canvas, "mosaic")
                self.print_image(mosaic_)
            except Exception as e:
                # Unsupported format detected
                logger.exception(
                    'Exception: "{}" - Image: "{}", unsupported mosaic'.format(
                        repr(e), str(self)
                    )
                )

    def print_images(self):
        """Prints images to disc according to options and selection

        Keyword Arguments:
            selection {list} -- List of image names to be printed (default: {[]})
        """
        if self.write_images == "print":
            for i, img in enumerate(self.image_list):
                if img["written"] is True:
                    continue
                self.print_image(img, i + 1)

        self.print_mosaic()

    def avg_brightness_contrast(
        self, img: Any = None, mode: str = "std", mask=None
    ) -> tuple:
        """Calculates average brightness using one of 3 available methods

        * std='standard, objective'
        * p1='perceived option 1
        * p2='perceived option 2, slower to calculate
        :param mask:
        :param img:
        :param mode: std, p1 or p2
        :return: mean, std_dev
        """
        if img is None:
            img = self.current_image
        b, g, r = cv2.split(img)
        if mode == "std":
            c = r * 0.2126 + g * 0.7152 + b * 0.0722
        elif mode == "p1":
            c = r * 0.299 + g * 0.587 + b * 0.114
        elif mode == "p2":
            c = np.sqrt(
                0.241 * np.power(r.astype(np.float), 2)
                + 0.691 * np.power(g.astype(np.float), 2)
                + 0.068 * np.power(b.astype(np.float), 2)
            )
        else:
            logger.error("Unknown average calculation mode")
            return 0, 0
        if mask is None:
            tmp_tuple = cv2.meanStdDev(c.reshape(c.shape[1] * c.shape[0]))
        else:
            tmp_tuple = cv2.meanStdDev(
                c.reshape(c.shape[1] * c.shape[0]),
                mask=mask.reshape(mask.shape[1] * mask.shape[0]),
            )

        return tmp_tuple[0][0][0], tmp_tuple[1][0][0]

    def object_composition(self, img: Any, contours: Any, hierarchy: Any):
        """From PlantCV: Groups objects into a single object, usually done after object filtering.
        Inputs:
        contours = object list
        Returns:
        group    = grouped contours list
        mask     = image mask
        :param img: numpy array
        :param contours: list
        :param hierarchy: list
        :return group: list
        :return mask: numpy array
        """

        ori_img = np.copy(img)
        if len(ori_img.shape) == 2:
            ori_img = np.dstack((ori_img, ori_img, ori_img))
            mask = np.zeros_like(a=ori_img, dtype=np.uint8)
        else:
            mask = np.zeros_like(a=ori_img[:, :, 0], dtype=np.uint8)

        stack = np.zeros((len(contours), 1))

        for c, cnt in enumerate(contours):
            # if hierarchy[0][c][3] == -1:
            if hierarchy[0][c][2] == -1 and hierarchy[0][c][3] > -1:
                stack[c] = 0
            else:
                stack[c] = 1
        ids = np.where(stack == 1)[0]
        if len(ids) > 0:
            group = np.vstack([contours[i] for i in ids])
            cv2.drawContours(mask, contours, -1, 255, -1, hierarchy=hierarchy)

            if self.store_images:
                dbg_img = self.draw_image(
                    src_image=ori_img,
                    src_mask=mask,
                    background="bw",
                    foreground="source",
                )
                cv2.drawContours(dbg_img, group, -1, (255, 0, 0), 6)
                for cnt in contours:
                    cv2.drawContours(dbg_img, cnt, -1, (255, 0, 255), 4)
                self.store_image(dbg_img, "objcomp")

            return group, mask
        else:
            logger.error(f"Warning: {repr(self.name)} Invalid contour.")
            return None, None

    # @time_method
    def analyze_object(self, img: Any, mask: Any):
        """Outputs numeric properties for an input object (contour or grouped contours).
        Inputs:
        img             = image object (most likely the original), color(RGB)
        obj             = single or grouped contour object
        mask            = binary image to use as mask for moments analysis
        debug           = None, print, or plot. Print = save to file, Plot = print to screen.
        Returns:
        shape_header    = shape data table headers
        shape_data      = shape data table values
        :param img: numpy array
        :param obj: list
        :param mask: numpy array
        :return:
        """

        obj, mask = self.prepare_analysis(
            self.draw_image(src_mask=mask, background="silver", foreground="source"),
            mask,
        )

        # Valid objects can only be analyzed if they have >= 5 vertices
        if len(obj) < 5:
            return None, None, None

        ori_img = np.copy(img)
        hull = cv2.convexHull(obj)
        m = cv2.moments(mask, binaryImage=True)
        area = m["m00"]
        if area:
            # x and y position (bottom left?) and extent x (width) and extent y (height)
            x, y, width, height = cv2.boundingRect(obj)

            # Centroid (center of mass x, center of mass y)
            cmx, cmy = (m["m10"] / m["m00"], m["m01"] / m["m00"])

            # Store Shape Data
            self.csv_data_holder.update_csv_value("area", area)
            if self.csv_data_holder.has_csv_key("centroid"):
                self.csv_data_holder.update_csv_value(
                    "centroid_x",
                    cmx,
                    force_pair=True,
                )
                self.csv_data_holder.update_csv_value(
                    "centroid_y",
                    cmy,
                    force_pair=True,
                )
                self.csv_data_holder.data_list.pop("centroid", None)

            hull_area = cv2.contourArea(hull)
            self.csv_data_holder.update_csv_value("hull_area", hull_area)
            self.csv_data_holder.update_csv_value("shape_solidity", area / hull_area)

            x, y, w, h = cv2.boundingRect(obj)
            self.csv_data_holder.update_csv_value("shape_extend", float(area) / (w * h))
            if self.csv_data_holder.has_csv_key("straight_bounding_rectangle"):
                self.csv_data_holder.update_csv_value(
                    "straight_bounding_rectangle_left", x, force_pair=True
                )
                self.csv_data_holder.update_csv_value(
                    "straight_bounding_rectangle_width", w, force_pair=True
                )
                self.csv_data_holder.update_csv_value(
                    "straight_bounding_rectangle_top", y, force_pair=True
                )
                self.csv_data_holder.update_csv_value(
                    "straight_bounding_rectangle_height", h, force_pair=True
                )
                self.csv_data_holder.data_list.pop("straight_bounding_rectangle", None)
                straight_bounding_rec_thickness = 4
            else:
                straight_bounding_rec_thickness = 0

            if self.csv_data_holder.has_csv_key("rotated_bounding_rectangle"):
                (x, y), (w, h), r = cv2.minAreaRect(obj)
                wl = max(w, h)
                hl = min(w, h)
                self.csv_data_holder.update_csv_value(
                    key="rotated_bounding_rectangle_cx", value=x, force_pair=True
                )
                self.csv_data_holder.update_csv_value(
                    key="rotated_bounding_rectangle_cy", value=y, force_pair=True
                )
                self.csv_data_holder.update_csv_value(
                    key="rotated_bounding_rectangle_width", value=wl, force_pair=True
                )
                self.csv_data_holder.update_csv_value(
                    key="rotated_bounding_rectangle_height", value=hl, force_pair=True
                )
                self.csv_data_holder.update_csv_value(
                    key="rotated_bounding_rectangle_rotation",
                    value=r + 180,
                    force_pair=True,
                )
                self.csv_data_holder.data_list.pop("rotated_bounding_rectangle", None)
                bounding_rec_thickness = 4
            else:
                bounding_rec_thickness = 0

            if self.csv_data_holder.has_csv_key("minimum_enclosing_circle"):
                (x, y), radius = cv2.minEnclosingCircle(obj)
                self.csv_data_holder.update_csv_value(
                    "minimum_enclosing_circle_cx", x, force_pair=True
                )
                self.csv_data_holder.update_csv_value(
                    "minimum_enclosing_circle_cy", y, force_pair=True
                )
                self.csv_data_holder.update_csv_value(
                    "minimum_enclosing_circle_radius", radius, force_pair=True
                )
                self.csv_data_holder.data_list.pop("minimum_enclosing_circle", None)
                enclosing_circle_thickness = 4
            else:
                enclosing_circle_thickness = 0

            self.csv_data_holder.update_csv_value("shape_height", height)

            if self.csv_data_holder.has_csv_key("width_data"):
                mask_data = ipc.MaskData(mask)
                _, _, _, min_, max_, avg_, std_ = mask_data.width_quantile_stats(
                    1, 0, tag=0
                )
                self.csv_data_holder.update_csv_value(
                    "shape_width", width, force_pair=True
                )
                self.csv_data_holder.update_csv_value(
                    "shape_width_min", min_, force_pair=True
                )
                self.csv_data_holder.update_csv_value(
                    "shape_width_max", max_, force_pair=True
                )
                self.csv_data_holder.update_csv_value(
                    "shape_width_avg", avg_, force_pair=True
                )
                self.csv_data_holder.update_csv_value(
                    "shape_width_std", std_, force_pair=True
                )
                self.csv_data_holder.data_list.pop("width_data", None)

            if self.store_images:
                # Start with the sure ones
                self.store_image(
                    self.draw_image(
                        src_image=ori_img,
                        src_mask=mask,
                        objects=obj,
                        background="bw",
                        foreground="source",
                        contour_thickness=4,
                        hull_thickness=4
                        if self.csv_data_holder.has_csv_key("hull_area")
                        else 0,
                        width_thickness=4
                        if self.csv_data_holder.has_csv_key("shape_width")
                        else 0,
                        height_thickness=4
                        if self.csv_data_holder.has_csv_key("shape_height")
                        else 0,
                        centroid_width=10
                        if self.csv_data_holder.has_csv_key("centroid_x")
                        else 0,
                    ),
                    "shapes",
                )
                self.store_image(
                    self.draw_image(
                        src_image=mask,
                        src_mask=mask,
                        objects=obj,
                        background="bw",
                        foreground="source",
                        contour_thickness=4,
                        hull_thickness=4
                        if self.csv_data_holder.has_csv_key("hull_area")
                        else 0,
                        width_thickness=4
                        if self.csv_data_holder.has_csv_key("shape_width")
                        else 0,
                        height_thickness=4
                        if self.csv_data_holder.has_csv_key("shape_height")
                        else 0,
                        centroid_width=10
                        if self.csv_data_holder.has_csv_key("centroid_x")
                        else 0,
                    ),
                    "shapes_on_mask",
                )
                # Add new ones
                if (
                    enclosing_circle_thickness
                    + bounding_rec_thickness
                    + straight_bounding_rec_thickness
                    > 0
                ):
                    self.store_image(
                        self.draw_image(
                            src_image=ori_img,
                            src_mask=mask,
                            objects=obj,
                            background="bw",
                            foreground="source",
                            enclosing_circle_thickness=enclosing_circle_thickness,
                            bounding_rec_thickness=bounding_rec_thickness,
                            straight_bounding_rec_thickness=straight_bounding_rec_thickness,
                        ),
                        "more_shapes",
                    )
                    self.store_image(
                        self.draw_image(
                            src_image=mask,
                            src_mask=mask,
                            objects=obj,
                            background="bw",
                            foreground="source",
                            enclosing_circle_thickness=enclosing_circle_thickness,
                            bounding_rec_thickness=bounding_rec_thickness,
                            straight_bounding_rec_thickness=straight_bounding_rec_thickness,
                        ),
                        "more_shapes_on_mask",
                    )

            # handle width quantiles
            keys = [k for k in self.csv_data_holder.data_list]
            for k in keys:
                if "quantile_width" in k:
                    _, kind, n = k.split("_")
                    n = int(n)
                    if kind.lower() == "width":
                        msk_dt = ipc.MaskData(mask)
                        qtl_img = np.zeros_like(mask)
                        qtl_img = np.dstack((qtl_img, qtl_img, qtl_img))
                        for i in range(n):
                            (
                                total_,
                                hull_,
                                solidity_,
                                min_,
                                max_,
                                avg_,
                                std_,
                            ) = msk_dt.width_quantile_stats(n, i, tag=i)
                            self.csv_data_holder.update_csv_value(
                                f"quantile_width_{i + 1}_{n}_area", total_, True
                            )
                            self.csv_data_holder.update_csv_value(
                                f"quantile_width_{i + 1}_{n}_hull", hull_, True
                            )
                            self.csv_data_holder.update_csv_value(
                                f"quantile_width_{i + 1}_{n}_solidity", solidity_, True
                            )
                            self.csv_data_holder.update_csv_value(
                                f"quantile_width_{i + 1}_{n}_min_{kind}", min_, True
                            )
                            self.csv_data_holder.update_csv_value(
                                f"quantile_width_{i + 1}_{n}_max_{kind}", max_, True
                            )
                            self.csv_data_holder.update_csv_value(
                                f"quantile_width_{i + 1}_{n}_avg_{kind}", avg_, True
                            )
                            self.csv_data_holder.update_csv_value(
                                f"quantile_width_{i + 1}_{n}_std_{kind}", std_, True
                            )
                            p_qt_msk = msk_dt.height_quantile_mask(
                                total=n, index=i, colour=int((i + 1) / (n + 1) * 255)
                            )
                            qtl_img = cv2.bitwise_or(
                                qtl_img,
                                np.dstack(
                                    (np.zeros_like(mask), p_qt_msk, np.zeros_like(mask))
                                ),
                            )
                        self.store_image(qtl_img, f"quantiles_width_{n}")

                        self.csv_data_holder.data_list.pop(k, None)
        else:
            pass

        return True

    # @time_method
    def analyze_bound(
        self,
        img: Any,
        mask: Any,
        line_position: int = -1,
        pseudo_color_channel: str = " v",
    ):
        """User-input boundary line tool
        Inputs:
        img             = image
        mask            = mask made from selected contours
        line_position   = position of boundary line (a value of 0 would draw the line through the bottom of the image)
        :param pseudo_color_channel: str
        :param mask: numpy array, mask made from selected contours
        :param line_position: int
        :return success: bool
        """
        if (line_position < 0) or not self.csv_data_holder.has_csv_key("bound_data"):
            self.csv_data_holder.data_list.pop("bound_data", None)
            return True

        self.csv_data_holder.data_list.pop("bound_data", None)

        roi_top = RectangleRegion(
            left=0, width=self.width, top=0, height=line_position, name="roi_top"
        )
        roi_bottom = RectangleRegion(
            left=0,
            width=self.width,
            top=line_position,
            height=self.height - line_position,
            name="roi_bottom",
        )

        mask_top = self.crop_to_roi(img=mask, roi=roi_top)
        mask_bottom = self.crop_to_roi(img=mask, roi=roi_bottom)

        mask_data_top = ipc.MaskData(mask_top)
        mask_data_bottom = ipc.MaskData(mask_bottom)

        area_ = self.csv_data_holder.retrieve_csv_value("area")
        if area_ is None:
            mask_data = ipc.MaskData(mask)
            area_ = mask_data.area

        if area_:
            try:
                t_height = mask_data_top.mask.shape[0] - mask_data_top.top_index
                b_height = mask_data_bottom.height

                self.csv_data_holder.update_csv_value(
                    "above_bound_height", t_height, force_pair=True
                )
                self.csv_data_holder.update_csv_value(
                    "above_bound_area", mask_data_top.area, force_pair=True
                )
                self.csv_data_holder.update_csv_value(
                    "above_bound_percent_area",
                    mask_data_top.area / area_ * 100,
                    force_pair=True,
                )

                self.csv_data_holder.update_csv_value(
                    "below_bound_height", b_height, force_pair=True
                )
                self.csv_data_holder.update_csv_value(
                    "below_bound_area", mask_data_bottom.area, force_pair=True
                )
                self.csv_data_holder.update_csv_value(
                    "below_bound_percent_area",
                    mask_data_bottom.area / area_ * 100,
                    force_pair=True,
                )

                self.csv_data_holder.update_csv_value(
                    "shape_height", t_height + b_height, force_pair=True
                )

                if self.store_images:
                    c = self.get_channel(src_img=img, channel=pseudo_color_channel)
                    background_img = np.dstack((c, c, c))
                    p_img = self.draw_image(
                        src_image=background_img,
                        channel=pseudo_color_channel,
                        src_mask=mask,
                        foreground="false_colour",
                        background="source",
                        normalize_before=True,
                        color_map=cv2.COLORMAP_SUMMER,
                        roi=roi_top,
                        centroid_width=10,
                        height_thickness=4,
                        width_thickness=4,
                    )
                    p_img = self.draw_image(
                        src_image=p_img,
                        channel=pseudo_color_channel,
                        src_mask=mask,
                        foreground="false_colour",
                        background="source",
                        normalize_before=False,
                        color_map=cv2.COLORMAP_HOT,
                        roi=roi_bottom,
                        centroid_width=10,
                        height_thickness=4,
                        width_thickness=4,
                    )
                    cv2.line(
                        p_img,
                        (0, line_position),
                        (self.width, line_position),
                        ipc.C_RED,
                        3,
                    )
                    self.store_image(p_img, "bounds")
            except Exception as e:
                logger.exception(f'Failed to analyse bounds "{repr(e)}"')
                return False
            else:
                return True
        else:
            return False

    @staticmethod
    def apply_mask(img: Any, mask: Any, background_color: Any):
        """
        Apply white image mask to image with a selected background color

        Inputs:
            * img              = image object, color(RGB)
            * mask             = image object, binary (black background with white object)
            * background_color = color tuple or white or black

        Returns:
        masked_img = masked image

        :param img: numpy array
        :param mask: numpy array
        :param background_color: tuple or string
        :return masked_img: numpy array
        """

        if background_color.lower() == "white":
            background_color = (255, 255, 255)
        elif background_color.lower() == "black":
            background_color = (0, 0, 0)

        rem_img = cv2.bitwise_and(img, img, mask=mask)
        background = np.full(img.shape, background_color, np.uint8)
        background = cv2.bitwise_and(background, background, mask=255 - mask)
        return cv2.bitwise_or(background, rem_img)

    def analyse_chlorophyll(self, img: Any, mask: Any):
        """
        Extract chlorophyll data
        """
        if self.csv_data_holder.has_csv_key(
            "chlorophyll_mean"
        ) or self.csv_data_holder.has_csv_key("chlorophyll_std_dev"):
            try:
                b, g, r = cv2.split(cv2.bitwise_and(img, img, mask=mask))
                c = np.exp(
                    (-0.0280 * r * 1.04938271604938)
                    + (0.0190 * g * 1.04938271604938)
                    + (-0.0030 * b * 1.04115226337449)
                    + 5.780
                )
                if self.store_images:
                    calc_img = cv2.bitwise_and(c, c, mask=mask)
                    calc_img = (
                        (calc_img - calc_img.min())
                        / (calc_img.max() - calc_img.min())
                        * 255
                    ).astype(np.uint8)
                    pseudo = self.draw_image(
                        src_image=img,
                        channel=calc_img,
                        background="source",
                        foreground="false_colour",
                        color_map=cv2.COLORMAP_RAINBOW,
                    )
                    self.store_image(pseudo, "pseudo_chlorophyll_on_img")
                    self.store_image(calc_img, "chlorophyll_calculated")
                tmp_tuple = cv2.meanStdDev(
                    c.reshape(c.shape[1] * c.shape[0]),
                    mask=mask.reshape(mask.shape[1] * mask.shape[0]),
                )
                self.csv_data_holder.update_csv_value(
                    "chlorophyll_mean", tmp_tuple[0][0][0]
                )
                self.csv_data_holder.update_csv_value(
                    "chlorophyll_std_dev", tmp_tuple[1][0][0]
                )
            except Exception as e:
                return False
            else:
                return True
        else:
            return True

    # @time_method
    def analyze_color(
        self,
        img: Any,
        mask: Any,
        pseudo_color_channel: str = "v",
        pseudo_color_map: int = 2,
        pseudo_bkg: str = "bw",
    ):
        """Analyze the color properties of an image object
        Inputs:
        img              = image
        mask             = mask made from selected contours
        debug            = None, print, or plot. Print = save to file, Plot = print to screen.
        hist_plot_type   = 'None', 'all', 'rgb','lab' or 'hsv'
        color_slice_type = 'None', 'rgb', 'hsv' or 'lab'
        pseudo_channel   = 'None', 'l', 'm' (green-magenta), 'y' (blue-yellow), h','s', or 'v',
                           creates pseudo colored image based on the specified channel
        pseudo_bkg       = 'img' => channel image,
                           'white' => white background image,
                           'both' => both img and white options
        :param pseudo_color_map:
        :param img: numpy array
        :param mask: numpy array
        :param pseudo_color_channel: str
        :param pseudo_bkg: str
        """

        if not (
            self.csv_data_holder.has_csv_key("color_std_dev")
            or self.csv_data_holder.has_csv_key("color_mean")
        ):
            return True

        masked = cv2.bitwise_and(img, img, mask=mask)

        channel_data = {}
        for c in self.file_handler.channels_data:
            if c[0] == "chla":
                continue
            channel_data[c[1]] = dict(
                color_space=c[0],
                channel_name=c[1],
                data=self.get_channel(src_img=masked, channel=c[1]),
                graph_color=ipc.channel_color(c[1]),
            )

        self.csv_data_holder.update_csv_value("hist_bins", f"{256}")

        for k, v in channel_data.items():
            if v["data"] is None:
                logger.warning(f"Missing channel {ipc.get_hr_channel_name(k)}")
                continue
            tmp_tuple = cv2.meanStdDev(
                src=v["data"].reshape(v["data"].shape[1] * v["data"].shape[0]),
                mask=mask.reshape(mask.shape[1] * mask.shape[0]),
            )
            v["hist"] = cv2.calcHist([v["data"]], [0], mask, [256], [0, (256 - 1)])
            seed_ = f'{v["color_space"]}_{k}'
            self.csv_data_holder.update_csv_value(
                key=f"{seed_}_std_dev",
                value=tmp_tuple[1][0][0],
                force_pair=self.csv_data_holder.has_csv_key("color_std_dev"),
            )
            self.csv_data_holder.update_csv_value(
                key=f"{seed_}_mean",
                value=tmp_tuple[0][0][0],
                force_pair=self.csv_data_holder.has_csv_key("color_mean"),
            )

        # Remove consumed keys
        if self.csv_data_holder.has_csv_key("color_std_dev"):
            self.csv_data_holder.data_list.pop("color_std_dev", None)
        if self.csv_data_holder.has_csv_key("color_mean"):
            self.csv_data_holder.data_list.pop("color_mean", None)

        # Create Histogram Plot
        if self.store_images:
            fig = plt.figure(figsize=(10, 10), dpi=100)
            for k, v in channel_data.items():
                if v["data"] is None:
                    continue
                plt.plot(v["hist"], label=v["channel_name"])
                plt.xlim([0, 256 - 1])
                plt.legend()

            if self.write_images != "print":
                fig.canvas.draw()
                # Now we can save it to a numpy array.
                data = np.fromstring(fig.canvas.tostring_rgb(), dtype=np.uint8, sep="")
                data = data.reshape(fig.canvas.get_width_height()[::-1] + (3,))
                self.store_image(data, "histogram")
            elif self.write_images != "plot":
                plt.axis("off")
                plt.title("histogram")
                fig.tight_layout()
                plt.show()

            plt.clf()
            plt.close()

            pseudo_colour = self.draw_image(
                src_image=img,
                channel=pseudo_color_channel,
                color_map=pseudo_color_map,
                foreground="false_colour",
                src_mask=mask,
                background=pseudo_bkg,
            )
            self.store_image(pseudo_colour, "pseudo_on")

        # handle color quantiles
        keys = [k for k in self.csv_data_holder.data_list]
        for k in keys:
            if "quantile_color" in k:
                *_, n = k.split("_")
                n = int(n)
                for c, v in channel_data.items():
                    if v["data"] is None:
                        logger.warning(
                            f'Missing channel {v["color_space"]}, {v["channel_name"]}'
                        )
                        continue
                    seed_ = f'{v["color_space"]}_{c}'
                    hist = cv2.calcHist([v["data"]], [0], mask, [n], [0, (256 - 1)])
                    total_pixels = np.sum(hist)
                    for i, qtt in enumerate([hist_val[0] for hist_val in hist]):
                        self.csv_data_holder.update_csv_value(
                            f"quantile_color_{seed_}_{i + 1}_{n}_percent",
                            qtt / total_pixels * 100,
                            True,
                        )
                self.csv_data_holder.data_list.pop(k, None)

        return True

    def fill_mask_holes(self, src_mask: Any, dbg_text: str = ""):
        """Fills holes inside mask using floodfill method

        Arguments:
            src_mask {numpy array} -- Source mask
            dbg_text {str} -- debug string for storing step images

        Returns:
            numpy array -- Filled image
        """

        im_floodfill = src_mask.copy()

        # Mask used to flood filling.
        # Notice the size needs to be 2 pixels than the image.
        h, w = src_mask.shape[:2]
        mask = np.zeros((h + 2, w + 2), np.uint8)

        # Floodfill from point (0, 0)
        cv2.floodFill(im_floodfill, mask, (0, 0), 255)
        if dbg_text:
            self.store_image(im_floodfill, "{}_floodfill".format(dbg_text))

        # Invert floodfilled image
        im_floodfill_inv = cv2.bitwise_not(im_floodfill)
        if dbg_text:
            self.store_image(im_floodfill_inv, "{}_floodfill_inv".format(dbg_text))

        # Combine the two images to get the foreground.
        mask_leafs = src_mask | im_floodfill_inv
        if dbg_text:
            self.store_image(mask_leafs, "{}_mask_filled".format(dbg_text))

        return mask_leafs

    @staticmethod
    def get_distance_data(hull, origin, max_dist):
        """
        Calculates distances from origin to contour barycenter,
        also returns surface data
        :param hull:
        :param origin:
        :param max_dist:
        :return: dict
        """
        m = cv2.moments(hull)
        if m["m00"] != 0:
            cx_ = int(m["m10"] / m["m00"])
            cy_ = int(m["m01"] / m["m00"])
            dist_ = math.sqrt(math.pow(cx_ - origin.x, 2) + math.pow(cy_ - origin.y, 2))
            dist_scaled_inverted = 1 - dist_ / max_dist
            res_ = dict(
                dist=dist_,
                cx=cx_,
                cy=cy_,
                dist_scaled_inverted=dist_scaled_inverted,
                area=cv2.contourArea(hull),
                scaled_area=cv2.contourArea(hull) * math.pow(dist_scaled_inverted, 2),
            )
        else:
            res_ = dict(dist=0, cx=0, cy=0, dist_scaled_inverted=0, area=0, scaled_area=0)
        return res_

    @staticmethod
    def contours_min_distance(cnt_a, cnt_b):
        """Returns minimal distance between 2 contours.
        Possible returns
            * 0: The two contours touch or intersect one another
            * > 0: The two contours are separated
        """
        min_dist = None
        for pt in cnt_a:
            cnt_point = Point(pt[0][0], pt[0][1])
            cur_dist = cv2.pointPolygonTest(cnt_b, (cnt_point.x, cnt_point.y), True)
            if cur_dist >= 0:
                return 0
            else:
                if min_dist is None:
                    min_dist = abs(cur_dist)
                elif abs(cur_dist) < min_dist:
                    min_dist = abs(cur_dist)
        return min_dist

    def check_hull(
        self,
        mask,
        cmp_hull,
        master_hull,
        tolerance_area=None,
        tolerance_distance=None,
        dilation_iter=0,
        keep_safe_close_enough=False,
        keep_safe_big_enough=False,
        safe_roi=None,
        area_override_size=0,
    ):
        """Compares to hulls

        Arguments:
            cmp_hull {numpy array} -- hull to be compared
            master_hull {numpy array} -- master hull

        Returns:
            int -- 1 if overlaps, 0 if fully inside, -1 if fully outside
        """

        def last_chance_(test_cnt):
            roi = self.get_roi(roi_name=safe_roi, exists_only=True)

            ok_size = (tolerance_area is not None) and (
                (tolerance_area < 0) or cv2.contourArea(test_cnt) >= tolerance_area
            )
            if ok_size and keep_safe_big_enough and roi.intersects_contour(test_cnt):
                return KLC_PROTECTED_SIZE_OK

            ok_dist = (tolerance_distance is not None) and (
                tolerance_distance < 0 or min_dist <= tolerance_distance
            )
            if ok_dist and keep_safe_close_enough and roi.intersects_contour(test_cnt):
                return KLC_PROTECTED_DIST_OK

            if ok_size and ok_dist:
                return KLC_OK_TOLERANCE
            elif (
                area_override_size > 0 and cv2.contourArea(test_cnt) > area_override_size
            ):
                return KLC_BIG_ENOUGH_TO_IGNORE_DISTANCE
            elif not ok_size and not ok_dist:
                return KLC_OUTSIDE
            elif not ok_size:
                return KLC_NO_BIG_ENOUGH
            elif not ok_dist:
                return KLC_NO_CLOSE_ENOUGH

        # Check hull intersection
        if (dilation_iter < 0) and (
            cv2.contourArea(cmp_hull) > cv2.contourArea(master_hull)
        ):
            cmp_img = np.full(mask.shape, 0, np.uint8)
            cv2.drawContours(cmp_img, [cmp_hull], -1, 255, -1)
            master_img = np.full(mask.shape, 0, np.uint8)
            cv2.drawContours(master_img, [master_hull], -1, 255, -1)
            test_img = cv2.bitwise_and(cmp_img, cmp_img, mask=master_img)
            if np.array_equal(test_img, cmp_img):
                return KLC_FULLY_INSIDE
            _, max_val, _, _ = cv2.minMaxLoc(test_img)
            nz_cmp_img = np.nonzero(cmp_img)
            nz_test_img = np.nonzero(test_img)
            if (
                (max_val > 0)
                and nz_cmp_img
                and nz_test_img
                and (len(nz_cmp_img[0]) > len(nz_test_img[0]))
            ):
                return KLC_OVERLAPS

        # Check point to point
        is_inside = False
        is_outside = False
        is_protected = False
        min_dist = mask.shape[0] * mask.shape[1]
        for pt in cmp_hull:
            cnt_point = Point(pt[0][0], pt[0][1])
            cur_dist = cv2.pointPolygonTest(master_hull, (cnt_point.x, cnt_point.y), True)
            if cur_dist >= 0:
                is_inside = True
            else:
                if abs(cur_dist) < min_dist:
                    min_dist = abs(cur_dist)
                is_outside = True
            if (is_inside and is_outside) or is_protected:
                break
        if is_inside and is_outside:
            return KLC_OVERLAPS
        elif is_inside:
            return KLC_FULLY_INSIDE
        else:
            return last_chance_(cmp_hull)

    # @time_method
    def keep_biggest_contour(self, **kwargs):
        """
        Keep contours inside the beggest contour

        Keyword Arguments:
            * src_image: Source image, required=False, default source
            * src_mask: Mask to clean, required=False, default mask
            * dilation_iter: if positive number of dilations, if negative number of erosions, required=False, default=0
            * roi: initial ROI, required=False, default=full image
            * root_position: if initial ROI exists, position to start contour, required=False, default=BOTTOM_CENTER
            * trusted_safe_zone: if true all contours in zones tagged safe will be accepted, required=False, default=False
        :return: : Filtered mask
        """
        src_image = kwargs.get("src_image", self.current_image)
        src_mask = kwargs.get("src_mask", self.mask)
        if (src_image is None) or (src_mask is None):
            logger.error(
                f'Source & mask are mandatory for keep linked contours "{str(self)}'
            )
            return None
        dilation_iter = kwargs.get("dilation_iter", 0)
        roi = kwargs.get("roi", self.get_roi("main_roi"))
        root_position = kwargs.get("root_position", "BOTTOM_CENTER")
        trusted_safe_zone = kwargs.get("trusted_safe_zone", False)

        safe_roi_name = kwargs.get("safe_roi_name")
        keep_safe_close_enough = kwargs.get("keep_safe_close_enough")
        keep_safe_big_enough = kwargs.get("keep_safe_big_enough")

        if dilation_iter > 0:
            dil_mask = self.dilate(src_mask, proc_times=dilation_iter)
        elif dilation_iter < 0:
            dil_mask = self.erode(src_mask, proc_times=abs(dilation_iter))
        else:
            dil_mask = src_mask.copy()
        self.store_image(dil_mask, "dil_mask")

        contours = ipc.get_contours(
            mask=dil_mask, retrieve_mode=cv2.RETR_LIST, method=cv2.CHAIN_APPROX_SIMPLE
        )
        self.store_image(
            cv2.drawContours(dil_mask.copy(), contours, -1, ipc.C_LIME, 2, 8),
            "img_dilated_cnt",
        )

        self.store_image(
            cv2.drawContours(src_image.copy(), contours, -1, ipc.C_GREEN, 2, 8),
            "src_img_with_cnt",
        )

        # Transform all contours into approximations
        hulls = []
        eps = 0.001
        for cnt in contours:
            hulls.append(cv2.approxPolyDP(cnt, eps * cv2.arcLength(cnt, True), True))
        hull_img = src_image.copy()
        cv2.drawContours(hull_img, hulls, -1, (0, 255, 0), 4)
        self.store_image(hull_img, "src_img_with_cnt_approx_{}".format(eps))

        # Find the largest hull
        main_hull = hulls[0]
        if roi:  # There's a ROI, lets keep the biggest hull close to its root
            roi_root = roi.point_at_position(root_position, True)
            if root_position == "MIDDLE_CENTER":
                dist_max = roi.radius
            else:
                dist_max = math.sqrt(roi.width ** 2 + roi.height ** 2)

            hull_img = src_image.copy()
            max_area = 0
            for hull in hulls:
                morph_dict = self.get_distance_data(hull, roi_root, dist_max)
                cl_cmp = morph_dict["dist_scaled_inverted"] * 255
                cv2.drawContours(
                    hull_img, [hull], 0, (0, int(cl_cmp), int((1 - cl_cmp) * 255)), 2
                )
                if morph_dict["scaled_area"] > max_area:
                    max_area = morph_dict["scaled_area"]
                    main_hull = hull

            self.store_image(hull_img, "src_img_with_cnt_distance_map")
        else:  # No ROI defined
            max_area = cv2.contourArea(hulls[0])
            for i, hull in enumerate(hulls):
                cur_area = cv2.contourArea(hull)
                if cur_area > max_area:
                    max_area = cur_area
                    main_hull = hull

        # At this point we have the zone were the contours are allowed to be
        contours = ipc.get_contours(
            mask=src_mask, retrieve_mode=cv2.RETR_LIST, method=cv2.CHAIN_APPROX_SIMPLE
        )
        for cnt in contours:
            hull = cv2.approxPolyDP(cnt, eps * cv2.arcLength(cnt, True), True)
            res = self.check_hull(
                mask=src_mask,
                cmp_hull=hull,
                master_hull=main_hull,
                dilation_iter=dilation_iter,
                keep_safe_big_enough=keep_safe_big_enough,
                keep_safe_close_enough=keep_safe_close_enough,
                safe_roi=safe_roi_name,
            )
            if res in [
                KLC_FULLY_INSIDE,
                KLC_OVERLAPS,
                KLC_PROTECTED_DIST_OK,
                KLC_PROTECTED_SIZE_OK,
                KLC_OK_TOLERANCE,
                KLC_BIG_ENOUGH_TO_IGNORE_DISTANCE,
            ]:
                cv2.drawContours(src_image, [cnt], 0, (0, 255, 0), 2)
            else:
                cv2.drawContours(src_image, [cnt], 0, (0, 0, 255), 2)
                cv2.drawContours(src_mask, [cnt], 0, (0, 0, 0), -1)

        self.store_image(src_image, "img_wth_tagged_cnt", force_store=True)
        self.store_image(src_mask, "mask_lnk_cnts")

        return src_mask

    # @time_method
    def keep_linked_contours(self, **kwargs) -> object:
        """
        Keep contours only linked to the root position

        Keyword Arguments:
            * src_image: Source image, required=False, default source
            * src_mask: Mask to clean, required=False, default mask
            * dilation_iter: if positive number of dilations, if negative number of erosions, required=False, default=0
            * tolerance_distance: max distance allowed between tested contour and current blob, required=False, default=0
            * tolerance_area: min contour area accepted, required=False, default=0
            * roi: initial ROI, required=False, default=full image
            * root_position: if initial ROI exists, position to start contour, required=False, default=BOTTOM_CENTER
            * trusted_safe_zone: if true all contours in zones tagged safe will be accepted, required=False, default=False
            * area_override_size: over this area all contours will be accepted as long as they are in a safe-ish or better region
            * delete_all_bellow: all contours smaller than value will be deleted
        :return: : Filtered mask
        """
        src_image = kwargs.get("src_image", self.current_image)
        src_mask = kwargs.get("src_mask", self.mask)
        if (src_image is None) or (src_mask is None):
            logger.error(
                f'Source & mask are mandatory for keep linked contours "{str(self)}',
            )
            return None
        dilation_iter = kwargs.get("dilation_iter", 0)
        tolerance_distance = kwargs.get("tolerance_distance", 0)
        tolerance_area = kwargs.get("tolerance_area", 0)
        roi: AbstractRegion = kwargs.get("roi", self.get_roi("main_roi"))
        root_position = kwargs.get("root_position", "BOTTOM_CENTER")
        trusted_safe_zone = kwargs.get("trusted_safe_zone", False)
        area_override_size = kwargs.get("area_override_size", 0)
        delete_all_bellow = kwargs.get("delete_all_bellow", 0)

        safe_roi_name = kwargs.get("safe_roi_name")
        keep_safe_close_enough = kwargs.get("keep_safe_close_enough")
        keep_safe_big_enough = kwargs.get("keep_safe_big_enough")

        if tolerance_distance != int(tolerance_distance) or tolerance_area != int(
            tolerance_area
        ):
            raise NotImplementedError("Only integers allowed")

        self.store_image(src_mask, "raw__mask")
        # Delete all small contours
        if delete_all_bellow > 0:
            fnt = (cv2.FONT_HERSHEY_SIMPLEX, 0.6)
            contours = ipc.get_contours(
                mask=src_mask,
                retrieve_mode=cv2.RETR_LIST,
                method=cv2.CHAIN_APPROX_SIMPLE,
            )
            small_img = src_mask.copy()
            small_img = np.dstack((small_img, small_img, small_img))
            for cnt in contours:
                area_ = cv2.contourArea(cnt)
                if area_ < delete_all_bellow:
                    # Delete
                    cv2.drawContours(src_mask, [cnt], 0, (0, 0, 0), -1)
                    # Print debug image
                    x, y, w, h = cv2.boundingRect(cnt)
                    x += w // 2 - 10
                    y += h // 2
                    cv2.drawContours(small_img, [cnt], -1, ipc.C_RED, -1)
                    cv2.putText(
                        small_img,
                        f"Area: {area_}",
                        (x, y),
                        fnt[0],
                        fnt[1],
                        ipc.C_FUCHSIA,
                        2,
                    )
                else:
                    cv2.drawContours(small_img, [cnt], -1, ipc.C_GREEN, -1)
            self.store_image(small_img, "small_removed_mask")

        if dilation_iter > 0:
            dil_mask = self.dilate(src_mask, proc_times=dilation_iter)
        elif dilation_iter < 0:
            dil_mask = self.erode(src_mask, proc_times=abs(dilation_iter))
        else:
            dil_mask = src_mask.copy()
        self.store_image(dil_mask, "dil_mask")
        contours = ipc.get_contours(
            mask=dil_mask, retrieve_mode=cv2.RETR_LIST, method=cv2.CHAIN_APPROX_SIMPLE
        )
        self.store_image(
            cv2.drawContours(dil_mask.copy(), contours, -1, ipc.C_LIME, 2, 8),
            "img_dilated_cnt",
        )

        img_cnt = cv2.drawContours(src_image.copy(), contours, -1, ipc.C_GREEN, 2, 8)
        self.store_image(img_cnt, "src_img_with_cnt")

        # Transform all contours into approximations
        hulls = []
        eps = 0.001
        for cnt in contours:
            hulls.append(cv2.approxPolyDP(cnt, eps * cv2.arcLength(cnt, True), True))
        hull_img = src_image.copy()
        cv2.drawContours(hull_img, hulls, -1, (0, 255, 0), 4)
        self.store_image(hull_img, "src_img_with_cnt_approx_{}".format(eps))

        if len(hulls) == 0:
            return np.zeros_like(src_mask)

        # Find the largest hull
        big_hull = hulls[0]
        big_idx = 0
        if roi:  # There's a ROI, lets keep the biggest hull close to its root
            roi_root = roi.point_at_position(root_position, True)
            if root_position == "MIDDLE_CENTER":
                dist_max = roi.radius
            else:
                dist_max = math.sqrt(roi.width ** 2 + roi.height ** 2)

            hull_img = src_image.copy()
            max_area = 0
            for i, hull in enumerate(hulls):

                morph_dict = self.get_distance_data(hull, roi_root, dist_max)
                # cnt_data.append(morph_dict)

                cv2.drawContours(
                    hull_img,
                    [hull],
                    0,
                    (
                        0,
                        int(morph_dict["dist_scaled_inverted"] * 255),
                        int((1 - morph_dict["dist_scaled_inverted"]) * 255),
                    ),
                    2,
                )
                if morph_dict["scaled_area"] > max_area:
                    max_area = morph_dict["scaled_area"]
                    big_hull = hull
                    big_idx = i

            self.store_image(hull_img, "src_img_with_cnt_distance_map")
        else:  # No ROI defined
            max_area = cv2.contourArea(hulls[0])
            for i, hull in enumerate(hulls):
                cur_area = cv2.contourArea(hull)
                if cur_area > max_area:
                    max_area = cur_area
                    big_hull = hull
                    big_idx = i
        # parse all hulls and switch
        good_hulls = [hulls.pop(big_idx)]
        unknown_hulls = []
        hull_img = src_image.copy()
        cv2.drawContours(hull_img, [good_hulls[0]], 0, (0, 255, 0), 4)

        while len(hulls) > 0:
            hull = hulls.pop()
            res = self.check_hull(
                mask=src_mask,
                cmp_hull=hull,
                master_hull=big_hull,
                tolerance_area=tolerance_area,
                tolerance_distance=tolerance_distance,
                dilation_iter=dilation_iter,
                keep_safe_big_enough=keep_safe_big_enough,
                keep_safe_close_enough=keep_safe_close_enough,
                safe_roi=safe_roi_name,
                area_override_size=area_override_size,
            )
            cv2.drawContours(hull_img, [hull], 0, res["color"], 2)
            if res == KLC_FULLY_INSIDE:
                pass
            elif res in [
                KLC_OVERLAPS,
                KLC_PROTECTED_DIST_OK,
                KLC_PROTECTED_SIZE_OK,
                KLC_OK_TOLERANCE,
                KLC_BIG_ENOUGH_TO_IGNORE_DISTANCE,
            ]:
                good_hulls.append(hull)
            else:
                unknown_hulls.append(hull)

        safe_roi = self.get_roi("safe", exists_only=True)
        if safe_roi is not None:
            hull_img = safe_roi.draw_to(dst_img=hull_img, line_width=self.width // 200)
        self.store_image(hull_img, "src_img_with_cnt_as_hull_init")

        hull_img = src_image.copy()
        cv2.drawContours(hull_img, good_hulls, -1, KLC_FULLY_INSIDE["color"], 4)
        self.store_image(hull_img, "init_good_hulls")
        # Try to aggregate unknown hulls to good hulls
        stable = False
        while not stable:
            stable = True
            i = 0
            iter_count = 1
            hull_img = src_image.copy()
            while i < len(unknown_hulls):
                hull = unknown_hulls[i]
                res = KLC_OUTSIDE
                for good_hull in good_hulls:
                    res = self.check_hull(
                        mask=src_mask,
                        cmp_hull=hull,
                        master_hull=good_hull,
                        tolerance_area=tolerance_area,
                        tolerance_distance=tolerance_distance,
                        dilation_iter=dilation_iter,
                        keep_safe_big_enough=keep_safe_big_enough,
                        keep_safe_close_enough=keep_safe_close_enough,
                        safe_roi=safe_roi_name,
                        area_override_size=area_override_size,
                    )
                    if res == KLC_FULLY_INSIDE:
                        del unknown_hulls[i]
                        stable = False
                        break
                    elif res in [
                        KLC_PROTECTED_SIZE_OK,
                        KLC_PROTECTED_DIST_OK,
                        KLC_OVERLAPS,
                        KLC_OK_TOLERANCE,
                        KLC_BIG_ENOUGH_TO_IGNORE_DISTANCE,
                    ]:
                        draw_hull = unknown_hulls.pop(i)
                        good_hulls.append(draw_hull)
                        cv2.drawContours(hull_img, [draw_hull], -1, res["color"], 2)
                        stable = False
                        break
                    elif res in [KLC_OUTSIDE, KLC_NO_BIG_ENOUGH, KLC_NO_CLOSE_ENOUGH]:
                        pass
                    # else:
                    #     raise
                if res in [KLC_OUTSIDE, KLC_NO_BIG_ENOUGH, KLC_NO_CLOSE_ENOUGH]:
                    i += 1
                if isinstance(res, dict):
                    cv2.drawContours(
                        hull_img, [hull], -1, res.get("color", ipc.C_CABIN_BLUE), 2
                    )
                else:
                    logger.error(f"Unknown check_hull res {str(res)}")
            self.store_image(hull_img, f"src_img_with_cnt_after_agg_iter_{iter_count}")
            iter_count += 1

        hull_img = src_image.copy()
        fnt = (cv2.FONT_HERSHEY_SIMPLEX, 0.6)
        for gh in good_hulls:
            x, y, w, h = cv2.boundingRect(gh)
            x += w // 2 - 10
            y += h // 2
            cv2.drawContours(hull_img, [gh], -1, KLC_FULLY_INSIDE["color"], 8)
        for uh in unknown_hulls:
            x, y, w, h = cv2.boundingRect(uh)
            x += w // 2 - 10
            y += h // 2
            cv2.drawContours(hull_img, [uh], -1, KLC_OUTSIDE["color"], 8)
        for gh in good_hulls:
            area_ = cv2.contourArea(gh)
            if area_ > 0:
                x, y, w, h = cv2.boundingRect(gh)
                x += w // 2 - 10
                y += h // 2
                cv2.putText(
                    hull_img, f"{area_}", (x, y), fnt[0], fnt[1], (255, 255, 0), 2
                )
        for uh in unknown_hulls:
            area_ = cv2.contourArea(uh)
            if area_ > 0:
                x, y, w, h = cv2.boundingRect(uh)
                x += w // 2 - 10
                y += h // 2
                cv2.putText(
                    hull_img, f"{area_}", (x, y), fnt[0], fnt[1], (255, 0, 255), 2
                )
        self.store_image(
            image=hull_img,
            text="src_img_with_cnt_after_agg_iter_last",
            force_store=True,
        )

        # At this point we have the zone were the contours are allowed to be
        contours = ipc.get_contours(
            mask=src_mask, retrieve_mode=cv2.RETR_LIST, method=cv2.CHAIN_APPROX_SIMPLE
        )
        for cnt in contours:
            hull = cv2.approxPolyDP(cnt, eps * cv2.arcLength(cnt, True), True)
            is_good_one = False
            for good_hull in good_hulls:
                res = self.check_hull(
                    mask=src_mask,
                    cmp_hull=hull,
                    master_hull=good_hull,
                    tolerance_area=tolerance_area,
                    tolerance_distance=tolerance_distance,
                    dilation_iter=dilation_iter,
                    keep_safe_big_enough=keep_safe_big_enough,
                    keep_safe_close_enough=keep_safe_close_enough,
                    safe_roi=safe_roi_name,
                    area_override_size=area_override_size,
                )
                if res in [
                    KLC_FULLY_INSIDE,
                    KLC_OVERLAPS,
                    KLC_PROTECTED_DIST_OK,
                    KLC_PROTECTED_SIZE_OK,
                    KLC_OK_TOLERANCE,
                    KLC_BIG_ENOUGH_TO_IGNORE_DISTANCE,
                ]:
                    is_good_one = True
                    break

            if is_good_one:
                cv2.drawContours(src_image, [cnt], 0, (0, 255, 0), 2)
            else:
                cv2.drawContours(src_image, [cnt], 0, (0, 0, 255), 2)
                cv2.drawContours(src_mask, [cnt], 0, (0, 0, 0), -1)

        self.store_image(src_image, "img_wth_tagged_cnt")
        self.store_image(src_mask, "mask_lnk_cnts")

        return src_mask

    # @time_method
    def prepare_analysis(self, img: Any, mask: Any):
        """Builds objects and mask needed for analysis

        Arguments:
            img {numpy array} -- source image
            mask {numpy array} -- final mask from

        Returns:
            list -- contour objects
            numpy array -- mask
        """

        # Identify objects
        id_objects, obj_hierarchy = ipc.get_contours_and_hierarchy(
            mask=mask, retrieve_mode=cv2.RETR_TREE, method=cv2.CHAIN_APPROX_NONE
        )

        if self.store_images:
            ori_img = np.copy(img)
            for i, _ in enumerate(id_objects):
                cv2.drawContours(
                    ori_img,
                    id_objects,
                    i,
                    (255, 0, 0),
                    -1,
                    lineType=8,
                    hierarchy=obj_hierarchy,
                )
                cv2.drawContours(
                    ori_img,
                    id_objects,
                    i,
                    (0, 0, 255),
                    2,
                    lineType=8,
                    hierarchy=obj_hierarchy,
                )
            self.store_image(ori_img, "masked_whole_cnts")

        # Object combine kept objects
        obj, msk = self.object_composition(img, id_objects, obj_hierarchy)

        return obj, msk

    # @time_method
    def analyse(
        self,
        img: Any,
        mask: Any,
        pseudo_color_channel: str,
        pseudo_color_map: int = 2,
        boundary_position: int = -1,
        pseudo_background_type="bw",
    ):
        """Creates shape, boundary and text data for image.
        Last step of pipeline

        Arguments:
            img {numpy array} -- source image
            mask {numpy array} -- final mask
            obj {array} -- contour object
        """
        try:
            # Find shape properties, output shape image (optional)
            self.analyze_object(img, mask.copy())
        except Exception as e:
            logger.exception(
                f'No contour detected "{repr(e)}", '
                + f'skipping analyze_object & analyze_bound for "{self.file_name}"'
            )
            return False
        else:
            res = True

        res = self.analyze_bound(img, mask, boundary_position, "v") and res

        # Determine color properties: Histograms,
        # Color Slices and Pseudocolored Images, output color analyzed images (optional)
        if not self.is_heliasen:
            res = self.analyse_chlorophyll(img=img, mask=mask) and res
            res = (
                self.analyze_color(
                    img=img,
                    mask=mask,
                    pseudo_color_channel=pseudo_color_channel,
                    pseudo_color_map=pseudo_color_map,
                    pseudo_bkg=pseudo_background_type,
                )
                and res
            )
        return res

    # @time_method
    def extract_image_data(
        self,
        mask: Any,
        source_image: Union[None, str, Any] = None,
        pseudo_color_channel: str = "v",
        pseudo_color_map: int = 2,
        boundary_position: int = -1,
        pseudo_background_type="bw",
    ) -> bool:
        """Extract image data after segmentation

        :param pseudo_background_type:
        :param pseudo_color_map:
        :param boundary_position:
        :param mask: Mask from segmentation
        :param pseudo_color_channel: Channel used for pseudo color output image
        :param source_image: name of overridden source image
        :return: success
        """
        res = False
        try:
            if source_image is None:
                img = self.current_image
            elif isinstance(source_image, str):
                img = self.retrieve_stored_image(source_image)
            else:
                img = source_image
            if img is None:
                img = self.current_image

            # Display mask on image
            masked_whole = self.draw_image(
                src_image=img, src_mask=mask, background="silver", foreground="source"
            )
            self.store_image(masked_whole, "masked_whole")

            # Analyse
            res = self.analyse(
                img=img,
                mask=mask,
                pseudo_color_channel=pseudo_color_channel,
                pseudo_color_map=pseudo_color_map,
                pseudo_background_type=pseudo_background_type,
                boundary_position=boundary_position,
            )
        except Exception as e:
            logger.exception(
                f'Failed to extract image data: "{str(self)}", because "{repr(e)}"'
            )
            res = False
        finally:
            return res

    def multi_and(self, image_list: tuple):
        """Performs an AND with all the images in the tuple

        :param image_list:
        :return: image
        """
        return ipc.multi_and(image_list)

    def multi_or(self, image_list: tuple):
        """Performs an OR with all the images in the tuple

        :param image_list:
        :return: image
        """
        return ipc.multi_or(image_list)

    def open(
        self,
        image: Any,
        kernel_size: int = 3,
        kernel_shape: int = cv2.MORPH_ELLIPSE,
        rois: tuple = (),
        dbg_text: str = "",
        proc_times: int = 1,
    ):
        """Morphology - Open wrapper

        Arguments:
            image {numpy array} -- Source image
            kernel_size {int} -- kernel size
            kernel_shape {int} -- cv2 constant
            roi -- Region of Interrest
            dbg_text {str} -- debug text (default: {''})
            proc_times {int} -- iterations

        Returns:
            numpy array -- opened image
        """
        result = ipc.open(
            image=image,
            kernel_size=kernel_size,
            kernel_shape=kernel_shape,
            rois=rois,
            proc_times=proc_times,
        )
        if dbg_text:
            self.store_image(result, "{}_open_{}".format(dbg_text, kernel_size), rois)
        return result

    def close(
        self,
        image: Any,
        kernel_size: int = 3,
        kernel_shape: int = cv2.MORPH_ELLIPSE,
        rois: tuple = (),
        dbg_text: str = "",
        proc_times: int = 1,
    ):
        """Morphology - Close wrapper

        Arguments:
            image {numpy array} -- Source image
            kernel_size {int} -- kernel size
            kernel_shape {int} -- cv2 constant
            roi -- Region of Interest
            dbg_text {str} -- debug text (default: {''})
            proc_times {int} -- iterations

        Returns:
            numpy array -- closed image
        """
        result = ipc.close(
            image=image,
            kernel_size=kernel_size,
            kernel_shape=kernel_shape,
            rois=rois,
            proc_times=proc_times,
        )
        if dbg_text:
            self.store_image(result, "{}_close_{}".format(dbg_text, kernel_size), rois)
        return result

    def dilate(
        self,
        image: Any,
        kernel_size: int = 3,
        kernel_shape: int = cv2.MORPH_ELLIPSE,
        rois: tuple = (),
        dbg_text: str = "",
        proc_times: int = 1,
    ):
        """Morphology - Dilate wrapper

        Arguments:
            image {numpy array} -- Source image
            kernel_size {int} -- kernel size
            kernel_shape {int} -- cv2 constant
            roi -- Region of Interrest
            dbg_text {str} -- debug text (default: {''})
            proc_times {int} -- iterations

        Returns:
            numpy array -- dilated image
        """
        result = ipc.dilate(
            image=image,
            kernel_size=kernel_size,
            kernel_shape=kernel_shape,
            rois=rois,
            proc_times=proc_times,
        )
        if dbg_text:
            self.store_image(
                result,
                "{}_dilate_{}_{}_times".format(dbg_text, kernel_size, proc_times),
                rois,
            )
        return result

    def erode(
        self,
        image: Any,
        kernel_size: int = 3,
        kernel_shape: int = cv2.MORPH_ELLIPSE,
        rois: tuple = (),
        dbg_text: str = "",
        proc_times: int = 1,
    ):
        """Morphology - Erode wrapper

        Arguments:
            image {numpy array} -- Source image
            kernel_size {int} -- kernel size
            kernel_shape {int} -- cv2 constant
            roi -- Region of Interrest
            dbg_text {str} -- debug text (default: {''})
            proc_times {int} -- iterations

        Returns:
            numpy array -- eroded image
        """
        result = ipc.erode(
            image=image,
            kernel_size=kernel_size,
            kernel_shape=kernel_shape,
            rois=rois,
            proc_times=proc_times,
        )
        if dbg_text:
            self.store_image(
                result,
                "{}_erode_{}_{}_times".format(dbg_text, kernel_size, proc_times),
                rois,
            )
        return result

    def print_channels(
        self,
        src_img: Any,
        rois: tuple = (),
        normalize: bool = False,
        median_filter_size: int = 0,
        test_normalize: bool = False,
        median_filter_max: int = 0,
        step_op: int = 2,
    ):
        """Creates images for each requested channel and stores them

        Arguments:
            src_img {numpy array} -- source image
            channels {list} -- channels to print, if empty all available channels will be printed
            rois {list} -- list of regions of interrest to be printed

        Keyword Arguments:
            normalize {bool} -- Apply normalization (default: {False})
            median_filter_size {int} -- median filter size (default: {0})
        """

        for color_space, channel, _ in ipc.create_channel_generator(
            self.file_handler.channels
        ):
            fs = median_filter_size
            while True:
                if test_normalize:
                    self.get_channel(src_img, channel, color_space, rois, False, fs)
                    self.get_channel(src_img, channel, color_space, rois, True, fs)
                else:
                    self.get_channel(src_img, channel, color_space, rois, normalize, fs)
                if fs == 0:
                    fs = 3
                else:
                    fs += step_op
                if fs > median_filter_max:
                    break

    def init_rois(self):
        """Builds image ROIs"""
        pass

    def init_standard_rois(self):
        """Builds ROIs for selected experiments, do not use if not sure"""
        if self.is_vis:
            if self.is_wide_angle:
                self.add_rect_roi(234, 1588, 258, 1034, "main_roi", "keep")
                self.add_rect_roi(1558, 272, 254, 234, "roi_cable", "erode")
                self.add_rect_roi(328, 32, 102, 2108, "roi_bar_left", "erode")
                self.add_rect_roi(1670, 48, 484, 1728, "roi_bar_right", "erode")
                self.add_rect_roi(268, 52, 786, 48, "roi_bolt_left", "erode")
                self.add_rect_roi(1722, 48, 782, 52, "roi_bolt_right", "erode")
                self.add_rect_roi(638, 778, 592, 654, "safe_zone", "safe")
            else:
                if self.is_blue_guide:
                    self.add_rect_roi(16, 2020, 22, 1306, "main_roi", "keep")
                    self.add_rect_roi(1702, 344, 6, 308, "roi_cable", "erode")
                    self.add_rect_roi(50, 60, 10, 1456, "roi_bar_left", "erode")
                    self.add_rect_roi(1970, 44, 16, 1406, "roi_bar_right", "erode")
                    self.add_rect_roi(732, 502, 900, 364, "safe_1", "safe")
                    self.add_rect_roi(1070, 894, 304, 960, "safe_2", "safe")
                    self.add_rect_roi(114, 800, 260, 1008, "safe_3", "safe")
                    self.add_rect_roi(114, 1590, 18, 812, "safe_4", "safe")
                elif self.is_drop_roi:
                    if self.is_blue_background:
                        self.add_rect_roi(28, 1998, 756, 1290, "main_roi", "keep")
                        self.add_rect_roi(1688, 338, 20, 290, "roi_cable", "erode")
                        self.add_rect_roi(42, 70, 6, 2432, "roi_bar_left", "erode")
                        self.add_rect_roi(1894, 46, 18, 2372, "roi_bar_right", "erode")
                        self.add_rect_roi(236, 1416, 42, 1876, "safe_left_top", "safe")
                        self.add_rect_roi(
                            1550, 256, 372, 1528, "safe_right_middle", "safe"
                        )
                    else:
                        self.add_rect_roi(28, 1998, 756, 1290, "main_roi", "keep")
                        self.add_rect_roi(1688, 338, 20, 290, "roi_cable", "erode")
                        self.add_rect_roi(150, 50, 6, 2432, "roi_bar_left", "erode")
                        self.add_rect_roi(1838, 38, 18, 2372, "roi_bar_right", "erode")
                        self.add_rect_roi(90, 46, 688, 46, "roi_bolt_left", "erode")
                        self.add_rect_roi(1894, 46, 686, 46, "roi_bolt_right", "erode")
                        self.add_rect_roi(236, 1416, 42, 1876, "safe_left_top", "safe")
                        self.add_rect_roi(
                            1550, 256, 372, 1528, "safe_right_middle", "safe"
                        )
                elif self.is_blue_background:
                    self.add_rect_roi(28, 1998, 20, 1290, "main_roi", "keep")
                    self.add_rect_roi(1688, 338, 20, 290, "roi_cable", "erode")
                    self.add_rect_roi(42, 70, 4, 2438, "roi_bar_left", "erode")
                    self.add_rect_roi(1941, 80, 4, 2438, "roi_bar_right", "erode")
                    self.add_rect_roi(236, 1416, 42, 1222, "safe_left_top", "safe")
                    self.add_rect_roi(1550, 256, 372, 892, "safe_right_middle", "safe")
                else:
                    self.add_rect_roi(28, 1998, 20, 1290, "main_roi", "keep")
                    self.add_rect_roi(1688, 338, 20, 290, "roi_cable", "erode")
                    self.add_rect_roi(150, 50, 6, 2432, "roi_bar_left", "erode")
                    self.add_rect_roi(1838, 38, 18, 2372, "roi_bar_right", "erode")
                    self.add_rect_roi(90, 46, 688, 46, "roi_bolt_left", "erode")
                    self.add_rect_roi(1894, 46, 686, 46, "roi_bolt_right", "erode")
                    self.add_rect_roi(236, 1416, 42, 1222, "safe_left_top", "safe")
                    self.add_rect_roi(1550, 256, 372, 892, "safe_right_middle", "safe")
        elif self.is_fluo:
            if self.is_drop_roi:
                self.add_rect_roi(1, 1036, 10, 1100, "main_roi", "keep")
                self.add_rect_roi(286, 456, 1092, 70, "roi_sticker")
                self.add_rect_roi(286, 456, 1053, 42, "roi_protect", "safe")
            else:
                self.add_rect_roi(1, 1036, 10, 725, "main_roi", "keep")
                self.add_rect_roi(286, 456, 711, 70, "roi_sticker")
                self.add_rect_roi(286, 456, 690, 42, "roi_protect", "safe")
        elif self.is_nir:
            pass
        else:
            pass

    @staticmethod
    def prepare_masks_data_dict(data: tuple):
        """DEPRECATED Prepares dictionaries for mask building

        :param data: list
        :return:
        """
        return [
            dict(
                channel=dt[0],
                mask=None,
                debug_name="",
                min=dt[1],
                max=dt[2],
                median_filter_size=dt[3],
            )
            for dt in data
        ]

    def apply_mask_data_dict(
        self,
        source_image,
        mask_data: dict,
        store_masks: bool = True,
        dbg_str_prefix: str = "",
    ):
        """DEPRECATED Build mask from dict built in prepare_masks_data_dict

        :param source_image:
        :param mask_data:
        :param store_masks:
        :param dbg_str_prefix:
        :return:
        """
        for dic_info in mask_data:
            dic_info["mask"], dic_info["debug_name"] = self.get_mask(
                source_image,
                dic_info["channel"],
                dic_info["min"],
                dic_info["max"],
                median_filter_size=dic_info["median_filter_size"],
            )
            if store_masks:
                root_dbg_name = dic_info["debug_name"]
                if dbg_str_prefix:
                    root_dbg_name = f"{dbg_str_prefix}_{root_dbg_name}"
                self.store_image(dic_info["mask"], root_dbg_name)

        return mask_data

    def build_mask(self, source_image, **kwargs):
        """Builds a mask for source_image from data in kwargs

        :param source_image: Source image
        :param kwargs: arguments to apply to channels
        :return: mask if merge_action is present, list of masks else
        """
        is_store_images = kwargs.get("is_store_images", False)
        masks_ = []

        for params in kwargs.get("params_list", None):
            channel = params.get("channel", "h")
            method = params.get("method", "standard")

            # Apply threshold
            if method == "standard":
                mask, _ = self.get_mask(
                    source_image,
                    channel=channel,
                    min_t=params.get("min_t", 0),
                    max_t=params.get("max_t", 255),
                    median_filter_size=params.get("median_filter_size", 0),
                )
            elif method == "otsu":
                c = self.get_channel(src_img=source_image, channel=channel)
                _, mask = cv2.threshold(c, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                if params.get("invert", False) is True:
                    mask = 255 - mask
            else:
                logger.error(f'Unknown threshold method "{method}"')
                continue

            if mask is None:
                continue

            # Apply morphology
            func = getattr(self, params.get("morph_op", "none"), None)
            if func:
                mask = func(
                    mask,
                    kernel_size=params.get("kernel_size", 3),
                    proc_times=params.get("proc_times", 1),
                )

            # Build dict
            res = dict(mask=mask, channel=channel, desc=self._params_to_string(**params))

            # Store image if needed
            if is_store_images:
                self.store_image(mask, res["desc"])

            masks_.append(res)

        if len(masks_) > 1:
            func = getattr(self, kwargs.get("merge_action", ""), None)
            if func:
                mask = func([dic["mask"] for dic in masks_])
                self.store_image(mask, "built_mask")
                return mask
            else:
                return masks_
        elif len(masks_) == 1:
            return masks_[0]["mask"]
        else:
            return None

    def keep_roi(self, src_mask, roi: AbstractRegion, dbg_str: str = ""):
        """Delete all data outside of the mask

        Arguments:
            src_mask {numpy array} -- binary image
            roi {any} -- zone to clear
            dbg_str {str} -- debug string

        Returns:
            [numpy array] -- [output mask]
        """

        cp = roi.keep(src_mask)
        if dbg_str:
            self.store_image(cp, dbg_str)

        return cp

    def delete_roi(self, src_mask, roi: AbstractRegion, dbg_str=""):
        """Delete data inside roi

        Arguments:
            src_mask {numpy array} -- binary image
            roi {rectangle} -- zone to clear
            dbg_str {str} -- debug string

        Returns:
            [numpy array] -- [output mask]
        """

        cp = roi.delete(src_mask)
        if dbg_str:
            self.store_image(cp, dbg_str)

        return cp

    def keep_rois(self, src_mask, tags, dbg_str="", print_rois=False):
        """

        :param src_mask:
        :param tags:
        :param dbg_str:
        :return:
        """
        roi_list = []
        images_ = []
        for tag in tags:
            if isinstance(tag, str):
                roi_list.extend(self.get_rois({tag}))
            else:
                roi_list.append(tag)
        if roi_list:
            for roi in roi_list:
                images_.append(roi.keep(src_mask))
            res = self.multi_or(tuple(images_))
        else:
            res = src_mask
        if dbg_str:
            self.store_image(image=res, text=dbg_str, rois=roi_list if dbg_str else ())

        return res

    def delete_rois(self, src_mask, tags, dbg_str="", print_rois=False):
        roi_list = []
        for tag in tags:
            if isinstance(tag, str):
                roi_list.extend(self.get_rois({tag}))
            else:
                roi_list.append(tag)
        for roi in roi_list:
            src_mask = roi.delete(src_mask)
        if dbg_str:
            self.store_image(
                image=src_mask, text=dbg_str, rois=roi_list if dbg_str else ()
            )

        return src_mask

    def draw_rois(self, img, rois):
        if len(img.shape) == 2 or (len(img.shape) == 3 and img.shape[2] == 1):
            img_ = np.dstack((img, img, img))
        else:
            img_ = img.copy()
        for roi in rois:
            img_ = roi.draw_to(dst_img=img_, line_width=self.width // 200)
        return img_

    def apply_roi_list(self, img, rois, print_dbg: bool = False):
        img_ = img.copy()
        if rois is not None:
            for roi in rois:
                img_ = self.apply_roi(img=img_, roi=roi, print_dbg=print_dbg)
        return img_

    def apply_roi(self, img, roi, print_dbg: bool = False):
        dbg_str = f"roi_{roi.tag}_{roi.name}" if print_dbg else ""
        if roi is None:
            return img
        elif roi.tag == "keep":
            return self.keep_roi(src_mask=img, roi=roi, dbg_str=dbg_str)
        elif roi.tag == "delete":
            return self.delete_roi(src_mask=img, roi=roi, dbg_str=dbg_str)
        elif roi.tag == "crop":
            return self.crop_to_roi(img=img, roi=roi, erase_outside_if_circle=True)
        elif roi.tag in ["safe", "enforce"]:
            return img
        elif roi.tag == "erode":
            return self.erode(image=img, rois=(roi,), dbg_text=dbg_str)
        elif roi.tag == "dilate":
            return self.dilate(image=img, rois=(roi,), dbg_text=dbg_str)
        elif roi.tag == "open":
            return self.open(image=img, rois=(roi,), dbg_text=dbg_str)
        elif roi.tag == "close":
            return self.close(image=img, rois=(roi,), dbg_text=dbg_str)
        else:
            return img

    def apply_rois(self, img, dbg_str=""):
        """Applies all stored rois to image according to tags

        Arguments:
            img {numpy array} -- source image
            dbg_str {str} -- debug string

        Returns:
            numpy array -- image with rois applied
        """

        for roi in self.rois_list:
            if dbg_str:
                tmp_str = "{}_{}".format(dbg_str, roi.name)
            else:
                tmp_str = ""
            if roi.tag == "keep":
                img = self.keep_roi(img, roi, tmp_str)
            elif roi.tag == "delete":
                img = self.delete_roi(img, roi, tmp_str)

        if dbg_str:
            self.store_image(img, dbg_str)
        return img

    def crop_to_roi(self, img, roi, erase_outside_if_circle: bool = False, dbg_str=""):
        """
        Crop image to ROI size and position
        :param img:
        :param roi:
        :param erase_outside_if_circle:
        :return:
        """
        if isinstance(roi, str):
            roi = self.get_roi(roi)

        img_ = img.copy()
        if roi is not None:
            img_ = roi.crop(img, erase_outside_if_circle)
            if dbg_str:
                self.store_image(img_, dbg_str)

        return img_

    def crop_to_keep_roi(self, img, erase_outside_if_circle: bool = False):
        """
        Crop image to first keep ROI size and position
        :param img:
        :param erase_outside_if_circle:
        :return:
        """
        keep_roi = None
        if not self.rois_list:
            self.init_rois()
        for roi in self.rois_list:
            if roi.tag == "keep":
                keep_roi = roi
                break
        if keep_roi is not None:
            return keep_roi.crop(img, erase_outside_if_circle)
        else:
            return img

    @staticmethod
    def fix_white_balance(img, min_values, max_values):
        """Performs color correction using an approximation of

        Arguments:
            img {numpy array} -- source image
            min_values {list} -- forced min values
            max_values {list} -- forced max values

        Returns:
            numpy array -- color corrected image
        """

        channels = cv2.split(img)
        out_channels = []

        for i, channel in enumerate(channels):
            # Search vmin & vmax
            vmin = min_values[i]
            vmax = max_values[i]
            # Saturate the pixels
            channel[channel < vmin] = vmin
            channel[channel > vmax] = vmax
            # Rescale the pixels
            channel = cv2.normalize(channel, channel.copy(), 0, 255, cv2.NORM_MINMAX)

            out_channels.append(channel)

        return cv2.merge(out_channels)

    @staticmethod
    def simplest_cb(img, percents):
        """Performs color correction using
        http://www.ipol.im/pub/art/2011/llmps-scb/

        Arguments:
            img {numpy array} -- source image
            percents {list} -- top and bottom percentile pixels to be floored

        Returns:
            numpy array -- color corrected image
        """

        channels = cv2.split(img)

        out_channels = []

        for channel in channels:
            # Flatten channel
            height, width = channel.shape
            vec_size = width * height
            # Build histogram
            histo = cv2.calcHist([channel], [0], None, [256], [0, 256])
            for i in range(1, 256):
                histo[i] += histo[i - 1]
            # Search vmin & vmax
            vmin = 0
            percent_ = vec_size * percents[0] / 100
            while histo[vmin + 1] <= percent_:
                vmin += 1
            vmax = 255 - 1
            percent_ = vec_size * (1 - percents[1] / 100)
            while histo[vmax - 1] > percent_:
                vmax -= 1
            if vmax < 255 - 1:
                vmax += 1

                # Saturate the pixels
            channel[channel < vmin] = vmin
            channel[channel > vmax] = vmax
            # Rescale the pixels
            channel = cv2.normalize(channel, channel.copy(), 0, 255, cv2.NORM_MINMAX)

            out_channels.append(channel)

        return cv2.merge(out_channels)

    def apply_CLAHE(
        self, img, color_space="HSV", clip_limit=(2.0, 2.0, 2.0), tile_grid_size=(8, 8)
    ):
        """Applies CLAHE (Contrast Limited Adaptive Histogram Equalization) to source image

        Arguments:
            img {numpy array} -- Source image

        Keyword Arguments:
            color_space {str} -- Color space to use (default: {'HSV'})
            clip_limit {tuple} -- Clip value for each channel,
                                  use negative value to ignore channel (default: {(2.0, 2.0, 2.0)})
            tile_grid_size {tuple} -- tile size (default: {(8,8)})

        Raises:
            NotImplementedError -- Raised if unknown color space is requested
            NotImplementedError -- Raised if unknown color space is requested

        Returns:
            numpy array -- Modified image
        """

        # Change color space
        if color_space.upper() == "HSV":
            csi = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        elif color_space.upper() == "LAB":
            csi = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        elif color_space.upper() == "RGB":
            csi = img.copy()
        else:
            raise NotImplementedError

        # Split channels
        c1, c2, c3 = cv2.split(csi)

        # Apply CLAHE
        if clip_limit[0] >= 0:
            clahe = cv2.createCLAHE(clipLimit=clip_limit[0], tileGridSize=tile_grid_size)
            c1 = clahe.apply(c1)
        if clip_limit[1] >= 0:
            clahe = cv2.createCLAHE(clipLimit=clip_limit[1], tileGridSize=tile_grid_size)
            c2 = clahe.apply(c2)
        if clip_limit[1] >= 0:
            clahe = cv2.createCLAHE(clipLimit=clip_limit[2], tileGridSize=tile_grid_size)
            c3 = clahe.apply(c3)

        # Merge channels
        csi = cv2.merge([c1, c2, c3])
        if color_space.upper() == "HSV":
            return cv2.cvtColor(csi, cv2.COLOR_HSV2BGR)
        elif color_space.upper() == "LAB":
            return cv2.cvtColor(csi, cv2.COLOR_LAB2BGR)
        elif color_space.upper() == "RGB":
            return csi
        else:
            raise NotImplementedError

    def test_simplest_cb(self, img, percents_limits, step=5):
        """Tests color correction using different values

        Arguments:
            img {numpy array} -- source image
            percents_limits {list} -- top and bottom percentiles

        Keyword Arguments:
            step {int} -- increment/decrement per test (default: {5})
        """

        while percents_limits[0] >= 0 or percents_limits[1] >= 0:
            if percents_limits[0] < 0:
                percents_limits[0] = 0
            if percents_limits[1] < 0:
                percents_limits[1] = 0
            img_test = self.simplest_cb(img.copy(), percents_limits)
            self.store_image(
                img_test, "wb_{}_{}".format(percents_limits[0], percents_limits[1])
            )
            percents_limits[0] -= step
            percents_limits[1] -= step

    def get_channel(
        self,
        src_img=None,
        channel="l",
        dbg_str="",
        rois=(),
        normalize=False,
        median_filter_size=0,
    ):
        """Returns channel component

        Arguments:
            src_img {numpy array} -- source image
            channel {str} -- target channel

        Keyword Arguments:
            dbg_str {str} -- root string to use in debug (default: {''})
            rois {list} -- ROIs to print to output debug (default: {[]})
            normalize {bool} -- normalization option (default: {False})
            median_filter_size {int} -- median filter size (default: {0})

        Raises:
            NameError -- Asked for unknown channel

        Returns:
            numpy array -- channel component
        """
        if src_img is None:
            img = self.current_image
        elif len(src_img.shape) == 2:
            return src_img
        else:
            img = src_img.copy()

        # Select source channel to process
        if channel in ipc.CHANNELS_BY_SPACE[ipc.HSV]:
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            h, s, v = cv2.split(hsv)
            if channel == "h":
                c = h
            elif channel == "s":
                c = s
            else:
                c = v
        elif channel in ipc.CHANNELS_BY_SPACE[ipc.LAB]:
            lab = cv2.cvtColor(img, cv2.COLOR_BGR2Lab)
            l, a, b = cv2.split(lab)
            if channel == "l":
                c = l
            elif channel == "a":
                c = a
            else:
                c = b
        elif channel in ipc.CHANNELS_BY_SPACE[ipc.RGB]:
            b, g, r = cv2.split(img)
            if channel == "bl":
                c = b
            elif channel == "gr":
                c = g
            else:
                c = r
        elif channel in ipc.CHANNELS_BY_SPACE[ipc.CHLA]:
            b, g, r = cv2.split(img)
            c = np.exp(
                (-0.0280 * r * 1.04938271604938)
                + (0.0190 * g * 1.04938271604938)
                + (-0.0030 * b * 1.04115226337449)
                + 5.780
            )
            c = ((c - c.min()) / (c.max() - c.min()) * 255).astype(np.uint8)
        elif channel in ipc.CHANNELS_BY_SPACE[ipc.MSP]:
            if self.is_msp and (self.retrieve_linked_images() != 0):
                _, wl = channel.split("_")
                img = self.linked_images_holder.retrieve_image(
                    key="view_option",
                    value=wl,
                    transformations=self.image_transformations,
                )
                if img is not None:
                    b, g, r = cv2.split(img)
                    lpo1 = r * 0.299 + g * 0.587 + b * 0.114
                    c = lpo1.astype(np.uint8)
                else:
                    return None
            else:
                return None
        elif channel in ipc.CHANNELS_BY_SPACE[ipc.NDVI]:
            if self.is_msp and (self.retrieve_linked_images() != 0):
                r = self.get_channel(channel="rd")
                nir = self.get_channel(channel=channel.replace("ndvi", "wl"))
                if r is not None and nir is not None:
                    np.seterr(divide="ignore")
                    try:
                        ndvi = np.divide(
                            np.subtract(nir, r).astype(np.float),
                            np.add(nir, r).astype(np.float),
                        ).astype(np.float)
                        ndvi[ndvi == np.inf] = 0
                        ndvi[np.isnan(ndvi)] = 0
                        res = np.multiply(
                            np.divide(
                                np.subtract(ndvi, ndvi.min()),
                                np.subtract(ndvi.max(), ndvi.min()),
                            ),
                            255,
                        ).astype(np.uint8)
                    finally:
                        np.seterr(divide="warn")
                    c = res
                else:
                    return None
            else:
                return None
        else:
            return None

        # Normalize, maybe. We do it first because it's the one that adds noise
        if normalize:
            c = cv2.equalizeHist(c)

        # Median filter
        if median_filter_size > 1:
            c = cv2.medianBlur(c, median_filter_size)

        if dbg_str:
            dbg_str = "{}_{}".format(ipc.get_channel_name(channel), dbg_str)
            if normalize:
                dbg_str = "{}_normalized".format(dbg_str)
            if median_filter_size > 1:
                dbg_str = "{}_median_{}".format(dbg_str, median_filter_size)

            self.store_image(c, dbg_str, rois)

        return c

    def get_channel_stats(
        self, src_img=None, channel="l", normalize=False, median_filter_size=0
    ):
        """Calculates average and standard deviation for a given channel"""
        if isinstance(channel, str):
            c = self.get_channel(
                src_img=src_img,
                channel=channel,
                normalize=normalize,
                median_filter_size=median_filter_size,
            )
        else:
            c = channel
        tmp_tuple = cv2.meanStdDev(c.reshape(c.shape[1] * c.shape[0]))
        avg, std = tmp_tuple[0][0][0], tmp_tuple[1][0][0]
        return avg, std

    def get_mask(
        self,
        src_img: Any,
        channel: str,
        min_t: int = 0,
        max_t: int = 255,
        normalize: bool = False,
        median_filter_size: int = 0,
    ) -> tuple:
        """Returns channel mask

        :param src_img: source image
        :param channel: target channel, if empty, src_img is grayscales
        :param min_t: min value for threshold
        :param max_t: max value for threshold
        :param normalize: normalization option (default: {False})
        :param median_filter_size: median filter size (default: {0})

        :return: tuple (mask, stored_string)
        """
        median_filter_size = (
            0 if median_filter_size == 1 else ipc.ensure_odd(median_filter_size)
        )
        if channel:
            dbg_str = ipc.get_hr_channel_name(channel)
            c = self.get_channel(src_img, channel, "", [], normalize, median_filter_size)
        else:
            dbg_str = "source"
            if len(src_img.shape) == 2 or (
                len(src_img.shape) == 3 and src_img.shape[2] == 1
            ):
                c = src_img.copy()
            else:
                logger.error(
                    "If no channel is selected source must be grayscale image",
                )
                return None, ""

        if c is None:
            return None, ""

        if normalize:
            dbg_str = "{}_normalized".format(dbg_str)
        if median_filter_size > 1:
            dbg_str = "{}_median_{}".format(dbg_str, median_filter_size)

        min_t, max_t = min(min_t, max_t), max(min_t, max_t)

        mask = cv2.inRange(c, min_t, max_t)
        stored_string = "{}_min_{}_max{}".format(dbg_str, min_t, max_t)

        return mask, stored_string

    def remove_hor_noise_lines(self, **kwargs):
        min_line_size = kwargs.get("min_line_size", 20)
        c = kwargs.get("mask", self.mask)
        fully_isolated = kwargs.get("fully_isolated", True)
        max_iter = kwargs.get("max_iter", 100)

        if c is None:
            return dict(mask=None, lines=[])

        stable_ = False
        iter_ = 0
        all_lines = []
        while not stable_ and (iter_ < max_iter):
            stable_ = True
            iter_ += 1
            msk_data = ipc.MaskData(mask=c)
            for l in msk_data.lines_data:
                if (l.solidity >= 0.99) and (l.nz_span >= msk_data.mask_width - 4):
                    ld_up, ld_down = msk_data.find_top_bottom_non_full_lines(l.height_pos)
                    l.merge_or(ld_up, ld_down)
                    all_lines.append([(l.height_pos, 0, msk_data.mask_width)])
                    c[l.height_pos] = 0
                    for i in l.nz_pos:
                        c[l.height_pos][i] = 255
                else:
                    lines = msk_data.horizontal_lines_at(
                        l.height_pos, min_line_size, fully_isolated
                    )
                    if not lines:
                        continue
                    all_lines.append(lines)
                    for i, line in enumerate(lines):
                        stable_ = False
                        cv2.line(c, (line[1], line[0]), (line[2], line[0]), 0, 1)
            self.store_image(c, f"cleaned_image_iter{iter_}")

        return dict(mask=c, lines=all_lines)

    def retrieve_stored_image(self, img_name):
        """Retrieves stored image from image_list using key.
        For some keys, image will be generated even if not present in image_list

        Arguments:
            img_name {str} -- key to stored image

        Generated keys details:
            * If key contains 'exp_fixed', exposure fixed image will be used as base if present,
              if not current_image will be used

        Generated keys:
            * source: Returns raw source image
            * current_image: Returns current default image.
            * mask_on_exp_fixed_bw_with_morph: Returns image as black and white background with
              colored parts where the mask is active. Morphology data will be printed on top of image.
            * mask_on_exp_fixed_bw: Returns image as black and white background with colored
              parts where the mask is active.
            * mask_on_exp_fixed_bw_roi: Returns image as black and white background with colored
              parts where the mask is active. Morphology data will be printed on top of image
              with ROIs on top
            * exp_fixed_roi: Image with stored ROIs on top
            * exp_fixed_pseudo_on_bw: Returns image as black and white background with
              pseudo colored parts where the mask is active.

        Returns:
            boolean -- True if successful
            numpy array -- stored image
        """

        if img_name.lower() == "":
            return None
        elif img_name.lower() == "source":
            return self.source_image
        elif img_name.lower() == "current_image":
            return self.current_image
        elif img_name.lower() == "mask" and self.mask is not None:
            return self.mask.copy()
        else:
            for dic in self.image_list:
                if dic["name"].lower() == img_name.lower():
                    return dic["image"]
            if "exp_fixed" in img_name.lower():
                foreground = self.retrieve_stored_image("exposure_fixed")
                if foreground is None:
                    foreground = self.current_image
                if img_name.lower() == "mask_on_exp_fixed_bw_with_morph":
                    return self.draw_image(
                        src_image=foreground,
                        src_mask=self.mask,
                        background="bw",
                        foreground="source",
                        bck_grd_luma=120,
                        contour_thickness=6,
                        hull_thickness=6,
                        width_thickness=6,
                        height_thickness=6,
                        centroid_width=20,
                        centroid_line_width=8,
                    )
                elif img_name.lower() == "mask_on_exp_fixed_bw":
                    return self.draw_image(
                        src_image=foreground,
                        src_mask=self.mask,
                        background="bw",
                        foreground="source",
                        bck_grd_luma=120,
                    )
                elif img_name.lower() == "mask_on_exp_fixed_bw_roi":
                    return self.draw_rois(
                        img=self.draw_image(
                            src_image=foreground,
                            src_mask=self.mask,
                            foreground="source",
                            background="bw",
                        ),
                        rois=self.rois_list,
                    )
                elif img_name.lower() == "exp_fixed_roi":
                    return self.draw_rois(
                        img=foreground,
                        rois=self.rois_list,
                    )
                elif img_name.lower() == "exp_fixed_pseudo_on_bw":
                    return self.draw_image(
                        src_image=foreground,
                        channel="l",
                        src_mask=self.mask,
                        foreground="false_colour",
                        background="bw",
                        normalize_before=True,
                    )
        return None

    def build_msp_mosaic(self, normalize=False, median_filter_size=0):
        """Builds mosaic using all available MSP images

        :return:
        """
        has_main = False
        mosaic_image_list = []
        for c in self.file_handler.channels_data:
            img = None
            if c[0] == "chla":
                continue
            elif c[0] == "msp":
                img = self.get_channel(
                    src_img=self.current_image,
                    channel=c[1],
                    normalize=normalize,
                    median_filter_size=median_filter_size,
                )
            elif c[0] in ["rgb", "lab", "hsv"]:
                if has_main:
                    continue
                img = self.current_image
                has_main = True

            if img is not None:
                self.store_image(img, c[2])
                mosaic_image_list.append(c[2])

        size = math.sqrt(len(mosaic_image_list))
        d, m = divmod(size, 1)
        if m != 0:
            d += 1
        d = int(d)
        mosaic_image_list = np.array(
            np.append(
                mosaic_image_list, ["" for _ in range(len(mosaic_image_list), d * d)]
            )
        ).reshape((d, d))

        return (
            mosaic_image_list,
            self.build_mosaic(self.current_image.shape, mosaic_image_list),
        )

    def build_channels_mosaic(
        self,
        src_img,
        rois=(),
        normalize=False,
        median_filter_size=0,
    ):
        """Builds mosaic of channels using parameters

        :param src_img:
        :param rois:
        :param normalize:
        :param median_filter_size:
        :return: Mosaic image
        """
        mosaic_data_ = {}
        for color_space, channel, channel_name in ipc.create_channel_generator(
            self.file_handler.channels
        ):
            channel_image = self.get_channel(
                src_img, channel, "", rois, normalize, median_filter_size
            )
            img_name = f"{channel_name}_{normalize}_{median_filter_size}"
            self.store_image(channel_image, img_name)
            if color_space not in mosaic_data_.keys():
                mosaic_data_[color_space] = [img_name]
            else:
                mosaic_data_[color_space].append(img_name)
        mosaic_image_list = np.array(
            [mosaic_data_[cs] for cs in ipc.CHANNELS_FLAT.keys()]
        )
        return mosaic_image_list, self.build_mosaic(src_img.shape, mosaic_image_list)

    def build_mosaic(
        self,
        shape=None,
        image_names=None,
        background_color: tuple = (125, 125, 125),
        padding: tuple = 2,
        images_dict: dict = {},
    ) -> np.ndarray:
        """Creates a mosaic aggregating stored images

        Arguments:
            shape {numpy array} -- height, width, channel count
            image_names {array, list} -- array of image names

        Returns:
            numpy array -- image containing the mosaic
        """
        if image_names is None:
            image_names = self._mosaic_data
        if isinstance(image_names, np.ndarray):
            image_names = image_names.tolist()
        if len(image_names) > 0 and not isinstance(image_names[0], list):
            image_names = [image_names]

        column_count = len(image_names[0])
        line_count = len(image_names)
        if shape is None:
            shape = (
                self.height * line_count + padding * line_count + padding,
                self.width * column_count + padding * column_count + padding,
                3,
            )

        canvas = np.full(shape, background_color, np.uint8)
        if len(image_names) == 0:
            return canvas

        def parse_line(a_line, a_line_idx, a_cnv):
            for c, column in enumerate(a_line):
                if isinstance(column, str):
                    src_img = self.retrieve_stored_image(column)
                    if src_img is None:
                        src_img = images_dict.get(column, None)
                else:
                    src_img = column
                if src_img is None:
                    continue
                else:
                    r = RectangleRegion(
                        left=int((shape[1] / column_count) * c),
                        width=int(shape[1] / column_count),
                        top=int((shape[0] / line_count) * a_line_idx),
                        height=int(shape[0] / line_count),
                    )
                    r.expand(-padding)
                    a_cnv = ipc.enclose_image(a_cnv, src_img, r)

        try:
            for l, line in enumerate(image_names):
                parse_line(line, l, canvas)
        except Exception as e:
            logger.exception(f'Failed to build mosaic, because "{repr(e)}"')

        return canvas

    @staticmethod
    def _params_to_string(**kwargs):
        return "".join([f"[{k}:{v}]" for k, v in kwargs.items()])

    # @time_method
    def default_process(self, **kwargs):
        res = True
        self.rois_list = []
        self.image_list = []

        mode = kwargs.get("method", "process_mode_test_channels")
        try:
            params_dict = kwargs.get("clean_params", None)
            if not params_dict:
                params_list = kwargs.get("params", [])
                params_dict = {}
                for param_ in params_list:
                    params_dict[param_["name"]] = param_["value"]

            func = getattr(self, mode, self.process_image)
            res = func(**params_dict)

        except Exception as e:
            res = False
            logger.exception(
                f'Failed default process {mode}, exception: "{repr(e)}"',
            )
        finally:
            self.print_images()
            return res

    def check_source(self):
        if self.is_color_checker:
            logger.error(
                "HANDLED FAILURE color checker",
            )
            return False

        if self.is_msp and (self.retrieve_linked_images() != 8):
            logger.error(
                f"Wrong number of MSP files expected 8, received {self.retrieve_linked_images()}"
            )

        if self.is_corrupted:
            logger.error(
                "Image has been tagged as corrupted",
            )
            return False

        return True

    def init_csv_data(self, source_image):
        return False

    def _fix_source_image(self, img):
        return img

    def preprocess_source_image(self, **kwargs):
        return kwargs.get("src_img", self.current_image)

    def build_channel_mask(self, source_image, **kwargs):
        self._mosaic_data, mosaic_image_ = self.build_channels_mosaic(
            source_image, self.rois_list
        )
        self.store_image(mosaic_image_, "full_channel_mosaic")

        return False

    def crop_mask(self):
        self.mask = self.apply_rois(self.mask, "mask_roi_all")
        return True

    def clean_mask(self, source_image):
        return True

    def ensure_mask_zone(self):
        return True

    def build_mosaic_data(self, **kwargs):
        return True

    def finalize_process(self, **kwargs):
        return True

    def update_analysis_params(self, **kwargs) -> dict:
        """Updates analysis params from keyword arguments
        Children may override this function

        Returns:
            dict -- dictionnary containing analysis options
        """
        pseudo_color_channel = kwargs.get(
            "pseudo_color_channel", "l" if self.is_msp else "v"
        )
        boundary_position = kwargs.get("boundary_position", -1)

        return dict(
            background="source",
            foreground="false_colour",
            pseudo_color_channel=pseudo_color_channel,
            boundary_position=boundary_position,
        )

    # @time_method
    def process_image(self, **kwargs):
        """
        Process image using default settings
        :param kwargs:
        :return:
        """
        res = False
        try:
            if not self.check_source():
                return

            self.init_rois()

            img = self.current_image
            if not self.good_image:
                logger.error(
                    "Image failed to load",
                )
                return

            img = self.preprocess_source_image(src_img=img)

            self.init_csv_data(img)

            if self.is_empty_pot:
                self.csv_data_holder.fill_values()
                res = True
                return

            res = self.build_channel_mask(img, **kwargs)
            if not res:
                logger.error(
                    "Failed to build channel mask",
                )
                return

            res = self.crop_mask()
            if not res:
                logger.error(
                    "Failed to crop mask for",
                )
                return

            res = self.clean_mask(source_image=img.copy())
            if not res:
                logger.error("Failed to clean mask")
                return

            res = self.ensure_mask_zone()
            if not res:
                logger.error(
                    "Mask not where expected to b",
                )
                return

            analysis_options = self.update_analysis_params(**kwargs)

            if kwargs.get("threshold_only", 0) != 1:
                res = self.extract_image_data(
                    mask=self.mask,
                    boundary_position=analysis_options["boundary_position"],
                    pseudo_color_channel=analysis_options["pseudo_color_channel"],
                )
            if self.store_images:
                self.store_image(
                    self.draw_image(
                        src_image=self.current_image,
                        src_mask=self.mask,
                        background="bw",
                        foreground="source",
                        bck_grd_luma=120,
                        contour_thickness=6,
                        hull_thickness=6,
                        width_thickness=6,
                        height_thickness=6,
                        centroid_width=20,
                        centroid_line_width=8,
                    ),
                    "shapes",
                )

            self.build_mosaic_data(**kwargs)

            self.finalize_process(**kwargs)
        except Exception as e:
            logger.exception(f'Failed to process image, because "{repr(e)}"')
            res = False
        finally:
            self.print_images()
            return res

    def rois_contains(self, tag, pt):
        """Tests if at least one ROI with tag contains point

        Arguments:
            tag {str} -- tag
            pt {Point} -- point

        Returns:
            boolean -- True if contained
        """

        for roi in self.rois_list:
            if (tag == "" or tag == roi.tag) and roi.contains(pt):
                return True
        return False

    def rois_intersects(self, tag: str, cnt) -> bool:
        """Checks if intersection between contour and rois is empty

        :param tag: target roi tag
        :param cnt: contour
        :return: True if intersection is not empty
        """

        for pt in cnt:
            cnt_point = Point(pt[0][0], pt[0][1])
            if self.rois_contains(tag, cnt_point):
                return True
        return False

    @staticmethod
    def constraint_to_image(x, y, img):
        if x < 0:
            x = 0
        if x > img.shape[1]:
            x = img.shape[1]
        if y < 0:
            y = 0
        if y > img.shape[0]:
            y = img.shape[0]

        return x, y

    # Accessors
    def get_roi(self, roi_name, exists_only: bool = False) -> AbstractRegion:
        """Returns the ROI corresponding to roi_name

        Arguments:
            roi_name {str} -- ROI name

        Returns:
            Rectangle -- rectangle associated to the roi
        """

        for roi in self.rois_list:
            if roi.name.lower() == roi_name:
                return roi
        if exists_only is True:
            return None
        if self.current_image is None:
            return EmptyRegion
        else:
            return RectangleRegion(
                left=0,
                width=self.width,
                top=0,
                height=self.height,
                name="main_roi",
                tag="keep",
            )

    def get_rois(self, tags: set = None):
        lst = []
        for roi in self.rois_list:
            if (tags is None) or (roi.tag in tags):
                lst.append(roi)
        return lst

    def add_roi(self, new_roi):
        """
        Add an already existing ROI object

        Arguments:
            new_roi {Region} -- Any ROI
        """
        roi = self.get_roi(roi_name=new_roi.name, exists_only=True)
        if roi is not None:
            self._rois_list.remove(roi)
        self._rois_list.append(new_roi)

    def add_rois(self, roi_list):
        """
        Add ROIs to collection

        Arguments:
            roi_list {List} -- List of ROIs
        """
        for roi in roi_list:
            self.add_roi(roi)

    def add_circle_roi(self, left, top, radius, name, tag="", color=None) -> CircleRegion:
        """Add Circle of Interest to list

        Arguments:
            left {int} -- Left
            top {int} -- Top
            radius {int} -- Radius
            name {str} -- ROI name

        Keyword Arguments:
            tag {str} -- ROI associated tag (default: {''})
            color {tuple} -- ROI print color (default: {None})
        """
        circle = CircleRegion(
            cx=left, cy=top, radius=radius, name=name, tag=tag, color=color
        )
        self._rois_list.append(circle)
        return circle

    def add_rect_roi(self, **kwargs) -> RectangleRegion:
        """Add Rectangle of Interest to list

        Arguments:
            left {int} -- Left
            width {int} -- Width
            top {int} -- Top
            height {int} -- Height
            name {str} -- ROI name

        Keyword Arguments:
            tag {str} -- ROI associated tag (default: {''})
            color {tuple} -- ROI print color (default: {None})
        """
        rect = RectangleRegion(**kwargs)
        self._rois_list.append(rect)
        return rect

    def _get_csv_file_path(self):
        return os.path.join(self.dst_path, "partials", self.csv_file_name)

    def check_source_image(self):
        _ = self.source_image
        return self.good_image

    @property
    def source_image(self):
        if self._source_image is None:
            if self._current_image is not None:
                self._source_image = self._current_image.copy()
            else:
                self._source_image = self.load_source_image()
                self._current_image = None
        if self._source_image is None:
            return None
        else:
            return self._source_image.copy()

    @source_image.setter
    def source_image(self, value):
        if value is not None:
            self._source_image = value.copy()
        else:
            self._source_image = None
        self._current_image = None

    @property
    def current_image(self):
        if self._current_image is None:
            self._current_image = self.source_image
        return None if self._current_image is None else self._current_image.copy()

    @current_image.setter
    def current_image(self, value):
        self._current_image = value.copy() if value is not None else None

    def _get_mask(self):
        if self._mask is not None:
            return self._mask.copy()
        else:
            return None

    def _set_mask(self, value):
        if value is not None:
            self._mask = value.copy()
        else:
            self._mask = None

    def is_store_image(self, name):
        return (self.store_images and (name.lower() != "mosaic")) or (
            (self.store_mosaic.lower() != "none") and (name.lower() == "mosaic")
        )

    def is_save_image(self, name):
        return (self.write_images == "print") or (
            (name == "mosaic") and (self.write_mosaic == "print")
        )

    def is_plot_image(self, name):
        return (self.write_images == "plot") or (
            (name == "mosaic") and (self.write_mosaic == "plot")
        )

    @property
    def log_times(self):
        return self._options.get("log_times", False)

    @property
    def dst_path(self):
        return self._options.get("dst_path", "")

    @property
    def is_color_checker(self):
        return self.plant == "color_checker"

    @property
    def is_empty_pot(self):
        return False

    @property
    def rois_list(self):
        return self._rois_list

    @rois_list.setter
    def rois_list(self, value):
        self._rois_list = value

    @property
    def write_images(self):
        return self._options.get("write_images", "none").lower()

    @write_images.setter
    def write_images(self, value):
        if isinstance(value, str):
            self._options["write_images"] = value.lower()
        else:
            self._options["write_images"] = "none"

    @property
    def store_images(self):
        return self._options.get("store_images", False)

    @store_images.setter
    def store_images(self, value):
        self._options["store_images"] = value

    @property
    def store_mosaic(self):
        return self._options.get("store_mosaic", "none")

    @store_mosaic.setter
    def store_mosaic(self, value):
        self._options["store_mosaic"] = value

    @property
    def write_result_text(self):
        return self._options.get("write_result_text", False)

    @property
    def write_mosaic(self):
        return self._options.get("write_mosaic", "none")

    @write_mosaic.setter
    def write_mosaic(self, value):
        self._options["write_mosaic"] = value

    @property
    def mosaic_data(self):
        return self._mosaic_data

    @mosaic_data.setter
    def mosaic_data(self, value):
        self._mosaic_data = value

    @property
    def data_output(self):
        return self._data_output

    @data_output.setter
    def data_output(self, value):
        self._data_output = value

    @property
    def width(self):
        src = self.current_image
        if src is None:
            return 0
        else:
            return src.shape[1]

    @property
    def height(self):
        src = self.current_image
        if src is None:
            return 0
        else:
            return src.shape[0]

    mask = property(_get_mask, _set_mask)

    csv_file_path = property(_get_csv_file_path)
