..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

==========================================
Neutron extension for edge VPN
==========================================

https://blueprints.launchpad.net/neutron/+spec/edge-vpn

Once an edge VPN has been provisioned using the spec defined at [1], a Neutron
network or a router needs to be attached to it.  This spec details the APIs
required to bind a Neutron network or a router to an edge VPN.


Problem Description
===================

Once an edge VPN has been provisioned using the spec defined at [1], a Neutron
network or router needs to be bridged to it.  As part of the edge VPN creation,
an empty list of "attachment circuit" is created.  A list of APIs are needed,
once a Neutron network or a router is created/deleted, to update the attachment
circuit which is part of the edge VPN construct.


Proposed Change
===============

When a user creates a Neutron network (for example, a VLAN), a tenant's edge
VPN attachment circuit can be "updated" to bridge this network across an
edge VPN.  An "update" call will be required to remove the network from
attachment in the event when a user deletes a Neutron network.  The attachment
circuit construct was introduced in the spec at [1].

Proposed API extensions are introduced under the REST API URL: /v2.0/edgevpn/.
The attachment circuit construct is defined as follows:

Attachment circuit object carries a list of Neutron networks.  Upon creation of
an edge VPN service, an attachment circuit with an empty list of Neutron networks is
created.  Once a user (tenant or an admin) creates a Neutron network (L2 or an
L3 - VLAN or a subnet), this network can be made part of the edge VPN.  CRUD
operations for attachment circuits will be supported under
/v2.0/edgevpn/attachment-circuits.


Data Model Impact
-----------------

None

REST API Impact
---------------

Attachment circuits can be created for a given tenant to attach (or bridge) its
Neutron networks to the edge VPN.  The provider edge in each datacenter
specifies the local end point of the edge VPN.

Request

::
     POST /v2.0/edgevpn/attachment-circuits
     Accept: application/json

     {
         "attachment_circuits": [
         {"tenant_id": "<UUID of tenant>,
         "name":"DataCenter 1",
         "type":"L2", // Other options L3
         "provider_edge_id":"<UUID of provider edge 1>",
         "networks":[
         "<UUID of a Neutron network to be extended>"
         // More Neutron networks are allowed]},

         {"tenant_id": "<UUID of tenant>,
         "name":"DataCenter 2",
         "type":"L2", // Other options L3
         "provider_edge_id":"<UUID of provider edge 2>",
         "networks":[
         "<UUID of a Neutron network to be extended>"
         // More Neutron networks are allowed]}

         ]

     }

Response

::
     {
         "attachment_circuits":[
         {"name":"DataCenter 1",
         "id":"<UUID of attachment circuit>",
         "tenant_id":"<UUID of the tenant for which it has been created>",
         "provider_edge_id": "<UUID of provider edge>",
         "networks":[
         "UUID of a Neutron network"]

         }

         {"name":"DataCenter 2",
         "id":"<UUID of attachment circuit>",
         "tenant_id":"<UUID of the tenant for which it has been created>",
         "provider_edge_id": "<UUID of provider edge>",
         "networks":[
         "UUID of a Neutron network"]

         }

         ]

     }

PUT call can be used to modify the network list after the attachment circuit
has already been created.

Request

::
     PUT /v2.0/edgevpn/attachment-circuits/{attachment-circuit-id}
     Accept: application/json

     {
         "attachment_circuit":
         {"networks":[
         "<UUID of a Neutron network to be extended>",
         // More Neutron networks are allowed ]

         }

     }

Response

::
     {
         "attachment_circuit":
         {"name":"DataCenter 1",
         "id":"<UUID of attachment circuit>",
         "provider_edge_id": "<UUID of provider edge>",
         "networks":[
         "UUID of a Neutron network"]

         }

    }


Security Impact
---------------

None

Notifications Impact
--------------------

None

Other End User Impact
---------------------

End user can interact using the following commands:

The following command lists attachment circuits for a given tenant.

::
    edgevpn-attachmentcircuit-list

The following command shows info of a given attachment circuit.

::
    edgevpn-attachmentcircuit-show

The following command creates an attachment circuit.

::
    edgevpn-attachmentcircuit-create

The following command updates the network list of an attachment circuit.

::
    edgevpn-attachmentcircuit-update

The following command deletes an attachment circuit.

::
    edgevpn-attachmentcircuit-delete

Performance Impact
------------------

None

IPv6 Impact
-----------

This spec addresses IPv6 scenarios and is expected to work in an IPv6
environment.


Other Deployer Impact
---------------------

None

Developer Impact
----------------

Developer use the APIs described in this spec to update an attachment circuit
which allows bridging of a Neutron network to an edge VPN.

Community Impact
----------------

None

Alternatives
------------

There is an alternate spec which only addresses bridging Neutron network to
one specific type of edge VPN called BGP VPN.  This spec can be found at [5].


Implementation
==============

Assignee(s)
-----------

Primary assignee:
  Mohammad Hanif <mhanif>

Other contributors:

  Karthik Natarajan <natarajk>
  Angela Smith <aallen-m>
  Tianran Zhou <zhoutianran>
  Vikram Choudhary <vikschw>

Work Items
----------

An attachment circuit is created as part of an edge VPN service creation [1].
It is initially an empty list.  The APIs proposed in this spec can be used to
make a Neutron network part of the attachment circuit (via ML2 driver, for
example) thereby extending (bridging) this network across an edge VPN.


Dependencies
============

The proposed APIs depend on the edge VPN API framework described in the spec at
[1].


Testing
=======

In order to test the bridging of a Neutron network to an edge VPN, for example
an L2 network, an ML2 mechanism driver will need to be modified to make an
"update" API call to update a Neutron network list in the attachment circuit
object.

Tempest Tests
-------------

None.

Functional Tests
----------------
Tests will be written to test the supported functionality defined objects such
as attachment circuits.  This object supports the standard CRUD operations.
The functional tests will ensure the correctness of these operations.

API Tests
---------

All of the defined APIs will be tested for all of their CRUD operations.
Neutron commands will be introduced which will make REST calls based on the
defined APIs.  The defined APIs support GET/POST/PUT/DELETE operations and the
Neutron commands utilize every aspect of these calls and will implement
create/update/delete/show/list operations.  One can utilize these commands to
test the API calls as well.


Documentation Impact
====================

The proposed APIs will need to be documented in the OpenStack Networking API
documentation.

User Documentation
------------------

Admin User guide will need to be updated with the introduction of the
attachment circuit API.

Developer Documentation
-----------------------

The proposed APIs will need to be documented in the OpenStack Networking API
documentation.

References
==========

.. [1] Edge VPN provisioning
   https://review.openstack.org/201378

.. [2] Interconnecting Data Centers using MPLS BGP L3 VPN
   https://www.youtube.com/watch?v=KwW0dtvHIgQ
   https://www.youtube.com/watch?v=q5z0aPrUZYc

.. [3] Different VPN Flavors in neutron
   https://etherpad.openstack.org/p/vpn-flavors

.. [4] BGP based IP VPNs attachment use case
   https://review.openstack.org/#/c/171680/

.. [5] Neutron Extension for BGPVPN
   https://review.openstack.org/#/c/177740/