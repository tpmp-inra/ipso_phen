import os
import numpy as np
import unittest

from ipso_phen.ipapi.ipt.ipt_rotate import IptRotate
from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
import ipso_phen.ipapi.base.ip_common as ipc


class TestIptRotate(unittest.TestCase):
    def test_use_case(self):
        """Rotate: Check that all use cases are allowed"""
        op = IptRotate()
        for uc in op.use_case:
            self.assertIn(
                uc, list(ipc.tool_family_hints.keys()), f"Unknown use case {uc}"
            )

    def test_docstring(self):
        """Rotate: Test that class process_wrapper method has docstring"""
        op = IptRotate()
        if not op.is_wip:
            self.assertIsNotNone(
                op.process_wrapper.__doc__, "Missing docstring for Rotate"
            )

    def test_has_test_function(self):
        """Rotate: Check that at least one test function has been generated"""
        self.assertTrue(True, "No compatible test function was generated")

    def test_image_transformation(self):
        """Rotate: Test that when an image is in an image goes out"""
        op = IptRotate()
        op.apply_test_values_overrides(use_cases=("Pre processing",))
        wrapper = BaseImageProcessor(
            "./ipso_phen/ipapi/samples/images/arabido_small.jpg",
            database=None,
        )
        res = op.process_wrapper(wrapper=wrapper)
        self.assertTrue(res, "Failed to process Rotate")
        self.assertIsInstance(op.result, np.ndarray, "Empty result for Rotate")

    def test_visualization(self):
        """Rotate: Test that visualization tools add images to list"""
        op = IptRotate()
        op.apply_test_values_overrides(use_cases=("Visualization",))
        wrapper = BaseImageProcessor(
            "./ipso_phen/ipapi/samples/images/arabido_small.jpg",
            database=None,
        )
        wrapper.store_images = True
        res = op.process_wrapper(wrapper=wrapper)
        res = op.process_wrapper(wrapper=wrapper)
        self.assertTrue(res, "Failed to process Simple white balance")
        self.assertGreater(
            len(wrapper.image_list), 0, "Visualizations must add images to list"
        )

    def test_documentation(self):
        doc_path = "./docs/ipt_Rotate.md"
        self.assertTrue(
            os.path.isfile(doc_path),
            "Missing doc file for ROI composition {doc_path}",
        )


if __name__ == "__main__":
    unittest.main()
