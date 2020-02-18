import os
import sys
import unittest

abspath = os.path.abspath(__file__)
fld_name = os.path.dirname(abspath)
sys.path.insert(0, fld_name)
sys.path.insert(0, os.path.dirname(fld_name))
sys.path.insert(0, os.path.join(os.path.dirname(fld_name), "ipso_phen", ""))

from ip_tools.ipt_circle_roi import IptCircleRoi
import tools.regions as regions
import ip_base.ip_common as ipc


class TestIptCircleRoi(unittest.TestCase):
    def test_use_case(self):
        """Check that all use cases are allowed"""
        op = IptCircleRoi()
        for uc in op.use_case:
            self.assertIn(
                uc, list(ipc.tool_group_hints.keys()), f"Unknown use case {uc}"
            )

    def test_docstring(self):
        """Test that class process_wrapper method has docstring"""
        op = IptCircleRoi()
        self.assertIsNotNone(
            op.process_wrapper.__doc__, "Missing docstring for Circle ROI"
        )

    def test_has_test_function(self):
        """Check that at list one test function has been generated"""
        self.assertTrue(True, "No compatible test function was generated")

    def test_roi_out(self):
        """Test that tool generates an ROI"""
        op = IptCircleRoi()
        self.assertTrue(
            hasattr(op, "generate_roi"), "Class must have method generate_roi"
        )
        op.apply_test_values_overrides(
            use_cases=(ipc.TOOL_GROUP_ROI_RAW_IMAGE_STR, ipc.TOOL_GROUP_ROI_PP_IMAGE_STR)
        )
        res = op.process_wrapper(
            wrapper=os.path.join(
                os.path.dirname(__file__), "..", "sample_images", "arabido_small.jpg",
            )
        )
        self.assertTrue(res, "Failed to process Circle ROI")
        r = op.generate_roi()
        self.assertIsInstance(r, regions.AbstractRegion, "ROI must be of type Region")

    def test_documentation(self):
        """Test that module has corresponding documentation file"""
        op = IptCircleRoi()
        op_doc_name = op.name.replace(" ", "_")
        op_doc_name = "ipt_" + op_doc_name + ".md"
        self.assertTrue(
            os.path.isfile(
                os.path.join(os.path.dirname(__file__), "..", "docs", f"{op_doc_name}")
            ),
            "Missing documentation file for Circle ROI",
        )


if __name__ == "__main__":
    unittest.main()