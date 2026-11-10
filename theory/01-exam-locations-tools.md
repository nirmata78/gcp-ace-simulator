---
title: "Part 1 — The exam, locations and the tools"
parent: Theory
nav_order: 1
---

# Part 1 — The exam, locations and the tools
{: .no_toc }

1. TOC
{:toc}

{: .objectives }
> Exam overview · 1.1 Verifying product availability across geographical locations · the interfaces every other objective assumes

Before any product, two things decide a surprising number of marks: knowing what the paper is actually testing,
and knowing *where* a resource lives — in a zone, a region, or globally. Both are here, with the tools you will
be asked to drive the platform with.

<a id="s1-1"></a>

## 1.1 The exam in numbers

| Property | Value |
|:----------------------|:------------------------------------------------------------|
| Length | **2 hours** |
| Items | **50–60**, multiple choice (one answer) and multiple select (the item says how many) |
| Cut score | **Not published.** About 70% is the working convention |
| Penalty for a wrong answer | None — never leave an item blank |
| Price | $125 plus tax (*verify*) |
| Languages | English, Japanese, Spanish, Portuguese |
| Delivery | Online-proctored, or at a testing centre |
| Validity | **3 years**. A shorter renewal exam (1 hour, 20 items) is available near expiry |
| Recommended experience | 6+ months hands-on with Google Cloud |

**Time budget.** 120 minutes over 50–60 items is roughly two minutes each. A practical rhythm: one pass answering
everything you know and flagging anything over 90 seconds; a second pass on the flagged items; a last pass on
every multiple-select item and every answer you changed.

{: .trap }
> **A multiple-select item says "Choose two" (or three).** <mark markdown="span">Selecting the wrong *number* of answers scores zero</mark>, and so
> does a single answer on a two-answer item. Read the instruction line before the options.

<a id="s1-2"></a>

## 1.2 The four sections, and what moved in June 2026

The exam guide that went live on **30 June 2026** has four sections:

| Section | Weight | What it covers |
|:----------------------------------|:------|:--------------------------------------------------------------|
| **1** Setting up a cloud solution environment | ~20% | Hierarchy, org policy, identities and groups, APIs, quotas, observability set-up, standalone orgs, networking set-up, locations, Asset Inventory, Workforce Identity Federation, billing |
| **2** Planning and implementing a cloud solution | ~30% | Choosing and deploying compute (VMs, MIGs, GKE, serverless, agents, GPUs/TPUs), storage and data products, networking, IaC and AI-assisted tooling |
| **3** Ensuring successful operation | ~30% | Day-2 work on compute, GKE, Cloud Run, storage and databases, networking, monitoring and logging, AI/dev platforms |
| **4** Configuring access and security | ~20% | IAM policies and roles, inheritance, service accounts, impersonation, short-lived credentials, Workload Identity Federation |

The previous guide had five sections (20 / 17.5 / 25 / 20 / 17.5) with "planning" and "deploying" separate. They
are now one 30% section, and "operating" grew from 20% to 30%. **Day-2 operations is now as heavy as building.**

{: .new-title }
> New in the June 2026 guide — the list to check yourself against
>
> **Setup:** standalone organizations · setting up cloud networking · verifying product availability by location ·
> Cloud Asset Inventory and Gemini Cloud Assist · **Workforce Identity Federation**.
> **Planning:** Agent Runtime on Gemini Enterprise Agent Platform · Hyperdisk · **GPUs vs TPUs** · Managed Service for
> Apache Kafka · Memorystore · Filestore, NetApp Volumes, Managed Lustre · multi-region redundancy · **Cloud NGFW
> policies and secure tags** · Cloud Interconnect · Fabric FAST · **AI-assisted tooling** (Gemini CLI, Google
> Antigravity, Gemini Cloud Assist, Application Design Center).
> **Operations:** Autopilot Pod resource requests · traffic splitting across Cloud Run, functions *and GKE* ·
> attaching GPUs/TPUs · deploying agents · Workbench and BigQuery notebooks · Cloud Workstations · Database Center ·
> **CMEK** · custom static routes · VPC Flow Logs and firewall logs · Query Insights and index advisor ·
> **Personalized Service Health** · Active Assist · **Cloud Hub**.
> **Security:** policy inheritance in the hierarchy · Google-managed service accounts · service accounts for GKE
> applications · provisioning Workload Identity Federation.

