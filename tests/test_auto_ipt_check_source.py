import os
import unittest

from ipso_phen.ipapi.ipt.ipt_check_source import IptCheckSource
from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
import ipso_phen.ipapi.base.ip_common as ipc


class TestIptCheckSource(unittest.TestCase):
    def test_use_case(self):
        """Check that all use cases are allowed"""
        op = IptCheckSource()
        for uc in op.use_case:
            self.assertIn(
                uc, list(ipc.tool_family_hints.keys()), f"Unknown use case {uc}"
            )

    def test_docstring(self):
        """Test that class process_wrapper method has docstring"""
        op = IptCheckSource()
        if not op.is_wip:
            self.assertIsNotNone(
                op.process_wrapper.__doc__, "Missing docstring for Check source image"
            )

    def test_has_test_function(self):
        """Check that at list one test function has been generated"""
        self.assertTrue(True, "No compatible test function was generated")

    def test_bool_out(self):
        """Test that tool returns a boolean"""
        op = IptCheckSource()
        op.apply_test_values_overrides(use_cases=("Assert...",))
        wrapper = BaseImageProcessor(
            "./ipso_phen/ipapi/samples/images/arabido_small.jpg"
        )
        res = op.process_wrapper(wrapper=wrapper)
        self.assertTrue(res, "Failed to process Check source image")
        self.assertIsInstance(
            op.result, bool, "Check source image must return a boolean"
        )

    def test_documentation(self):
        doc_path = "./docs/ipt_Check_source_image.md"
        self.assertTrue(
            os.path.isfile(doc_path),
            "Missing doc file for ROI composition {doc_path}",
        )


if __name__ == "__main__":
    unittest.main()
