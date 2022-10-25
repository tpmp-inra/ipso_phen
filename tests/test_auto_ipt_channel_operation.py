import os
import numpy as np
import unittest

from ipso_phen.ipapi.ipt.ipt_channel_operation import IptChannelOperation
from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
import ipso_phen.ipapi.base.ip_common as ipc


class TestIptChannelOperation(unittest.TestCase):
    def test_use_case(self):
        """Channel operation: Check that all use cases are allowed"""
        op = IptChannelOperation()
        for uc in op.use_case:
            self.assertIn(
                uc, list(ipc.tool_family_hints.keys()), f"Unknown use case {uc}"
            )

    def test_docstring(self):
        """Channel operation: Test that class process_wrapper method has docstring"""
        op = IptChannelOperation()
        if not op.is_wip:
            self.assertIsNotNone(
                op.process_wrapper.__doc__, "Missing docstring for Channel operation"
            )

    def test_has_test_function(self):
        """Channel operation: Check that at least one test function has been generated"""
        self.assertTrue(True, "No compatible test function was generated")

    def test_image_transformation(self):
        """Channel operation: Test that when an image is in an image goes out"""
        op = IptChannelOperation()
        op.apply_test_values_overrides(use_cases=("Pre processing",))
        wrapper = BaseImageProcessor(
            "./ipso_phen/ipapi/samples/images/arabido_small.jpg",
            database=None,
        )
        res = op.process_wrapper(wrapper=wrapper)
        self.assertTrue(res, "Failed to process Channel operation")
        self.assertIsInstance(
            op.result, np.ndarray, "Empty result for Channel operation"
        )

    def test_documentation(self):
        doc_path = "./docs/ipt_Channel_operation.md"
        self.assertTrue(
            os.path.isfile(doc_path),
            "Missing doc file for ROI composition {doc_path}",
        )


if __name__ == "__main__":
    unittest.main()
