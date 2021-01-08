import os
import logging
import datetime as dt

import pandas as pd
import sqlite3
from sqlalchemy import exc

from ipso_phen.ipapi.database.base import DbInfo, QueryHandler, DbWrapper
from ipso_phen.ipapi.tools.common_functions import force_directories
from ipso_phen.ipapi.tools.image_list import ImageList
from ipso_phen.ipapi.file_handlers.fh_base import file_handler_factory


logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))


def adapt_time_object(time_object):
    return (
        3600 * time_object.hour + 60 * time_object.minute + time_object.second
    ) * 10 ** 6  # + time_object.microsecond


def convert_time_object(val):
    val = int(val)
    hour, val = divmod(val, 3600 * 10 ** 6)
    minute, val = divmod(val, 60 * 10 ** 6)
    second, val = divmod(val, 10 ** 6)
    microsecond = 0  # int(val)
    return dt.time(hour, minute, second, microsecond)


# Converts DT.time to TEXT when inserting
sqlite3.register_adapter(dt.time, adapt_time_object)

# Converts TEXT to DT.time when selecting
sqlite3.register_converter("TIME_OBJECT", convert_time_object)


class QueryHandlerSQLite(QueryHandler):
    @staticmethod
    def format_key(key, value):
        if isinstance(value, dict):
            op = value["operator"]
            if op.lower() == "between":
                return f"{key} {op} " + " AND ".join(
                    "?" for k in value.keys() if k != "operator"
                )
            elif op.lower() == "in":
                return (
                    f"{key} {op} ("
                    + ", ".join("?" for _ in range(0, len(value["values"])))
                    + ")"
                )
        else:
            return f"{key} = ?"

    def _prepare_query(
        self,
        command: str,
        table: str = "snapshots",
        columns: str = "*",
        additional: str = "",
        **kwargs,
    ):
        sql_ = ""
        params_ = []

        for key, value in kwargs.items():
            if value:
                if sql_:
                    sql_ += f"AND {self.format_key(key=key, value=value)} "
                else:
                    sql_ += f"{self.format_key(key=key, value=value)} "
                if isinstance(value, dict):
                    op = value["operator"]
                    if op.lower() == "between":
                        params_.extend([v for k, v in value.items() if k != "operator"])
                    elif op.lower() == "in":
                        params_.extend(value["values"])
                else:
                    params_.append(value)

        return sql_, params_

    def query_to_pandas(
        self,
        command: str,
        table: str = "snapshots",
        columns: str = "*",
        additional: str = "",
        **kwargs,
    ):
        if self.connect() is False:
            return None

        sql_, params_ = self._prepare_query(
            command=command,
            table=table,
            columns=columns,
            additional=additional,
            **kwargs,
        )

        if self.open_connexion():
            if sql_:
                self.connexion.execute(
                    f"""{command} {columns} FROM {table} WHERE {sql_} {additional}""",
                    params_,
                )
            else:
                self.connexion.execute(
                    f"""{command} {columns} FROM {table} {additional}""", params_
                )

            # Get columns
            if columns == "*":
                cursor = self.connexion.execute(f"SELECT * from {table}")
                cols = list(map(lambda x: x[0], cursor.description))
            else:
                cols = columns.replace(" ", "").split(",")
            dataframe = pd.DataFrame(self.connexion.fetchall(), columns=cols)
            self.close_connexion()
        else:
            dataframe = None
        return dataframe

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

        sql_, params_ = self._prepare_query(
            command=command,
            table=table,
            columns=columns,
            additional=additional,
            **kwargs,
        )

        if self.open_connexion():
            if sql_:
                self.connexion.execute(
                    f"""{command} {columns} FROM {table} WHERE {sql_} {additional}""",
                    params_,
                )
            else:
                self.connexion.execute(
                    f"""{command} {columns} FROM {table} {additional}""", params_
                )
            ret = self.connexion.fetchall()
            self.close_connexion()
        else:
            ret = None
        return ret

    @property
    def dbms(self) -> str:
        return "sqlite"


