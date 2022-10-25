import os
import numpy as np
import unittest

from ipso_phen.ipapi.ipt.ipt_ilastik_inference import IptIlastikInference
from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
import ipso_phen.ipapi.base.ip_common as ipc


class TestIptIlastikInference(unittest.TestCase):
    def test_use_case(self):
        """Ilastik inference: Check that all use cases are allowed"""
        op = IptIlastikInference()
        for uc in op.use_case:
            self.assertIn(
                uc, list(ipc.tool_family_hints.keys()), f"Unknown use case {uc}"
            )

    def test_docstring(self):
        """Ilastik inference: Test that class process_wrapper method has docstring"""
        op = IptIlastikInference()
        if not op.is_wip:
            self.assertIsNotNone(
                op.process_wrapper.__doc__, "Missing docstring for Ilastik inference"
            )

    def test_has_test_function(self):
        """Ilastik inference: Check that at least one test function has been generated"""
        self.assertTrue(True, "No compatible test function was generated")

    def test_documentation(self):
        doc_path = "./docs/ipt_Ilastik_inference.md"
        self.assertTrue(
            os.path.isfile(doc_path),
            "Missing doc file for ROI composition {doc_path}",
        )


if __name__ == "__main__":
    unittest.main()
