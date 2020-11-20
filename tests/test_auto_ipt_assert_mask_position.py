import os
import unittest

from ipso_phen.ipapi.ipt.ipt_assert_mask_position import IptAssertMaskPosition
from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
import ipso_phen.ipapi.base.ip_common as ipc


class TestIptAssertMaskPosition(unittest.TestCase):
    def test_use_case(self):
        """Check that all use cases are allowed"""
        op = IptAssertMaskPosition()
        for uc in op.use_case:
            self.assertIn(
                uc, list(ipc.tool_family_hints.keys()), f"Unknown use case {uc}"
            )

    def test_docstring(self):
        """Test that class process_wrapper method has docstring"""
        op = IptAssertMaskPosition()
        if not op.is_wip:
            self.assertIsNotNone(
                op.process_wrapper.__doc__, "Missing docstring for Assert mask position"
            )

    def test_has_test_function(self):
        """Check that at list one test function has been generated"""
        self.assertTrue(True, "No compatible test function was generated")

    def test_bool_out(self):
        """Test that tool returns a boolean"""
        op = IptAssertMaskPosition()
        op.apply_test_values_overrides(use_cases=("Assert...",))
        wrapper = BaseImageProcessor(
            "./ipso_phen/ipapi/samples/images/arabido_small.jpg"
        )
        res = op.process_wrapper(wrapper=wrapper)
        self.assertTrue(res, "Failed to process Assert mask position")
        self.assertIsInstance(
            op.result, bool, "Assert mask position must return a boolean"
        )

    def test_documentation(self):
        doc_path = "./docs/ipt_Assert_mask_position.md"
        self.assertTrue(
            os.path.isfile(doc_path),
            "Missing doc file for ROI composition {doc_path}",
        )


if __name__ == "__main__":
    unittest.main()
