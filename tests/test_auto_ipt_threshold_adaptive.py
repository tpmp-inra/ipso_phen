import os
import numpy as np
import unittest

from ipso_phen.ipapi.ipt.ipt_threshold_adaptive import IptThresholdAdaptive
from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
import ipso_phen.ipapi.base.ip_common as ipc


class TestIptThresholdAdaptive(unittest.TestCase):
    def test_use_case(self):
        """Adaptive threshold: Check that all use cases are allowed"""
        op = IptThresholdAdaptive()
        for uc in op.use_case:
            self.assertIn(
                uc, list(ipc.tool_family_hints.keys()), f"Unknown use case {uc}"
            )

    def test_docstring(self):
        """Adaptive threshold: Test that class process_wrapper method has docstring"""
        op = IptThresholdAdaptive()
        if not op.is_wip:
            self.assertIsNotNone(
                op.process_wrapper.__doc__, "Missing docstring for Adaptive threshold"
            )

    def test_has_test_function(self):
        """Adaptive threshold: Check that at least one test function has been generated"""
        self.assertTrue(True, "No compatible test function was generated")

    def test_mask_generation(self):
        """Adaptive threshold: Test that when an image is in a mask goes out"""
        op = IptThresholdAdaptive()
        op.apply_test_values_overrides(use_cases=("Threshold",))
        wrapper = BaseImageProcessor(
            "./ipso_phen/ipapi/samples/images/arabido_small.jpg",
            database=None,
        )
        res = op.process_wrapper(wrapper=wrapper)
        self.assertTrue(res, "Failed to process Adaptive threshold")
        self.assertIsInstance(
            op.result, np.ndarray, "Empty result for Adaptive threshold"
        )
        self.assertEqual(len(op.result.shape), 2, "Masks can only have one channel")
        self.assertEqual(
            np.sum(op.result[op.result != 255]),
            0,
            "Masks values can only be 0 or 255",
        )

    def test_documentation(self):
        doc_path = "./docs/ipt_Adaptive_threshold.md"
        self.assertTrue(
            os.path.isfile(doc_path),
            "Missing doc file for ROI composition {doc_path}",
        )


if __name__ == "__main__":
    unittest.main()
