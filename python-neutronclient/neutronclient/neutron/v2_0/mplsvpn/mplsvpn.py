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

import logging
import string

from neutronclient.neutron import v2_0 as neutronv20
from neutronclient.openstack.common.gettextutils import _


class ListMPLSVPN(neutronv20.ListCommand):
    """List MPLSVPN configurations that belong to a given tenant."""

    resource = 'mplsvpn'
    log = logging.getLogger(__name__ + '.ListMPLSVPN')
    list_columns = [
        'id', 'name', 'status'
    ]
    _formatters = {}
    pagination_support = True
    sorting_support = True


class ShowMPLSVPN(neutronv20.ShowCommand):
    """Show information of a given MPLSVPN."""

    resource = 'mplsvpn'
    log = logging.getLogger(__name__ + '.ShowMPLSVPN')


class CreateMPLSVPN(neutronv20.CreateCommand):
    """Create a MPLSVPN."""
    resource = 'mplsvpn'
    log = logging.getLogger(__name__ + '.CreateMPLSVPN')

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--vpn-id',
            required=True,
            help=_('VPLS ID'))
        parser.add_argument(
            '--name', default='',
            help=_('The MPLSVPN name to assign.'))
        parser.add_argument(
            '--tunnel-type', default='fullmesh',
            choices=['fullmesh', 'Customized'],
            help=_('LSP tunnel type.'))
        parser.add_argument(
            '--tunnel-backup', default='frr',
            choices=['frr', 'Secondary'],
            help=_('Tunnel failover option.'))
        parser.add_argument(
            '--qos', default='Gold',
            choices=['Gold', 'Silver', 'Bronze'],
            help=_('Tunnel qos'))
        parser.add_argument(
            '--bandwidth', default='10',
            help=_('Tunnel bandwidth, default: 10.'))
        parser.add_argument(
            '--attachment-circuits', type=string.split,
            help=_('List of whitespace-delimited attachment circuit'
                   ' names or IDs; e.g., --attachment-circuits \"ac1 ac2\"'))

    def args2body(self, parsed_args):
        body = {
            self.resource: {
                'vpn_id': parsed_args.vpn_id,
                'name': parsed_args.name,
                'tunnel_options': {
                    'tunnel_type': parsed_args.tunnel_type,
                    'tunnel_backup': parsed_args.tunnel_backup,
                    'qos': parsed_args.qos,
                    'bandwidth': parsed_args.bandwidth
                }
            }
        }
        if parsed_args.attachment_circuits:
            _attachment_circuits = []
            for n in parsed_args.attachment_circuits:
                _attachment_circuits.append(
                    neutronv20.find_resourceid_by_name_or_id(
                        self.get_client(), 'attachment_circuit', n))
            (body['mplsvpn'].
             update({'attachment_circuits': _attachment_circuits}))

        neutronv20.update_dict(parsed_args, body[self.resource],
                               ['tenant_id'])
        return body


class UpdateMPLSVPN(neutronv20.UpdateCommand):
    """Update a given MPLSVPN by modifying attachment circuit list."""

    resource = 'mplsvpn'
    log = logging.getLogger(__name__ + '.UpdateMPLSVPN')

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
            (body['mplsvpn'].
             update({'attachment_circuits': _attachment_circuits}))
        return body


class DeleteMPLSVPN(neutronv20.DeleteCommand):
    """Delete a given MPLSVPN."""

    resource = 'mplsvpn'
    log = logging.getLogger(__name__ + '.DeleteMPLSVPN')
