import os
from datetime import datetime as dt

from sqlalchemy import Column, String, DATETIME
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ipso_phen.ipapi.tools.common_functions import force_directories
from ipso_phen.ipapi.tools.folders import ipso_folders

TABLE_ANNOTATIONS = "TABLE_ANNOTATIONS"


def to_padded_string(f):
    def new_function(*args):
        x = f(*args)
        if x > 100:
            return x
        else:
            return "{:02d}".format(x)

    return new_function


BaseOrmClass = declarative_base()


class OrmAnnotation(BaseOrmClass):
    __tablename__ = TABLE_ANNOTATIONS

    idk = Column(String(255, collation="NOCASE"), primary_key=True)
    kind = Column(String(255, collation="NOCASE"))
    text = Column(String(255, collation="NOCASE"))
    auto_text = Column(String(255, collation="NOCASE"))

    last_access = Column(DATETIME())
    first_access = Column(DATETIME())

    def __init__(self, idk, kind, text, auto_text):

        self.idk = idk
        self.kind = kind
        self.text = text
        self.auto_text = auto_text

        self.last_access = dt.now()
        self.first_access = dt.now()

    def __repr__(self):  # Serialization
        return f"{self.idk}_{self.kind}_{self.text}_{self.auto_text}"

    def __str__(self):  # Human readable
        return (
            f"[id:{self.idk}]"
            f"[kind:{self.kind}]"
            f"[text:{self.text}]"
            f"[auto_text:{self.auto_text}]"
        )

    def __eq__(self, other):
        return (self.idk == other.idk) and (self.kind == other.kind)

    def __lt__(self, other):
        return self.idk < other.idk


class OrmAnnotationsDbWrapper:
    def __init__(self, prefix):
        force_directories("saved_data")
        db_path = os.path.join(
            ipso_folders.get_path("saved_data", force_creation=True),
            f"{prefix}_annotations.db",
        )
        engine = create_engine(f"sqlite:///{db_path}")

        Session = sessionmaker(bind=engine)
        self.session = Session()
        BaseOrmClass.metadata.create_all(engine)

    def __enter__(self):
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.commit()
