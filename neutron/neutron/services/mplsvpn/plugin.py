#    Copyright 2014 OpenStack Foundation
#
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

from neutron.db.mplsvpn import mplsvpn_db
from neutron.openstack.common import log as logging
from neutron.plugins.common import constants
from neutron.services import service_base

LOG = logging.getLogger(__name__)


class MPLSVPNPlugin(mplsvpn_db.MPLSVPNPluginDb):

    """Implementation of the MPLS VPN Service Plugin.

    This class manages the workflow of MPLSVPN request/response.
    Most DB related works are implemented in class
    mplsvpn_db.MPLSVPNPluginDb.
    """

    supported_extension_aliases = ["mplsvpn"]


class MPLSVPNDriverPlugin(MPLSVPNPlugin):

    def __init__(self):
        super(MPLSVPNDriverPlugin, self).__init__()
        # Load the service driver from neutron.conf.
        drivers, default_provider = service_base.load_drivers(
            constants.MPLSVPN, self)
        LOG.info(_("MPLSVPN plugin service driver: %s"), default_provider)
        self.mpls_driver = drivers[default_provider]

    def _get_driver(self):
        return self.mpls_driver

    def create_mplsvpn(self, context, mplsvpn):
        """Call super to create row in DB."""
        mplsvpn = super(MPLSVPNDriverPlugin, self).create_mplsvpn(context,
                                                                  mplsvpn)
        """Get service driver."""
        driver = self._get_driver()
        """Call service driver to create mplsvpn instance on device."""
        mplsvpn = driver.create_mplsvpn(context, mplsvpn)
        (super(MPLSVPNDriverPlugin, self).
            update_mplsvpn_status_and_name(context, mplsvpn))
        return mplsvpn

    def update_mplsvpn(self, context, mplsvpn_id, mplsvpn):
        old_mplsvpn = self.get_mplsvpn(context, mplsvpn_id)
        new_mplsvpn = super(MPLSVPNDriverPlugin,
                            self).update_mplsvpn(context, mplsvpn_id, mplsvpn)
        """Get service driver."""
        driver = self._get_driver()
        """Call service driver to update mplsvpn instance on device."""
        mplsvpn = driver.update_mplsvpn(context, old_mplsvpn, new_mplsvpn)
        return new_mplsvpn

    def delete_mplsvpn(self, context, mplsvpn_id):
        """Get MPLSVPN instances from DB by the given id."""
        mplsvpn = self._get_mplsvpn(context, mplsvpn_id)
        """Get service driver."""
        driver = self._get_driver()
        """Call service driver to delete mplsvpn instance on the device."""
        driver.delete_mplsvpn(context, mplsvpn)
        """Delete the instance from the DB."""
        super(MPLSVPNDriverPlugin, self).delete_mplsvpn(context, mplsvpn_id)

    def create_attachment_circuit(self, context, attachment_circuit):
        """Call super to create row in DB."""
        attachcircuit = (super(MPLSVPNDriverPlugin, self).
                         create_attachment_circuit(context,
                                                   attachment_circuit))
        return attachcircuit

    def update_attachment_circuit(self, context, attachmentcircuit_id,
                                  attachment_circuit):
        old_ac = self.get_attachment_circuit(context, attachmentcircuit_id)
        new_ac = super(MPLSVPNDriverPlugin,
                       self).update_attachment_circuit(context,
                                                       attachmentcircuit_id,
                                                       attachment_circuit)
        driver = self._get_driver()
        attachment_circuit = driver.update_attachment_circuit(context,
                                                              old_ac, new_ac)
        return new_ac

    def delete_attachment_circuit(self, context, attachmentcircuit_id):
        """Get AttachmentCircuit instances from DB by the given id."""
        self._get_attachment_circuit(context, attachmentcircuit_id)
        """Delete the instance from the DB."""
        super(MPLSVPNDriverPlugin,
              self).delete_attachment_circuit(context, attachmentcircuit_id)

    def create_provider_edge(self, context, provider_edge):
        """Call super to create row in DB."""
        provideredge = super(MPLSVPNDriverPlugin,
                             self).create_provider_edge(context, provider_edge)
        return provideredge

    def delete_provider_edge(self, context, provideredge_id):
        """Get Provider Edge instances from DB by the given id."""
        self._get_provider_edge(context, provideredge_id)
        """Delete the instance from the DB."""
        super(MPLSVPNDriverPlugin,
              self).delete_provider_edge(context, provideredge_id)
