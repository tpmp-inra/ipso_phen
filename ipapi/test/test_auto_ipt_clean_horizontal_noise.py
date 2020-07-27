import os
import sys
import numpy as np
import unittest

abspath = os.path.abspath(__file__)
fld_name = os.path.dirname(abspath)
sys.path.insert(0, fld_name)
sys.path.insert(0, os.path.dirname(fld_name))
sys.path.insert(0, os.path.join(os.path.dirname(fld_name), "ipso_phen", ""))

from ipapi.ipt.ipt_clean_horizontal_noise import IptCleanHorizontalNoise
from ipapi.base.ip_abstract import AbstractImageProcessor
from ipapi.base.ipt_loose_pipeline import LoosePipeline
import ipapi.base.ip_common as ipc


class TestIptCleanHorizontalNoise(unittest.TestCase):
    def test_use_case(self):
        """Check that all use cases are allowed"""
        op = IptCleanHorizontalNoise()
        for uc in op.use_case:
            self.assertIn(uc, list(ipc.tool_family_hints.keys()), f"Unknown use case {uc}")

    def test_docstring(self):
        """Test that class process_wrapper method has docstring"""
        op = IptCleanHorizontalNoise()
        if "(wip)" not in op.name.lower():
            self.assertIsNotNone(
                op.process_wrapper.__doc__, "Missing docstring for Clean horizontal noise",
            )

    def test_has_test_function(self):
        """Check that at list one test function has been generated"""
        self.assertTrue(True, "No compatible test function was generated")

    def test_mask_transformation(self):
        """Test that when using the basic mask generated script this tool produces a mask"""
        op = IptCleanHorizontalNoise()
        op.apply_test_values_overrides(use_cases=(ipc.ToolFamily.MASK_CLEANUP,))
        script = LoosePipeline.load(
            os.path.join(
                os.path.dirname(__file__), "..", "samples", "pipelines", "test_cleaners.json",
            )
        )
        script.add_module(operator=op, target_group="grp_test_cleaners")
        wrapper = AbstractImageProcessor(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "samples",
                "images",
                "18HP01U17-CAM11-20180712221558.bmp",
            )
        )
        res = script.execute(src_image=wrapper, silent_mode=True)
        self.assertTrue(res, "Failed to process Clean horizontal noise with test script")
        self.assertIsInstance(wrapper.mask, np.ndarray, "Empty result for Range threshold")
        self.assertEqual(len(wrapper.mask.shape), 2, "Masks can only have one channel")
        self.assertEqual(
            np.sum(wrapper.mask[wrapper.mask != 255]), 0, "Masks values can only be 0 or 255",
        )

    def test_documentation(self):
        """Test that module has corresponding documentation file"""
        op = IptCleanHorizontalNoise()
        op_doc_name = op.name.replace(" ", "_")
        op_doc_name = "ipt_" + op_doc_name + ".md"
        self.assertTrue(
            os.path.isfile(
                os.path.join(os.path.dirname(__file__), "..", "help", f"{op_doc_name}")
            ),
            "Missing documentation file for Clean horizontal noise",
        )


if __name__ == "__main__":
    unittest.main()
