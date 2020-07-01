import os
import datetime
from datetime import datetime as dt
import inspect
import sys
from abc import ABC, abstractclassmethod
import pkgutil

import file_handlers
from tools.common_functions import get_module_classes


class FileHandlerBase(ABC):
    def __init__(self, **kwargs):
        self._file_path = ""
        self._exp = ""
        self._plant = ""
        self._camera = ""
        self._view_option = ""
        self._date_time = dt.now()
        self.update(**kwargs)

    def update(self, **kwargs):
        if "file_path" in kwargs:
            self._file_path = kwargs.get("file_path")
        if "experiment" in kwargs:
            self._exp = kwargs.get("experiment")
        if "plant" in kwargs:
            self._plant = kwargs.get("plant")
        if "camera" in kwargs:
            self._camera = kwargs.get("camera")
        if "view_option" in kwargs:
            self._view_option = kwargs.get("view_option")
        if "date_time" in kwargs:
            try:
                ts = kwargs.get("date_time")
                if isinstance(ts, str):
                    self._date_time = dt.strptime(ts, "%Y-%m-%d %Hh%Mm%Ss")
                else:
                    self._date_time = ts
            except Exception as e:
                print(f'Failed to update timestamp, please check format "{str(e)}"')

    def __repr__(self):  # Serialization
        return self.file_path

    def __str__(self):  # Human readable
        return (
            f"[exp:{self.experiment}]"
            f"[plant:{self.plant}]"
            f"[date:{self.condensed_date}]"
            f"[camera:{self.camera}]"
            f"[view_option:{self.view_option}]"
        )

    def fix_image(self, src_image):
        return src_image

    def compare_date(self, **kwargs):
        """Compares wrapper's date to kwargs date

        Keyword arguments either date, wrapper or assortment of year, month, day:
            * date: date type
            * year: as int or str: if missing will be replaced by wrapper's data
            * month: as int or str: if missing will be replaced by wrapper's data
            * day: as int or str: if missing will be replaced by wrapper's data
            * wrapper: wrappers dates will be compared
        :return: 0 if equal, -1 if before, 1 if after
        """
        dtc = kwargs.get("date", None)
        if dtc is None:
            wrapper = kwargs.get("wrapper", None)
            if wrapper:
                y, m, d = wrapper.year, wrapper.month, wrapper.day
            else:
                y = str(kwargs.get("year", self.year))
                m = str(kwargs.get("month", self.month))
                d = str(kwargs.get("day", self.day))
            dtc = dt.strptime(f"{y}_{m}_{d}", "%Y_%m_%d")
        if dtc.date() == self.date:
            return 0
        elif self.date < dtc.date():
            return -1
        else:
            return 1

    def compare_time(self, **kwargs):
        """Compares wrapper's time to kwargs time

        Keyword arguments either date, wrapper or assortment of year, month, day:
            * time: time type
            * hour: as int or str: if missing will be replaced by wrapper's data
            * minute: as int or str: if missing will be replaced by wrapper's data
            * second: as int or str: if missing will be replaced by wrapper's data
            * wrapper: wrappers times will be compared
        :return: 0 if equal, -1 if before, 1 if after
        """
        ttc = kwargs.get("date", None)
        if ttc is None:
            wrapper = kwargs.get("wrapper", None)
            if wrapper:
                h, m, s = wrapper.hour, wrapper.minute, wrapper.second
            else:
                h = str(kwargs.get("hour", self.hour))
                m = str(kwargs.get("minute", self.minute))
                s = str(kwargs.get("second", self.second))
            ttc = dt.strptime(f"{h}-{m}-{s}", "%H-%M-%S")
        if ttc.time() == self.time:
            return 0
        elif self.time < ttc.time():
            return -1
        else:
            return 1

    def compare_timestamp(self, **kwargs):
        """Compares wrapper's time to kwargs time

        Keyword arguments either date, wrapper or assortment of year, month, day:
            * time: time type
            * year: as int or str: if missing will be replaced by wrapper's data
            * month: as int or str: if missing will be replaced by wrapper's data
            * day: as int or str: if missing will be replaced by wrapper's data
            * hour: as int or str: if missing will be replaced by wrapper's data
            * minute: as int or str: if missing will be replaced by wrapper's data
            * second: as int or str: if missing will be replaced by wrapper's data
            * wrapper: wrappers times will be compared
        :return: 0 if equal, -1 if before, 1 if after
        """
        dtc = self.compare_date(**kwargs)
        if dtc == 0:
            return self.compare_time(**kwargs)
        else:
            return dtc

    def is_at_date(self, **kwargs):
        """Compares wrapper's date to kwargs date

        Keyword arguments either date, wrapper or assortment of year, month, day:
            * date: date type
            * year: as int or str: if missing will be replaced by wrapper's data
            * month: as int or str: if missing will be replaced by wrapper's data
            * day: as int or str: if missing will be replaced by wrapper's data
            * wrapper: wrappers dates will be compared
        :return: True if equal
        """
        return self.compare_date(**kwargs) == 0

    def is_after_date(self, **kwargs):
        """Compares wrapper's date to kwargs date

        Keyword arguments either date, wrapper or assortment of year, month, day:
            * date: date type
            * year: as int or str: if missing will be replaced by wrapper's data
            * month: as int or str: if missing will be replaced by wrapper's data
            * day: as int or str: if missing will be replaced by wrapper's data
            * wrapper: wrappers dates will be compared
        :return: True if wrapper's date is after kwargs data
        """
        return self.compare_date(**kwargs) > 0

    def is_before_date(self, **kwargs):
        """Compares wrapper's date to kwargs date

        Keyword arguments either date, wrapper or assortment of year, month, day:
            * date: date type
            * year: as int or str: if missing will be replaced by wrapper's data
            * month: as int or str: if missing will be replaced by wrapper's data
            * day: as int or str: if missing will be replaced by wrapper's data
            * wrapper: wrappers dates will be compared
        :return: True if wrapper's date is before kwargs data
        """
        return self.compare_date(**kwargs) < 0

    def is_at_time(self, **kwargs):
        """Compares wrapper's time to kwargs time

        Keyword arguments either date, wrapper or assortment of year, month, day:
            * time: time type
            * hour: as int or str: if missing will be replaced by wrapper's data
            * minute: as int or str: if missing will be replaced by wrapper's data
            * second: as int or str: if missing will be replaced by wrapper's data
            * wrapper: wrappers times will be compared
        :return: True if equal
        """
        return self.compare_time(**kwargs) == 0

    def is_before_time(self, **kwargs):
        """Compares wrapper's time to kwargs time

        Keyword arguments either date, wrapper or assortment of year, month, day:
            * time: time type
            * hour: as int or str: if missing will be replaced by wrapper's data
            * minute: as int or str: if missing will be replaced by wrapper's data
            * second: as int or str: if missing will be replaced by wrapper's data
            * wrapper: wrappers times will be compared
        :return: True if wrapper's time is before kwargs data
        """
        return self.compare_time(**kwargs) < 0

    def is_after_time(self, **kwargs):
        """Compares wrapper's time to kwargs time

        Keyword arguments either date, wrapper or assortment of year, month, day:
            * time: time type
            * hour: as int or str: if missing will be replaced by wrapper's data
            * minute: as int or str: if missing will be replaced by wrapper's data
            * second: as int or str: if missing will be replaced by wrapper's data
            * wrapper: wrappers times will be compared
        :return: True if wrapper's time is after kwargs data
        """
        return self.compare_time(**kwargs) > 0

    def is_at_date_time(self, **kwargs):
        return self.compare_timestamp(**kwargs) == 0

    def is_after_date_time(self, **kwargs):
        return self.compare_timestamp(**kwargs) > 0

    def is_before_date_time(self, **kwargs):
        return self.compare_timestamp(**kwargs) < 0

    def is_between_dates(
        self,
        start_date,
        end_date,
        date_format="%Y_%m_%d",
        include_start=True,
        include_end=False,
    ):
        if isinstance(start_date, str):
            start_date = dt.strptime(start_date, date_format)
        if isinstance(end_date, str):
            end_date = dt.strptime(end_date, date_format)
        if include_start:
            start_date -= datetime.timedelta(days=1)
        if include_end:
            end_date += datetime.timedelta(days=1)

        return start_date.date() < self.date < end_date.date()

    def is_between_times(
        self,
        start_hour="00",
        start_minute="00",
        start_second="00",
        end_hour="00",
        end_minute="00",
        end_second="00",
        include_start=True,
        include_end=False,
    ):
        start = dt.strptime(f"{start_hour}-{start_minute}-{start_second}", "%H-%M-%S")
        end = dt.strptime(f"{end_hour}-{end_minute}-{end_second}", "%H-%M-%S")
        if include_start:
            start -= datetime.timedelta(seconds=1)
        if include_end:
            end += datetime.timedelta(seconds=1)
        start = start.time()
        end = end.time()
        return start < self.time < end

    def value_of(self, key):
        """Returns value associated to key

        Arguments:
            key {str} -- key

        Returns:
            str -- value
        """

        if key == "exp":
            return self.experiment
        elif key == "plant":
            return self.plant
        elif key == "cam":
            return self.camera
        elif key == "view_option":
            return self.view_option
        elif key == "date":
            return self.date_str
        elif key == "year":
            return self.year
        elif key == "month":
            return self.month
        elif key == "day":
            return self.day
        elif key == "hour":
            return self.hour
        elif key == "minute":
            return self.minute
        elif key == "second":
            return self.second
        else:
            return ""

    def matches(self, key, value):
        if isinstance(value, list):
            for val in value:
                if self.value_of(key).lower() == val.lower():
                    return True
            return False
        else:
            return self.value_of(key).lower() == value.lower()

    @abstractclassmethod
    def probe(cls, file_path):
        return 0

    @classmethod
    def extract_file_name(cls, file_path):
        return os.path.basename(file_path)

    @property
    def file_path(self):
        return self._file_path

    @property
    def folder_path(self):
        return os.path.join(os.path.dirname(self.file_path), "")

    @property
    def file_name(self):
        return os.path.basename(self._file_path)

    @property
    def file_name_no_ext(self):
        fn, _ = os.path.splitext(self.file_name)
        return fn

    @property
    def file_ext(self):
        _, ext = os.path.splitext(self.file_name)
        return ext

    @property
    def name(self):
        return self.file_name_no_ext

    @property
    def date(self):
        return self.date_time.date()

    @property
    def time(self):
        return self.date_time.time()

    @property
    def date_time(self):
        return self._date_time

    @property
    def date_str(self):
        return dt.strftime(self.date_time, "%Y-%m-%d %H:%M:%S")

    @property
    def year(self):
        return self.date_time.year

    @property
    def month(self):
        return self.date_time.month

    @property
    def day(self):
        return self.date_time.day

    @property
    def hour(self):
        return self.date_time.hour

    @property
    def minute(self):
        return self.date_time.minute

    @property
    def second(self):
        return self.date_time.second

    @property
    def plant(self):
        return self._plant.lower()

    @property
    def camera(self):
        return self._camera.lower()

    @property
    def view_option(self):
        return self._view_option.lower()

    @property
    def experiment(self):
        return self._exp.lower()

    @property
    def condensed_date(self):
        return dt.strftime(self._date_time, "%Y%m%d-%H%M%S")

    @property
    def luid(self):
        return f'{self.experiment}_{self.plant}_{dt.strftime(self._date_time, "%Y%m%d%H%M%S")}_{self.camera}_{self.view_option}'

    @property
    def is_vis(self):
        return True

    @property
    def is_fluo(self):
        return False

    @property
    def is_nir(self):
        return False

    @property
    def is_msp(self):
        return False

    @property
    def is_cf_calc(self):
        return False

    @property
    def is_cf_raw(self):
        return False

    @property
    def is_cf_csv(self):
        return False

    @property
    def is_cf_pim(self):
        return False

    @property
    def is_heliasen(self):
        return False


