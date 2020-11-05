import os
import logging
from sqlalchemy.inspection import _self_inspects
from tqdm import tqdm

import pandas as pd

from ipapi.database.base import QueryHandler, DbWrapper
from ipapi.tools.common_functions import force_directories

logger = logging.getLogger(__name__)


class PandasQueryHandler(QueryHandler):
    @staticmethod
    def format_key(key, value):
        pass

    def query(
        self,
        command: str,
        table: str = "snapshots",
        columns: str = "*",
        additional: str = "",
        **kwargs,
    ):
        if self.connect() is False:
            return None
        return self.query_to_pandas(
            command=command,
            table=table,
            columns=columns,
            additional=additional,
            **kwargs,
        ).to_numpy()

    def query_to_pandas(
        self,
        command: str,
        table: str = "snapshots",
        columns: str = "*",
        additional: str = "",
        **kwargs,
    ):
        assert "select" in command.lower(), f"Can't handle {command} command"

        if self.connect() is False:
            return None

        def match_column(c: str, cols: list) -> str:
            if c in cols:
                return c
            for col in cols:
                if c.lower() == col.lower():
                    return col
            else:
                return ""

        res_df = self.dataframe.copy()
        if kwargs:
            for k, v in kwargs.items():
                k = match_column(k, res_df.columns)
                if not k:
                    continue
                if isinstance(v, dict):
                    if v["operator"].lower() == "between":
                        res_df = res_df[
                            (res_df[k] >= v["date_min"]) & (res_df[k] <= v["date_max"])
                        ]
                    else:
                        logger.error(f"Unknown operator: {v['operator']}")
                else:
                    res_df = res_df[res_df[k].isin([v])]

        if additional:
            assert "order by" in additional.lower(), f"Can't handle {additional}"
            _, _, column, direction = additional.split(" ")
            res_df = res_df.sort_values(by=column, ascending=direction.lower() == "asc")

        if columns != "*":
            res_df = res_df[
                [
                    c
                    for c in [
                        match_column(c, res_df.columns)
                        for c in columns.replace(" ", "").split(",")
                    ]
                    if c
                ]
            ]

        if "distinct" in command.lower():
            res_df = res_df.drop_duplicates()

        return res_df

    def query_one(
        self,
        command: str,
        table: str = "snapshots",
        columns: str = "*",
        additional: str = "",
        **kwargs,
    ):
        if self.connect() is False:
            return None

        ret = self.query(
            command=command, columns=columns, table=table, additional=additional, **kwargs
        )
        if (ret is not None) and (len(ret) > 0):
            return ret[0]
        else:
            return None

    @property
    def dbms(self) -> str:
        return "pandas"


class PandasDbWrapper(DbWrapper, PandasQueryHandler):
    dataframe = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.df_builder = None

    def __del__(self):
        pass

    def copy(self):
        return self.__class__(db_info=self.db_info.copy())

    def connect_from_cache(self) -> pd.DataFrame:
        cache_file_path = self.cache_file_path
        if os.path.isfile(cache_file_path):
            return pd.read_csv(
                cache_file_path,
                parse_dates=[4],
            ).reset_index(drop=True)
        else:
            return None

    def connect(self, auto_update: bool = True):
        if self.dataframe is None:
            self.dataframe = self.connect_from_cache()
            cache_file_path = self.cache_file_path
            if self.dataframe is None:
                self.dataframe = self.df_builder(self.db_info.display_name)
                force_directories(self.cache_folder)
                self.dataframe.to_csv(cache_file_path)
            temp_date_time = pd.DatetimeIndex(self.dataframe["date_time"])
            self.dataframe.insert(loc=4, column="Time", value=temp_date_time.time)
            self.dataframe.insert(loc=4, column="Date", value=temp_date_time.date)

    def open_connexion(self) -> bool:
        return self.dataframe is not None

    def close_connexion(self):
        pass

    def update(
        self,
        db_qualified_name="",
        extensions: tuple = (".jpg", ".tiff", ".png", ".bmp"),
    ):
        self.reset()

    def is_exists(self):
        return True

    def reset(self):
        cache_file_path = self.cache_file_path
        if os.path.isfile(cache_file_path):
            os.remove(cache_file_path)
        self.connect()

    @property
    def cache_file_path(self):
        return os.path.join(
            self.cache_folder,
            f"{self.db_info.display_name}.csv",
        )

    @property
    def cache_folder(self):
        return os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "cache",
            "",
        )
