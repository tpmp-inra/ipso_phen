import os
import logging
from collections import defaultdict
from enum import Enum, unique

try:
    import win32api
except Exception as e:
    is_winapi = False
else:
    is_winapi = True

from ipapi.database.base import DbInfo
from ipapi.database.phenoserre_wrapper import get_exp_list

try:
    from ipapi.database.db_connect_data import db_connect_data as dbc
except Exception as e:
    dbc = {}

logger = logging.getLogger(__name__)


@unique
class DbType(Enum):
    LOCAL_DB = "Local PSQL databases"
    MASS_DB = "Mass storage databases"
    PHENOSERRE = "Phenoserre databases"
    PHENOPSIS = "Phenopsis databases"
    CUSTOM_DB = "Custom databases"


g_storage_path = ""

available_db_dicts = defaultdict(list)

if "psql_local" in dbc:

    def _get_mass_storage_path():
        global g_storage_path
        if not g_storage_path and is_winapi:
            drives = {}
            for drive in win32api.GetLogicalDriveStrings().split("\000")[:-1]:
                try:
                    drives[win32api.GetVolumeInformation(drive)[0]] = drive
                except Exception as e:
                    pass
            if "2bigTPMP" in drives:
                g_storage_path = os.path.join(drives["2bigTPMP"], "images", "")
            elif "TPMP_ EXT" in drives:
                g_storage_path = os.path.join(drives["TPMP_ EXT"], "input", "")
            else:
                g_storage_path = ""
        return g_storage_path

    def _get_local_storage_path():
        return os.path.join(
            os.path.expanduser("~"),
            "Pictures",
            "ipso_phen_cache",
            "",
        )

    available_db_dicts[DbType.LOCAL_DB] = [
        DbInfo(
            display_name=name,
            target="psql_local",
            src_files_path=os.path.join(_get_local_storage_path(), name),
            dbms="psql",
        )
        for name in os.listdir(_get_local_storage_path())
        if os.path.isdir(os.path.join(_get_local_storage_path(), name))
    ]

    if _get_mass_storage_path():
        available_db_dicts[DbType.MASS_DB] = [
            DbInfo(
                display_name=name,
                target="psql_local",
                src_files_path=os.path.join(_get_mass_storage_path(), name),
                dbms="psql",
            )
            for name in os.listdir(_get_mass_storage_path())
            if os.path.isdir(os.path.join(_get_mass_storage_path(), name))
        ]


if "phenoserre" in dbc:
    available_db_dicts[DbType.PHENOSERRE] = [
        DbInfo(
            display_name=name,
            target="phenoserre",
            dbms="pandas",
        )
        for name in get_exp_list()
    ]
