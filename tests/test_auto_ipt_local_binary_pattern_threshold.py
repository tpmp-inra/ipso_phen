import os
import numpy as np
import unittest

from ipso_phen.ipapi.ipt.ipt_local_binary_pattern_threshold import (
    IptLocalBinaryPatternThreshold,
)
from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
import ipso_phen.ipapi.base.ip_common as ipc


class TestIptLocalBinaryPatternThreshold(unittest.TestCase):
    def test_use_case(self):
        """Local binary pattern threshold: Check that all use cases are allowed"""
        op = IptLocalBinaryPatternThreshold()
        for uc in op.use_case:
            self.assertIn(
                uc, list(ipc.tool_family_hints.keys()), f"Unknown use case {uc}"
            )

    def test_docstring(self):
        """Local binary pattern threshold: Test that class process_wrapper method has docstring"""
        op = IptLocalBinaryPatternThreshold()
        if not op.is_wip:
            self.assertIsNotNone(
                op.process_wrapper.__doc__,
                "Missing docstring for Local binary pattern threshold",
            )
