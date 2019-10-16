import numpy as np
import cv2
import matplotlib
from matplotlib import pyplot as plt

from ip_base.ip_common import get_hr_channel_name, channel_color
from ip_base.ipt_abstract_analyzer import IptBaseAnalyzer
from ip_base.ip_common import TOOL_GROUP_FEATURE_EXTRACTION_STR

matplotlib.use("agg")


class IptAnalyzeColor(IptBaseAnalyzer):
    def build_params(self):
        self.add_checkbox(name="color_mean", desc="Add color mean information", default_value=1)
        self.add_checkbox(
            name="color_std_dev", desc="Add color standard deviation information", default_value=1
        )
        self.add_spin_box(
            name="hist_bins", desc="Histogram bins", default_value=256, minimum=2, maximum=256
        )
        self.add_spin_box(
            name="quantile_color",
            desc="Select amount of quantiles for color analysis",
            default_value=4,
            minimum=0,
            maximum=20,
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
            --------------
        """

        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            img = self.extract_source_from_args()
            mask = wrapper.mask
            if mask is None:
                res = False

            masked = cv2.bitwise_and(img, img, mask=mask)

            channel_data = {}
            for c in wrapper.available_channels_as_tuple:
                if c[0] == "chla":
                    continue
                channel_data[c[1]] = dict(
                    color_space=c[0],
                    channel_name=c[1],
                    data=wrapper.get_channel(src_img=masked, channel=c[1]),
                    graph_color=channel_color(c[1]),
                )

            hist_bins = self.get_value_of("hist_bins")
            self.add_value(key="hist_bins", value=hist_bins, force_add=True)
            add_mean_info = self.get_value_of("color_mean") == 1
            add_std_dev_info = self.get_value_of("color_mean") == 1

            for k, v in channel_data.items():
                if v["data"] is None:
                    wrapper.error_holder.add_error(f"Missing channel {get_hr_channel_name(k)}")
                    continue
                tmp_tuple = cv2.meanStdDev(
                    src=v["data"].reshape(v["data"].shape[1] * v["data"].shape[0]),
                    mask=mask.reshape(mask.shape[1] * mask.shape[0]),
                )
                v["hist"] = cv2.calcHist([v["data"]], [0], mask, [hist_bins], [0, (256 - 1)])
                seed_ = f'{v["color_space"]}_{k}'
                self.add_value(
                    key=f"{seed_}_std_dev", value=tmp_tuple[1][0][0], force_add=add_mean_info
                )
                self.add_value(
                    key=f"{seed_}_mean", value=tmp_tuple[0][0][0], force_add=add_std_dev_info
                )

            # Create Histogram Plot
            if wrapper.store_images:
                fig = plt.figure(figsize=(10, 10), dpi=100)
                for k, v in channel_data.items():
                    if v["data"] is None:
                        continue
                    plt.plot(v["hist"], label=v["channel_name"])
                    plt.xlim([0, hist_bins - 1])
                    plt.legend()

                if wrapper.write_images != "print":
                    fig.canvas.draw()
                    # Now we can save it to a numpy array.
                    data = np.fromstring(fig.canvas.tostring_rgb(), dtype=np.uint8, sep="")
                    data = data.reshape(fig.canvas.get_width_height()[::-1] + (3,))
                    wrapper.store_image(data, "histogram")
                elif wrapper.write_images != "plot":
                    plt.axis("off")
                    plt.title("histogram")
                    fig.tight_layout()
                    plt.show()

                plt.clf()
                plt.close()

                wrapper.store_image(
                    image=wrapper.draw_image(
                        src_image=img,
                        channel=self.get_value_of("channel"),
                        color_map=self.get_value_of("color_map"),
                        foreground="false_colour",
                        src_mask=mask,
                        background=self.get_value_of("background"),
                    ),
                    text=f"pseudo_on",
                )

            # handle color quantiles
            n = self.get_value_of("quantile_color")
            if n > 0:
                for c, v in channel_data.items():
                    if v["data"] is None:
                        wrapper.error_holder.add_error(
                            f'Missing channel {v["color_space"], v["channel_name"]}'
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
            wrapper.error_holder.add_error(f'Failed : "{repr(e)}"')
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
        return [TOOL_GROUP_FEATURE_EXTRACTION_STR]

    @property
    def description(self):
        return "Analyses object color.\nNeeds a mask as an input.\nNormally used in a pipeline after a clean mask is created."
