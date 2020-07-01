import os
import sys
import unittest

abspath = os.path.abspath(__file__)
fld_name = os.path.dirname(abspath)
sys.path.insert(0, fld_name)
sys.path.insert(0, os.path.dirname(fld_name))
sys.path.insert(0, os.path.join(os.path.dirname(fld_name), "ipso_phen", ""))

from ipt.ipt_roi_manager import IptRoiManager
from base.ip_abstract import AbstractImageProcessor
import tools.regions as regions
import base.ip_common as ipc


class TestIptRoiManager(unittest.TestCase):
    def test_use_case(self):
        """Check that all use cases are allowed"""
        op = IptRoiManager()
        for uc in op.use_case:
            self.assertIn(
                uc, list(ipc.tool_group_hints.keys()), f"Unknown use case {uc}"
            )

    def test_docstring(self):
        """Test that class process_wrapper method has docstring"""
        op = IptRoiManager()
        if "(wip)" not in op.name.lower():
            self.assertIsNotNone(
                op.process_wrapper.__doc__,
                "Missing docstring for ROI manager (deprecated)",
            )
