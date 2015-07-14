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
VPN service using OpenStack.  This work will be accomplished as part of one of
the Neutron advanced services.  A vendor can implement a service plugin
conforming to this framework/APIs to allow orchestrating an edge VPN on its
physical device.  Once a VPN service is created, a Neutron network can be
bridged to this VPN.  There is a related spec which addresses how a Neutron
network can be bridged to an edge VPN.  That spec can be found at [2].

A framework and a set of networking APIs is introduced to aid orchestrating
edge VPN connectivity by leveraging Neutron APIs.  Following describes the
abstractions used to detail the proposed API.

Provider Edge (PE): Virtual concept to describe the provider edge devices
(single or cluster) in each datacenter that extends Neutron L2 networks (such
as a VLAN) or L3 networks (such as a subnet) using an MPLS or BGP VPN service
over WAN.

Attachment Circuit: Virtual concept to bridge a Neutron network to the edge
VPN.

Tunnel: Virtual concept to describe the connectivity between provider edges
(from one edge of a datacenter to another) that provides Qos, Backup-type,
and Bandwidth criteria.

Edge VPN: An Edge VPN service that provides connectivity between attachment
circuits in different datacenters.

Using these basic abstractions, the defined APIs provide operations to connect
two or more Neutron networks distributed in different datacenters using
the steps given below:

1. Cloud network administrator provisions an edge VPN for a given tenant by
creating an edge VPN service.  As part of an edge VPN service creation, the
network administrator creates a list of remote PEs and the tunnels to provide
connectivity to remote PEs.  Also, as part of an edge VPN service creation, an
attachment circuit is also created.  Initially, the Neutron network list is
an empty list inside the attachment circuit.

2.  When a user creates a Neutron network (for example, a VLAN), a tenant' edge
VPN's attachment circuit may be "updated" to bridge this network across an edge
VPN.  An API to achieve this described in the spec described above.

Service API extensions for Inter DC orchestration support are introduced
under the REST API URL: /v2.0/edgevpn/

Provider Edge (PE):
Operations on a PE object can only be performed by a network administrator.PE
objects define the datacenter border(edge) routers.  PE objects are specified
as part of an edge VPN service creation.  CRUD operations for provider edges
will be supported under /v2.0/edgevpn/provider-edges.

Attachment Circuit:
Attachment circuit object carries a list of Neutron networks.  Upon creation of
an edge VPN service, an attachment circuit with an empty list of Neutron
networks is created.  Once a user (tenant or an admin) creates a Neutron
network (L2 or an L3 - VLAN or a subnet), this network can be made part of the
edge VPN.  This is explained in the neutron-edge-vpn spec described at [2].
CRUD operations for attachment circuits will be supported under
/v2.0/edgevpn/attachment-circuits and described in [2].

Tunnel:
Tunnel related operations are available only to cloud network administrators.
Network administrators can create tunnel objects with remote PEs as egress end
points for these tunnels.  Tunnels may be shared across multiple edge VPNs.
This spec details one such tunnel type called operation.  Other tunnel types
may be introduced in future.  CRUD operations for MPLS tunnels will be
supported under /v2.0/edgevpn/mpls-tunnels.

Edge VPN:
Edge VPN related operations are available only to cloud network administrators.
CRUD operations for Edge VPN service will be supported under
ß/v2.0/edgevpn/edgevpnservice.

Data Model Impact
-----------------

None.

REST API Impact
---------------

The example below uses REST API to provision an MPLS L2 edge VPN service.

First step is to create provider edges in Datacenter-1 and Datacenter-2. This
will be created by an administrator and can be used for multiple tenants.
This step can be automated by describing the provider edges in the plugin
driver configuration file.

Request

::
     POST /v2.0/edgevpn/provider-edges
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
connection between two provider edge nodes.  For tunnels options: "qos",
"tunnel_backup", and "bandwidth" are optional parameters.

Request

::
     POST /v2.0/edgevpn/mpls-tunnel
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


Create edgevpn with initially empty attachment circuits list.

Request

