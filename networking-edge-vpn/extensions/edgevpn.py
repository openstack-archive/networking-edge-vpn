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

import abc

from neutron.api import extensions
from neutron.api.v2 import attributes as attr
from neutron.api.v2 import resource_helper
from neutron.common import exceptions as qexception
from neutron.plugins.common import constants
from neutron.services import service_base
import six

supported_tunnel_types = ['fullmesh', 'Customized']
supported_tunnel_backup = ['frr', 'Secondary']
supported_qos = ['Gold', 'Silver', 'Bronze']
positive_int = (0, attr.UNLIMITED)
network_type = ['L2', 'L3']


class EdgeVPNNotFound(qexception.NotFound):
    message = "EDGEVPN %(edgevpn_id)s could not be found"


class DuplicateEdgeVPNForTenant(qexception.InvalidInput):
    message = ("EDGEVPN service %(edgevpn_id)s already exists "
               "for tenant %(tenant_id)s")


class AttachmentCircuitNotFound(qexception.NotFound):
    message = ("AttachmentCircuit %(attachmentcircuit_id)s could "
               "not be found")


class DuplicateAttachmentCircuitForTenant(qexception.InvalidInput):
    message = ("Attachment circuit %(attachmentcircuit_id)s already "
               "exists for tenant %(tenant_id)s")


class ProviderEdgeNotFound(qexception.NotFound):
    message = ("ProviderEdge %(provideredge_id)s could not be found")


class MPLSTunnelNotFound(qexception.NotFound):
    message = "MPLSTunnel %(mpls_tunnel_id)s could not be found"

RESOURCE_ATTRIBUTE_MAP = {

    'edgevpns': {
        'id': {'allow_post': False, 'allow_put': False,
               'validate': {'type:uuid': None},
               'is_visible': True,
               'primary_key': True},
        'tenant_id': {'allow_post': True, 'allow_put': False,
                      'validate': {'type:string': None},
                      'is_visible': True},
        'vpn_id': {'allow_post': True, 'allow_put': False,
                   'validate': {'type:string': None},
                   'is_visible': True},
        'network_type': {'allow_post': True, 'allow_put': False,
                         'validate': {'type:string': None},
                         'is_visible': True, 'default': 'L2'},
        'name': {'allow_post': True, 'allow_put': False,
                 'validate': {'type:string': None},
                 'is_visible': True, 'default': ''},
        'status': {'allow_post': False, 'allow_put': False,
                   'is_visible': True},
        'mpls_tunnels': {'allow_post': True, 'allow_put': True,
                         'convert_to': attr.convert_none_to_empty_list,
                         'validate': {'type:uuid_list': None},
                         'default': None,
                         'is_visible': True},
        'attachment_circuits': {'allow_post': True, 'allow_put': True,
                                'convert_to': attr.convert_none_to_empty_list,
                                'validate': {'type:uuid_list': None},
                                'default': None,
                                'is_visible': True}
    },
    'attachment_circuits': {
        'id': {'allow_post': False, 'allow_put': False,
               'validate': {'type:uuid': None},
               'is_visible': True,
               'primary_key': True},
        'tenant_id': {'allow_post': True, 'allow_put': False,
                      'validate': {'type:string': None},
                      'is_visible': True},
        'name': {'allow_post': True, 'allow_put': False,
                 'validate': {'type:string': None},
                 'is_visible': True, 'default': ''},
        'network_type': {'allow_post': True, 'allow_put': False,
                         'validate': {'type:string': None},
                         'is_visible': True, 'default': 'L2'},
        'provider_edge_id': {'allow_post': True, 'allow_put': False,
                             'validate': {'type:uuid': None},
                             'is_visible': True},
        'networks': {'allow_post': True, 'allow_put': True,
                     'convert_to': attr.convert_none_to_empty_list,
                     'validate': {'type:uuid_list': None},
                     'default': None,
                     'is_visible': True}
    },
    'provider_edges': {
        'id': {'allow_post': False, 'allow_put': False,
               'validate': {'type:uuid': None},
               'is_visible': True,
               'primary_key': True},
        'name': {'allow_post': True, 'allow_put': True,
                 'validate': {'type:string': None},
                 'is_visible': True, 'default': ''},
        'tenant_id': {'allow_post': True, 'allow_put': False,
                      'validate': {'type:string': None},
                      'is_visible': True},
        'ip_address': {'allow_post': True, 'allow_put': False,
                       'validate': {'type:string': None},
                       'is_visible': True, 'default': ''},
        'ip_version': {'allow_post': True, 'allow_put': False,
                       'validate': {'type:string': None},
                       'is_visible': True, 'default': ''},
        'remote_flag': {'allow_post': True, 'allow_put': False,
                        'validate': {'type:string': None},
                        'is_visible': True, 'default': ''}
    },
    'mpls_tunnels': {
        'id': {'allow_post': False, 'allow_put': False,
               'validate': {'type:uuid': None},
               'is_visible': True,
               'primary_key': True},
        'name': {'allow_post': True, 'allow_put': True,
                 'validate': {'type:string': None},
                 'is_visible': True, 'default': ''},
        'tenant_id': {'allow_post': True, 'allow_put': False,
                      'validate': {'type:string': None},
                      'is_visible': True},
        'provider_edge_id': {'allow_post': True, 'allow_put': False,
                             'validate': {'type:uuid': None},
                             'is_visible': True},
        'peer_ip_address': {'allow_post': True, 'allow_put': False,
                            'validate': {'type:string': None},
                            'is_visible': True},
        'peer_ip_version': {'allow_post': True, 'allow_put': False,
                            'validate': {'type:string': None},
                            'is_visible': True},
        'tunnel_options': {'allow_post': True, 'allow_put': False,
                           'convert_to': attr.convert_none_to_empty_dict,
                           'default': {},
                           'validate': {'type:dict_or_empty': {
                               'backup': {'type:values':
                                          supported_tunnel_backup,
                                          'default': 'frr',
                                          'required': False},
                               'qos': {'type:values': supported_qos,
                                       'default': 'Gold',
                                       'required': False},
                               'bandwidth': {'type:range': positive_int,
                                             'default': '10',
                                             'required': False}}},
                           'is_visible': True},
        'status': {'allow_post': False, 'allow_put': False,
                   'is_visible': True}
    }

}


