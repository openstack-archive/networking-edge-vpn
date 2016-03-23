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


from neutronclient.common import extension
from neutronclient.i18n import _
from neutronclient.neutron import v2_0 as neutronv20


class ProviderEdge(extension.NeutronClientExtension):
    resource = 'provider_edge'
    path = 'provider-edges'
    resource_plural = '%ss' % resource
    object_path = '/edgevpn/%s' % path
    resource_path = '/edgevpn/%s/%%s' % path
    versions = ['2.0']


class ProviderEdgeCreate(extension.ClientExtensionCreate, ProviderEdge):
    """Create a provider-edge."""

    shell_command = 'provider-edge-create'

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--name', default='',
            required=True,
            help=_('The ProviderEdge name to assign.'))
        parser.add_argument(
            '--ip_address', default='',
            help=_('The ProviderEdge ip address to assign.'))
        parser.add_argument(
            '--ip_version', default='',
            help=_('The ProviderEdge ip version to assign.'))
        parser.add_argument(
            '--remote_flag', default='',
            help=_('The ProviderEdge remote flag to assign.'))

    def args2body(self, parsed_args):
        body = {}
        neutronv20.update_dict(parsed_args, body,
                               ['name', 'tenant_id'])
        return {self.resource: body}


class ProviderEdgeDelete(extension.ClientExtensionDelete, ProviderEdge):
    """Delete a given provider-edge."""

    shell_command = 'provider-edge-delete'


class ProviderEdgeList(extension.ClientExtensionList, ProviderEdge):
    """List provider-edge that belong to a given tenant."""

    shell_command = 'provider-edge-list'

    list_columns = [
        'id', 'name', 'tenant_id'
    ]
    pagination_support = True
    sorting_support = True


class ProviderEdgeShow(extension.ClientExtensionShow, ProviderEdge):
    """Show information of a given provider-edge."""

    shell_command = 'provider-edge-show'
