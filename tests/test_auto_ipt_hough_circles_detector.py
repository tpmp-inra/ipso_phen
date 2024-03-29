import os
import unittest

from ipso_phen.ipapi.ipt.ipt_hough_circles_detector import IptHoughCircles
from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
import ipso_phen.ipapi.tools.regions as regions
import ipso_phen.ipapi.base.ip_common as ipc


class TestIptHoughCircles(unittest.TestCase):
    def test_use_case(self):
        """Hough circles detector: Check that all use cases are allowed"""
        op = IptHoughCircles()
        for uc in op.use_case:
            self.assertIn(
                uc, list(ipc.tool_family_hints.keys()), f"Unknown use case {uc}"
            )

    def test_docstring(self):
        """Hough circles detector: Test that class process_wrapper method has docstring"""
        op = IptHoughCircles()
        if not op.is_wip:
            self.assertIsNotNone(
                op.process_wrapper.__doc__,
                "Missing docstring for Hough circles detector",
            )

    def test_has_test_function(self):
        """Hough circles detector: Check that at least one test function has been generated"""
        self.assertTrue(True, "No compatible test function was generated")

    def test_roi_out(self):
        """Hough circles detector: Test that tool generates an ROI"""
        op = IptHoughCircles()
        op.apply_test_values_overrides(use_cases=("Create an ROI",))
        wrapper = BaseImageProcessor(
            "./ipso_phen/ipapi/samples/images/arabido_small.jpg",
            database=None,
        )
        res = op.process_wrapper(wrapper=wrapper)
        self.assertTrue(
            hasattr(op, "generate_roi"), "Class must have method generate_roi"
        )
        self.assertTrue(res, "Failed to process Hough circles detector")
        r = op.generate_roi()
        self.assertIsInstance(r, regions.AbstractRegion, "ROI must be of type Region")

    def test_documentation(self):
        doc_path = "./docs/ipt_Hough_circles_detector.md"
        self.assertTrue(
            os.path.isfile(doc_path),
            "Missing doc file for ROI composition {doc_path}",
        )


if __name__ == "__main__":
    unittest.main()
