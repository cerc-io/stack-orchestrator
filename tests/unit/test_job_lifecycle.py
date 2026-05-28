# tests/unit/test_job_lifecycle.py
"""Unit tests for the job-suspend + enhanced run-job feature."""
import unittest

from stack_orchestrator.deploy.k8s.cluster_info import _is_suspended


class TestIsSuspended(unittest.TestCase):
    def test_dict_form_true(self):
        svc = {"labels": {"laconic.suspend": "true"}}
        self.assertTrue(_is_suspended(svc))

    def test_dict_form_mixed_case(self):
        svc = {"labels": {"laconic.suspend": "True"}}
        self.assertTrue(_is_suspended(svc))
        svc = {"labels": {"laconic.suspend": "TRUE"}}
        self.assertTrue(_is_suspended(svc))

    def test_dict_form_false(self):
        svc = {"labels": {"laconic.suspend": "false"}}
        self.assertFalse(_is_suspended(svc))

    def test_label_absent(self):
        svc = {"labels": {"other": "x"}}
        self.assertFalse(_is_suspended(svc))

    def test_labels_block_absent(self):
        svc = {"image": "x"}
        self.assertFalse(_is_suspended(svc))

    def test_list_form_true(self):
        svc = {"labels": ["laconic.suspend=true", "other=x"]}
        self.assertTrue(_is_suspended(svc))

    def test_list_form_absent(self):
        svc = {"labels": ["other=x"]}
        self.assertFalse(_is_suspended(svc))

    def test_labels_null(self):
        svc = {"labels": None}
        self.assertFalse(_is_suspended(svc))