class Edgevpn(extensions.ExtensionDescriptor):

    @classmethod
    def get_name(cls):
        return "EDGE VPN service"

    @classmethod
    def get_alias(cls):
        return "edgevpn"

    @classmethod
    def get_description(cls):
        return "Extension for EDGE VPN service"

    @classmethod
    def get_namespace(cls):
        return "https://wiki.openstack.org/Neutron/EDGEVPN"

    @classmethod
    def get_updated(cls):
        return "2014-03-17T10:00:00-00:00"

    @classmethod
    def get_resources(cls):
        special_mappings = {}
        plural_mappings = resource_helper.build_plural_mappings(
            special_mappings, RESOURCE_ATTRIBUTE_MAP)
        attr.PLURALS.update(plural_mappings)
        return resource_helper.build_resource_info(plural_mappings,
                                                   RESOURCE_ATTRIBUTE_MAP,
                                                   constants.EDGEVPN,
                                                   register_quota=True,
                                                   translate_name=True)

    @classmethod
    def get_plugin_interface(cls):
        return EdgeVPNPluginBase

    def update_attributes_map(self, attributes):
        super(Edgevpn, self).update_attributes_map(
            attributes, extension_attrs_map=RESOURCE_ATTRIBUTE_MAP)

    def get_extended_resources(self, version):
        if version == "2.0":
            return RESOURCE_ATTRIBUTE_MAP
        else:
            return {}


@six.add_metaclass(abc.ABCMeta)
class EdgeVPNPluginBase(service_base.ServicePluginBase):

    def get_plugin_name(self):
        return constants.EDGEVPN

    def get_plugin_type(self):
        return constants.EDGEVPN

    def get_plugin_description(self):
        return 'EDGE VPN service plugin'

    @abc.abstractmethod
    def get_edgevpns(self, context, filters=None, fields=None):
        pass

    @abc.abstractmethod
    def get_edgevpn(self, context, edgevpn_id, fields=None):
        pass

    @abc.abstractmethod
    def create_mpls_tunnel(self, context, mpls_tunnel):
        pass

    @abc.abstractmethod
    def update_mpls_tunnel(self, context, mpls_tunnel):
        pass

    @abc.abstractmethod
    def delete_mpls_tunnel(self, context, mpls_tunnel):
        pass

    @abc.abstractmethod
    def create_edgevpn(self, context, edgevpn):
        pass

    @abc.abstractmethod
    def update_edgevpn(self, context, edgevpn_id, edgevpn):
        pass

    @abc.abstractmethod
    def delete_edgevpn(self, context, edgevpn_id):
        pass

    @abc.abstractmethod
    def get_attachment_circuits(self, context, filters=None, fields=None):
        pass

    @abc.abstractmethod
    def get_attachment_circuit(self, context, attachmentcircuit_id,
                               fields=None):
        pass

    @abc.abstractmethod
    def create_attachment_circuit(self, context, attachmentcircuit):
        pass

    @abc.abstractmethod
    def update_attachment_circuit(self, context, attachmentcircuit_id,
                                  attachmentcircuit):
        pass

    @abc.abstractmethod
    def delete_attachment_circuit(self, context, attachmentcircuit_id):
        pass

    @abc.abstractmethod
    def get_provider_edges(self, context, filters=None, fields=None):
        pass

    @abc.abstractmethod
    def get_provider_edge(self, context, provideredge_id, fields=None):
        pass

    @abc.abstractmethod
    def create_provider_edge(self, context, provideredge):
        pass

    @abc.abstractmethod
    def delete_provider_edge(self, context, provideredge_id):
        pass
