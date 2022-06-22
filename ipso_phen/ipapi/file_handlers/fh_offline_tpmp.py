# from datetime import datetime as dt
import datetime
from datetime import datetime as dt
import os
import shutil

import platform
import pathlib

import cv2

from ipso_phen.ipapi.file_handlers.fh_base import FileHandlerBase
from ipso_phen.ipapi.tools.common_functions import force_directories
import ipso_phen.ipapi.base.ip_common as ipc

from ipso_phen.ipapi.database.base import connect_to_lipmcalcul


import logging

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))


class FileHandlerTpmp(FileHandlerBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._file_path = kwargs.get("file_path", "")
        self._database = kwargs.get("database", "")

        if self._file_path:
            tmp_str = self.file_name_no_ext.replace("(", "")
            (
                self._exp,
                self._date_time,
                self._plant,
                self._camera,
                self._angle,
                self._wavelength,
                _,
                self._job_id,
            ) = tmp_str.split("#")
            self._date_time = dt.strptime(self._date_time, "%Y%m%d%H%M%S")

        self.db_linked = False

    def get_channel(self, src_img=None, channel="l"):
        c = super().get_channel(src_img=src_img, channel=channel)
        if c is None:
            try:
                ret = self._database.query(
                    command="SELECT",
                    columns="filepath",
                    experiment=self.experiment,
                    plant=self.plant,
                    date_time=dict(
                        operator="BETWEEN",
                        date_min=self.date_time - datetime.timedelta(hours=1),
                        date_max=self.date_time + datetime.timedelta(hours=1),
                    ),
                    angle=self.angle,
                    job_id=self.job_id,
                    wavelength=channel,
                )
                return cv2.cvtColor(
                    self.load_source_file(filename=ret[0][0]),
                    cv2.COLOR_BGR2HSV,
                )[:, :, 2]
            except:
                return None
        else:
            return c

    @property
    def job_id(self):
        return self._job_id

    @property
    def robot(self):
        if "phenopsis" in self.camera:
            return "phenopsis"
        elif "phenoserre" in self.camera:
            return "phenoserre"
        elif "robotracine" in self.camera:
            return "robotracine"
        else:
            return ""

    @classmethod
    def probe(cls, file_path, database):
        return (
            100
            if (database is None or database.target != "tpmp")
            and isinstance(file_path, str)
            and os.path.isfile(file_path)
            and "#" in cls.extract_file_name(file_path)
            else 0
        )

    @property
    def linked_images(self):
        if not self._linked_images:
            ret = self._database.query(
                command="SELECT",
                columns="filepath",
                experiment=self.experiment,
                plant=self.plant,
                date_time=dict(
                    operator="BETWEEN",
                    date_min=self.date_time - datetime.timedelta(hours=1),
                    date_max=self.date_time + datetime.timedelta(hours=1),
                ),
                job_id=self.job_id,
            )
            self._linked_images = [
                item[0] for item in ret if self.file_path not in item[0]
            ]
        return self._linked_images

    @property
    def available_channels(self):
        if not self._available_channels:
            ret = self._database.query(
                command="SELECT",
                columns="wavelength",
                experiment=self.experiment,
                plant=self.plant,
                date_time=dict(
                    operator="BETWEEN",
                    date_min=self.date_time - datetime.timedelta(hours=1),
                    date_max=self.date_time + datetime.timedelta(hours=1),
                ),
                angle=self.angle,
                job_id=self.job_id,
            )
            wavelengths = [item[0] for item in ret]
            for wave in wavelengths:
                if wave.lower() == "sw755":
                    self._available_channels.update(ipc.CHANNELS_VISIBLE)
                else:
                    self._available_channels.update({wave: wave})

        return self._available_channels

    @property
    def channels(self):
        return {}