class FileHandlerDefault(FileHandlerBase):
    def __init__(self, **kwargs):
        self._file_path = kwargs.get("file_path", "")
        if self._file_path:
            self._plant = self.file_name_no_ext
            self._camera = "unknown"
            _, ext_ = os.path.splitext(self.file_name)
            self._view_option = ext_ if ext_ else "unknown"
            try:
                self._exp = os.path.basename(os.path.dirname(self.file_path))
            except Exception as e:
                print(f"Unable to extract extension: {repr(e)}")
                self._exp = ""
            try:
                self._date_time = dt.fromtimestamp(os.path.getmtime(self.file_path))
            except Exception as e:
                print(f"Unable to extract date from file because: {repr(e)}")
                self._date_time = dt.now()
            self._date_time = self._date_time.replace(microsecond=0)

        self.update(**kwargs)

    @classmethod
    def probe(cls, file_path):
        return 0


def file_handler_factory(file_path: str) -> FileHandlerBase:
    # Build unique class list
    file_handlers_list = get_module_classes(
        package=file_handlers, class_inherits_from=FileHandlerBase, remove_abstract=True
    )

    # Create objects
    best_score = 0
    best_class = None
    for cls in file_handlers_list:
        if (
            inspect.isclass(cls)
            and callable(getattr(cls, "probe", None))
            and (cls.probe(file_path) > best_score)
        ):
            best_score = cls.probe(file_path)
            best_class = cls

    if best_class:
        return best_class(file_path=file_path)
    else:
        return FileHandlerDefault(file_path=file_path)