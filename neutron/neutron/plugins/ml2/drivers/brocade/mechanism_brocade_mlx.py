# Copyright 2014 Brocade Communications System, Inc.
# All rights reserved.
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
# Author:
# Angela Smith (aallen@brocade.com)


"""Implementation of Brocade MLX ML2 Mechanism driver for ML2 Plugin."""

from oslo.config import cfg

from neutron.db.mplsvpn.mplsvpn_db import MPLSVPNPluginDb as mplsvpn_db
from neutron.openstack.common import importutils
from neutron.openstack.common import log as logging
from neutron.plugins.common import constants as p_const
from neutron.plugins.ml2 import driver_api as api
from neutron.plugins.ml2.drivers.brocade.db import models as brocade_db

LOG = logging.getLogger(__name__)
MECHANISM_VERSION = 0.1
MLX_DRIVER = 'neutron.plugins.ml2.drivers.brocade.mlx.mlxdriver.MLXDriver'

ML2_BROCADE_MLX = [cfg.StrOpt('address', default='',
                          help=_('The address of the host to SSH to')),
                   cfg.StrOpt('username', default='',
                          help=_('The SSH username to use')),
                   cfg.StrOpt('password', default='', secret=True,
                          help=_('The SSH password to use')),
                   cfg.StrOpt('uplink_ports', default='',
                          help=_('The uplink ports to tag')),
                   cfg.StrOpt('cluster_peer_address', default='',
                          help=_('The MCT cluster peer address to SSH to')),
                   cfg.StrOpt('cluster_peer_username', default='',
                          help=_('The SSH username to use')),
                   cfg.StrOpt('cluster_peer_password', default='', secret=True,
                          help=_('The SSH password to use')),
                   cfg.StrOpt('cluster_peer_uplink_ports', default='',
                          help=_('The uplink ports to tag'))]

cfg.CONF.register_opts(ML2_BROCADE_MLX, "ml2_brocade_mlx")


