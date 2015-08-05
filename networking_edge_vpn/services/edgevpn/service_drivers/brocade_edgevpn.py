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

from networking_edge_vpn.db.edgevpn import edgevpn_db
from networking_edge_vpn.services.edgevpn import service_drivers

from neutron.common import exceptions as qexception
from neutron.i18n import _
from neutron.plugins.common import constants
from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import importutils

LOG = logging.getLogger(__name__)

EDGEVPN = 'edgevpn'
MLX_DRIVER = ('neutron.services.edgevpn.device_drivers.'
              'brocade_mlxdriver.BrocadeMLXDriver')
VPLS_NAME = "openstack-{vpls_id}"
mlx_opts = [cfg.StrOpt('address', default='',
                       help='The address of the MLX to configure'),
            cfg.StrOpt('username', default='',
                       help='The SSH username to use'),
            cfg.StrOpt('password', default='', secret=True,
                       help='The SSH password to use'),
            cfg.StrOpt('l2vpn_peer_ip', default='',
                       help='The MCT peer loopback address'),
            cfg.StrOpt('uplink_ports', default='',
                       help='The uplink ports to tag'),
            cfg.StrOpt('cluster_peer_address', default='',
                       help='The address of the MCT cluster peer MLX'),
            cfg.StrOpt('cluster_peer_username', default='',
                       help='The SSH username to use'),
            cfg.StrOpt('cluster_peer_password', default='', secret=True,
                       help='The SSH password to use'),
            cfg.StrOpt('cluster_peer_l2vpn_peer_ip', default='',
                       help='The MCT peer loopback address'),
            cfg.StrOpt('cluster_peer_uplink_ports', default='',
                       help='The uplink ports to tag'),
            ]

cfg.CONF.register_opts(mlx_opts, "switch_mlx")


