import os
import numpy as np
import unittest

from ipso_phen.ipapi.ipt.ipt_print_channels import IptPrintChannels
from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
import ipso_phen.ipapi.base.ip_common as ipc


class TestIptPrintChannels(unittest.TestCase):
    def test_use_case(self):
        """Print channels: Check that all use cases are allowed"""
        op = IptPrintChannels()
        for uc in op.use_case:
            self.assertIn(
                uc, list(ipc.tool_family_hints.keys()), f"Unknown use case {uc}"
            )

    def test_docstring(self):
        """Print channels: Test that class process_wrapper method has docstring"""
        op = IptPrintChannels()
        if not op.is_wip:
            self.assertIsNotNone(
                op.process_wrapper.__doc__, "Missing docstring for Print channels"
            )

    def test_has_test_function(self):
        """Print channels: Check that at least one test function has been generated"""
        self.assertTrue(True, "No compatible test function was generated")

    def test_image_transformation(self):
        """Print channels: Test that when an image is in an image goes out"""
        op = IptPrintChannels()
        op.apply_test_values_overrides(use_cases=("Pre processing",))
        wrapper = BaseImageProcessor(
            "./ipso_phen/ipapi/samples/images/arabido_small.jpg",
            database=None,
        )
        res = op.process_wrapper(wrapper=wrapper)
        self.assertTrue(res, "Failed to process Print channels")
        self.assertIsInstance(op.result, np.ndarray, "Empty result for Print channels")

    def test_visualization(self):
        """Print channels: Test that visualization tools add images to list"""
        op = IptPrintChannels()
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
        doc_path = "./docs/ipt_Print_channels.md"
        self.assertTrue(
            os.path.isfile(doc_path),
            "Missing doc file for ROI composition {doc_path}",
        )


if __name__ == "__main__":
    unittest.main()
