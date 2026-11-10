---
title: "Part 8 — Tooling: infrastructure as code, AI assistance, developer platforms"
parent: Theory
nav_order: 8
---

# Part 8 — Tooling: infrastructure as code, AI assistance, developer platforms
{: .no_toc }

1. TOC
{:toc}

{: .objectives }
> 2.4 Infrastructure as Code tooling (Fabric FAST, Config Connector, Terraform, Helm) · AI-assisted planning and implementation (Gemini CLI, Google Antigravity, Gemini Cloud Assist, Application Design Center) · 2.1 Agent Runtime · 3.1 deploying an agent · notebooks in Workbench and BigQuery · Cloud Workstations

<a id="s8-1"></a>

## 8.1 Infrastructure as code: the model

**Infrastructure as code (IaC)** describes infrastructure in version-controlled files and lets a tool make reality
match them. The exam prefers it over console clicks and shell scripts for anything repeatable, and it prefers
**declarative** tools.

| Property | Declarative IaC (Terraform, Config Connector) | A script of `gcloud` commands |
|:------------------------------|:------------------------------------------------|:------------------------------------------------|
| You write | The **desired end state** | The **steps** |
| Re-running | **Idempotent** — changes only what differs | Fails or duplicates |
| Preview | **Plan / diff before apply** | None |
| Drift | **Detected** on the next plan | Invisible |
| Review | Pull request on a readable diff | Review of imperative code |

{: .trap }
> <mark markdown="span">**Deployment Manager is deprecated**</mark> — never choose it for new work. **Console export** gives a one-time copy, not a
> maintained definition. **A shell script** is repeatable but not declarative. When an option offers Terraform (or
> Infrastructure Manager) against any of these, Terraform wins.

<a id="s8-2"></a>

## 8.2 Terraform on Google Cloud

| Concept | Meaning |
|:------------------------------|:----------------------------------------------------------------------|
| **Provider** | The plug-in that talks to an API — `google` and `google-beta` |
| **Resource** / **data source** | Something Terraform manages / something it only reads |
| **Module** | A reusable package of resources with inputs and outputs |
| **State** | Terraform's record of what it manages — the mapping from code to real resource IDs |
| **Plan** / **apply** | Compute the diff / execute it |

**State is the heart of it, and the exam's Terraform items are mostly about state:**

- <mark markdown="span">**Store it remotely** in a **Cloud Storage backend**</mark> — shared by the team, with **locking** so two applies cannot
  run at once. Local state on laptops is the classic failure: two engineers, two truths.
- **State contains secrets and resource details.** Restrict the bucket, enable **versioning** to recover a corrupted
  state, never commit it to git.
- **One state per environment** (separate directories or backends) limits the blast radius of a mistake.
- **Existing resources** made by hand are brought under management with **`import`** blocks or `terraform import`
  — not by deleting and recreating them.
- **Pin** provider and module versions so a plan today means the same tomorrow.

{: .cmds }
| Task | How |
|:------------------------------------|:----------------------------------------------------------------------|
| Remote state, with locking | a `backend "gcs"` block naming a bucket and a prefix |
| Pin the provider | `version = "~> 7.0"` for `hashicorp/google` |
| The loop | `terraform init` → `terraform plan -out=tfplan` → `terraform apply tfplan` |
| Adopt a resource made by hand | an `import` block, or `terraform import ADDRESS ID` |


**Infrastructure Manager** is Google's managed service that **runs Terraform for you**: it stores state, runs
plans (*previews*) and applies (*revisions*) as a service account, and records history — Terraform without owning
the runner or the state bucket.

<a id="s8-3"></a>

## 8.3 Blueprints and Kubernetes-native tools

| Tool | What it is | Choose it when |
|:------------------------------|:------------------------------------------------------------------|:------------------------------|
| **Cloud Foundation Toolkit (CFT)** | Google-maintained **Terraform modules and blueprints** (project factory, network, GKE...) | *"Use Google's tested modules rather than writing from scratch"* |
| **Fabric FAST** | An opinionated, staged **landing-zone** built from Cloud Foundation Fabric modules: bootstrap (org, automation, billing, logging) → resource management (folders) → networking and security → project factory | *"Stand up an enterprise-grade organization foundation quickly, following Google's practices"* |
| **Config Connector** | A Kubernetes add-on that manages Google Cloud resources as **Kubernetes custom resources**, continuously **reconciling** them | *"Teams manage their Cloud SQL and buckets with the same YAML and GitOps flow as their apps"* |
| **Config Controller** | Hosted Config Connector + Config Sync + Policy Controller | A managed control plane for that model |
| **Helm** | The **package manager for Kubernetes**: **charts** (templated manifests), **values**, **releases** with history | *"Install and upgrade the same application across many clusters, with rollback"* |



