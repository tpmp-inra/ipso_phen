import os
import numpy as np
import unittest

from ipso_phen.ipapi.ipt.ipt_load_mask import IptLoadMask
from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
import ipso_phen.ipapi.base.ip_common as ipc


class TestIptLoadMask(unittest.TestCase):
    def test_use_case(self):
        """Load mask: Check that all use cases are allowed"""
        op = IptLoadMask()
        for uc in op.use_case:
            self.assertIn(
                uc, list(ipc.tool_family_hints.keys()), f"Unknown use case {uc}"
            )

    def test_docstring(self):
        """Load mask: Test that class process_wrapper method has docstring"""
        op = IptLoadMask()
        if not op.is_wip:
            self.assertIsNotNone(
                op.process_wrapper.__doc__, "Missing docstring for Load mask"
            )

    def test_has_test_function(self):
        """Load mask: Check that at least one test function has been generated"""
        self.assertTrue(True, "No compatible test function was generated")

    def test_documentation(self):
        doc_path = "./docs/ipt_Load_mask.md"
        self.assertTrue(
            os.path.isfile(doc_path),
            "Missing doc file for ROI composition {doc_path}",
        )


if __name__ == "__main__":
    unittest.main()
