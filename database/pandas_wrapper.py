import os
import logging
from tqdm import tqdm

import pandas as pd

from ipapi.database.base import QueryHandler, DbWrapper

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

        res_df = self.dataframe.copy()
        if kwargs:
            for k, v in kwargs.items():
                if k not in res_df.columns:
                    for c in res_df.columns:
                        if k.lower() == c.lower():
                            k = c
                            break
                res_df = res_df[res_df[k].isin([v])]

        if additional:
            assert "order by" in additional.lower(), f"Can't handle {additional}"
            _, _, column, direction = additional.split(" ")
            res_df = res_df.sort_values(by=column, ascending=direction == "asc")

        if columns != "*":
            res_df = res_df[columns.replace(" ", "").split(",")]

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
    def __init__(self, **kwargs):
        self._tqdm = None
        self.db_info = kwargs.get("db_info", None)
        self.df_builder = None
        self.dataframe = None

    def __del__(self):
        pass

    def copy(self):
        return self.__class__(db_info=self.db_info.copy())

    def connect(self, auto_update: bool = True):
        if self.dataframe is None:
            cache_file_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "cache",
                f"{self.db_info.display_name}.csv",
            )
            if os.path.isfile(cache_file_path):
                self.dataframe = pd.read_csv(
                    cache_file_path,
                    parse_dates=[4],
                ).reset_index(drop=True)
            else:
                self.dataframe = self.df_builder(self.db_info.display_name)
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
        self.dataframe = None
        self.connect()

    def _init_progress(self, total: int, desc: str = "") -> None:
        if self.progress_call_back is None:
            logger.info(f'Starting "{desc}"')
            self._tqdm = tqdm(total=total, desc=desc)

    def _callback(self, step, total, msg):
        if self.progress_call_back is not None:
            return self.progress_call_back(step, total, True)
        else:
            self._tqdm.update(1)
            return True

    def _close_progress(self, desc: str = ""):
        if self._tqdm is not None:
            logger.info(f'Ended "{desc}"')
            self._tqdm.close()

    def is_exists(self):
        return True
