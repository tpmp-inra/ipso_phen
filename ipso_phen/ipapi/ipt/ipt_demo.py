import logging
import os

logger = logging.getLogger(os.path.splitext(__name__)[-1].replace(".", ""))

from ipso_phen.ipapi.base.ipt_functional import call_ipt
from ipso_phen.ipapi.base.ipt_abstract import IptBase
from ipso_phen.ipapi.base.ip_common import ToolFamily


class IptDemo(IptBase):
    def __init__(self, wrapper=None, **kwargs):
        """Normally there's no need to override the 'constructor'

        Keyword Arguments:
            wrapper {[BaseImageProcessor, str, None]} -- A wrapper, path to image or nothing (default: {None})
        """
        super().__init__(wrapper, **kwargs)
        self.update_count = 0

    def copy(self, copy_wrapper: bool = True):
        """Creates a copy of the current tool, widgets are never copied

        Keyword Arguments:
            copy_wrapper {bool} -- Copies the wrapper if true (default: {True})
        """
        res = super().copy(copy_wrapper)
        res.update_count = self.update_count
        return res

    def build_params(self):
        """
        Declare all widgets that will be present in the UI\n
        For this tool all available widgets will be displayed
        """
        self.add_label(
            name="lbl_zero",
            desc="Hi, I'm a demo tool, I'm here to showcase some widgets, I don't do much else",
        )
        self.add_combobox(
            name="output_mode",
            desc="Output image mode",
            default_value="raw",
            values=dict(
                raw="Source image",
                false_color="False color image from advanced widgets",
                full_widget="Edge detection from full widget",
                error_prone="Unknown mode, this will generate an error",
            ),
        )
        self.add_separator(name="sep0")
        self.add_checkbox(
            name="checkbox",
            desc="A sample checkbox",
            default_value=0,
            hint="This is a hint",
        )
        self.add_combobox(
            name="combobox",
            desc="Sample combobox",
            default_value="a",
            values=dict(
                a="First sample choice",
                b="Second sample choice",
                c="Third sample choice",
            ),
            hint="This is a sample combobox",
        )
        self.add_label(
            name="label",
            desc="This is a label, below there's a separator",
            hint="This is a label for a hint",
        )
        self.add_separator(name="sep1")
        self.add_slider(
            name="slider",
            desc="A slider",
            default_value=25,
            minimum=0,
            maximum=100,
            hint="This is a hint for a slider",
        )
        self.add_spin_box(
            name="spin_box",
            desc="A spin box",
            default_value=75,
            minimum=0,
            maximum=100,
            hint="This is a hint for a slider",
        )
        self.add_text_input(
            name="text_input",
            desc="A text input",
            default_value="Write any text you like",
            hint="This is a hint for the text input",
        )
        self.add_separator(name="sep2")
        self.add_text_output(
            is_single_line=True,
            name="text_output",
            desc="A sample text output widget",
            default_value="Change any parameter to change this output",
            hint="This is a hint for the text output widget",
        )
        self.add_table_output(
            name="table_output",
            desc=("key", "value"),
            default_value={},
            hint="This is a hint for the sample output table",
        )
        self.add_button(
            name="button_sample",
            desc="This is a button, click to see what happens",
            index=0,
            hint="This is a hint for a sample button",
        )
        self.add_separator(name="sep3")
        self.add_text_output(
            is_single_line=False,
            desc="Advanced widgets:",
            name="adv_txt",
            default_value="Some methods are simplified calls to build dedicated widgets\nSome examples follow",
        )
        self.add_channel_selector(default_value="h")
        self.add_color_map_selector()
        self.add_separator(name="sep3")
        self.add_text_output(
            is_single_line=False,
            desc="Composit widgets:",
            name="cmp_txt",
            default_value="Some methods build a full tool, for example an edge detector.\n"
            + "You can call directly an already implemented edge detector without handling anything.\n"
            + "All parameters set in this widget will be used by the edge detector.\n"
            + "Even the channel value from the false color above",
        )
        self.add_edge_detector()

    def execute(self, param, **kwargs):
        """
        Callback for all buttons.
        Calling button is identified by its name

        Arguments:
            param {dict} -- Any argument wanted/needed

        Returns:
            str -- returns name of the method to execute after execution
        """
        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            wrapper.store_image(
                image=255 - wrapper.current_image,
                text="inverted_image",
            )
            res = True
        except Exception as e:
            logger.error(f'Failed to execute: "{repr(e)}"')
            res = False
        else:
            pass
        finally:
            if res:
                return "print_images"
            else:
                return ""

    def process_wrapper(self, **kwargs):
        """
        IPT Demo:
        IPT Demo (Image Processing Tool Demo)
        A simple showcase of some of the available widgets
        Best starting point if you want to build your own widgets
        Real time : True

        Keyword Arguments (in parentheses, argument name):
            * Output image mode (output_mode):
            * A sample checkbox (checkbox): This is a hint
            * Sample combobox (combobox): This is a sample combobox
            * A slider (slider): This is a hint for a slider
            * A spin box (spin_box): This is a hint for a slider
            * A text input (text_input): This is a hint for the text input
            * This is a button, click to see what happens (button_sample): This is a hint for a sample button
            * Channel (channel):
            * Select pseudo color map (color_map):
            * Select edge detection operator (operator):
            * Canny's sigma (canny_sigma): Sigma.
            * Canny's first Threshold (canny_first): First threshold for the hysteresis procedure.
            * Canny's second Threshold (canny_second): Second threshold for the hysteresis procedure.
            * Kernel size (kernel_size):
            * Threshold (threshold): Threshold for kernel based operators
            * Apply threshold (apply_threshold):
        --------------
            * output  (text_output): A sample text output widget
            * output  (table_output): ('key', 'value')
            * output  (adv_txt): Advanced widgets:
            * output  (cmp_txt): Composit widgets:
        """

        wrapper = self.init_wrapper(**kwargs)
        if wrapper is None:
            return False

        res = False
        try:
            # Update table output
            p = self.find_by_name("table_output")
            p.update_output(output_value=self.params_to_dict())

            # Update multiline output
            p_out = self.find_by_name("text_output")
            p_in = self.find_by_name("text_input")
            self.update_count += 1
            if p_in is not None and p_out is not None:
                p_out.update_output(
                    label_text=f"Text updated {self.update_count} times",
                    output_value=p_in.value,
                )

            # Accessing a widget value, there's always a default value available
            output_mode = self.get_value_of("output_mode")
            if output_mode == "raw":
                img = wrapper.current_image
            elif output_mode == "false_color":
                img = wrapper.draw_image(
                    src_image=wrapper.current_image,
                    channel=self.get_value_of("channel"),
                    color_map=self.get_value_of("color_map"),
                    foreground="false_colour",
                )
            elif output_mode == "full_widget":
                # As all the params needed for  the tool are already in this one
                # we pass everything and the next tool will keep and reject what it wants.
                # The ipt_id param is the name of the class of the target tool
                img = call_ipt(
                    ipt_id="IptEdgeDetector", source=wrapper, **self.params_to_dict()
                )
            else:  # This how we handle errors
                # If the error is added to the wrapper, it will be displayed in the main log
                logger.error("Unknown output mode")
                # We can also create an empty image that will generate another error when storing it
                img = None

            wrapper.store_image(
                img,
                self.name,
                text_overlay=self.input_params_as_str(
                    exclude_defaults=False, excluded_params=("progress_callback",)
                ).replace(", ", "\n"),
            )
            self.result = img
            res = True
        except Exception as e:
            logger.error(f'Failed to process {self. name}: "{repr(e)}"')
            res = False
        else:
            pass
        finally:
            return res

    @property
    def name(self) -> str:
        """Name displayed for tool selection in menus and such

        Returns:
            str -- Name
        """
        return "IPT Demo"

    @property
    def real_time(self) -> bool:
        """Handles wether or not the tool will react in real time to input modifications\n
            Return value does not have to static\n
            Warning: Some tools may take a lot of time to compute

        Returns:
            bool -- Wether or not tool reacts in real time
        """
        return True

    @property
    def result_name(self) -> str:
        """Result name used when generating automated scripts\n
            In case of a tool that returns nothing (like this one) return 'none'
        Returns:
            str
        """
        return "none"

    @property
    def order(self) -> int:
        """Order in which the tool will be displayed.\n
            The lower the number, the higher the priority.\n
            Set this to a low value if you want your tools to show first

        Returns:
            int -- Priority value
        """
        return 1

    @property
    def output_kind(self) -> str:
        """Not used at the moment"""
        return ""

    @property
    def use_case(self) -> list:
        """Double purpose:\n
            * Tells the program in which submenu(s) this tool must be displayed
            * Used to know where this tool can be put in the pipelines

        Returns:
            list -- [description]
        """
        return [ToolFamily.DEMO, ToolFamily.VISUALIZATION]

    @property
    def description(self) -> str:
        """Short(ish) description of the tool.\n
            From this and the params comes the auto generated documentation that can be pasted to make the docstring\n
                cf. Help tab in IPSO Phen

        Returns:
            str -- [description]
        """
        return "IPT Demo (Image Processing Tool Demo)\nA simple showcase of some of the available widgets\nBest starting point if you want to build your own widgets"
