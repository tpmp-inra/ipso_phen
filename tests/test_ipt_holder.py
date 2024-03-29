import unittest
import os
import glob
import sys

abspath = os.path.abspath(__file__)
fld_name = os.path.dirname(abspath)
sys.path.insert(0, os.getcwd())
sys.path.insert(0, fld_name)
sys.path.insert(0, os.path.dirname(fld_name))
sys.path.insert(0, os.path.join(os.path.dirname(fld_name), "ipso_phen", ""))

from ipso_phen.ipapi.tools.common_functions import get_module_classes
from ipso_phen.ipapi.base.ipt_abstract import IptBase
from ipso_phen.ipapi import ipt

# Check PlantCV
try:
    from plantcv import plantcv
except Exception as e:
    allow_pcv = False
else:
    allow_pcv = True


class TestIptHolder(unittest.TestCase):
    def test_tools_folder(self):
        """IPT Holder: Check that tools folder is present"""
        print(__file__)
        tool_fld = os.path.join(
            os.path.dirname(__file__),
            "..",
            "ipso_phen",
            "ipapi",
            "ipt",
            "",
        )
        self.assertTrue(
            os.path.isdir(tool_fld),
            f"Missing root ip tools folder '{tool_fld}'",
        )

    def test_objects(self):
        """IPT Holder: Check objects are created"""
        for cls in get_module_classes(
            package=ipt, class_inherits_from=IptBase, remove_abstract=True
        ):
            self.assertIsInstance(
                cls(),
                cls=cls,
                msg=f"Failed to create ipt of type {cls.__name__}",
            )

    def test_script_files(self):
        """
        IPT Holder: Check that for every file in ipt, there's a corresponding file in the test's folder.
        WIP tools will be excluded.
        """

        test_folder = os.path.dirname(__file__)

        script_list = [
            f
            for f in glob.glob(
                os.path.join(os.path.join("..", test_folder, "ipt", ""), "ipt_*.py"),
                recursive=True,
            )
            if allow_pcv or "pcv" not in f
        ]
        for script_ in script_list:
            self.assertTrue(
                os.path.isfile(
                    os.path.join(test_folder, f"test_{os.path.basename(script_)}"),
                ),
                f"Missing test script for {os.path.basename(script_)}",
            )


if __name__ == "__main__":
    unittest.main()
