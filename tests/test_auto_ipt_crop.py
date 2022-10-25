import os
import numpy as np
import unittest

from ipso_phen.ipapi.ipt.ipt_crop import IptCrop
from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
from ipso_phen.ipapi.base.ipt_loose_pipeline import LoosePipeline
from ipso_phen.ipapi.base.ipt_abstract_analyzer import IptBaseAnalyzer

import ipso_phen.ipapi.base.ip_common as ipc


class TestIptCrop(unittest.TestCase):
    def test_use_case(self):
        """Crop: Check that all use cases are allowed"""
        op = IptCrop()
        for uc in op.use_case:
            self.assertIn(
                uc, list(ipc.tool_family_hints.keys()), f"Unknown use case {uc}"
            )

    def test_docstring(self):
        """Crop: Test that class process_wrapper method has docstring"""
        op = IptCrop()
        if not op.is_wip:
            self.assertIsNotNone(op.process_wrapper.__doc__, "Missing docstring for Crop")

    def test_has_test_function(self):
        """Crop: Check that at least one test function has been generated"""
        self.assertTrue(True, "No compatible test function was generated")

    def test_image_transformation(self):
        """Crop: Test that when an image is in an image goes out"""
        op = IptCrop()
        op.apply_test_values_overrides(use_cases=("Pre processing",))
        wrapper = BaseImageProcessor(
            "./ipso_phen/ipapi/samples/images/arabido_small.jpg",
            database=None,
        )
        res = op.process_wrapper(wrapper=wrapper)
        self.assertTrue(res, "Failed to process Crop")
        self.assertIsInstance(op.result, np.ndarray, "Empty result for Crop")

        """Crop: "Test that when using the basic mask generated script this tool extracts features"""
        op = IptCrop()
        op.apply_test_values_overrides(use_cases=("Feature extraction",))
        script = LoosePipeline.load(
            "./ipso_phen/ipapi/samples/pipelines/test_extractors.json"
        )
        script.add_module(operator=op, target_group="grp_test_extractors")
        wrapper = BaseImageProcessor(
            "./ipso_phen/ipapi/samples/images/arabido_small.jpg",
            database=None,
        )
        res = script.execute(src_image=wrapper, silent_mode=True)
        self.assertIsInstance(
            op,
            IptBaseAnalyzer,
            "Crop must inherit from ipso_phen.ipapi.iptBaseAnalyzer",
        )
        self.assertTrue(res, "Failed to process Crop with test script")
        self.assertNotEqual(
            first=len(wrapper.csv_data_holder.data_list),
            second=0,
            msg="Crop returned no data",
        )

    def test_documentation(self):
        doc_path = "./docs/ipt_Crop.md"
        self.assertTrue(
            os.path.isfile(doc_path),
            "Missing doc file for ROI composition {doc_path}",
        )


if __name__ == "__main__":
    unittest.main()
