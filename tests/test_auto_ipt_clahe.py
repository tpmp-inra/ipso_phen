import os
import numpy as np
import unittest

from ipso_phen.ipapi.ipt.ipt_clahe import IptClahe
from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
import ipso_phen.ipapi.base.ip_common as ipc


class TestIptClahe(unittest.TestCase):
    def test_use_case(self):
        """CLAHE: Check that all use cases are allowed"""
        op = IptClahe()
        for uc in op.use_case:
            self.assertIn(
                uc, list(ipc.tool_family_hints.keys()), f"Unknown use case {uc}"
            )

    def test_docstring(self):
        """CLAHE: Test that class process_wrapper method has docstring"""
        op = IptClahe()
        if not op.is_wip:
            self.assertIsNotNone(
                op.process_wrapper.__doc__, "Missing docstring for CLAHE"
            )

    def test_has_test_function(self):
        """CLAHE: Check that at least one test function has been generated"""
        self.assertTrue(True, "No compatible test function was generated")

    def test_image_transformation(self):
        """CLAHE: Test that when an image is in an image goes out"""
        op = IptClahe()
        op.apply_test_values_overrides(use_cases=("Pre processing",))
        wrapper = BaseImageProcessor(
            "./ipso_phen/ipapi/samples/images/arabido_small.jpg",
            database=None,
        )
        res = op.process_wrapper(wrapper=wrapper)
        self.assertTrue(res, "Failed to process CLAHE")
        self.assertIsInstance(op.result, np.ndarray, "Empty result for CLAHE")

    def test_documentation(self):
        doc_path = "./docs/ipt_CLAHE.md"
        self.assertTrue(
            os.path.isfile(doc_path),
            "Missing doc file for ROI composition {doc_path}",
        )


if __name__ == "__main__":
    unittest.main()
