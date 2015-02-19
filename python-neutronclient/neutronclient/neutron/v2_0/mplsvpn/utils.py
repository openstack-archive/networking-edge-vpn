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

from neutron.openstack.common import uuidutils
from neutronclient.common import exceptions
from neutronclient.openstack.common.gettextutils import _

networks_supported_keys = ['network_id']


def validate_networks_dict(network_dict):
    for key, value in network_dict.items():
        if key not in networks_supported_keys:
            message = _(
                "Network Dictionary KeyError: "
                "Reason-Invalid Network key : "
                "'%(key)s' not in %(supported_key)s ") % {
                    'key': key, 'supported_key': networks_supported_keys}
            raise exceptions.CommandError(message)
        if key in ('network_id'):
            try:
                if not uuidutils.is_uuid_like(value):
                    raise ValueError()
            except ValueError:
                message = _(
                    "Network Dictionary ValueError: "
                    "Reason-Invalid uuid value: "
                    "'%(key)s' = %(value)s ") % {
                        'key': key, 'value': value}
                raise exceptions.CommandError(message)
        else:
            network_dict[key] = value
    return
