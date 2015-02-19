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

from neutronclient.neutron import v2_0 as neutronv20
from neutronclient.openstack.common.gettextutils import _


class ListProviderEdge(neutronv20.ListCommand):
    """List ProviderEdges configurations that belong to a given tenant."""

    resource = 'provider_edge'
    log = logging.getLogger(__name__ + '.ListProviderEdge')
    list_columns = [
        'id', 'name'
    ]
    _formatters = {}
    pagination_support = True
    sorting_support = True


class ShowProviderEdge(neutronv20.ShowCommand):
    """Show information of a given ProviderEdge."""

    resource = 'provider_edge'
    log = logging.getLogger(__name__ + '.ShowProviderEdge')


class CreateProviderEdge(neutronv20.CreateCommand):
    """Create a Provider Edge."""
    resource = 'provider_edge'
    log = logging.getLogger(__name__ + '.CreateProviderEdge')

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--name', default='',
            help=_('The ProviderEdge name to assign.'))

    def args2body(self, parsed_args):
        body = {
            self.resource: {
                'name': parsed_args.name
            }
        }
        neutronv20.update_dict(parsed_args, body[self.resource],
                               ['tenant_id'])
        return body


class DeleteProviderEdge(neutronv20.DeleteCommand):
    """Delete a given ProviderEdge."""

    resource = 'provider_edge'
    log = logging.getLogger(__name__ + '.DeleteProviderEdge')
