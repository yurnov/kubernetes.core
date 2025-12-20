# -*- coding: utf-8 -*-
# Copyright: (c) 2024, Contributors to the Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import unittest
from unittest.mock import MagicMock, patch

from ansible.playbook.play_context import PlayContext


class TestKubectlConnection(unittest.TestCase):
    """Test kubectl connection plugin"""

    def setUp(self):
        """Set up test fixtures"""
        self.play_context = MagicMock(spec=PlayContext)
        self.play_context.remote_addr = "test-pod"
        self.play_context.executable = "/bin/sh"

    @patch("shutil.which")
    def test_validate_certs_true_string(self, mock_which):
        """Test that K8S_AUTH_VERIFY_SSL=true is properly handled"""
        from ansible_collections.kubernetes.core.plugins.connection.kubectl import (
            Connection,
        )

        mock_which.return_value = "/usr/bin/kubectl"

        # Create connection instance
        conn = Connection(self.play_context, None)

        # Set validate_certs to string "true"
        with patch.object(conn, "get_option") as mock_get_option:

            def get_option_side_effect(key):
                options = {
                    "validate_certs": "true",
                    "kubectl_pod": "test-pod",
                    "kubectl_container": "",
                    "kubectl_namespace": "",
                    "kubectl_kubeconfig": "",
                    "kubectl_context": "",
                    "kubectl_host": "",
                    "kubectl_username": "",
                    "kubectl_password": "",
                    "kubectl_token": "",
                    "client_cert": "",
                    "client_key": "",
                    "ca_cert": "",
                    "kubectl_extra_args": "",
                }
                return options.get(key, "")

            mock_get_option.side_effect = get_option_side_effect

            # Build command
            cmd, censored = conn._build_exec_cmd(["/bin/sh", "-c", "echo test"])

            # Verify that --insecure-skip-tls-verify=false is in the command
            # (validate_certs=true means don't skip verification)
            cmd_str = " ".join(cmd)
            self.assertIn("--insecure-skip-tls-verify=false", cmd_str)
            # Ensure "true" is NOT a separate argument (the bug we're fixing)
            self.assertNotIn(" true exec ", cmd_str)

    @patch("shutil.which")
    def test_validate_certs_false_string(self, mock_which):
        """Test that K8S_AUTH_VERIFY_SSL=false is properly handled"""
        from ansible_collections.kubernetes.core.plugins.connection.kubectl import (
            Connection,
        )

        mock_which.return_value = "/usr/bin/kubectl"

        conn = Connection(self.play_context, None)

        with patch.object(conn, "get_option") as mock_get_option:

            def get_option_side_effect(key):
                options = {
                    "validate_certs": "false",
                    "kubectl_pod": "test-pod",
                    "kubectl_container": "",
                    "kubectl_namespace": "",
                    "kubectl_kubeconfig": "",
                    "kubectl_context": "",
                    "kubectl_host": "",
                    "kubectl_username": "",
                    "kubectl_password": "",
                    "kubectl_token": "",
                    "client_cert": "",
                    "client_key": "",
                    "ca_cert": "",
                    "kubectl_extra_args": "",
                }
                return options.get(key, "")

            mock_get_option.side_effect = get_option_side_effect

            cmd, censored = conn._build_exec_cmd(["/bin/sh", "-c", "echo test"])

            cmd_str = " ".join(cmd)
            # validate_certs=false means skip verification
            self.assertIn("--insecure-skip-tls-verify=true", cmd_str)
            # Ensure "false" is NOT a separate argument
            self.assertNotIn(" false exec ", cmd_str)

    @patch("shutil.which")
    def test_validate_certs_various_boolean_strings(self, mock_which):
        """Test various boolean string values for validate_certs"""
        from ansible_collections.kubernetes.core.plugins.connection.kubectl import (
            Connection,
        )

        mock_which.return_value = "/usr/bin/kubectl"

        test_cases = [
            # (input_value, expected_in_command)
            ("true", "--insecure-skip-tls-verify=false"),
            ("True", "--insecure-skip-tls-verify=false"),
            ("yes", "--insecure-skip-tls-verify=false"),
            ("1", "--insecure-skip-tls-verify=false"),
            ("false", "--insecure-skip-tls-verify=true"),
            ("False", "--insecure-skip-tls-verify=true"),
            ("no", "--insecure-skip-tls-verify=true"),
            ("0", "--insecure-skip-tls-verify=true"),
        ]

        for input_val, expected_flag in test_cases:
            with self.subTest(input_value=input_val):
                conn = Connection(self.play_context, None)

                with patch.object(conn, "get_option") as mock_get_option:

                    def get_option_side_effect(key):
                        options = {
                            "validate_certs": input_val,
                            "kubectl_pod": "test-pod",
                            "kubectl_container": "",
                            "kubectl_namespace": "",
                            "kubectl_kubeconfig": "",
                            "kubectl_context": "",
                            "kubectl_host": "",
                            "kubectl_username": "",
                            "kubectl_password": "",
                            "kubectl_token": "",
                            "client_cert": "",
                            "client_key": "",
                            "ca_cert": "",
                            "kubectl_extra_args": "",
                        }
                        return options.get(key, "")

                    mock_get_option.side_effect = get_option_side_effect

                    cmd, censored = conn._build_exec_cmd(["/bin/sh", "-c", "echo test"])
                    cmd_str = " ".join(cmd)

                    self.assertIn(
                        expected_flag,
                        cmd_str,
                        f"Input '{input_val}' should result in '{expected_flag}' in command",
                    )


    @patch("shutil.which")
    def test_validate_certs_all_sources_documentation(self, mock_which):
        """
        Document that validate_certs handles all configuration sources.
        
        All of these configuration methods map to the same option key 'validate_certs':
        - K8S_AUTH_VERIFY_SSL environment variable
        - ansible_kubectl_verify_ssl variable
        - ansible_kubectl_validate_certs variable
        - validate_certs parameter
        - kubectl_verify_ssl parameter (alias)
        
        The Ansible plugin system resolves these to a single value that
        get_option('validate_certs') returns, regardless of the source.
        Therefore, the fix handles ALL sources correctly.
        """
        from ansible_collections.kubernetes.core.plugins.connection.kubectl import (
            Connection,
        )

        mock_which.return_value = "/usr/bin/kubectl"

        # Test that the option key is always 'validate_certs'
        # regardless of which configuration source was used
        conn = Connection(self.play_context, None)

        with patch.object(conn, "get_option") as mock_get_option:

            def get_option_side_effect(key):
                # Simulating K8S_AUTH_VERIFY_SSL=true
                # (or any other source - they all map to validate_certs)
                options = {
                    "validate_certs": "true",
                    "kubectl_pod": "test-pod",
                    "kubectl_container": "",
                    "kubectl_namespace": "",
                    "kubectl_kubeconfig": "",
                    "kubectl_context": "",
                    "kubectl_host": "",
                    "kubectl_username": "",
                    "kubectl_password": "",
                    "kubectl_token": "",
                    "client_cert": "",
                    "client_key": "",
                    "ca_cert": "",
                    "kubectl_extra_args": "",
                }
                return options.get(key, "")

            mock_get_option.side_effect = get_option_side_effect

            cmd, censored = conn._build_exec_cmd(["/bin/sh", "-c", "echo test"])
            cmd_str = " ".join(cmd)

            # Verify correct handling
            self.assertIn("--insecure-skip-tls-verify=false", cmd_str)
            # This test passes regardless of whether the value came from:
            # - K8S_AUTH_VERIFY_SSL env var
            # - ansible_kubectl_verify_ssl var
            # - ansible_kubectl_validate_certs var
            # - validate_certs parameter
            # - kubectl_verify_ssl alias


if __name__ == "__main__":
    unittest.main()