class SqLiteDbWrapper(DbWrapper, QueryHandlerSQLite):
    def connect(self, auto_update: bool = True):
        if self.engine is None:
            needs_creating = not self.is_exists()
            if self.db_qualified_name == ":memory:":
                db_qualified_name = ":memory:"
            else:
                db_qualified_name = self.db_info.db_full_file_path
                force_directories(self.db_folder_name)
            self.engine = sqlite3.connect(
                database=db_qualified_name,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            )
            if needs_creating:
                self.engine.execute(
                    f"""CREATE TABLE {self.main_table} (Luid TEXT NOT NULL PRIMARY KEY,
                                                        Name TEXT NOT NULL COLLATE NOCASE,
                                                        FilePath TEXT NOT NULL COLLATE NOCASE,
                                                        Experiment TEXT COLLATE NOCASE,
                                                        Plant TEXT COLLATE NOCASE,
                                                        Date DATE,
                                                        Time TIME_OBJECT,
                                                        date_time TIMESTAMP,
                                                        Camera TEXT COLLATE NOCASE,
                                                        view_option TEXT COLLATE NOCASE)"""
                )
                if auto_update:
                    self.update()
        return True

    def open_connexion(self):
        if self.connexion is not None:
            self.close_connexion()
        self.connexion = self.engine.cursor()
        return self.connexion

    def close_connexion(self):
        if self.connexion is not None:
            self.engine.commit()
            self.connexion.close()
            self.connexion = None

    def is_exists(self):
        if self.db_qualified_name == ":memory:":
            return self.engine is not None
        else:
            return os.path.isfile(self.db_info.db_full_file_path)

    def update(
        self, src_files_path="", extensions: tuple = (".jpg", ".tiff", ".png", ".bmp")
    ):
        if not self.connect(auto_update=False):
            return -1

        files_added = 0
        if src_files_path:
            self.src_files_path = src_files_path
        if os.path.isdir(self.src_files_path):
            # Grab all images in folder
            img_lst = ImageList(extensions)
            img_lst.add_folder(self.src_files_path)
            file_list = img_lst.filter(())
            # Fill database
            self.close_connexion()
            total_ = len(file_list)
            self._init_progress(total=total_, desc="Updating database")
            with self.engine as conn_:
                for i, file in enumerate(file_list):
                    try:
                        fh = file_handler_factory(file, database=None)
                        conn_.execute(
                            f"""INSERT INTO {self.main_table} (Luid, Name, FilePath, Experiment, Plant, Date, Time, date_time, Camera, view_option)
                                        VALUES (:Luid, :Name, :FilePath, :Experiment, :Plant, :Date, :Time, :date_time, :Camera, :view_option)""",
                            {
                                "Luid": fh.luid,
                                "Name": fh.name,
                                "FilePath": fh.file_path,
                                "Experiment": fh.experiment,
                                "Plant": fh.plant,
                                "Date": fh.date_time.date(),
                                "Time": fh.date_time.time(),
                                "date_time": fh.date_time,
                                "Camera": fh.camera,
                                "view_option": fh.view_option,
                            },
                        )
                    except exc.IntegrityError:
                        pass
                    except Exception as e:
                        logger.exception(f'Cannot add "{file}" because "{e}"')
                    else:
                        files_added += 1
                    self._callback(
                        step=i,
                        total=total_,
                        msg=f'Updating database "{self.src_files_path}"',
                    )
                self._callback(
                    step=total_,
                    total=total_,
                    msg=f'Updated database "{self.src_files_path}"',
                )
                self._close_progress(desc="Updating database")
        elif self.src_files_path.lower().endswith((".csv",)):
            dataframe = pd.read_csv(self.src_files_path, parse_dates=[3])
            try:
                dataframe = dataframe.drop_duplicates(subset="luid", keep="first")
                dataframe.to_sql(name="snapshots", con=self.engine, if_exists="replace")
                conn_ = self.open_connexion()
                try:
                    conn_.execute("alter table snapshots add primary key (luid)")
                    conn_.execute("alter table snapshots drop column index")
                finally:
                    self.close_connexion()
            except Exception as e:
                logger.exception(f"Failed to create table because {repr(e)}")
                files_added = -1
            else:
                files_added = dataframe["luid"].count()
        else:
            logger.error(f"I don't know what to do with {self.src_files_path}")
            files_added = -1

        return files_added
