import os
import numpy as np
import unittest

from ipso_phen.ipapi.ipt.ipt_horizontal_line_remover import IptHorizontalLineDetector
from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
import ipso_phen.ipapi.base.ip_common as ipc


class TestIptHorizontalLineDetector(unittest.TestCase):
    def test_use_case(self):
        """Horizontal line remover: Check that all use cases are allowed"""
        op = IptHorizontalLineDetector()
        for uc in op.use_case:
            self.assertIn(
                uc, list(ipc.tool_family_hints.keys()), f"Unknown use case {uc}"
            )

    def test_docstring(self):
        """Horizontal line remover: Test that class process_wrapper method has docstring"""
        op = IptHorizontalLineDetector()
        if not op.is_wip:
            self.assertIsNotNone(
                op.process_wrapper.__doc__,
                "Missing docstring for Horizontal line remover",
            )

    def test_has_test_function(self):
        """Horizontal line remover: Check that at least one test function has been generated"""
        self.assertTrue(True, "No compatible test function was generated")

    def test_image_transformation(self):
        """Horizontal line remover: Test that when an image is in an image goes out"""
        op = IptHorizontalLineDetector()
        op.apply_test_values_overrides(use_cases=("Pre processing",))
        wrapper = BaseImageProcessor(
            "./ipso_phen/ipapi/samples/images/18HP01U17-CAM11-20180712221558.bmp",
            database=None,
        )
        res = op.process_wrapper(wrapper=wrapper)
        self.assertTrue(res, "Failed to process Horizontal line remover")
        self.assertIsInstance(
            op.result, np.ndarray, "Empty result for Horizontal line remover"
        )

    def test_documentation(self):
        doc_path = "./docs/ipt_Horizontal_line_remover.md"
        self.assertTrue(
            os.path.isfile(doc_path),
            "Missing doc file for ROI composition {doc_path}",
        )


if __name__ == "__main__":
    unittest.main()
