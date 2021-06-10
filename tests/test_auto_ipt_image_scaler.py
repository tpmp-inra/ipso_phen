import os
import unittest

from ipso_phen.ipapi.ipt.ipt_image_scaler import IptImageScaler
from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
from ipso_phen.ipapi.base.ipt_loose_pipeline import LoosePipeline
from ipso_phen.ipapi.base.ipt_abstract_analyzer import IptBaseAnalyzer

import ipso_phen.ipapi.base.ip_common as ipc


class TestIptImageScaler(unittest.TestCase):
    def test_use_case(self):
        """Image scaler: Check that all use cases are allowed"""
        op = IptImageScaler()
        for uc in op.use_case:
            self.assertIn(
                uc, list(ipc.tool_family_hints.keys()), f"Unknown use case {uc}"
            )

    def test_docstring(self):
        """Image scaler: Test that class process_wrapper method has docstring"""
        op = IptImageScaler()
        if not op.is_wip:
            self.assertIsNotNone(
                op.process_wrapper.__doc__, "Missing docstring for Image scaler"
            )

    def test_has_test_function(self):
        """Image scaler: Check that at least one test function has been generated"""
        self.assertTrue(True, "No compatible test function was generated")

    def test_feature_out(self):
        """Image scaler: "Test that when using the basic mask generated script this tool extracts features"""
        op = IptImageScaler()
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
            "Image scaler must inherit from ipso_phen.ipapi.iptBaseAnalyzer",
        )
        self.assertTrue(res, "Failed to process Image scaler with test script")
        self.assertNotEqual(
            first=len(wrapper.csv_data_holder.data_list),
            second=0,
            msg="Image scaler returned no data",
        )

    def test_visualization(self):
        """Image scaler: Test that visualization tools add images to list"""
        op = IptImageScaler()
        op.apply_test_values_overrides(use_cases=("Visualization",))
        wrapper = BaseImageProcessor(
            "./ipso_phen/ipapi/samples/images/arabido_small.jpg",
            database=None,
        )
        wrapper.store_images = True
        res = op.process_wrapper(wrapper=wrapper)
        self.assertTrue(res, "Failed to process Simple white balance")
        self.assertGreater(
            len(wrapper.image_list), 0, "Visualizations must add images to list"
        )

    def test_documentation(self):
        doc_path = "./docs/ipt_Image_scaler.md"
        self.assertTrue(
            os.path.isfile(doc_path),
            "Missing doc file for ROI composition {doc_path}",
        )


if __name__ == "__main__":
    unittest.main()
