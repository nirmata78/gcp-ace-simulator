---
title: "Part 5 — Compute Engine"
parent: Theory
nav_order: 5
---

# Part 5 — Compute Engine
{: .no_toc }

1. TOC
{:toc}

{: .objectives }
> 2.1 selecting compute · launching an instance · storage for Compute Engine (PD, regional PD, Hyperdisk) · autoscaled MIGs · OS Login · VM Manager · Spot VMs and custom machine types · GPUs or TPUs · 3.1 connecting remotely · viewing running instances · snapshots and images · attaching GPUs and TPUs

<a id="s5-1"></a>

## 5.1 Choosing compute — the whole landscape

Read the tree top to bottom and take the first exit that fits.

```
Is it an AI agent you want hosted, with sessions, memory and scaling managed for you?
    YES -> Agent Runtime on Gemini Enterprise Agent Platform            (§8.6)
Is it a container, or can it be one?
    NO  -> Do you need the OS: kernel modules, licensed software, lift-and-shift, Windows?
             YES -> Compute Engine VM (+ a managed instance group to scale and heal)
    YES -> Is it request- or event-driven and stateless?
             YES -> Cloud Run service (requests) / Cloud Run job (run to completion)
                    One small function per event?  -> Cloud Run functions
             NO  -> Do you need Kubernetes: operators, StatefulSets, DaemonSets, Helm, a mesh?
                      YES -> GKE Autopilot (Google runs the nodes)
                             GKE Standard  (you need node-level control)
Heavy parallel maths (training, large inference)? -> add GPUs or TPUs to the chosen platform (§5.9)
```

