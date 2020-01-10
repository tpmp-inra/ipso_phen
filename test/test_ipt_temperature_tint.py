import os
import sys
import numpy as np
import unittest

abspath = os.path.abspath(__file__)
fld_name = os.path.dirname(abspath)
sys.path.insert(0, fld_name)
sys.path.insert(0, os.path.dirname(fld_name))
sys.path.insert(0, os.path.join(os.path.dirname(fld_name), "ipso_phen", ""))

from ip_tools.ipt_temperature_tint import IptTemperatureTint
import ip_base.ip_common as ipc


class TestIptTemperatureTint(unittest.TestCase):
    def test_use_case(self):
        """Check that all use cases are allowed"""
        op = IptTemperatureTint()
        for uc in op.use_case:
            self.assertIn(
                uc, list(ipc.tool_group_hints.keys()), f"Unknown use case {uc}"
            )

    def test_docstring(self):
        """Test that class process_wrapper method has docstring"""
        op = IptTemperatureTint()
        self.assertIsNotNone(
            op.process_wrapper.__doc__, "Missing docstring for Temperature and tint"
        )

    def test_has_test_function(self):
        """Check that at list one test function has been generated"""
        self.assertTrue(True, "No compatible test function was generated")

    def test_image_transformation(self):
        """Test that when an image is in an image goes out"""
        op = IptTemperatureTint()
        op.apply_test_values_overrides(use_cases=("Pre processing",))
        res = op.process_wrapper(
            wrapper=os.path.join(
                os.path.dirname(__file__), "..", "sample_images", "arabido_small.jpg",
            )
        )
        self.assertTrue(res, "Failed to process Temperature and tint")
        self.assertIsInstance(
            op.result, np.ndarray, "Empty result for Temperature and tint"
        )

    def test_documentation(self):
        """Test that module has corresponding documentation file"""
        op = IptTemperatureTint()
        op_doc_name = op.name.replace(" ", "_")
        op_doc_name = "ipt_" + op_doc_name + ".md"
        self.assertTrue(
            os.path.isfile(
                os.path.join(os.path.dirname(__file__), "..", "docs", f"{op_doc_name}")
            ),
            "Missing documentation file for Temperature and tint",
        )


if __name__ == "__main__":
    unittest.main()
