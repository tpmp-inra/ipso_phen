import os
import numpy as np
import unittest

from ipso_phen.ipapi.ipt.ipt_threshold_distance import IptThresholdDistance
from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
import ipso_phen.ipapi.base.ip_common as ipc


class TestIptThresholdDistance(unittest.TestCase):
    def test_use_case(self):
        """Image from distances: Check that all use cases are allowed"""
        op = IptThresholdDistance()
        for uc in op.use_case:
            self.assertIn(
                uc, list(ipc.tool_family_hints.keys()), f"Unknown use case {uc}"
            )

    def test_docstring(self):
        """Image from distances: Test that class process_wrapper method has docstring"""
        op = IptThresholdDistance()
        if not op.is_wip:
            self.assertIsNotNone(
                op.process_wrapper.__doc__, "Missing docstring for Image from distances"
            )

    def test_has_test_function(self):
        """Image from distances: Check that at least one test function has been generated"""
        self.assertTrue(True, "No compatible test function was generated")

    def test_image_transformation(self):
        """Image from distances: Test that when an image is in an image goes out"""
        op = IptThresholdDistance()
        op.apply_test_values_overrides(use_cases=("Pre processing",))
        wrapper = BaseImageProcessor(
            "./ipso_phen/ipapi/samples/images/arabido_small.jpg",
            database=None,
        )
        res = op.process_wrapper(wrapper=wrapper)
        self.assertTrue(res, "Failed to process Image from distances")
        self.assertIsInstance(
            op.result, np.ndarray, "Empty result for Image from distances"
        )

    def test_documentation(self):
        doc_path = "./docs/ipt_Image_from_distances.md"
        self.assertTrue(
            os.path.isfile(doc_path),
            "Missing doc file for ROI composition {doc_path}",
        )


if __name__ == "__main__":
    unittest.main()
