import os
import json
import logging

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.tools.folders import ipso_folders

dbc_path = os.path.join(
    ipso_folders.get_path("db_connect_data", force_creation=False),
    "db_connect_data.json",
)

password_overrides = {}
master_password = None


def get_user_and_password(key: str) -> tuple:
    if master_password:
        return master_password
    elif key in password_overrides:
        return password_overrides[key]["user"], password_overrides[key]["password"]
    elif os.path.isfile(dbc_path):
        try:
            with open(dbc_path, "r") as f:
                dbc = json.load(f)[key]
            return dbc["user"], dbc["password"]
        except Exception as e:
            logger.error(f"Unable to find user and password: {repr(e)}")
            return None, None
    else:
        return None, None


def check_password(key: str) -> bool:
    if master_password or key in password_overrides:
        return True
    elif os.path.isfile(dbc_path):
        try:
            with open(dbc_path, "r") as f:
                dbc = json.load(f)[key]
            return "user" in dbc and "password" in dbc
        except Exception as e:
            logger.error(f"Unable to find user and password: {repr(e)}")
            return False
    else:
        return False
