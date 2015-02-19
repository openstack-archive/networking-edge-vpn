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
"""Brocade MLX Driver implements TELNET for
Neutron network life-cycle management of Network.
"""

import telnetlib
import re


from neutron.openstack.common import importutils
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
CER_PATTERN = "^\*{2,3} NetIron CE[S|R] \d+C \*{2,3}$"
MLX_XMR_PATTERN = "^\*{2,3} NetIron \d+-slot Chassis \*{2,3}$"
patterns = ["(.*Invalid input*)","(.*failed.*)","(^|.*Error|.*)",".*incorrect password\\.$"]
ENABLE_TERMINAL_CMD = "en\r"
CONFIGURE_TERMINAL_CMD = "conf t\r"
ROUTER_MPLS_CONFIGURATION = "router mpls\r"
CREATE_VPLS_INSTANCE = "vpls {name} {id}\r"
CONFIGURE_VLAN = "vlan {vlan_id}\r"
CONFIGURE_ETHERNET = "tagged ethe {if_name}\r"
DELETE_CONFIGURED_VLAN  = "no vlan {vlan_id}\r"


class MLXDriver():
    """TELNET interface driver for Neutron network.
    Handles life-cycle management of Neutron network 
    """

    def __init__(self):
        self.mgr = None

    def connect(self, switch):
        # Open new Telnet connection
        try:
            host = switch['address']
            username = switch['username']
            password = switch['password']
            self.mgr = telnetlib.Telnet(host=host, port=TELNET_PORT)
            self.mgr.read_until(LOGIN_USER_TOKEN, MIN_TIMEOUT)
            self.mgr.write(username + END_OF_LINE)
            self.mgr.read_until(LOGIN_PASS_TOKEN, AVG_TIMEOUT)
            self.mgr.write(password + END_OF_LINE)
            self.mgr.read_until(TELNET_TERMINAL, MAX_TIMEOUT)
        except Exception as e:
            LOG.error(_("Connect failed to switch: %s"), e)
            raise

        LOG.debug(_("Connect success to host %s:%d"), host, TELNET_PORT)
        return self.mgr

    def close_session(self):
        """Close TELNET session."""
        if self.mgr:
            self.mgr.close()
            self.mgr = None

    def enable_authentication(self, mgr, username, password):
        """To authenticate with enable authentications"""
        mgr.write(username + END_OF_LINE)
        mgr.read_until(LOGIN_PASS_TOKEN, AVG_TIMEOUT)
        mgr.write(password + END_OF_LINE)
        return mgr

    def super_user_authentication(self, mgr, password):
        """To authenticate with super user authentication"""
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

    def add_vlan_to_vpls(self, switch, mplsvpn, vlan_id):
        """Associate Vlan vpls."""
        cliCmdOutput = ''
        mgr = self.connect(switch)
        ports = [x.strip() for x in switch['ports'].split(',')]
        vplsname = mplsvpn['name']
        vpls_id = mplsvpn['vpn_id']
        self._enter_mpls_configuration(mgr)
        mgr.write(CREATE_VPLS_INSTANCE.format(name=vplsname, id=vpls_id))
        cliCmdOutput = self._read_response(mgr)
        mgr.write(CONFIGURE_VLAN.format(vlan_id=vlan_id))
        cliCmdOutput = self._read_response(mgr)
        for port in ports:
            mgr.write(CONFIGURE_ETHERNET.format(if_name=port))
            cliCmdOutput = self._read_response(mgr)
        self.close_session()

    def remove_vlan_from_vpls(self, switch, mplsvpn, vlan_id):
	"""Remove the Associated VLAN from vpls."""
        cliCmdOutput = ''
        mgr = self.connect(switch)
        vplsname = mplsvpn['name']
        vpls_id = mplsvpn['vpn_id']
        self._enter_mpls_configuration(mgr)
        mgr.write(CREATE_VPLS_INSTANCE.format(name=vplsname, id=vpls_id))
        cliCmdOutput = self._read_response(mgr)
        mgr.write(DELETE_CONFIGURED_VLAN.format(vlan_id=vlan_id))
        cliCmdOutput = self._read_response(mgr)
        self.close_session()
