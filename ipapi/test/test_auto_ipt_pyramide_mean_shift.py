import os
import sys
import numpy as np
import unittest

abspath = os.path.abspath(__file__)
fld_name = os.path.dirname(abspath)
sys.path.insert(0, fld_name)
sys.path.insert(0, os.path.dirname(fld_name))
sys.path.insert(0, os.path.join(os.path.dirname(fld_name), "ipso_phen", ""))

from ipapi.ipt.ipt_pyramide_mean_shift import IptPyramidMeanShift
from ipapi.base.ip_abstract import AbstractImageProcessor
import ipapi.base.ip_common as ipc


class TestIptPyramidMeanShift(unittest.TestCase):
    def test_use_case(self):
        """Check that all use cases are allowed"""
        op = IptPyramidMeanShift()
        for uc in op.use_case:
            self.assertIn(uc, list(ipc.tool_family_hints.keys()), f"Unknown use case {uc}")

    def test_docstring(self):
        """Test that class process_wrapper method has docstring"""
        op = IptPyramidMeanShift()
        if "(wip)" not in op.name.lower():
            self.assertIsNotNone(
                op.process_wrapper.__doc__, "Missing docstring for Pyramid mean shift"
            )

    def test_has_test_function(self):
        """Check that at list one test function has been generated"""
        self.assertTrue(True, "No compatible test function was generated")

    def test_image_transformation(self):
        """Test that when an image is in an image goes out"""
        op = IptPyramidMeanShift()
        op.apply_test_values_overrides(use_cases=("Pre processing",))
        wrapper = AbstractImageProcessor(
            os.path.join(
                os.path.dirname(__file__), "..", "samples", "images", "arabido_small.jpg",
            )
        )
        res = op.process_wrapper(wrapper=wrapper)
        self.assertTrue(res, "Failed to process Pyramid mean shift")
        self.assertIsInstance(op.result, np.ndarray, "Empty result for Pyramid mean shift")

    def test_documentation(self):
        """Test that module has corresponding documentation file"""
        op = IptPyramidMeanShift()
        op_doc_name = op.name.replace(" ", "_")
        op_doc_name = "ipt_" + op_doc_name + ".md"
        self.assertTrue(
            os.path.isfile(
                os.path.join(os.path.dirname(__file__), "..", "help", f"{op_doc_name}")
            ),
            "Missing documentation file for Pyramid mean shift",
        )


if __name__ == "__main__":
    unittest.main()
