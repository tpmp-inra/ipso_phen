# from datetime import datetime as dt
# import datetime
import os
from pathlib import Path

# import json

from ipso_phen.ipapi.file_handlers.fh_base import FileHandlerBase

# import ipso_phen.ipapi.base.ip_common as ipc
# from ipso_phen.ipapi.tools.folders import ipso_folders
# from ipso_phen.ipapi.database.db_passwords import get_user_and_password, check_password
# from ipso_phen.ipapi.database.base import connect_to_lipmcalcul
# from ipso_phen.ipapi.database.tpmp_wrapper import get_image_data
from ipso_phen.ipapi.tools.folders import ipso_folders
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
        self.db_linked = True

    def load_source_file(self):
        if self.db_linked:
            sftp = connect_to_lipmcalcul(target_ftp=True)
            try:
                return self.load_from_database(sftp)
            except Exception as e:
                logger.exception(f"Failed to download {repr(self)} because {repr(e)}")
                return None
            finally:
                sftp.close()
        else:
            return self.load_from_harddrive()

    def load_from_database(self, sftp):
        if os.path.isdir(ipso_folders.get_path("mass_storage", False)) and os.path.isfile(
            self.cache_file_path
        ):
            logger.debug(f"Retrieved from cache: {str(self)}")
            return self.load_from_harddrive(self.cache_file_path)
        logger.info(f"Downloading {self.name}, please wait...")
        sftp.get(
            f"images/{self.robot}/{self.experiment}/{self.file_name}",
            self.cache_file_path,
        )
        logger.info(f"Download succeeded for  {self.name}")
        return self.load_from_harddrive(override_path=self.cache_file_path)

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
        return 100 if database.target == "tpmp" else 0

    @property
    def linked_images(self):
        if not self._linked_images:
            ret = self._database.query(
                command="SELECT",
                columns="filepath",
                experiment=self.experiment,
                plant=self.plant,
                job_id=self.job_id,
            )
            self._linked_images = [
                item[0] for item in ret if self.file_path not in item[0]
            ]
        return self._linked_images
