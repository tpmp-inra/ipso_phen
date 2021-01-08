import logging
from collections import defaultdict
import os
import json

import paramiko
import pandas as pd
from stat import S_ISDIR

from ipso_phen.ipapi.database.pandas_wrapper import PandasDbWrapper
from ipso_phen.ipapi.file_handlers.fh_phenopsys import FileHandlerPhenopsis
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
logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))


PHENOPSIS_ROOT_FOLDER = "./phenopsis"
FILES_PER_CONNEXION = 400
IMAGE_EXTENSIONS = (".jpg", ".tiff", ".png", ".bmp", ".tif", ".pim", ".csv")


def connect_to_phenodb():
    p = paramiko.SSHClient()
    p.set_missing_host_key_policy(paramiko.AutoAddPolicy)
    p.connect(
        GENOLOGIN_ADDRESS,
        port=TPMP_PORT,
        username=dbc["user"],
        password=dbc["password"],
    )
    return p


def get_pheno_db_ftp():
    return connect_to_phenodb().open_sftp()


def get_phenopsis_exp_list() -> list:
    assert dbc, "Unable to connect to phenoserre"
    try:
        ftp = get_pheno_db_ftp()
        exp_lst = sorted(ftp.listdir(path=PHENOPSIS_ROOT_FOLDER))
        ftp.close()
    except Exception as e:
        logger.error(f"Unable to reach Phenopsis: {repr(e)}")
        return []
    else:
        return [exp for exp in exp_lst if exp != "csv"]


def isdir(ftp, path):
    try:
        return S_ISDIR(ftp.stat(path).st_mode)
    except IOError:
        # Path does not exist, so by definition not a directory
        return False


class PhenopsisDbWrapper(PandasDbWrapper):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.df_builder = self.get_exp_as_df
        self.main_selector = {"view_option": "sw755"}

    def get_all_files(
        self,
        ftp,
        path,
        extensions,
    ):
        ret = []
        sf = ftp.listdir_attr(path=path)
        for fd in sf:
            obj_path = f"{path}/{fd.filename}"
            self._callback_undefined()
            if isdir(ftp=ftp, path=obj_path):
                ret.extend(
                    self.get_all_files(
                        ftp=ftp,
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
        dataframe["Experiment"] = dataframe["experiment"].str.lower()
        dataframe["Plant"] = dataframe["plant"].str.lower()
        dataframe["date_time"] = pd.to_datetime(dataframe["date_time"], utc=True)
        dataframe["Camera"] = dataframe["camera"]
        dataframe["FilePath"] = dataframe["filepath"].str.replace("./phenopsis/", "")
        dataframe["Luid"] = dataframe["luid"]
        return dataframe[
            [
                "Luid",
                "Experiment",
                "Plant",
                "date_time",
                "Camera",
                "view_option",
                "FilePath",
                "blob_path",
            ]
        ]

    def get_exp_as_df(self, exp_name: str) -> pd.DataFrame:
        ftp = get_pheno_db_ftp()
        csv_path = (
            PHENOPSIS_ROOT_FOLDER + "/" + "csv" + "/" + f"{exp_name.lower()}.dst.csv"
        )
        try:
            ftp.stat(csv_path)
        except Exception as _:
            logger.info(f"Missing CSV for {exp_name}, building it")
            self._init_progress_undefined("Looking for images")
            images = self.get_all_files(
                ftp=ftp,
                path=PHENOPSIS_ROOT_FOLDER + "/" + exp_name,
                extensions=IMAGE_EXTENSIONS,
            )
            self._close_progress_undefined(f"Found {len(images)} images")

            self._init_progress(total=len(images), desc="Building dataframe")
            d = defaultdict(list)
            for j, fh in enumerate(images):
                d["Luid"].append(fh.luid)
                d["Experiment"].append(fh.experiment)
                d["Plant"].append(fh.plant)
                d["date_time"].append(fh.date_time)
                d["Camera"].append(fh.camera)
                d["view_option"].append(fh.view_option)
                d["FilePath"].append(fh.file_path)
                d["blob_path"].append(fh.file_path)
                self._callback(step=j, total=len(images))
            self._close_progress()
            logger.info(f"Built CSV for {exp_name}")
            dataframe = pd.DataFrame(d)
            dataframe.to_csv(self.cache_file_path)
        else:
            file = ftp.open(csv_path)
            dataframe = pd.read_csv(file)
            file.close()
            dataframe["Experiment"] = dataframe["experiment"].str.lower()
            dataframe["Plant"] = dataframe["plant"].str.lower()
            dataframe["date_time"] = pd.to_datetime(dataframe["date_time"], utc=True)
            dataframe["Camera"] = dataframe["camera"]
            dataframe["FilePath"] = dataframe["filepath"]
            dataframe["Luid"] = dataframe["luid"]
            dataframe = dataframe[
                [
                    "Luid",
                    "Experiment",
                    "Plant",
                    "date_time",
                    "Camera",
                    "view_option",
                    "FilePath",
                    "blob_path",
                ]
            ]
        finally:
            ftp.close()
        return dataframe
