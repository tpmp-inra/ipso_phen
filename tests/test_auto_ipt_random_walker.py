import os
import numpy as np
import unittest

from ipso_phen.ipapi.ipt.ipt_random_walker import IptRandomWalker
from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
import ipso_phen.ipapi.base.ip_common as ipc


class TestIptRandomWalker(unittest.TestCase):
    def test_use_case(self):
        """Random Walker: Check that all use cases are allowed"""
        op = IptRandomWalker()
        for uc in op.use_case:
            self.assertIn(
                uc, list(ipc.tool_family_hints.keys()), f"Unknown use case {uc}"
            )

    def test_docstring(self):
        """Random Walker: Test that class process_wrapper method has docstring"""
        op = IptRandomWalker()
        if not op.is_wip:
            self.assertIsNotNone(
                op.process_wrapper.__doc__, "Missing docstring for Random Walker"
            )
