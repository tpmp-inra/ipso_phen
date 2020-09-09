import os
import sys
import numpy as np
import unittest

abspath = os.path.abspath(__file__)
fld_name = os.path.dirname(abspath)
sys.path.insert(0, fld_name)
sys.path.insert(0, os.path.dirname(fld_name))
sys.path.insert(0, os.path.join(os.path.dirname(fld_name), "ipso_phen", ""))

from ipapi.base.ip_abstract import AbstractImageProcessor
from ipapi.base.ipt_loose_pipeline import LoosePipeline


class TestIptKeepCountoursNearRois(unittest.TestCase):

    pipeline_dir_path = os.path.join(
        os.path.dirname(__file__), "..", "samples", "pipelines", ""
    )

    def test_load(self):
        """Try loading all test pipelines"""
        for file_name in [
            "test_cleaners.json",
            "sample_pipeline_arabidopsis.json",
            "test_extractors.json",
            "tutorial.json",
        ]:
            pipeline = LoosePipeline.load(
                os.path.join(self.pipeline_dir_path, "test_cleaners.json",)
            )
            self.assertIsInstance(pipeline, LoosePipeline, msg=f'Failed to load "{file_name}"')

    def test_cleaners_pipeline(self):
        """Test cleaner's test pipeline"""
        pipeline = LoosePipeline.load(
            os.path.join(self.pipeline_dir_path, "test_cleaners.json",)
        )
        wrapper = AbstractImageProcessor(
            os.path.join(
                os.path.dirname(__file__), "..", "samples", "images", "arabido_small.jpg",
            )
        )
        res = pipeline.execute(src_image=wrapper, silent_mode=True)
        self.assertTrue(res, "Failed to process Keep countours near ROIs with test pipeline")
        self.assertIsInstance(wrapper.mask, np.ndarray, "Empty result for Range threshold")
        self.assertEqual(len(wrapper.mask.shape), 2, "Masks can only have one channel")
        self.assertEqual(
            np.sum(wrapper.mask[wrapper.mask != 255]), 0, "Masks values can only be 0 or 255",
        )

    def test_extractors_pipeline(self):
        """Test extractors's test pipeline"""
        pipeline = LoosePipeline.load(
            os.path.join(self.pipeline_dir_path, "test_extractors.json",)
        )
        wrapper = AbstractImageProcessor(
            os.path.join(
                os.path.dirname(__file__), "..", "samples", "images", "arabido_small.jpg",
            )
        )
        res = pipeline.execute(src_image=wrapper, silent_mode=True)
        self.assertTrue(res, "Failed to process Keep countours near ROIs with test pipeline")
        self.assertIsInstance(wrapper.mask, np.ndarray, "Empty result for Range threshold")
        self.assertEqual(len(wrapper.mask.shape), 2, "Masks can only have one channel")
        self.assertEqual(
            np.sum(wrapper.mask[wrapper.mask != 255]), 0, "Masks values can only be 0 or 255",
        )

    def test_sample_pipeline(self):
        """Test sample pipeline"""
        pipeline = LoosePipeline.load(
            os.path.join(self.pipeline_dir_path, "sample_pipeline_arabidopsis.json",)
        )
        wrapper = AbstractImageProcessor(
            os.path.join(
                os.path.dirname(__file__), "..", "samples", "images", "arabido_small.jpg",
            )
        )
        res = pipeline.execute(src_image=wrapper, silent_mode=True)
        self.assertTrue(res, "Failed to process Keep countours near ROIs with test pipeline")
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
