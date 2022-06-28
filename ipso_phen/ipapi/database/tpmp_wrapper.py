import os
import logging

import pandas as pd
import pandas.io.sql as sqlio

import psycopg2

from ipso_phen.ipapi.database.pandas_wrapper import PandasDbWrapper
from ipso_phen.ipapi.database.db_passwords import get_user_and_password, check_password

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))


def get_db_connexion():
    u, p = get_user_and_password("tpmp")
    return psycopg2.connect(
        host="lipm-data.toulouse.inra.fr",
        database="TPMP",
        user=u,
        password=p,
        port=5434,
    )


def _query_tpmp(query: str) -> pd.DataFrame:
    conn = get_db_connexion()
    try:
        cur = conn.cursor()
        cur.execute(query)
        return cur.fetchall()
    finally:
        conn.close()


def get_tpmp_exp_list() -> list:
    if check_password(key="tpmp") is False:
        return []
    try:
        exp_list = [
            i[0] for i in sorted(_query_tpmp("select distinct name from dbms_experiment"))
        ]
    except Exception as e:
        logger.error(f"Unable to connect to Phenoserre: {repr(e)}")
        return []
    else:
        return exp_list


def get_image_data(filename) -> dict:
    conn = get_db_connexion()
    columns = [
        "experiment",
        "plant",
        "camera",
        "date_time",
        "angle",
        "wavelength",
        "height",
        "job_id",
        "filepath",
    ]
    columns_str = ",".join(columns)
    try:
        cur = conn.cursor()
        cur.execute(f"SELECT {columns_str} FROM dbms_photo WHERE filename = '{filename}'")
        data = {k: v for k, v in zip(columns_str, cur.fetchone())}
    except:
        data = {k: None for k in columns_str}
    finally:
        conn.close()
        return data


def get_exp_as_df(exp_name: str) -> pd.DataFrame:
    conn = get_db_connexion()
    try:
        df = sqlio.read_sql_query(
            f"""
            select 
                experiment.name as Experiment, 
                plant.name as Plant, 
                camera.label as Camera,
                photo.timestamp as date_time,
                photo.angle as Angle,
                photo.wavelength as Wavelength,
                photo.height as Height,
                photo.job_id as Job_Id,
                photo.filename as FilePath
            from 
                dbms_photo as photo, 
                dbms_experiment as experiment, 
                dbms_plant as plant,
                dbms_sensor as camera
            where 
                photo.experiment_id = (select id from dbms_experiment where name = '{exp_name}') and
                experiment.id = photo.experiment_id and 
                plant.id = photo.plant_id and
                camera.id = photo.camera_id             
            order by photo.timestamp asc 
            """,
            conn,
        )
        df.date_time = pd.to_datetime(df.date_time, utc=True, infer_datetime_format=True)
    except:
        return pd.DataFrame()
    else:
        df.columns = [
            "experiment",
            "plant",
            "camera",
            "date_time",
            "angle",
            "wavelength",
            "height",
            "job_id",
            "filepath",
        ]
        return df
    finally:
        conn.close()


class TpmpDbWrapper(PandasDbWrapper):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.df_builder = get_exp_as_df
        self.main_selector = {"wavelength": "SW755"}

    def connect_from_cache(self) -> pd.DataFrame:
        return None

    def connect(self, auto_update: bool = True):
        if self.dataframe is None:
            self.dataframe = self.df_builder(self.db_info.display_name)
            self.dataframe = self.check_dataframe(dataframe=self.dataframe)

    def check_dataframe(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        dataframe = super().check_dataframe(dataframe=dataframe)
        dataframe["luid"] = dataframe["filepath"]
        for column in dataframe.select_dtypes("number").columns:
            dataframe[column] = dataframe[column].map(str)
        return dataframe
