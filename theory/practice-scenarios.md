---
title: Practice scenarios
parent: Theory
nav_order: 13
---

# Practice scenarios
{: .no_toc }

Eight companies, 47 decision paths. Each scenario forks into exam-style questions on the same morning; try each
one before you open its answer. They are original and are not taken from the exam.

1. TOC
{:toc}

## From Part 2 — Organization, projects, billing and quotas

{: .story-title }
> Scenario — Kestrel Labs, day one
>
> Kestrel Labs is three founders and a Free Trial account. One of them, Lara, signed in to the console last week
> with her Google account and created a project for a prototype. They expect to hire fifteen engineers this year,
> run a production service by spring, and they have a fixed monthly cloud budget. Each path below starts from the
> same morning.

#### Path 1 — "Do we even have an organization?"

Lara sees a resource named `lara-brown-org` above her project. A co-founder wants org-level admin rights. What is
true?

**A.** It is a Cloud Identity organization; verify `kestrel.io` and rename it.  
**B.** It is a **standalone organization**; invite the co-founder as an owner, who must accept within 30 days.  
**C.** Organizations need Workspace; the resource is a placeholder until they buy it.  
**D.** Grant the co-founder's Google account `roles/owner` on the project; org roles do not apply to trial accounts.

<details markdown="1">
<summary>Show the answer</summary>

**B.** New Free Trial customers get a standalone organization automatically, named after the user and never after a
domain. People join by invitation, accepted within 30 days. **A** fails because a standalone org's name cannot be a
domain; **C** is simply false; **D** grants project Owner, which is not organization administration.

</details>

#### Path 2 — "Separate prototype from production"

They want production isolated from experiments — separate quota, separate billing visibility, and access granted
once for everything production, including projects added later.

<details markdown="1">
<summary>Show the answer</summary>

**Two folders (`prototype`, `production`) with projects inside them, and IAM granted on the folders.** Projects give
isolation of quota, APIs and billing linkage; the folder binding covers future projects. Per-project bindings, or
one shared project with naming conventions, both fail *"including projects added later"* or *"separate quota"*.

</details>

#### Path 3 — "Never let the bill surprise us"

Finance wants an email at 50% and 90% of the monthly budget and a warning if the month is **forecast** to overshoot
— but production must never be interrupted.

<details markdown="1">
<summary>Show the answer</summary>

**A budget on the billing account with threshold rules at 50% and 90% of actual spend and 100% of forecasted
spend.** A budget alerts and never caps, which is exactly what *"never interrupted"* requires. A quota would
interrupt; a Pub/Sub-driven billing shutdown would interrupt; a weekly look at billing reports is not an alert.

</details>

#### Path 4 — "The GPU experiment will not start"

A founder tries to create a VM with a GPU and gets a quota error showing a limit of 0.

<details markdown="1">
<summary>Show the answer</summary>

**Upgrade the Free Trial to a paid billing account, then request a GPU quota increase for that region in Cloud
Quotas.** Trial accounts cannot use GPUs; after upgrading, GPU quota is per region and must be requested. Creating
another project does not help — the new project has the same zero quota.

</details>

#### Path 5 — "Who spent what?"

By summer, finance wants monthly cost per team and per environment, queryable in SQL.

<details markdown="1">
<summary>Show the answer</summary>

**Label every resource with `team` and `env`, and enable the standard (or detailed) billing export to BigQuery on
the billing account.** Labels appear on every export row; network tags never appear in billing data; the console
reports cannot be joined and queried. Enable the export now — at most the previous month is backfilled.

</details>

## From Part 3 — Identity and access

{: .story-title }
> Scenario — Mara leaves Kestrel Labs
>
> Kestrel Labs now has an organization on Cloud Identity, users synced from their Entra ID tenant by SCIM, and
> twelve projects across `prototype` and `production` folders. Mara, a senior engineer, resigned this morning and her
> last day is today. Over two years she accumulated access: group memberships, a few direct project bindings, Owner
> on one legacy project, and — it turns out — a service-account key she downloaded for a script. The security
> lead gives you the list below.

#### Path 1 — Cut her off everywhere, immediately

**A.** Remove her from every group she belongs to.  
**B.** Suspend her account — in the IdP, and in Cloud Identity, so it propagates at once.  
**C.** Add a deny policy at the organization denying all permissions to her.  
**D.** Remove her bindings project by project, starting with production.

<details markdown="1">
<summary>Show the answer</summary>

