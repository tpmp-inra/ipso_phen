import os
import cv2
import numpy as np

from ip_base.ipt_abstract import IptBase
from tools.common_functions import force_directories
from ip_base.ip_common import TOOL_GROUP_IMAGE_GENERATOR_STR


class IptCopyImage(IptBase):

    def build_params(self):
        self.add_text_input(
            name='target_folder',
            desc='Target folder',
            default_value=os.path.join(os.path.expanduser('~'), 'Pictures', 'ipso_phen', '')
        )
        self.add_checkbox(
            name='add_sub_folder', desc='Put image in subfolder with experiment as its name', default_value=0
        )
        self.add_combobox(
            name='output_format',
            desc='Image output format',
            default_value='source',
            values=dict(source='As source image', jpg='JPEG', png='PNG', tiff='TIFF')
        )
        self.add_checkbox(name='test_only', desc='Test only, do not actually copy', default_value=1)
        self.add_separator(name='s1')
        self.add_checkbox(name='original', desc='Source image', default_value=1)
        self.add_checkbox(name='r90', desc='Rotate 90 degres', default_value=0)
        self.add_checkbox(name='r180', desc='Rotate 180 degres', default_value=0)
        self.add_checkbox(name='r270', desc='Rotate 270 degres', default_value=0)
        self.add_checkbox(name='flip_h', desc='flip horizontally', default_value=0)
        self.add_checkbox(name='flip_v', desc='flip vertically', default_value=0)
        self.add_separator(name='s2')
        self.add_text_input(
            name='gamma_values', desc='Gamma values (same syntax as grid search)', default_value='1'
        )

    def save_image(self, image, gamma):
        test_only = self.get_value_of('test_only') == 1
        write_original = self.get_value_of('original') == 1
        write_r90 = self.get_value_of('r90') == 1
        write_r180 = self.get_value_of('r180') == 1
        write_r270 = self.get_value_of('r270') == 1
        write_flip_h = self.get_value_of('flip_h') == 1
        write_flip_v = self.get_value_of('flip_v') == 1
        dst_path = self.get_value_of('target_folder')
        if self.get_value_of('add_sub_folder') == 1:
            dst_path = os.path.join(dst_path, self.wrapper.file_handler.experiment, '')
            force_directories(dst_path)

        file_ext = self.get_value_of('output_format')
        if file_ext == 'source':
            file_ext = self.wrapper.file_handler.file_ext
        else:
            file_ext = f'.{file_ext}'

        if gamma != 1:
            inv_gamma = 1.0 / gamma
            table = np.array([((i / 255.0)**inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
            img = cv2.LUT(src=image, lut=table)
            root_file_name = f'{self.wrapper.file_handler.file_name_no_ext}_{gamma:.2f}'
        else:
            img = image.copy()
            root_file_name = self.wrapper.file_handler.file_name_no_ext

        if write_original:
            if test_only:
                self.wrapper.store_image(img, root_file_name)
            else:
                cv2.imwrite(filename=os.path.join(dst_path, f'{root_file_name}{file_ext}'), img=img)
        if write_r90:
            t = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
            if test_only:
                self.wrapper.store_image(t, f'{root_file_name}_r90.{file_ext}')
            else:
                cv2.imwrite(filename=os.path.join(dst_path, f'{root_file_name}_r90.{file_ext}'), img=t)
        if write_r180:
            t = cv2.rotate(img, cv2.ROTATE_180)
            if test_only:
                self.wrapper.store_image(t, f'{root_file_name}_r180.{file_ext}')
            else:
                cv2.imwrite(filename=os.path.join(dst_path, f'{root_file_name}_r180.{file_ext}'), img=t)
        if write_r270:
            t = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
            if test_only:
                self.wrapper.store_image(t, f'{root_file_name}_r270.{file_ext}')
            else:
                cv2.imwrite(filename=os.path.join(dst_path, f'{root_file_name}_r270.{file_ext}'), img=t)
        if write_flip_h:
            t = cv2.flip(img, +1)
            if test_only:
                self.wrapper.store_image(t, f'{root_file_name}_flip_h.{file_ext}')
            else:
                cv2.imwrite(filename=os.path.join(dst_path, f'{root_file_name}_flip_h.{file_ext}'), img=t)
        if write_flip_v:
            t = cv2.transpose(img)
            t = cv2.flip(img, 0)
            if test_only:
                self.wrapper.store_image(t, f'{root_file_name}_flip_v.{file_ext}')
            else:
                cv2.imwrite(filename=os.path.join(dst_path, f'{root_file_name}_flip_v.{file_ext}'), img=t)

    def process_wrapper(self, **kwargs):
        """
        Copy image:
        Copies image to target folder
        Can have a ROI as a pre-processor
        Real time : False

        Keyword Arguments (in parentheses, argument name):
            * Target folder (target_folder): 
            * Put image in subfolder with experiment as its name (add_sub_folder): 
            * Image output format (output_format): 
            * Test only, do not actually copy (test_only): 
            * Source image (original): 
            * Rotate 90 degres (r90): 
            * Rotate 180 degres (r180): 
            * Rotate 270 degres (r270): 
            * flip horizontally (flip_h): 
            * flip vertically (flip_v): 
            * Gamma values (same syntax as grid search) (gamma_values): 
        --------------
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            if self.get_value_of('test_only') == 0:
                try:
                    force_directories(self.get_value_of('target_folder'))
                except Exception as e:
                    self.wrapper.error_holder.add_error(f'Unable to create folder: {repr(e)}')
            p = self.find_by_name(name='gamma_values')
            gsl = None if p is None else p.decode_string(p.value)
            src_img = wrapper.current_image
            if gsl:
                for gamma_value in gsl:
                    self.save_image(image=src_img, gamma=float(gamma_value))
            else:
                self.save_image(image=src_img, gamma=1)
        except Exception as e:
            wrapper.error_holder.add_error(f'Failed : "{repr(e)}"')
            res = False
        else:
            pass
        finally:
            return res

    @property
    def name(self):
        return 'Copy image'

    @property
    def real_time(self):
        return False

    @property
    def result_name(self):
        return 'none'

    @property
    def output_kind(self):
        return ''

    @property
    def use_case(self):
        return [TOOL_GROUP_IMAGE_GENERATOR_STR]

    @property
    def description(self):
        return """Copies image to target folder.\nCan use a ROI as a pre-processor"""
