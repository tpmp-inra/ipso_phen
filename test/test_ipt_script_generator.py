import os
import sys
import numpy as np
import unittest

abspath = os.path.abspath(__file__)
fld_name = os.path.dirname(abspath)
sys.path.insert(0, fld_name)
sys.path.insert(0, os.path.dirname(fld_name))
sys.path.insert(0, os.path.join(os.path.dirname(fld_name), "ipso_phen", ""))

from ip_base.ip_abstract import AbstractImageProcessor
from ip_base.ipt_strict_pipeline import IptStrictPipeline


class TestIptKeepCountoursNearRois(unittest.TestCase):

    pipeline_dir_path = os.path.join(os.path.dirname(__file__), "..", "sample_pipelines", "")

    def test_load(self):
        """Try loading all test pipelines"""
        for file_name in [
            "test_cleaners.json",
            "sample_pipeline_arabidopsis.json",
            "test_extractors.json",
            "tutorial.json",
        ]:
            script = IptStrictPipeline.load(
                os.path.join(self.pipeline_dir_path, "test_cleaners.json",)
            )
            self.assertIsInstance(script, IptStrictPipeline, msg=f'Failed to load "{file_name}"')

    def test_cleaners_pipeline(self):
        """Test cleaner's test pipeline"""
        script = IptStrictPipeline.load(
            os.path.join(self.pipeline_dir_path, "test_cleaners.json",)
        )
        wrapper = AbstractImageProcessor(
            os.path.join(os.path.dirname(__file__), "..", "sample_images", "arabido_small.jpg",)
        )
        res = script.process_image(wrapper=wrapper)
        self.assertTrue(res, "Failed to process Keep countours near ROIs with test script")
        self.assertIsInstance(wrapper.mask, np.ndarray, "Empty result for Range threshold")
        self.assertEqual(len(wrapper.mask.shape), 2, "Masks can only have one channel")
        self.assertEqual(
            np.sum(wrapper.mask[wrapper.mask != 255]), 0, "Masks values can only be 0 or 255",
        )

    def test_extractors_pipeline(self):
        """Test extractors's test pipeline"""
        script = IptStrictPipeline.load(
            os.path.join(self.pipeline_dir_path, "test_extractors.json",)
        )
        wrapper = AbstractImageProcessor(
            os.path.join(os.path.dirname(__file__), "..", "sample_images", "arabido_small.jpg",)
        )
        res = script.process_image(wrapper=wrapper)
        self.assertTrue(res, "Failed to process Keep countours near ROIs with test script")
        self.assertIsInstance(wrapper.mask, np.ndarray, "Empty result for Range threshold")
        self.assertEqual(len(wrapper.mask.shape), 2, "Masks can only have one channel")
        self.assertEqual(
            np.sum(wrapper.mask[wrapper.mask != 255]), 0, "Masks values can only be 0 or 255",
        )

    def test_sample_pipeline(self):
        """Test sample pipeline"""
        script = IptStrictPipeline.load(
            os.path.join(self.pipeline_dir_path, "sample_pipeline_arabidopsis.json",)
        )
        wrapper = AbstractImageProcessor(
            os.path.join(os.path.dirname(__file__), "..", "sample_images", "arabido_small.jpg",)
        )
        res = script.process_image(wrapper=wrapper)
        self.assertTrue(res, "Failed to process Keep countours near ROIs with test script")
        self.assertIsInstance(wrapper.mask, np.ndarray, "Empty result for Range threshold")
        self.assertEqual(len(wrapper.mask.shape), 2, "Masks can only have one channel")
        self.assertEqual(
            np.sum(wrapper.mask[wrapper.mask != 255]), 0, "Masks values can only be 0 or 255",
        )
        self.assertIsInstance(
            wrapper.csv_data_holder.data_list, dict, "Features should be a dictionnary"
        )
        self.assertGreater(len(wrapper.csv_data_holder.data_list), 0, "Non features extracted")


if __name__ == "__main__":
    unittest.main()