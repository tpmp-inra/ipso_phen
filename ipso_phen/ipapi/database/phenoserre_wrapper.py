import os
import json
import paramiko
import pandas as pd
from io import StringIO
import logging
from tqdm import tqdm

import psycopg2

from ipso_phen.ipapi.database.pandas_wrapper import PandasDbWrapper
from ipso_phen.ipapi.database.db_passwords import get_user_and_password, check_password

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))


def _split_camera_label(cam_label: str) -> tuple:
    """
    Split camera and view option tag from numerous formats to camera and angle/wavelenght
    :param cam_label: str
    :res =: tuple camera & view option
    """
    cam_label = cam_label.lower()
    res = None
    if ("-" in cam_label) and ("_" in cam_label):
        # Brachy_Vis-Side225
        _, tmp = cam_label.split("_")
        res = tmp.split("-")
    elif "-" in cam_label:
        tmp = cam_label.split("-")
        if len(tmp) == 2:
            if "in" in tmp:
                # FluTop - In
                res = tmp[0][0:3], tmp[0][3:]
            else:
                # FLUO-Side45, MSP - BP520
                res = tmp
        elif len(tmp) == 3:
            if "in" in tmp:
                # Fluo-Side-In
                res = tmp[0], tmp[1]
            elif "r" in tmp[2]:
                if tmp[1] == "side":
                    # vis-side-R0
                    res = tmp[0], tmp[1] + tmp[2][1:]
                else:
                    # GGT-Fluo-r0
                    res = tmp[1], f"side{tmp[2][1:]}"
            elif "top" in tmp[2]:
                # GGT-Vis-Top
                res = tmp[1], tmp[2]
            else:
                # fluo-side-180
                res = tmp[0], tmp[1] + tmp[2]
        else:
            raise ValueError
    elif "_" in cam_label:
        tmp = cam_label.split("_")
        if len(tmp) == 2:
            if tmp[1] == "sv":
                # fluo_sv
                res = tmp[0], "unk"
            elif tmp[1] == "tv":
                # fluo_tv
                res = tmp[0], "top"
            else:
                raise ValueError
    elif "h1r" in cam_label:
        # fluoSideH1R0, fluoTopH1R0
        res = _split_camera_label(cam_label.replace("h1r", ""))
    elif "msp" in cam_label:
        res = "msp", "unk"
    elif ("fluo" in cam_label) or ("nir" in cam_label) or ("vis" in cam_label):
        if "fluo" in cam_label:
            cam = "fluo"
            idx = 4
        elif "nir" in cam_label:
            cam = "nir"
            idx = 3
        elif "vis" in cam_label:
            cam = "vis"
            idx = 3
        else:
            res = None
            raise ValueError
        if "top" in cam_label:
            # fluoTop
            res = cam, "top"
        else:
            # fluo90, fluoSide90
            angle = cam_label[idx:]
            if "side" not in angle:
                angle = f"side{angle}"
            res = cam, angle
    elif "topview" in cam_label:
        res = "unk", "top"
    else:
        raise ValueError

    if res is not None:
        if res[0] == "flu":
            res = "fluo", res[1]

        if res[1] == "side":
            res = res[0], "side0"

    return res


def _query_phenoserre(query: str) -> pd.DataFrame:
    u, p = get_user_and_password("old_phenoserre_db")
    if u is None or p is None:
        logger.warning("Missing connection data for server")
        return pd.DataFrame()
    try:
        conn = psycopg2.connect(
            host="lipm-data.toulouse.inra.fr",
            database="LemnaTecOptimalogTest",
            user=u,
            password=p,
            port=5434,
        )
    except Exception as e:
        logger.error(f"Unable to query Phenoserre: {repr(e)}")
        return pd.DataFrame()

    df = pd.read_sql_query(query, conn)

    return df


def get_phenoserre_exp_list() -> list:
    if check_password(key="phenoserre") is False:
        return []
    try:
        exp_list = sorted(
            _query_phenoserre("select distinct measurement_label from snapshot")
            .iloc[:, 0]
            .to_list()
        )
    except Exception as e:
        logger.error(f"Unable to connect to Phenoserre: {repr(e)}")
        return []
    else:
        return exp_list


def get_exp_as_df(exp_name: str) -> pd.DataFrame:
    dataframe = _query_phenoserre(
        query=f"""select
                    s.measurement_label as Experiment,
                    s.id_tag as Plant,
                    ti.camera_label as cam_view_option,
                    s.time_stamp as date_time,
                    file.path as blob_path
                from
                    snapshot as s, tiled_image as ti, tile as t, image_file_table as file
                where
                    s.measurement_label = '{exp_name}' and
                    s.id = ti.snapshot_id and
                    ti.id = t.tiled_image_id and
                    t.raw_image_oid = file.id
                order by s.time_stamp asc"""
    ).reset_index(drop=True)

    # Lowercase all
    dataframe["experiment"] = dataframe["experiment"].str.lower()
    dataframe["plant"] = dataframe["plant"].str.lower()
    dataframe["cam_view_option"] = dataframe["cam_view_option"].str.lower()
    # Ensure datetime column is datetim
    dataframe["date_time"] = pd.to_datetime(dataframe["date_time"], utc=True)
    # Wrangle
    dataframe[["camera", "angle"]] = (
        dataframe["cam_view_option"].apply(_split_camera_label).apply(pd.Series)
    )
    dataframe["wavelength"] = "SW755"
    dataframe["filepath"] = (
        dataframe["experiment"]
        + "/"
        + "("
        + dataframe["plant"]
        + ")--("
        + dataframe["date_time"].dt.strftime("%Y-%m-%d %H_%M_%S")
        + ")--("
        + dataframe["experiment"]
        + ")--("
        + dataframe["camera"]
        + "-"
        + dataframe["angle"]
        + ").png"
    )
    dataframe["luid"] = (
        dataframe["experiment"]
        + "_"
        + dataframe["plant"]
        + "_"
        + dataframe["date_time"].dt.strftime("%Y%m%d%H%M%S")
        + "_"
        + dataframe["camera"]
        + "_"
        + dataframe["angle"]
    )
    dataframe["blob_path"] = dataframe["blob_path"].map(
        "./ftp/LemnaTecOptimalogTest/{}".format
    )
    dataframe["wavelength"] = "SW755"
    dataframe["height"] = 0
    dataframe["job_id"] = 0

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
            "wavelength",
            "height",
            "job_id",
        ]
    ]


class PhenoserreDbWrapper(PandasDbWrapper):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.df_builder = get_exp_as_df

    def check_dataframe(self, dataframe) -> pd.DataFrame:
        dataframe = super().check_dataframe(dataframe=dataframe)
        return dataframe
