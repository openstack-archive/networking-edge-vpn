..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

=========================================================
Edge VPN APIs
=========================================================

Include the URL of your launchpad blueprint:

https://blueprints.launchpad.net/neutron/+spec/edge-vpn

With the advent of cloud services that require massive computing resources on-
demand, the architectural model of datacenters are drifting towards
geographically distributed pools of shared resources. As a result, Cloud
should be conceived as a multi datacenter environment that offers
orchestration of per tenant virtual (logical) network which spans multiple
datacenters.  This will provide capabilities to implement inter datacenter
multi-tenant services or to migrate tenant services, such as a virtual
machine(VM), from one datacenter to another in order to exploit, for instance,
geographical variations of energy costs.

MPLS VPNs are some of the widely deployed edge VPNs in the data center. MPLS
technology enables the deployment of layer 2 and layer 3 VPNs between
datacenters with QoS guarantees to provide inter datacenter connectivity.
With these capabilities, tenant virtual machines located in different
datacenters can communicate transparently and can also seamlessly move between
datacenters.

Problem Description
===================

OpenStack currently does not support creation of Edge VPNs for inter datacenter
connectivity.  Hence, the connectivity between Neutron networks is only limited
to within a single datacenter.

Proposed Change
===============

This blueprint proposes a framework and a set of APIs to orchestrate an edge
VPN service using OpenStack.  A vendor can implement a service plugin
conforming to this framework/APIs to allow orchestrating an edge VPN on its
physical device.  Once a VPN service is created, a Neutron network can be
bridged to this VPN.  This spec also addresses how a Neutron network can be
bridged to an edge VPN.

A framework and a set of networking APIs is introduced to aid orchestrating
edge VPN connectivty by leveraging Neutron APIs.  Following describes the
abstractions used to detail the proposed API.

Provider Edge (PE): Virtual concept to describe the provider edge devices
(single or cluster) in each datacenter that extends Neutron L2 networks (such as
a VLAN) or L3 networks (such as a subnet) using an MPLS VPN service over WAN.

Attachment Circuit: Virtual concept to bridge a Neutron network to the edge
VPN.

Tunnel: Virtual concept to describe the connectivity between provider edges
(from one edge of a datacenter to another) that provides Qos, Backup-type,
and Bandwidth criteria.

MPLS VPN: An Edge VPN service that provides connectivity between attachment
circuits in different datacenters.

Using these basic abstractions, the defined APIs provide operations to connect
two or more Neutron networks distributed in different datacenters using
the steps given below:

1. Cloud network administrator provisions an edge VPN for a given tenant by
creating an MPLS VPN service.  As part of an MPLS VPN service creation, the
network administrator creates a list of remote PEs and the tunnels to provide
connectivity to remote PEs.  Also, as part of an MPLS VPN service creation, an
attachment circuit is also created.  Initially, the Neutron network list is
an empty list inside the attachement circuit.

2.  When a user creates a Neutron network (for example, a VLAN), a tenant' edge
VPN's attachement circuit may be "updated" to bridge this network across an edge
VPN.  An "update" call will be required to remove the network from attachement
in the event when a user deletes a Neutron network.

Service API extensions for Inter DC orchestration support are introduced
under the REST API URL: /v2.0/mplsvpn/

Provider Edge (PE):
Operations on a PE object can only be performed by a network administrator.PE
objects define the datacenter border(edge) routers.  PE objects are specified
as part of an edge VPN service creation.  CRUD operations for provider edges
will be supported under /v2.0/mplsvpn/provider-edges.

Attachment Circuit:
Attachment circuit object carries a list of Neutron networks.  Upon creation of
a VPN service, an attachment circuit with an empty list of Neutron networks is
created.  Once a user creates a Neutron network (L2 or an L3 - VLAN or a
subnet), this network can be made part of the edge VPN by an update call to the
attachment circuit object.  CRUD operations for attachment circuits will be
supported under /v2.0/mplsvpn/attachment-circuits.

Tunnel:
Tunnel related operations are available only to cloud network administrators.
Network administrators can create tunnel objects with remote PES as egress end
points for these tunnels.  Tunnels may be shared across multiple VPNs. CRUD
operations for tunnels will be supported under /v2.0/mplsvpn/tunnels.

MPLS VPN:
MPLS VPN related operations are available only to cloud network administrators.
CRUD operations for MPLS VPN service will be supported under
ß/v2.0/mplsvpn/mplsvpns.

Data Model Impact
-----------------

None.

REST API Impact
---------------

The example below uses REST API to create attachment circuits in each
datacenter and connects them together using MPLS L2 VPN service.

First step is to create provider edges in Datacenter-1 and Datacenter-2. This
will be created by an administrator and can be used for multiple tenants.
This step can be automated by describing the provider edges in the plugin
driver configuration file.

Request

::
     POST /v2.0/mplsvpn/provider-edges
     Accept: application/json

     {
         "provider_edges": [
            {
             "name" : "DC1_Provider_Edge",
             "ip_address" : "192.168.4.1",
             "ip_version" : "4", // Other option: "6"
             "remote_flag" : "False"},

            {
             "name":"DC2_Provider_Edge",
             "ip_address": "192.168.5.1",
             "ip_version": "4", // Other option: "6"
             "remote_flag": "True"}

            ]

    }