class BrocadeMechanismMLX():
    """ML2 Mechanism driver for Brocade MLX switches. This is the upper
    layer driver class that interfaces to lower layer (SSH) below.
    """

    def __init__(self):
        self._driver = None
        self._switch = None
        self._cluster_peer_switch = None
        self.initialize()

    def initialize(self):
        """Initialize the variables needed by this class."""
        self.brocade_init()

    def brocade_init(self):
        """Brocade specific initialization for this class."""

        self._switch = {'address': cfg.CONF.ml2_brocade_mlx.address,
                        'username': cfg.CONF.ml2_brocade_mlx.username,
                        'password': cfg.CONF.ml2_brocade_mlx.password,
                        'ports': cfg.CONF.ml2_brocade_mlx.uplink_ports}
        if cfg.CONF.ml2_brocade_mlx.cluster_peer_address:
            self._cluster_peer_switch = {'address': cfg.CONF.ml2_brocade_mlx.cluster_peer_address,
                                         'username': cfg.CONF.ml2_brocade_mlx.cluster_peer_username,
                                         'password': cfg.CONF.ml2_brocade_mlx.cluster_peer_password,
                                         'ports': cfg.CONF.ml2_brocade_mlx.cluster_peer_uplink_ports}
        self._driver = importutils.import_object(MLX_DRIVER)

    def create_network_precommit(self, mech_context):
        """Noop now, it is left here for future."""
        pass

    def create_network_postcommit(self, mech_context):
        """No-op."""
        pass

    def delete_network_precommit(self, mech_context):
        """No-op."""
        pass

    def delete_network_postcommit(self, mech_context):
        """No-op."""
        pass

    def update_network_precommit(self, mech_context):
        """No-op."""
        pass

    def update_network_postcommit(self, mech_context):
        """No-op."""
        pass

    def create_port_precommit(self, mech_context):
        """Add network to attachment circuit network id association."""
        port = mech_context.current
        network_id = port['network_id']
        tenant_id = port['tenant_id']
        context = mech_context._plugin_context
        attachmentcircuit = mplsvpn_db.get_attachmentcircuit_for_tenant(context, tenant_id)
        if attachmentcircuit is None:
            LOG.debug("Attachment circuit not found for tenant %s", tenant_id)
            return
        mplsvpn_db.add_network_to_attachmentcircuit(context, attachmentcircuit['id'], network_id)

    def create_port_postcommit(self, mech_context):
        """Add the VLAN to the VPLS definition on the MLX."""
        LOG.debug(_("create_port_postcommit: called"))
        port = mech_context.current
        port_id = port['id']
        network_id = port['network_id']
        tenant_id = port['tenant_id']
        segment = mech_context.bound_segment
        vlan_id = self._get_vlanid(segment)
        context = mech_context._plugin_context
        mplsvpn = mplsvpn_db.get_mplsvpn_for_tenant(self, context, tenant_id)
        if mplsvpn is None:
            LOG.debug("MPLSVPN NOT FOUND for tenant %s", tenant_id)
            return
        try:
            self._driver.add_vlan_to_vpls(self._switch, mplsvpn, vlan_id)
            if self._cluster_peer_switch:
                self._driver.add_vlan_to_vpls(self._cluster_peer_switch, mplsvpn, vlan_id)
        except Exception:
            LOG.exception(
                 _("Brocade MLX driver: failed to add vlan to vpls %s")
                 % vlan_id)
            raise Exception(
                _("Brocade switch exception: create_port_postcommit failed"))

        LOG.info(
            _("created port (postcommit): port_id=%(port_id)s"
              " network_id=%(network_id)s tenant_id=%(tenant_id)s"),
            {'port_id': port_id,
             'network_id': network_id, 'tenant_id': tenant_id})

    def delete_port_precommit(self, mech_context):
        """Remove network from attachment circuit network id association."""
        port = mech_context.current
        network_id = port['network_id']
        tenant_id = port['tenant_id']
        context = mech_context._plugin_context
        ports = mplsvpn_db.get_network_ports(self, context, network_id)
        LOG.debug("ports in network %s", len(ports))
        if len(ports) == 1:
            attachmentcircuit = mplsvpn_db.get_attachmentcircuit_for_tenant(context, tenant_id)
            if attachmentcircuit is None:
                LOG.debug("Attachment circuit not found for tenant %s", tenant_id)
                return
            mplsvpn_db.remove_network_from_attachmentcircuit(context, attachmentcircuit['id'], network_id)

    def delete_port_postcommit(self, mech_context):
        """Remove the VLAN from the VPLS definition if this is the last port in the network."""
        LOG.debug(_("delete_port_postcommit: called"))
        port = mech_context.current
        port_id = port['id']
        network_id = port['network_id']
        context = mech_context._plugin_context
        ports = mplsvpn_db.get_network_ports(self, context, network_id)
        if len(ports) == 0:
            tenant_id = port['tenant_id']
            segment = mech_context.bound_segment
            vlan_id = self._get_vlanid(segment)
            mplsvpn = mplsvpn_db.get_mplsvpn_for_tenant(self, context, tenant_id)
            if mplsvpn is None:
                LOG.debug("MPLSVPN NOT FOUND for tenant %s", tenant_id)
                return
            try:
                self._driver.remove_vlan_from_vpls(self._switch, mplsvpn, vlan_id)
                if self._cluster_peer_switch:
                    self._driver.remove_vlan_from_vpls(self._cluster_peer_switch, mplsvpn, vlan_id)
            except Exception:
                LOG.exception(
                    _("Brocade MLX driver: failed to remove VLAN from VPLS %s") %
                    vlan_id)
                raise Exception(
                    _("Brocade switch exception, delete_port_postcommit failed"))

            LOG.info(
                _("delete port (postcommit): port_id=%(port_id)s"
                  " network_id=%(network_id)s tenant_id=%(tenant_id)s"),
                {'port_id': port_id,
                 'network_id': network_id, 'tenant_id': tenant_id})

    def update_port_precommit(self, mech_context):
        """Noop now, it is left here for future."""
        LOG.debug(_("update_port_precommit(self: called"))

    def update_port_postcommit(self, mech_context):
        """Noop now, it is left here for future."""
        LOG.debug(_("update_port_postcommit: called"))

    def create_subnet_precommit(self, mech_context):
        """Noop now, it is left here for future."""
        LOG.debug(_("create_subnetwork_precommit: called"))

    def create_subnet_postcommit(self, mech_context):
        """Noop now, it is left here for future."""
        LOG.debug(_("create_subnetwork_postcommit: called"))

    def delete_subnet_precommit(self, mech_context):
        """Noop now, it is left here for future."""
        LOG.debug(_("delete_subnetwork_precommit: called"))

    def delete_subnet_postcommit(self, mech_context):
        """Noop now, it is left here for future."""
        LOG.debug(_("delete_subnetwork_postcommit: called"))

    def update_subnet_precommit(self, mech_context):
        """Noop now, it is left here for future."""
        LOG.debug(_("update_subnet_precommit(self: called"))

    def update_subnet_postcommit(self, mech_context):
        """Noop now, it is left here for future."""
        LOG.debug(_("update_subnet_postcommit: called"))

    def _get_vlanid(self, segment):
        if (segment and segment[api.NETWORK_TYPE] == p_const.TYPE_VLAN):
            return segment.get(api.SEGMENTATION_ID)
