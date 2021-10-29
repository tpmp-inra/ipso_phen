import logging
from collections import defaultdict
import os
import pandas as pd
from stat import S_ISDIR

from ipso_phen.ipapi.database.pandas_wrapper import PandasDbWrapper
from ipso_phen.ipapi.file_handlers.fh_phenopsys import FileHandlerPhenopsis
from ipso_phen.ipapi.tools.folders import ipso_folders
from ipso_phen.ipapi.database.db_passwords import check_password
from ipso_phen.ipapi.database.base import connect_to_lipmcalcul

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))


PHENOPSIS_ROOT_FOLDER = "./phenopsis"
FILES_PER_CONNEXION = 400
IMAGE_EXTENSIONS = (".jpg", ".tiff", ".png", ".bmp", ".tif", ".pim", ".csv")


def get_phenopsis_exp_list() -> list:
    if check_password("phenopsis") is False:
        return []
    sftp = connect_to_lipmcalcul(target_ftp=False)
    try:
        exp_lst = sorted(sftp.listdir(path=PHENOPSIS_ROOT_FOLDER))
    except Exception as e:
        logger.error(f"Unable to reach Phenopsis: {repr(e)}")
        return []
    else:
        return [exp for exp in exp_lst if exp != "csv"]
    finally:
        sftp.close()


def isdir(sftp, path):
    try:
        return S_ISDIR(sftp.stat(path).st_mode)
    except IOError:
        # Path does not exist, so by definition not a directory
        return False


class PhenopsisDbWrapper(PandasDbWrapper):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.df_builder = self.get_exp_as_df
        self.main_selector = {"wavelength": "sw755"}

    def check_dataframe(self, dataframe) -> pd.DataFrame:
        dataframe = super().check_dataframe(dataframe=dataframe)
        if "view_option" in dataframe:
            dataframe["wavelength"] = dataframe["view_option"]
            dataframe["angle"] = "0"
            dataframe["height"] = "0"
            dataframe["job_id"] = "0"
        return dataframe

    def get_all_files(
        self,
        sftp,
        path,
        extensions,
    ):
        ret = []
        sf = sftp.listdir_attr(path=path)
        for fd in sf:
            obj_path = f"{path}/{fd.filename}"
            self._callback_undefined()
            if isdir(sftp=sftp, path=obj_path):
                ret.extend(
                    self.get_all_files(
                        sftp=sftp,
                        path=obj_path,
                        extensions=extensions,
                    )
                )
            else:
                if obj_path.lower().endswith(extensions):
                    ret.append(FileHandlerPhenopsis(file_path=obj_path, database=None))
        return ret

    def get_local_df(self, exp_name) -> pd.DataFrame:
        csv_path = os.path.join(
            ipso_folders.get_path("database_builders", force_creation=True),
            f"{exp_name.lower()}.dst.csv",
        )
        dataframe = pd.read_csv(csv_path)
        dataframe["experiment"] = dataframe["experiment"].str.lower()
        dataframe["plant"] = dataframe["plant"].str.lower()
        dataframe["date_time"] = pd.to_datetime(dataframe["date_time"], utc=True)
        dataframe["camera"] = dataframe["camera"]
        dataframe["filepath"] = dataframe["filepath"].str.replace(
            "./images/phenopsis/", ""
        )
        dataframe["luid"] = dataframe["luid"]
        return dataframe[
            [
                "luid",
                "experiment",
                "plant",
                "date_time",
                "camera",
                "angle",
                "filepath",
                "blob_path",
            ]
        ]

    def get_exp_as_df(self, exp_name: str) -> pd.DataFrame:
        sftp = connect_to_lipmcalcul(target_ftp=False)
        csv_path = (
            PHENOPSIS_ROOT_FOLDER + "/" + "csv" + "/" + f"{exp_name.lower()}.dst.csv"
        )
        try:
            sftp.stat(csv_path)
        except Exception as _:
            logger.info(f"Missing CSV for {exp_name}, building it")
            self._init_progress_undefined("Looking for images")
            images = self.get_all_files(
                sftp=sftp,
                path=PHENOPSIS_ROOT_FOLDER + "/" + exp_name,
                extensions=IMAGE_EXTENSIONS,
            )
            self._close_progress_undefined(f"Found {len(images)} images")

            self._init_progress(total=len(images), desc="Building dataframe")
            d = defaultdict(list)
            for j, fh in enumerate(images):
                d["luid"].append(fh.luid)
                d["experiment"].append(fh.experiment)
                d["plant"].append(fh.plant)
                d["date_time"].append(fh.date_time)
                d["camera"].append(fh.camera)
                d["angle"].append(fh.angle)
                d["wavelength"].append(fh.wavelength)
                d["filepath"].append(fh.file_path)
                d["blob_path"].append(fh.file_path)
                self._callback(step=j, total=len(images))
            self._close_progress()
            logger.info(f"Built CSV for {exp_name}")
            dataframe = pd.DataFrame(d)
            dataframe.to_csv(self.cache_file_path)
        else:
            file = sftp.open(csv_path)
            dataframe = pd.read_csv(file)
            file.close()
            dataframe["experiment"] = dataframe["experiment"].str.lower()
            dataframe["plant"] = dataframe["plant"].str.lower()
            dataframe["date_time"] = pd.to_datetime(dataframe["date_time"], utc=True)
            dataframe["camera"] = dataframe["camera"]
            dataframe["filepath"] = dataframe["filepath"]
            dataframe["luid"] = dataframe["luid"]
            dataframe = dataframe[
                [
                    "luid",
                    "experiment",
                    "plant",
                    "date_time",
                    "camera",
                    "angle",
                    "wavelength",
                    "filepath",
                    "blob_path",
                ]
            ]
        finally:
            sftp.close()
        return dataframe