| Stem language | Points at |
|:------------------------------------------------------------|:------------------------------------------|
| "scale to zero", "pay nothing when idle", "spiky HTTP traffic" | **Cloud Run** |
| "one function per upload / message / event" | **Cloud Run functions** (with Eventarc) |
| "already on Kubernetes", "Helm charts", "operators", "DaemonSet" | **GKE** |
| "do not want to manage nodes, upgrades or node pools" | **GKE Autopilot** |
| "specific OS / kernel", "licensed software", "lift and shift", "Windows Server" | **Compute Engine** |
| "batch job that runs to completion" | **Cloud Run jobs**, or Batch on Compute Engine |
| "deploy our LangGraph / ADK agent with managed sessions and memory" | **Agent Runtime** |
| "train a large model", "matrix maths at scale" | **GPUs** or **TPUs** ([§5.9](#s5-9)) |

{: .trap }
> **Scale-to-zero distractors.** A GKE Standard cluster with a Horizontal Pod Autoscaler scales **Pods**, but the
> nodes keep running and billing. A managed instance group scaling on CPU needs running VMs to measure. App Engine
> **flexible** keeps at least one instance. Only Cloud Run, Cloud Run functions (and App Engine standard) idle to
> zero cost.

<a id="s5-2"></a>

## 5.2 Machine families, custom types and provisioning models

| Family | Series (examples — *verify* the current catalogue) | Use |
|:----------------------|:--------------------------------------------|:------------------------------------------------|
| **General purpose** | E2 (cost-optimised, shared-core `e2-micro`/`small`/`medium`), N2, N2D, N4, C3, C4, Arm-based C4A / T2A, Tau T2D | Most workloads; E2 for the cheapest general VM |
| **Compute-optimised** | C2, C2D, H3 | High clock, HPC, game servers |
| **Memory-optimised** | M1, M2, M3, X4 | SAP HANA, very large in-memory databases |
| **Storage-optimised** | Z3 | Very high local-SSD density |
| **Accelerator-optimised** | A2, A3, A4 (NVIDIA GPUs), G2 (L4 GPUs) | ML training and inference, graphics |

The exam tests the **category**, not model numbers: *"4 TB of RAM in one VM"* is memory-optimised; *"cheapest
possible dev box"* is E2; *"GPU for inference"* is accelerator-optimised or GPUs attached ([§5.9](#s5-9)).

**Custom machine types** set vCPU and memory independently (on E2, N2, N2D, N4 and N1, among others) — the answer
to *"6 vCPUs and 40 GB; every predefined shape wastes one or the other"*. **Extended memory** goes beyond the
normal memory-per-vCPU ceiling.

### Provisioning models

| Model | Discount | Catch | Right for |
|:----------------------|:----------------|:------------------------------------------------------|:------------------------------|
| **Standard** (on-demand) | — | — | Default |
| **Spot VMs** | Large (60–91%, *verify*) | **Can be preempted at any time with ~30 s notice**; no SLA; no live migration; **no maximum runtime** | Fault-tolerant, checkpointing batch, CI runners, rendering |
| Preemptible VMs (legacy) | Large | Preemptible **and capped at 24 hours** | Superseded by Spot — recognise the name |
| Committed use | Up to ~55–70% (*verify*) | 1 or 3 years, billed regardless | Steady 24×7 footprint ([§2.8](02-organization-projects-billing.md#s2-8)) |
| Sole-tenant nodes | Premium | Most expensive | Physical isolation, bring-your-own-licence rules |

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| Custom shape on a Spot VM | `gcloud compute instances create render-1 --machine-type=n2-custom-6-40960 --provisioning-model=SPOT --instance-termination-action=DELETE` |

**On preemption** a Spot VM is **stopped** or **deleted** (your `--instance-termination-action`); a shutdown script
gets the notice period to checkpoint. In a MIG, preempted VMs are recreated when capacity returns.

<a id="s5-3"></a>

## 5.3 Launching an instance


| Flag family | What it controls |
|:------------------------------------|:------------------------------------------------------------------|
| `--image-family` + `--image-project` | Boots the **latest non-deprecated** image in a family — `debian-cloud`, `ubuntu-os-cloud`, `windows-cloud`, or your own |
| Disks | Boot disk type and size; extra disks created or attached ([§5.4](#s5-4)) |
| Network | Subnet, `--no-address` for no external IP, network tags |
| Identity | Service account and scopes ([§3.10](03-identity-access.md#s3-10)) |
| **Metadata** | Key–values read by the guest from the metadata server: `startup-script`, `shutdown-script`, `enable-oslogin`, `ssh-keys` |
| **Availability policy** | `--maintenance-policy=MIGRATE` (live-migrate during host maintenance) or `TERMINATE`; `--restart-on-failure` (automatic restart if the host crashes) |
| Protection | `--deletion-protection`; Shielded VM (secure boot, vTPM, integrity monitoring); Confidential VM (memory encryption) |

{: .key }
> **The availability policy is two settings.** *On host maintenance*: **MIGRATE** keeps the VM running by moving it
> to another host — the default — or **TERMINATE** stops it. *Automatic restart*: bring the VM back if the host
> fails. <mark markdown="span">**GPU VMs must use TERMINATE**</mark> (they cannot live-migrate), and Spot VMs always terminate and never
> auto-restart.

**Changing a running VM:** the machine type, service account and scopes can be changed <mark markdown="span">**only while the VM is
stopped**</mark>; disks can be attached live; labels, tags and metadata change live. A **stopped** VM, listed as `TERMINATED`, keeps its disks
(billed) and loses an ephemeral external IP; a **suspended** VM also keeps its memory state.

<a id="s5-4"></a>

## 5.4 Disks: Persistent Disk, Hyperdisk and Local SSD

| Type | Nature | Notes |
|:--------------------------------|:------------------------------------------|:--------------------------------------------------------|
| **pd-balanced** | SSD-backed network block storage | Good default for most boot and data disks |
| **pd-ssd** | Higher IOPS per GB | Databases on older machine series |
| **pd-standard** | HDD-backed | Cheapest, sequential throughput |
| pd-extreme | Provisioned IOPS | Top PD performance on some series |
| **Hyperdisk Balanced / Throughput / Extreme** | Network block storage with **performance (IOPS, throughput) provisioned independently of size** | The storage of the **newest machine series** — several (e.g. C4, N4) support **only** Hyperdisk (*verify* per series) |
| **Hyperdisk ML** | Read-only, attachable to **many VMs at once** | Serving model weights to a fleet |
| **Regional PD / Hyperdisk Balanced High Availability** | **Synchronously replicated across two zones** | Survives a zone failure; force-attach to a standby VM in the other zone |
| **Local SSD** | Physically attached, 375 GB partitions | **Highest performance, ephemeral**: data survives a reboot or live migration, **lost when the VM stops or is deleted** |

**Rules of thumb the exam uses:**

1. <mark markdown="span">**Disks can be resized up, never down**</mark>, while attached. Grow the file system inside the guest afterwards.
2. <mark markdown="span">**Local SSD plus a durability requirement is always wrong.**</mark> Use it for scratch, caches, temporary data.
3. <mark markdown="span">**Regional disks are high availability; snapshots are backup.**</mark> *"Survive a zone failure with no data loss"* for
   a single-VM database is a regional disk, not a snapshot schedule.
4. **Zonal disks attach only to VMs in their zone.** To move one, snapshot it and create a disk elsewhere.

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| Grow a disk (never shrink) | `gcloud compute disks resize data-2 --zone=Z --size=1TB` |
| Attach an existing disk | `gcloud compute instances attach-disk web-1 --disk=data-2 --zone=Z` |
| Regional disk, replicated in two zones | `gcloud compute disks create db-ha --region=R --replica-zones=R-a,R-b --type=pd-balanced` |

<a id="s5-5"></a>

## 5.5 Connecting to instances: SSH keys, OS Login, IAP

### Two ways Linux SSH access is authorised

| Method | How access is granted | Revoke by | Choose when |
|:----------------------|:----------------------------------------------|:------------------|:----------------------------|
| **Metadata-managed SSH keys** | Public keys in **project-wide** or **instance** metadata; `gcloud compute ssh` adds yours | Removing the key from metadata | Small, informal set-ups |
| **OS Login** | Linux accounts **tied to Google identities**; access is an **IAM role** | Removing the IAM role, or suspending the user | **The recommended answer** for teams |

**OS Login** is enabled with metadata `enable-oslogin=TRUE` (project or instance) or enforced org-wide with
`compute.requireOsLogin`. Access is then pure IAM:

| Role | Grants |
|:--------------------------------------|:----------------------------------------------------------|
| `roles/compute.osLogin` | SSH as a normal user |
| `roles/compute.osAdminLogin` | SSH with **sudo** |
| `roles/iam.serviceAccountUser` on the VM's service account | Also needed when the VM runs as a service account |
| `roles/compute.osLoginExternalUser` (on the org) | Users from **outside** your organization |

Add **`enable-oslogin-2fa=TRUE`** to require two-step verification. OS Login is Linux-only; Windows uses RDP with a
password generated by `gcloud compute reset-windows-password`.

{: .trap }
> **Project-wide SSH keys reach every VM in the project** that does not block them. *"A contractor's key must work
> on one VM only"* — instance-level key with `block-project-ssh-keys=TRUE`, or better, OS Login with an IAM binding
> on that one instance.

### Reaching a VM with no external IP

| Mechanism | Needs |
|:----------------------------------|:------------------------------------------------------------------|
| **IAP TCP forwarding** | `gcloud compute ssh vm --tunnel-through-iap`; a firewall rule allowing **`35.235.240.0/20`** on 22 (or 3389); **`roles/iap.tunnelResourceAccessor`** |
| Bastion host | A VM with an external IP you harden and patch — the assembled alternative |
| VPN / Interconnect | Private path from on-premises |
| **Serial console** | Boot problems, broken networking: `gcloud compute connect-to-serial-port vm`, metadata `serial-port-enable=TRUE` |

{: .tip }
> *"SSH to VMs with no public IP, per-user authorisation, no bastion"* — **IAP TCP forwarding + OS Login**.
> *"The VM does not boot / sshd is dead"* — **serial console**.

<a id="s5-6"></a>

## 5.6 Inventory and VM Manager

### Viewing what is running


A project-level list is `gcloud compute instances list`; **across projects** it is Cloud Asset Inventory ([§2.9](02-organization-projects-billing.md#s2-9)).

### VM Manager

**VM Manager** is a suite for running a fleet of VMs, driven by the **OS Config agent** (pre-installed in most
Google public images). Enable it with the OS Config API and metadata `enable-osconfig=TRUE`.

| Component | Does |
|:----------------------------------|:----------------------------------------------------------------|
| **OS inventory management** | Collects installed packages, OS version, available updates — per VM, queryable, exported to Asset Inventory |
| **Patch management** | **Patch jobs** (run now) and **patch deployments** (scheduled), filtered by labels or zones, with pre/post scripts, a **rollout** (zone by zone or concurrent, with a **disruption budget** capping how many VMs patch at once) and **patch compliance** reporting |
| **OS policies** | Declare desired state — packages installed, files, services, scripts — and the agent enforces it; assigned to VMs by filters |


{: .tip }
> *"Patch 400 Linux VMs every Sunday, and report which are non-compliant"* — **VM Manager patch deployment**. *"Make
> sure the Ops Agent is installed on every VM labelled `env=prod`"* — an **OS policy assignment**. A cron job on
> each VM is the assembled distractor.

<a id="s5-7"></a>

## 5.7 Snapshots, images and machine images

| Artefact | Captures | Use it to |
|:----------------------|:--------------------------------------------------------|:------------------------------------------------|
| **Snapshot** | **One disk's data**, incrementally | Back up a disk; restore or clone **that disk**, in any zone or region |
| **Custom image** | **One disk**, as a **bootable** image | Boot new VMs from a golden state; **what an instance template references** |
| **Machine image** | **All of a VM's disks plus its configuration** — machine type, metadata, labels, tags, network, service account | Clone, back up or move a **whole VM** |
| Instance template | A **specification**, no data | Tell a MIG what to create ([§5.8](#s5-8)) |

> **Snapshot = one disk's data. Image = one bootable disk. Machine image = the whole VM. Template = a recipe.**

### Snapshots

- **Incremental**: the first is full, later ones store changed blocks; deleting one never breaks the others.
- Stored **multi-regionally or regionally** (you choose), so a disk can be created from them anywhere.
- **Snapshot schedules** are resource policies attached to disks, with retention — the managed answer to *"back up
  these disks nightly, keep 14 days"*. A cron job running `gcloud` is the assembled distractor.
- **Archive snapshots** cost less to store and more to restore; **instant snapshots** are fast, in-place,
  point-in-time copies for rollback — **not** a backup, since they live with the disk.
- For application consistency, quiesce the application or use **VSS** on Windows.

### Images

- **Image families** point at the newest non-deprecated image — build `hardened-v7`, add it to family
  `hardened`, and every template using the family picks it up.
- **Deprecation states**: `DEPRECATED` (warn), `OBSOLETE` (no new use), `DELETED`.
- **Share** images across projects by granting `roles/compute.imageUser` on the image project.
- The **golden-image** pattern: *"every VM must boot already hardened, with no configuration step at start-up"* —
  bake a custom image; a startup script is configuration at boot and can fail.

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| Nightly snapshots, kept 14 days | `gcloud compute resource-policies create snapshot-schedule nightly --region=R --daily-schedule --start-time=02:00 --max-retention-days=14`, then `gcloud compute disks add-resource-policies data-2 --resource-policies=nightly --zone=Z` |
| Snapshot now; restore in another zone | `gcloud compute snapshots create snap-1 --source-disk=data-2 --source-disk-zone=Z` · `gcloud compute disks create data-2-copy --source-snapshot=snap-1 --zone=Z2` |
| Custom image in a family | `gcloud compute images create hardened-v7 --source-disk=golden --source-disk-zone=Z --family=hardened` |
| Whole VM: every disk plus its configuration | `gcloud compute machine-images create web-1-mi --source-instance=web-1 --source-instance-zone=Z` |

{: .trap }
> *"Recreate this VM — with all three data disks and its configuration — in another zone, fewest steps"* is a
> **machine image**. Three snapshots move the data but lose the machine type, metadata, tags and service account;
> a custom image contains only one disk.

<a id="s5-8"></a>

## 5.8 Instance templates and managed instance groups

<mark markdown="span">**An instance template is immutable.**</mark> To change what a group creates, make a **new** template and roll it out.
Templates are **global** or **regional** (a regional template keeps its dependencies in one region).

### MIG versus unmanaged instance group

| | Managed (MIG) | Unmanaged |
|:----------------------|:------------------------------------------------|:------------------------------------|
| Instances | Identical, **from a template** | Any VMs you add by hand |
| Autoscaling, autohealing, rolling updates | **Yes** | No |
| Use | Almost everything | Load-balancing a heterogeneous legacy set |

**Zonal MIGs** keep all VMs in one zone; **regional MIGs** spread them across zones (three by default) and survive
a zone outage — the answer to *"must stay up if a zone fails"*.

### The four MIG features, and which problem each solves

| Feature | Solves |
|:----------------------------------|:------------------------------------------------------------------|
| **Autohealing** (a health check on the MIG) | The VM is up but **the application is broken** — the MIG **recreates** it |
| **Autoscaling** | Not enough or too much **capacity** — changes the **count** |
| **Updates** (rolling, canary) | Rolling a **new template** out without an outage |
| **Regional distribution** | Surviving a **zone** failure |

{: .watch }
> **MIG health check versus load-balancer health check.** A load balancer's health check only **stops sending
> traffic** to a failing instance — the broken VM keeps running forever. The MIG's **autohealing** health check
> **recreates** it. Give autohealing an **initial delay** long enough for boot, or it will kill instances in a loop.

### Autoscaling

| Signal | Example |
|:----------------------------------|:------------------------------------------------------------------|
| **CPU utilisation** | Target 60% average |
| **Load-balancing serving capacity** | Utilisation or requests per second per instance behind an HTTP(S) LB |
| **Cloud Monitoring metric** | Per-instance or per-group, e.g. Pub/Sub backlog |
| **Schedules** | Scale up at 08:00 on weekdays |

Other controls: **min and max** replicas, the **initialisation period** (how long a new VM is ignored while it
warms up), **scale-in controls** (limit how fast it shrinks), and **predictive** autoscaling for CPU patterns.

### Updating a group

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| Autoscale on CPU | `gcloud compute instance-groups managed set-autoscaling web-mig --region=R --min-num-replicas=3 --max-num-replicas=12 --target-cpu-utilization=0.6` |
| Autohealing | `gcloud compute instance-groups managed update web-mig --region=R --health-check=hc-http --initial-delay=300` |
| Canary: 20% on the new template | `gcloud compute instance-groups managed rolling-action start-update web-mig --region=R --version=template=web-v1 --canary-version=template=web-v2,target-size=20%` |
| Full rollout with no capacity loss | `... rolling-action start-update web-mig --region=R --version=template=web-v2 --max-surge=3 --max-unavailable=0` |
| Restart or recreate every VM | `... rolling-action restart web-mig` · `... rolling-action replace web-mig` |

| Knob | Effect |
|:----------------------------------|:------------------------------------------------------------------|
| `--max-surge` | Extra instances created above target during the update (capacity kept) |
| `--max-unavailable` | How many may be down at once (0 = never below target) |
| `--type=proactive` / `opportunistic` | Replace now, or only when instances are recreated anyway |
| `--replacement-method=substitute` / `recreate` | New names, or keep names (needed for stateful MIGs) |
| `--canary-version=...,target-size=N%` | Send part of the group to the new template first |
| **Rollback** | Another `start-update` back to the old template |

**Stateful MIGs** preserve per-instance disks, metadata and IPs across recreation — MIG management for workloads
like databases or legacy apps that need stable identity.

<a id="s5-9"></a>

## 5.9 GPUs and TPUs

{: .new-title }
> New in the June 2026 guide — GPUs and TPUs
>
> The guide asks you to **identify whether to use GPUs or TPUs**, and to **attach** them. The choice is about the
> workload; the attaching is about a handful of hard constraints.

| | **GPUs** (NVIDIA) | **TPUs** (Google) |
|:----------------------|:------------------------------------------------|:------------------------------------------------|
| What | General-purpose parallel processors | ASICs built for large matrix / tensor operations |
| Frameworks | Anything CUDA: PyTorch, TensorFlow, JAX, RAPIDS, custom kernels | **JAX, PyTorch/XLA, TensorFlow** via the XLA compiler |
| Strong at | Broad model variety, custom ops, inference, graphics, rendering, video, smaller jobs | **Large-scale training and serving** of big models, cost per unit of throughput at scale |
| Where | Compute Engine (attached or accelerator-optimised series), GKE node pools, Cloud Run | **Cloud TPU VMs**, **GKE TPU node pools**, Agent Platform training |
| Unit | 1–8+ GPUs per VM | Chips, hosts, **slices** (e.g. `v5litepod-8`), multislice |

{: .tip }
> *"Rendering"*, *"video transcoding"*, *"our model uses custom CUDA kernels"*, *"a few GPUs for inference"* —
> **GPU**. *"Train a very large transformer in JAX as cheaply as possible at scale"* — **TPU**. When the stem gives
> no framework constraint and the workload is general, GPU is the safer answer.

### Attaching GPUs — the constraints

- **Accelerator-optimised series** (A2, A3, A4, G2) come with GPUs built into the machine type — one A100 40GB is
  **`a2-highgpu-1g`**, the 80GB A100 is `a2-ultragpu-*`; you choose the machine type, not `--accelerator`. **N1** VMs
  take attached GPUs (`--accelerator=type=nvidia-tesla-t4,count=1`); A100s cannot be attached to N1, and E2/C3 take
  no GPUs.
- **Graphics desktops** (CAD, 3D) — NVIDIA GPUs such as the L4 with **RTX Virtual Workstation** images. TPUs never
  render graphics.
- **Very large training** across thousands of chips — a **multi-host TPU slice**, joined by the inter-chip
  interconnect.
- **GKE Autopilot**: the Pod asks — `nodeSelector: cloud.google.com/gke-accelerator: nvidia-l4` plus
  `resources.limits: nvidia.com/gpu: 1`; Autopilot provisions the node and drivers.
- **`--maintenance-policy=TERMINATE`** — GPU VMs cannot live-migrate.
- **Drivers**: use a GPU-ready image (Deep Learning VM) or install NVIDIA drivers; GKE can install them for you.
- **Quota**: per region **and** an all-regions GPU quota; request both ([§2.5](02-organization-projects-billing.md#s2-5)).
- **Availability**: GPU and TPU types exist only in certain **zones** ([§1.4](01-exam-locations-tools.md#s1-4)). *"The create call fails in this zone"*
  — check `accelerator-types list` and choose another zone.
- Spot pricing applies to both GPUs and TPUs for interruptible work.

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| GPU attached to an N1 VM | `gcloud compute instances create train-1 --machine-type=n1-standard-8 --accelerator=type=nvidia-tesla-t4,count=2 --maintenance-policy=TERMINATE` |
| GPU built into the machine type (G2, A2, A3) | `gcloud compute instances create infer-1 --machine-type=g2-standard-8 --maintenance-policy=TERMINATE` |
| Which zones offer a GPU | `gcloud compute accelerator-types list --filter="name~l4"` |

### More to recognise

- **Compute choices beyond the big four.** **Batch** runs arrays of tasks on VMs it creates and deletes.
  **VMware Engine** moves vSphere estates unchanged. **Sole-tenant nodes** give dedicated hosts for per-core
  licences. **Oracle Database@Google Cloud** runs Exadata inside Google Cloud regions.
- **Capacity and placement.** A **future reservation** holds capacity for a known date (quota is permission, a
  commitment is a discount, neither is capacity). **Dynamic Workload Scheduler flex-start** obtains a set of GPUs
  together when capacity appears, without pre-emption during the run. A regional MIG's **target distribution shape
  `ANY`** places VMs wherever a zone has capacity. Spot VMs with **`--instance-termination-action=STOP`** keep
  their disks for a later restart.
- **Disks and security.** **Hyperdisk Balanced High Availability** is the synchronous two-zone disk for
  Hyperdisk-only machine series. **Hyperdisk Storage Pools** pool capacity and performance across many disks.
  **Confidential VM** encrypts memory in use. **OS policy assignments** in VM Manager enforce desired state
  (packages, files) continuously.

<a id="s5-10"></a>

## 5.10 Part 5 recall card

| Prompt | Answer |
|:------------------------------------------------|:--------------------------------------------------------|
| 6 vCPU / 40 GB, no waste | **Custom machine type** |
| Interruptible, checkpointing, cheapest | **Spot VM** (no 24 h cap; ~30 s notice) |
| GPU VM creation fails on maintenance policy | `--maintenance-policy=TERMINATE` |
| Keep VM running during host maintenance | **MIGRATE** (the default) |
| Change machine type | **Stop** first |
| Newest series refuses a PD | Use **Hyperdisk** |
| Block volume that survives a zone failure | **Regional PD** / Hyperdisk Balanced HA |
| Fast scratch, data may vanish | **Local SSD** |
| Team SSH, revocable by IAM | **OS Login** (+ 2FA) |
| SSH with no external IP, no bastion | **IAP TCP forwarding** (`35.235.240.0/20`) |
| VM won't boot | **Serial console** |
| Patch a fleet on schedule, report compliance | **VM Manager** patch deployment |
| Nightly disk backups, 14 days | **Snapshot schedule** |
| Whole VM to another zone | **Machine image** |
| Boot pre-hardened, no startup config | **Custom image** (family) in the template |
| App hung, VM up | MIG **autohealing** |
| Survive a zone outage | **Regional** MIG |
| New template, gradual, no capacity loss | `start-update --max-surge=N --max-unavailable=0` |
| Large JAX training, lowest cost at scale | **TPU** |
| Custom CUDA kernels / rendering | **GPU** |


