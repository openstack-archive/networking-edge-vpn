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


class ListAttachmentCircuit(neutronv20.ListCommand):
    """List AttachmentCircuits configurations that belong to a given tenant."""

    resource = 'attachment_circuit'
    log = logging.getLogger(__name__ + '.ListAttachmentCircuit')
    list_columns = [
         'id', 'name', 'tenant_id'
    ]
    _formatters = {}
    pagination_support = True
    sorting_support = True


class ShowAttachmentCircuit(neutronv20.ShowCommand):
    """Show information of a given AttachmentCircuit."""

    resource = 'attachment_circuit'
    log = logging.getLogger(__name__ + '.ShowAttachmentCircuit')

class CreateAttachmentCircuit(neutronv20.CreateCommand):
    """Create a Attachment Circuit."""
    resource = 'attachment_circuit'
    log = logging.getLogger(__name__ + '.CreateAttachmentCircuit')

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--name', default='',
            required=True,
            help=_('The attachmentcircuit name to assign.  Required.'))
        parser.add_argument(
            '--network-type', default='L2',
            choices=['L2', 'L3'],
            help=_('Type of Network, default: L2. Other option: L3'))
        parser.add_argument(
            '--provider-edge-id', default='',
            required=True,
            help=_('Provider Edge Id.  Required.'))
	parser.add_argument(
            '--networks', type=string.split, default="",
            help=_('List of whitespace-delimited network names or IDs; e.g., --networks \"net1 net2\"'))	 

    def args2body(self, parsed_args):
        body = {
            self.resource: {
                'name': parsed_args.name,
		'network_type': parsed_args.network_type,
		'provider_edge_id': neutronv20.find_resourceid_by_name_or_id(
                                        self.get_client(), 'provider_edge', parsed_args.provider_edge_id)
            }
        }
        if parsed_args.networks:
            _networks = []
            for n in parsed_args.networks:
                _networks.append(
                    neutronv20.find_resourceid_by_name_or_id(
                        self.get_client(), 'network', n))
            body['attachment_circuit'].update({'networks': _networks})

        neutronv20.update_dict(parsed_args, body[self.resource],
                               ['tenant_id'])
        return body
   

class UpdateAttachmentCircuit(neutronv20.UpdateCommand):
    """Update a given AttachmentCircuit by modifying network list."""

    resource = 'attachment_circuit'
    log = logging.getLogger(__name__ + '.UpdateAttachmentCircuit')

    def add_known_arguments(self, parser):

        parser.add_argument(
            '--networks', type=string.split,
            help=_('List of whitespace-delimited network names or IDs; e.g., --networks \"net1 net2\".  To remove last network, specify \"none\".'))

    def args2body(self, parsed_args):
        body = {
            self.resource: {
            }
        }
        if parsed_args.networks:
            _networks = []
            for n in parsed_args.networks:
                if n.lower() in ['none']:
                    break
                _networks.append(
                    neutronv20.find_resourceid_by_name_or_id(
                        self.get_client(), 'network', n))
            body['attachment_circuit'].update({'networks': _networks})

        return body


class DeleteAttachmentCircuit(neutronv20.DeleteCommand):
    """Delete a given AttachmentCircuit."""

    resource = 'attachment_circuit'
    log = logging.getLogger(__name__ + '.DeleteAttachmentCircuit')
