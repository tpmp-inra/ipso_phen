import os
from abc import ABC, abstractmethod, abstractproperty
import logging

from tqdm import tqdm

from ipso_phen.ipapi.tools.common_functions import (
    force_directories,
    make_safe_name,
    undefined_tqdm,
)

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))


class DbInfo:
    def __init__(self, **kwargs):
        # For all
        self.display_name = kwargs.get("display_name", "unknown")
        self.db_qualified_name = kwargs.get(
            "db_qualified_name",
            make_safe_name(self.display_name),
        )
        self.src_files_path = kwargs.get("src_files_path", "")
        self.dbms = kwargs.get("dbms", "?")
        self.target = kwargs.get("target", "sqlite_local")

        # SQLite
        self.db_folder_name = kwargs.get("db_folder_name", "./sqlite_databases")

        # Overrides
        if self.db_qualified_name != ":memory:":
            if self.dbms == "sqlite" and not self.db_qualified_name.endswith(".db"):
                self.db_qualified_name += ".db"
            elif self.dbms == "psql" and not self.db_qualified_name.startswith("psql_"):
                self.db_qualified_name = "psql_" + self.db_qualified_name

    @property
    def full_display_name(self):
        return f"{self.display_name} ({self.dbms})"

    @classmethod
    def from_json(cls, json_data: dict):
        return cls(**json_data)

    def to_json(self):
        return {
            "display_name": self.display_name,
            "db_qualified_name": self.db_qualified_name,
            "src_files_path": self.src_files_path,
            "dbms": self.dbms,
            "db_folder_name": self.db_folder_name,
            "target": self.target,
        }

    def copy(self):
        return self.__class__.from_json(self.to_json())

    @property
    def db_full_file_path(self) -> str:
        return os.path.join(self.db_folder_name, self.db_qualified_name)


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
            command=command,
            columns=columns,
            table=table,
            additional=additional,
            **kwargs,
        )
        if (ret is not None) and (len(ret) > 0):
            return ret[0]
        else:
            return None

    @property
    def dbms(self) -> str:
        return "unknown"


class DbWrapper(ABC):
    def __init__(self, **kwargs):
        self.port = kwargs.get("port", 5432)
        self.password = kwargs.get("password", "")
        self.user = kwargs.get("user", "")
        self.main_table = kwargs.get("main_table", "snapshots")
        self.engine = None
        self.progress_call_back = kwargs.get("progress_call_back", None)
        self.connexion = None
        self._tqdm = None
        self._last_step = 0
        self.step_dir = "right"
        self.db_info = kwargs.get("db_info", None)
        self.main_selector = {}

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
    def update(
        self,
        db_qualified_name="",
        extensions: tuple = (".jpg", ".tiff", ".png", ".bmp"),
    ):
        pass

    def _init_progress(self, total: int, desc: str = "") -> None:
        if self.progress_call_back is None:
            logger.info(f'Starting "{desc}"')
            self._tqdm = tqdm(total=total, desc=desc)

    def _callback(self, step, total, msg=""):
        if self.progress_call_back is not None:
            return self.progress_call_back(step, total, True)
        else:
            self._tqdm.update(1)
            return True

    def _close_progress(self, desc: str = ""):
        if self._tqdm is not None:
            logger.info(f'Ended "{desc}"')
            self._tqdm.close()

    def _init_progress_undefined(self, desc: str = "") -> None:
        if self.progress_call_back is None:
            logger.info(f'"{desc}"')
            self._tqdm = undefined_tqdm(desc=desc, lapse=0.4, bar_length=20)

    def _callback_undefined(self):
        if self.progress_call_back is not None:
            if self.step_dir == "right":
                self._last_step += 1
            else:
                self.self._last_step -= 1
            if self.self._last_step < 0:
                self.step_dir = "right"
                self.self._last_step = 0
            elif self.self._last_step > 100:
                self.step_dir = "left"
                self.self._last_step = 100
            return self.progress_call_back(self._last_step, 100, True)
        else:
            self._tqdm.step()
            return True

    def _close_progress_undefined(self, desc: str = ""):
        if self._tqdm is not None:
            logger.info(f'"{desc}"')
            self._tqdm.stop()

    def is_exists(self):
        return False

    def reset(self):
        logger.warning(f"Not implemented for {self.__class__.__name__}")

    @property
    def url(self):
        return f"postgresql://{self.user}@localhost:{self.port}"

    @property
    def db_url(self):
        return f"{self.url}/{self.db_qualified_name.lower()}"

    @property
    def display_name(self):
        return self.db_info.display_name

    @display_name.setter
    def display_name(self, value):
        self.db_info.display_name = value

    @property
    def db_qualified_name(self):
        return self.db_info.db_qualified_name

    @db_qualified_name.setter
    def db_qualified_name(self, value):
        self.db_info.db_qualified_name = value

    @property
    def src_files_path(self):
        return self.db_info.src_files_path

    @src_files_path.setter
    def src_files_path(self, value):
        self.db_info.src_files_path = value

    @property
    def target(self):
        return self.db_info.target

    @target.setter
    def target(self, value):
        self.db_info.target = value

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
