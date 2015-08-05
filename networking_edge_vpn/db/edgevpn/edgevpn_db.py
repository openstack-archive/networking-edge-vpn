#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#         http://www.apache.org/licenses/LICENSE-2.0
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from networking_edge_vpn.extensions import edgevpn as edgevpnextension

from neutron.db import api as qdbapi
from neutron.db import common_db_mixin as base_db
from neutron.db import model_base
from neutron.db import models_v2
from neutron.plugins.common import constants
from neutron.plugins.ml2 import db as ml2_db
from oslo_log import log as logging
from oslo_utils import excutils
from oslo_utils import uuidutils
import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.orm import exc


LOG = logging.getLogger(__name__)


class AttachmentCircuit(model_base.BASEV2, models_v2.HasId,
                        models_v2.HasTenant):

    """Represents a Attached Circuit."""
    name = sa.Column(sa.String(255))
    network_type = sa.Column(sa.Enum("L2", "L3",
                                     name="network_type"),
                             nullable=False)
    provider_edge_id = sa.Column(sa.String(255),
                                 sa.ForeignKey('provideredges.id'),
                                 nullable=False)
    networks = orm.relationship("ACNetworkAssociation",
                                backref="attachmentcircuits",
                                cascade="all", lazy="joined")


class ACNetworkAssociation(model_base.BASEV2,
                           models_v2.HasId,
                           models_v2.HasStatusDescription):
    attachmentcircuit_id = sa.Column(sa.String(36),
                                     sa.ForeignKey("attachmentcircuits.id"),
                                     primary_key=True)
    network_id = sa.Column(sa.String(36), sa.ForeignKey("networks.id"),
                           primary_key=True)


class ACEdgeVPNAssociation(model_base.BASEV2,
                           models_v2.HasId,
                           models_v2.HasStatusDescription):
    edgevpn_id = sa.Column(sa.String(36), sa.ForeignKey("edgevpns.id"),
                           primary_key=True)
    attachmentcircuit_id = sa.Column(sa.String(36),
                                     sa.ForeignKey("attachmentcircuits.id"),
                                     primary_key=True)


class EdgeVPN(model_base.BASEV2, models_v2.HasId, models_v2.HasTenant):

    """Represents a EdgeVPN Object."""
    name = sa.Column(sa.String(255))
    status = sa.Column(sa.String(16), nullable=False)
    tunnel_type = sa.Column(sa.Enum("fullmesh", "Customized",
                                    name="lsp_tunnel_type"),
                            nullable=False)
    tunnel_backup = sa.Column(sa.Enum("frr", "Secondary",
                                      name="lsp_tunnel_backup"),
                              nullable=False)
    qos = sa.Column(sa.Enum("Gold", "Silver", "Bronze", name="qos"),
                    nullable=False)
    bandwidth = sa.Column(sa.Integer, nullable=False)
    vpn_id = sa.Column(sa.String(36), default="", nullable=False)
    attachment_circuits = orm.relationship("ACEdgeVPNAssociation",
                                           backref="edgevpns",
                                           cascade="all", lazy="joined")


class ProviderEdge(model_base.BASEV2, models_v2.HasId):

    """Represents a Provider Edge."""
    name = sa.Column(sa.String(36), nullable=False)


