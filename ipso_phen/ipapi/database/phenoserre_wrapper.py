import os
import json
import paramiko
import pandas as pd
from io import StringIO
import logging
from tqdm import tqdm

from ipso_phen.ipapi.database.pandas_wrapper import PandasDbWrapper
from ipso_phen.ipapi.tools.folders import ipso_folders
from ipso_phen.ipapi.database.db_consts import (
    GENOLOGIN_ADDRESS,
    TPMP_PORT,
    PHENODB_ADDRESS,
)

dbc_path = os.path.join(
    ipso_folders.get_path("db_connect_data", force_creation=False),
    "db_connect_data.json",
)
if os.path.isfile(dbc_path):
    with open(dbc_path, "r") as f:
        dbc = json.load(f)["phenoserre"]
else:
    dbc = {}

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

    assert dbc, "Unable to connect to phenoserre"

    # Create jump ssh connexion
    jump_connexion = paramiko.SSHClient()
    jump_connexion.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    jump_connexion.connect(
        GENOLOGIN_ADDRESS,
        port=TPMP_PORT,
        username=dbc["user"],
        password=dbc["password"],
    )

    # Create transport
    jump_transport = jump_connexion.get_transport()
    dest_addr = (PHENODB_ADDRESS, TPMP_PORT)
    local_addr = (GENOLOGIN_ADDRESS, TPMP_PORT)
    jump_channel = jump_transport.open_channel(
        "direct-tcpip",
        dest_addr,
        local_addr,
    )

    # Create target connexion
    host_connexion = paramiko.SSHClient()
    host_connexion.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    host_connexion.connect(
        PHENODB_ADDRESS,
        username=dbc["user"],
        password=dbc["password"],
        sock=jump_channel,
    )

    # Query and return result
    _, stdout, _ = host_connexion.exec_command(
        'psql -A -F , -q -P "footer=off" -d LemnaTecOptimalogTest -U phenodbpg -c '
        + f'"{query}"'
    )
    output = stdout.readlines()
    output = "".join(output)
    return pd.read_csv(StringIO(output))


def get_phenoserre_exp_list() -> list:
    assert dbc, "Unable to connect to phenoserre"
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
    dataframe["Experiment"] = dataframe["experiment"].str.lower()
    dataframe["Plant"] = dataframe["plant"].str.lower()
    dataframe["cam_view_option"] = dataframe["cam_view_option"].str.lower()
    # Ensure datetime column is datetim
    dataframe["date_time"] = pd.to_datetime(dataframe["date_time"], utc=True)
    # Wrangle
    dataframe[["Camera", "view_option"]] = (
        dataframe["cam_view_option"].apply(_split_camera_label).apply(pd.Series)
    )
    dataframe["FilePath"] = (
        dataframe["Experiment"]
        + "/"
        + "("
        + dataframe["Plant"]
        + ")--("
        + dataframe["date_time"].dt.strftime("%Y-%m-%d %H_%M_%S")
        + ")--("
        + dataframe["Experiment"]
        + ")--("
        + dataframe["Camera"]
        + "-"
        + dataframe["view_option"]
        + ").png"
    )
    dataframe["Luid"] = (
        dataframe["Experiment"]
        + "_"
        + dataframe["Plant"]
        + "_"
        + dataframe["date_time"].dt.strftime("%Y%m%d%H%M%S")
        + "_"
        + dataframe["Camera"]
        + "_"
        + dataframe["view_option"]
    )
    dataframe["blob_path"] = dataframe["blob_path"].map(
        "./ftp/LemnaTecOptimalogTest/{}".format
    )

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


class PhenoserreDbWrapper(PandasDbWrapper):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.df_builder = get_exp_as_df
