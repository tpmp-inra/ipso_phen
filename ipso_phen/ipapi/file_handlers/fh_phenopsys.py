from datetime import datetime as dt
import datetime
import os
import json

from ipso_phen.ipapi.file_handlers.fh_base import FileHandlerBase
import ipso_phen.ipapi.base.ip_common as ipc
from ipso_phen.ipapi.tools.folders import ipso_folders
from ipso_phen.ipapi.database.db_consts import TPMP_PORT, GENOLOGIN_ADDRESS

dbc_path = os.path.join(
    ipso_folders.get_path("db_connect_data", force_creation=False),
    "db_connect_data.json",
)
if os.path.isfile(dbc_path):
    with open(dbc_path, "r") as f:
        dbc = json.load(f)["phenopsis"]
else:
    dbc = {}

import logging

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))


class FileHandlerPhenopsis(FileHandlerBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._database = kwargs.get("database", None)
        self.db_linked = (
            dbc
            and self._database is not None
            and self._database.db_info.target == "phenopsis"
        ) is True
        self._file_path = kwargs.get("file_path", "")
        self._linked_images = []
        if self._file_path:
            [
                self._exp,
                self._plant,
                self._view_option,
                date_time_str,
                self._opaque,
            ] = self.file_name_no_ext.split(";")
            if not self.db_linked:
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

    def load_source_file(self):
        if self.db_linked:
            return self.load_from_database(
                address=GENOLOGIN_ADDRESS,
                port=TPMP_PORT,
                user=dbc["user"],
                pwd=dbc["password"],
            )
        else:
            return self.load_from_harddrive()

    @classmethod
    def probe(cls, file_path, database):
        if (
            isinstance(file_path, str)
            and os.path.isfile(file_path)
            and (";" in cls.extract_file_name(file_path))
        ):
            return 100
        elif dbc and database is not None and database.db_info.target == "phenopsis":
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
            ret = self._database.query(
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