{: .watch }
> **Terraform versus Config Connector.** Both are declarative. **Terraform** reconciles **when you run it**.
> **Config Connector** reconciles **continuously** inside a cluster — a console change is reverted automatically —
> and fits teams already working in Kubernetes YAML. **Helm** deploys *applications* into Kubernetes; it does not
> create the cluster or cloud resources (unless charts contain Config Connector objects).

<a id="s8-4"></a>

## 8.4 Making changes the recommended way

1. **Everything in version control**; changes by **pull request** with the `plan` output attached for review.
2. **Apply from a pipeline**, not a laptop — Cloud Build or another CI running as a **dedicated deploy service
   account**, reached by **impersonation** or **Workload Identity Federation**, never a key ([§3.10](03-identity-access.md#s3-10), [§3.12](03-identity-access.md#s3-12)).
3. **Least privilege per stage** — the networking pipeline cannot touch IAM on the org; separate states per
   environment.
4. **No manual console changes** in managed environments; if one happens, the next `plan` shows the **drift** —
   revert it in code or adopt it into code.
5. **Policy as code** — organization policies as guardrails, plus plan validation (Policy Controller, `gcloud
   beta terraform vet`) before apply.
6. **Promote the same code** dev → staging → prod with different variables, not three copies.

<a id="s8-5"></a>

## 8.5 AI-assisted planning and implementation

{: .new-title }
> New in the June 2026 guide — AI-assisted tooling
>
> The June 2026 guide describes an Associate Cloud Engineer as someone who works **"supported by AI tooling"**, and
> names four tools. Expect *"which tool fits this task"* items and items about **using them safely**, not trivia about
> their menus.

| Tool | Where it lives | What it is for |
|:------------------------------|:------------------------------|:----------------------------------------------------------------|
| **Gemini Cloud Assist** | The **Google Cloud console** (and APIs) | Ask about **your** resources in natural language; generate `gcloud` and Terraform; **troubleshoot** with investigations over logs, metrics and config changes; explain log entries; draft alerting policies and queries; cost and optimisation insights; design architectures |
| **Gemini CLI** / **Antigravity CLI** | Your **terminal** | An AI agent that reads your code and files, runs shell commands (with your approval), scaffolds projects, writes IaC and can provision resources. In 2026 Google moved Gemini CLI's capabilities into the Antigravity CLI |
| **Google Antigravity** | A desktop **agent-first development platform** (IDE, CLI, SDK) | Agents that plan and carry out multi-step development tasks across editor, terminal and browser |
| **Application Design Center** | The console | Platform teams publish **approved, Terraform-backed application templates**; developers design on a **visual canvas** (AI-assisted), then deploy; results are registered as **App Hub applications** |

{: .tip }
> *"Ask which of my VMs have public IPs, from the console"* — **Gemini Cloud Assist**. *"From my terminal, have an
> agent generate and apply the Terraform for this service"* — **Gemini CLI / Antigravity CLI**. *"The platform team
> wants developers to deploy only from governed, reusable architecture templates"* — **Application Design Center**.
> *"An agentic IDE"* — **Antigravity**.

{: .key }
> **The rules that do not change because an AI wrote it.** <mark markdown="span">Generated commands and IaC are **drafts**</mark>: review the plan
> before applying. The assistant acts **with your permissions**, so least privilege still governs what it can see and
> change. Prefer generated **code** that goes through the normal review and pipeline over an agent making direct
> changes to production. Never paste secrets into prompts.

**Configuring the tools — three mechanics worth recognising.** A **`GEMINI.md`** file in the repository gives
Gemini CLI **standing instructions** (conventions, modules to use, what never to do) in every session. Extra tools
reach Gemini CLI through **MCP servers** registered under `mcpServers` in `.gemini/settings.json`. In the other
direction, Gemini Cloud Assist's **remote MCP server** lets a third-party assistant use it with the signed-in
user's permissions, but that server is *Preview*, so recognise it rather than pick it. Gemini Cloud Assist itself needs **`geminicloudassist.googleapis.com`**
enabled and **`roles/geminicloudassist.user`** for its users; *describe an app in a sentence and get a design to
refine and deploy* is Gemini Cloud Assist in **Application Design Center**.

<a id="s8-6"></a>

## 8.6 AI and developer platforms

{: .new-title }
> New in the June 2026 guide — agents, notebooks and workstations
>
> **Vertex AI is now Gemini Enterprise Agent Platform** (renamed April 2026; services unchanged). The guide names
> three of its operations tasks plus Cloud Workstations. Old names still appear in documentation and older material:
> *Vertex AI Agent Engine* → **Agent Runtime**; *Vertex AI Workbench* → **Agent Platform Workbench**.

### Agent Runtime

**Agent Runtime** (on Gemini Enterprise Agent Platform) is a **managed runtime for AI agents** built with the Agent
Development Kit (ADK), LangChain/LangGraph and other frameworks. You deploy the agent; it provides **scaling,
sessions, memory, identity, tracing and logging**, including long-running agents. It is the compute answer for
*"host our agent without building the serving infrastructure"* — the alternative is packaging the agent yourself
on Cloud Run or GKE.

Deploying is done from the Agent Platform SDK (or console): package the agent, **deploy** it to a region, give it a
**service identity** with only the roles its tools need, then query it through its endpoint and watch it in Cloud
Trace and Logging.

- The deployment names the agent's **`requirements`** (only those packages are installed — *"ModuleNotFoundError
  after deploy"* means a missing requirement) and a **Cloud Storage staging bucket**. Keep the bucket in the agent's
  project; a bucket elsewhere needs a read grant to the **Agent Platform service agent**.
- **Release a new version by updating** the existing Agent Runtime resource: callers keep its resource name.

### Notebooks: Workbench and BigQuery

| Surface | What it is | Operational points |
|:------------------------------|:------------------------------------------------------------|:--------------------------------------------|
| **Agent Platform Workbench** instances | Managed **JupyterLab on a Compute Engine VM** you configure (machine type, GPUs, disks, network) | **Idle shutdown** to stop paying for idle notebooks; start/stop, custom containers. **Access mode**: **single-user** (`--instance-owners`, one individual account, not a group) or **service-account** (anyone who can act as the instance's service account). **Upgrade** rebuilds the boot disk and **keeps the data disk** (`/home/jupyter`) |
| **BigQuery notebooks** (Colab Enterprise in BigQuery Studio) | Serverless notebooks next to your data | **Runtime templates** define the machine an admin allows; notebooks can be **scheduled**; notebooks are **code assets with version history, shared individually** — no project-wide BigQuery role needed to collaborate on one |


{: .tip }
> *"Data scientists leave notebook VMs running all weekend"* — **idle shutdown** on Workbench instances (or
> serverless notebooks in BigQuery). *"Notebook needs a GPU"* — a Workbench instance with an attached GPU, in a zone
> that offers it.

### Cloud Workstations

**Cloud Workstations** gives developers **managed development environments** in Google Cloud, reached from a browser
IDE or a local IDE over a tunnel. Administrators define them in layers:

```
Workstation cluster   (a region + VPC subnet: where workstations run, private networking)
  +-- Workstation configuration   (machine type, container image with tools, persistent disk,
  |                                idle and running timeouts, who may use it)
        +-- Workstation            (one developer's instance of that configuration)
```

It answers *"source code must not live on laptops"*, *"standardise every developer's toolchain"*, *"developers
need access to private resources on the VPC"*. Access is IAM, images come from Artifact Registry, and **idle
timeouts** control cost.

- **Self-service**: **`roles/workstations.workstationCreator`** on a configuration lets developers create
  workstations from it; creators get **`roles/workstations.user`** on their own. Neither lets them edit the
  configuration.
- **Standard tooling**: extend a Cloud Workstations **base image**, push it to Artifact Registry, set it as the
  configuration's container image.
- **Only `/home` persists** (the persistent disk). Anything written elsewhere is recreated from the image on every
  start — *"my clone in /opt vanished overnight"*.


### More to recognise

- **Agents.** **Agent Identity** gives each deployed agent its own principal, tied to its lifecycle, so grants and
  audit logs are per agent — and deleting the agent **does not** remove bindings to that principal.
- **Notebooks.** An administrator's **runtime template** fixes the network, subnet and public-IP setting for
  Colab Enterprise runtimes.
- **Workstations.** A **private cluster** (private gateway) is reached only through Private Service Connect.
  GPUs are declared on the **configuration** (N1, A2 or A3 machine types only).
- **Tooling.** Store Terraform state in a **`gcs` backend** (shared, locked, versioned). A console create form's
  **Equivalent code** shows the gcloud, Terraform or REST version of your settings.

<a id="s8-7"></a>

## 8.7 Part 8 recall card

| Prompt | Answer |
|:------------------------------------------------|:--------------------------------------------------------|
| Reviewable diff before change | **Terraform plan** |
| Two engineers' applies clash | **GCS backend with locking** |
| Manual console change in managed env | Shows as **drift** on next plan |
| Bring a hand-made bucket under Terraform | **`import`** |
| Terraform without running it yourself | **Infrastructure Manager** |
| Deprecated IaC service | **Deployment Manager** |
| Enterprise landing zone, fast | **Fabric FAST** / CFT blueprints |
| Cloud resources as Kubernetes YAML, auto-reconciled | **Config Connector** |
| Same app to many clusters, rollback | **Helm** |
| Plain-language questions about my resources | **Gemini Cloud Assist** |
| Terminal AI agent | **Gemini CLI / Antigravity CLI** |
| Governed, reusable app templates | **Application Design Center** |
| Host an ADK/LangGraph agent | **Agent Runtime** |
| Idle notebooks costing money | Workbench **idle shutdown** |
| No source on laptops; standard dev toolchain | **Cloud Workstations** |


