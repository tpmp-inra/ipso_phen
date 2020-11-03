import os
import logging
from collections import defaultdict
from enum import Enum, unique

from ipapi.database.base import DbInfo
from ipapi.database.phenoserre_wrapper import get_phenoserre_exp_list
from ipapi.database.phenopsis_wrapper import get_phenopsis_exp_list
from ipapi.tools.folders import ipso_folders


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

    available_db_dicts[DbType.LOCAL_DB] = [
        DbInfo(
            display_name=name,
            target="psql_local",
            src_files_path=os.path.join(
                ipso_folders.get_path("local_storage", False), name
            ),
            dbms="psql",
        )
        for name in os.listdir(ipso_folders.get_path("local_storage"))
        if os.path.isdir(
            os.path.join(ipso_folders.get_path("local_storage", False), name)
        )
    ]

    if ipso_folders.get_path("mass_storage"):
        available_db_dicts[DbType.MASS_DB] = [
            DbInfo(
                display_name=name,
                target="psql_local",
                src_files_path=os.path.join(
                    ipso_folders.get_path("mass_storage", False), name
                ),
                dbms="psql",
            )
            for name in os.listdir(ipso_folders.get_path("mass_storage"))
            if os.path.isdir(
                os.path.join(ipso_folders.get_path("mass_storage", False), name)
            )
        ]


if "phenoserre" in dbc:
    available_db_dicts[DbType.PHENOSERRE] = [
        DbInfo(
            display_name=name,
            target="phenoserre",
            dbms="pandas",
        )
        for name in get_phenoserre_exp_list()
    ]


if "phenopsis" in dbc:
    available_db_dicts[DbType.PHENOPSIS] = [
        DbInfo(
            display_name=name,
            target="phenopsis",
            dbms="pandas",
        )
        for name in get_phenopsis_exp_list()
    ]
