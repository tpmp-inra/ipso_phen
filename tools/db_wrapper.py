import datetime as dt
import os
import sqlite3
from abc import ABC, abstractmethod, abstractproperty
from typing import Union


import pandas as pd
from sqlalchemy import create_engine, exc
from sqlalchemy.sql import text
from sqlalchemy_utils import database_exists

from tools.image_list import ImageList
from file_handlers.fh_base import file_handler_factory
from tools.common_functions import print_progress_bar, force_directories, make_safe_name

DB_USER = "fmavianemac"
DB_PREFIX = "ipso_local_db_"
LOAD_DISTANT_DATABASES = False
DB_MAIN_TABLE = "snapshots"
DB_DEFAULT_PORT = 5432
DB_PASSWORD = ""

DB_TYPE_SQLITE = "DB_TYPE_SQLITE"
DB_TYPE_POSTGRESS = "DB_TYPE_POSTGRESS"
DB_TYPE_PERMANENT = "DB_TYPE_PERMANENT"
DB_TYPE_MEMORY = "DB_TYPE_MEMORY"
DB_TYPE_RO = "DB_TYPE_RO"
DB_TYPE_RW = "DB_TYPE_RW"


class DbInfo:
    def __init__(self, **kwargs):
        self.display_name = kwargs.get("display_name", "unknown")
        self.db_file_name = kwargs.get(
            "db_file_name", DB_PREFIX + make_safe_name(self.display_name)
        )
        self.src_files_path = kwargs.get("src_files_path", "")
        self.dbms = kwargs.get("dbms", "sqlite")
        self.db_folder_name = kwargs.get("db_folder_name", "./sqlite_databases")

    @classmethod
    def from_json(cls, json_data: dict):
        return cls(**json_data)

    def to_json(self):
        return {
            "display_name": self.display_name,
            "db_file_name": self.db_file_name,
            "src_files_path": self.src_files_path,
            "dbms": self.dbms,
            "db_folder_name": self.db_folder_name,
        }

    def copy(self):
        return self.__class__.from_json(self.to_json())

    @property
    def db_full_file_path(self) -> str:
        return os.path.join(self.db_folder_name, self.db_file_name)


DB_INFO_LOCAL_SAMPLES = DbInfo(
    display_name="local_samples",
    src_files_path=os.path.join(os.path.expanduser("~"), "Pictures", "ipso_phen_cache", ""),
    dbms="psql",
)

DB_INFO_EXT_HD = DbInfo(
    display_name="external_hard_drive", src_files_path="d:/input", dbms="psql",
)


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


class QueryHandler(ABC):
    @staticmethod
    def format_key(key, value):
        pass

    @staticmethod
    def query(
        self,
        command: str,
        table: str = "snapshots",
        columns: str = "*",
        additional: str = "",
        **kwargs,
    ):
        pass

    @staticmethod
    def query_to_pandas(
        self,
        command: str,
        table: str = "snapshots",
        columns: str = "*",
        additional: str = "",
        **kwargs,
    ):
        pass

    def query_one(
        self,
        command: str,
        table: str = "snapshots",
        columns: str = "*",
        additional: str = "",
        **kwargs,
    ):
        ret = self.query(
            command=command, columns=columns, table=table, additional=additional, **kwargs
        )
        if (ret is not None) and (len(ret) > 0):
            return ret[0]
        else:
            return None

    @property
    def dbms(self) -> str:
        return "unknown"


