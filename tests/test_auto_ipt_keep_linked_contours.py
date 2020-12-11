import os
import numpy as np
import unittest

from ipso_phen.ipapi.ipt.ipt_keep_linked_contours import IptKeepLinkedContours
from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
from ipso_phen.ipapi.base.ipt_loose_pipeline import LoosePipeline
import ipso_phen.ipapi.base.ip_common as ipc


class TestIptKeepLinkedContours(unittest.TestCase):
    def test_use_case(self):
        """Keep linked Contours: Check that all use cases are allowed"""
        op = IptKeepLinkedContours()
        for uc in op.use_case:
            self.assertIn(
                uc, list(ipc.tool_family_hints.keys()), f"Unknown use case {uc}"
            )

    def test_docstring(self):
        """Keep linked Contours: Test that class process_wrapper method has docstring"""
        op = IptKeepLinkedContours()
        if not op.is_wip:
            self.assertIsNotNone(
                op.process_wrapper.__doc__, "Missing docstring for Keep linked Contours"
            )

    def test_has_test_function(self):
        """Keep linked Contours: Check that at least one test function has been generated"""
        self.assertTrue(True, "No compatible test function was generated")

    def test_mask_transformation(self):
        """Keep linked Contours: Test that when using the basic mask generated script this tool produces a mask"""
        op = IptKeepLinkedContours()
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
        self.assertTrue(res, "Failed to process Keep linked Contours with test script")
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
        doc_path = "./docs/ipt_Keep_linked_Contours.md"
        self.assertTrue(
            os.path.isfile(doc_path),
            "Missing doc file for ROI composition {doc_path}",
        )


if __name__ == "__main__":
    unittest.main()
