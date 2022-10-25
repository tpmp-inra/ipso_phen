import os
import numpy as np
import unittest

from ipso_phen.ipapi.ipt.ipt_convert_image_to_mask import IptConvertImageToMask
from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
import ipso_phen.ipapi.base.ip_common as ipc


class TestIptConvertImageToMask(unittest.TestCase):
    def test_use_case(self):
        """Convert image to mask: Check that all use cases are allowed"""
        op = IptConvertImageToMask()
        for uc in op.use_case:
            self.assertIn(
                uc, list(ipc.tool_family_hints.keys()), f"Unknown use case {uc}"
            )

    def test_docstring(self):
        """Convert image to mask: Test that class process_wrapper method has docstring"""
        op = IptConvertImageToMask()
        if not op.is_wip:
            self.assertIsNotNone(
                op.process_wrapper.__doc__,
                "Missing docstring for Convert image to mask",
            )
