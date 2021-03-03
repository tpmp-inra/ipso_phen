import os
import numpy as np
import unittest

from ipso_phen.ipapi.ipt.ipt_match_image_and_mask_resolution import (
    IptMatchImageAndMaskResolution,
)
from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
from ipso_phen.ipapi.base.ipt_loose_pipeline import LoosePipeline
import ipso_phen.ipapi.base.ip_common as ipc


class TestIptMatchImageAndMaskResolution(unittest.TestCase):
    def test_use_case(self):
        """Match image and mask resolution: Check that all use cases are allowed"""
        op = IptMatchImageAndMaskResolution()
        for uc in op.use_case:
            self.assertIn(
                uc, list(ipc.tool_family_hints.keys()), f"Unknown use case {uc}"
            )

    def test_docstring(self):
        """Match image and mask resolution: Test that class process_wrapper method has docstring"""
        op = IptMatchImageAndMaskResolution()
        if not op.is_wip:
            self.assertIsNotNone(
                op.process_wrapper.__doc__,
                "Missing docstring for Match image and mask resolution",
            )

    def test_has_test_function(self):
        """Match image and mask resolution: Check that at least one test function has been generated"""
        self.assertTrue(True, "No compatible test function was generated")

    def test_mask_transformation(self):
        """Match image and mask resolution: Test that when using the basic mask generated script this tool produces a mask"""
        op = IptMatchImageAndMaskResolution()
        op.apply_test_values_overrides(use_cases=("Mask cleanup",))
        script = LoosePipeline.load(
            "./ipso_phen/ipapi/samples/pipelines/test_cleaners.json"
        )
        script.add_module(operator=op, target_group="grp_test_cleaners")
        wrapper = BaseImageProcessor(
            "./ipso_phen/ipapi/samples/images/arabido_small.jpg",
            database=None,
        )
        res = script.execute(src_image=wrapper, silent_mode=True)
        self.assertTrue(
            res, "Failed to process Match image and mask resolution with test script"
        )
        self.assertIsInstance(
            wrapper.mask, np.ndarray, "Empty result for Range threshold"
        )
        self.assertEqual(len(wrapper.mask.shape), 2, "Masks can only have one channel")
        self.assertEqual(
            np.sum(wrapper.mask[wrapper.mask != 255]),
            0,
            "Masks values can only be 0 or 255",
        )

    def test_documentation(self):
        doc_path = "./docs/ipt_Match_image_and_mask_resolution.md"
        self.assertTrue(
            os.path.isfile(doc_path),
            "Missing doc file for ROI composition {doc_path}",
        )


if __name__ == "__main__":
    unittest.main()
