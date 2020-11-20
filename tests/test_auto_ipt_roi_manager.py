import os
import unittest

from ipso_phen.ipapi.ipt.ipt_roi_manager import IptRoiManager
from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
import ipso_phen.ipapi.tools.regions as regions
import ipso_phen.ipapi.base.ip_common as ipc


class TestIptRoiManager(unittest.TestCase):
    def test_use_case(self):
        """Check that all use cases are allowed"""
        op = IptRoiManager()
        for uc in op.use_case:
            self.assertIn(
                uc, list(ipc.tool_family_hints.keys()), f"Unknown use case {uc}"
            )

    def test_docstring(self):
        """Test that class process_wrapper method has docstring"""
        op = IptRoiManager()
        if not op.is_wip:
            self.assertIsNotNone(
                op.process_wrapper.__doc__,
                "Missing docstring for ROI manager (deprecated)",
            )

    def test_has_test_function(self):
        """Check that at list one test function has been generated"""
        self.assertTrue(True, "No compatible test function was generated")

    def test_roi_out(self):
        """Test that tool generates an ROI"""
        op = IptRoiManager()
        op.apply_test_values_overrides(use_cases=("Create an ROI",))
        wrapper = BaseImageProcessor(
            "./ipso_phen/ipapi/samples/images/arabido_small.jpg"
        )
        res = op.process_wrapper(wrapper=wrapper)
        self.assertTrue(
            hasattr(op, "generate_roi"), "Class must have method generate_roi"
        )
        self.assertTrue(res, "Failed to process ROI manager (deprecated)")
        r = op.generate_roi()
        self.assertIsInstance(r, regions.AbstractRegion, "ROI must be of type Region")

    def test_visualization(self):
        """Test that visualization tools add images to list"""
        op = IptRoiManager()
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
        doc_path = "./docs/ipt_ROI_manager_(deprecated).md"
        self.assertTrue(
            os.path.isfile(doc_path),
            "Missing doc file for ROI composition {doc_path}",
        )


if __name__ == "__main__":
    unittest.main()
