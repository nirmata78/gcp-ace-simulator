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
global**, routes learned in one region are usable from all regions.

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
| **On-premises** hosts reach Google APIs privately over VPN / Interconnect | Private Google Access for on-premises | `private.googleapis.com` (or `restricted.googleapis.com` with VPC Service Controls) via Cloud DNS and advertised routes |
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


