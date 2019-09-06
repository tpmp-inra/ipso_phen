from ip_base.ipt_abstract import IptBase
from ip_base.ip_common import TOOL_GROUP_VISUALIZATION_STR


class IptPrintContourOnImage(IptBase):

    def build_params(self):
        self.add_combobox(
            name='background',
            desc='Select background',
            default_value='source',
            values=dict(
                source='Source image', bw='Black and white', black='black', silver='silver', white='white'
            )
        )
        self.add_slider(
            name='bck_grd_luma', desc='Background lightness', default_value=100, minimum=0, maximum=100
        )

        self.add_separator('sep_1')
        self.add_combobox(
            name='foreground',
            desc='Select foreground',
            default_value='source',
            values=dict(
                source='Source image',
                bw='Black and white',
                false_colour='Pseudo colour',
                black='black',
                silver='silver',
                white='white'
            )
        )
        self.add_channel_selector(desc='Channel to use for pseudo color image', default_value='h')
        self.add_color_map_selector(name='color_map', default_value='c_2')
        self.add_checkbox(
            name='normalize_before', desc='Normalize channel before applying pseudo color', default_value=0
        )

        self.add_separator('sep_2')
        self.add_slider(
            name='contour_thickness', desc='Countour thickness', default_value=0, minimum=0, maximum=10
        )
        self.add_slider(name='hull_thickness', desc='Hull thickness', default_value=0, minimum=0, maximum=10)
        self.add_slider(
            name='bounding_rec_thickness',
            desc='Bounding rectangle thickness',
            default_value=0,
            minimum=0,
            maximum=10
        )
        self.add_slider(
            name='straight_bounding_rec_thickness',
            desc='Straight bounding rectangle  thickness',
            default_value=0,
            minimum=0,
            maximum=10
        )
        self.add_slider(
            name='enclosing_circle_thickness',
            desc='enclosing circle thickness',
            default_value=0,
            minimum=0,
            maximum=10
        )
        self.add_slider(name='centroid_width', desc='centroid width', default_value=0, minimum=0, maximum=20)
        self.add_slider(
            name='width_thickness', desc='width thickness', default_value=0, minimum=0, maximum=10
        )
        self.add_slider(
            name='height_thickness', desc='height thickness', default_value=0, minimum=0, maximum=10
        )

        self.add_separator('sep_3')
        self.add_text_overlay(default_value=0)

    def process_wrapper(self, **kwargs):
        """
        Draw image info: Requires class pipeline to work


        Real time : False

        Keyword Arguments (in parentheses, argument name):
            * Select background (background):
            * Background lightness (bck_grd_luma):
            * Select foreground (foreground):
            * Channel to use for pseudo color image (channel):
            * Select pseudo color map (color_map):
            * Normalize channel before applying pseudo color (normalize_before):
            * Countour thickness (contour_thickness):
            * Hull thickness (hull_thickness):
            * Bounding rectangle thickness (bounding_rec_thickness):
            * Straight bounding rectangle  thickness (straight_bounding_rec_thickness):
            * enclosing circle thickness (enclosing_circle_thickness):
            * centroid width (centroid_width):
            * width thickness (width_thickness):
            * height thickness (height_thickness):
            * Overlay text on top of images (text_overlay): Draw description text on top of images
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        text_overlay = self.get_value_of('text_overlay') == 1

        res = False
        try:
            # Build mask
            if wrapper.mask is None:
                wrapper.process_image(threshold_only=True)

            self.result = wrapper.draw_image(**self.params_to_dict())
            wrapper.store_image(self.result, f'COI_{wrapper.short_name}', text_overlay=text_overlay)

        except Exception as e:
            res = False
            wrapper.error_holder.add_error(f'Failed to print contour color image, exception: "{repr(e)}"')
        else:
            res = True
        finally:
            return res

    @property
    def name(self):
        return 'Draw image info'

    @property
    def real_time(self):
        if self.wrapper is None:
            return False
        else:
            return self.wrapper.mask is not None

    @property
    def result_name(self):
        return 'image'

    @property
    def output_kind(self):
        return 'image'

    @property
    def use_case(self):
        return [TOOL_GROUP_VISUALIZATION_STR]

    @property
    def description(self):
        return "Draw image info: Requires class pipeline to work"
