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

from neutronclient.common import extension
from neutronclient.i18n import _
from neutronclient.neutron import v2_0 as neutronv20
import string


class EdgeVPN(extension.NeutronClientExtension):
    resource = 'edgevpn'
    path = 'edgevpns'
    resource_plural = '%ss' % resource
    object_path = '/edgevpn/%s' % path
    resource_path = '/edgevpn/%s/%%s' % path
    versions = ['2.0']


class EdgeVPNCreate(extension.ClientExtensionCreate, EdgeVPN):
    """Create a MPLSVPN."""

    shell_command = 'edge-vpn-create'

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--name', default='',
            help=_('The MPLSVPN name to assign.'))
        parser.add_argument(
            '--vpn-id',
            required=True,
            help=_('VPLS ID'))
        parser.add_argument(
            '--network-type', default='L2',
            choices=['L2', 'L3'],
            help=_('Type of Network, default: L2. Other option: L3'))
        parser.add_argument(
            '--mpls-tunnels', type=string.split, default="",
            help=_('List of whitespace-delimited mpls tunnel names or IDs;'
                   ' e.g., --mpls-tunnels \"tunn1 tunn2\"'))
        parser.add_argument(
            '--attachment-circuits', type=string.split,
            help=_('List of whitespace-delimited attachment circuit'
                   ' names or IDs; e.g., --attachment-circuits \"ac1 ac2\"'))

    def args2body(self, parsed_args):
        body = {
            self.resource: {
                'vpn_id': parsed_args.vpn_id,
                'name': parsed_args.name,
                'network_type': parsed_args.network_type
            }
        }
        if parsed_args.mpls_tunnels:
            _mpls_tunnels = []
            for n in parsed_args.mpls_tunnels:
                _mpls_tunnels.append(
                    neutronv20.find_resourceid_by_name_or_id(
                        self.get_client(), 'mpls_tunnel', n))
            body['edgevpn'].update({'mpls_tunnels': _mpls_tunnels})

        if parsed_args.attachment_circuits:
            _attachment_circuits = []
            for n in parsed_args.attachment_circuits:
                _attachment_circuits.append(
                    neutronv20.find_resourceid_by_name_or_id(
                        self.get_client(), 'attachment_circuit', n))
            (body['edgevpn'].
             update({'attachment_circuits': _attachment_circuits}))

        neutronv20.update_dict(parsed_args, body[self.resource],
                               ['tenant_id'])
        return body


class EdgeVPNUpdate(extension.ClientExtensionUpdate, EdgeVPN):
    """Update a given EDGEVPN by modifying attachment circuit list."""

    shell_command = 'edge-vpn-update'

    def add_known_arguments(self, parser):

        parser.add_argument(
            '--attachment-circuits', type=string.split,
            help=_('List of whitespace-delimited attachment circuit names'
                   ' or IDs; e.g., --attachment-circuits \"ac1 ac2\".  '
                   'To remove last attachment circuit, specify \"none\".'))

    def args2body(self, parsed_args):
        body = {
            self.resource: {
            }
        }
        if parsed_args.attachment_circuits:
            _attachment_circuits = []
            for n in parsed_args.attachment_circuits:
                if n.lower() in ['none']:
                    break
                _attachment_circuits.append(
                    neutronv20.find_resourceid_by_name_or_id(
                        self.get_client(), 'attachment_circuit', n))
            (body['edgevpn'].
             update({'attachment_circuits': _attachment_circuits}))
        return body


class EdgeVPNDelete(extension.ClientExtensionDelete, EdgeVPN):
    """Delete a given EDGEVPN."""

    shell_command = 'edge-vpn-delete'


class EdgeVPNList(extension.ClientExtensionList, EdgeVPN):
    """List EDGEVPN configurations that belong to a given tenant."""

    shell_command = 'edge-vpn-list'

    list_columns = [
        'id', 'name', 'status'
    ]
    pagination_support = True
    sorting_support = True


class EdgeVPNShow(extension.ClientExtensionShow, EdgeVPN):
    """Show information of a given EDGEVPN."""

    shell_command = 'edge-vpn-show'
