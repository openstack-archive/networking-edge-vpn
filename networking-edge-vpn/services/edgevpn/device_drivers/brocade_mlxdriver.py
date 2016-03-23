#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
"""Brocade MPLS Driver implements TELNET for
Neutron network life-cycle management of VPLS.
"""

import re
import telnetlib

from neutron.openstack.common import log as logging


LOG = logging.getLogger(__name__)
TELNET_PORT = 23
END_OF_LINE = "\r"
TELNET_TERMINAL = ">"
CONFIGURE_TERMINAL = "#"
MIN_TIMEOUT = 2
AVG_TIMEOUT = 4
MAX_TIMEOUT = 8
LOGIN_USER_TOKEN = "Name:"
LOGIN_PASS_TOKEN = "Password:"
PATTERN_EN_AUTH = '.*\\r\\n.*Name\\:$'
SUPER_USER_AUTH = '^Password\\:$'
AUTH_FAILED = '.*incorrect password\\.$'
FDP_INFO = '^(info\\s*\\-\\s*FDP.*)'
CER_PATTERN = "^\*{2,3} NetIron CE[S|R] \d+C \*{2,3}$"
MLX_XMR_PATTERN = "^\*{2,3} NetIron \d+-slot Chassis \*{2,3}$"
patterns = ["(.*Invalid input*)", "(.*failed.*)", "(^|.*Error|.*)"]
ENABLE_TERMINAL_CMD = "en\r"
CONFIGURE_TERMINAL_CMD = "conf t\r"
ROUTER_MPLS_CONFIGURATION = "router mpls\r"
CREATE_VPLS_INSTANCE = "vpls {name} {id}\r"
AUTO_DISCOVER_LOAD_BALANCE = "auto-discovery load-balance\r"
ACTIVATE_PW_REDUNDANCY = "vpls-pw-redundancy-active\r"
CLUSTER_PEER = "cluster-peer {peer_ip}\r"
ENABLE_VC_MODE_TAGGED = "vc-mode tagged\r"
ENABLE_VC_MODE_RAW = "vc-mode raw-pass-through\r"
DELETE_VPLS_INSTANCE = "no vpls {name} {id}\r"
CONFIGURE_VLAN = "vlan {vlan_id}\r"
CONFIGURE_ETHERNET = "tagged ethe {if_name}\r"
DELETE_CONFIGURED_VLAN = "no vlan {vlan_id}\r"
EXIT = "exit\r"


