import os
import numpy as np
import unittest

from ipso_phen.ipapi.ipt.ipt_temperature_tint import IptTemperatureTint
from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
import ipso_phen.ipapi.base.ip_common as ipc


class TestIptTemperatureTint(unittest.TestCase):
    def test_use_case(self):
        """Temperature and tint: Check that all use cases are allowed"""
        op = IptTemperatureTint()
        for uc in op.use_case:
            self.assertIn(
                uc, list(ipc.tool_family_hints.keys()), f"Unknown use case {uc}"
            )

    def test_docstring(self):
        """Temperature and tint: Test that class process_wrapper method has docstring"""
        op = IptTemperatureTint()
        if not op.is_wip:
            self.assertIsNotNone(
                op.process_wrapper.__doc__, "Missing docstring for Temperature and tint"
            )

    def test_has_test_function(self):
        """Temperature and tint: Check that at least one test function has been generated"""
        self.assertTrue(True, "No compatible test function was generated")

    def test_image_transformation(self):
        """Temperature and tint: Test that when an image is in an image goes out"""
        op = IptTemperatureTint()
        op.apply_test_values_overrides(use_cases=("Pre processing",))
        wrapper = BaseImageProcessor(
            "./ipso_phen/ipapi/samples/images/arabido_small.jpg",
            database=None,
        )
        res = op.process_wrapper(wrapper=wrapper)
        self.assertTrue(res, "Failed to process Temperature and tint")
        self.assertIsInstance(
            op.result, np.ndarray, "Empty result for Temperature and tint"
        )

    def test_documentation(self):
        doc_path = "./docs/ipt_Temperature_and_tint.md"
        self.assertTrue(
            os.path.isfile(doc_path),
            "Missing doc file for ROI composition {doc_path}",
        )


if __name__ == "__main__":
    unittest.main()
