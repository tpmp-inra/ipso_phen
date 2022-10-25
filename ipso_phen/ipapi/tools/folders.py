import os
from datetime import datetime as dt
import logging

if __name__ == "__main__":
    import sys

    sys.path.append(os.path.join("..", ".."))
    sys.path.append(os.path.join(".", "app"))

from ipso_phen.ipapi.tools.common_functions import force_directories
import platform

try:
    import win32api
except Exception as e:
    is_winapi = False
else:
    is_winapi = True

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))


g_storage_path = ""

ALLOW_CACHE = True

ROOT_IPSO_FOLDER = "ipso_phen"

conf = {"folder_names": ["images", "input"]}


def get_mass_storage_path():
    global g_storage_path
    if not g_storage_path:
        if platform.system().lower() == "windows" and is_winapi and conf:
            for drive in win32api.GetLogicalDriveStrings().split("\000")[:-1]:
                try:
                    for folder_name in conf["folder_names"]:
                        if os.path.isdir(os.path.join(drive, folder_name)):
                            g_storage_path = os.path.join(drive, folder_name)
                            break
                except Exception as e:
                    pass
                if g_storage_path:
                    break
        elif (platform.system().lower() == "linux" or platform.system().lower() == "darwin") and conf:
            if platform.system().lower() == "darwin":
                mount_point = "/Volumes/"
            else:
                mount_point = "/mnt/"
            for mnt in os.listdir(mount_point):
                for fld in conf["folder_names"]:
                    if os.path.isdir(os.path.join("/", mount_point, mnt, fld, "")):
                        g_storage_path = os.path.join("/", mount_point, mnt, fld, "")
                        break
                if g_storage_path:
                    break
        else:
            g_storage_path = ""
    return g_storage_path


def get_local_storage_path():
    return os.path.join(
        os.path.expanduser("~"),
        "Pictures",
        ROOT_IPSO_FOLDER,
        "storage",
        "",
    )


class FolderData:
    def __init__(self, path: str, dynamic: bool = False) -> None:
        self._path = path
        self.dynamic = dynamic

    def get_path(
        self,
        force_creation: bool = True,
        subfolder: str = "",
    ) -> str:
        try:
            path_ = os.path.join(self._path, subfolder) if subfolder else self._path
            if force_creation is True and path_:
                force_directories(path_)
        except FileNotFoundError as e:
            logger.exception(f'Unable to create folder: "{repr(e)}"')
            path_ = os.path.join(os.path.expanduser("~"), "Documents", "")
        return path_

    def set_path(self, value):
        self._path = value


class IpsoFolders(dict):
    def get_path(
        self,
        key: str,
        force_creation: bool = True,
        subfolder: str = "",
        fallback_folder: str = "",
    ):
        if key in self.keys():
            return self[key].get_path(
                force_creation=force_creation,
                subfolder=subfolder,
            )
        elif fallback_folder:
            return fallback_folder
        else:
            return ""

    def set_path(self, key: str, path: str):
        if key in self.keys():
            assert self[key].dynamic is True, f"Can not set '{self[key]}' path is static"
            self[key].set_path(path)

    def add_static(self, key, path, user_folder=""):
        if not user_folder:
            self[key] = FolderData(path=path, dynamic=False)
        else:
            self[key] = FolderData(
                path=os.path.join(
                    os.path.expanduser("~"),
                    user_folder,
                    ROOT_IPSO_FOLDER,
                    path,
                    "",
                ),
                dynamic=False,
            )

    def add_dynamic(self, key, path, user_folder=""):
        if not user_folder:
            self[key] = FolderData(path=path, dynamic=True)
        else:
            self[key] = FolderData(
                path=os.path.join(
                    os.path.expanduser("~"),
                    user_folder,
                    ROOT_IPSO_FOLDER,
                    path,
                    "",
                ),
                dynamic=True,
            )

    @property
    def static(self):
        return {k: v for k, v in self.items() if v.dynamic is False}

    @property
    def dynamic(self):
        return {k: v for k, v in self.items() if v.dynamic is True}


