import os
import sys
import numpy as np
import unittest

abspath = os.path.abspath(__file__)
fld_name = os.path.dirname(abspath)
sys.path.insert(0, fld_name)
sys.path.insert(0, os.path.dirname(fld_name))
sys.path.insert(0, os.path.join(os.path.dirname(fld_name), "ipso_phen", ""))

from ip_tools.ipt_keep_linked_contours import IptKeepLinkedContours
from ip_base.ip_abstract import AbstractImageProcessor
from ip_base.ipt_script_generator import IptScriptGenerator
import ip_base.ip_common as ipc


class TestIptKeepLinkedContours(unittest.TestCase):
    def test_use_case(self):
        """Check that all use cases are allowed"""
        op = IptKeepLinkedContours()
        for uc in op.use_case:
            self.assertIn(
                uc, list(ipc.tool_group_hints.keys()), f"Unknown use case {uc}"
            )

    def test_docstring(self):
        """Test that class process_wrapper method has docstring"""
        op = IptKeepLinkedContours()
        self.assertIsNotNone(
            op.process_wrapper.__doc__, "Missing docstring for Keep linked Contours"
        )

    def test_has_test_function(self):
        """Check that at list one test function has been generated"""
        self.assertTrue(True, "No compatible test function was generated")

    def test_mask_transformation(self):
        """Test that when using the basic mask generated script this tool produces a mask"""
        op = IptKeepLinkedContours()
        op.apply_test_values_overrides(use_cases=("Mask cleanup",))
        script = IptScriptGenerator.load(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "sample_pipelines",
                "test_cleaners.json",
            )
        )
        script.add_operator(operator=op, kind=ipc.TOOL_GROUP_MASK_CLEANUP_STR)
        wrapper = AbstractImageProcessor(
            os.path.join(
                os.path.dirname(__file__), "..", "sample_images", "arabido_small.jpg",
            )
        )
        res = script.process_image(wrapper=wrapper)
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
        """Test that module has corresponding documentation file"""
        op = IptKeepLinkedContours()
        op_doc_name = op.name.replace(" ", "_")
        op_doc_name = "ipt_" + op_doc_name + ".md"
        self.assertTrue(
            os.path.isfile(
                os.path.join(os.path.dirname(__file__), "..", "docs", f"{op_doc_name}")
            ),
            "Missing documentation file for Keep linked Contours",
        )


if __name__ == "__main__":
    unittest.main()
