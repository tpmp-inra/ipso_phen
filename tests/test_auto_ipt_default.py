import os
import unittest

from ipso_phen.ipapi.ipt.ipt_default import IptDefault
from ipso_phen.ipapi.base.ip_abstract import BaseImageProcessor
import ipso_phen.ipapi.base.ip_common as ipc


class TestIptDefault(unittest.TestCase):
    def test_use_case(self):
        """Default process: Check that all use cases are allowed"""
        op = IptDefault()
        for uc in op.use_case:
            self.assertIn(
                uc, list(ipc.tool_family_hints.keys()), f"Unknown use case {uc}"
            )

    def test_docstring(self):
        """Default process: Test that class process_wrapper method has docstring"""
        op = IptDefault()
        if not op.is_wip:
            self.assertIsNotNone(
                op.process_wrapper.__doc__, "Missing docstring for Default process"
            )
