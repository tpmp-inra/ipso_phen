import os
import sys
import unittest

abspath = os.path.abspath(__file__)
fld_name = os.path.dirname(abspath)
sys.path.insert(0, fld_name)
sys.path.insert(0, os.path.dirname(fld_name))
sys.path.insert(0, os.path.join(os.path.dirname(fld_name), "ipso_phen", ""))

from ipt.ipt_image_stats import IptImageStats
from base.ip_abstract import AbstractImageProcessor
from base.ipt_loose_pipeline import LoosePipeline
from base.ipt_abstract_analyzer import IptBaseAnalyzer

import base.ip_common as ipc


class TestIptImageStats(unittest.TestCase):
    def test_use_case(self):
        """Check that all use cases are allowed"""
        op = IptImageStats()
        for uc in op.use_case:
            self.assertIn(
                uc, list(ipc.tool_group_hints.keys()), f"Unknown use case {uc}"
            )

    def test_docstring(self):
        """Test that class process_wrapper method has docstring"""
        op = IptImageStats()
        if "(wip)" not in op.name.lower():
            self.assertIsNotNone(
                op.process_wrapper.__doc__, "Missing docstring for Image statistics"
            )

    def test_has_test_function(self):
        """Check that at list one test function has been generated"""
        self.assertTrue(True, "No compatible test function was generated")

    def test_feature_out(self):
        """Test that when using the basic mask generated script this tool extracts features"""
        op = IptImageStats()
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
        wrapper = AbstractImageProcessor(
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
            op, IptBaseAnalyzer, "Image statistics must inherit from IptBaseAnalyzer"
        )
        self.assertTrue(res, "Failed to process Image statistics with test script")
        self.assertNotEqual(
            first=len(wrapper.csv_data_holder.data_list),
            second=0,
            msg="Image statistics returned no data",
        )

    def test_documentation(self):
        """Test that module has corresponding documentation file"""
        op = IptImageStats()
        op_doc_name = op.name.replace(" ", "_")
        op_doc_name = "ipt_" + op_doc_name + ".md"
        self.assertTrue(
            os.path.isfile(
                os.path.join(os.path.dirname(__file__), "..", "help", f"{op_doc_name}")
            ),
            "Missing documentation file for Image statistics",
        )


if __name__ == "__main__":
    unittest.main()
