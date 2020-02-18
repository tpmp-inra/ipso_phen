import os
import sys
import numpy as np
import unittest

abspath = os.path.abspath(__file__)
fld_name = os.path.dirname(abspath)
sys.path.insert(0, fld_name)
sys.path.insert(0, os.path.dirname(fld_name))
sys.path.insert(0, os.path.join(os.path.dirname(fld_name), "ipso_phen", ""))

from ip_tools.ipt_check_exposure import IptExposureChecker
from ip_base.ip_abstract import AbstractImageProcessor
from ip_base.ipt_strict_pipeline import IptStrictPipeline
from ip_base.ipt_abstract_analyzer import IptBaseAnalyzer

import ip_base.ip_common as ipc


class TestIptExposureChecker(unittest.TestCase):
    def test_use_case(self):
        """Check that all use cases are allowed"""
        op = IptExposureChecker()
        for uc in op.use_case:
            self.assertIn(
                uc, list(ipc.tool_group_hints.keys()), f"Unknown use case {uc}"
            )

    def test_docstring(self):
        """Test that class process_wrapper method has docstring"""
        op = IptExposureChecker()
        self.assertIsNotNone(
            op.process_wrapper.__doc__, "Missing docstring for Check exposure"
        )

    def test_has_test_function(self):
        """Check that at list one test function has been generated"""
        self.assertTrue(True, "No compatible test function was generated")

    def test_image_transformation(self):
        """Test that when an image is in an image goes out"""
        op = IptExposureChecker()
        op.apply_test_values_overrides(use_cases=("Pre processing",))
        res = op.process_wrapper(
            wrapper=os.path.join(
                os.path.dirname(__file__), "..", "sample_images", "arabido_small.jpg",
            )
        )
        self.assertTrue(res, "Failed to process Check exposure")
        self.assertIsInstance(op.result, np.ndarray, "Empty result for Check exposure")

    def test_feature_out(self):
        """Test that when using the basic mask generated script this tool extracts features"""
        op = IptExposureChecker()
        op.apply_test_values_overrides()
        self.assertIsInstance(
            op, IptBaseAnalyzer, "Check exposure must inherit from IptBaseAnalyzer"
        )
        script = IptStrictPipeline.load(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "sample_pipelines",
                "test_extractors.json",
            )
        )
        script.add_operator(operator=op, kind=ipc.TOOL_GROUP_FEATURE_EXTRACTION_STR)
        wrapper = AbstractImageProcessor(
            os.path.join(
                os.path.dirname(__file__), "..", "sample_images", "arabido_small.jpg",
            )
        )
        res = script.process_image(wrapper=wrapper)
        self.assertTrue(res, "Failed to process Check exposure with test script")
        self.assertNotEqual(
            first=len(wrapper.csv_data_holder.data_list),
            second=0,
            msg="Check exposure returned no data",
        )

    def test_documentation(self):
        """Test that module has corresponding documentation file"""
        op = IptExposureChecker()
        op_doc_name = op.name.replace(" ", "_")
        op_doc_name = "ipt_" + op_doc_name + ".md"
        self.assertTrue(
            os.path.isfile(
                os.path.join(os.path.dirname(__file__), "..", "docs", f"{op_doc_name}")
            ),
            "Missing documentation file for Check exposure",
        )


if __name__ == "__main__":
    unittest.main()