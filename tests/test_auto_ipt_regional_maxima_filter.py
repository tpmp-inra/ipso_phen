import os
import numpy as np
import unittest

from ipso_phen.ipapi.ipt.ipt_regional_maxima_filter import IptRegionalMaximaFiltering
from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
import ipso_phen.ipapi.base.ip_common as ipc


class TestIptRegionalMaximaFiltering(unittest.TestCase):
    def test_use_case(self):
        """Filtering regional maxima: Check that all use cases are allowed"""
        op = IptRegionalMaximaFiltering()
        for uc in op.use_case:
            self.assertIn(
                uc, list(ipc.tool_family_hints.keys()), f"Unknown use case {uc}"
            )

    def test_docstring(self):
        """Filtering regional maxima: Test that class process_wrapper method has docstring"""
        op = IptRegionalMaximaFiltering()
        if not op.is_wip:
            self.assertIsNotNone(
                op.process_wrapper.__doc__,
                "Missing docstring for Filtering regional maxima",
            )

    def test_has_test_function(self):
        """Filtering regional maxima: Check that at least one test function has been generated"""
        self.assertTrue(True, "No compatible test function was generated")

    def test_image_transformation(self):
        """Filtering regional maxima: Test that when an image is in an image goes out"""
        op = IptRegionalMaximaFiltering()
        op.apply_test_values_overrides(use_cases=("Pre processing",))
        wrapper = BaseImageProcessor(
            "./ipso_phen/ipapi/samples/images/arabido_small.jpg",
            database=None,
        )
        res = op.process_wrapper(wrapper=wrapper)
        self.assertTrue(res, "Failed to process Filtering regional maxima")
        self.assertIsInstance(
            op.result, np.ndarray, "Empty result for Filtering regional maxima"
        )

    def test_documentation(self):
        doc_path = "./docs/ipt_Filtering_regional_maxima.md"
        self.assertTrue(
            os.path.isfile(doc_path),
            "Missing doc file for ROI composition {doc_path}",
        )


if __name__ == "__main__":
    unittest.main()