Response

::
     {
         "provider_edges": [
           {
             "name": "DC1_Provider_Edge",
             "ip_address": "192.168.4.1",
             "ip_version": "4", // Other option: "6"
             "remote_flag": "False",
             "id":"<UUID value>"},

           {
             "name":"DC2_Provider_Edge",
             "ip_address": "192.168.5.1",
             "ip_version": "4", // Other option: "6"
             "remote_flag": "True",
             "id":"<UUID value>"}

     ]

     }


MPLS Tunnels can be created for each provider edge to provide the transport
connection between two provider edge nodes.

Request

::
     POST /v2.0/mplsvpn/mpls-tunnel
     Accept: application/json

     {
         "mpls_tunnel":
         {"name":"tunnel1",
         "provider_edge_id":"<UUID of provider edge>",
         "peer_ip_address": "192.168.16.1",
         "peer_ip_version": "4", // Other option: "6"
         "tunnel_options": {
         "backup": "frr", // Other options: Secondary
         "qos": "Gold", // Other options: Silver, Bronze
         "bandwidth": "10" // Unit: Gbps
         }

         }

     }

Response

::
     {
         "mpls_tunnel":
         {"name":"tunnel1",
         "id":"<UUID of mpls tunnel>",
         "provider_edge_id": "<UUID of provider edge>",
         "status":"DOWN",
         "tunnel_options": {
         "backup": "frr", // Other options: Secondary
         "qos": "Gold", // Other options: Silver, Bronze
         "bandwidth": "10" // Unit: Gbps
         }

         }

     }

Attachment circuits can be created for a given tenant to attach (or bridge) its
Neutron networks to the edge VPN.  The provider edge in each datacenter
specifies the local end point of the edge VPN.

Request

::
     POST /v2.0/mplsvpn/attachment-circuits
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
     PUT /v2.0/mplsvpn/attachment-circuits/{attachment-circuit-id}
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


Create mplsvpn with attachment circuits specifying full mesh option. Here
tunnels are created automatically if they are not available between the
provider edges. Also, all the attachment circuits created for a tenant could
be added for further automation.  For tunnels options: "qos",
"tunnel_backup", and "bandwidth" are optional parameters

Request