ipso_folders = IpsoFolders(
    {
        "image_output": FolderData(
            os.path.join(
                os.path.expanduser("~"),
                "Pictures",
                ROOT_IPSO_FOLDER,
                "saved_images",
                "",
            )
        ),
        "script": FolderData("./script_pipelines/"),
        "saved_data": FolderData(
            os.path.join(
                os.path.expanduser("~"),
                "Documents",
                ROOT_IPSO_FOLDER,
                "saved_data",
                "",
            )
        ),
        "pipelines": FolderData(
            os.path.join(
                os.path.expanduser("~"),
                "Documents",
                ROOT_IPSO_FOLDER,
                "pipelines",
                "",
            )
        ),
        "pipeline_output_folder": FolderData(
            os.path.join(
                os.path.expanduser("~"),
                "Documents",
                ROOT_IPSO_FOLDER,
                "pipeline_output",
                "",
            )
        ),
        "stored_data": FolderData(
            os.path.join(
                os.path.expanduser("~"),
                "Documents",
                ROOT_IPSO_FOLDER,
                "stored_data",
                "",
            )
        ),
        "sql_db": FolderData(
            os.path.join(
                os.path.expanduser("~"),
                "Documents",
                ROOT_IPSO_FOLDER,
                "sqlite_databases",
                "",
            )
        ),
        "logs": FolderData(
            os.path.join(
                os.path.expanduser("~"),
                "Documents",
                ROOT_IPSO_FOLDER,
                "logs",
                "",
            )
        ),
        "db_cache": FolderData(
            os.path.join(
                os.path.expanduser("~"),
                "Documents",
                ROOT_IPSO_FOLDER,
                "db_cache",
                "",
            )
        ),
        "img_cache": FolderData(
            os.path.join(
                os.path.expanduser("~"),
                "Documents",
                ROOT_IPSO_FOLDER,
                "img_cache",
                "",
            )
        ),
        "db_connect_data": FolderData(
            os.path.join(
                os.path.expanduser("~"),
                "Documents",
                ROOT_IPSO_FOLDER,
                "db_connect_data",
                "",
            )
        ),
        "database_builders": FolderData(
            os.path.join(
                os.path.expanduser("~"),
                "Documents",
                ROOT_IPSO_FOLDER,
                "database_builders",
                "",
            )
        ),
        "tensorflow_models": FolderData(
            os.path.join(
                os.path.expanduser("~"),
                "Documents",
                ROOT_IPSO_FOLDER,
                "tensorflow_models",
                "",
            )
        ),
        "ilastik_models": FolderData(
            os.path.join(
                os.path.expanduser("~"),
                "Documents",
                ROOT_IPSO_FOLDER,
                "ilastik_models",
                "",
            )
        ),
        "mass_storage": FolderData(get_mass_storage_path()),
        "local_storage": FolderData(get_local_storage_path()),
        "image_cache": FolderData(
            get_mass_storage_path()
            if get_mass_storage_path()
            else get_local_storage_path()
        ),
    }
)

ipso_folders.add_dynamic(
    key="pipeline",
    path="pipelines",
    user_folder="Documents",
)
ipso_folders.add_dynamic(
    key="csv",
    path="saved_csv",
    user_folder="Documents",
)
ipso_folders.add_dynamic(
    key="image_list",
    path="image_lists",
    user_folder="Documents",
)
ipso_folders.add_dynamic(
    key="pp_output",
    path="pipeline_output",
    user_folder="Documents",
)
ipso_folders.add_dynamic(
    key="pp_state",
    path="pipeline_state",
    user_folder="Documents",
)
ipso_folders.add_dynamic(
    key="db_image_folder",
    path="",
    user_folder="Pictures",
)


if __name__ == "__main__":
    for k, v in ipso_folders.items():
        print(f"{k}: {v.get_path(False)}")
