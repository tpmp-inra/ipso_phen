import os
import unittest

from ipso_phen.ipapi.ipt.ipt_heliasen_quality_control import IptHeliasenQualityControl
from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
from ipso_phen.ipapi.base.ipt_loose_pipeline import LoosePipeline
from ipso_phen.ipapi.base.ipt_abstract_analyzer import IptBaseAnalyzer

import ipso_phen.ipapi.base.ip_common as ipc


class TestIptHeliasenQualityControl(unittest.TestCase):
    def test_use_case(self):
        """Heliasen Quality Control: Check that all use cases are allowed"""
        op = IptHeliasenQualityControl()
        for uc in op.use_case:
            self.assertIn(
                uc, list(ipc.tool_family_hints.keys()), f"Unknown use case {uc}"
            )

    def test_docstring(self):
        """Heliasen Quality Control: Test that class process_wrapper method has docstring"""
        op = IptHeliasenQualityControl()
        if not op.is_wip:
            self.assertIsNotNone(
                op.process_wrapper.__doc__,
                "Missing docstring for Heliasen Quality Control",
            )
