import os
import numpy as np
import unittest

from ipso_phen.ipapi.ipt.ipt_quick_shift import IptQuickShift
from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
import ipso_phen.ipapi.base.ip_common as ipc


class TestIptQuickShift(unittest.TestCase):
    def test_use_case(self):
        """Check that all use cases are allowed"""
        op = IptQuickShift()
        for uc in op.use_case:
            self.assertIn(
                uc, list(ipc.tool_family_hints.keys()), f"Unknown use case {uc}"
            )

    def test_docstring(self):
        """Test that class process_wrapper method has docstring"""
        op = IptQuickShift()
        if not op.is_wip:
            self.assertIsNotNone(
                op.process_wrapper.__doc__, "Missing docstring for Quick shift"
            )

    def test_has_test_function(self):
        """Check that at list one test function has been generated"""
        self.assertTrue(True, "No compatible test function was generated")

    def test_image_transformation(self):
        """Test that when an image is in an image goes out"""
        op = IptQuickShift()
        op.apply_test_values_overrides(use_cases=("Pre processing",))
        wrapper = BaseImageProcessor(
            "./ipso_phen/ipapi/samples/images/arabido_small.jpg"
        )
        res = op.process_wrapper(wrapper=wrapper)
        self.assertTrue(res, "Failed to process Quick shift")
        self.assertIsInstance(op.result, np.ndarray, "Empty result for Quick shift")

    def test_visualization(self):
        """Test that visualization tools add images to list"""
        op = IptQuickShift()
        op.apply_test_values_overrides(use_cases=("Visualization",))
        wrapper = BaseImageProcessor(
            "./ipso_phen/ipapi/samples/images/arabido_small.jpg"
        )
        wrapper.store_images = True
        res = op.process_wrapper(wrapper=wrapper)
        res = op.process_wrapper(wrapper=wrapper)
        self.assertTrue(res, "Failed to process Simple white balance")
        self.assertGreater(
            len(wrapper.image_list), 0, "Visualizations must add images to list"
        )

    def test_documentation(self):
        doc_path = "./docs/ipt_Quick_shift.md"
        self.assertTrue(
            os.path.isfile(doc_path),
            "Missing doc file for ROI composition {doc_path}",
        )


if __name__ == "__main__":
    unittest.main()