class BrocadeEDGEVPNDriver(service_drivers.EdgeVpnDriver):
    """EDGE VPN Service Driver class for Brocade MLX."""

    def __init__(self, service_plugin):
        super(BrocadeEDGEVPNDriver, self).__init__(service_plugin)
        self._driver = importutils.import_object(MLX_DRIVER)
        mlx = cfg.CONF.switch_mlx
        self._switch = {
            'address': mlx.address,
            'username': mlx.username,
            'password': mlx.password,
            'peer_ip': mlx.l2vpn_peer_ip,
            'ports': mlx.uplink_ports,
        }
        self._cluster_peer_switch = None
        if mlx.cluster_peer_address:
            self._cluster_peer_switch = {
                'address': mlx.cluster_peer_address,
                'username': mlx.cluster_peer_username,
                'password': mlx.cluster_peer_password,
                'peer_ip': mlx.cluster_peer_l2vpn_peer_ip,
                'ports': mlx.cluster_peer_uplink_ports,
            }
        self.db = edgevpn_db.EDGEVPNPluginDb()

    @property
    def service_type(self):
        return EDGEVPN

    def create_edgevpn(self, context, edgevpn):
        """Method to create edgevpn instance on device."""
        vpls_name = edgevpn['name']
        vpls_id = edgevpn['vpn_id']
        deviceType = "MLX"
        if not vpls_name:
            vpls_name = VPLS_NAME.format(vpls_id=vpls_id)
            edgevpn['name'] = vpls_name
        if not vpls_id:
            msg = "No vpn_id specified for service, exiting"
            LOG.error(msg)
            raise EdgevpnInvalidRequest()
        with context.session.begin(subtransactions=True):
            vlans = []
            ac_id_list = edgevpn['attachment_circuits']
            for ac_id in ac_id_list:
                vlans.extend(self.db.get_vlans_for_attachment_circuit_id(
                    context,
                    ac_id))
            try:
                deviceType = self._driver.find_hardware(self._switch)
                self._driver.configure_vpls(self._switch, vpls_id,
                                            vpls_name, deviceType, vlans)
                if self._cluster_peer_switch:
                    deviceType = (self._driver.
                                  find_hardware(self._cluster_peer_switch))
                    self._driver.configure_vpls(self._cluster_peer_switch,
                                                vpls_id, vpls_name,
                                                deviceType, vlans)
            except Exception:
                raise Exception(_("Brocade plugin exception, check logs"))
            edgevpn['status'] = constants.ACTIVE
        return edgevpn

    def update_edgevpn(self, context, old_edgevpn, new_edgevpn):
        """Method to update edgevpn instance on device."""
        old_vlans = []
        new_vlans = []
        with context.session.begin(subtransactions=True):
            old_ac_id_list = old_edgevpn['attachment_circuits']
            for ac_id in old_ac_id_list:
                (old_vlans.extend(self.db.
                                  get_vlans_for_attachment_circuit_id(context,
                                                                      ac_id)))
            new_ac_id_list = new_edgevpn['attachment_circuits']
            for ac_id in new_ac_id_list:
                (new_vlans.extend(self.db.
                                  get_vlans_for_attachment_circuit_id(context,
                                                                      ac_id)))
            vlans_to_add = []
            vlans_to_remove = []
            for vlan in old_vlans:
                if vlan not in new_vlans:
                    vlans_to_remove.append(vlan)
            for vlan in new_vlans:
                if vlan not in old_vlans:
                    vlans_to_add.append(vlan)
            if vlans_to_add or vlans_to_remove:
                LOG.debug("vlans_to_add: %s, vlans_to_remove: %s",
                          vlans_to_add, vlans_to_remove)
                try:
                    self._driver.modify_vlans_for_vpls(self._switch,
                                                       new_edgevpn['vpn_id'],
                                                       new_edgevpn['name'],
                                                       vlans_to_add,
                                                       vlans_to_remove)
                    if self._cluster_peer_switch:
                        (self._driver.
                            modify_vlans_for_vpls(self._cluster_peer_switch,
                                                  new_edgevpn['vpn_id'],
                                                  new_edgevpn['name'],
                                                  vlans_to_add,
                                                  vlans_to_remove))
                except Exception:
                    raise Exception(_("Brocade plugin exception, check logs"))
        return new_edgevpn

    def delete_edgevpn(self, context, edgevpn):
        """Method to delete edgevpn instance on device."""
        with context.session.begin(subtransactions=True):
            vpn_id = edgevpn['vpn_id']
            vplsname = edgevpn['name']
            try:
                self._driver.delete_vpls(self._switch, vplsname, vpn_id)
                if self._cluster_peer_switch:
                    self._driver.delete_vpls(self._cluster_peer_switch,
                                             vplsname, vpn_id)
            except Exception:
                raise Exception(_("Brocade MLX plugin exception, check logs"))

    def update_attachment_circuit(self, context, old_ac, new_ac):
        """Method to update attachment circuit on device."""
        old_vlans = []
        new_vlans = []
        with context.session.begin(subtransactions=True):
            edgevpn = (self.db.
                       get_edgevpn_for_attachment_circuit(context,
                                                          old_ac['id']))
            if edgevpn:
                old_vlans = (self.db.
                             get_vlans_for_attachment_circuit(context, old_ac))
                new_vlans = (self.db.
                             get_vlans_for_attachment_circuit(context, new_ac))
                LOG.debug("old vlans %s, new vlans %s", old_vlans, new_vlans)
                vlans_to_add = []
                vlans_to_remove = []
                for vlan in old_vlans:
                    if vlan not in new_vlans:
                        vlans_to_remove.append(vlan)
                for vlan in new_vlans:
                    if vlan not in old_vlans:
                        vlans_to_add.append(vlan)
                if vlans_to_add or vlans_to_remove:
                    LOG.debug("vlans_to_add: %s, vlans_to_remove: %s",
                              vlans_to_add, vlans_to_remove)
                    try:
                        self._driver.modify_vlans_for_vpls(self._switch,
                                                           edgevpn['vpn_id'],
                                                           edgevpn['name'],
                                                           vlans_to_add,
                                                           vlans_to_remove)
                        if self._cluster_peer_switch:
                            (self._driver.
                                modify_vlans_for_vpls(
                                    self._cluster_peer_switch,
                                    edgevpn['vpn_id'], edgevpn['name'],
                                    vlans_to_add, vlans_to_remove))
                    except Exception:
                        raise Exception(_("plugin exception, check logs"))
        return new_ac


class EdgevpnInvalidRequest(qexception.InvalidInput):
    message = "No vpn_id specified for edgevpn service, exiting"
