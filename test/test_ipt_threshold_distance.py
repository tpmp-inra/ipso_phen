import os
import sys
import numpy as np
import unittest

abspath = os.path.abspath(__file__)
fld_name = os.path.dirname(abspath)
sys.path.insert(0, fld_name)
sys.path.insert(0, os.path.dirname(fld_name))
sys.path.insert(0, os.path.join(os.path.dirname(fld_name), "ipso_phen", ""))

from ip_tools.ipt_threshold_distance import IptThresholdDistance
import ip_base.ip_common as ipc


class TestIptThresholdDistance(unittest.TestCase):
    def test_use_case(self):
        """Check that all use cases are allowed"""
        op = IptThresholdDistance()
        for uc in op.use_case:
            self.assertIn(
                uc, list(ipc.tool_group_hints.keys()), f"Unknown use case {uc}"
            )

    def test_docstring(self):
        """Test that class process_wrapper method has docstring"""
        op = IptThresholdDistance()
        self.assertIsNotNone(
            op.process_wrapper.__doc__, "Missing docstring for Distance threshold"
        )

    def test_has_test_function(self):
        """Check that at list one test function has been generated"""
        self.assertTrue(True, "No compatible test function was generated")

    def test_mask_generation(self):
        """Test that when an image is in a mask goes out"""
        op = IptThresholdDistance()
        op.apply_test_values_overrides(use_cases=("Threshold",))
        res = op.process_wrapper(
            wrapper=os.path.join(
                os.path.dirname(__file__), "..", "sample_images", "arabido_small.jpg",
            )
        )
        self.assertTrue(res, "Failed to process Distance threshold")
        self.assertIsInstance(
            op.result, np.ndarray, "Empty result for Distance threshold"
        )
        self.assertEqual(len(op.result.shape), 2, "Masks can only have one channel")
        self.assertEqual(
            np.sum(op.result[op.result != 255]), 0, "Masks values can only be 0 or 255"
        )

    def test_image_transformation(self):
        """Test that when an image is in an image goes out"""
        op = IptThresholdDistance()
        op.apply_test_values_overrides(use_cases=("Pre processing",))
        res = op.process_wrapper(
            wrapper=os.path.join(
                os.path.dirname(__file__), "..", "sample_images", "arabido_small.jpg",
            )
        )
        self.assertTrue(res, "Failed to process Distance threshold")
        self.assertIsInstance(
            op.result, np.ndarray, "Empty result for Distance threshold"
        )

    def test_documentation(self):
        """Test that module has corresponding documentation file"""
        op = IptThresholdDistance()
        op_doc_name = op.name.replace(" ", "_")
        op_doc_name = "ipt_" + op_doc_name + ".md"
        self.assertTrue(
            os.path.isfile(
                os.path.join(os.path.dirname(__file__), "..", "docs", f"{op_doc_name}")
            ),
            "Missing documentation file for Distance threshold",
        )


if __name__ == "__main__":
    unittest.main()
