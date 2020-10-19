from datetime import datetime as dt
import numpy as np
import os

import cv2
import paramiko

from ipapi.file_handlers.fh_base import FileHandlerBase

try:
    from ipapi.database.db_connect_data import db_connect_data as dbc

    conf = dbc.get("phenoserre", {})
except Exception as e:
    conf = {}

import logging

logger = logging.getLogger(__name__)


class FileHandlerPhenoserre(FileHandlerBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._file_path = kwargs.get("file_path", "")
        if self._file_path:
            tmp_str = self.file_name_no_ext.replace("(", "")
            tmp_str = tmp_str.replace(")", "")
            [self._plant, date_time_str, self._exp, cam_str] = tmp_str.split("--")
            self._date_time = dt.strptime(date_time_str, "%Y-%m-%d %H_%M_%S")
            [self._camera, self._view_option] = cam_str.split("-")

        self.update(**kwargs)

    def fix_image(self, src_image):
        if self.is_nir and self.view_option == "top":
            return np.flip(np.flip(src_image, 0), 1)
        else:
            return super().fix_image(src_image)

    @classmethod
    def probe(cls, file_path, database):
        if not isinstance(file_path, str) or not os.path.isfile(file_path):
            return 0
        elif ")--(" in cls.extract_file_name(file_path):
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


class DirectHandlerPhenoserre(FileHandlerPhenoserre):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._file_path = kwargs.get("file_path", "")
        self._database = kwargs.get("database", None)

        (
            self._exp,
            self._plant,
            self._date_time,
            self._camera,
            self._view_option,
            self._blob_path,
        ) = self._database.query_one(
            command="SELECT",
            columns="Experiment,Plant,date_time,Camera,view_option,blob_path",
            additional="ORDER BY Time ASC",
            FilePath=self._file_path,
        )

        self.update(**kwargs)

    def load_source_file(self, database=None):
        src_img = None
        try:
            p = paramiko.SSHClient()
            p.set_missing_host_key_policy(paramiko.AutoAddPolicy)
            p.connect(
                conf["jump_address"],
                port=conf["port"],
                username=conf["user"],
                password=conf["password"],
            )
            ftp = p.open_sftp()
            with ftp.open(self._blob_path) as file:
                file_size = file.stat().st_size
                file.prefetch(file_size)
                file.set_pipelined()
                src_img = cv2.imdecode(np.fromstring(file.read(), np.uint8), 1)
            src_img = self.fix_image(src_image=src_img)
        except Exception as e:
            logger.exception(f"Failed to load {repr(self)} because {repr(e)}")
            return None
        else:
            return src_img

    def get_stream(self):
        p = paramiko.SSHClient()
        p.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        p.connect(
            conf["jump_address"],
            port=conf["port"],
            username=conf["user"],
            password=conf["password"],
        )
        ftp = p.open_sftp()
        with ftp.open(self._blob_path) as f:
            img = cv2.imdecode(np.fromstring(f.read(), np.uint8), 1)

        return open(self.file_path, "rb")

    def fix_image(self, src_image):
        if self.is_nir and self.view_option == "top":
            return np.flip(np.flip(src_image, 0), 1)
        else:
            return super().fix_image(src_image)

    @classmethod
    def probe(cls, file_path, database):
        return (
            100
            if conf and database is not None and database.db_info.target == "phenoserre"
            else 0
        )

    @property
    def is_vis(self):
        return "vis" in self.camera

    @property
    def is_fluo(self):
        return "fluo" in self.camera

    @property
    def is_nir(self):
        return "nir" in self.camera
