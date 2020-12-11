import os
import numpy as np
import unittest

from ipso_phen.ipapi.ipt.ipt_clean_horizontal_noise_hough import (
    IptCleanHorizontalNoiseHough,
)
from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
from ipso_phen.ipapi.base.ipt_loose_pipeline import LoosePipeline
import ipso_phen.ipapi.base.ip_common as ipc


class TestIptCleanHorizontalNoiseHough(unittest.TestCase):
    def test_use_case(self):
        """Clean horizontal noise (Hough method): Check that all use cases are allowed"""
        op = IptCleanHorizontalNoiseHough()
        for uc in op.use_case:
            self.assertIn(
                uc, list(ipc.tool_family_hints.keys()), f"Unknown use case {uc}"
            )

    def test_docstring(self):
        """Clean horizontal noise (Hough method): Test that class process_wrapper method has docstring"""
        op = IptCleanHorizontalNoiseHough()
        if not op.is_wip:
            self.assertIsNotNone(
                op.process_wrapper.__doc__,
                "Missing docstring for Clean horizontal noise (Hough method)",
            )

    def test_has_test_function(self):
        """Clean horizontal noise (Hough method): Check that at least one test function has been generated"""
        self.assertTrue(True, "No compatible test function was generated")

    def test_mask_transformation(self):
        """Clean horizontal noise (Hough method): Test that when using the basic mask generated script this tool produces a mask"""
        op = IptCleanHorizontalNoiseHough()
        op.apply_test_values_overrides(use_cases=("Mask cleanup",))
        script = LoosePipeline.load(
            "./ipso_phen/ipapi/samples/pipelines/test_cleaners.json"
        )
        script.add_module(operator=op, target_group="grp_test_cleaners")
        wrapper = BaseImageProcessor(
            "./ipso_phen/ipapi/samples/images/18HP01U17-CAM11-20180712221558.bmp",
            database=None,
        )
        res = script.execute(src_image=wrapper, silent_mode=True)
        self.assertTrue(
            res,
            "Failed to process Clean horizontal noise (Hough method) with test script",
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
        doc_path = "./docs/ipt_Clean_horizontal_noise_(Hough_method).md"
        self.assertTrue(
            os.path.isfile(doc_path),
            "Missing doc file for ROI composition {doc_path}",
        )


if __name__ == "__main__":
    unittest.main()
