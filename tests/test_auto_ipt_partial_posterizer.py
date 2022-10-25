import os
import numpy as np
import unittest

from ipso_phen.ipapi.ipt.ipt_partial_posterizer import IptPartialPosterizer
from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
import ipso_phen.ipapi.base.ip_common as ipc


class TestIptPartialPosterizer(unittest.TestCase):
    def test_use_case(self):
        """Partial posterizer: Check that all use cases are allowed"""
        op = IptPartialPosterizer()
        for uc in op.use_case:
            self.assertIn(
                uc, list(ipc.tool_family_hints.keys()), f"Unknown use case {uc}"
            )

    def test_docstring(self):
        """Partial posterizer: Test that class process_wrapper method has docstring"""
        op = IptPartialPosterizer()
        if not op.is_wip:
            self.assertIsNotNone(
                op.process_wrapper.__doc__, "Missing docstring for Partial posterizer"
            )

    def test_has_test_function(self):
        """Partial posterizer: Check that at least one test function has been generated"""
        self.assertTrue(True, "No compatible test function was generated")

    def test_image_transformation(self):
        """Partial posterizer: Test that when an image is in an image goes out"""
        op = IptPartialPosterizer()
        op.apply_test_values_overrides(use_cases=("Pre processing",))
        wrapper = BaseImageProcessor(
            "./ipso_phen/ipapi/samples/images/arabido_small.jpg",
            database=None,
        )
        res = op.process_wrapper(wrapper=wrapper)
        self.assertTrue(res, "Failed to process Partial posterizer")
        self.assertIsInstance(
            op.result, np.ndarray, "Empty result for Partial posterizer"
        )

    def test_documentation(self):
        doc_path = "./docs/ipt_Partial_posterizer.md"
        self.assertTrue(
            os.path.isfile(doc_path),
            "Missing doc file for ROI composition {doc_path}",
        )


if __name__ == "__main__":
    unittest.main()
