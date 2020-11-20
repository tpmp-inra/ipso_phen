from datetime import datetime as dt
import os

from ipso_phen.ipapi.file_handlers.fh_base import FileHandlerBase


class FileHandlerGridSplit(FileHandlerBase):
    def __init__(self, **kwargs):
        self._file_path = kwargs.get("file_path", "")
        if self._file_path:
            _, *self._exp, self._plant = self.file_name_no_ext.split("_")
            self._exp = "_".join(self._exp)
            *_, self._view_option = self._plant.split("-")
            self._camera = "scanner"
            try:
                self._date_time = dt.fromtimestamp(
                    os.path.getmtime(self.file_path)
                ).replace(microsecond=0)
            except:
                self._date_time = dt.now().replace(microsecond=0)

        self.update(**kwargs)

    @classmethod
    def probe(cls, file_path, database):
        if not isinstance(file_path, str) or not os.path.isfile(file_path):
            return 0
        fn, _ = os.path.splitext(os.path.basename(file_path))
        return 100 if fn.startswith("gridsplit_") else 0

    @property
    def is_vis(self):
        return True
