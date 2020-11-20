from datetime import datetime as dt

from ipso_phen.ipapi.file_handlers.fh_base import FileHandlerBase


class FileHandlerStub(FileHandlerBase):
    def __init__(self, **kwargs):
        """Fill plant, date, time, experiment, camera and view_option from file data"""
        # Your code here

        self.update(**kwargs)

    @classmethod
    def probe(cls, file_path, database):
        """Checks wether or not the file in file_path can be handled"""
        # Your code here
        return 0
