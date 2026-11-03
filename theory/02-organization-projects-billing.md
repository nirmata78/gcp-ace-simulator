---
title: "Part 2 — Organization, projects, billing and quotas"
parent: Theory
nav_order: 2
---

# Part 2 — Organization, projects, billing and quotas
{: .no_toc }

1. TOC
{:toc}

{: .objectives }
> 1.1 Creating a resource hierarchy · setting up standalone organizations · enabling APIs · assessing quotas · setting up cloud networking · Cloud Asset Inventory and Gemini Cloud Assist · 1.2 all of billing · 3.2 estimating costs

Everything in Google Cloud is attached to a node in one tree, paid for by one billing account, and bounded by the
quotas of one project. Get this part right and half of the identity and governance questions in Part 3 answer
themselves.

<a id="s2-1"></a>

## 2.1 The resource hierarchy

```
Organization                 the root: one per Cloud Identity / Workspace customer, or a standalone org
  +-- Folder                 optional, nestable (up to 10 levels): departments, environments, teams
  |     +-- Folder
  |     |     +-- Project    the unit of billing, quota, API enablement and default isolation
  |     |           +-- Resource   VM, bucket, Cloud SQL instance, cluster, topic ...
  |     +-- Project
  +-- Project                projects may hang directly off the organization
```

**Four rules follow from the tree, and each is examined directly:**

