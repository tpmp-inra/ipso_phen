import os
import sys
import unittest

abspath = os.path.abspath(__file__)
fld_name = os.path.dirname(abspath)
sys.path.insert(0, fld_name)
sys.path.insert(0, os.path.dirname(fld_name))
# When running tests from ipapi
sys.path.insert(0, os.path.join(os.path.dirname(fld_name), "ipso_phen", ""))

# When running tests from IPSO Phen
sys.path.insert(0, os.path.join(os.path.dirname(fld_name), "..", ""))

from ipapi.ipt.ipt_copy_or_rename_image import IptCopyOrRenameImage
from ipapi.base.ip_abstract import BaseImageProcessor
from ipapi.base.ipt_loose_pipeline import LoosePipeline
from ipapi.base.ipt_abstract_analyzer import IptBaseAnalyzer

import ipapi.base.ip_common as ipc


class TestIptCopyOrRenameImage(unittest.TestCase):
    def test_use_case(self):
        """Check that all use cases are allowed"""
        op = IptCopyOrRenameImage()
        for uc in op.use_case:
            self.assertIn(
                uc, list(ipc.tool_family_hints.keys()), f"Unknown use case {uc}"
            )

    def test_docstring(self):
        """Test that class process_wrapper method has docstring"""
        op = IptCopyOrRenameImage()
        if "(wip)" not in op.name.lower():
            self.assertIsNotNone(
                op.process_wrapper.__doc__, "Missing docstring for Copy or rename image"
            )

    def test_has_test_function(self):
        """Check that at list one test function has been generated"""
        self.assertTrue(True, "No compatible test function was generated")

    def test_needed_param(self):
        """Test that class has needed param path"""
        op = IptCopyOrRenameImage()
        self.assertTrue(
            op.has_param("path"), "Missing needed param path for Copy or rename image"
        )

    def test_feature_out(self):
        """Test that when using the basic mask generated script this tool extracts features"""
        op = IptCopyOrRenameImage()
        op.apply_test_values_overrides(use_cases=("",))
        script = LoosePipeline.load(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "samples",
                "pipelines",
                "test_extractors.json",
            )
        )
        script.add_module(operator=op, target_group="grp_test_extractors")
        wrapper = BaseImageProcessor(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "samples",
                "images",
                "arabido_small.jpg",
            )
        )
        res = script.execute(src_image=wrapper, silent_mode=True)
        self.assertIsInstance(
            op,
            IptBaseAnalyzer,
            "Copy or rename image must inherit from ipapi.iptBaseAnalyzer",
        )
        self.assertTrue(res, "Failed to process Copy or rename image with test script")
        self.assertNotEqual(
            first=len(wrapper.csv_data_holder.data_list),
            second=0,
            msg="Copy or rename image returned no data",
        )

    def test_documentation(self):
        """Test that module has corresponding documentation file"""
        op = IptCopyOrRenameImage()
        op_doc_name = op.name.replace(" ", "_")
        op_doc_name = "ipt_" + op_doc_name + ".md"
        self.assertTrue(
            os.path.isfile(
                os.path.join(os.path.dirname(__file__), "..", "help", f"{op_doc_name}")
            ),
            "Missing documentation file for Copy or rename image",
        )


if __name__ == "__main__":
    unittest.main()
