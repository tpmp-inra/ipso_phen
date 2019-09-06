from datetime import datetime as dt

from file_handlers.fh_base import FileHandlerBase


class FileHandlerPhenoserre(FileHandlerBase):

    def __init__(self, **kwargs):
        self._file_path = kwargs.get('file_path', '')
        if self._file_path:
            tmp_str = self.file_name_no_ext.replace('(', '')
            tmp_str = tmp_str.replace(')', '')
            [self._plant, date_time_str, self._exp, cam_str] = tmp_str.split('--')
            self._date_time = dt.strptime(date_time_str, '%Y-%m-%d %H_%M_%S')
            [self._camera, self._view_option] = cam_str.split('-')

        self.update(**kwargs)

    @classmethod
    def probe(cls, file_path):
        if ')--(' in cls.extract_file_name(file_path):
            return 100
        else:
            return 0

    @property
    def is_vis(self):
        return 'vis' in self.camera

    @property
    def is_fluo(self):
        return 'fluo' in self.camera

    @property
    def is_nir(self):
        return 'nir' in self.camera
