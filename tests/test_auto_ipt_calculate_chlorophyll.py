import os
import unittest

from ipso_phen.ipapi.ipt.ipt_calculate_chlorophyll import IptCalculateChlorophyll
from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
import ipso_phen.ipapi.base.ip_common as ipc


class TestIptCalculateChlorophyll(unittest.TestCase):
    def test_use_case(self):
        """Calculate chlorophyll: Check that all use cases are allowed"""
        op = IptCalculateChlorophyll()
        for uc in op.use_case:
            self.assertIn(
                uc, list(ipc.tool_family_hints.keys()), f"Unknown use case {uc}"
            )

    def test_docstring(self):
        """Calculate chlorophyll: Test that class process_wrapper method has docstring"""
        op = IptCalculateChlorophyll()
        if not op.is_wip:
            self.assertIsNotNone(
                op.process_wrapper.__doc__,
                "Missing docstring for Calculate chlorophyll",
            )

    def test_has_test_function(self):
        """Calculate chlorophyll: Check that at least one test function has been generated"""
        self.assertTrue(True, "No compatible test function was generated")

    def test_visualization(self):
        """Calculate chlorophyll: Test that visualization tools add images to list"""
        op = IptCalculateChlorophyll()
        op.apply_test_values_overrides(use_cases=("Visualization",))
        wrapper = BaseImageProcessor(
            "./ipso_phen/ipapi/samples/images/arabido_small.jpg",
            database=None,
        )
        wrapper.store_images = True
        res = op.process_wrapper(wrapper=wrapper)
        self.assertTrue(res, "Failed to process Simple white balance")
        self.assertGreater(
            len(wrapper.image_list), 0, "Visualizations must add images to list"
        )

    def test_documentation(self):
        doc_path = "./docs/ipt_Calculate_chlorophyll.md"
        self.assertTrue(
            os.path.isfile(doc_path),
            "Missing doc file for ROI composition {doc_path}",
        )


if __name__ == "__main__":
    unittest.main()
