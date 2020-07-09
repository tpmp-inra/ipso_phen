import logging
import os
import sys
import datetime

if not os.path.exists("logs"):
    os.mkdir("logs")
logging.basicConfig(
    filename=os.path.join(
        "logs", f"{datetime.datetime.now().strftime('%Y%b%d %H%M%S')}_ipso_cli.log"
    ),
    filemode="w",
    level=logging.INFO,
    format="[%(asctime)s - %(name)s - %(levelname)s] - %(message)s",
)

sys.path.append("./ipapi")
