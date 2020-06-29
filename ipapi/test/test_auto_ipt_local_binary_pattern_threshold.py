import os
import sys
import numpy as np
import unittest

abspath = os.path.abspath(__file__)
fld_name = os.path.dirname(abspath)
sys.path.insert(0, fld_name)
sys.path.insert(0, os.path.dirname(fld_name))
sys.path.insert(0, os.path.join(os.path.dirname(fld_name), "ipso_phen", ""))

from ipt.ipt_local_binary_pattern_threshold import IptLocalBinaryPatternThreshold
from base.ip_abstract import AbstractImageProcessor
import base.ip_common as ipc


class TestIptLocalBinaryPatternThreshold(unittest.TestCase):
    def test_use_case(self):
        """Check that all use cases are allowed"""
        op = IptLocalBinaryPatternThreshold()
        for uc in op.use_case:
            self.assertIn(uc, list(ipc.tool_group_hints.keys()), f"Unknown use case {uc}")

    def test_docstring(self):
        """Test that class process_wrapper method has docstring"""
        op = IptLocalBinaryPatternThreshold()
        if "(wip)" not in op.name.lower():
            self.assertIsNotNone(
                op.process_wrapper.__doc__,
                "Missing docstring for Local binary pattern threshold (WIP)",
            )
