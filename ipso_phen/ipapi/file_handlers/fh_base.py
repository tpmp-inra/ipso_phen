import os
from pathlib import Path
import datetime
from datetime import datetime as dt
import inspect
from abc import ABC, abstractclassmethod, abstractproperty

import cv2
import numpy as np
import paramiko
import pandas as pd

import ipso_phen.ipapi.file_handlers
import ipso_phen.ipapi.base.ip_common as ipc
from ipso_phen.ipapi.tools.common_functions import get_module_classes, force_directories
from ipso_phen.ipapi.tools.folders import ipso_folders
import ipso_phen.ipapi.base.ip_common as ipc

import logging

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

call_back = None


class FileHandlerBase(ABC):
    def __init__(self, **kwargs):
        self._file_path = ""
        self._exp = ""
        self._plant = ""
        self._camera = ""
        self._angle = "0"
        self._wavelength = "SW755"
        self._date_time = None
        self._job_id = 0
        self._linked_images = []
        self._available_channels = {}
        self._database = None
        self._cache_file_path = ""
        self._cache_file_dir = ""
        self._blob_path = ""
        self.db_linked = False
        self._source_image = None
        self._current_image = None
        self._luid = None
        self.good_image = False

    def __repr__(self):  # Serialization
        return self.file_path

    def __str__(self):  # Human readable
        if self._date_time:
            return (
                f"[exp:{self.experiment}]"
                f"[plant:{self.plant}]"
                f"[date:{self.condensed_date}]"
                f"[camera:{self.camera}]"
                f"[angle:{self.angle}]"
                f"[wavelength:{self.wavelength}]"
            )
        else:
            return self.file_name

    def load_from_database(self, sftp):
        if os.path.isfile(self.cache_file_path):
            logger.debug(f"Retrieved from cache: {str(self)}")
            return self.load_from_harddrive(self.cache_file_path)
        src_img = None
        try:
            logger.info(f"Downloading {self.name}, please wait...")
            try:
                with sftp.open(self.blob_path) as file:
                    file_size = file.stat().st_size
                    file.prefetch(file_size)
                    file.set_pipelined()
                    src_img = cv2.imdecode(
                        np.fromstring(file.read(), np.uint8),
                        1,
                    )
                    if os.path.isdir(ipso_folders.get_path("mass_storage", False)):
                        force_directories(os.path.dirname(self.cache_file_path))
                        cv2.imwrite(self.cache_file_path, src_img)
            except Exception as e:
                logger.exception(f"FTP error: {repr(e)}")
            src_img = self.fix_image(src_image=src_img)
        except Exception as e:
            logger.exception(f"Failed to download {repr(self)} because {repr(e)}")
            return None
        else:
            logger.info(f"Download succeeded for  {self.name}")
            return src_img

    def load_from_harddrive(self, override_path: str = None):
        src_img = None
        try:
            fp = override_path if override_path is not None else self.file_path
            with open(fp, "rb") as stream:
                bytes = bytearray(stream.read())
            np_array = np.asarray(bytes, dtype=np.uint8)
            src_img = cv2.imdecode(np_array, 3)
            src_img = self.fix_image(src_image=src_img)
        except Exception as e:
            logger.exception(f"Failed to load {repr(self)} because {repr(e)}")
            return None
        else:
            return src_img

    def load_source_file(self):
        return self.load_from_harddrive()

    def update(self, **kwargs):
        self._file_path = kwargs.get("file_path", self._file_path)
        self._exp = kwargs.get("experiment", self._exp)
        self._plant = kwargs.get("plant", self._plant)
        self._camera = kwargs.get("camera", self._camera)
        self._angle = kwargs.get("angle", self._angle)
        self._wavelength = kwargs.get("wavelength", self._wavelength)
        if "date_time" in kwargs:
            try:
                ts = kwargs.get("date_time")
                if isinstance(ts, str):
                    self._date_time = dt.strptime(ts, "%Y-%m-%d %Hh%Mm%Ss")
                else:
                    self._date_time = ts
            except Exception as e:
                logger.exception(
                    f'Failed to update timestamp, please check format "{str(e)}"'
                )
        self._database = kwargs.get("database", None)

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
        elif key == "angle":
            return self.angle
        elif key == "wavelength":
            return self.wavelength
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
                if self.value_of(key) == val:
                    return True
            return False
        else:
            return self.value_of(key) == value

    def get_channel(self, src_img=None, channel="l"):
        if src_img is None:
            img = self.current_image
        elif len(src_img.shape) == 2:
            return src_img
        else:
            img = src_img.copy()
        if channel in ipc.CHANNELS_BY_SPACE[ipc.HSV]:
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            return hsv[:, :, 0 if channel == "h" else 1 if channel == "s" else 2]
        elif channel in ipc.CHANNELS_BY_SPACE[ipc.LAB]:
            lab = cv2.cvtColor(img, cv2.COLOR_BGR2Lab)
            return lab[:, :, 0 if channel == "l" else 1 if channel == "a" else 2]
        elif channel in ipc.CHANNELS_BY_SPACE[ipc.RGB]:
            return img[:, :, 0 if channel == "bl" else 1 if channel == "gr" else 2]
        else:
            return None

    def load_source_image(self, store_source=False):
        """
        Loads source image and applies corrections if needed

        :param store_source: if true image will be stores in image_list
        :return:numpy array -- Fixed source image
        """
        src_img = self.load_source_file()
        self.good_image = src_img is not None
        return src_img

    def check_source_image(self):
        _ = self.source_image
        return self.good_image

    @abstractclassmethod
    def probe(cls, file_path, database):
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
        if not self._date_time and self.db_linked:
            self._date_time = self._database.query_one(
                command="SELECT",
                columns="date_time",
                additional="ORDER BY date_time ASC",
                FilePath=self.file_path,
            )[0]
            self._date_time = pd.to_datetime(self._date_time)
        return self._date_time

    @property
    def job_id(self):
        return self._job_id

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
        return self._plant

    @property
    def camera(self):
        return self._camera

    @property
    def angle(self):
        return self._angle

    @property
    def wavelength(self):
        return self._wavelength

    @property
    def experiment(self):
        return self._exp

    @property
    def condensed_date(self):
        return dt.strftime(self.date_time, "%Y%m%d-%H%M%S")

    @property
    def luid(self):
        if self._luid is None:
            return f'{self.experiment}_{self.plant}_{dt.strftime(self.date_time, "%Y%m%d%H%M%S")}_{self.camera}_{self.angle}_{self.wavelength}'
        else:
            return self._luid

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

    @property
    def channels(self):
        return [ci[0] for ci in self.available_channels]

    @property
    def channels_data(self):
        return [ipc.build_channel_data(k, v) for k, v in self.available_channels.items()]

    @property
    def linked_images(self):
        return self._linked_images

    @property
    def blob_path(self):
        if not self._blob_path and self.db_linked is True:
            try:
                self._blob_path = self._database.query_one(
                    command="SELECT",
                    columns="blob_path",
                    FilePath=self.file_path,
                )[0]
            except Exception as e:
                self._blob_path = ""
        return self._blob_path

    @property
    def robot(self):
        return ""

    @property
    def cache_file_root(self):
        return (
            ipso_folders.get_path("mass_storage", False)
            if os.path.isdir(ipso_folders.get_path("mass_storage", False))
            else ipso_folders.get_path(key="img_cache", force_creation=True)
        )

    @property
    def cache_file_dir(self):
        if not self._cache_file_dir and self.db_linked is True:
            self._cache_file_dir = os.path.join(
                self.cache_file_root,
                self.robot,
                self.experiment,
                "",
            )
        return self._cache_file_dir

    @property
    def cache_file_path(self):
        if not self._cache_file_path and self.db_linked is True:
            self._cache_file_path = os.path.join(self.cache_file_dir, self.file_name)
        return self._cache_file_path

    @property
    def channels(self):
        return {}

    @property
    def source_image(self):
        if self._source_image is None:
            if self._current_image is not None:
                self._source_image = self._current_image.copy()
            else:
                self._source_image = self.load_source_image()
                self._current_image = None
        if self._source_image is None:
            return None
        else:
            return self._source_image.copy()

    @source_image.setter
    def source_image(self, value):
        if value is not None:
            self._source_image = value.copy()
        else:
            self._source_image = None
        self._current_image = None

    @property
    def current_image(self):
        if self._current_image is None:
            self._current_image = self.source_image
        return None if self._current_image is None else self._current_image.copy()

    @current_image.setter
    def current_image(self, value):
        self._current_image = value.copy() if value is not None else None

    @property
    def available_channels(self):
        return ipc.CHANNELS_VISIBLE

    @property
    def short_name(self):
        return f"[{self.plant}|{self.date}|{self.angle}]"