class BrocadeMLXDriver():
    """TELNET interface driver for Neutron network."""

    def __init__(self):
        self.mgr = None

    def connect(self, switch):
        # Open new Telnet connection
        host = switch['address']
        user = switch['username']
        pwd = switch['password']
        try:
            self.mgr = telnetlib.Telnet(host=host, port=TELNET_PORT)
            self.mgr.read_until(LOGIN_USER_TOKEN, MIN_TIMEOUT)
            self.mgr.write(user + END_OF_LINE)
            self.mgr.read_until(LOGIN_PASS_TOKEN, AVG_TIMEOUT)
            self.mgr.write(pwd + END_OF_LINE)
            self.mgr.read_until(TELNET_TERMINAL, MAX_TIMEOUT)
        except Exception as e:
            LOG.error(_("Connect failed to switch: %s"), e)
            raise

        LOG.debug(_("Connect success to host %s"), {host: TELNET_PORT})
        return self.mgr

    def close_session(self):
        """Close TELNET session."""
        if self.mgr:
            self.mgr.close()
            self.mgr = None

    def validate_response(self, response):
        """Validate the response cli output to decide success/failure."""
        isFailed = None

        for index in range(len(patterns)):
            pattern = re.compile(patterns[index], re.IGNORECASE)
            if pattern.match(response):
                isFailed = "True"
                break

        if isFailed:
            raise Exception(_("Brocade MLX plugin exception, check logs"))

    def validate_terminal(self, mgr):
        """To identify the terminal mode is superuser/enable authentication."""
        requiredAuth = ''
        response = mgr.write(ENABLE_TERMINAL_CMD)
        pattern = re.compile(PATTERN_EN_AUTH, re.IGNORECASE)
        if pattern.match(response):
            requiredAuth = 'enAuth'
        pattern = re.compile(SUPER_USER_AUTH, re.IGNORECASE)
        if pattern.match(response):
            requiredAuth = 'superAuth'
        LOG.debug(_("Device in %s authentication mode"), requiredAuth)
        return requiredAuth

    def enable_authentication(self, mgr, username, password):
        """To authenticate with enable authentications."""
        mgr.write(username + END_OF_LINE)
        mgr.read_until(LOGIN_PASS_TOKEN, AVG_TIMEOUT)
        mgr.write(password + END_OF_LINE)
        return mgr

    def super_user_authentication(self, mgr, password):
        """To authenticate with super user authentication."""
        mgr.write(password + END_OF_LINE)
        return mgr

    def _read_response(self, mgr):
        return mgr.read_until(CONFIGURE_TERMINAL, MIN_TIMEOUT)

    def _enter_mpls_configuration(self, mgr):
        mgr.write(ENABLE_TERMINAL_CMD)
        self._read_response(mgr)
        mgr.write(CONFIGURE_TERMINAL_CMD)
        self._read_response(mgr)
        mgr.write(ROUTER_MPLS_CONFIGURATION)
        self._read_response(mgr)

    def configure_vpls(self, switch, vpls_id, vplsname, deviceType, vlans):
        """To create a VPLS instance with required attributes(parameters)."""
        ports = [x.strip() for x in switch['ports'].split(',')]
        mgr = self.connect(switch)
        self._enter_mpls_configuration(mgr)
        mgr.write(CREATE_VPLS_INSTANCE.format(name=vplsname, id=vpls_id))
        self._read_response(mgr)
        mgr.write(AUTO_DISCOVER_LOAD_BALANCE)
        self._read_response(mgr)
        if switch['peer_ip']:
            mgr.write(CLUSTER_PEER.format(peer_ip=switch['peer_ip']))
            self._read_response(mgr)
            mgr.write(ACTIVATE_PW_REDUNDANCY)
            self._read_response(mgr)
        if deviceType == 'MLX':
            mgr.write(ENABLE_VC_MODE_TAGGED)
        else:
            mgr.write(ENABLE_VC_MODE_RAW)
        self._read_response(mgr)
        for vlan_id in vlans:
            LOG.debug("adding vlan %s to new vpls", vlan_id)
            mgr.write(CONFIGURE_VLAN.format(vlan_id=vlan_id))
            self._read_response(mgr)
            for port in ports:
                mgr.write(CONFIGURE_ETHERNET.format(if_name=port))
                self._read_response(mgr)
            mgr.write(EXIT)
            self._read_response(mgr)
        self.close_session()

    def modify_vlans_for_vpls(self, switch, vpls_id, vplsname,
                              vlans_to_add, vlans_to_remove):
        """To modify vlans configured for existing VPLS instance."""
        ports = [x.strip() for x in switch['ports'].split(',')]
        mgr = self.connect(switch)
        self._enter_mpls_configuration(mgr)
        mgr.write(CREATE_VPLS_INSTANCE.format(name=vplsname, id=vpls_id))
        self._read_response(mgr)
        for vlan_id in vlans_to_add:
            LOG.debug("adding vlan %s", vlan_id)
            mgr.write(CONFIGURE_VLAN.format(vlan_id=vlan_id))
            self._read_response(mgr)
            for port in ports:
                mgr.write(CONFIGURE_ETHERNET.format(if_name=port))
                self._read_response(mgr)
            mgr.write(EXIT)
            self._read_response(mgr)
        for vlan_id in vlans_to_remove:
            LOG.debug("removing vlan %s", vlan_id)
            mgr.write(DELETE_CONFIGURED_VLAN.format(vlan_id=vlan_id))
            self._read_response(mgr)
        self.close_session()

    def delete_vpls(self, switch, vplsname, vpls_id):
        """To delete the vpls instance by using the vplsname and id."""
        mgr = self.connect(switch)
        self._enter_mpls_configuration(mgr)
        mgr.write(DELETE_VPLS_INSTANCE.format(name=vplsname, id=vpls_id))
        self._read_response(mgr)
        self.close_session()

    def find_hardware(self, switch):
        """To validate the hardware type."""
        self.hardwareType = "MLX"
        mgr = self.connect(switch)
        mgr.write("sh chassis " + "\n\r")
        mgr.write(" " + "\n\r")
        message = mgr.read_until("#", 8)
        response = re.split("\r\n\r\n|\r\n", message)
        chassisType = re.compile(MLX_XMR_PATTERN, re.IGNORECASE)
        cesrType = re.compile(CER_PATTERN, re.IGNORECASE)
        if chassisType.match(response[1]):
            self.hardwareType = "MLX"
        elif cesrType.match(response[1]):
            self.hardwareType = "CER"
        self.close_session()
        return self.hardwareType
