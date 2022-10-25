import os
import numpy as np
import unittest

from ipso_phen.ipapi.ipt.ipt_fast_radial_symmetry_transform import (
    IptFastRadialSymmetryTransform,
)
from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
from ipso_phen.ipapi.base.ipt_loose_pipeline import LoosePipeline
from ipso_phen.ipapi.base.ipt_abstract_analyzer import IptBaseAnalyzer

import ipso_phen.ipapi.base.ip_common as ipc


class TestIptFastRadialSymmetryTransform(unittest.TestCase):
    def test_use_case(self):
        """Fast Radial Symmetry Transform: Check that all use cases are allowed"""
        op = IptFastRadialSymmetryTransform()
        for uc in op.use_case:
            self.assertIn(
                uc, list(ipc.tool_family_hints.keys()), f"Unknown use case {uc}"
            )

    def test_docstring(self):
        """Fast Radial Symmetry Transform: Test that class process_wrapper method has docstring"""
        op = IptFastRadialSymmetryTransform()
        if not op.is_wip:
            self.assertIsNotNone(
                op.process_wrapper.__doc__,
                "Missing docstring for Fast Radial Symmetry Transform",
            )
