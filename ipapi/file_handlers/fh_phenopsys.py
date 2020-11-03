from datetime import datetime as dt
import datetime
import os

import numpy as np
import cv2
import paramiko

from ipapi.file_handlers.fh_base import FileHandlerBase
import ipapi.base.ip_common as ipc


try:
    from ipapi.database.db_connect_data import db_connect_data as dbc

    conf = dbc.get("phenopsis", {})
except Exception as e:
    conf = {}

import logging

logger = logging.getLogger(__name__)


class FileHandlerPhenopsis(FileHandlerBase):
    def __init__(self, **kwargs):
        self._file_path = kwargs.get("file_path", "")
        self.database = kwargs.get("database", None)
        self._linked_images = []
        if self._file_path:
            [
                self._exp,
                self._plant,
                self._view_option,
                date_time_str,
                self._opaque,
            ] = self.file_name_no_ext.split(";")
            try:
                self._date_time = dt.strptime(date_time_str, "%Y,%m,%d-%Hh%Mm%Ss")
            except ValueError:
                self._date_time = dt.strptime(date_time_str, "%Y%m%d-%Hh%Mm%Ss")
            if "fluo-" in self._view_option.lower():
                self._camera = "cf"
                if self.is_cf_calc:
                    self._view_option = "calc"
                elif self.is_cf_csv:
                    self._view_option = "csv"
                elif self.is_cf_pim:
                    self._view_option = "pim"
                elif self.is_cf_raw:
                    self._view_option = "raw"
            else:
                self._camera, self._view_option = self._view_option.split("-")

        self.update(**kwargs)

    @classmethod
    def probe(cls, file_path, database):
        if not isinstance(file_path, str) or not os.path.isfile(file_path):
            return 0
        elif ";" in cls.extract_file_name(file_path):
            return 100
        else:
            return 0

    @property
    def is_cf_calc(self):
        return (self.view_option == "fluo-") and (self.file_ext.lower() == ".jpg")

    @property
    def is_cf_raw(self):
        return (self.view_option == "fluo-") and (self.file_ext.lower() == ".tif")

    @property
    def is_cf_csv(self):
        return (self.view_option == "fluo-") and (self.file_ext.lower() == ".csv")

    @property
    def is_cf_pim(self):
        return (self.view_option == "fluo-") and (self.file_ext.lower() == ".pim")

    @property
    def is_msp(self):
        return ("msp" in self.camera) or ("msp" in self.view_option)

    @property
    def is_vis(self):
        return False

    @property
    def channels_data(self):
        return [
            ci
            for ci in ipc.create_channel_generator(
                include_vis=True,
                include_msp=True,
            )
        ]

    @property
    def linked_images(self):
        if not self._linked_images:
            current_date_time = self.date_time
            ret = self.database.query(
                command="SELECT",
                columns="FilePath",
                additional="ORDER BY date_time ASC",
                experiment=self.experiment,
                plant=self.plant,
                camera=self.camera,
                date_time=dict(
                    operator="BETWEEN",
                    date_min=current_date_time - datetime.timedelta(hours=1),
                    date_max=current_date_time + datetime.timedelta(hours=1),
                ),
            )
            self._linked_images = [
                item[0] for item in ret if "sw755" not in item[0].lower()
            ]
        return self._linked_images


class DirectHandlerPhenopsis(FileHandlerPhenopsis):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.init_from_database(**kwargs)

    def load_source_file(self):
        return self.load_from_database(
            address=conf["address"],
            port=conf["port"],
            user=conf["user"],
            pwd=conf["password"],
        )

    @classmethod
    def probe(cls, file_path, database):
        return (
            90
            if conf and database is not None and database.db_info.target == "phenopsis"
            else 0
        )
