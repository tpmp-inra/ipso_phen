from datetime import datetime as dt

from file_handlers.fh_base import FileHandlerBase


class FileHandlerPhenopsys(FileHandlerBase):
    def __init__(self, **kwargs):
        self._file_path = kwargs.get("file_path", "")
        if self._file_path:
            [
                self._exp,
                self._plant,
                self._view_option,
                date_time_str,
                self._opaque,
            ] = self.file_name_no_ext.split(";")
            try:
                self._date_time = dt.strptime(date_time_str, "%Y,%m,%d-%Hh%Mm%Ss")
            except ValueError:
                self._date_time = dt.strptime(date_time_str, "%Y%m%d-%Hh%Mm%Ss")
            if "fluo-" in self._view_option.lower():
                self._camera = "cf"
                if self.is_cf_calc:
                    self._view_option = "calc"
                elif self.is_cf_csv:
                    self._view_option = "csv"
                elif self.is_cf_pim:
                    self._view_option = "pim"
                elif self.is_cf_raw:
                    self._view_option = "raw"
            else:
                self._camera, self._view_option = self._view_option.split("-")

        self.update(**kwargs)

    @classmethod
    def probe(cls, file_path):
        if ";" in cls.extract_file_name(file_path):
            return 100
        else:
            return 0

    @property
    def is_cf_calc(self):
        return (self.view_option == "fluo-") and (self.file_ext.lower() == ".jpg")

    @property
    def is_cf_raw(self):
        return (self.view_option == "fluo-") and (self.file_ext.lower() == ".tif")

    @property
    def is_cf_csv(self):
        return (self.view_option == "fluo-") and (self.file_ext.lower() == ".csv")

    @property
    def is_cf_pim(self):
        return (self.view_option == "fluo-") and (self.file_ext.lower() == ".pim")

    @property
    def is_msp(self):
        return ("msp" in self.camera) or ("msp" in self.view_option)

    @property
    def is_vis(self):
        return False