class EdgeVPNPluginDb(edgevpnextension.EdgeVPNPluginBase,
                      base_db.CommonDbMixin):

    """Edge VPN plugin database class using SQLAlchemy models."""

    def __init__(self):
        """Do the initialization for the edge vpn service plugin here."""
        engine = qdbapi.get_engine()
        model_base.BASEV2.metadata.create_all(engine)

    def _get_resource(self, context, model, v_id):
        try:
            r = self._get_by_id(context, model, v_id)
        except exc.NoResultFound:
            with excutils.save_and_reraise_exception():
                if issubclass(model, EdgeVPN):
                    raise edgevpnextension.EdgeVPNNotFound(edgevpn_id=v_id)
                elif issubclass(model, AttachmentCircuit):
                    raise (edgevpnextension.
                           AttachmentCircuitNotFound(
                               attachmentcircuit_id=v_id))
                elif issubclass(model, ProviderEdge):
                    raise (edgevpnextension.
                           ProviderEdgeNotFound(provideredge_id=v_id))
        return r

    def _create_attachment_circuits_dict(self, edgevpn):
        res = {edgevpn['id']: edgevpn['attachment_circuits']}
        return res

    def _modify_edgevpn_ac_associations(self, context, edgevpn_id, ac_id_list):
        with context.session.begin(subtransactions=True):
            """Get associations and filter for edgevpn."""
            assoc_qry = context.session.query(ACEdgeVPNAssociation)
            assocs = assoc_qry.filter_by(edgevpn_id=edgevpn_id).all()
            """
            For each association, delete if not in updated
            attachment circuit list for edgevpn.
            """
            for assoc in assocs:
                if assoc.attachmentcircuit_id not in ac_id_list:
                    assoc_db = self._get_resource(context,
                                                  ACEdgeVPNAssociation,
                                                  assoc.id)
                    context.session.delete(assoc_db)
            """Get edgevpn from db and new list of associations."""
            edgevpn_db = self._get_resource(context, EdgeVPN, edgevpn_id)
            assoc_qry = context.session.query(ACEdgeVPNAssociation)
            """
            For each attachment circuit in updated attachment circuit list
            verify association exists.  If not, create one.
            """
            for attachmentcircuit_id in ac_id_list:
                assoc = (assoc_qry.filter_by(edgevpn_id=edgevpn_id,
                         attachmentcircuit_id=attachmentcircuit_id).first())
                if not assoc:
                    assoc = ACEdgeVPNAssociation(
                        edgevpn_id=edgevpn_id,
                        attachmentcircuit_id=attachmentcircuit_id,
                        status=constants.ACTIVE)
                    edgevpn_db.attachment_circuits.append(assoc)

    def _create_tunneloptions_dict(self, edgevpn):
        res = {'tunnel_type': edgevpn['tunnel_type'],
               'tunnel_backup': edgevpn['tunnel_backup'],
               'qos': edgevpn['qos'],
               'bandwidth': edgevpn['bandwidth']}
        return res

    def _make_edgevpn_dict(self, edgevpn, fields=None):
        res = {'id': edgevpn['id'],
               'tenant_id': edgevpn['tenant_id'],
               'name': edgevpn['name'],
               'vpn_id': edgevpn['vpn_id'],
               'tunnel_options': self._create_tunneloptions_dict(edgevpn),
               'status': edgevpn['status']}
        res['attachment_circuits'] = ([n['attachmentcircuit_id']
                                       for n in edgevpn.attachment_circuits])
        return self._fields(res, fields)

    def create_edgevpn(self, context, edgevpn):
        edgevpns = edgevpn['edgevpn']
        tenant_id = self._get_tenant_id_for_create(context, edgevpns)
        edgevpn_db = (context.session.query(EdgeVPN).
                      filter_by(tenant_id=tenant_id).first())
        if edgevpn_db:
            edgevpn_id = edgevpn_db['id']
            raise (edgevpnextension.
                   DuplicateEdgeVPNForTenant(edgevpn_id=edgevpn_id,
                                             tenant_id=tenant_id))
        tunnel_type = "fullmesh"
        tunnel_backup = "frr"
        qos = "Gold"
        bandwidth = 10
        tunnel_options = edgevpns.get('tunnel_options')
        if tunnel_options:
            if tunnel_options.get('tunnel_type'):
                tunnel_type = tunnel_options['tunnel_type']
            if tunnel_options.get('tunnel_backup'):
                tunnel_backup = tunnel_options['tunnel_backup']
            if tunnel_options.get('qos'):
                qos = tunnel_options['qos']
            if tunnel_options.get('bandwidth'):
                bandwidth = tunnel_options['bandwidth']
        with context.session.begin(subtransactions=True):
            tenant_id = self._get_tenant_id_for_create(context, edgevpns)
            edgevpns_db = EdgeVPN(id=uuidutils.generate_uuid(),
                                  tenant_id=tenant_id,
                                  name=edgevpns['name'],
                                  tunnel_type=tunnel_type,
                                  tunnel_backup=tunnel_backup,
                                  qos=qos,
                                  bandwidth=bandwidth,
                                  status=constants.PENDING_CREATE,
                                  vpn_id=edgevpns['vpn_id'])
            context.session.add(edgevpns_db)
            self._modify_edgevpn_ac_associations(context,
                                                 edgevpns_db.id,
                                                 edgevpns[
                                                     'attachment_circuits'])
        return self._make_edgevpn_dict(edgevpns_db)

    def update_edgevpn(self, context, edgevpn_id, edgevpn):
        edgevpns = edgevpn['edgevpn']
        with context.session.begin(subtransactions=True):
            if 'attachment_circuits' in edgevpns:
                ac_id_list = edgevpns['attachment_circuits']
                self._modify_edgevpn_ac_associations(context,
                                                     edgevpn_id,
                                                     ac_id_list)
            edgevpn_db = self._get_resource(context, EdgeVPN, edgevpn_id)
        return self._make_edgevpn_dict(edgevpn_db)

    def update_edgevpn_status_and_name(self, context, edgevpn):
        with context.session.begin(subtransactions=True):
            edgevpns_db = self._get_resource(context, EdgeVPN, edgevpn['id'])
            edgevpns_db['name'] = edgevpn['name']
            edgevpns_db['status'] = edgevpn['status']
        return self._make_edgevpn_dict(edgevpns_db)

    def delete_edgevpn(self, context, edgevpn_id):
        with context.session.begin(subtransactions=True):
            edgevpns_db = self._get_resource(context, EdgeVPN, edgevpn_id)
            context.session.delete(edgevpns_db)

    def _get_edgevpn(self, context, edgevpn_id):
        return self._get_resource(context, EdgeVPN, edgevpn_id)

    def get_edgevpn(self, context, edgevpn_id, fields=None):
        edgevpns_db = self._get_resource(context, EdgeVPN, edgevpn_id)
        return self._make_edgevpn_dict(edgevpns_db, fields)

    def get_network_ports(self, context, network_id):
        session = context.session
        return (session.query(models_v2.Port).
                filter_by(network_id=network_id,
                          device_owner='compute:nova').all())

    def get_edgevpn_for_tenant(self, context, tenant_id):
        session = context.session
        return session.query(EdgeVPN).filter_by(tenant_id=tenant_id).first()

    def get_edgevpns(self, context, filters=None, fields=None):
        return self._get_collection(context, EdgeVPN,
                                    self._make_edgevpn_dict,
                                    filters=filters, fields=fields)

    def _modify_ac_networks_associations(self, context,
                                         attachmentcircuit_id,
                                         network_id_list):
        with context.session.begin(subtransactions=True):
            assoc_qry = context.session.query(ACNetworkAssociation)
            assocs = (assoc_qry.
                      filter_by(attachmentcircuit_id=attachmentcircuit_id).
                      all())
            for assoc in assocs:
                if assoc.network_id not in network_id_list:
                    assoc_db = self._get_resource(context,
                                                  ACNetworkAssociation,
                                                  assoc.id)
                    context.session.delete(assoc_db)
            attachmentcircuit_db = self._get_resource(context,
                                                      AttachmentCircuit,
                                                      attachmentcircuit_id)
            assoc_qry = context.session.query(ACNetworkAssociation)
            for network_id in network_id_list:
                assoc = (assoc_qry.
                         filter_by(attachmentcircuit_id=attachmentcircuit_id,
                                   network_id=network_id).first())
                if not assoc:
                    assoc = ACNetworkAssociation(
                        attachmentcircuit_id=attachmentcircuit_id,
                        network_id=network_id,
                        status=constants.ACTIVE)
                    attachmentcircuit_db.networks.append(assoc)

    def add_network_to_attachmentcircuit(self, context,
                                         attachmentcircuit_id, network_id):
        with context.session.begin(subtransactions=True):
            session_qry = context.session.query(AttachmentCircuit)
            attachmentcircuit_db = (session_qry.
                                    filter_by(id=attachmentcircuit_id).first())
            assoc_qry = context.session.query(ACNetworkAssociation)
            assoc = (assoc_qry.
                     filter_by(attachmentcircuit_id=attachmentcircuit_id,
                               network_id=network_id).first())
            if not assoc:
                assoc = ACNetworkAssociation(
                    attachmentcircuit_id=attachmentcircuit_id,
                    network_id=network_id,
                    status=constants.ACTIVE)
                attachmentcircuit_db.networks.append(assoc)

    def remove_network_from_attachmentcircuit(context,
                                              attachmentcircuit_id,
                                              network_id):
        with context.session.begin(subtransactions=True):
            assoc_qry = context.session.query(ACNetworkAssociation)
            assoc = assoc_qry.filter_by(
                attachmentcircuit_id=attachmentcircuit_id,
                network_id=network_id).first()
            if assoc:
                LOG.debug("Assoc found, deleting.")
                context.session.delete(assoc)

    def _make_attachmentcircuit_dict(self, attachmentcircuit, fields=None):
        res = {'id': attachmentcircuit['id'],
               'tenant_id': attachmentcircuit['tenant_id'],
               'name': attachmentcircuit['name'],
               'network_type': attachmentcircuit['network_type'],
               'provider_edge_id': attachmentcircuit['provider_edge_id']}
        res['networks'] = [n['network_id'] for n in attachmentcircuit.networks]
        return self._fields(res, fields)

    def create_attachment_circuit(self, context, attachment_circuit):
        attachmentcircuits = attachment_circuit['attachment_circuit']
        tenant_id = attachmentcircuits['tenant_id']
        attachmentcircuit_db = (context.session.
                                query(AttachmentCircuit).
                                filter_by(tenant_id=tenant_id).first())
        if attachmentcircuit_db:
            ac_id = attachmentcircuit_db['id']
            raise (edgevpnextension.
                   DuplicateAttachmentCircuitForTenant(
                       attachmentcircuit_id=ac_id, tenant_id=tenant_id))
        with context.session.begin(subtransactions=True):
            attachmentcircuits_db = AttachmentCircuit(
                id=uuidutils.generate_uuid(),
                name=attachmentcircuits['name'],
                tenant_id=attachmentcircuits['tenant_id'],
                network_type=attachmentcircuits['network_type'],
                provider_edge_id=attachmentcircuits['provider_edge_id'])
            context.session.add(attachmentcircuits_db)
            self._modify_ac_networks_associations(
                context,
                attachmentcircuits_db.id,
                attachmentcircuits['networks'])
        return self._make_attachmentcircuit_dict(attachmentcircuits_db)

    def update_attachment_circuit(self, context, attachmentcircuit_id,
                                  attachmentcircuit):
        attachmentcircuits = attachmentcircuit['attachment_circuit']
        with context.session.begin(subtransactions=True):
            if 'networks' in attachmentcircuits:
                self._modify_ac_networks_associations(
                    context, attachmentcircuit_id,
                    attachmentcircuits['networks'])
            attachmentcircuits_db = self._get_resource(context,
                                                       AttachmentCircuit,
                                                       attachmentcircuit_id)
        return self._make_attachmentcircuit_dict(attachmentcircuits_db)

    def delete_attachment_circuit(self, context, attachmentcircuit_id):
        with context.session.begin(subtransactions=True):
            attachmentcircuits_db = self._get_resource(context,
                                                       AttachmentCircuit,
                                                       attachmentcircuit_id)
            context.session.delete(attachmentcircuits_db)

    def _get_attachment_circuit(self, context, attachmentcircuit_id):
        return self._get_resource(context, AttachmentCircuit,
                                  attachmentcircuit_id)

    def get_attachment_circuit(self, context,
                               attachmentcircuit_id, fields=None):
        attachmentcircuits_db = self._get_resource(context, AttachmentCircuit,
                                                   attachmentcircuit_id)
        return self._make_attachmentcircuit_dict(attachmentcircuits_db, fields)

    def get_attachment_circuits(self, context, filters=None, fields=None):
        return self._get_collection(context, AttachmentCircuit,
                                    self._make_attachmentcircuit_dict,
                                    filters=filters, fields=fields)

    def get_attachmentcircuit_for_tenant(self, context, tenant_id):
        session = context.session
        return (session.query(AttachmentCircuit).
                filter_by(tenant_id=tenant_id).first())

    def get_attachmentcircuit(self, context, attachmentcircuit_id):
        session = context.session
        return (session.query(AttachmentCircuit).
                filter_by(id=attachmentcircuit_id).first())

    def get_vlans_for_attachment_circuit_id(
            self, context, attachmentcircuit_id):
        vlans = []
        session = context.session
        attachment_circuit = (session.query(AttachmentCircuit).
                              filter_by(id=attachmentcircuit_id).first())
        net_id_list = [n['network_id'] for n in attachment_circuit.networks]
        for network_id in net_id_list:
            segments = ml2_db.get_network_segments(context.session, network_id)
            for segment in segments:
                vlans.append(str(segment['segmentation_id']))
        return vlans

    def get_vlans_for_attachment_circuit(self, context, attachment_circuit):
        vlans = []
        for network_id in attachment_circuit['networks']:
            segments = ml2_db.get_network_segments(context.session, network_id)
            for segment in segments:
                vlans.append(str(segment['segmentation_id']))
        return vlans

    def get_edgevpn_for_attachment_circuit(
            self, context, attachmentcircuit_id):
        edgevpn = None
        assoc_qry = context.session.query(ACEdgeVPNAssociation)
        assoc = (assoc_qry.
                 filter_by(attachmentcircuit_id=attachmentcircuit_id).first())
        if assoc:
            edgevpn = (context.session.query(EdgeVPN).
                       filter_by(id=assoc.edgevpn_id).first())
        return edgevpn

    def _make_provideredge_dict(self, provideredge, fields=None):
        res = {'id': provideredge['id'],
               'name': provideredge['name']}
        return self._fields(res, fields)

    def create_provider_edge(self, context, provider_edge):
        provideredges = provider_edge['provider_edge']
        with context.session.begin(subtransactions=True):
            provideredges_db = ProviderEdge(id=uuidutils.generate_uuid(),
                                            name=provideredges['name'])
            context.session.add(provideredges_db)
        return self._make_provideredge_dict(provideredges_db)

    def update_provider_edge(self, context, provideredge):
        with context.session.begin(subtransactions=True):
            provideredges_db = self._get_resource(context, ProviderEdge,
                                                  provideredge['id'])
            provideredges_db.update(provideredge)
        return self._make_provideredge_dict(provideredges_db)

    def delete_provider_edge(self, context, provideredge_id):
        with context.session.begin(subtransactions=True):
            provideredges_db = self._get_resource(context, ProviderEdge,
                                                  provideredge_id)
            context.session.delete(provideredges_db)

    def _get_provider_edge(self, context, provideredge_id):
        return self._get_resource(context, ProviderEdge, provideredge_id)

    def get_provider_edge(self, context, provideredge_id, fields=None):
        provideredges_db = self._get_resource(context, ProviderEdge,
                                              provideredge_id)
        return self._make_provideredge_dict(provideredges_db, fields)

    def get_provider_edges(self, context, filters=None, fields=None):
        return self._get_collection(context, ProviderEdge,
                                    self._make_provideredge_dict,
                                    filters=filters, fields=fields)