class FileHandlerDefault(FileHandlerBase):
    def __init__(self, **kwargs):
        super().__init__()
        self._file_path = kwargs.get("file_path", "")
        if self._file_path:
            self._plant = self.file_name_no_ext
            self._camera = "unknown"
            self._wavelength = "unknown"
            self._angle = "unknown"
            try:
                self._exp = os.path.basename(os.path.dirname(self.file_path))
            except Exception as e:
                logger.exception(f"Unable to extract extension: {repr(e)}")
                self._exp = ""
            try:
                self._date_time = dt.fromtimestamp(os.path.getmtime(self.file_path))
            except Exception as e:
                logger.exception(f"Unable to extract date from file because: {repr(e)}")
                self._date_time = dt.now()
            self._date_time = self._date_time.replace(microsecond=0)

        self.update(**kwargs)

    @classmethod
    def probe(cls, file_path, database):
        return 0


def file_handler_factory(file_path: str, database) -> FileHandlerBase:
    # Build unique class list
    file_handlers_list = get_module_classes(
        package=ipso_phen.ipapi.file_handlers,
        class_inherits_from=FileHandlerBase,
        remove_abstract=True,
    )
    file_handlers_list = [
        fh
        for fh in file_handlers_list
        if inspect.isclass(fh) and callable(getattr(fh, "probe", None))
    ]

    # Create objects
    best_score = 0
    best_class = None
    for cls in file_handlers_list:
        if cls.probe(file_path, database) > best_score:
            best_score = cls.probe(file_path, database)
            best_class = cls

    if best_class:
        return best_class(file_path=file_path, database=database)
    else:
        return FileHandlerDefault(file_path=file_path, database=database)
