import os
from datetime import datetime as dt

if __name__ == "__main__":
    import sys

    sys.path.append(os.path.join("..", ".."))
    sys.path.append(os.path.join(".", "app"))

from ipapi.tools.common_functions import force_directories
import platform

try:
    import win32api
except Exception as e:
    is_winapi = False
else:
    is_winapi = True

try:
    from ipapi.database.db_connect_data import db_connect_data as dbc

    conf = dbc.get("mass_storage", {})
except Exception as e:
    conf = {}


g_storage_path = ""


ROOT_IPSO_FOLDER = "ipso_phen"


def get_mass_storage_path():
    global g_storage_path
    if not g_storage_path:
        if platform.system().lower() == "windows" and is_winapi and conf:
            drives = {}
            for drive in win32api.GetLogicalDriveStrings().split("\000")[:-1]:
                try:
                    drives[win32api.GetVolumeInformation(drive)[0]] = drive
                except Exception as e:
                    pass
            for drive, subfolder in [
                (d, n) for d, n in zip(conf["drive_names"], conf["folder_names"])
            ]:
                if drive in drives:
                    g_storage_path = os.path.join(drives[drive], subfolder, "")
                    break
            else:
                g_storage_path = ""
        elif platform.system().lower() == "linux" and conf:
            for mnt in os.listdir("/mnt/"):
                for fld in conf["folder_names"]:
                    if os.path.isdir(os.path.join("/", "mnt", mnt, fld, "")):
                        g_storage_path = os.path.join("/", "mnt", mnt, fld, "")
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

    def get_path(self, force_creation: bool = True) -> str:
        if force_creation is True and self._path:
            force_directories(self._path)
        return self._path

    def set_path(self, value):
        self._path = value


class IpsoFolders(dict):
    def get_path(self, key: str, force_creation: bool = True):
        if key in self.keys():
            return self[key].get_path(force_creation=force_creation)
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
        return {k: v for k, v in self.items() if v.dynamic is False}


ipso_folders = IpsoFolders(
    {
        "image_output": FolderData(
            os.path.join(
                os.path.expanduser("~"),
                "Pictures",
                ROOT_IPSO_FOLDER,
                "saved_images",
                dt.now().strftime("%Y_%B_%d-%H%M%S"),
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
