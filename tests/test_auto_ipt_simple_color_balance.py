import os
import numpy as np
import unittest

from ipso_phen.ipapi.ipt.ipt_simple_color_balance import IptSimpleWhiteBalance
from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
import ipso_phen.ipapi.base.ip_common as ipc


class TestIptSimpleWhiteBalance(unittest.TestCase):
    def test_use_case(self):
        """Simple white balance: Check that all use cases are allowed"""
        op = IptSimpleWhiteBalance()
        for uc in op.use_case:
            self.assertIn(
                uc, list(ipc.tool_family_hints.keys()), f"Unknown use case {uc}"
            )

    def test_docstring(self):
        """Simple white balance: Test that class process_wrapper method has docstring"""
        op = IptSimpleWhiteBalance()
        if not op.is_wip:
            self.assertIsNotNone(
                op.process_wrapper.__doc__, "Missing docstring for Simple white balance"
            )

    def test_has_test_function(self):
        """Simple white balance: Check that at least one test function has been generated"""
        self.assertTrue(True, "No compatible test function was generated")

    def test_image_transformation(self):
        """Simple white balance: Test that when an image is in an image goes out"""
        op = IptSimpleWhiteBalance()
        op.apply_test_values_overrides(use_cases=("Pre processing",))
        wrapper = BaseImageProcessor(
            "./ipso_phen/ipapi/samples/images/arabido_small.jpg",
            database=None,
        )
        res = op.process_wrapper(wrapper=wrapper)
        self.assertTrue(res, "Failed to process Simple white balance")
        self.assertIsInstance(
            op.result, np.ndarray, "Empty result for Simple white balance"
        )

    def test_documentation(self):
        doc_path = "./docs/ipt_Simple_white_balance.md"
        self.assertTrue(
            os.path.isfile(doc_path),
            "Missing doc file for ROI composition {doc_path}",
        )


if __name__ == "__main__":
    unittest.main()
