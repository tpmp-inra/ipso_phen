import os
import unittest

from ipso_phen.ipapi.ipt.ipt_hough_ellipses_detector import IptHoughEllipses
from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
from ipso_phen.ipapi.base.ipt_loose_pipeline import LoosePipeline
from ipso_phen.ipapi.base.ipt_abstract_analyzer import IptBaseAnalyzer

import ipso_phen.ipapi.base.ip_common as ipc


class TestIptHoughEllipses(unittest.TestCase):
    def test_use_case(self):
        """Hough ellipses detector: Check that all use cases are allowed"""
        op = IptHoughEllipses()
        for uc in op.use_case:
            self.assertIn(
                uc, list(ipc.tool_family_hints.keys()), f"Unknown use case {uc}"
            )

    def test_docstring(self):
        """Hough ellipses detector: Test that class process_wrapper method has docstring"""
        op = IptHoughEllipses()
        if not op.is_wip:
            self.assertIsNotNone(
                op.process_wrapper.__doc__,
                "Missing docstring for Hough ellipses detector",
            )
