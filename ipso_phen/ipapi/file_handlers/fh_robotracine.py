import os
from datetime import datetime as dt

from ipso_phen.ipapi.file_handlers.fh_base import FileHandlerBase

import logging

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))


class FileHandlerRobotRacine(FileHandlerBase):
    def __init__(self, **kwargs):
        """Fill plant, date, time, experiment, camera and view_option from file data"""
        self._file_path = kwargs.get("file_path", "")
        if self._file_path:
            tmp_str, self._plant = self.file_name_no_ext.split(" ")
            self._plant = "plant_" + self._plant.replace("(", "").replace(")", "")
            _, self._exp, _ = tmp_str.split("_")
            self._exp = "rr_" + self._exp
            try:
                self._date_time = dt.fromtimestamp(os.path.getmtime(self.file_path))
            except Exception as e:
                logger.exception(f"Unable to extract date from file because: {repr(e)}")
                self._date_time = dt.now()
            self._date_time = self._date_time.replace(microsecond=0)
            self._camera = "pi_camera"
            _, ext_ = os.path.splitext(self.file_name)
            self._view_option = ext_ if ext_ else "unknown"

        self.update(**kwargs)

    @classmethod
    def probe(cls, file_path, database):
        if not isinstance(file_path, str) or not os.path.isfile(file_path):
            return 0
        return 100 if cls.extract_file_name(file_path).lower().startswith("rr_") else 0

    @property
    def is_vis(self):
        return True

    @property
    def is_fluo(self):
        return False

    @property
    def is_nir(self):
        return False
