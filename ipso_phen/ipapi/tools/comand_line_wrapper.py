import os
import datetime


class ArgWrapper:
    """Quick and dirty wrapper to handle cmd line in debug mode

    kwargs (only used if no command line is present):
        * dst_path: Output directory for image files, required=False.
        * store_images: Store images while processing, required= False, default=False)
        * write_images: Write/print images, required= False, default=False)
        * write_result_text: Write result text file, required= False, default=False
        * store_mosaic: Store mosaic, required= False, default=none)
        * write_mosaic: Write mosaic image in a separate folder
        * overwrite: Overwrite already analysed files, required= False, default=False
        * seed_output: Suffix output folder with date, required= False, default=False
        * threshold_only: if true no analysis will be performed after threshold, required=False, default=False
        * group_by_series: if true all images from the plant from the sames series will be assigned the same id
    """

    def __init__(self, **kwargs):
        self.store_images = kwargs.get("store_images", False)
        self.write_images = kwargs.get("write_images", "none")
        self.write_result_text = kwargs.get("write_result_text", True)
        self.store_mosaic = kwargs.get("store_mosaic", "none")
        self.write_mosaic = kwargs.get("write_mosaic", "none")

        self.overwrite = kwargs.get("overwrite", False)
        self.seed_output = kwargs.get("seed_output", False)

        self.threshold_only = kwargs.get("threshold_only", False)

        self.group_by_series = kwargs.get("group_by_series", False)

        self.log_times = kwargs.get("log_times", False)

        self.masks = kwargs.get("masks", {})

        self.multi_thread = kwargs.get("multi_thread", False)

        _dst_path = kwargs.get("dst_path", "")
        if self.seed_output:
            self.dst_path = os.path.join(
                _dst_path, datetime.datetime.now().strftime("%Y_%B_%d %H-%M-%S"), ""
            )
        else:
            self.dst_path = os.path.join(_dst_path, "")
        self.partials_path = os.path.join(self.dst_path, "partials", "")