**B.** Suspension ends her ability to authenticate everywhere at once and revokes her sessions, so every binding —
direct, via groups, in all twelve projects — becomes unusable without being found. **A** leaves her direct
bindings; **C** works but is a policy object you now maintain forever for a principal that should simply not
authenticate; **D** is slow and will miss one. (With Workforce Identity Federation instead of synced accounts,
disabling her in Entra ID alone would do the same.)

</details>

#### Path 2 — The key she downloaded

Audit shows a user-managed key on `etl-runner@` created by Mara. The ETL job still runs on a VM as that account.

<details markdown="1">
<summary>Show the answer</summary>

**Delete (or first disable) that key; the VM keeps working because it uses the attached service account through the
metadata server, not the key.** Then stop it recurring: enforce `iam.disableServiceAccountKeyCreation` on the
organization. Rotating the key would keep a long-lived credential alive for no reason; deleting the service account
would break the job.

</details>

#### Path 3 — She was the only Owner of a legacy project

Nobody else can change IAM on `legacy-billing`.

<details markdown="1">
<summary>Show the answer</summary>

**An Organization Administrator grants Owner (or a narrower admin role) on that project to a group** such as
`legacy-owners@`. Org-level administrators can set IAM on any project beneath them. The durable lesson: grant
ownership to **groups**, so no individual's departure orphans a project.

</details>

#### Path 4 — What did she do last month?

Legal wants every configuration change Mara made in production in the last 30 days.

<details markdown="1">
<summary>Show the answer</summary>

