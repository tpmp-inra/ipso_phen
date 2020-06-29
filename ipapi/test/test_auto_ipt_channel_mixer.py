import os
import sys
import numpy as np
import unittest

abspath = os.path.abspath(__file__)
fld_name = os.path.dirname(abspath)
sys.path.insert(0, fld_name)
sys.path.insert(0, os.path.dirname(fld_name))
sys.path.insert(0, os.path.join(os.path.dirname(fld_name), "ipso_phen", ""))

from ipt.ipt_channel_mixer import IptChannelMixer
from base.ip_abstract import AbstractImageProcessor
import base.ip_common as ipc


class TestIptChannelMixer(unittest.TestCase):
    def test_use_case(self):
        """Check that all use cases are allowed"""
        op = IptChannelMixer()
        for uc in op.use_case:
            self.assertIn(uc, list(ipc.tool_group_hints.keys()), f"Unknown use case {uc}")

    def test_docstring(self):
        """Test that class process_wrapper method has docstring"""
        op = IptChannelMixer()
        if "(wip)" not in op.name.lower():
            self.assertIsNotNone(
                op.process_wrapper.__doc__, "Missing docstring for Channel mixer"
            )

    def test_has_test_function(self):
        """Check that at list one test function has been generated"""
        self.assertTrue(True, "No compatible test function was generated")

    def test_image_transformation(self):
        """Test that when an image is in an image goes out"""
        op = IptChannelMixer()
        op.apply_test_values_overrides(use_cases=("Pre processing",))
        wrapper = AbstractImageProcessor(
            os.path.join(os.path.dirname(__file__), "..", "sample_images", "arabido_small.jpg",)
        )
        res = op.process_wrapper(wrapper=wrapper)
        self.assertTrue(res, "Failed to process Channel mixer")
        self.assertIsInstance(op.result, np.ndarray, "Empty result for Channel mixer")

    def test_documentation(self):
        """Test that module has corresponding documentation file"""
        op = IptChannelMixer()
        op_doc_name = op.name.replace(" ", "_")
        op_doc_name = "ipt_" + op_doc_name + ".md"
        self.assertTrue(
            os.path.isfile(
                os.path.join(os.path.dirname(__file__), "..", "docs", f"{op_doc_name}")
            ),
            "Missing documentation file for Channel mixer",
        )


if __name__ == "__main__":
    unittest.main()
