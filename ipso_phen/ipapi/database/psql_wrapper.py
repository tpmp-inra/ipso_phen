import logging
import os

from sqlalchemy import create_engine, exc
from sqlalchemy.sql import text

import pandas as pd

from ipso_phen.ipapi.database.base import DbInfo, QueryHandler, DbWrapper
from ipso_phen.ipapi.tools.image_list import ImageList
from ipso_phen.ipapi.file_handlers.fh_base import file_handler_factory


logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))


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
            s = text(
                f'{command} {columns} FROM "{table}" WHERE {constraints_} {additional}'
            )
        else:
            s = text(f'{command} {columns} FROM "{table}" {additional}')

        param_dict = {k: v for k, v in kwargs.items() if not isinstance(v, dict)}
        for k, v in kwargs.items():
            if isinstance(v, dict):
                op = v["operator"]
                if op.lower() == "between":
                    param_dict.update(v)
                elif op.lower() == "in":
                    param_dict.update(
                        {f"val_{i}": val for i, val in enumerate(v["values"])}
                    )

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
            command=command,
            table=table,
            columns=columns,
            additional=additional,
            **kwargs,
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
                dataframe = pd.DataFrame(
                    self.connexion.execute(s, param_dict).fetchall(), columns=cols
                )
            except Exception as e:
                logger.exception(f"Query failed because: {repr(e)}")
                dataframe = None
            finally:
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

        s, param_dict = self._prepare_query(
            command=command,
            table=table,
            columns=columns,
            additional=additional,
            **kwargs,
        )

        if self.open_connexion():
            try:
                ret = self.connexion.execute(s, param_dict).fetchall()
            except Exception as e:
                logger.exception(f"Query failed because: {repr(e)}")
                ret = None
            finally:
                self.close_connexion()
        else:
            ret = None
        return ret

    @property
    def dbms(self) -> str:
        return "psql"


class PgSqlDbWrapper(DbWrapper, QueryHandlerPostgres):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.port = kwargs.get("port", 5432)
        self.password = kwargs.get("password", "")
        self.user = kwargs.get("user", "")
        self.engine_path = kwargs.get("engine_path", "")

    def connect(self, auto_update: bool = True):
        missing_data = False

        # Check database exists
        db_url = self.db_url
        if not self.is_exists():
            engine = create_engine("postgres://postgres@/postgres")
            conn = engine.connect()
            conn.execute("commit")
            conn.execute(f"create database {self.db_qualified_name.lower()}")
            conn.execute(
                f"GRANT ALL ON DATABASE {self.db_qualified_name.lower()} TO {self.user};"
            )
            conn.execute(
                f"ALTER DATABASE {self.db_qualified_name.lower()} OWNER TO {self.user};"
            )
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
                logger.exception(f"Failed to create table because {repr(e)}")
                return False

        if missing_data and auto_update and self.db_qualified_name:
            self.update()

        return True

    def open_connexion(self) -> bool:
        if self.connexion is not None:
            self.close_connexion()
        self.connexion = self.engine.connect()
        return self.connexion is not None

    def is_exists(self):
        pwd = f"-W {self.password}" if self.password else ""
        user = f"-U {self.user}" if self.user else ""
        return self.db_qualified_name.lower() in [
            line.lower().split("|")[0]
            for line in os.popen(f"psql -l -t -A {user} {pwd}").read().split("\n")
            if "|" in line
        ]

    def update(
        self,
        src_files_path="",
        extensions: tuple = (".jpg", ".tiff", ".png", ".bmp"),
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
            if self.open_connexion():
                total_ = len(file_list)
                self._init_progress(total=total_, desc="Updating database")
                for i, file in enumerate(file_list):
                    try:
                        fh = file_handler_factory(file, database=None)
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
                        logger.exception(f'Cannot add "{file}" because "{e}"')
                    else:
                        files_added += 1
                    self._callback(
                        step=i,
                        total=total_,
                        msg=f'Updating database "{self.db_qualified_name}"',
                    )
                self.close_connexion()
                self._callback(
                    step=total_,
                    total=total_,
                    msg=f'Updated database "{self.db_qualified_name}"',
                )
                self._close_progress(desc="Updating database")
        elif self.src_files_path.lower().endswith((".csv",)):
            dataframe = pd.read_csv(self.src_files_path, parse_dates=[3])
            try:
                dataframe = dataframe.drop_duplicates(subset="luid", keep="first")
                dataframe.to_sql(name="snapshots", con=self.engine, if_exists="replace")
                if self.open_connexion():
                    try:
                        self.connexion.execute(
                            "alter table snapshots add primary key (luid)"
                        )
                        self.connexion.execute("alter table snapshots drop column index")
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
