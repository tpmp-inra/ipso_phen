import os
import numpy as np
import cv2
import matplotlib
from matplotlib import pyplot as plt
import seaborn as sns
import pandas as pd

import logging

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ip_common import get_hr_channel_name, channel_color
from ipso_phen.ipapi.base.ipt_abstract_analyzer import IptBaseAnalyzer
from ipso_phen.ipapi.base.ip_common import ToolFamily, enclose_image, C_BLACK
from ipso_phen.ipapi.tools import regions
import os

matplotlib.use("agg")


class IptAnalyzeColor(IptBaseAnalyzer):
    def build_params(self):
        self.add_checkbox(
            name="normalize",
            desc="Normalize histograms",
            default_value=0,
        )
        self.add_spin_box(
            name="remove_outliers",
            desc="Remove top and bottom % values",
            default_value=0,
            minimum=0,
            maximum=100,
            hint="Removes top and bottom % values of histogram before normalization (100 -> 1%)",
        )
        self.add_checkbox(
            name="color_mean",
            desc="Add color mean information",
            default_value=1,
        )
        self.add_checkbox(
            name="color_std_dev",
            desc="Add color standard deviation information",
            default_value=1,
        )
        self.add_checkbox(
            name="include_chlorophyll",
            desc="Include chlorophyll",
            default_value=0,
        )
        self.add_spin_box(
            name="hist_bins",
            desc="Histogram bins",
            default_value=256,
            minimum=2,
            maximum=256,
        )
        self.add_spin_box(
            name="quantile_color",
            desc="Select amount of quantiles for color analysis",
            default_value=4,
            minimum=0,
            maximum=20,
        )
        self.add_checkbox(
            name="draw_histograms",
            desc="Display histograms with channel images",
            default_value=0,
        )
        self.add_checkbox(
            name="save_histograms",
            desc="Save histograms",
            default_value=0,
            hint="Only if build histograms is enabled",
        )
        self.add_separator(name="sep_1")
        self.add_channel_selector(default_value="l")
        self.add_combobox(
            name="background",
            desc="Debug image background",
            default_value="bw",
            values=dict(
                source="Source image",
                black="Black",
                white="White",
                silver="Silver",
                bw="Black and white",
            ),
        )
        self.add_color_map_selector()

    def process_wrapper(self, **kwargs):
        """
        Analyze color:
        Analyses object color.
        Needs a mask as an input.
        Normally used in a pipeline after a clean mask is created.
        Real time: False

        Keyword Arguments (in parentheses, argument name):
            * Add color mean information (color_mean):
            * Add color standard deviation information (color_std_dev):
            * Histogram bins (hist_bins):
            * Select amount of quantiles for color analysis (quantile_color):
            * Channel (channel):
            * Debug image background (background):
            * Select pseudo color map (color_map):
        """

        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            self.data_dict = {}
            img = wrapper.current_image
            mask = self.get_mask()
            if mask is None:
                logger.error(f"FAIL {self.name}: mask must be initialized")
                return

            hist_bins = self.get_value_of("hist_bins")
            self.add_value(key="hist_bins", value=hist_bins, force_add=True)
            add_mean_info = self.get_value_of("color_mean") == 1
            add_std_dev_info = self.get_value_of("color_mean") == 1
            rem_percent = self.get_value_of("remove_outliers") / 100
            is_normalize = self.get_value_of("normalize") == 1

            if self.get_value_of("normalize") == 1 and rem_percent > 0:
                nz_pix_count = np.count_nonzero(mask)
            else:
                nz_pix_count = 0

            channel_data = {}
            for c in wrapper.file_handler.channels_data:
                if c[0] == "chla" and self.get_value_of("include_chlorophyll") == 0:
                    continue
                channel = wrapper.get_channel(src_img=img, channel=c[1])
                if channel is None:
                    continue

                # Normalize
                if self.get_value_of("normalize") == 1:
                    channel = cv2.bitwise_and(channel, channel, mask=mask)
                    # Remove outliers
                    if rem_percent > 0:
                        # Create cumulative histogram
                        hist = cv2.calcHist(
                            images=[channel],
                            channels=[0],
                            mask=mask,
                            histSize=[256],
                            ranges=[0, (256 - 1)],
                        ).flatten()
                        hist = np.cumsum(hist)
                        # Search min_val & max_val
                        min_val = 0
                        percentile = nz_pix_count * rem_percent / 100
                        while hist[min_val + 1] <= percentile:
                            min_val += 1
                        max_val = 255 - 1
                        percentile = nz_pix_count * (1 - rem_percent / 100)
                        while hist[max_val - 1] > percentile:
                            max_val -= 1
                        if max_val < 255 - 1:
                            max_val += 1

                        # Saturate the pixels
                        channel[channel < min_val] = min_val
                        channel[channel > max_val] = max_val

                    # Rescale the pixels
                    channel = cv2.normalize(
                        channel, channel.copy(), 0, 255, cv2.NORM_MINMAX
                    )
                # Build histogram
                hist = cv2.calcHist(
                    images=[channel],
                    channels=[0],
                    mask=mask,
                    histSize=[hist_bins],
                    ranges=[0, (hist_bins - 1)],
                )

                channel = cv2.bitwise_and(channel, channel, mask=mask)
                # Get Mean, median & standard deviation
                tmp_tuple = cv2.meanStdDev(src=channel.flatten(), mask=mask.flatten())
                seed_ = f"{c[0]}_{c[1]}"
                self.add_value(
                    key=f"{seed_}_std_dev",
                    value=tmp_tuple[1][0][0],
                    force_add=add_mean_info,
                )
                self.add_value(
                    key=f"{seed_}_mean",
                    value=tmp_tuple[0][0][0],
                    force_add=add_std_dev_info,
                )

                channel_data[c[1]] = dict(
                    color_space=c[0],
                    channel_name=c[1],
                    data=channel,
                    hist=hist,
                )

            # Create Histogram Plot
            if wrapper.store_images and self.get_value_of("draw_histograms") == 1:
                for _, v in channel_data.items():
                    fig = plt.figure(figsize=(10, 10), dpi=100)
                    plt.plot(v["hist"], label=v["channel_name"])
                    plt.xlim([0, hist_bins - 1])
                    plt.legend()
                    title_ = f'histogram_{v["channel_name"]}'
                    plt.title(title_)
                    fig.canvas.draw()
                    # Now we can save it to a numpy array.
                    data = np.fromstring(
                        fig.canvas.tostring_rgb(), dtype=np.uint8, sep=""
                    )
                    fig_shape = fig.canvas.get_width_height()[::-1]
                    data = data.reshape(fig_shape + (3,))
                    # Crop the image to keep only the object
                    canvas = np.full((fig_shape[0], fig_shape[1], 3), C_BLACK, np.uint8)
                    channel_img = enclose_image(
                        a_cnv=canvas,
                        img=v["data"][np.ix_(mask.any(1), mask.any(0))],
                        rect=regions.RectangleRegion(
                            width=fig_shape[1],
                            height=fig_shape[0],
                        ),
                        frame_width=0,
                    )
                    wrapper.store_image(np.hstack((channel_img, data)), title_)
                    plt.clf()
                    plt.close()

            if self.get_value_of("save_histograms") == 1:
                dataframe = pd.DataFrame(columns=["channel"] + [i for i in range(0, 256)])
                for i, v in enumerate(channel_data.values()):
                    dataframe.loc[i] = [v["channel_name"]] + list(v["hist"].flatten())
                dataframe.to_csv(
                    path_or_buf=os.path.join(
                        self.output_path,
                        f"{wrapper.plant}_histograms.csv",
                    ),
                    index=False,
                )

            self.demo_image = wrapper.draw_image(
                src_image=img,
                channel=self.get_value_of("channel"),
                color_map=self.get_value_of("color_map"),
                foreground="false_colour",
                src_mask=mask,
                background=self.get_value_of("background"),
            )
            wrapper.store_image(image=self.demo_image, text="pseudo_on")

            # handle color quantiles
            n = self.get_value_of("quantile_color")
            if n > 0:
                for c, v in channel_data.items():
                    if v["data"] is None:
                        logger.error(
                            f'Missing channel {v["color_space"]}, {v["channel_name"]}'
                        )
                        continue
                    seed_ = f'{v["color_space"]}_{c}'
                    hist = cv2.calcHist([v["data"]], [0], mask, [n], [0, (256 - 1)])
                    total_pixels = np.sum(hist)
                    for i, qtt in enumerate([hist_val[0] for hist_val in hist]):
                        self.add_value(
                            f"quantile_color_{seed_}_{i + 1}_{n}_percent",
                            qtt / total_pixels * 100,
                            True,
                        )

            res = True
        except Exception as e:
            logger.error(f'Failed to process {self. name}: "{repr(e)}"')
            res = False
        else:
            pass
        finally:
            self.result = len(self.data_dict) > 0
            return res

    @property
    def name(self):
        return "Analyze color"

    @property
    def real_time(self):
        return False

    @property
    def result_name(self):
        return "dictionary"

    @property
    def output_kind(self):
        return "dictionnary"

    @property
    def use_case(self):
        return [ToolFamily.FEATURE_EXTRACTION]

    @property
    def description(self):
        return """Analyses object color.\nNeeds a mask as an input.
        Normally used in a pipeline after a clean mask is created."""
