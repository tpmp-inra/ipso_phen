# from datetime import datetime as dt
import datetime
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
        data = {
            k: list(v.values())[0]
            for k, v in self._database.dataframe[
                self._database.dataframe.luid == self._file_path
            ]
            .to_dict()
            .items()
        }
        self._exp = data["experiment"]
        self._plant = data["plant"]
        self._camera = data["camera"]
        self._angle = data["angle"]
        self._wavelength = data["wavelength"]
        self._job_id = data["job_id"]
        self._date_time = data["date_time"]
        self._luid = data["luid"]
        self.db_linked = True

    def load_source_file(self, filename=None):
        if filename is None:
            fcp = self.cache_file_path
        else:
            fcp = os.path.join(self.cache_file_dir, filename)
        if os.path.isfile(fcp):
            logger.debug(f"Retrieved from cache: {str(self)}")
            return self.load_from_harddrive(fcp)
        elif self.db_linked:
            sftp = connect_to_lipmcalcul(target_ftp=True)
            try:
                return self.load_from_database(sftp, fcp, filename)
            except Exception as e:
                logger.exception(f"Failed to download {repr(self)} because {repr(e)}")
                return None
            finally:
                sftp.close()
        else:
            return self.load_from_harddrive()

    def load_from_database(self, sftp, file_cache_path, filename=None):
        logger.info(f"Downloading {self.name}, please wait...")
        force_directories(self.cache_file_dir)
        sftp.get(
            f"images/{self.robot}/{self.experiment}/{self.file_name if filename is None else filename}",
            file_cache_path,
        )
        total, _, free = shutil.disk_usage("/")
        p = (
            pathlib.PureWindowsPath(self.cache_file_dir)
            if platform.system().lower() == "windows"
            else pathlib.PurePath(self.cache_file_dir)
        )
        logger.info(
            f"Download succeeded for {self.name if filename is None else filename}, {free // (2**30)}GiB remaining of {total // (2**30)}GiB in {p.parts[0]}"
        )
        return self.load_from_harddrive(override_path=self.cache_file_path)

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
        return 100 if database is not None and database.target == "tpmp" else 0

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
