---
title: "Part 4 — Networking"
parent: Theory
nav_order: 4
---

# Part 4 — Networking
{: .no_toc }

1. TOC
{:toc}

{: .objectives }
> 2.3 all of networking: VPCs and subnets, Shared VPC, peering, VPC firewall rules, Cloud NGFW policies and secure tags, VPN and Interconnect, load balancers, Network Service Tiers · 3.3 resizing subnets, static IPs, custom static routes, Cloud DNS, Cloud NAT, managing firewall rules and policies · 3.4 VPC Flow Logs and firewall logs

Every VM, GKE node, Cloud SQL private IP and serverless connector lives on a VPC. The exam's networking items are
mostly one of four questions: *can these two things reach each other*, *who is allowed to*, *how does traffic
get in or out*, and *which load balancer*. This part answers them in that order.

<a id="s4-1"></a>

## 4.1 The VPC model

| Fact | Consequence |
|:----------------------------------------------|:--------------------------------------------------------------|
| A **VPC network is global** | One VPC spans all regions; VMs in different regions talk over internal IPs with no VPN or peering |
| **Subnets are regional** | A subnet exists in one region, across all its zones |
| VPCs are **isolated from each other** by default, even in one project | Connecting two needs peering, a VPN, NCC or Shared VPC ([§4.5](#s4-5)) |
| Firewall rules and routes belong to the **network** | They are global resources, scoped by targets |
| **Auto mode** creates one `/20` subnet per region from `10.128.0.0/9` | Convenient, overlapping with every other auto-mode VPC |
| **Custom mode** creates no subnets — you define them | **The production answer.** Auto mode can convert to custom, never back |

The **`default` network** in a new project is an auto-mode VPC with permissive firewall rules (internal traffic,
SSH, RDP, ICMP from anywhere). Production work starts on a custom-mode VPC, and the org policy
`compute.skipDefaultNetworkCreation` stops the default network appearing at all.

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| Custom-mode VPC | `gcloud compute networks create vpc-prod --subnet-mode=custom` |
| Subnet with Private Google Access | `gcloud compute networks subnets create web-euc2 --network=vpc-prod --region=R --range=10.10.0.0/20 --enable-private-ip-google-access` |

<a id="s4-2"></a>

## 4.2 Subnets and IP ranges

- A subnet has one **primary IPv4 range** (RFC 1918 or other private ranges) and optional **secondary ranges** —
  used by GKE for Pod and Service IPs (alias IPs).
- <mark markdown="span">**Four addresses in every primary range are reserved**</mark>: network, default gateway, second-to-last, and broadcast.
- Subnet ranges in one VPC, and across peered VPCs, **must not overlap**.
- Subnets can be **dual-stack** (IPv4 + IPv6) or IPv6-only (*recognise*).

### Secondary ranges and VPC-native GKE

A **secondary range** is an extra, named IPv4 range on a subnet, used for **alias IPs**: addresses a VM's interface
owns besides its primary IP. A **VPC-native GKE cluster** (the default) is built on them:

| Range | From | Used for |
|:------------------------------|:----------------------------------|:------------------------------------------------|
| Subnet **primary** range | The subnet | **Node** IPs |
| **Pod** range | A subnet **secondary** range | Each node gets a slice (a `/24` for 110 Pods per node) |
| **Service** range | Another secondary range | ClusterIP addresses |
| **Additional Pod ranges** | More secondary ranges, added later | Pod IPs for **new node pools** when the first Pod range is full |

<mark markdown="span">**A subnet can have up to 170 secondary IPv4 ranges**</mark> (a hard limit, *verify*), and
GKE takes its Pod ranges from them. A cluster starts with **one** Pod range and **one** Service range; when the Pod
range runs out you **add more Pod ranges** (*discontiguous multi-Pod CIDR*), on Autopilot (1.26+) and Standard
clusters, without recreating the cluster. Existing node pools keep their original range; **new node pools** use the
new one. On Standard you can also give one node pool its own range with `--pod-ipv4-range`. Routes-based clusters
support none of this, which is one more reason VPC-native is the default.

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| Add a secondary range to a subnet | `gcloud compute networks subnets update gke-euw4 --region=R --add-secondary-ranges=pods-2=10.64.0.0/14` |
| Give the cluster the new Pod range | `gcloud container clusters update shop --location=R --additional-pod-ipv4-ranges=pods-2` |
| A node pool on its own Pod range (Standard) | `gcloud container node-pools create pool-2 --cluster=shop --location=R --pod-ipv4-range=pods-2` |

{: .trap }
> **"Out of Pod addresses" is not "recreate the cluster".** The subnet's primary range limits **nodes**; the Pod
> secondary range limits **Pods**. Expanding the primary range does not help a full Pod range. Add a Pod range and a
> new node pool, or lower max Pods per node on a **new** node pool (it cannot be changed in place).

### Resizing a subnet — expand only

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| Grow a full subnet (never shrink) | `gcloud compute networks subnets expand-ip-range web-euc2 --region=R --prefix-length=19` |

<mark markdown="span">**A subnet's primary range can be expanded (a shorter prefix), never shrunk**</mark>, without downtime, as long as the
larger range does not overlap anything. *"The subnet is out of addresses"* is `expand-ip-range`; *"we made it too
big"* has no fix except a new subnet and migration. Auto-mode subnets can grow up to `/16`.

{: .trap }
> **Adding a subnet versus expanding one.** More addresses *in the same region for the same workloads* —
> expand. A **new region**, or a separate range for a different tier — create a new subnet in the existing VPC
> (`subnets create`). Creating a new VPC is almost never the answer to "out of IPs".

<a id="s4-3"></a>

## 4.3 Routes

Every packet leaving a VM is matched against the VPC's routing table.

| Route type | Created by | Notes |
|:----------------------|:------------------------------|:------------------------------------------------------------|
| **Subnet routes** | Automatically, per subnet range | Cannot be deleted; make every subnet reachable across the VPC |
| **Default route** `0.0.0.0/0` → default internet gateway | Automatically | Priority 1000. Delete it to cut all internet egress paths |
| **Custom static routes** | You | Destination, next hop, priority, optional **network tags** to apply to only some VMs |
| **Dynamic routes** | **Cloud Router** via BGP | Learned from VPN or Interconnect peers; regional or global per the VPC's routing mode |

**Next hops for a custom static route:** a VM instance (e.g. a firewall or NAT appliance), an internal IP, an
**internal passthrough Network Load Balancer** (for highly available appliances), a Classic VPN tunnel, or the
default internet gateway.

**Selection:** the **most specific prefix** wins; among equal prefixes, the **lowest priority number** wins; equal
priority spreads traffic (ECMP). Subnet routes cannot be overridden by a less specific custom route.

### Dynamic routing mode: regional or global

Every VPC has one **dynamic routing mode**. It decides **which regions** can use the routes a Cloud Router learns
over BGP, and which subnets the Cloud Router advertises back.

| | **Regional** (the default) | **Global** |
|:----------------------------------|:----------------------------------|:----------------------------------|
| Routes learned by a Cloud Router in `europe-west4` | Programmed **only in `europe-west4`** | Programmed in **every region** of the VPC |
| Subnets the Cloud Router advertises to on-premises | Only subnets **in its region** | **All** subnets of the VPC |
| VMs in `us-central1` reach on-premises through the `europe-west4` tunnel | **No** | **Yes**, with an inter-region cost added |
| Typical use | One region, or a VPN and Cloud Router per region | One hybrid connection serving a multi-region VPC |

In global mode a route learned in another region gets an **inter-region cost** added to its priority, and subnets
from other regions are advertised with the base priority **plus** that cost (as the BGP MED). So the local
connection is preferred where you have one, and the remote one is the fallback. The mode is a property of the
**network**, set at creation or changed at any time without downtime.

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| Make learned routes usable from every region | `gcloud compute networks update vpc-prod --bgp-routing-mode=global` |
| See the routes a Cloud Router learned | `gcloud compute routers get-status rtr-euw4 --region=europe-west4` |

{: .tip }
> **The symptom names the fix.** *"VMs in the VPN's region reach on-premises, VMs in another region of the same VPC
> do not"* is the routing mode. Firewall rules do not depend on region, and a second VPN is unnecessary.

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| Send a range through an appliance VM, for tagged VMs only | `gcloud compute routes create to-onprem --network=vpc-prod --destination-range=172.16.0.0/12 --next-hop-instance=fw-1 --tags=needs-inspection --priority=800` |

{: .new-title }
> New in the June 2026 guide — custom static routes
>
> The guide now names *adding custom static routes*. The usual stems: send traffic for a range through a
> **network virtual appliance** (next hop instance or, for HA, an internal passthrough NLB); route only **tagged**
> VMs through it; or give VMs with a special tag a **higher-priority** path. Remember that a route only *forwards*
> — the appliance VM also needs **IP forwarding** enabled (`--can-ip-forward` at creation), and firewall rules
> still apply.

<a id="s4-4"></a>

## 4.4 Firewall rules and Cloud NGFW policies

Firewalls are **distributed and stateful**: they are enforced at each VM's network interface, and return traffic
of an allowed connection is allowed automatically. Google Cloud's firewall product is now called **Cloud Next
Generation Firewall (Cloud NGFW)**, and it has two kinds of rule containers.

### VPC firewall rules — the classic kind

| Component | Values |
|:----------------------|:----------------------------------------------------------------------|
| Direction | **Ingress** or **egress** |
| Action | Allow or deny |
| **Priority** | **0–65535, lower wins**; default **1000**. Ties: deny beats allow |
| Targets | All instances · **network tags** · **service accounts** |
| Source (ingress) / destination (egress) | IP ranges; for ingress also source tags or source service accounts |
| Protocols and ports | `tcp:443`, `udp:53`, `icmp`, or all |
| Logging | Off by default; per rule ([§4.11](#s4-11)) |

**Implied rules**, present in every VPC and invisible in the list: **allow all egress** and **deny all ingress**,
both at the lowest priority (65535). Some traffic is outside the firewall's control altogether: the metadata
server (`169.254.169.254`) is always reachable, and **egress to TCP port 25 on external addresses is always
blocked**.

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| HTTPS from anywhere to VMs tagged `web` | `gcloud compute firewall-rules create allow-web --network=vpc-prod --direction=INGRESS --action=ALLOW --rules=tcp:443 --source-ranges=0.0.0.0/0 --target-tags=web` |
| Load-balancer health checks to one service account's VMs | `... --rules=tcp:8080 --source-ranges=130.211.0.0/22,35.191.0.0/16 --target-service-accounts=SA_EMAIL` |
| Record what a rule matches | `gcloud compute firewall-rules update allow-web --enable-logging` |

{: .watch }
> **Target by network tag versus by service account.** A **network tag** is a string that anyone able to edit the VM
> can add — adding `web` silently opens the VM to the web rule. A **target service account** can only be changed
> by someone who may attach that service account (and only while the VM is stopped). *"Ensure only the web tier's
> VMs receive this traffic, even if developers edit instances"* points at service accounts (or secure tags).

### Firewall policies — hierarchical, global and regional

| Policy | Attached to | Use |
|:----------------------------------|:------------------------------|:----------------------------------------------------|
| **Hierarchical firewall policy** | Organization or folder | Guardrails that apply to every VPC beneath — *"block this range everywhere"*, *"always allow the security scanner"* |
| **Global network firewall policy** | One VPC (all regions) | Modern replacement for VPC firewall rules; supports secure tags, FQDNs, geolocation, address groups |
| **Regional network firewall policy** | One VPC in one region | Region-specific rules |

Policy rules add a fourth action to allow and deny: **`goto_next`**, which hands evaluation down to the next level
(for example, an org policy delegating a decision to projects). Standard and Enterprise features add
**`apply_security_profile_group`** for intrusion prevention.

**Evaluation order**, top to bottom, stopping at the first allow or deny:

```
1. Hierarchical policy at the organization  -->  2. hierarchical policies on folders (top down)
3. VPC firewall rules and the global network firewall policy (order configurable per network)
4. Regional network firewall policy          -->  5. implied rules (allow egress, deny ingress)
```

{: .new-title }
> New in the June 2026 guide — Cloud NGFW and secure tags
>
> **Secure tags** are resource-manager tags created with the firewall purpose and bound to a VPC. You attach tag
> *values* to VM instances (or GKE node pools), and firewall-**policy** rules select sources and targets by those
> values. Because attaching a tag value needs an IAM role (`roles/resourcemanager.tagUser` on the value), **a
> developer cannot open a VM to a rule simply by editing it** — the property network tags lack. And the mapping
> runs one way only: <mark markdown="span">**network tags work only in VPC firewall rules; firewall policies use secure tags, not network
> tags.**</mark>
>
> **Cloud NGFW tiers:** **Essentials** — the foundational stateful firewall, policies, secure tags (no extra
> charge); **Standard** — adds FQDN objects, geolocation and threat-intelligence lists (charged on evaluated
> traffic); **Enterprise** — adds intrusion detection and prevention with TLS inspection, via firewall endpoints
> and security profiles.


**Operating policies.** Move an existing VPC's rules into a policy with the **migration tool** (it keeps evaluation order; rules using
network tags need tag-to-secure-tag mapping first), then **associate** the policy — a new policy does nothing until
associated. To record what a policy rule matches, set **`--enable-logging`** on that rule; flow logs sample and do not name the rule.

<a id="s4-5"></a>

## 4.5 Shared VPC and VPC Network Peering

| Need | Product | The deciding property |
|:----------------------------------------------|:------------------------|:----------------------------------------------------|
| **One network used by many projects**; a central team owns subnets, routes and firewalls; app teams keep their own projects, IAM and billing | **Shared VPC** | Host project + service projects, **one** network |
| **Two separate VPCs**, private connectivity, no gateways | **VPC Network Peering** | Native, full bandwidth, **non-transitive** |
| **Many VPCs** (and on-premises) in hub-and-spoke, with transitivity | **Network Connectivity Center** | A hub that makes spokes reach each other |

### Shared VPC

- The **host project** owns the VPC; **service projects** are attached and create resources in its subnets.
  Resources (and their bills) belong to the service project; the network belongs to the host.
- Requires an **organization**. A service project attaches to **one** host; a host cannot also be a service project.
- **Roles:** the **Shared VPC Admin** (`roles/compute.xpnAdmin`, granted at the org or a folder) enables hosts and
  attaches service projects. **Network User** (`roles/compute.networkUser`) on the host project — or on
  **individual subnets** for least privilege — lets service-project developers put resources in those subnets.

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| Make the host project | `gcloud compute shared-vpc enable HOST_PROJECT` |
| Attach a service project | `gcloud compute shared-vpc associated-projects add SVC_PROJECT --host-project=HOST_PROJECT` |
| Least privilege: one subnet only | `gcloud compute networks subnets add-iam-policy-binding web-euc2 --region=R --member=group:team-a@example.com --role=roles/compute.networkUser` |

### VPC Network Peering

- **Both sides must create** the peering before it becomes active; the networks can be in different projects or
  organizations.
- **Non-transitive:** if A peers with B and B with C, <mark markdown="span">**A cannot reach C**</mark>. Nor can a peer use your VPN or
  Interconnect to reach your on-premises network, unless custom routes are exported and imported.
- **No overlapping subnet ranges** between peers.
- **Subnet routes are exchanged automatically**; custom (static and dynamic) routes only if you enable export and
  import. **Firewall rules are not exchanged** — each side still controls its own ingress.
- Peering is also how **private services access** works (Cloud SQL, Memorystore private IP, [§4.7](#s4-7)), which is why
  those services inherit the non-transitivity.

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| Peer two VPCs — run it on **both** sides | `gcloud compute networks peerings create a-to-b --network=vpc-a --peer-project=PB --peer-network=vpc-b` |

{: .tip }
> **When a stem forgives a weakness, it is naming the product that has it.** *"Transitive routing is not required"*
> points straight at peering. *"No gateways or tunnels in the path"* eliminates VPN. *"A central network team must
> own the firewall rules"* is Shared VPC, not peering.

<a id="s4-6"></a>

## 4.6 Hybrid connectivity: VPN, Interconnect, Cloud Router

| Product | Path | Capacity | SLA | Right when |
|:----------------|:----------------|:----------------------|:------------------|:----------------------------|
| **HA VPN** | IPsec over the internet | ~3 Gbps per tunnel (*verify*); add tunnels | **99.99%** with two interfaces and two tunnels | Encrypted, quick to set up, moderate bandwidth |
| Classic VPN | IPsec, one interface | Same per tunnel | 99.9% | Legacy; static routing |
| **Dedicated Interconnect** | Your own circuits in a Google **colocation facility** | 10 or 100 Gbps circuits (400 Gbps in some locations, *verify*) | 99.9 / 99.99% by topology | High, steady bandwidth; you can reach a colo |
| **Partner Interconnect** | Through a service provider | 50 Mbps – 50 Gbps per attachment | 99.9 / 99.99% | You **cannot** reach a colo, or need less than 10 Gbps |
| **Cross-Cloud Interconnect** | Dedicated circuits to AWS, Azure, OCI, Alibaba | 10 / 100 Gbps | 99.9 / 99.99% | Private link to another cloud |
| Direct / Carrier Peering | To Google's edge | — | None | Reaching **Google public services** (Workspace, public APIs) — **not your VPC** |

**Cloud Router** is the regional BGP speaker for your VPC: it learns on-premises prefixes over VPN or
Interconnect and advertises your subnets back. HA VPN requires it. With the VPC's **dynamic routing mode set to
global**, routes learned in one region are usable from all regions ([§4.3](#s4-3)).

### BGP in one page

**BGP (Border Gateway Protocol)** is the routing protocol networks use to tell each other which IP prefixes they can
reach. It is how the internet's providers exchange routes, and it is how Cloud Router and your on-premises router
exchange them over a VPN tunnel or an Interconnect attachment. You never type routes for the other side: each router
**advertises** its prefixes, and the other **learns** them.

| Term | Meaning on Google Cloud |
|:----------------------------------|:------------------------------------------------------------------|
| **Autonomous system (AS), ASN** | A network under one routing policy, identified by a number. Cloud Router needs a **private ASN**: `64512–65534` or `4200000000–4294967294`. Your on-premises ASN may be public or private, but must differ |
| **BGP session (peer)** | A TCP session between two routers. On HA VPN and Interconnect each session uses a pair of **link-local addresses** from `169.254.0.0/16` |
| **Advertised routes** | What Cloud Router announces to on-premises: by default the **subnets** (per the routing mode); with **custom advertisement** also extra ranges, such as `199.36.153.8/30` for Private Google Access from on-premises |
| **Learned routes** | What on-premises announces. They become **dynamic routes** in the VPC |
| **MED / advertised route priority** | A preference value sent with each route; **lower is preferred**. Different priorities on two tunnels make one active and the other standby |
| **BFD** | Optional fast failure detection on a session |

Why it matters: with BGP, a failed tunnel's routes are **withdrawn** and traffic moves to the surviving tunnel by
itself, which is why HA VPN's 99.99% SLA requires **dynamic (BGP) routing**, and why a new on-premises subnet
appears in Google Cloud without anyone editing a route. Classic VPN can use static routes; nothing else hybrid does.

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| A Cloud Router with a private ASN | `gcloud compute routers create rtr-euw4 --network=vpc-prod --region=europe-west4 --asn=65010` |
| Also advertise the Private Google Access range | `gcloud compute routers update rtr-euw4 --region=europe-west4 --advertisement-mode=custom --set-advertisement-groups=all_subnets --set-advertisement-ranges=199.36.153.8/30` |

{: .note }
> <mark markdown="span">**Interconnect traffic is not encrypted by default.**</mark> Options: **MACsec** on Dedicated Interconnect, or **HA VPN
> over Cloud Interconnect** for IPsec on top of the private circuit. *"Private, high-bandwidth and encrypted"* is one
> of those two.


{: .tip }
> **Do the bandwidth sum first.** *"2 Gbps, encrypted, next week"* — HA VPN. *"20 Gbps sustained, we are in an
> Equinix facility where Google is present"* — Dedicated Interconnect. *"5 Gbps, our data centre is nowhere near a
> Google facility"* — Partner Interconnect.

<a id="s4-7"></a>

## 4.7 Private access to Google and to services

| Need | Mechanism | How |
|:----------------------------------------------|:----------------------------------|:----------------------------------------------|
| VMs **without external IPs** reach Google APIs (Cloud Storage, BigQuery...) | **Private Google Access** | A **per-subnet** setting |
| **On-premises** hosts reach Google APIs privately over VPN / Interconnect | Private Google Access for on-premises | `private.googleapis.com` (`199.36.153.8/30`, most APIs) or `restricted.googleapis.com` (`199.36.153.4/30`, only APIs that support VPC Service Controls), via on-premises DNS and a Cloud Router **custom advertisement** of that range |
| Reach Google APIs at an **internal IP you choose** in your VPC | **Private Service Connect endpoint** for Google APIs | A PSC forwarding rule |
| Private IP for **Cloud SQL, Memorystore, Filestore, AlloyDB** | **Private services access** | Allocate a range; Google peers a service-producer VPC to yours |
| Consume a **specific service** (another team's, a partner's, a Google service) by internal IP, no peering | **Private Service Connect** (consumer endpoint → producer service attachment) | No overlapping-range problems, no transitivity issues |
| **Cloud Run / functions** reach resources on your VPC | **Direct VPC egress** (recommended) or a Serverless VPC Access connector | Per service |

{: .watch }
> **Private Google Access versus Cloud NAT.** <mark markdown="span">PGA reaches **Google APIs only**. Cloud NAT reaches **the internet**</mark>
> (package mirrors, a partner API). A private VM that needs only Cloud Storage and BigQuery needs PGA and nothing
> else; one that must `apt-get` from the internet needs Cloud NAT.

<a id="s4-8"></a>

## 4.8 IP addresses, Cloud DNS and Cloud NAT

### Addresses

| Type | Behaviour |
|:----------------------------------|:----------------------------------------------------------------|
| **Ephemeral** internal or external | Assigned at creation; an ephemeral **external** IP is released when the VM **stops** |
| **Static external, regional** | Reserved; for VMs and regional load balancers. **Billed while reserved and unused** |
| **Static external, global** | For global load balancers (Premium Tier only) |
| **Static internal** | A reserved address from a subnet — *"the licence server must always be `10.0.3.21`"* |

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| Static IP for a global load balancer | `gcloud compute addresses create lb-ip --global` |
| Keep a VM's current ephemeral IP | `gcloud compute addresses create keep-me --addresses=34.118.1.2 --region=R` |
| Reserve a fixed internal IP | `gcloud compute addresses create lic-ip --region=R --subnet=app-euc2 --addresses=10.0.3.21` |

{: .trap }
> **Private ranges can never be external IPs.** `10.x`, `172.16--31.x`, `192.168.x` are RFC 1918; an option
> assigning one as a VM's *external* address is invalid on sight.

### Cloud DNS

| Zone or policy | Does |
|:--------------------------------------|:----------------------------------------------------------------------|
| **Public zone** | Authoritative DNS on the internet for your domain; **DNSSEC** available; 100% SLA |
| **Private zone** | Names visible only to the **VPC networks you authorise** — `db.internal.kestrel.io` |
| **Forwarding zone** | Sends queries for a domain (e.g. `corp.local`) to **on-premises resolvers** |
| **Peering zone** | Resolves a domain using **another VPC's** DNS configuration |
| **Inbound server policy** | Gives the VPC resolver an address **on-premises clients can query** — so on-prem can resolve private zones |
| Response policy | Overrides answers for specific names — e.g. steer `*.googleapis.com` to private endpoints |

VMs also get **internal DNS** automatically: `VM_NAME.ZONE.c.PROJECT_ID.internal`.


{: .tip }
> <mark markdown="span">**Direction decides the DNS object.**</mark> Cloud VMs must resolve **on-premises** names — a **forwarding zone**.
> On-premises hosts must resolve **Cloud private** names — an **inbound server policy**.

### Cloud NAT

**Cloud NAT gives resources without external IPs outbound connectivity to the internet, and nothing inbound.** It
is a **regional**, software-defined service (no proxy VM, no single point of failure) configured on a **Cloud
Router**. It serves VMs, **private GKE nodes**, and serverless workloads using Direct VPC egress.

| Setting | Why it matters |
|:----------------------------------|:------------------------------------------------------------------|
| **Automatic vs manual (static) NAT IPs** | Manual IPs give a **fixed egress address** a partner can allow-list |
| Ports per VM | Too few ports cause dropped connections under load (*"OUT_OF_RESOURCES"*) |
| NAT logging | Translations and drops, in Cloud Logging |
| Public NAT vs Private NAT | Private NAT translates between VPCs or to on-premises with overlapping ranges |

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| Cloud NAT for one region | `gcloud compute routers create nat-router --network=vpc-prod --region=R`, then `gcloud compute routers nats create nat-1 --router=nat-router --region=R --nat-all-subnet-ip-ranges --auto-allocate-nat-external-ips` |

<a id="s4-9"></a>

## 4.9 Load balancing

Four questions choose every load balancer: **external or internal · global or regional · HTTP(S) or any TCP/UDP
· proxy (terminates) or passthrough (preserves the client IP)**.

| Load balancer | Layer | Scope | Traffic | Client IP at backend | Typical use |
|:------------------------------|:-------|:----------------|:----------------|:--------------|:----------------------------|
| **Global external Application LB** | 7 | Global, **one anycast IP** | HTTP(S), HTTP/2, gRPC | No (`X-Forwarded-For`) | Public web app across regions; Cloud CDN, Cloud Armor |
| Regional external Application LB | 7 | Regional | HTTP(S) | No | Public HTTP in one region; Standard Tier possible |
| **Internal Application LB** (regional or cross-region) | 7 | Internal | HTTP(S) | No | Internal microservices, path routing |
| External proxy Network LB | 4 | Global or regional | TCP, SSL | No | Non-HTTP TCP needing TLS offload or global reach |
| Internal proxy Network LB | 4 | Internal | TCP | No | Internal TCP with a proxy |
| **External passthrough Network LB** | 4 | Regional | TCP, **UDP**, ESP, ICMP | **Yes** | Games, UDP, protocols needing the real client IP |
| **Internal passthrough Network LB** | 4 | Regional, internal | TCP, **UDP** | **Yes** | Internal TCP/UDP; next hop for appliances ([§4.3](#s4-3)) |

Envoy-based load balancers, such as the internal Application Load Balancer and the regional external one, need a
**proxy-only subnet** in each region they use (`--purpose=REGIONAL_MANAGED_PROXY`, *verify*): the proxies take
their addresses from it, so backend firewall rules must allow that range.

{: .key }
> **Three eliminations answer most load-balancer items.** *UDP* or *not HTTP* removes every Application LB.
> *Must see the client's source IP* removes every proxy — it is a **passthrough** LB. *One IP worldwide with
> failover between regions* is the **global external Application LB** (Premium Tier).

**The parts of an Application LB**, which the exam names: a **forwarding rule** (IP and port) → a **target proxy**
(HTTP or HTTPS, holding the **certificate**) → a **URL map** (host and path rules) → **backend services** (with
health checks, session affinity, Cloud CDN, Cloud Armor) → **backends**:

| Backend type | Points at |
|:----------------------------------|:------------------------------------------------------------------|
| **Instance group** (managed or unmanaged) | VMs |
| **Zonal NEG** | Pod or VM IP:port — GKE **container-native load balancing** |
| **Serverless NEG** | **Cloud Run**, Cloud Run functions, App Engine — the way to put them behind a global LB |
| Internet NEG | An external endpoint |
| Hybrid NEG | On-premises or other-cloud endpoints over hybrid connectivity |
| Private Service Connect NEG | A published service or Google API |

{: .trap }
> <mark markdown="span">**Health checks come from Google's probe ranges, `35.191.0.0/16` and `130.211.0.0/22`.**</mark> If no firewall rule allows
> them to the backends' serving port, every backend is marked unhealthy and the load balancer returns errors even
> though the VMs are fine. *"All backends unhealthy right after creating the LB"* is almost always this rule.

**Certificates:** **Google-managed certificates** (provisioned and renewed automatically once DNS points at the
LB, or via DNS authorisation in **Certificate Manager**) versus self-managed certificates you upload and renew.

<a id="s4-10"></a>

## 4.10 Network Service Tiers, Cloud CDN and Cloud Armor

| Tier | Path | Scope | Cost | Right when |
|:----------------|:----------------------------------------------|:------------------|:--------|:----------------------------|
| **Premium** (default) | Traffic enters and leaves **Google's backbone** at the edge closest to the user | **Global** — required for global LBs and global anycast IPs | Higher | Performance, global reach |
| **Standard** | Traffic rides the **public internet** to and from the region | **Regional only** | Lower egress price | Cost-sensitive, single-region, latency-tolerant |

Set per project default (`gcloud compute project-info update --default-network-tier=STANDARD`) or per resource on
IP addresses and forwarding rules.

{: .tip }
> *"Lowest network cost, users in one region, performance not critical"* — **Standard Tier**. *"Single anycast IP
> for users on three continents"* — **Premium Tier** with a global external Application LB; Standard Tier cannot do
> it.

**Cloud CDN** caches responses at Google's edge; it is enabled on a **backend service or backend bucket** of a
global external Application LB. **Cloud Armor** is a WAF and DDoS policy attached to backend services of external
load balancers: preconfigured OWASP rules, IP and geo allow/deny, rate limiting, bot management, and **Adaptive
Protection** (ML-detected layer-7 attacks).

<a id="s4-11"></a>

## 4.11 Seeing the network: flow logs, firewall logs, Connectivity Tests

| Tool | Records or does | Use it for |
|:----------------------------------|:------------------------------------------------------------|:------------------------------|
| **VPC Flow Logs** | A **sample** of network flows (5-tuple, bytes, packets, latency, metadata), enabled per subnet or at network/attachment level | Traffic analysis, forensics, capacity and cost investigations |
| **Firewall Rules Logging** | One record per connection **allowed or denied by a specific rule** you enabled logging on | *"Is my rule matching? Which rule blocked this?"* |
| **Connectivity Tests** (Network Intelligence Center) | Simulates a packet from A to B through routes, firewalls, peering, VPN; can also probe the live data plane | *"Why can't VM A reach B?"* without touching production |
| Firewall Insights | Shadowed, overly permissive and unused rules | Cleaning up rules |
| Network Topology / Performance Dashboard | Visual topology; Google-measured latency and loss | Understanding and baselining |

{: .watch }
> **Flow logs versus firewall logs.** Flow logs say **what traffic flowed** (sampled, per subnet). Firewall logs say
> **which rule decided** a connection. The **implied** deny-ingress rule cannot be logged — to log denied traffic,
> create an explicit low-priority deny rule with logging on. Both land in Cloud Logging and cost ingestion ([§9.7](09-operations.md#s9-7)).

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| Turn on VPC Flow Logs for a subnet | `gcloud compute networks subnets update web-euc2 --region=R --enable-flow-logs` |

### More to recognise

- **Firewall operations.** An **address group** is a reusable list of IP ranges for policy rules. **Cloud NGFW
  Enterprise** adds intrusion prevention: a firewall endpoint, a security profile group and a rule with
  `apply_security_profile_group`. A firewall-purpose tag key is scoped to **one VPC** by its purpose data.
  `gcloud compute instances network-interfaces get-effective-firewalls` lists every rule and policy that applies
  to one VM.
- **Routing.** A **policy-based route** matches on **source** range and protocol and forwards to an internal
  passthrough load balancer — static routes match destinations only. A static route with **`--next-hop-ilb`**
  spreads over healthy appliances. Peered VPCs share **custom** (including VPN-learned) routes only when one side
  exports and the other imports them.
- **Connectivity.** **Network Connectivity Center** with **VPC spokes** gives any-to-any connectivity among many
  VPCs (peering is not transitive). **HA VPN to AWS** uses two AWS VPN connections and **four tunnels** for the
  99.99% topology. A **cross-region internal Application Load Balancer** fails internal traffic over between
  regions; a global external ALB with a **serverless NEG per region** does the same for Cloud Run.
- **Addresses and NAT.** Global load balancers need a **global** static address. A full GKE Pod range is extended
  by adding another secondary range and new node pools with `--pod-ipv4-range`. **Dynamic port allocation** on
  Cloud NAT fixes port exhaustion on a few busy VMs.

<a id="s4-12"></a>

## 4.12 Part 4 recall card

| Prompt | Answer |
|:------------------------------------------------|:--------------------------------------------------------|
| One VPC across regions? | Yes — VPC global, subnets regional |
| Subnet out of addresses | `subnets expand-ip-range` (never shrink) |
| Traffic for a range through an appliance VM | **Custom static route**, next hop instance (+ IP forwarding) |
| Lowest number wins? | Yes — priority 0–65535, default 1000 |
| Firewall targets developers cannot change by editing a VM | Service accounts, or **secure tags** in a firewall policy |
| Network tags in a firewall **policy**? | **No** — policies use secure tags |
| Guardrail rule for every VPC in a folder | **Hierarchical firewall policy** |
| Central team owns network, app teams own projects | **Shared VPC** |
| Two VPCs, private, non-transitive is fine | **VPC Network Peering** |
| Many VPCs, transitive hub | **Network Connectivity Center** |
| Encrypted, a few Gbps, fast to set up | **HA VPN** (99.99%) |
| 10+ Gbps, in a Google colo | **Dedicated Interconnect** |
| Cannot reach a colo | **Partner Interconnect** |
| Private VMs to Google APIs only | **Private Google Access** |
| Private VMs to the internet, nothing inbound | **Cloud NAT** |
| Fixed egress IP for a partner's allow-list | Cloud NAT with **static** NAT IPs |
| Cloud Run to a private Cloud SQL IP | **Direct VPC egress** |
| Cloud VMs resolve `corp.local` | **Forwarding zone** |
| On-prem resolves Cloud private zone | **Inbound server policy** |
| UDP, preserve client IP | **Passthrough** Network LB |
| One anycast IP, TLS at edge, multi-region | **Global external Application LB** (Premium Tier) |
| All backends unhealthy | Allow **35.191.0.0/16** and **130.211.0.0/22** |
| Cheapest egress, one region | **Standard Tier** |
| Why can't A reach B? | **Connectivity Tests** |
| On-prem routes work in one region only | VPC **dynamic routing mode → global** |
| What exchanges routes with on-premises | **BGP**, spoken by **Cloud Router** (private ASN) |
| GKE Pod range full | **Add a Pod secondary range** + new node pool (not a new cluster) |
| Secondary ranges per subnet | Up to **170** |



<a id="s4-13"></a>

## 4.13 Worked blueprints: five network topologies

The exam describes a company and asks for one missing piece. These five topologies are the shapes those stems come
from. For each one: the picture, every resource you would create in order, and which public addresses it needs.
Once you can build these five from memory, most networking items are a matter of spotting which piece is missing.

### Blueprint 1 — a public web tier on private VMs

```
 Internet ──► global external Application LB  (1 global static IP, Premium Tier, Cloud Armor)
                     │  health checks from 35.191.0.0/16, 130.211.0.0/22
                     ▼
 vpc-web (custom mode) ── subnet web-euw4 10.10.0.0/20  Private Google Access ON
        regional MIG, VMs with NO external IP ── Cloud NAT (auto IPs) ──► internet: apt, pip
        SSH only through IAP: allow 35.235.240.0/20 on tcp:22
```

| Step | Resource | Why |
|:----|:------------------------------------|:------------------------------------------------------------|
| 1 | Custom-mode VPC and one subnet with **Private Google Access** | VMs reach Cloud Storage and Artifact Registry with no public IP |
| 2 | Firewall: allow **health-check ranges** to the serving port; allow **35.235.240.0/20** on 22 | Without the first, every backend is unhealthy; the second is IAP TCP forwarding |
| 3 | Instance template **without** an external IP, regional MIG, health check, autohealing | No VM is reachable from the internet directly |
| 4 | **Cloud Router + Cloud NAT** in the region, automatic NAT IPs | Outbound updates; nothing can connect in |
| 5 | **Global static external IP**, then the load balancer's forwarding rule on it | DNS and customers' allow-lists keep working when the LB is rebuilt |

Public addresses: **one**, the load balancer's global static IP (Cloud NAT's automatic IPs are Google's to choose).
A single VM that must keep its public address when it is **replaced** needs a **regional static external IP**,
reserved once and attached to the new VM.

### Blueprint 2 — fixed egress for a partner's allow-list

```
 MIG workers (no external IPs, recreated often)
        │
 Cloud Router ── Cloud NAT  ── manual NAT IPs: nat-ip-1, nat-ip-2 (regional static) ──► partner API
                                 the partner allow-lists exactly these two addresses
```

| Step | Resource | Why |
|:----|:------------------------------------|:------------------------------------------------------------|
| 1 | Reserve **two regional static external IPs** in the workers' region | They exist independently of any VM |
| 2 | Cloud NAT with **manual** IP assignment using them | Every connection leaves from one of these two, whatever VM sends it |
| 3 | Enough **ports per VM**, or dynamic port allocation; NAT logging on | Many connections to one partner endpoint exhaust ports first |

Public addresses: **two**, both NAT IPs. Giving each VM a static IP fails as soon as the MIG recreates a VM, and
automatic NAT IPs can change.

### Blueprint 3 — hybrid: one data centre, HA VPN, a multi-region VPC

```
 On-premises  AS 65001   peer gateway (1 or 2 public IPs)
     ║ tunnel 0  BGP 169.254.0.1 ↔ .2         ║ tunnel 1  BGP 169.254.1.1 ↔ .2
 HA VPN gateway (2 interfaces, 2 Google-assigned public IPs)  europe-west4
     │
 Cloud Router rtr-euw4  AS 65010   learns 10.0.0.0/8 from on-premises, advertises the VPC's subnets
     │
 vpc-prod, dynamic routing mode GLOBAL ── subnets in europe-west4 AND us-central1 both reach on-premises
 Cloud DNS: forwarding zone corp.example → on-premises resolvers;  inbound server policy for on-premises → Cloud
```

| Step | Resource | Why |
|:----|:------------------------------------|:------------------------------------------------------------|
| 1 | Non-overlapping ranges for every subnet and on-premises network | Overlapping prefixes cannot be routed |
| 2 | **HA VPN gateway** and an **external peer gateway** resource for on-premises | Two interfaces, two tunnels, for the 99.99% SLA |
| 3 | **Cloud Router** with a private ASN; two tunnels, each with a **BGP session** | Routes are exchanged and fail over without static routes |
| 4 | VPC **dynamic routing mode: global** | Otherwise only europe-west4 learns the on-premises routes |
| 5 | Firewall rules allowing the on-premises ranges in | BGP brings routes, not permission |
| 6 | DNS: **forwarding zone** (Cloud → on-premises names) and **inbound server policy** (on-premises → private zones) | Name resolution in both directions |
| 7 | Optional: custom advertisement of `199.36.153.8/30` | On-premises hosts reach Google APIs privately |

Public addresses: the HA VPN gateway's two, assigned automatically, and the on-premises gateway's own. **Swap HA VPN
for Dedicated or Partner Interconnect** when bandwidth or steadiness demands it; the Cloud Router, BGP, routing mode
and DNS steps are identical, with **VLAN attachments** in place of tunnels.

### Blueprint 4 — enterprise landing zone: Shared VPC per environment

```
 Org ── folder common ── net-host-prod    vpc-prod      ── Interconnect VLAN attachments ── on-premises
     │                └─ net-host-nonprod vpc-nonprod   ── HA VPN ───────────────────────── on-premises
     ├─ folder production     ── shop-prod, data-prod     (service projects of net-host-prod)
     └─ folder non-production ── shop-dev, shop-stg       (service projects of net-host-nonprod)
 Hierarchical firewall policy at the org: deny everything from 0.0.0.0/0 except the LB and IAP ranges
 Org policy compute.vmExternalIpAccess: deny external IPs on VMs
```

| Step | Resource | Why |
|:----|:------------------------------------|:------------------------------------------------------------|
| 1 | Folders `production` and `non-production` with different org policies | Guardrails follow the folder ([§2.3](02-organization-projects-billing.md#s2-3)) |
| 2 | **Two host projects**, each with its own VPC | A route or firewall change in non-production cannot touch production |
| 3 | `compute.networkUser` on **individual subnets** to each team | Least privilege; teams cannot use another team's subnet |
| 4 | GKE in a service project: subnet with **secondary ranges**; grant the service project's GKE service agent **Host Service Agent User** on the host | The cluster uses ranges owned by the host project |
| 5 | Hybrid connection into each host VPC; **global** routing mode | One connection serves every region and every service project |
| 6 | **Hierarchical firewall policy** at the organization or folder | Rules app teams cannot override |

Public addresses: none on workloads at all; only load balancers' static IPs in the service projects that serve the
internet.

### Blueprint 5 — an internal service in two regions

```
 clients in us-east1 and us-west1 (and on-premises over Blueprint 3)
        │  one internal IP per region, same service
 cross-region internal Application LB
   proxy-only subnet us-east1 ── backends us-east1      fails over to ──►
   proxy-only subnet us-west1 ── backends us-west1
 Cloud DNS private zone api.internal.example → the LB's addresses, with health-checked routing policy
```

| Step | Resource | Why |
|:----|:------------------------------------|:------------------------------------------------------------|
| 1 | A **proxy-only subnet** (purpose `GLOBAL_MANAGED_PROXY`) in **each** region | Envoy proxies of the cross-region LB run there |
| 2 | Backends (MIGs or NEGs) in both regions, one **global** backend service | Failover between regions |
| 3 | Forwarding rules in each region, and a private DNS name | Clients use one name; on-premises resolves it through the inbound policy |

Public addresses: **none**. A *regional* internal Application LB cannot fail over to another region, and a global
**external** LB is reachable from the internet, so neither fits *"internal, survives a region"*.

### Which public addresses does a design need?

| Need | Address | Scope |
|:------------------------------------------------|:----------------------------------|:-----------------|
| A global external LB that keeps its IP | **Static external, global** | Global |
| A VM or regional LB that keeps its IP across replacement | **Static external, regional** | Region |
| Fixed **egress** for many private VMs | Cloud NAT with **manual** static IPs | Region |
| Private VMs reach Google APIs | **None**: Private Google Access | Subnet |
| Private VMs reach the internet, nothing inbound | **None of yours**: Cloud NAT automatic IPs | Region |
| HA VPN | **Assigned automatically**, one per interface | Region |
| A VM reached only by administrators | **None**: IAP TCP forwarding | — |

{: .tip }
> **Read a networking stem as a blueprint with one hole.** Name the blueprint (public web tier, fixed egress, hybrid,
> landing zone, internal multi-region), then ask which step is missing: a health-check rule, the routing mode, the
> NAT IP mode, an inbound DNS policy, a proxy-only subnet. The options are usually the other blueprints' pieces.
