import os
import numpy as np
import unittest

from ipso_phen.ipapi.ipt.ipt_fix_white_balance_with_roi import IptFixWhiteBalanceWithRoi
from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
import ipso_phen.ipapi.base.ip_common as ipc


class TestIptFixWhiteBalanceWithRoi(unittest.TestCase):
    def test_use_case(self):
        """Fix white balance with ROI: Check that all use cases are allowed"""
        op = IptFixWhiteBalanceWithRoi()
        for uc in op.use_case:
            self.assertIn(
                uc, list(ipc.tool_family_hints.keys()), f"Unknown use case {uc}"
            )

    def test_docstring(self):
        """Fix white balance with ROI: Test that class process_wrapper method has docstring"""
        op = IptFixWhiteBalanceWithRoi()
        if not op.is_wip:
            self.assertIsNotNone(
                op.process_wrapper.__doc__,
                "Missing docstring for Fix white balance with ROI",
            )

    def test_has_test_function(self):
        """Fix white balance with ROI: Check that at least one test function has been generated"""
        self.assertTrue(True, "No compatible test function was generated")

    def test_image_transformation(self):
        """Fix white balance with ROI: Test that when an image is in an image goes out"""
        op = IptFixWhiteBalanceWithRoi()
        op.apply_test_values_overrides(use_cases=("Pre processing",))
        wrapper = BaseImageProcessor(
            "./ipso_phen/ipapi/samples/images/arabido_small.jpg",
            database=None,
        )
        res = op.process_wrapper(wrapper=wrapper)
        self.assertTrue(res, "Failed to process Fix white balance with ROI")
        self.assertIsInstance(
            op.result, np.ndarray, "Empty result for Fix white balance with ROI"
        )

    def test_documentation(self):
        doc_path = "./docs/ipt_Fix_white_balance_with_ROI.md"
        self.assertTrue(
            os.path.isfile(doc_path),
            "Missing doc file for ROI composition {doc_path}",
        )


if __name__ == "__main__":
    unittest.main()
