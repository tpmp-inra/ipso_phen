import os
import numpy as np
import unittest

from ipso_phen.ipapi.ipt.ipt_smooth_contours import IptSmoothContours
from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
from ipso_phen.ipapi.base.ipt_loose_pipeline import LoosePipeline
import ipso_phen.ipapi.base.ip_common as ipc


class TestIptSmoothContours(unittest.TestCase):
    def test_use_case(self):
        """Smooth contours: Check that all use cases are allowed"""
        op = IptSmoothContours()
        for uc in op.use_case:
            self.assertIn(
                uc, list(ipc.tool_family_hints.keys()), f"Unknown use case {uc}"
            )

    def test_docstring(self):
        """Smooth contours: Test that class process_wrapper method has docstring"""
        op = IptSmoothContours()
        if not op.is_wip:
            self.assertIsNotNone(
                op.process_wrapper.__doc__, "Missing docstring for Smooth contours"
            )
