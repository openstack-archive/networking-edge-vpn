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
#
from neutron.db.edgevpn import edgevpn_db
from neutron.i18n import _LI
from neutron.plugins.common import constants
from neutron.services import service_base
from oslo_log import log as logging

LOG = logging.getLogger(__name__)


class EdgeVPNPlugin(edgevpn_db.EdgeVPNPluginDb):

    """Implementation of the Edge VPN Service Plugin.

    This class manages the work flow of EdgeVPN request/response.
    Most DB related works are implemented in class
    edgevpn_db.EdgeVPNPluginDb.
    """

    supported_extension_aliases = ["edgevpn", "service-type"]
    path_prefix = "/edgevpn"


class EdgeVPNDriverPlugin(EdgeVPNPlugin):

    def __init__(self):
        super(EdgeVPNDriverPlugin, self).__init__()
        # Load the service driver from neutron.conf.
        drivers, default_provider = service_base.load_drivers(
            constants.EDGEVPN, self)
        LOG.info(_LI("EdgeVPN plugin service driver: %s"), default_provider)
        self.edgevpn_driver = drivers[default_provider]

    def _get_driver(self):
        return self.edgevpn_driver

    def create_edgevpn(self, context, edgevpn):
        """Call super to create row in DB."""
        edgevpn = super(EdgeVPNDriverPlugin, self).create_edgevpn(context,
                                                                  edgevpn)
        """Get service driver."""
        driver = self._get_driver()
        """Call service driver to create edgevpn instance on device."""
        edgevpn = driver.create_edgevpn(context, edgevpn)
        (super(EdgeVPNDriverPlugin, self).
            update_edgevpn_status_and_name(context, edgevpn))
        return edgevpn

    def update_edgevpn(self, context, edgevpn_id, edgevpn):
        old_edgevpn = self.get_edgevpn(context, edgevpn_id)
        new_edgevpn = super(EdgeVPNDriverPlugin,
                            self).update_edgevpn(context, edgevpn_id, edgevpn)
        """Get service driver."""
        driver = self._get_driver()
        """Call service driver to update edgevpn instance on device."""
        edgevpn = driver.update_edgevpn(context, old_edgevpn, new_edgevpn)
        return new_edgevpn

    def delete_edgevpn(self, context, edgevpn_id):
        """Get EdgeVPN instances from DB by the given id."""
        edgevpn = self._get_edgevpn(context, edgevpn_id)
        """Get service driver."""
        driver = self._get_driver()
        """Call service driver to delete edgevpn instance on the device."""
        driver.delete_edgevpn(context, edgevpn)
        """Delete the instance from the DB."""
        super(EdgeVPNDriverPlugin, self).delete_edgevpn(context, edgevpn_id)

    def create_attachment_circuit(self, context, attachment_circuit):
        """Call super to create row in DB."""
        attachcircuit = (super(EdgeVPNDriverPlugin, self).
                         create_attachment_circuit(context,
                                                   attachment_circuit))
        return attachcircuit

    def update_attachment_circuit(self, context, attachmentcircuit_id,
                                  attachment_circuit):
        old_ac = self.get_attachment_circuit(context, attachmentcircuit_id)
        new_ac = super(EdgeVPNDriverPlugin,
                       self).update_attachment_circuit(context,
                                                       attachmentcircuit_id,
                                                       attachment_circuit)
        """Get service driver."""
        driver = self._get_driver()
        """Call service driver to update attachment circuit on the device."""
        attachment_circuit = driver.update_attachment_circuit(context,
                                                              old_ac, new_ac)
        return new_ac

    def delete_attachment_circuit(self, context, attachmentcircuit_id):
        """Get AttachmentCircuit instances from DB by the given id."""
        self._get_attachment_circuit(context, attachmentcircuit_id)
        """Delete the instance from the DB."""
        super(EdgeVPNDriverPlugin,
              self).delete_attachment_circuit(context, attachmentcircuit_id)

    def create_provider_edge(self, context, provider_edge):
        """Call super to create row in DB."""
        provideredge = super(EdgeVPNDriverPlugin,
                             self).create_provider_edge(context, provider_edge)
        return provideredge

    def delete_provider_edge(self, context, provideredge_id):
        """Get Provider Edge instances from DB by the given id."""
        self._get_provider_edge(context, provideredge_id)
        """Delete the instance from the DB."""
        super(EdgeVPNDriverPlugin,
              self).delete_provider_edge(context, provideredge_id)

    def create_mpls_tunnel(self, context, mpls_tunnel):
        """Call super to create row in DB."""
        mplstunnel = super(EdgeVPNDriverPlugin,
                           self).create_mpls_tunnel(context, mpls_tunnel)
        return mplstunnel

    def update_mpls_tunnel(self, context, mpls_tunnel_id, mpls_tunnel):
        old_mpls_tunnel = self.get_mpls_tunnel(context, mpls_tunnel_id)
        new_mpls_tunnel = super(EdgeVPNDriverPlugin, self).update_mpls_tunnel(
            context, mpls_tunnel_id, mpls_tunnel)
        """Get service driver."""
        driver = self._get_driver()
        """Call service driver to update mpls tunnel instance on device."""
        mpls_tunnel = driver.update_mpls_tunnel(context, old_mpls_tunnel,
                                                new_mpls_tunnel)
        return new_mpls_tunnel

    def delete_mpls_tunnel(self, context, mpls_tunnel_id):
        """Get MPLS Tunnel instances from DB by the given id."""
        self._get_mpls_tunnel(context, mpls_tunnel_id)
        """Delete the instance from the DB."""
        super(EdgeVPNDriverPlugin,
              self).delete_mpls_tunnel(context, mpls_tunnel_id)