::
     POST /v2.0/mplsvpn/mplsvpns
     Accept: application/json

     {
         "mplsvpns":
         {"tenant_id": "<UUID of tenant>,
         "name":"Datacenter Interconnect",
         "vpn_id":<Integer VPN ID>,
         "type":"L2", // Other options: L3
         "mpls_tunnels":[
         "<UUID of mpls tunnel>",
         // More mpls tunnels are allowed]

         "attachment_circuits":[
         "<UUID of attachment circuit>",
         // More attachment circuits are allowed]

         }

      }

Response

::
     {
         "mplsvpns":
         {"id":"<UUID of mpls vpn service>",
         "tenant_id":"<UUID of the tenant for which VPN was created>",
         "status":"DOWN",
         // Can return "ACTIVE" when the service is up on
         // both the ends during read calls.

         // List of MPLS tunnels
         "mpls_tunnels":[
         "UUID of mpls tunnel"]

         // List of attachment circuits
         "attachment_circuits":[
         "UUID of attachment circuit"]

         }

     }

PUT call can be used to modify the attachment circuit list after the MPLS VPN
service has already been created.

Request

::
     PUT /v2.0/mplsvpn/mplsvpns
     Accept: application/json

     {
         "mplsvpn":
         {
         "attachment_circuits":[
         "<UUID of attachment circuit>",
         // More attachment circuits are allowed]
         "mpls_tunnels":[
         "<UUID of mpls tunnel>",
         // More mpls tunnels are allowed]

         }

    }

Response

::
     {
         "mplsvpns":
         {"id":"<UUID of mpls vpn service>",
         "tenant_id":"<UUID of the tenant for which VPN was created>",
         "status":"DOWN",
         // Can return "ACTIVE" when the service is up on
         // both the ends during read calls.
         "attachment_circuits":[
         "UUID of attachment circuit"]
         "mpls_tunnels":[
         "UUID of mpls tunnel"]

         }

     }

Following REST API calls allow the display of tunnels parameters.  This can be
used to display the operational status of the tunnel as well.

Request

::
     GET /v2.0/mplsvpn/mpls-tunnels
     Accept: application/json

Response

::

  {[
    { "tunnel":
        {
          "id": "<UUID value>",
          "name": "tunnel1",
          "peer_ip_address": "192.168.4.1",
          "peer_ip_version": "4", // Other option: "6"
          "provider_edge_id":"<UUID of provider edge>",
          "tunnel_options": {
          "backup": "frr", // Other options: Secondary
          "qos": "Gold", // Other options: Silver, Bronze
          "bandwidth": "10" // Unit: Gbps
          }
          "status": "UP",
    },
    { "tunnel":
        {
          "id": "<UUID value>",
          "name": "tunnel2",
          "peer_ip_address": "192.168.5.1",
          "peer_ip_version": "4", // Other option: "6"
          "provider_edge_id":"<UUID of provider edge>",
          "tunnel_options": {
          "backup": "frr", // Other options: Secondary
          "qos": "Silver", // Other options: Silver, Bronze
          "bandwidth": "20" // Unit: Gbps
          }
          "status": "DOWN",
    },
  ]}


Security Impact
---------------

None.

Notifications Impact
--------------------

None.

Other End User Impact
---------------------

End user can interact using the following commands:

The following command lists provider edges.

::
    mplsvpn-provideredge-list

The following command shows information of a given provider edge.

::
    mplsvpn-provideredge-show

The following command creates a provider edge

::
    mplsvpn-provideredge-create

The following command deletes a given provider edge.

::
    mplsvpn-provideredge-delete

The following command lists attachment circuits for a given tenant.

::
    mplsvpn-attachmentcircuit-list

The following command shows info of a given attachment circuit.

::
    mplsvpn-attachmentcircuit-show

The following command creates an attachment circuit.

::
    mplsvpn-attachmentcircuit-create

The following command updates the network list of an attachment circuit.

::
    mplsvpn-attachmentcircuit-update

The following command deletes an attachment circuit.

::
    mplsvpn-attachmentcircuit-delete

The following command lists MPLS VPN service config for a given tenant.

::
    mplsvpn-service-list

The following command shows information of a given MPLS VPN service.

::
    mplsvpn-service-show

The following command creates a MPLS VPN service.

::
    mplsvpn-service-create

The following command updates the attachment circuit list of a MPLS VPN
service.

::
    mplsvpn-service-update

The following command deletes a MPLS VPN service

::
    mplsvpn-service-delete

The following command lists tunnels for a given tenant.

::
    mplsvpn-tunnel-list

The following command shows information of a given tunnel.

::
    mplsvpn-tunnel-show

The following command creates an MPLS LSP tunnel.

::
    mplsvpn-tunnel-create

The following command updates an MPLS LSP tunnel.

::
    mplsvpn-tunnel-update

The following command deletes an MPLS LSP tunnel.

::
    mplsvpn-tunnel-delete

Performance Impact
------------------

None

IPv6 Impact
------------------

This spec addresses IPv6 scenarios and is expected to work in an IPv6
environment.

Other Deployer Impact
---------------------

None

Developer Impact
----------------

Developers use this framework to implement a service plugin to orchestrate an
edge VPN for a vendor specific device.  The developer may also provide
support to update an attachment circuit which allows bridging of a Neutron
network to an edge VPN.

Community Impact
----------------

It has been brought up in the last two OpenStack summits (Atlanta and Paris)
that there is a gap in Neutron when it comes to addressing the WAN
orchestration.  This attempt of defining the Edge-VPN use case addresses this
gap.

We have had several discussion on this in the Paris Kilo design summit.
Below are some of the links mentioning this discussion:

https://etherpad.openstack.org/p/neutron-kilo-lightning-talks
https://etherpad.openstack.org/p/mplsvpn

It was also discussed in the Kilo meetup in Paris as well.

https://etherpad.openstack.org/p/neutron-kilo-meetup-slots

Alternatives
------------

There is no alternate spec which proposes a framework to orchestrate an edge
VPN.  However, there are alternative specs which propose how a Neutron network
may be bridged to an edge VPN.


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

Work Items
----------

Each vendor will have to create an OpenStack service plugin which supports the
REST APIs proposed in this specification.  This plugin in turn makes calls to
the vendor specific device to provision different aspects of a per tenant edge
VPN.  An attachement circuit is created as part of a VPN service creation.  A
user may make a Neutron network part of the attachment circuit (via ML2 driver,
for example) thereby extending (bridging) this network across a VPN.

Currently, there is no open source reference implementation of an MPLS edge VPN
which can be used to simulate a PE device and can be used as a vendor
independent gate for the testing of the APIs described in this spec.

Dependencies
============

None


Testing
=======

The APIs will be tested by driving them through the OpenStack using a service
plugin which will directly talk to the device (a PE) which implements an edge
VPN functionality.  In order to test the bridging of a Neutron network to an
edge VPN, for example an L2 network, an ML2 mechanism driver will need to be
modified to make an "update" API call to update a Neutron network list in the
attachment circuit object.

Tempest Tests
-------------

None.

Functional Tests
----------------
Tests will be written to test the supported funcionality of all of the four
objects such as PEs, tunnels, attachement circuits, and an MPLS VPN service.
All of these objects support the standard CRUD operations.  The functional
tests will ensure the correctness of these operations.

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

Admin User guide will need to be updated with the introduction of the MPLS VPN
service.

Developer Documentation
-----------------------

The proposed APIs will need to be documented in the OpenStack Networking API
documentation.

References
==========

* https://etherpad.openstack.org/p/juno-vpnaas
* http://youtu.be/iv80K0WjcOQ
