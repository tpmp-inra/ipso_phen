import os
import sys
import numpy as np
import unittest

abspath = os.path.abspath(__file__)
fld_name = os.path.dirname(abspath)
sys.path.insert(0, fld_name)
sys.path.insert(0, os.path.dirname(fld_name))
# When running tests from ipapi
sys.path.insert(0, os.path.join(os.path.dirname(fld_name), "ipso_phen", ""))

# When running tests from IPSO Phen
sys.path.insert(0, os.path.join(os.path.dirname(fld_name), "..", ""))

from ipapi.ipt.ipt_slic import IptSlic
from ipapi.base.ip_abstract import BaseImageProcessor
import ipapi.base.ip_common as ipc


class TestIptSlic(unittest.TestCase):
    def test_use_case(self):
        """Check that all use cases are allowed"""
        op = IptSlic()
        for uc in op.use_case:
            self.assertIn(
                uc, list(ipc.tool_family_hints.keys()), f"Unknown use case {uc}"
            )

    def test_docstring(self):
        """Test that class process_wrapper method has docstring"""
        op = IptSlic()
        if "(wip)" not in op.name.lower():
            self.assertIsNotNone(op.process_wrapper.__doc__, "Missing docstring for Slic")

    def test_has_test_function(self):
        """Check that at list one test function has been generated"""
        self.assertTrue(True, "No compatible test function was generated")

    def test_image_transformation(self):
        """Test that when an image is in an image goes out"""
        op = IptSlic()
        op.apply_test_values_overrides(use_cases=("Pre processing",))
        wrapper = BaseImageProcessor(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "samples",
                "images",
                "arabido_small.jpg",
            )
        )
        res = op.process_wrapper(wrapper=wrapper)
        self.assertTrue(res, "Failed to process Slic")
        self.assertIsInstance(op.result, np.ndarray, "Empty result for Slic")

    def test_documentation(self):
        """Test that module has corresponding documentation file"""
        op = IptSlic()
        op_doc_name = op.name.replace(" ", "_")
        op_doc_name = "ipt_" + op_doc_name + ".md"
        self.assertTrue(
            os.path.isfile(
                os.path.join(os.path.dirname(__file__), "..", "help", f"{op_doc_name}")
            ),
            "Missing documentation file for Slic",
        )


if __name__ == "__main__":
    unittest.main()
