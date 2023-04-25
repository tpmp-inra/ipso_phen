from ipso_phen.ipapi.base.ipt_abstract_analyzer import IptBaseAnalyzer

import os
import logging
import itertools

import cv2
import numpy as np
import skimage.feature as feature

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))


class IptAnalyzeImageData(IptBaseAnalyzer):
    def build_params(self):
        self.add_enabled_checkbox()
        self.add_checkbox(
            name="is_real_time",
            desc="Execute in real time",
            default_value=0,
            hint="If true, tool image will be processed when widget is modified",
        )
        self.add_checkbox(
            name="is_perceived_brightness_data",
            desc="Add perceived brightness",
            default_value=1,
        )
        self.add_checkbox(name="is_hsv_data", desc="Add HSH data", default_value=1)
        self.add_checkbox(name="is_lab_data", desc="Add LAB data", default_value=1)
        self.add_checkbox(name="is_rgb_data", desc="Add RGB data", default_value=1)
        self.add_checkbox(
            name="is_sharpnes_data", desc="Add sharpness data", default_value=1
        )
        self.add_separator()
        self.add_checkbox(
            name="is_grey_coprop_data",
            desc="Add grey comatrix properties",
            default_value=1,
        )
        self.add_text_input(name="distances", desc="distances", default_value="1,10")
        self.add_text_input(
            name="angles",
            desc="Angles (π dividers)",
            default_value="0,4",
            hint="π dividers",
        )

    def process_wrapper(self, **kwargs):
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            if self.get_value_of("enabled") == 1:
                img = wrapper.current_image
                self.data_dict = {}

                if self.get_value_of("is_perceived_brightness_data", 0) == 1:
                    b, g, r = cv2.split(img)
                    s = np.sqrt(
                        0.241 * np.power(r.astype(np.float), 2)
                        + 0.691 * np.power(g.astype(np.float), 2)
                        + 0.068 * np.power(b.astype(np.float), 2)
                    )
                    for k, v in {
                        "cl_bright_mean": s.mean(),
                        "cl_bright_std": np.std(s),
                        "cl_bright_min": s.min(),
                        "cl_bright_max": s.max(),
                    }.items():
                        self.add_value(k, v, force_add=True)
                if self.get_value_of("is_hsv_data", 0) == 1:
                    h, s, *_ = cv2.split(cv2.cvtColor(img, cv2.COLOR_BGR2HSV))
                    for k, v in {
                        "cl_hue_mean": h.mean(),
                        "cl_hue_std": np.std(h),
                        "cl_hue_min": h.min(),
                        "cl_hue_max": h.max(),
                        "cl_sat_mean": s.mean(),
                        "cl_sat_std": np.std(s),
                        "cl_sat_min": s.min(),
                        "cl_sat_max": s.max(),
                    }.items():
                        self.add_value(k, v, force_add=True)
                if self.get_value_of("is_lab_data", 0) == 1:
                    _, a, b = cv2.split(cv2.cvtColor(img, cv2.COLOR_BGR2LAB))
                    for k, v in {
                        "cl_lab_a_mean": a.mean(),
                        "cl_lab_a_std": np.std(a),
                        "cl_lab_a_min": a.min(),
                        "cl_lab_a_max": a.max(),
                        "cl_lab_b_mean": b.mean(),
                        "cl_lab_b_std": np.std(b),
                        "cl_lab_b_min": b.min(),
                        "cl_lab_b_max": b.max(),
                    }.items():
                        self.add_value(k, v, force_add=True)
                if self.get_value_of("is_rgb_data", 0) == 1:
                    b, g, r = cv2.split(img)
                    for k, v in {
                        "cl_rgb_b_mean": b.mean(),
                        "cl_rgb_b_std": np.std(b),
                        "cl_rgb_b_min": b.min(),
                        "cl_rgb_b_max": b.max(),
                        "cl_rgb_g_mean": g.mean(),
                        "cl_rgb_g_std": np.std(g),
                        "cl_rgb_g_min": g.min(),
                        "cl_rgb_g_max": g.max(),
                        "cl_rgb_r_mean": r.mean(),
                        "cl_rgb_r_std": np.std(r),
                        "cl_rgb_r_min": r.min(),
                        "cl_rgb_r_max": r.max(),
                    }.items():
                        self.add_value(k, v, force_add=True)
                if self.get_value_of("is_rgb_data", 0) == 1:
                    self.add_value(
                        "sharpness",
                        cv2.Laplacian(
                            cv2.cvtColor(img, cv2.COLOR_BGR2GRAY),
                            cv2.CV_64F,
                        ).var(),
                        force_add=True,
                    )
                if self.get_value_of("is_grey_coprop_data", 0) == 1:
                    distances = [
                        [f"d{d}", i, int(d)]
                        for i, d in enumerate(
                            self.get_value_of("distances", "1").split(",")
                        )
                    ]
                    angles = [
                        [f"api{a}", i, np.pi / int(a) if int(a) != 0 else 0]
                        for i, a in enumerate(
                            self.get_value_of("angles", "1").split(",")
                        )
                    ]
                    graycom = feature.graycomatrix(
                        cv2.cvtColor(img, cv2.COLOR_BGR2GRAY),
                        [x[2] for x in distances],
                        [x[2] for x in angles],
                        levels=256,
                    )
                    for k, v in dict(
                        contrast=np.array(feature.graycoprops(graycom, "contrast")),
                        dissimilarity=np.array(
                            feature.graycoprops(graycom, "dissimilarity")
                        ),
                        homogeneity=np.array(
                            feature.graycoprops(graycom, "homogeneity")
                        ),
                        energy=np.array(feature.graycoprops(graycom, "energy")),
                        correlation=np.array(
                            feature.graycoprops(graycom, "correlation")
                        ),
                        asm=np.array(feature.graycoprops(graycom, "ASM")),
                    ).items():
                        for e in itertools.product(distances, angles):
                            self.add_value(
                                key=f"gp_{k}_{e[0][0]}_{e[1][0]}",
                                value=v[e[0][1]][e[1][1]],
                                force_add=True,
                            )

                wrapper.store_image(img, "current_image")
                res = True
            else:
                wrapper.store_image(wrapper.current_image, "current_image")
                res = True
        except Exception as e:
            res = False
            logger.error(f"Analyze image data FAILED, exception: {repr(e)}")
        else:
            pass
        finally:
            return res

    @property
    def name(self):
        return "Analyze image data"

    @property
    def package(self):
        return "TPMP"

    @property
    def is_wip(self):
        return True

    @property
    def real_time(self):
        return self.get_value_of("is_real_time") == 1

    @property
    def result_name(self):
        "dictionary"

    @property
    def output_kind(self):
        "dictionary"

    @property
    def use_case(self):
        return ["Feature extraction"]

    @property
    def description(self):
        return """'Write your tool s description here. it will be used to generate documentation files"""
