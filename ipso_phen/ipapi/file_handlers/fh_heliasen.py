import os
from datetime import datetime as dt

from ipso_phen.ipapi.file_handlers.fh_base import FileHandlerBase


class FileHandlerHeliasen(FileHandlerBase):
    def __init__(self, **kwargs):
        self._file_path = kwargs.get("file_path", "")
        if self._file_path:
            if "-V-" in self.file_name_no_ext:
                exp_name_, self._camera, _, date_time_str = self.file_name_no_ext.split(
                    "-"
                )
            else:
                exp_name_, self._camera, date_time_str = self.file_name_no_ext.split(
                    "-"
                )
            self._exp = exp_name_[0:6]
            self._plant = exp_name_[6:]
            self._date_time = dt.strptime(date_time_str, "%Y%m%d%H%M%S")
            self._view_option = "default"

        self.update(**kwargs)

    def fix_image(self, src_image):
        return None if src_image is None else 255 - src_image

    @classmethod
    def probe(cls, file_path, database):
        if not isinstance(file_path, str) or not os.path.isfile(file_path):
            return 0
        if "-CAM" in cls.extract_file_name(file_path):
            return 100
        else:
            return 0

    @property
    def is_heliasen(self):
        return True
