import datetime

from tools.image_list import ImageList
from tools.pipeline_processor import PipelineProcessor
from tools.common_functions import print_progress_bar
from file_handlers.fh_base import file_handler_factory


class PipelineProcessorDb(PipelineProcessor):

    def build_files_list(
        self,
        flatten_list=True,
        target_database=None,
        target_table='snapshots',
        accepted_extensions=('.jpg', '.tiff', '.png', '.bmp'),
        grab_associated_images: bool = False,
        **kwargs
    ):

        if target_database is None:
            self.accepted_files = []
            return -1

        ret = target_database.query(
            command='SELECT', columns='FilePath', table=target_table, additional='ORDER BY Time ASC', **kwargs
        )
        file_list_ = [item[0] for item in ret]

        img_lst = ImageList(accepted_extensions)
        self.accepted_files = img_lst.filter_db(input_list=file_list_, masks=self.masks, flat_list_out=flatten_list)
        if grab_associated_images:
            parse_list = self.accepted_files[:]
            total = len(parse_list)
            for i, root_file in enumerate(parse_list):
                fh = file_handler_factory(root_file)
                if fh.is_msp:
                    current_date_time = fh.date_time
                    lnk_img_lst = target_database.query(
                        command='SELECT',
                        columns='FilePath',
                        table=target_table,
                        additional='ORDER BY Date ASC',
                        experiment=fh.experiment,
                        plant=fh.plant,
                        camera=fh.camera,
                        date_time=dict(
                            operator='BETWEEN',
                            date_min=current_date_time - datetime.timedelta(minutes=10),
                            date_max=current_date_time + datetime.timedelta(minutes=10)
                        )
                    )
                    self.accepted_files.extend([item[0] for item in lnk_img_lst])
                if (fh.is_vis or fh.is_nir or fh.is_fluo) and ('side' in fh.view_option):
                    current_date_time = fh.date_time
                    lnk_img_lst = target_database.query(
                        command='SELECT',
                        columns='FilePath',
                        table=target_table,
                        additional='ORDER BY Date ASC',
                        experiment=fh.experiment,
                        plant=fh.plant,
                        camera=fh.camera,
                        date_time=dict(
                            operator='BETWEEN',
                            date_min=current_date_time - datetime.timedelta(minutes=10),
                            date_max=current_date_time + datetime.timedelta(minutes=10)
                        )
                    )
                    self.accepted_files.extend([item[0] for item in lnk_img_lst])
                else:
                    pass
                print_progress_bar(iteration=i, total=total, prefix=f'Grabbing files', suffix='complete')

        self.accepted_files = list(set(self.accepted_files))
        if len([True for mask in self.masks if mask.get('action', '') == 'pick_random']) == 0:
            self._last_signature += str(len(self.accepted_files))
        else:
            self._last_signature = ''

        return len(self.accepted_files) > 0