**Query the Admin Activity audit logs** (always on, kept 400 days) for
`protoPayload.authenticationInfo.principalEmail="mara@kestrel.io"` across the production folder — Logs Explorer
per project, or an aggregated sink / Log Analytics for the folder ([§9.7](09-operations.md#s9-7)). *What she read* is a different question:
Data Access logs, which exist only if they were enabled beforehand.

</details>

#### Path 5 — Her replacement starts tomorrow, for a trial period

Tomas joins as a contractor for eight weeks and needs what Mara's team group grants — but it must end on its own.

<details markdown="1">
<summary>Show the answer</summary>

**Add Tomas to the team group through the IdP, and grant any extra role with an IAM condition expiring after eight
weeks** — or, for elevated production rights, a **Privileged Access Manager** entitlement he requests when
needed. A calendar reminder to remove access is not a control.

</details>

#### Path 6 — Her GitHub pipeline used a key too

A GitHub Actions workflow she wrote authenticates with a key stored as a repository secret.

<details markdown="1">
<summary>Show the answer</summary>

**Replace it with Workload Identity Federation**: a pool and OIDC provider for `token.actions.githubusercontent.com`,
an attribute condition restricting it to Kestrel's repository, and `roles/iam.workloadIdentityUser` on the deploy
service account for that principal set. Then delete the key. An encrypted key, or a key in Secret Manager, is still a
key.

</details>

## From Part 4 — Networking

{: .story-title }
> Scenario — Northwind goes hybrid
>
> Northwind Retail runs its ERP in a data centre in Warsaw. It is moving its web shop to Google Cloud in
> `europe-central2`, keeping the ERP on premises for now. A central network team will run connectivity for six
> product teams, each with its own projects. The shop must be public; everything else must stay private.

#### Path 1 — Connect the data centre this month

The link must be encrypted, carry about 2 Gbps, and survive the failure of one tunnel. The nearest Google
colocation facility is in another country.

**A.** Dedicated Interconnect with two circuits.  
**B.** HA VPN with two tunnels to two on-premises interfaces, dynamic routing through Cloud Router.  
**C.** VPC Network Peering with the data-centre network.  
**D.** Direct Peering.

<details markdown="1">
<summary>Show the answer</summary>

**B.** HA VPN is encrypted, deploys in days, gives 99.99% with the two-interface topology, and two tunnels carry 2
Gbps. **A** needs presence in a colo and weeks of lead time; **C** only connects Google VPCs; **D** reaches Google
public services, not the VPC.

</details>

#### Path 2 — Six teams, one network

The network team must own subnets and firewall policy; each product team keeps its own projects and budgets.

<details markdown="1">
<summary>Show the answer</summary>

**Shared VPC**: a host project owned by the network team, each team's projects attached as service projects, and
`roles/compute.networkUser` granted **per subnet** to each team's group. Peering six VPCs would give six networks,
six sets of firewall rules and no transitivity to the VPN.

</details>

#### Path 3 — Names, both ways

Cloud VMs must resolve `erp.corp.northwind.local`; ERP servers must resolve `api.internal.northwind.pl` hosted in
a Cloud DNS private zone.

<details markdown="1">
<summary>Show the answer</summary>

**A forwarding zone for `corp.northwind.local` pointing at the on-premises resolvers, and an inbound DNS server
policy on the VPC so on-premises resolvers can forward `internal.northwind.pl` queries to Cloud DNS.** One object
per direction; a public zone would expose internal names.

</details>

#### Path 4 — Web tier locked down

The shop's VMs sit behind a global external Application LB. They must accept traffic only from the load balancer,
and developers must not be able to widen that by editing instances.

<details markdown="1">
<summary>Show the answer</summary>

**A global network firewall policy rule allowing the serving port from the Google front-end and health-check
ranges (`130.211.0.0/22`, `35.191.0.0/16`) to targets selected by a *secure tag* `tier=web`**, whose tag value only
the network team may bind. A network-tag rule would work until a developer added the tag elsewhere; allowing
`0.0.0.0/0` is wrong on its face.

</details>

#### Path 5 — Private VMs need patches and Cloud Storage

Application VMs have no external IPs. They must download OS updates from public mirrors and read from Cloud
Storage; nothing may connect in.

<details markdown="1">
<summary>Show the answer</summary>

**Cloud NAT on the region's Cloud Router for internet egress, and Private Google Access on the subnet for Cloud
Storage.** NAT alone would also reach Cloud Storage, but via public endpoints; PGA keeps Google API traffic on the
private path. Giving VMs external IPs would make them reachable inbound.

</details>

#### Path 6 — "The app cannot reach the ERP"

After a change, a Cloud VM can no longer open port 1433 to an ERP server at `192.168.40.12`.

<details markdown="1">
<summary>Show the answer</summary>

**Run a Connectivity Test from the VM to `192.168.40.12:1433`** — it traces routes (is the on-prem prefix still
learned over BGP?), firewall rules and policies, and the VPN, and names the component that drops the packet.
Then confirm with Firewall Rules Logging on the suspected rule. Recreating the VPN tunnel is guesswork.

</details>

## From Part 5 — Compute Engine

{: .story-title }
> Scenario — Orbis Studio's render farm
>
> Orbis Studio renders animation frames overnight: 4,000 frames, each ten minutes of work, restartable from a
> checkpoint, needed by 07:00. By day, a small team fine-tunes and serves image models. Artists and engineers log in
> to VMs to debug. Everything runs in `europe-west4`.

#### Path 1 — The cheapest way to render overnight

**A.** A three-year committed use discount on 200 VMs.  
**B.** A managed instance group of Spot VMs from a template, scaled on a Pub/Sub backlog metric, workers checkpointing each frame.  
**C.** Preemptible VMs, recreated by a cron job every 24 hours.  
**D.** A GKE Standard cluster with on-demand nodes and an HPA.

<details markdown="1">
<summary>Show the answer</summary>

**B.** Frames are short and restartable, so preemption costs minutes, and Spot is the deepest discount; the MIG
recreates preempted VMs and scales to the queue. **A** commits to 24×7 capacity used eight hours a day; **C** uses
the legacy model plus hand-built automation; **D** pays on-demand prices and still needs node scaling.

</details>

#### Path 2 — The GPU VM will not create

`instances create --machine-type=n1-standard-8 --accelerator=type=nvidia-tesla-t4,count=1` returns an error about
the maintenance policy.

<details markdown="1">
<summary>Show the answer</summary>

**Add `--maintenance-policy=TERMINATE`** — GPU VMs cannot live-migrate. If the next error is *"not available in
this zone"*, run `gcloud compute accelerator-types list` and pick a zone that offers T4; if it is a quota error,
request both the regional and the all-regions GPU quota. (An **L4** is never attached this way: it comes built into a
**G2** machine type.)

</details>

#### Path 3 — Training the new model

The research lead wants to pre-train a large model written in JAX, as cheaply as possible per training step at
scale, and does not use custom CUDA kernels.

<details markdown="1">
<summary>Show the answer</summary>

**Cloud TPU** (a TPU VM slice, or a GKE TPU node pool), with Spot capacity if the job checkpoints. TPUs are built
for large-scale XLA workloads and JAX runs natively on them. GPUs would work but are the better answer only when
CUDA-specific code or broad framework variety is required.

</details>

#### Path 4 — A new render driver, no downtime

The render image needs a new driver. The MIG must keep full capacity during the change.

<details markdown="1">
<summary>Show the answer</summary>

**Build a new custom image in the render image family, create a new instance template, and run a rolling update
with `--max-surge` > 0 and `--max-unavailable=0`.** Templates are immutable, so editing the old one is impossible;
patching VMs in place leaves the template stale, and recreated VMs would revert.

</details>

#### Path 5 — Who may log in?

Artists must SSH to render VMs, which have no external IPs, using their company identities; access must end the
moment someone leaves.

<details markdown="1">
<summary>Show the answer</summary>

**OS Login (enforced with `compute.requireOsLogin`), `roles/compute.osLogin` granted to the artists' group, and IAP
TCP forwarding** with a firewall rule for `35.235.240.0/20` on port 22 and `roles/iap.tunnelResourceAccessor`.
Suspending a user removes access everywhere. Metadata SSH keys would outlive the person unless someone removes
them by hand.

</details>

#### Path 6 — Move the licence server

The licence VM, with three data disks and specific metadata, must move to another zone before maintenance.

<details markdown="1">
<summary>Show the answer</summary>

**Create a machine image of it and create the new VM from the machine image in the target zone** — then, if
clients use its internal IP, reserve that address as a static internal IP in the same subnet before moving.

</details>

## From Part 6 — Containers and serverless

{: .story-title }
> Scenario — Lumen's photo pipeline
>
> Lumen is a photo-sharing app. Users upload originals to the bucket `lumen-uploads` in `europe-central2`; a function
> makes thumbnails; an API on Cloud Run serves the app and reads metadata from Cloud SQL on a private IP; a
> nightly job recomputes recommendations. Traffic is spiky — nothing at night, bursts after lunch.

#### Path 1 — Thumbnails on every upload

**A.** A VM polling the bucket every minute.  
**B.** A Cloud Run function with an Eventarc trigger on `google.cloud.storage.object.v1.finalized` for `lumen-uploads`.  
**C.** A Cloud Scheduler job every minute calling the function.  
**D.** Object versioning, with a function reading old versions.

<details markdown="1">
<summary>Show the answer</summary>

**B.** An event-driven function fires once per finalized object, scales with bursts, and costs nothing when idle.
**A** and **C** poll — latency, waste, and duplicate processing; **D** confuses versioning with events. If it
never fires: trigger region = bucket region, and the Cloud Storage service agent needs `pubsub.publisher`.

</details>

#### Path 2 — Slow first request in the morning

Users complain that the first API call after the quiet night takes several seconds.

<details markdown="1">
<summary>Show the answer</summary>

**Set a small number of minimum instances on the API service** (and consider startup CPU boost). Min instances keep
warm containers ready; the cost is that the service no longer idles to exactly zero. Raising max instances or
concurrency does nothing for a cold start.

</details>

#### Path 3 — Release v2 to 10% of users

<details markdown="1">
<summary>Show the answer</summary>

**`gcloud run deploy api --image=...:v2 --no-traffic --tag=canary`, test at the tag URL, then `update-traffic
–to-tags=canary=10`**; promote with `–to-latest` or roll back by sending 100% to the previous revision. A plain
deploy would have moved 100% at once.

</details>

#### Path 4 — The API must reach Cloud SQL's private IP

<details markdown="1">
<summary>Show the answer</summary>

**Configure Direct VPC egress on the service** into a subnet of the VPC that has private services access to the
Cloud SQL instance, and connect with the Cloud SQL connector or to the private IP. A public IP on Cloud SQL with
authorized networks would expose the database; Cloud NAT is for the internet, not for private IPs.

</details>

#### Path 5 — Lumen moves the API to GKE Autopilot

A year later, the API runs on Autopilot. Its Pods must read `lumen-uploads`, and some Pods sit in `Pending`
while others were given more memory than their manifests specify.

<details markdown="1">
<summary>Show the answer</summary>

**Access:** a Kubernetes service account for the API, granted `roles/storage.objectViewer` on the bucket through
Workload Identity Federation for GKE — no key, no node-account grants. **Scheduling and memory:** Autopilot
applies defaults to containers without requests and raises requests that violate minimums or the CPU:memory ratio;
set explicit, realistic requests (VPA recommendations help). `Pending` Pods on Autopilot usually mean requests the
chosen compute class cannot satisfy, or a quota limit — not a node pool to resize.

</details>

#### Path 6 — Three services, one domain

`/api`, `/admin` and `/` must be served from one external IP with a Google-managed certificate.

<details markdown="1">
<summary>Show the answer</summary>

**On GKE: one Gateway (or Ingress) with path rules** to the three Services. **On Cloud Run: one global external
Application LB with a URL map and three serverless NEGs.** Three LoadBalancer Services, or three Cloud Run default
URLs, fail *"one IP"*.

</details>

## From Part 7 — Storage and data

{: .story-title }
> Scenario — Aerwave's telemetry platform
>
> Aerwave makes smart meters. 300,000 devices each send a reading every ten seconds. Support engineers must see any
> device's last 24 hours instantly; analysts run SQL over years of history; raw files must be kept for seven years
> for the regulator and are almost never read; billing data lives in a relational database that must survive a
> region failure with no data loss.

#### Path 1 — Ingest

**A.** Devices write directly into BigQuery with streaming inserts.  
**B.** Devices publish to a Pub/Sub topic; a Dataflow streaming pipeline writes to Bigtable and BigQuery.  
**C.** Devices upload a file per reading to Cloud Storage.  
**D.** Devices write into Cloud SQL, which exports nightly.

<details markdown="1">
<summary>Show the answer</summary>

**B.** Pub/Sub absorbs 30,000 messages a second and decouples devices from consumers; Dataflow transforms once and
writes both stores. **A** puts every device on BigQuery's write path with no buffer or transformation; **C**
creates billions of tiny objects; **D** meets Cloud SQL's single-primary write ceiling.

</details>

#### Path 2 — "Last 24 hours of meter 42, now"

<details markdown="1">
<summary>Show the answer</summary>

**Bigtable, with a row key of `meter_id#reverse_timestamp`** so one device's recent readings are adjacent and a
prefix scan returns them in milliseconds. A key starting with the timestamp would hotspot every write onto one
node; BigQuery would scan instead of look up.

</details>

#### Path 3 — Analysts' bill doubled

<details markdown="1">
<summary>Show the answer</summary>

**Partition the BigQuery table by reading date, cluster by `meter_id`, require a partition filter, and set maximum
bytes billed** (or a per-user query quota). Then find the worst queries in `INFORMATION_SCHEMA.JOBS`. Adding
`LIMIT` changes nothing; a budget alert tells you after the money is spent.

</details>

#### Path 4 — Seven years, untouched

<details markdown="1">
<summary>Show the answer</summary>

**A bucket with the Archive class, a seven-year retention policy locked with Bucket Lock**, and lifecycle deletion
after seven years. Archive's 365-day minimum is irrelevant at seven years, and first-byte latency is identical to
Standard. Versioning alone would let someone delete the versions.

</details>

#### Path 5 — Billing database, region failure, zero data loss

<details markdown="1">
<summary>Show the answer</summary>

**Spanner with a multi-region configuration** — synchronous replication, strong consistency and automatic
failover give an RPO of zero. A Cloud SQL cross-region replica is asynchronous (RPO greater than zero) and needs
promotion; Cloud SQL HA only covers a zone.

</details>

#### Path 6 — Stop the pipeline for an upgrade

The streaming Dataflow job must be replaced by a new version whose graph is **not** compatible with the old one.

<details markdown="1">
<summary>Show the answer</summary>

**Drain the running job** — it stops reading from Pub/Sub, finishes in-flight elements, and exits — then start
the new job on the same subscription, which has kept unacknowledged messages. **Cancel** would drop in-flight data;
an in-place **update** is only for compatible changes.

</details>

#### Path 7 — The regulator wants your own key

The billing database and the raw-file bucket must use keys Aerwave controls, rotated every 90 days, revocable on
demand.

<details markdown="1">
<summary>Show the answer</summary>

**CMEK**: Cloud KMS keys in locations matching each resource, a 90-day rotation period, and the **service agents**
of Spanner and Cloud Storage granted `cryptoKeyEncrypterDecrypter`. Revocation is disabling the key version. CSEK
does not apply to Spanner and has no schedule; Cloud EKM is the answer only if the key must live outside Google.

</details>

## From Part 8 — Tooling: infrastructure as code, AI assistance, developer platforms

{: .story-title }
> Scenario — Kestrel's platform team grows up
>
> Kestrel now has three environments and a two-person platform team. Infrastructure started as console clicks, then
> Terraform run from laptops. Application teams want self-service without breaking governance.

#### Path 1 — "Terraform deleted my change"

Two engineers applied from their laptops the same afternoon; one apply undid the other.

<details markdown="1">
<summary>Show the answer</summary>

**Move state to a Cloud Storage backend (versioned, locked) and apply only from a pipeline** running as a deploy
service account. Locking serialises applies; one shared state removes the two truths. Taking turns on Slack is not
a control.

</details>

#### Path 2 — A firewall rule changed in the console

<details markdown="1">
<summary>Show the answer</summary>

**The next `terraform plan` shows the drift**; either revert by applying the code, or put the change into code
through review. Then remove console write access from humans in managed projects. Deleting and recreating the
network would be absurd.

</details>

#### Path 3 — A new organization foundation by next month

<details markdown="1">
<summary>Show the answer</summary>

**Start from Fabric FAST (or CFT blueprints)** — staged Terraform for bootstrap, folders, networking, security and
a project factory, following Google's recommended practices. Hand-building it from scratch or clicking through the
console repeats solved problems without the review trail.

</details>

#### Path 4 — App teams live in Kubernetes

Teams already deploy with GitOps and want their buckets and Cloud SQL instances in the same repositories as YAML.

<details markdown="1">
<summary>Show the answer</summary>

**Config Connector**, so cloud resources are Kubernetes objects reconciled continuously by the same GitOps flow —
with **Helm** charts packaging each application. Asking the platform team to translate every request into Terraform
is the bottleneck they want to remove.

</details>

#### Path 5 — Self-service, but only approved architectures

<details markdown="1">
<summary>Show the answer</summary>

**Application Design Center**: the platform team publishes approved, Terraform-backed templates; developers compose
and deploy from them on the canvas, with Gemini Cloud Assist helping, and the result lands as an App Hub
application. Letting developers run an AI agent with Owner rights in production is the opposite of governance.

</details>

## From Part 9 — Operations: observability, health and optimisation

{: .story-title }
> Scenario — the 02:10 page
>
> At 02:10 Kestrel's on-call engineer is paged: checkout latency on the Cloud Run API has breached its threshold for
> five minutes. The API calls a Cloud SQL database and a payments service on GKE. The morning after, security and
> finance each have questions of their own.

#### Path 1 — Is it us or Google?

<details markdown="1">
<summary>Show the answer</summary>

**Check Personalized Service Health (or the application's view in Cloud Hub)** for an active incident on Cloud Run,
Cloud SQL or GKE in the region. If Google has an incident, follow it and communicate; if not, the problem is
yours. Opening a support case before looking is slower; the public dashboard may not show a localised event.

</details>

#### Path 2 — Which hop is slow?

**A.** CPU utilisation of each service.  
**B.** Cloud Trace for checkout requests, to see which span grew.  
**C.** Cloud Profiler on the API.  
**D.** Error Reporting.

<details markdown="1">
<summary>Show the answer</summary>

**B.** Trace breaks one request into spans per service and shows where the added time is. **A** cannot see waiting;
**C** explains *why* a known service is slow and comes second; **D** only sees exceptions.

</details>

#### Path 3 — The database span grew

Trace shows the Cloud SQL call went from 20 ms to 900 ms after yesterday's release.

<details markdown="1">
<summary>Show the answer</summary>

**Query Insights** identifies the new top query by load and its plan; **index advisor** recommends the missing
index. Then either add the index or **roll back the Cloud Run revision** with one `update-traffic` command while you
fix it. Scaling the instance up would mask a missing index at a higher bill.

</details>

#### Path 4 — The payments VMs look fine, but memory is not on the dashboard

<details markdown="1">
<summary>Show the answer</summary>

**Install the Ops Agent** — fleet-wide through a VM Manager OS policy — and grant the VMs' service account
`logging.logWriter` and `monitoring.metricWriter`. Memory is a guest metric the hypervisor cannot see.

</details>

#### Path 5 — Security wants a record of who read customer exports

<details markdown="1">
<summary>Show the answer</summary>

**Enable Data Access audit logs (`DATA_READ`) for Cloud Storage** on the relevant projects or folder, and route them
with an aggregated sink to the SIEM through **Pub/Sub** (and to a locked, long-retention bucket if required). For
last month's reads there is no record if the logs were off — an uncomfortable but correct answer.

</details>

#### Path 6 — Finance wants the cloud bill down 20%

<details markdown="1">
<summary>Show the answer</summary>

**Act on Active Assist recommendations**: rightsize over-provisioned VMs and Cloud SQL, delete idle disks and
unused IPs, buy committed use discounts for the steady baseline — tracked in the FinOps hub and the billing
export — and add exclusion filters for noisy debug logs. Cutting instance sizes blindly risks the latency you
were paged for.

</details>
