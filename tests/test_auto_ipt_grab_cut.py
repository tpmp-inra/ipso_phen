import os
import numpy as np
import unittest

from ipso_phen.ipapi.ipt.ipt_grab_cut import IptGrabCut
from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
from ipso_phen.ipapi.base.ipt_loose_pipeline import LoosePipeline
import ipso_phen.ipapi.base.ip_common as ipc


class TestIptGrabCut(unittest.TestCase):
    def test_use_case(self):
        """Grab cut: Check that all use cases are allowed"""
        op = IptGrabCut()
        for uc in op.use_case:
            self.assertIn(
                uc, list(ipc.tool_family_hints.keys()), f"Unknown use case {uc}"
            )

    def test_docstring(self):
        """Grab cut: Test that class process_wrapper method has docstring"""
        op = IptGrabCut()
        if not op.is_wip:
            self.assertIsNotNone(
                op.process_wrapper.__doc__, "Missing docstring for Grab cut"
            )
