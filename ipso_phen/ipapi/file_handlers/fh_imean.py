from datetime import datetime as dt
import os

from ipso_phen.ipapi.file_handlers.fh_base import FileHandlerBase


class FileHandlerIMean(FileHandlerBase):
    """File handler for IMean images
    Schema:
        imean_datetime_experiment_tray_imgfilename.ext
    Plant will be used to store tray information
    View_option will store original file name
    """

    def __init__(self, **kwargs):
        self._file_path = kwargs.get("file_path", "")
        file_, self._camera = os.path.splitext(self.file_name)
        if file_:
            _, date_time_str, self._exp, self._plant, self._view_option = file_.split(
                "_"
            )
            self._date_time = dt.strptime(date_time_str, "%Y%m%d%H%M%S")

        self.update(**kwargs)

    @classmethod
    def probe(cls, file_path, database):
        if not isinstance(file_path, str) or not os.path.isfile(file_path):
            return 0
        return 100 if cls.extract_file_name(file_path).startswith("imean_") else 0

    @property
    def is_vis(self):
        return True