class QueryHandlerPostgres(QueryHandler):
    @staticmethod
    def format_key(key, value):
        if isinstance(value, dict):
            op = value["operator"]
            if op.lower() == "between":
                return f"{key} {op} " + " AND ".join(
                    f":{k}" for k in value.keys() if k != "operator"
                )
            elif op.lower() == "in":
                return (
                    f"{key} {op} ("
                    + ", ".join(f":val_{i}" for i in range(0, len(value["values"])))
                    + ")"
                )
        else:
            return f"{key} = :{key}"

    def _prepare_query(
        self,
        command: str,
        table: str = "snapshots",
        columns: str = "*",
        additional: str = "",
        **kwargs,
    ):
        constraints_ = " AND ".join(
            [f"{self.format_key(key=k, value=v)}" for k, v in kwargs.items()]
        )
        if constraints_:
            s = text(f'{command} {columns} FROM "{table}" WHERE {constraints_} {additional}')
        else:
            s = text(f'{command} {columns} FROM "{table}" {additional}')

        param_dict = {k: v for k, v in kwargs.items() if not isinstance(v, dict)}
        for k, v in kwargs.items():
            if isinstance(v, dict):
                op = v["operator"]
                if op.lower() == "between":
                    param_dict.update(v)
                elif op.lower() == "in":
                    param_dict.update({f"val_{i}": val for i, val in enumerate(v["values"])})

        return s, param_dict

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

        s, param_dict = self._prepare_query(
            command=command, table=table, columns=columns, additional=additional, **kwargs
        )

        if self.open_connexion():
            try:
                # Get columns
                if columns == "*":
                    cols = self.connexion.execute(
                        f"select column_name from INFORMATION_SCHEMA.COLUMNS where TABLE_NAME='{table}'"
                    ).fetchall()
                    cols = [c[0] for c in cols]
                else:
                    cols = columns.replace(" ", "").split(",")
                df = pd.DataFrame(
                    self.connexion.execute(s, param_dict).fetchall(), columns=cols
                )
            except Exception as e:
                self.last_error = f"Query failed because: {repr(e)}"
                df = None
            finally:
                self.close_connexion()
        else:
            df = None
        return df

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

        s, param_dict = self._prepare_query(
            command=command, table=table, columns=columns, additional=additional, **kwargs
        )

        if self.open_connexion():
            try:
                ret = self.connexion.execute(s, param_dict).fetchall()
            except Exception as e:
                self.last_error = f"Query failed because: {repr(e)}"
                ret = None
            finally:
                self.close_connexion()
        else:
            ret = None
        return ret

    @property
    def dbms(self) -> str:
        return "psql"


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
            command=command, table=table, columns=columns, additional=additional, **kwargs
        )

        if self.open_connexion():
            if sql_:
                self.connexion.execute(
                    f"""{command} {columns} FROM {table} WHERE {sql_} {additional}""", params_
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
            df = pd.DataFrame(self.connexion.fetchall(), columns=cols)
            self.close_connexion()
        else:
            df = None
        return df

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
            command=command, table=table, columns=columns, additional=additional, **kwargs
        )

        if self.open_connexion():
            if sql_:
                self.connexion.execute(
                    f"""{command} {columns} FROM {table} WHERE {sql_} {additional}""", params_
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


class DbWrapper(ABC):
    def __init__(self, **kwargs):
        self.port = kwargs.get("port", 5432)
        self.password = kwargs.get("password", "")
        self.user = kwargs.get("user", "")
        self.main_table = kwargs.get("main_table", "snapshots")
        self.engine = None
        self.progress_call_back = kwargs.get("progress_call_back", None)
        self.connexion = None
        self._last_error = ""
        self.db_info = kwargs.get("db_info", None)

    def __del__(self):
        self.close_connexion()
        self.engine = None

    def copy(self):
        return self.__class__(
            user=self.user,
            port=self.port,
            password=self.password,
            main_table=self.main_table,
            db_info=self.db_info.copy(),
        )

    @abstractmethod
    def connect(self, auto_update: bool = True):
        pass

    @abstractmethod
    def open_connexion(self) -> bool:
        return False

    def close_connexion(self):
        if self.connexion is not None:
            self.connexion.close()
            self.connexion = None

    @abstractmethod
    def drop(self, super_user, password):
        pass

    @abstractmethod
    def update(self, db_file_name="", extensions: tuple = (".jpg", ".tiff", ".png", ".bmp")):
        pass

    def _callback(self, step, total, msg):
        if self.progress_call_back is not None:
            return self.progress_call_back(step, total, True)
        else:
            print_progress_bar(
                iteration=step, total=total, prefix=msg, suffix=f"Complete {step}/{total}"
            )
            return True

    def print_table_names(self):
        if not self.connect():
            return -1
        if self.open_connexion():
            try:
                res = self.connexion.execute("SELECT table_name FROM information_schema.tables")
                table_list = [item[0] for item in res]
                print("\n".join(table_list))
            finally:
                self.close_connexion()

    def is_exists(self):
        return database_exists(self.db_url)

    @property
    def url(self):
        return f"postgresql://{self.user}@localhost:{self.port}"

    @property
    def db_url(self):
        return f"{self.url}/{self.db_file_name.lower()}"

    @property
    def last_error(self):
        return self._last_error

    @last_error.setter
    def last_error(self, value):
        if value:
            print(value)
        self._last_error = value

    @abstractproperty
    def type(self) -> list:
        return []

    @property
    def display_name(self):
        return self.db_info.display_name

    @display_name.setter
    def display_name(self, value):
        self.db_info.display_name = value

    @property
    def db_file_name(self):
        return self.db_info.db_file_name

    @db_file_name.setter
    def db_file_name(self, value):
        self.db_info.db_file_name = value

    @property
    def src_files_path(self):
        return self.db_info.src_files_path

    @src_files_path.setter
    def src_files_path(self, value):
        self.db_info.src_files_path = value

    @property
    def dbms(self):
        return self.db_info.dbms

    @dbms.setter
    def dbms(self, value):
        self.db_info.dbms = value

    @property
    def db_folder_name(self):
        return self.db_info.db_folder_name

    @db_folder_name.setter
    def db_folder_name(self, value):
        self.db_info.db_folder_name = value


class PgSqlDbWrapper(DbWrapper, QueryHandlerPostgres):
    def connect(self, auto_update: bool = True):
        missing_data = False

        # Check database exists
        db_url = self.db_url
        if not database_exists(db_url):
            engine = create_engine("postgres://postgres@/postgres")
            conn = engine.connect()
            conn.execute("commit")
            conn.execute(f"create database {self.db_file_name.lower()}")
            conn.execute(f"GRANT ALL ON DATABASE {self.db_file_name.lower()} TO {self.user};")
            conn.execute(f"ALTER DATABASE {self.db_file_name.lower()} OWNER TO {self.user};")
            conn.close()
            missing_data = True

        # Create engine
        if self.engine is None:
            self.engine = create_engine(db_url)
        if self.engine is None:
            return False

        # Check table exists
        if (
            not self.engine.dialect.has_table(self.engine, self.main_table)
            and self.open_connexion()
        ):
            try:
                self.connexion.execute(
                    f"""CREATE TABLE {self.main_table} (Luid TEXT NOT NULL PRIMARY KEY,
                                                        Name TEXT NOT NULL,
                                                        FilePath TEXT NOT NULL,
                                                        Experiment TEXT,
                                                        Plant TEXT,
                                                        Date DATE,
                                                        Time TIME,
                                                        date_time TIMESTAMP,
                                                        Camera TEXT,
                                                        view_option TEXT )"""
                )
                missing_data = True
            except Exception as e:
                self.close_connexion()
                self.last_error = f"Failed to create table because {repr(e)}"
                return False

        if missing_data and auto_update and self.db_file_name:
            self.update()

        return True

    def open_connexion(self) -> bool:
        if self.connexion is not None:
            self.close_connexion()
        self.connexion = self.engine.connect()
        return self.connexion is not None

    def drop(self, super_user, password):
        engine = create_engine(f"postgres://{super_user}@/postgres")
        conn_ = engine.connect()
        trans_ = conn_.begin()
        try:
            conn_.execute("commit")
            conn_.execute(f"drop database if exists {self.db_file_name.lower()}")
            trans_.commit()
            conn_.close()
        except Exception as e:
            trans_.rollback()
            self.last_error = f'Something went wrong: "{repr(e)}"'
            return False
        else:
            return True

    def update(self, src_files_path="", extensions: tuple = (".jpg", ".tiff", ".png", ".bmp")):
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
            if self.open_connexion():
                total_ = len(file_list)
                for i, file in enumerate(file_list):
                    try:
                        fh = file_handler_factory(file)
                        sql_ = text(
                            f"INSERT INTO {self.main_table}"
                            "(Luid, Name, FilePath, Experiment, Plant, Date, Time, date_time, Camera, view_option)"
                            "VALUES (:Luid, :Name, :FilePath, :Experiment, :Plant, :Date, :Time, :date_time, :Camera, :view_option)"
                        )
                        self.connexion.execute(
                            sql_,
                            Luid=fh.luid,
                            Name=fh.name,
                            FilePath=fh.file_path,
                            Experiment=fh.experiment,
                            Plant=fh.plant,
                            Date=fh.date_time.date(),
                            Time=fh.date_time.time(),
                            date_time=fh.date_time,
                            Camera=fh.camera,
                            view_option=fh.view_option,
                        )
                    except exc.IntegrityError:
                        pass
                    except Exception as e:
                        self.last_error = f'Cannot add "{file}" because "{e}"'
                    else:
                        files_added += 1
                    self._callback(
                        step=i, total=total_, msg=f'Updating database "{self.db_file_name}"'
                    )
                self.close_connexion()
                self._callback(
                    step=total_, total=total_, msg=f'Updated database "{self.db_file_name}"'
                )
        elif self.src_files_path.lower().endswith((".csv",)):
            df = pd.read_csv(self.src_files_path, parse_dates=[3])
            try:
                df.drop_duplicates(subset="luid", keep="first", inplace=True)
                df.to_sql(name="snapshots", con=self.engine, if_exists="replace")
                if self.open_connexion():
                    try:
                        self.connexion.execute("alter table snapshots add primary key (luid)")
                        self.connexion.execute("alter table snapshots drop column index")
                    finally:
                        self.close_connexion()
            except Exception as e:
                self.last_error = f"Failed to create table because {repr(e)}"
                files_added = -1
            else:
                files_added = df["luid"].count()
        else:
            self.last_error = f"I don't know what to do with {self.src_files_path}"
            files_added = -1

        return files_added

    @property
    def type(self) -> list:
        return [DB_TYPE_PERMANENT, DB_TYPE_POSTGRESS, DB_TYPE_RW]


class ReadOnlyDbWrapper(DbWrapper, QueryHandlerPostgres):
    def connect(self, auto_update: bool = True):
        # Check database exists
        db_url = self.db_url
        if not database_exists(db_url):
            return False

        # Create engine
        if self.engine is None:
            self.engine = create_engine(db_url)
        if self.engine is None:
            return False

        return True

    def open_connexion(self):
        self.connexion = self.engine.connect()
        return self.connexion

    def drop(self, super_user, password):
        return False

    def update(self, db_file_name="", extensions: tuple = (".jpg", ".tiff", ".png", ".bmp")):
        return -1

    @property
    def type(self) -> list:
        return [DB_TYPE_PERMANENT, DB_TYPE_POSTGRESS, DB_TYPE_RO]


class SqLiteDbWrapper(DbWrapper, QueryHandlerSQLite):
    def connect(self, auto_update: bool = True):
        if self.engine is None:
            needs_creating = not self.is_exists()
            if self.db_file_name == ":memory:":
                db_file_name = ":memory:"
            else:
                db_file_name = self.db_info.db_full_file_path
                force_directories(self.db_folder_name)
            self.engine = sqlite3.connect(
                database=db_file_name,
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
        if self.db_file_name == ":memory:":
            return self.engine is not None
        else:
            return os.path.isfile(self.db_info.db_full_file_path)

    def drop(self, super_user, password):
        return False

    def update(self, src_files_path="", extensions: tuple = (".jpg", ".tiff", ".png", ".bmp")):
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
            with self.engine as conn_:
                for i, file in enumerate(file_list):
                    try:
                        fh = file_handler_factory(file)
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
                        self.last_error = f'Cannot add "{file}" because "{e}"'
                    else:
                        files_added += 1
                    self._callback(
                        step=i, total=total_, msg=f'Updating database "{self.src_files_path}"'
                    )
                self._callback(
                    step=total_, total=total_, msg=f'Updated database "{self.src_files_path}"'
                )
        elif self.src_files_path.lower().endswith((".csv",)):
            df = pd.read_csv(self.src_files_path, parse_dates=[3])
            try:
                df.drop_duplicates(subset="luid", keep="first", inplace=True)
                df.to_sql(name="snapshots", con=self.engine, if_exists="replace")
                conn_ = self.open_connexion()
                try:
                    conn_.execute("alter table snapshots add primary key (luid)")
                    conn_.execute("alter table snapshots drop column index")
                finally:
                    self.close_connexion()
            except Exception as e:
                self.last_error = f"Failed to create table because {repr(e)}"
                files_added = -1
            else:
                files_added = df["luid"].count()
        else:
            self.last_error = f"I don't know what to do with {self.src_files_path}"
            files_added = -1

        return files_added

    @property
    def type(self) -> list:
        if self.db_file_name == ":memory:":
            return [DB_TYPE_MEMORY, DB_TYPE_SQLITE, DB_TYPE_RW]
        else:
            return [DB_TYPE_SQLITE, DB_TYPE_RW]


def db_info_to_database(info: DbInfo, **kwargs) -> Union[DbWrapper, str]:
    """Builds a database from information

    Arguments:
        info {DbInfo} -- Describes the database

    Returns:
        [DbWrapper, str] -- Database wrapper if success, string descriging the problem else
    """
    if info.dbms == "psql":
        return PgSqlDbWrapper(
            user=DB_USER,
            port=DB_DEFAULT_PORT,
            password=DB_PASSWORD,
            db_info=info.copy(),
            progress_call_back=kwargs.get("progress_call_back", None),
        )
    elif info.dbms == "sqlite":
        return SqLiteDbWrapper(
            db_info=info.copy(),
            progress_call_back=kwargs.get("progress_call_back", None),
            db_folder_name=info.db_folder_name,
        )
    else:
        return f"Unknown DBMS {info.dbms}"