::
     POST /v2.0/edgevpn/edgevpnservice
     Accept: application/json

     {
         "edgevpns":
         {"tenant_id": "<UUID of tenant>,
         "name":"Datacenter Interconnect",
         "l2-vpn_id":<string VPN ID - relevant in MPLS-L2 edge VPN type>,
         "l3-vpn-params": [{"route-distinguisher": "1:1",
         "import-route-target": "2:2",
         "export-route-target": "3:3" }] //Other options: auth, etc.
         "type":"MPLS-L2", // Other options: MPLS-L3, BGP, etc.
         "mpls_tunnels":[
         "<UUID of mpls tunnel>",
         // More mpls tunnels are allowed]

         // Other tunnel type encapsulation defined here

         "attachment_circuits":[
         "<UUID of attachment circuit>",
         // More attachment circuits are allowed]

         }

      }

Response

::
     {
         "edgevpns":
         {"id":"<UUID of edge vpn service>",
         "tenant_id":"<UUID of the tenant for which VPN was created>",
         "status":"DOWN",
         // Can return "ACTIVE" when the service is up on
         // both the ends during read calls.

         // List of MPLS tunnels
         "mpls_tunnels":[
         "UUID of mpls tunnel"]

         // Other tunnel types here

         // List of attachment circuits
         "attachment_circuits":[
         "UUID of attachment circuit"]

         }

     }

PUT call can be used to modify the attachment circuit list after the edge VPN
service has already been created.

Request

::
     PUT /v2.0/edgevpn/edgevpnservice
     Accept: application/json

     {
         "edgevpns":
         {
         "attachment_circuits":[
         "<UUID of attachment circuit>",
         // More attachment circuits are allowed]
         "mpls_tunnels":[
         "<UUID of mpls tunnel>",
         // More mpls tunnels are allowed]

         // Or other tunnel types ...

         }

    }

Response

::
     {
         "edgevpns":
         {"id":"<UUID of an edge vpn service>",
         "tenant_id":"<UUID of the tenant for which VPN was created>",
         "status":"DOWN",
         // Can return "ACTIVE" when the service is up on
         // both the ends during read calls.
         "attachment_circuits":[
         "UUID of attachment circuit"]
         "mpls_tunnels":[
         "UUID of mpls tunnel"]

         }

         // Or other tunnel types ...

     }

Following REST API calls allow the display of tunnels parameters.  This can be
used to display the operational status of the tunnel as well.

Request

::
     GET /v2.0/edgevpn/mpls-tunnels
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
    edgevpn-provideredge-list

The following command shows information of a given provider edge.

::
    edgevpn-provideredge-show

The following command creates a provider edge

::
    edgevpn-provideredge-create

The following command deletes a given provider edge.

::
    edgevpn-provideredge-delete

The following command lists edge VPN service config for a given tenant.

::
    edgevpn-service-list

The following command shows information of a given edge VPN service.

::
    edgevpn-service-show

The following command creates a edge VPN service.

::
    edgevpn-service-create

The following command updates the attachment circuit list of a edge VPN
service.

::
    edgevpn-service-update

The following command deletes a edge VPN service

::
    edgevpn-service-delete

The following command lists tunnels for a given tenant.

::
    edgevpn-mpls-tunnel-list

The following command shows information of a given tunnel.

::
    edgevpn-mpls-tunnel-show

The following command creates an  LSP tunnel.

::
    edgevpn-mpls-tunnel-create

The following command updates an MPLS LSP tunnel.

::
    edgevpn-mpls-tunnel-update

The following command deletes an MPLS LSP tunnel.

::
    edgevpn-mpls-tunnel-delete

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
edge VPN for a vendor specific device.

Community Impact
----------------

It has been brought up in the last three OpenStack summits (Atlanta, Paris,
and Vancouver) that there is a gap in Neutron when it comes to addressing the
WAN orchestration.  This attempt of defining the Edge-VPN use case addresses
this gap.

We have had several discussion on this in the Paris Kilo design summit as well
as Vancouver Liberty summit. Below are some of the links mentioning this
discussion:

https://etherpad.openstack.org/p/neutron-kilo-lightning-talks
https://etherpad.openstack.org/p/edgevpn

It was also discussed in the Kilo meetup in Paris as well.

https://etherpad.openstack.org/p/neutron-kilo-meetup-slots

and Vancouver summit at:

https://etherpad.openstack.org/p/YVR-neutron-vpnaas

Alternatives
------------

There is no alternate spec which proposes a framework to orchestrate an edge
VPN.  However, there are alternative specs which propose how a Neutron network
may be bridged to a BGP VPN and can be found at [5].


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

Each vendor will have to create an OpenStack service plugin which supports the
REST APIs proposed in this specification.  This plugin in turn makes calls to
the vendor specific device to provision different aspects of a per tenant edge
VPN.

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
VPN functionality.

Tempest Tests
-------------

None.

Functional Tests
----------------
Tests will be written to test the supported functionality of all of the four
objects such as PEs, tunnels, attachment circuits, and an edge VPN service.
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

Admin User guide will need to be updated with the introduction of the edge VPN
service.

Developer Documentation
-----------------------

The proposed APIs will need to be documented in the OpenStack Networking API
documentation.

References
==========

.. [1] Edge VPN stackforge
    https://github.com/stackforge/networking-edge-vpn

.. [2] Neutron extension for Edge VPN


.. [3] Interconnecting Data Centers for WAN orchestration
    http://youtu.be/iv80K0WjcOQ
    https://www.youtube.com/watch?v=KwW0dtvHIgQ
    https://www.youtube.com/watch?v=q5z0aPrUZYc

.. [4] Different VPN Flavors in neutron
   https://etherpad.openstack.org/p/vpn-flavors

.. [5] Neutron Extension for BGPVPN
   https://review.openstack.org/#/c/177740/

.. [6] L2 and L3 VPN references
    https://www.ietf.org/rfc/rfc4664.txt
    https://www.ietf.org/rfc/rfc4364.txt