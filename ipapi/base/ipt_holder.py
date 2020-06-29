from typing import Any
import pkgutil
import sys
import subprocess

if __name__ == "__main__":
    import os

    abspath = os.path.abspath(__file__)
    fld_name = os.path.dirname(abspath)
    sys.path.insert(0, fld_name)
    sys.path.insert(0, os.path.dirname(fld_name))
    sys.path.insert(0, os.path.join(os.path.dirname(fld_name), "ipso_phen", ""))

from tools.common_functions import get_module_classes
from base.ipt_abstract import IptBase
import ipt
import base.ip_common as ipc
import os
import inspect

# Check PlantCV
try:
    from plantcv import plantcv as pcv
except Exception as e:
    allow_pcv = False
else:
    allow_pcv = True


DEFAULT_TEST_IMAGE = "arabido_small.jpg"
HELIASEN_TEST_IMAGE = "18HP01U17-CAM11-20180712221558.bmp"
_FORCE_OVERWRITE = True


def add_tab(sc: str) -> str:
    return sc + "    "


def remove_tab(sc: str) -> str:
    return sc[4:]


class IptHolder(object):
    def __init__(self, **kwargs):
        self._ipt_list = []
        self._use_cases = []
        self._log_callback = None

    def _init_holders(self):
        """Build list containing a single instance of all available tools
        """
        # Build unique class list
        ipt_classes_list = get_module_classes(
            package=ipt, class_inherits_from=IptBase, remove_abstract=True
        )

        # Create objects
        for cls in ipt_classes_list:
            try:
                op = cls()
                self._ipt_list.append(op)
                self._use_cases.extend(op.use_case)
            except Exception as e:
                print(f'Failed to add "{cls.__name__}" because "{repr(e)}"')
            self._use_cases = sorted(list(set(self._use_cases)))
            self._ipt_list.sort(key=lambda x: (x.order, x.name))

    def list_by_use_case(self, use_case: str = ""):
        return [op for op in self.ipt_list if not use_case or (use_case in op.use_case)]

    def write_init_pipeline(
        self, f, use_case, pipeline_name, test_image, group_uuid, op, spaces
    ):
        f.write(f"{spaces}op = {op.__class__.__name__}()\n")
        f.write(f"{spaces}op.apply_test_values_overrides(use_cases=('{use_case}',))\n")
        f.write(f"{spaces}script = LoosePipeline.load(\n")
        spaces = add_tab(spaces)
        f.write(f"{spaces}os.path.join(\n")
        spaces = add_tab(spaces)
        f.write(
            f'{spaces}os.path.dirname(__file__), "..", "sample_pipelines", "{pipeline_name}",\n'
        )
        spaces = remove_tab(spaces)
        f.write(f"{spaces})\n")
        spaces = remove_tab(spaces)
        f.write(f"{spaces})\n")
        f.write(f"{spaces}script.add_module(operator=op, target_group='{group_uuid}')\n")
        f.write(f"{spaces}wrapper = AbstractImageProcessor(\n")
        spaces = add_tab(spaces)
        f.write(
            f'{spaces}os.path.join(os.path.dirname(__file__), "..", "sample_images", "{test_image}",)\n'
        )
        spaces = remove_tab(spaces)
        f.write(f"{spaces})\n")
        f.write(f"{spaces}res = script.execute(src_image=wrapper, silent_mode=True)\n")
        return spaces

    def write_init_operator(
        self,
        f,
        use_case: str,
        test_image: str,
        op,
        spaces: str,
        run_op: bool = True,
        store_images: bool = False,
    ):
        f.write(f"{spaces}op = {op.__class__.__name__}()\n")
        f.write(f"{spaces}op.apply_test_values_overrides(use_cases=('{use_case}',))\n")
        f.write(f"{spaces}wrapper = AbstractImageProcessor(\n")
        spaces = add_tab(spaces)
        f.write(
            f'{spaces}os.path.join(os.path.dirname(__file__), "..", "sample_images", "{test_image}",)\n'
        )
        spaces = remove_tab(spaces)
        f.write(f"{spaces})\n")
        if store_images:
            f.write(f"{spaces}wrapper.store_images = True\n")
        if run_op:
            f.write(f"{spaces}res = op.process_wrapper(wrapper=wrapper)\n")
        return spaces

    def write_imports(self, f, op, tests_needed: dict):
        f.write("import os\n")
        f.write("import sys\n")
        if (
            "img_in_img_out" in tests_needed
            or "img_in_msk_out" in tests_needed
            or "script_in_msk_out" in tests_needed
        ):
            f.write("import numpy as np\n")
        f.write("import unittest\n\n")
        f.write("abspath = os.path.abspath(__file__)\n")
        f.write("fld_name = os.path.dirname(abspath)\n")
        f.write("sys.path.insert(0, fld_name)\n")
        f.write("sys.path.insert(0, os.path.dirname(fld_name))\n")
        f.write(
            'sys.path.insert(0, os.path.join(os.path.dirname(fld_name), "ipso_phen", ""))\n\n'
        )
        f.write(f"from {op.__module__} import {op.__class__.__name__}\n")
        f.write("from base.ip_abstract import AbstractImageProcessor\n")
        if "script_in_info_out" in tests_needed or "script_in_msk_out" in tests_needed:
            f.write("from base.ipt_loose_pipeline import LoosePipeline\n")
            if "script_in_info_out" in tests_needed:
                f.write("from base.ipt_abstract_analyzer import IptBaseAnalyzer\n\n")

        if "img_in_roi_out" in tests_needed:
            f.write("import tools.regions as regions\n")
        f.write("import base.ip_common as ipc\n\n\n")

    def write_test_use_case(self, f, op, spaces):
        f.write(f"{spaces}def test_use_case(self):\n")
        spaces = add_tab(spaces)
        f.write(f'{spaces}"""Check that all use cases are allowed"""\n')
        f.write(f"{spaces}op = {op.__class__.__name__}()\n")
        f.write(f"{spaces}for uc in op.use_case:\n")
        spaces = add_tab(spaces)
        f.write(
            f'{spaces}self.assertIn(uc, list(ipc.tool_group_hints.keys()), f"Unknown use case {{uc}}")\n\n'
        )
        return remove_tab(remove_tab(spaces))

    def write_test_docstring(self, f, op, spaces):
        f.write(f"{spaces}def test_docstring(self):\n")
        spaces = add_tab(spaces)
        f.write(f'{spaces}"""Test that class process_wrapper method has docstring"""\n')
        f.write(f"{spaces}op = {op.__class__.__name__}()\n")
        f.write(f"{spaces}if '(wip)' not in op.name.lower():\n")
        spaces = add_tab(spaces)
        f.write(
            f"{spaces}self.assertIsNotNone(op.process_wrapper.__doc__, 'Missing docstring for {op.name}')\n\n"
        )
        return remove_tab(remove_tab(spaces))

    def write_test_needed_param(self, f, op, param_name, spaces):
        f.write(f"{spaces}def test_needed_param(self):\n")
        spaces = add_tab(spaces)
        f.write(f'{spaces}"""Test that class has needed param {param_name}"""\n')
        f.write(f"{spaces}op = {op.__class__.__name__}()\n")
        f.write(
            f'{spaces}self.assertTrue(op.has_param("{param_name}"), "Missing needed param path for {op.name}")\n\n'
        )
        return remove_tab(spaces)

    def write_test_has_test_function(self, f, op, spaces, found_fun):
        f.write(f"{spaces}def test_has_test_function(self):\n")
        spaces = add_tab(spaces)
        f.write(f'{spaces}"""Check that at list one test function has been generated"""\n')
        if found_fun:
            f.write(
                f"{spaces}self.assertTrue(True, 'No compatible test function was generated')\n\n"
            )
        else:
            f.write(
                f"{spaces}self.assertTrue(False, 'At least one compatible function was generated')\n\n"
            )
        return remove_tab(spaces)

    def write_test_mask_generation(self, f, op, spaces):
        f.write(f"{spaces}def test_mask_generation(self):\n")
        spaces = add_tab(spaces)
        f.write(f'{spaces}"""Test that when an image is in a mask goes out"""\n')
        self.write_init_operator(
            f=f,
            use_case=ipc.TOOL_GROUP_THRESHOLD_STR,
            test_image=HELIASEN_TEST_IMAGE
            if op.package.lower() == "heliasen"
            else DEFAULT_TEST_IMAGE,
            op=op,
            spaces=spaces,
            run_op=True,
        )
        f.write(f'{spaces}self.assertTrue(res, "Failed to process {op.name}")\n')
        f.write(
            f'{spaces}self.assertIsInstance(op.result, np.ndarray, "Empty result for {op.name}")\n'
        )
        f.write(
            f'{spaces}self.assertEqual(len(op.result.shape), 2, "Masks can only have one channel")\n'
        )
        f.write(
            f'{spaces}self.assertEqual(np.sum(op.result[op.result != 255]), 0, "Masks values can only be 0 or 255")\n\n'
        )
        return remove_tab(spaces)

    def write_test_image_transformation(self, f, op, spaces):
        f.write(f"{spaces}def test_image_transformation(self):\n")
        spaces = add_tab(spaces)
        f.write(f'{spaces}"""Test that when an image is in an image goes out"""\n')
        self.write_init_operator(
            f=f,
            use_case=ipc.TOOL_GROUP_PRE_PROCESSING_STR,
            test_image=HELIASEN_TEST_IMAGE
            if op.package.lower() == "heliasen"
            else DEFAULT_TEST_IMAGE,
            op=op,
            spaces=spaces,
            run_op=True,
        )
        f.write(f'{spaces}self.assertTrue(res, "Failed to process {op.name}")\n')
        f.write(
            f'{spaces}self.assertIsInstance(op.result, np.ndarray, "Empty result for {op.name}")\n\n'
        )
        return remove_tab(spaces)

    def write_test_mask_transformation(self, f, op, spaces):
        f.write(f"{spaces}def test_mask_transformation(self):\n")
        spaces = add_tab(spaces)
        f.write(
            f'{spaces}"""Test that when using the basic mask generated script this tool produces a mask"""\n'
        )
        spaces = self.write_init_pipeline(
            f=f,
            use_case=ipc.TOOL_GROUP_MASK_CLEANUP_STR,
            pipeline_name="test_cleaners.json",
            test_image=HELIASEN_TEST_IMAGE
            if op.package.lower() == "heliasen"
            else DEFAULT_TEST_IMAGE,
            group_uuid="grp_test_cleaners",
            op=op,
            spaces=spaces,
        )
        f.write(
            f'{spaces}self.assertTrue(res, "Failed to process {op.name} with test script")\n'
        )
        f.write(
            f'{spaces}self.assertIsInstance(wrapper.mask, np.ndarray, "Empty result for Range threshold")\n'
        )
        f.write(
            f'{spaces}self.assertEqual(len(wrapper.mask.shape), 2, "Masks can only have one channel")\n'
        )
        f.write(
            f'{spaces}self.assertEqual(np.sum(wrapper.mask[wrapper.mask != 255]), 0, "Masks values can only be 0 or 255")\n\n'
        )
        return remove_tab(spaces)

    def write_test_feature_out(self, f, op, spaces):
        f.write(f"{spaces}def test_feature_out(self):\n")
        spaces = add_tab(spaces)
        f.write(
            f'{spaces}"""Test that when using the basic mask generated script this tool extracts features"""\n'
        )
        spaces = self.write_init_pipeline(
            f=f,
            use_case="",
            pipeline_name="test_extractors.json",
            test_image=HELIASEN_TEST_IMAGE
            if op.package.lower() == "heliasen"
            else DEFAULT_TEST_IMAGE,
            group_uuid="grp_test_extractors",
            op=op,
            spaces=spaces,
        )
        f.write(
            f'{spaces}self.assertIsInstance(op, IptBaseAnalyzer, "{op.name} must inherit from IptBaseAnalyzer")\n'
        )
        f.write(
            f'{spaces}self.assertTrue(res, "Failed to process {op.name} with test script")\n'
        )
        f.write(f"{spaces}self.assertNotEqual(\n")
        spaces = add_tab(spaces)
        f.write(f"{spaces}first=len(wrapper.csv_data_holder.data_list),\n")
        f.write(f"{spaces}second=0,\n")
        f.write(f'{spaces}msg="{op.name} returned no data",\n')
        spaces = remove_tab(spaces)
        f.write(f"{spaces})\n\n")
        return remove_tab(spaces)

    def write_test_roi_out(self, f, op, spaces):
        f.write(f"{spaces}def test_roi_out(self):\n")
        spaces = add_tab(spaces)
        f.write(f'{spaces}"""Test that tool generates an ROI"""\n')
        self.write_init_operator(
            f=f,
            use_case=ipc.TOOL_GROUP_ROI,
            test_image=HELIASEN_TEST_IMAGE
            if op.package.lower() == "heliasen"
            else DEFAULT_TEST_IMAGE,
            op=op,
            spaces=spaces,
            run_op=True,
        )
        f.write(
            f'{spaces}self.assertTrue(hasattr(op, "generate_roi"), "Class must have method generate_roi")\n'
        )
        f.write(f'{spaces}self.assertTrue(res, "Failed to process {op.name}")\n')
        f.write(f"{spaces}r = op.generate_roi()\n")
        f.write(
            f'{spaces}self.assertIsInstance(r, regions.AbstractRegion, "ROI must be of type Region")\n\n'
        )
        return remove_tab(spaces)

    def write_test_bool_out(self, f, op, spaces):
        f.write(f"{spaces}def test_bool_out(self):\n")
        spaces = add_tab(spaces)
        f.write(f'{spaces}"""Test that tool returns a boolean"""\n')
        self.write_init_operator(
            f=f,
            use_case=ipc.TOOL_GROUP_ASSERT_STR,
            test_image=HELIASEN_TEST_IMAGE
            if op.package.lower() == "heliasen"
            else DEFAULT_TEST_IMAGE,
            op=op,
            spaces=spaces,
            run_op=True,
        )
        f.write(f'{spaces}self.assertTrue(res, "Failed to process {op.name}")\n')
        f.write(
            f'{spaces}self.assertIsInstance(op.result, bool, "{op.name} must return a boolean")\n\n'
        )
        return remove_tab(spaces)

    def write_test_visualization(self, f, op, spaces):
        f.write(f"{spaces}def test_visualization(self):\n")
        spaces = add_tab(spaces)
        f.write(f'{spaces}"""Test that visualization tools add images to list"""\n')
        self.write_init_operator(
            f=f,
            use_case=ipc.TOOL_GROUP_VISUALIZATION_STR,
            test_image=HELIASEN_TEST_IMAGE
            if op.package.lower() == "heliasen"
            else DEFAULT_TEST_IMAGE,
            op=op,
            spaces=spaces,
            run_op=True,
            store_images=True,
        )
        f.write(f"{spaces}res = op.process_wrapper(wrapper=wrapper)\n")
        f.write(f'{spaces}self.assertTrue(res, "Failed to process Simple white balance")\n')
        f.write(
            f'{spaces}self.assertGreater(len(wrapper.image_list), 0, "Visualizations must add images to list")\n\n'
        )
        return remove_tab(spaces)

    def write_test_documentation(self, f, op, spaces):
        f.write(f"{spaces}def test_documentation(self):\n")
        spaces = add_tab(spaces)
        f.write(f'{spaces}"""Test that module has corresponding documentation file"""\n')
        f.write(f"{spaces}op = {op.__class__.__name__}()\n")
        f.write(f"{spaces}op_doc_name = op.name.replace(' ', '_')\n")
        f.write(f"{spaces}op_doc_name = 'ipt_' + op_doc_name + '.md'\n")
        f.write(f"{spaces}self.assertTrue(\n")
        spaces = add_tab(spaces)
        f.write(f"{spaces}os.path.isfile(\n")
        spaces = add_tab(spaces)
        f.write(
            f"{spaces}os.path.join(os.path.dirname(__file__), '..', 'docs', f'{{op_doc_name}}')\n"
        )
        spaces = remove_tab(spaces)
        f.write(f"{spaces}),\n")
        f.write(f"{spaces}'Missing documentation file for {op.name}',\n")
        spaces = remove_tab(spaces)
        f.write(f"{spaces})\n\n")
        return remove_tab(spaces)

    def build_test_list(self, use_cases: tuple) -> dict:
        res = {}
        for name, group in zip(
            [
                "img_in_bool_out",
                "img_in_img_out",
                "img_in_msk_out",
                "output_folder",
                "script_in_msk_out",
                "script_in_info_out",
                "img_in_roi_out",
                "visualization",
            ],
            [
                [ipc.TOOL_GROUP_ASSERT_STR],
                [
                    ipc.TOOL_GROUP_EXPOSURE_FIXING_STR,
                    ipc.TOOL_GROUP_PRE_PROCESSING_STR,
                    ipc.TOOL_GROUP_WHITE_BALANCE_STR,
                    ipc.TOOL_GROUP_CLUSTERING_STR,
                ],
                [ipc.TOOL_GROUP_THRESHOLD_STR],
                [ipc.TOOL_GROUP_IMAGE_GENERATOR_STR],
                [ipc.TOOL_GROUP_MASK_CLEANUP_STR],
                [ipc.TOOL_GROUP_FEATURE_EXTRACTION_STR, ipc.TOOL_GROUP_IMAGE_GENERATOR_STR],
                [ipc.TOOL_GROUP_ROI],
                [ipc.TOOL_GROUP_VISUALIZATION_STR],
            ],
        ):
            if use_cases.intersection(group):
                res[name] = True
        return res

    def log_state(
        self,
        status_message: str = "",
        log_message: Any = None,
        use_status_as_log: bool = False,
        collect_garbage: bool = True,
    ):
        if self._log_callback is not None:
            return self._log_callback(
                status_message, log_message, use_status_as_log, collect_garbage
            )
        else:
            print(f"status: {status_message} - log: {log_message}")
            return True

    def build_test_files(self, log_callback=None):

        self._log_callback = log_callback
        try:
            i = 1
            files_to_format = []
            self.log_state(
                status_message=f"Building test scripts ...", use_status_as_log=True,
            )
            for (_, name, _) in pkgutil.iter_modules(ipt.__path__):
                if "pcv" in name and not allow_pcv:
                    self.log_state(
                        status_message=f"Ignoring {name}...",
                        log_message=f"Ignoring {name}, PlantCV not found",
                    )
                    continue

                pkg_name = ipt.__name__ + "." + name
                pkg = __import__(pkg_name)
                module = sys.modules[pkg_name]
                for _, cls_ in inspect.getmembers(module):
                    if not inspect.isclass(cls_):
                        continue
                    if not issubclass(cls_, IptBase):
                        continue
                    if inspect.isabstract(cls_):
                        continue
                    op = cls_()
                    file_name = os.path.join(
                        os.path.dirname(__file__), "..", "test", f"test_auto_{name}.py",
                    )
                    if not _FORCE_OVERWRITE and os.path.isfile(file_name):
                        self.log_state(
                            log_message=f"Skipped test script for {op.name}, script already exists"
                        )
                        continue
                    self.log_state(
                        status_message=f"Building test script for {op.name}",
                        use_status_as_log=True,
                    )
                    files_to_format.append(file_name)
                    with open(file_name, "w", encoding="utf8") as f:
                        needed_tests = self.build_test_list(set(op.use_case))

                        # Imports
                        self.write_imports(f, op, needed_tests)

                        # Class
                        f.write(f"class Test{op.__class__.__name__}(unittest.TestCase):\n")
                        spaces = add_tab("")

                        spaces = self.write_test_use_case(f, op, spaces=spaces)
                        spaces = self.write_test_docstring(f, op, spaces=spaces)

                        if op.short_test_script is True:
                            self.log_state(
                                log_message=f"Create short test script for {op.name}, as per class definition"
                            )
                            continue

                        spaces = self.write_test_has_test_function(
                            f, op, spaces=spaces, found_fun=needed_tests
                        )

                        if "output_folder" in needed_tests:
                            spaces = self.write_test_needed_param(
                                f, op, param_name="path", spaces=spaces
                            )

                        if "img_in_msk_out" in needed_tests:
                            spaces = self.write_test_mask_generation(f, op, spaces=spaces)

                        if "img_in_img_out" in needed_tests:
                            spaces = self.write_test_image_transformation(f, op, spaces=spaces)

                        if "script_in_msk_out" in needed_tests:
                            spaces = self.write_test_mask_transformation(f, op, spaces=spaces)

                        if "script_in_info_out" in needed_tests:
                            spaces = self.write_test_feature_out(f, op, spaces=spaces)

                        if "img_in_roi_out" in needed_tests:
                            spaces = self.write_test_roi_out(f, op, spaces=spaces)

                        if "img_in_bool_out" in needed_tests:
                            spaces = self.write_test_bool_out(f, op, spaces=spaces)

                        if "visualization" in needed_tests:
                            spaces = self.write_test_visualization(f, op, spaces=spaces)

                        spaces = self.write_test_documentation(f, op, spaces=spaces)

                        f.write("\n")
                        spaces = remove_tab(spaces)
                        f.write(f"{spaces}if __name__ == '__main__':\n")
                        spaces = add_tab(spaces)
                        f.write(f"{spaces}unittest.main()\n")

            self.log_state(
                status_message=f"Formatting test scripts ...", use_status_as_log=True,
            )
            for test_script in files_to_format:
                self.log_state(
                    status_message=f"Formating {test_script}", use_status_as_log=True,
                )
                subprocess.run(args=("black", test_script))

        finally:
            self._log_callback = None

    @property
    def ipt_list(self):
        if not self._ipt_list:
            self._init_holders()
        return self._ipt_list

    @property
    def use_cases(self):
        if not self._use_cases:
            self._init_holders()
        return self._use_cases


if __name__ == "__main__":
    ih = IptHolder()
    ih.build_test_files()
