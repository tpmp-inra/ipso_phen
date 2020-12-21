import os
import shutil
import unittest

from ipso_phen.ipapi.base.pipeline_launcher import launch


ROOT_PATH = os.path.join(os.path.dirname(__file__), "")


class TestPipelineProcessor(unittest.TestCase):
    def test_pipeline_processor(self):
        """Run a test pipeline on a set of images and get a valid output"""
        exp = "test_experiment"
        csv_file = "test_csv"
        dst_fld = os.path.join(ROOT_PATH, "output_files", exp)
        if os.path.isdir(dst_fld):
            shutil.rmtree(dst_fld)

        res = launch(
            script=os.path.join(ROOT_PATH, "input_files", "test_pipeline.json"),
            image_folder=os.path.join(ROOT_PATH, "input_files", ""),
            thread_count=1,
            output_folder=os.path.join(ROOT_PATH, "output_files", ""),
            csv_file_name=csv_file,
            overwrite=True,
            experiment=exp,
            report_progress=False,
        )
        self.assertEquals(
            res,
            0,
            "Failed to execute pipeline",
        )
        self.assertTrue(os.path.isfile(os.path.join(dst_fld, f"{csv_file}.csv")))


if __name__ == "__main__":
    unittest.main()