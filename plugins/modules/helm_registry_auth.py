#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: © Ericsson AB 2024
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: helm_registry_auth

short_description: Helm registry authentication module

version_added: 5.1.0

author:
  - Yuriy Novostavskiy (@yurnov)

requirements:
  - "helm (https://github.com/helm/helm/releases)"

description:
  -  Helm registry authentication module allows you to login C(helm registry login) and logout C(helm registry logout) from a Helm registry.

options:
  state:
    description:
      - Desired state of the registry.
      - If set to C(present) attempt to log in to the remote registry server using the URL specified in I(host).
      - If set to C(absent) attempt to log out from the remote registry server using the URL specified in I(host).
    required: false
    default: present
    choices: ['present', 'absent']
    type: str
  host:
    description:
      - Provide a URL for accessing the registry.
    required: true
    aliases: [ registry_url ]
    type: str
  insecure:
    description:
      - Allow connections to SSL sites without certs.
    required: false
    default: false
    type: bool
  username:
    description:
      - Username for the registry.
    required: false
    type: str
    aliases: [ repo_username ]
  password:
    description:
      - Password for the registry.
    required: false
    type: str
    aliases: [ repo_password ]
  key_file:
    description:
      - Path to the client key SSL file for identify registry client using this key file.
    required: false
    type: path
  cert_file:
    description:
      - Path to the client certificate SSL file for identify registry client using this certificate file.
    required: false
    type: path
  ca_file:
    description:
      - Path to the CA certificate SSL file for verify registry server certificate.
    required: false
    type: path
  binary_path:
    description:
      - The path of a helm binary to use.
    required: false
    type: path
"""

EXAMPLES = r"""
- name: Login to remote registry
  kubernetes.core.helm_registry_auth:
    username: admin
    password: "sample_password"
    host: localhost:5000

- name: Logout from remote registry
  kubernetes.core.helm_registry_auth:
    state: absent
    host: localhost:5000
"""

RETURN = r"""
stdout:
  type: str
  description: Full `helm` command stdout, in case you want to display it or examine the event log
  returned: always
stout_lines:
  type: list
  description: Full `helm` command stdout, in case you want to display it or examine the event log
  returned: always
stderr:
  type: str
  description: Full `helm` command stderr, in case you want to display it or examine the event log. Please be note that helm binnary may print messages to stderr even if the command is successful.
  returned: always
  sample: 'Login Succeeded\n'
stderr_lines:
  type: list
  description: Full `helm` command stderr, in case you want to display it or examine the event log
  returned: always
command:
  type: str
  description: Full `helm` command executed
  returned: always
  sample: '/usr/local/bin/helm registry login oci-registry.domain.example --username=admin --password-stdin --insecure'
failed:
  type: bool
  description: Indicate if the `helm` command failed
  returned: always
  sample: false
changed:
  type: bool
  returned: always
"""

import copy
import traceback

from ansible.module_utils.basic import missing_required_lib
from ansible.module_utils.common.process import get_bin_path
from ansible_collections.kubernetes.core.plugins.module_utils.helm import (
    AnsibleHelmModule,
)
from ansible_collections.kubernetes.core.plugins.module_utils.helm_args_common import (
    HELM_AUTH_ARG_SPEC,
    HELM_AUTH_MUTUALLY_EXCLUSIVE,
)


def argument_spec():
    arg_spec = copy.deepcopy(HELM_AUTH_ARG_SPEC)
    arg_spec.update(
        dict(
            host=dict(type="str", aliases=["registry_url"], required=True),
            state=dict(
                default="present", choices=["present", "absent"], required=False
            ),
            insecure=dict(type="bool", default=False, required=False),
            username=dict(type="str", aliases=["repo_username"], required=False),
            password=dict(
                type="str", aliases=["repo_password"], no_log=True, required=False
            ),
            key_file=dict(type="path", required=False),
            cert_file=dict(type="path", required=False),
            ca_file=dict(type="path", required=False),
        )
    )
    return arg_spec


def login(
    command,
    host,
    insecure,
    username,
    password,
    key_file,
    cert_file,
    ca_file,
):
    login_command = command + " registry login " + host

    if username is not None and password is not None:
        login_command += " --username=" + username + " --password-stdin"

    if insecure:
        login_command += " --insecure"

    if key_file is not None:
        login_command += " --key-file=" + key_file

    if cert_file is not None:
        login_command += " --cert-file=" + cert_file

    if ca_file is not None:
        login_command += " --ca-file=" + ca_file

    return login_command


def logout(command, host):
    return command + " registry logout " + host


def main():
    global module

    module = AnsibleHelmModule(
        argument_spec=argument_spec(),
        required_together=[["username", "password"]],
        mutually_exclusive=HELM_AUTH_MUTUALLY_EXCLUSIVE,
        supports_check_mode=True,
    )

    changed = False

    host = module.params.get("host")
    state = module.params.get("state")
    insecure = module.params.get("insecure")
    username = module.params.get("username")
    password = module.params.get("password")
    key_file = module.params.get("key_file")
    cert_file = module.params.get("cert_file")
    ca_file = module.params.get("ca_file")

    helm_cmd = module.get_helm_binary()

    if state == "absent":
        helm_cmd = logout(helm_cmd, host)
        changed = True
    elif state == "present":
        helm_cmd = login(
            helm_cmd, host, insecure, username, password, key_file, cert_file, ca_file
        )
        changed = True

    if module.check_mode:
        module.exit_json(changed=changed)
    # This one is reduntant, but it's here for clarity
    elif not changed:
        module.exit_json(changed=False)

    rc, out, err = module.run_helm_command(helm_cmd, data=password)

    if rc != 0:
        module.fail_json(
            msg="Failure when executing Helm command. Exited {0}.\nstdout: {1}\nstderr: {2}".format(
                rc, out, err
            ),
            command=helm_cmd,
        )

    module.exit_json(changed=changed, stdout=out, stderr=err, command=helm_cmd)


if __name__ == "__main__":
    main()
