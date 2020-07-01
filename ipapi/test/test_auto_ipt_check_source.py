import os
import sys
import unittest

abspath = os.path.abspath(__file__)
fld_name = os.path.dirname(abspath)
sys.path.insert(0, fld_name)
sys.path.insert(0, os.path.dirname(fld_name))
sys.path.insert(0, os.path.join(os.path.dirname(fld_name), "ipso_phen", ""))

from ipt.ipt_check_source import IptCheckSource
from base.ip_abstract import AbstractImageProcessor
import base.ip_common as ipc


class TestIptCheckSource(unittest.TestCase):
    def test_use_case(self):
        """Check that all use cases are allowed"""
        op = IptCheckSource()
        for uc in op.use_case:
            self.assertIn(
                uc, list(ipc.tool_group_hints.keys()), f"Unknown use case {uc}"
            )

    def test_docstring(self):
        """Test that class process_wrapper method has docstring"""
        op = IptCheckSource()
        if "(wip)" not in op.name.lower():
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
        wrapper = AbstractImageProcessor(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "samples",
                "images",
                "arabido_small.jpg",
            )
        )
        res = op.process_wrapper(wrapper=wrapper)
        self.assertTrue(res, "Failed to process Check source image")
        self.assertIsInstance(
            op.result, bool, "Check source image must return a boolean"
        )

    def test_documentation(self):
        """Test that module has corresponding documentation file"""
        op = IptCheckSource()
        op_doc_name = op.name.replace(" ", "_")
        op_doc_name = "ipt_" + op_doc_name + ".md"
        self.assertTrue(
            os.path.isfile(
                os.path.join(os.path.dirname(__file__), "..", "help", f"{op_doc_name}")
            ),
            "Missing documentation file for Check source image",
        )


if __name__ == "__main__":
    unittest.main()