1. <mark markdown="span">**IAM allow policies are inherited downward and are additive.**</mark> A grant on a folder is effective on every
   project in it, including projects created later. There is no "more specific wins" ([§3.3](03-identity-access.md#s3-3)).
2. **Organization policies are inherited downward too.** The **constraint** is the rule type Google defines
   (`compute.vmExternalIpAccess`); the **organization policy** is your setting of that constraint on a node. Descendants inherit the policy; a lower node can **replace** it, or for
   list constraints **merge** with it ([§3.7](03-identity-access.md#s3-7)). Unlike IAM, it binds Owners too.
3. **The project is the boundary** for billing linkage, quota, API enablement and, by default, networking.
   *"Stop one team exhausting another's quota"* means separate projects.
4. **Grant at the smallest node that covers the requirement, including its future.** *"All of Finance's projects,
   including new ones"* is one binding on the Finance folder — not forty project bindings.

### Project identifiers

| Identifier | Mutable? | Notes |
|:--------------|:--------|:--------------------------------------------------------------|
| Project **ID** | **No** | Globally unique, chosen at creation (6–30 characters, lowercase, digits, hyphens). What almost every command takes |
| Project **name** | Yes | A display label; not unique |
| Project **number** | No | Assigned by Google; appears in default and Google-managed service account addresses |

`gcloud` accepts the ID or the number, never the display name.

<a id="s2-2"></a>

## 2.2 Creating the organization: Cloud Identity, Workspace, or standalone

An **organization resource** is created for you — you never "create an organization" with a command. There are
now two routes to one:

| Route | How the org appears | Principals it holds | Named after |
|:----------------------|:----------------------------------------------|:---------------------------|:-----------------|
| **Cloud Identity or Google Workspace** | Verify a domain, then the org is created when the first project or billing account is made by that customer | Managed users and groups in your domain, plus federated identities | The domain (`example.com`) |
| **Standalone organization** | Created automatically when a **new Free Trial** customer signs in to the console with a Google account and accepts the terms | Google accounts, and principals in a **workforce identity pool** ([§3.2](03-identity-access.md#s3-2)) | The user, e.g. `lara-brown-org` — **never a domain name** |

{: .new-title }
> New in the June 2026 guide — standalone organizations
>
> A standalone organization gives a new customer a real hierarchy — folders, org policies, org-level IAM —
> without a Cloud Identity super administrator or a verified domain. The signing-up user becomes **Organization
> Owner**. Facts worth holding: it is available **only to new Free Trial customers**, not to existing accounts;
> **one organization per user account**; its name cannot be a domain name, because domain names are reserved for
> Cloud Identity and Workspace organizations; other people are added by **invitation, which they must accept within
> 30 days**; a service account can never be an organization owner, and at least one active Google account must
> remain one. Workforce Identity Federation ([§3.2](03-identity-access.md#s3-2)) is how a standalone org lets people sign in with an external IdP.

**The first administrators.** In a Cloud Identity / Workspace org, the **super administrator** (Admin console) and
the **Organization Administrator** (`roles/resourcemanager.organizationAdmin`, IAM) are different roles in
different systems. The super admin manages users, groups and domain settings; the Organization Administrator
manages IAM on the resource hierarchy. Google's set-up guidance is to grant org-level roles to **groups** such as
`gcp-organization-admins@` rather than to individuals.

{: .watch }
> **Super admin versus Organization Administrator.** *"Create users, reset passwords, manage groups"* is the Admin
> console and a Cloud Identity / Workspace admin role. *"Grant IAM roles on folders and projects"* is the
> Organization Administrator IAM role. Neither implies the other.

{: .note }
> **Google Cloud Setup** is the console's guided flow for a new organization: identity and groups, administrative
> access, billing, the folder hierarchy, a starter network (a Shared VPC host with subnets), central logging and
> monitoring, and a baseline of security org policies. It can apply the result directly or hand it to you as
> Terraform. This is the practical meaning of the guide's *"setting up cloud networking"* in Section 1 — the
> foundation network, not individual firewall rules.

<a id="s2-3"></a>

## 2.3 Folders and projects in practice

{: .cmds }
| Task | Command |
|:------------------------------------|:------------------------------------------------------------|
| Create a folder | `gcloud resource-manager folders create --display-name=finance --organization=ORG_ID` |
| Create a project in a folder | `gcloud projects create kestrel-fin-prod --folder=FOLDER_ID` |
| Move a project | `gcloud beta projects move P --folder=FOLDER_ID` |
| Delete / restore a project | `gcloud projects delete P` · `gcloud projects undelete P` |
| Protect a project from deletion | a **lien**: `gcloud alpha resource-manager liens create --project=P --restrictions=resourcemanager.projects.delete --reason=...` |

**Deleting a project** starts a **30-day pending-deletion** period: billing stops, resources are shut down, and
`gcloud projects undelete` brings it all back. After 30 days it is gone.

**The Resource Manager roles you should be able to name:**

| Role | For |
|:--------------------------------------------|:------------------------------------------------------------|
| `roles/resourcemanager.organizationAdmin` | Manage IAM and structure for the whole organization — very broad |
| `roles/resourcemanager.folderAdmin` | Full control of a folder and everything under it |
| `roles/resourcemanager.folderCreator` | Create folders |
| `roles/resourcemanager.projectCreator` | Create projects (usually granted on a folder) |
| `roles/resourcemanager.projectDeleter` | Delete projects |
| `roles/resourcemanager.projectMover` | Update and **move** projects between folders |
| `roles/browser` | See the hierarchy — folders and projects — but nothing inside them |

A move needs rights on the project, the source and the destination. <mark markdown="span">**Project Mover granted on a common ancestor
(often the organization) covers all three in one binding**</mark>, which is why it beats Folder Admin or Organization
Administrator on a least-privilege question.

{: .trap }
> **Historic default grants.** When a Cloud Identity / Workspace organization is created, every user in the domain is
> granted **Project Creator** and **Billing Account Creator** at the organization. Removing those two grants is a
> standard first governance step — it is the answer to *"users keep creating projects and billing accounts
> outside the folder structure"*.

<a id="s2-4"></a>

## 2.4 APIs and services

**APIs are enabled per project.** A new project has very little enabled, and a call to a disabled API fails with
*"API has not been used in project N before or it is disabled"* — an **enablement** problem, not a permission
problem.

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| Enable an API | `gcloud services enable sqladmin.googleapis.com` |
| What is enabled | `gcloud services list --enabled` |

Enabling some APIs also creates **Google-managed service accounts** (service agents) that the product uses to act
in your project ([§3.9](03-identity-access.md#s3-9)). Enabling the Compute Engine API also creates the **default VPC network** unless the
organization policy `compute.skipDefaultNetworkCreation` is enforced — a common baseline, because the default
network ships with permissive firewall rules ([§4.4](04-networking.md#s4-4)).

{: .key }
> **Three error shapes, three different fixes.** *"API not enabled / not used before"* — enable the API.
> **403 / PERMISSION_DENIED** — an IAM grant is missing. **401 / UNAUTHENTICATED** — there are no valid
> credentials at all. The exam puts all three in one item often enough to learn the table.

<a id="s2-5"></a>

## 2.5 Quotas and limits

| Kind | Caps | Example | When hit |
|:----------------|:----------------------------------------|:------------------------------------------|:----------------------------|
| **Allocation quota** | How much may exist at once | vCPUs per region, GPUs per region, static IPs, VPC networks per project | Creation fails with a quota error |
| **Rate quota** | Requests per interval | API reads per minute | `429 RESOURCE_EXHAUSTED`; retry with exponential backoff |
| **System limit** | A fixed maximum, not adjustable | Maximum labels per resource | Redesign, do not request |

<mark markdown="span">**Quotas are per project**</mark>, and many are **per region** (GPUs have both a per-region and an all-regions quota).
When a legitimate workload needs more, the answer is to **request an increase for that quota in that project** in
**Cloud Quotas** (IAM & Admin → Quotas & System Limits), or let the **quota adjuster** raise eligible quotas
automatically as usage approaches them. Spreading the workload across extra projects to dodge a quota is the
distractor.


{: .key }
> <mark markdown="span">**A quota is a hard stop; a budget is only an alert ([§2.7](#s2-7)).**</mark> You can also *lower* a quota deliberately — for
> example BigQuery's query-usage-per-day quota — to cap consumption. That is the answer to *"make it impossible to
> exceed"*, where a budget is not.

{: .note }
> Free Trial accounts cannot use GPUs and have tight quotas; upgrading to a paid billing account is the fix, not a
> quota request. Quota increases can also depend on billing history for a new account (*verify* current rules).

<a id="s2-6"></a>

## 2.6 Billing accounts and the roles around them

A **Cloud Billing account** pays for projects. **A project is linked to at most one billing account; a billing
account can pay for many projects**, even across organizations. Two kinds exist: **self-serve** (card or bank
account, charged automatically) and **invoiced** (monthly invoice, for eligible customers). Unlinking a project's
billing account stops its paid services, and resources may be deleted.

| Role | Granted on | Lets the holder |
|:--------------------------------------|:------------------|:----------------------------------------------------|
| `roles/billing.admin` — Billing Account Administrator | Billing account | Everything: users, payment, links, budgets, exports |
| `roles/billing.user` — Billing Account User | Billing account | **Link projects to this account** |
| `roles/billing.viewer` — Billing Account Viewer | Billing account | Read costs and transactions |
| `roles/billing.costsManager` — Billing Account Costs Manager | Billing account | Budgets, exports, cost views — no payment control |
| `roles/billing.creator` — Billing Account Creator | Organization | Create new billing accounts |
| `roles/billing.projectManager` — Project Billing Manager | Project | Link and unlink **this project** |

{: .key }
> <mark markdown="span">**Linking a project needs a grant on both sides:**</mark> permission on the **project** (Project Billing Manager, or
> Owner) **and** Billing Account User on the **billing account**. Owner of the project alone cannot attach it to an
> account it has no role on. This two-sided rule is the single most examined billing fact.

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| Link a project to a billing account | `gcloud billing projects link P --billing-account=ID` |

<a id="s2-7"></a>

## 2.7 Budgets, alerts and exports

<mark markdown="span">**A budget watches spend and notifies. It never stops anything.**</mark> Each budget has a **scope** (the whole billing
account, or selected projects, services or labels), an **amount** (fixed, or last month's spend), and **threshold
rules** on **actual** or **forecasted** spend — for example 50%, 90% and 100%.

| Notification route | Use |
|:----------------------------------|:------------------------------------------------------------|
| Email to billing admins and users | The default |
| Cloud Monitoring notification channels | Route to on-call tools, SMS, chat |
| **Pub/Sub topic** | **Programmatic response** — a function that scales down, notifies, or even unlinks billing |

{: .trap }
> **"Automatically stop spending at the budget"** has no built-in switch. The supported pattern is a budget
> publishing to **Pub/Sub**, a **Cloud Run function** subscribed to it, and code that acts — for example disabling
> billing on the project. Say what that costs: disabling billing shuts services down and can delete resources. If the
> stem needs a *hard ceiling on a resource*, a **quota** is the tool.


### Billing export to BigQuery

The console's reports are for looking; **the BigQuery export is for querying**. There are three datasets:

| Export | Contains | Use |
|:----------------------|:----------------------------------------------------------------|:------------------------|
| **Standard usage cost** | Per-service, per-SKU, per-project cost with **labels** | Chargeback by team or cost centre |
| **Detailed usage cost** | The above **plus resource-level** rows (which VM, which bucket) | Per-resource analysis |
| **Pricing** | The list prices and your contract prices | Price analysis |

**Turn the export on early.** It is not a time machine: into a **multi-region** dataset (`US`, `EU`) the usage-cost
exports backfill only from the **start of the previous month**; into a **single-region** dataset, and for **pricing**,
nothing is backfilled. *"We need two years of queryable history"* is only possible if the export was on two years ago.
It is configured on the **billing account**, into a dataset in a project you choose.

<a id="s2-8"></a>

## 2.8 Reading and predicting cost

| Question | Tool |
|:----------------------------------------------|:------------------------------------------------------------|
| What **will** this architecture cost? (nothing built yet) | **Google Cloud Pricing Calculator** |
| What **did** it cost, by team? | **Billing export to BigQuery** + labels; billing reports for a glance |
| Tell me **when** spend crosses a line | **Budget** with threshold rules |
| How do I spend less on what I already run? | **Active Assist** recommendations ([§9.10](09-operations.md#s9-10)), CUD analysis, FinOps hub |

### Discounts

| Mechanism | Commitment | Notes |
|:----------------------|:----------------|:--------------------------------------------------------------|
| **Sustained use discounts** | None — automatic | For eligible machine series running much of the month. **E2 and several newer series do not receive them** (*verify*) |
| **Committed use discounts** — resource-based | 1 or 3 years of vCPU / memory / GPU in a region | Deepest discount for a steady footprint; billed whether used or not |
| **Committed use discounts** — spend-based (flexible) | 1 or 3 years of hourly spend | Applies across machine types and regions for a service |
| **Spot VMs** | None | Large discount, can be reclaimed any time ([§5.2](05-compute-engine.md#s5-2)) |
| **Free Trial / free tier** | — | $300 of credit for 90 days for new customers; small always-free usage (*verify*) |

{: .tip }
> *"Steady, predictable, 24×7 for years"* — **committed use discount**, three years if the stem says so.
> *"Interruptible, restartable, cheapest"* — **Spot VMs**. *"No commitment, discount without doing anything"* —
> **sustained use discount**.

### Labels are the cost dimension

| Metadata | What it is | In the billing export? | Used by |
|:----------------|:----------------------------------------------|:----------|:--------------------------------|
| **Labels** | Free key–value pairs on resources | **Yes** | Cost attribution, filtering, automation |
| **Network tags** | Strings on VMs | **No** | VPC firewall rules and routes ([§4.3](04-networking.md#s4-3), [§4.4](04-networking.md#s4-4)) |
| **Tags** (resource-manager tags) | IAM-governed key–values attached to org, folders, projects, resources; inherited | — | Conditional IAM, org policy, Cloud NGFW ([§3.7](03-identity-access.md#s3-7)) |

<a id="s2-9"></a>

## 2.9 Seeing everything: Cloud Asset Inventory and Gemini Cloud Assist

**Cloud Asset Inventory** is the metadata database of every resource and policy in your organization — the
answer whenever a question needs a view *across* projects.

| Need | Capability |
|:------------------------------------------------|:----------------------------------------------------------|
| Find every VM with an external IP across the org | `gcloud asset search-all-resources --scope=organizations/ORG --query="..."` |
| Find every binding that grants `roles/owner` | `gcloud asset search-all-iam-policies --scope=organizations/ORG --query="policy:roles/owner"` |
| Who can do X on Y? | `gcloud asset analyze-iam-policy` — this is **Policy Analyzer** ([§3.8](03-identity-access.md#s3-8)) |
| Snapshot everything into BigQuery for SQL | `gcloud asset export --content-type=resource --bigquery-table=...` |
| React to changes in near real time | **Asset feeds** to a Pub/Sub topic |
| What did this resource look like last month? | Change **history** (about 35 days) with `gcloud asset get-history` |

Content types include `resource`, `iam-policy`, `org-policy`, `access-policy` and `os-inventory` (from VM
Manager, [§5.6](05-compute-engine.md#s5-6)). Reading it needs `roles/cloudasset.viewer` at the scope you query.

{: .new-title }
> New in the June 2026 guide — Asset Inventory with Gemini Cloud Assist
>
> **Gemini Cloud Assist** is the AI assistant in the console. For this objective it answers natural-language
> questions about your estate — *"which Compute Engine instances in folder Finance have external IP addresses?"*,
> *"summarise the resources in this project"* — and explains or drafts the `gcloud` / query to get the answer. It
> draws on Asset Inventory and your permissions: it **cannot show you what your IAM roles do not allow you to see**,
> and its output is a draft to verify, not an authority. It needs its API enabled and a role such as
> `roles/geminicloudassist.user`. The rest of its jobs are in [§8.5](08-tooling.md#s8-5) and [§9.10](09-operations.md#s9-10).

### More to recognise

- **Cloud Asset Inventory analyses, not just searches.** It returns the **effective** organization policy for every
  resource in scope, reports the IAM and policy effects of moving a project **before** you move it (project moves
  have no dry run), and runs **SQL** over asset data without a user-built BigQuery export.
- **Protect and verify.** A **lien** (`resourcemanager.projects.delete`) stops even an Owner deleting a project
  until the lien is removed. **Assured Workloads** applies a control package to a folder — data
  location **and** support-personnel controls; the `gcp.resourceLocations` constraint covers location only.
- **Organization policy beyond the catalogue.** `sql.restrictPublicIp` blocks public IPs on Cloud SQL
  (`sql.restrictAuthorizedNetworks` only blocks authorized networks). **Custom constraints** use CEL on resource
  fields when no predefined constraint fits — for example *every new GKE cluster must have Workload Identity
  Federation enabled*.
- **Quotas.** The **quota adjuster** requests increases automatically as usage nears a supported quota (it only
  raises). A **usage alert** from the Quotas page is a Cloud Monitoring alerting policy — a budget watches money,
  not quota.
- **Cost.** **Cost anomaly detection** in Cloud Billing flags spikes against historical patterns with no thresholds
  to set. **Gemini Cloud Assist in Cloud Billing** answers *"why did the bill go up?"* in natural language, within
  the user's billing permissions.
- **Everyday gcloud.** Named **configurations** (`gcloud config configurations create/activate`) switch account,
  project and region together. A **log scope** lets Logs Explorer query several projects' logs together without
  moving them.

<a id="s2-10"></a>

## 2.10 Part 2 recall card

| Prompt | Answer |
|:------------------------------------------------|:--------------------------------------------------------|
| All of a department's projects, now and future | Bind on the **folder** |
| Recover a project deleted last week | `gcloud projects undelete` (30-day window) |
| Stop a critical project being deleted | A **lien** |
| Move a project, least privilege | **Project Mover** at a common ancestor |
| Users create projects anywhere they like | Remove the default **Project Creator** grant at the org |
| New Free Trial, no domain, still want folders and org policy | **Standalone organization** |
| "API has not been used in project" | **Enable the API** |
| Hard ceiling on consumption | **Quota** (possibly lowered on purpose) |
| Warn on spend, never interrupt | **Budget** threshold rules |
| Act automatically at a budget threshold | Budget → **Pub/Sub** → Cloud Run function |
| Link project P to billing account B | Project Billing Manager (or Owner) on P **and** Billing Account User on B |
| Chargeback by team | **Labels** + BigQuery **billing export** |
| Price something not yet built | **Pricing Calculator** |
| Every public-IP VM across the org | **Cloud Asset Inventory** search |
| Ask about my resources in plain language | **Gemini Cloud Assist** |


