import os
from datetime import datetime as dt

import ipso_phen.ipapi.file_handlers.fh_base as fh


class ImageWrapper:
    """Class wrapping an image item importing using the TPMP standard name"""

    def __init__(self, file_path, database):
        self._file_handler = fh.file_handler_factory(file_path, database)

    def __repr__(self):  # Serialization
        return self.file_path

    def __str__(self):  # Human readable
        return str(self._file_handler)

    def __eq__(self, other):
        return self.file_name == other.file_name

    def __lt__(self, other):
        if self.experiment < other.experiment:
            return True
        if self.experiment > other.experiment:
            return False

        if self.plant < other.plant:
            return True
        if self.plant > other.plant:
            return False

        # Compare date
        dt_self = self.date
        dt_other = other.date
        if dt_self < dt_other:
            return True
        if dt_self > dt_other:
            return False

        if self.camera != other.camera:
            if self.is_vis:
                return False
            elif self.is_fluo:
                return other.is_vis
            elif self.is_nir:
                return True
            else:
                return False

        if self.view_option < other.angle:
            return True
        if self.view_option > other.angle:
            return False

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
        return self.file_handler.compare_date(**kwargs)

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
        return self.file_handler.compare_time(**kwargs)

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
        return self.file_handler.compare_timestamp(**kwargs)

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
        return self.file_handler.is_between_dates(
            start_date, end_date, date_format, include_start, include_end
        )

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
        return self.file_handler.is_between_times(
            start_hour,
            start_minute,
            start_second,
            end_hour,
            end_minute,
            end_second,
            include_start,
            include_end,
        )

    def is_camera_match(self, camera_type):
        """Does camera_type match own camera

        Arguments:
            camera_type {str} -- camera mnemo

        Returns:
            boolean -- does camera match
        """

        if camera_type.lower() in ["*", ""]:
            return True
        elif camera_type.lower() == "nir":
            return self.is_nir
        elif camera_type.lower() == "vis":
            return self.is_vis
        elif camera_type.lower() == "fluo":
            return self.is_fluo
        else:
            return False

    def value_of(self, key):
        """Returns value associated to key

        Arguments:
            key {str} -- key

        Returns:
            str -- value
        """
        return self.file_handler.value_of(key)

    def matches(self, key, value):
        return self.file_handler.matches(key=key, value=value)

    @property
    def is_vis(self):
        return self._file_handler.is_vis

    @property
    def is_fluo(self):
        return self._file_handler.is_fluo

    @property
    def is_nir(self):
        return self._file_handler.is_nir

    @property
    def is_msp(self):
        return self._file_handler.is_msp

    @property
    def is_cf_calc(self):
        return self._file_handler.is_cf_calc

    @property
    def is_heliasen(self):
        return self._file_handler.is_heliasen

    @property
    def luid(self):
        return self._file_handler.luid

    @property
    def file_path(self):
        return self._file_handler.file_path

    @property
    def file_name(self):
        return self._file_handler.file_name

    @property
    def folder_path(self):
        return self._file_handler.folder_path

    @property
    def name(self):
        return self._file_handler.file_name_no_ext

    @property
    def experiment(self):
        return self._file_handler.experiment

    @property
    def year(self):
        return self._file_handler.year

    @property
    def month(self):
        return self._file_handler.month

    @property
    def day(self):
        return self._file_handler.day

    @property
    def hour(self):
        return self._file_handler.hour

    @property
    def minute(self):
        return self._file_handler.minute

    @property
    def second(self):
        return self._file_handler.second

    @property
    def plant(self):
        return self._file_handler.plant

    @property
    def camera(self):
        return self._file_handler.camera

    @property
    def view_option(self):
        return self._file_handler.view_option

    @property
    def csv_file_name(self):
        return "{}_result.csv".format(self.name)

    @property
    def date_time(self):
        return self._file_handler.date_time

    @property
    def date(self):
        return self._file_handler.date()

    @property
    def time(self):
        return self._file_handler.time()

    @property
    def date_str(self):
        return self.file_handler.date_str

    @property
    def is_drop_roi(self):
        return (
            self.is_fluo
            and self.view_option == "side45"
            and self.is_after_date(year="2018", month="02", day="06")
        ) or (
            self.is_vis
            and self.view_option == "side315"
            and self.is_at_date(year=2018, month="03", day=20)
        )

    @property
    def is_blue_guide(self):
        return (self.experiment.lower() == "008s1807_sym") or (
            (self.experiment.lower() == "013s1801_sym")
            and self.is_after_date(year="2018", month="02", day="27")
        )

    @property
    def is_green_guide(self):
        return self.experiment.lower() == "009s1709_sym" and self.is_after_date(
            year="2017", month="10", day="12"
        )

    @property
    def is_low_light(self):
        return ((self.experiment == "009s1709_sym") and self.is_fluo) or (
            (self.experiment == "011s1801_sym") and self.is_vis
        )

    @property
    def is_blue_background(self):
        return (
            self.is_vis
            and self.is_after_date(year="2018", month="03", day="22")
            and self.view_option != "top"
        )

    @property
    def is_wide_angle(self):
        return self.is_vis and self.is_before_date(year="2018", month="02", day="07")

    @property
    def is_no_wb_fix(self):
        return (
            self.is_vis
            and self.is_after_date(year="2018", month="03", day="20")
            and self.is_before_date(year="2018", month="03", day="27")
        )

    @property
    def is_overexposed(self):
        return self.is_fluo and self.is_before_date(year="2018", month="02", day="14")

    @property
    def scale_width(self):
        if self.is_vis:
            if self.is_wide_angle:
                return 1426
            else:
                return 1800
        else:
            return 1

    @property
    def short_name(self):
        return f"[exp:{self.experiment}][plant:{self.plant}][vo:{self.view_option}][{self._file_handler.condensed_date}]"

    @property
    def is_corrupted(self):
        return (
            not os.path.isfile(self.file_path)
            or (
                self.experiment in ["011s1801_sym", "013s1801_sym"]
                and self.is_before_date_time(
                    year="2018",
                    month="02",
                    day="01",
                    hour="12",
                    minute="00",
                    seconds="00",
                )
            )
            or (
                self.experiment == "020s1804_nem"
                and self.is_before_date(year="2018", month="04", day="20")
            )
        )

    @property
    def file_handler(self):
        return self._file_handler
