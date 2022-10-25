from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
from ipso_phen.ipapi.tools.csv_writer import AbstractCsvWriter
from ipso_phen.ipapi.tools.common_functions import add_header_footer
from ipso_phen.ipapi.tools.common_functions import time_method


class ImageMpsCsvWriter(AbstractCsvWriter):
    def __init__(self):
        super().__init__()
        self.data_list = dict.fromkeys(
            [
                # Header - text values
                "experiment",
                "plant",
                "plant_id",
                "treatment",
                "genotype",
                "condition",
                "date_time",
                "hist_bins",
                # Morphology
                "area",
                "hull_area",
                "width_data",
                "shape_height",
                "shape_solidity",
                "shape_extend",
                "rotated_bounding_rectangle",
                "minimum_enclosing_circle",
                # Color descriptors
                "color_std_dev",
                "color_mean",
            ]
        )


_MAIN_ROI_RADIUS = 2056 / 2
_SAFE_ROI_RADIUS = 944 / 2


class Ip008C0604DevelopAbio(BaseImageProcessor):
    def init_csv_writer(self):
        return ImageMpsCsvWriter()

    @staticmethod
    def can_process(dict_data: dict) -> bool:
        """
        Checks if the class can process the image
        :param dict_data: Dictionary containing filter data
        :return: True if current class can process data
        """
        return dict_data["experiment"] in ["008C0604_DevelopAbio".lower()]

    def init_rois(self):
        self.add_circle_roi(
            int(194 + _MAIN_ROI_RADIUS),
            int(0 + _MAIN_ROI_RADIUS),
            int(_MAIN_ROI_RADIUS),
            "main_roi",
            "keep",
        )
        self.add_circle_roi(
            int(782 + _SAFE_ROI_RADIUS),
            int(542 + _SAFE_ROI_RADIUS),
            int(_SAFE_ROI_RADIUS),
            "safe_roi",
            "safe",
        )

    def _process_job_mps(self):
        # Init rois
        self.init_rois()

        img = self.source_image

        if not self.good_image:
            self.error_holder.add_error(
                "Image failed to load", new_error_kind="source_issue"
            )
            return False, None

        # Build preliminary mask
        op = "multi_and"
        params_dict = [
            dict(channel="h", min_t=10, max_t=100, median_filter_size=3),
            dict(channel="a", min_t=15, max_t=135, median_filter_size=3),
            dict(channel="b", min_t=120, max_t=155, median_filter_size=3),
            dict(channel="rd", min_t=20, max_t=160, median_filter_size=3),
        ]
        mask = self.build_mask(
            img, **dict(is_store_images=True, merge_action=op, params_list=params_dict)
        )

        # Clean mask
        mask = self.keep_roi(mask, self.get_roi("main_roi"))
        self.store_image(mask, "mask_before_open", rois=self.rois_list)
        mask = self.multi_or(
            (
                self.open(self.keep_roi(mask, self.get_roi("safe_roi")), 3),
                self.open(mask, 7),
            )
        )
        self.store_image(mask, "mask_from_channels", rois=self.rois_list)

        mask = self.keep_linked_contours(
            src_image=img,
            src_mask=mask,
            tolerance_distance=40,
            tolerance_area=5000,
            root_position="MIDDLE_CENTER",
        )
        self.store_image(mask, "mask")
        self.mask = mask

        return True, mask

    def _process_job_fluo(self):
        self.default_process()
        return False, None

    @add_header_footer
    @time_method
    def process_image(self, **kwargs):
        """Executes pipeline instructions to process image

        Raises:
            NotImplementedError -- Only fluo- is implemented

        Returns:
            boolean -- is job successful
        """
        res = False
        threshold_only_ = kwargs.get("threshold_only", 0) == 1
        try:
            if self.is_corrupted:
                self.error_holder.add_error(
                    "HANDLED FAILURE Image has been tagged as corrupted",
                    new_error_kind="source_issue",
                )
                return False

            if self.is_color_checker:
                self.error_holder.add_error("HANDLED FAILURE Image is color checker")
                return False

            if self.is_empty_ctrl or self.is_missing_plant:
                self.error_holder.add_error("HANDLED FAILURE Image is empty control")
                return False

            if not self.is_good_batch:
                self.error_holder.add_error(
                    "HANDLED FAILURE some images are missing",
                    new_error_kind="source_issue",
                )
                return False

            [genotype_, condition_, plant_id_] = self.plant.split("_")
            self.csv_data_holder.update_csv_value("plant_id", plant_id_)
            self.csv_data_holder.update_csv_value("condition", condition_)
            self.csv_data_holder.update_csv_value("genotype", genotype_)
            self.csv_data_holder.update_csv_value(
                "treatment", f"{genotype_} - {condition_}"
            )

            if self.is_fluo:
                res, mask = self._process_job_fluo()
            else:
                res, mask = self._process_job_mps()

            if not res:
                self.error_holder.add_error("Segmentation failed")

            # self._mosaic_data = np.array([['source', 'pseudo_on'],
            #                               ['src_img_with_cnt_after_agg_iter_last', 'mask']])

            if self.is_msp:
                pseudo_color_channel = "l"
            else:
                pseudo_color_channel = "v"
            pseudo_color_channel = kwargs.get(
                "pseudo_color_channel", pseudo_color_channel
            )

            if kwargs.get("threshold_only", 0) != 1:
                res = self.extract_image_data(self.mask, pseudo_color_channel)
            else:
                pseudo_color_img = self.draw_image(
                    channel=pseudo_color_channel, background="source"
                )
                self.store_image(pseudo_color_img, "pseudo_on")

            self.build_mosaic_data(**kwargs)

        except Exception as e:
            self.error_holder.add_error(f'Failed to process image because "{repr(e)}"')
            res = False

        self.print_images()

        self.csv_data_holder.clean_data()

        return res

    @property
    def is_empty_ctrl(self):
        return "empty" in self.plant

    @property
    def is_missing_plant(self):
        return self.plant in [
            "arf4_drought_84",
            "arf4_mock_73",
            "arf4_salt_76",
            "arf4_drought_421",
            "arf4_salt_417",
        ]

    @property
    def is_good_batch(self):
        return self.is_fluo or self.is_after_date(year="2018", month="04", day="10")
