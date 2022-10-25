import os
import numpy as np
import unittest

from ipso_phen.ipapi.ipt.ipt_clean_mask_backward import IptCleanMaskBackward
from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
from ipso_phen.ipapi.base.ipt_loose_pipeline import LoosePipeline
import ipso_phen.ipapi.base.ip_common as ipc


class TestIptCleanMaskBackward(unittest.TestCase):
    def test_use_case(self):
        """Clean mask with previous mask: Check that all use cases are allowed"""
        op = IptCleanMaskBackward()
        for uc in op.use_case:
            self.assertIn(
                uc, list(ipc.tool_family_hints.keys()), f"Unknown use case {uc}"
            )

    def test_docstring(self):
        """Clean mask with previous mask: Test that class process_wrapper method has docstring"""
        op = IptCleanMaskBackward()
        if not op.is_wip:
            self.assertIsNotNone(
                op.process_wrapper.__doc__,
                "Missing docstring for Clean mask with previous mask",
            )