**What left the guide:** Cloud Run for Anthos and GKE Enterprise are no longer named, and *Cloud Functions* is now
**Cloud Run functions**. App Engine is not named at all, but it still exists and still appears as a distractor;
[§6.12](06-containers-serverless.md#s6-12) covers it in one page.

<a id="s1-3"></a>

## 1.3 How ACE items are written

The exam is scenario-based: a short story, a requirement, and four options that all *work* to some degree. It is
testing whether you pick the one Google would recommend. Five preferences run through almost every item:

1. **Managed over assembled.** If a product exists for the job, the answer is that product, not a VM running
   open-source software that does the same thing.
2. **Least privilege, at the smallest sufficient scope.** A predefined role on one resource beats a broad role on a
   project; a group binding beats per-user bindings.
3. **No long-lived secrets.** An attached service account, impersonation or federation beats a downloaded key every
   time a keyless option exists.
4. **The fewest moving parts that satisfy every clause.** One command, one object, one resource — unless the
   requirement genuinely needs two constructs (alerting is the classic case, [§9.3](09-operations.md#s9-3)).
5. **Cost matters, but never above a stated requirement.** "Cheapest" only decides between options that all meet
   the availability, latency and compliance clauses.

{: .tip }
> **Find the deciding clause first.** Most stems contain one phrase that eliminates three options — *"without
> changing the application"*, *"including project owners"*, *"no key material"*, *"must survive a zone failure"*,
> *"scale to zero"*. Underline it mentally before reading the options, and check each option against it.

<a id="s1-4"></a>

## 1.4 Locations: regions, zones and what lives where

A **region** is a geographic area (`europe-central2`, Warsaw). A **zone** is an isolated failure domain inside it
(`europe-central2-a`); most regions have three. A **multi-region** is a continent-scale location (`US`, `EU`,
`ASIA`) used by storage and analytics products. Some products add **dual-regions** (a named pair).

Every resource has a scope, and the scope decides what survives what:

| Scope | Examples | Survives |
|:-----------|:------------------------------------------------------------------|:------------------|
| **Zonal** | VM instances, zonal Persistent Disks, zonal MIGs, zonal GKE clusters, TPU VMs | Nothing beyond its zone |
| **Regional** | Subnets, regional disks, regional MIGs, Cloud SQL instances (HA ones span two zones), Cloud Run services, regional load balancers, Cloud Router, Cloud NAT, Artifact Registry repositories, regional GKE clusters | A zone failure (if spread) |
| **Multi-regional / global** | VPC networks, firewall rules, routes, images, snapshots (by default), global instance templates, global load balancers, Cloud DNS, Pub/Sub topics, IAM | A region failure |

**Two consequences worth holding:** <mark markdown="span">a **VPC is global while its subnets are regional**</mark>, so one VPC spans every
region with no peering; and <mark markdown="span">**images and snapshots are global**</mark>, so a disk in one zone can be recreated in any
other zone or region from them.

### Verifying that a product is available where you need it

Not every product, machine series, GPU or TPU type exists in every region — and within a region, not in every
zone. The exam frames this as *"the deployment failed in zone X"* or *"which regions can host workload Y"*.


The **Cloud locations** page and each product's *locations* page are the documentation answers. For a data-residency
requirement the enforcement answer is different: the `gcp.resourceLocations` organization-policy constraint
([§3.7](03-identity-access.md#s3-7)), which stops anyone creating resources outside approved locations.

{: .watch }
> **Available versus allowed.** *"Is the A3 machine series offered in this zone?"* is a catalogue question —
> `machine-types list` / `accelerator-types list`. *"Make sure nobody can create resources outside the EU"* is a
> governance question — the `gcp.resourceLocations` organization policy. Neither answers the other.

<a id="s1-5"></a>

## 1.5 The interfaces: Console, gcloud, Cloud Shell, SDKs

| Interface | Use it for |
|:----------------------|:----------------------------------------------------------------|
| Google Cloud console | Point and click; some features and every Gemini Cloud Assist panel appear here first |
| `gcloud` | The CLI for almost every service |
| `gcloud storage` | Cloud Storage — **replaces `gsutil`**; prefer it in any new answer |
| `bq` | BigQuery |
| `kubectl` | Kubernetes objects **inside** a cluster — never to create the cluster itself |
| `cbt` | Bigtable data-plane operations |
| Cloud Shell | A browser terminal with all of the above pre-installed and already authenticated |
| Client libraries | Application code, using Application Default Credentials ([§3.11](03-identity-access.md#s3-11)) |

### gcloud grammar and configurations

The grammar is regular: `gcloud [GROUP] [SUBGROUP] VERB NAME --flags`, with scope expressed as `--zone`,
`--region` or `--global` (newer groups use `--location`). Two flags work almost everywhere: **`--format`**
(`json`, `yaml`, `table(...)`, `value(...)`) to shape output, and **`--filter`** to select server-side.

**`gcloud beta ...` and `gcloud alpha ...` are release tracks, not typos.** A command that exists only on those
tracks must be typed with the prefix: in the current SDK that includes `beta projects move`, the whole
`beta quotas` group and `beta services identity create`, and `alpha resource-manager liens`. Everything else in this booklet is GA and takes no prefix. Exam options sometimes
drop the prefix — judge the *verb and flags*, not the track.

**Launch stages: what can be a right answer.** A Google Cloud product or feature is **Preview** (sometimes
*Private Preview*), then **GA** (generally available). Preview carries the *"Pre-GA Offerings Terms"*: no SLA,
limited support, and it can change. The documentation marks it with a **Preview** banner at the top of the page,
or *(Preview)* beside one feature of a GA product. This course and its question bank follow one rule: <mark
markdown="span">**a right answer never depends on a feature that was only in Preview in June 2026**</mark>, the
state of Google Cloud the exam guide was written against. Preview features can appear as distractors, and the
theory names them with a *Preview* tag so you recognise them. The one exception is a product the guide itself
names: **Gemini Cloud Assist** is still labelled Preview in the documentation, but the June 2026 guide lists it in
three objectives, so its core uses are taught and tested. Its newer extensions (in Cloud Billing, its remote MCP
server) are not. A **`gcloud beta`** command is not the same thing: it is a command track, and the feature behind
it is often GA.

A **configuration** is a named bundle of properties — account, project, default region and zone. It is the
answer to *"switch between work contexts in one command"*:

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| First-time set-up | `gcloud init` |
| Create / switch a named context | `gcloud config configurations create prod` · `gcloud config configurations activate prod` |
| Default project and region | `gcloud config set project P` · `gcloud config set compute/region R` |
| Credentials for the CLI (a human) | `gcloud auth login` |
| Credentials for local application code (ADC) | `gcloud auth application-default login` |
| Add kubectl to a local SDK | `gcloud components install kubectl` |

{: .watch }
> **`gcloud auth login` versus `gcloud auth application-default login`.** The first gives **the gcloud CLI** your
> credentials. The second writes **Application Default Credentials** that client libraries — your own code —
> pick up. A program that says "could not find default credentials" on a laptop where `gcloud` works fine needs
> the second. And the Docker daemon is a third client again (`gcloud auth configure-docker`, [§6.7](06-containers-serverless.md#s6-7)).

### Cloud Shell

| Property | Value |
|:----------------------|:----------------------------------------------------------|
| What it is | A small VM, provisioned per user on demand, reached from the console |
| Persistent storage | **5 GB mounted at `$HOME`** — the only thing that survives |
| Everything else | Ephemeral: packages installed outside `$HOME` vanish when the VM is recycled |
| Keeping tools | Install into `$HOME`, or re-install at start from `~/.customize_environment` |
| Inactivity | The session ends after idle time; an unused home disk is eventually deleted (*verify* the window) |
| Pre-installed | `gcloud`, `kubectl`, `docker`, `terraform`, `helm`, language runtimes, an editor, web preview |

{: .tip }
> **"Only `$HOME` persists" is the whole Cloud Shell topic.** Options that claim the VM is permanently yours, that
> nothing persists, or that system paths like `/usr/local/bin` persist are each a near-miss of that one fact.

<a id="s1-6"></a>

## 1.6 Part 1 recall card

| Prompt | Answer |
|:----------------------------------------------|:------------------------------------------------|
| The four sections and weights | Setup 20 · Plan & implement 30 · Operate 30 · Security 20 |
| A VPC is ... ; a subnet is ... | Global ; regional |
| Recreate a disk in another region | From a **snapshot** or **image** — both are global |
| Is GPU type X offered in this zone? | `gcloud compute accelerator-types list` |
| Stop anyone creating resources outside the EU | `gcp.resourceLocations` org policy |
| Switch account + project + region in one command | `gcloud config configurations activate NAME` |
| Library code cannot find credentials on a laptop | `gcloud auth application-default login` |
| What survives a Cloud Shell recycle | **`$HOME`** (5 GB) |
| Cloud Storage CLI | `gcloud storage` (not `gsutil`) |


