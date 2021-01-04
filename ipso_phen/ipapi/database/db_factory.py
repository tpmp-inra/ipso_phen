import os
import json
from typing import Union

from ipso_phen.ipapi.database.base import DbInfo, DbWrapper

from ipso_phen.ipapi.database.sqlite_wrapper import SqLiteDbWrapper
from ipso_phen.ipapi.database.psql_wrapper import PgSqlDbWrapper

from ipso_phen.ipapi.tools.folders import ipso_folders

from ipso_phen.ipapi.database.phenoserre_wrapper import PhenoserreDbWrapper
from ipso_phen.ipapi.database.phenopsis_wrapper import PhenopsisDbWrapper

dbc_path = os.path.join(
    ipso_folders.get_path("db_connect_data", force_creation=False),
    "db_connect_data.json",
)
if os.path.isfile(dbc_path):
    with open(dbc_path, "r") as f:
        dbc = json.load(f)
else:
    dbc = {}


def db_info_to_database(info: DbInfo, **kwargs) -> Union[DbWrapper, str]:
    """Connects to a database from information, may create DB if needed and able

    Arguments:
        info {DbInfo} -- Describes the database

    Returns:
        [DbWrapper, str] -- Database wrapper if success, string descriging the problem else
    """
    if info.target == "psql_local":
        return PgSqlDbWrapper(
            **dbc.get(info.target, {}),
            db_info=info.copy(),
            progress_call_back=kwargs.get("progress_call_back", None),
        )
    elif info.target == "sqlite":
        return SqLiteDbWrapper(
            db_info=info.copy(),
            **dbc.get(info.target, {}),
            progress_call_back=kwargs.get("progress_call_back", None),
            db_folder_name=info.db_folder_name,
        )
    elif info.target == "phenoserre":
        return PhenoserreDbWrapper(
            db_info=info.copy(),
            progress_call_back=kwargs.get("progress_call_back", None),
        )
    elif info.target == "phenopsis":
        return PhenopsisDbWrapper(
            db_info=info.copy(),
            progress_call_back=kwargs.get("progress_call_back", None),
        )
    else:
        return f"Unknown target {info.target}"
