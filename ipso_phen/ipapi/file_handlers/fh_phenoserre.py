from datetime import datetime as dt
import numpy as np
import os
import json

from ipso_phen.ipapi.file_handlers.fh_base import FileHandlerBase
from ipso_phen.ipapi.database.db_consts import GENOLOGIN_ADDRESS, TPMP_PORT
from ipso_phen.ipapi.database.db_passwords import get_user_and_password, check_password


import logging

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))


class FileHandlerPhenoserre(FileHandlerBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._database = kwargs.get("database", None)
        self.db_linked = (
            check_password(key="phenoserre")
            and self._database is not None
            and self._database.db_info.target == "phenoserre"
        ) is True
        self._file_path = kwargs.get("file_path", "")
        self._linked_images = []

        if self._file_path:
            tmp_str = self.file_name_no_ext.replace("(", "")
            tmp_str = tmp_str.replace(")", "")
            [self._plant, date_time_str, self._exp, cam_str] = tmp_str.split("--")
            if not self.db_linked:
                self._date_time = dt.strptime(date_time_str, "%Y-%m-%d %H_%M_%S")
            [self._camera, self._view_option] = cam_str.split("-")

    def load_source_file(self):
        if self.db_linked:
            user, pwd = get_user_and_password(key="phenoserre")
            return self.load_from_database(
                address=GENOLOGIN_ADDRESS,
                port=TPMP_PORT,
                user=user,
                pwd=pwd,
            )
        else:
            return self.load_from_harddrive()

    def fix_image(self, src_image):
        if self.is_nir and self.view_option == "top":
            return np.flip(np.flip(src_image, 0), 1)
        else:
            return super().fix_image(src_image)

    @classmethod
    def probe(cls, file_path, database):
        if (
            isinstance(file_path, str)
            and os.path.isfile(file_path)
            and (")--(" in cls.extract_file_name(file_path))
        ):
            return 100
        elif (
            check_password(key="phenoserre")
            and database is not None
            and database.db_info.target == "phenoserre"
        ):
            return 100
        else:
            return 0

    @property
    def is_vis(self):
        return "vis" in self.camera

    @property
    def is_fluo(self):
        return "fluo" in self.camera

    @property
    def is_nir(self):
        return "nir" in self.camera
