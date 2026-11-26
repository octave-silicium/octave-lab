import unittest
from tools.security_triage import workflow_findings, secret_types

class SecurityTriageTest(unittest.TestCase):
    def test_action_pins(self):
        r=workflow_findings("w.yml","permissions:\n  contents: read\n- uses: actions/checkout@v4\n- uses: x/y@"+"a"*40+"\n- uses: ./local")
        self.assertEqual(len(r["remote_uses"]),2)
        self.assertEqual(r["unpinned_remote_uses"],["actions/checkout@v4"])
        self.assertTrue(r["permission_declaration"])
        self.assertFalse(r["write_indicator"])
    def test_write_and_main(self):
        r=workflow_findings("w.yml","permissions:\n contents: write\nrun: git push origin HEAD:main")
        self.assertTrue(r["write_indicator"])
        self.assertTrue(r["push_main_indicator"])
    def test_secret_shape(self):
        self.assertEqual(secret_types(b"gh"+b"p_"+b"A"*36),{"github_classic_token"})
        self.assertEqual(secret_types(b"-----BEGIN "+b"PRIVATE KEY-----"),{"private_key_header"})
    def test_public_cert_and_placeholders(self):
        self.assertEqual(secret_types(b"-----BEGIN CERTIFICATE-----\n\${{ secrets.TOKEN }}"),set())
    def test_dependencies_and_triggers(self):
        r=workflow_findings("w.yml","on: pull_request_target\nrun: python -m pip install x")
        self.assertTrue(r["dependency_install_indicator"])
        self.assertTrue(r["pull_request_target_indicator"])
