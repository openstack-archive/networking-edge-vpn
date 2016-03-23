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
import string

from neutronclient.common import extension
from neutronclient.i18n import _
from neutronclient.neutron import v2_0 as neutronv20


class MPLSTunnel(extension.NeutronClientExtension):
    resource = 'mpls_tunnel'
    path = 'mpls-tunnels'
    resource_plural = '%ss' % resource
    object_path = '/edgevpn/%s' % path
    resource_path = '/edgevpn/%s/%%s' % path
    versions = ['2.0']


class MPLSTunnelCreate(extension.ClientExtensionCreate, MPLSTunnel):
    """Create a MPLSVPN."""

    shell_command = 'mpls-tunnel-create'

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--name', default='',
            required=True,
            help=_('The MPLSVPN name to assign.'))
        parser.add_argument(
            '--provider-edge-id', default='',
            required=True,
            help=_('Provider Edge Id.  Required.'))
        parser.add_argument(
            '--peer-ip-address', default='',
            help=_('Peer IP Addr.  Required.'))
        parser.add_argument(
            '--peer-ip-version', default='',
            help=_('Peer IP version.  Required.'))
        parser.add_argument(
            '--backup', default='frr',
            choices=['frr', 'Secondary'],
            help=_('Tunnel failover option.'))
        parser.add_argument(
            '--qos', default='Gold',
            choices=['Gold', 'Silver', 'Bronze'],
            help=_('Tunnel qos'))
        parser.add_argument(
            '--bandwidth', default='10',
            help=_('Tunnel bandwidth, default: 10.'))

    def args2body(self, parsed_args):
        body = {
            self.resource: {
                'name': parsed_args.name,
                'provider_edge_id': neutronv20.find_resourceid_by_name_or_id(
                    self.get_client(), 'provider_edge',
                    parsed_args.provider_edge_id),
                'tunnel_options': {
                    'backup': parsed_args.backup,
                    'qos': parsed_args.qos,
                    'bandwidth': parsed_args.bandwidth
                }
            }
        }

        neutronv20.update_dict(parsed_args, body[self.resource],
                               ['tenant_id'])
        return body


class MPLSTunnelUpdate(extension.ClientExtensionUpdate, MPLSTunnel):
    """Update a given MPLSVPN by modifying attachment circuit list."""

    shell_command = 'mpls-tunnel-update'

    def add_known_arguments(self, parser):

        parser.add_argument(
            '--mpls-tunnels', type=string.split,
            help=_('List of whitespace-delimited attachment circuit names'
                   ' or IDs; e.g., --attachment-circuits \"ac1 ac2\".  '
                   'To remove last attachment circuit, specify \"none\".'))

    def args2body(self, parsed_args):
        body = {
            self.resource: {
            }
        }
        if parsed_args.mpls_tunnels:
            _mpls_tunnels = []
            for n in parsed_args.mpls_tunnels:
                if n.lower() in ['none']:
                    break
                _mpls_tunnels.append(
                    neutronv20.find_resourceid_by_name_or_id(
                        self.get_client(), 'mpls_tunnel', n))
            (body['mpls_tunnel'].
             update({'mpls_tunnels': _mpls_tunnels}))
        return body


class MPLSTunnelDelete(extension.ClientExtensionDelete, MPLSTunnel):
    """Delete a given MPLS Tunnel."""

    shell_command = 'mpls-tunnel-delete'


class MPLSTunnelList(extension.ClientExtensionList, MPLSTunnel):
    """List MPLSVPN configurations that belong to a given tenant."""

    shell_command = 'mpls-tunnel-list'

    list_columns = [
        'id', 'name'
    ]
    pagination_support = True
    sorting_support = True


class MPLSTunnelShow(extension.ClientExtensionShow, MPLSTunnel):
    """Show information of a given MPLSVPN."""

    shell_command = 'mpls-tunnel-show'
