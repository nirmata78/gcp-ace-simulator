---
title: "Part 9 — Operations: observability, health and optimisation"
parent: Theory
nav_order: 9
---

# Part 9 — Operations: observability, health and optimisation
{: .no_toc }

1. TOC
{:toc}

{: .objectives }
> 1.1 provisioning and setting up Google Cloud Observability · 3.4 all of monitoring and logging: alerts, custom metrics, audit / flow / firewall logs, exports, log buckets, Log Analytics, log routers, viewing and filtering logs, diagnostic tools, Personalized Service Health, Ops Agent, Managed Service for Prometheus, Gemini Cloud Assist for Monitoring, Active Assist, Cloud Hub

<a id="s9-1"></a>

## 9.1 Google Cloud Observability, and setting it up

| Product | Answers |
|:------------------------------|:----------------------------------------------------------------------|
| **Cloud Monitoring** | Metrics, dashboards, **alerting policies**, uptime checks, SLOs |
| **Cloud Logging** | Log collection, storage, routing, querying, log-based metrics |
| **Cloud Trace** | Where time goes across services in one request |
| **Cloud Profiler** | Where CPU and memory go **inside** one service |
| **Error Reporting** | Groups and counts **exceptions** from logs, and notifies on new ones |
| **Ops Agent** | Collects **guest** metrics and logs from VMs |
| **Managed Service for Prometheus** | Prometheus metrics, collected and stored for you, queried in PromQL |
| **Personalized Service Health / Cloud Hub** | Google-side incidents affecting you / an application-centric operations view |

**Setting it up** (the Section 1 objective) means: the Logging and Monitoring APIs enabled (they are by default in
new projects); a **metrics scope** that lets one project see metrics from many; **log routing and retention**
decided (buckets, sinks, org-level defaults — including the **default storage location** of new projects' log
buckets, `gcloud logging settings update --organization=ORG_ID --storage-location=R`, for data residency); **agents** on VMs; **Managed Prometheus** on GKE (enabled by default
on new clusters); **notification channels** created once and reused by alerts.

### Metrics scopes

A **metrics scope** makes one **scoping project** able to chart and alert on metrics of many **monitored
projects** — *"one dashboard over twelve projects"*. Keep the scoping project free of workloads; add projects in
**Monitoring → Settings**. The Logging equivalent is an **aggregated sink** or a **log scope** / Log Analytics view
across projects ([§9.5](#s9-5)).

<a id="s9-2"></a>

## 9.2 Metrics and the Ops Agent

Metrics are identified by type; the **prefix tells you where they come from**:

| Prefix | Source |
|:----------------------------------|:------------------------------------------------------------------|
| `compute.googleapis.com/...` | The **hypervisor** — CPU utilisation, disk and network I/O. No agent needed |
| `agent.googleapis.com/...` | The **Ops Agent** — **memory**, swap, disk space used, processes |
| `workload.googleapis.com/...` | Application metrics via the Ops Agent's OpenTelemetry / third-party receivers |
| `custom.googleapis.com/...` | **Custom metrics** you write through the Monitoring API |
| `logging.googleapis.com/user/...` | **Log-based metrics** you define |
| `prometheus.googleapis.com/...` | **Managed Service for Prometheus** |

{: .key }
> **The hypervisor cannot see inside the guest.** CPU appears on every VM's charts; <mark markdown="span">**memory and disk-space
> utilisation appear only after the Ops Agent is installed.**</mark> *"Memory is missing from the dashboard"* — install the
> Ops Agent.

**The Ops Agent** combines Fluent Bit (logs) and an OpenTelemetry collector (metrics) in one agent, replacing the
legacy Logging and Monitoring agents. It is configured in `/etc/google-cloud-ops-agent/config.yaml`, has
**integrations** for common applications (nginx, MySQL, PostgreSQL, JVM, Redis...), and its VM's service account
needs **`roles/logging.logWriter`** and **`roles/monitoring.metricWriter`**. To install on a fleet, use an **OS
policy** through VM Manager ([§5.6](05-compute-engine.md#s5-6)) or the console's agent-install flow, not a script run by hand on each VM.


<a id="s9-3"></a>

## 9.3 Alerting, uptime checks and SLOs

> **Only an alerting policy notifies anyone.** Dashboards, uptime checks, log-based metrics and SLOs measure; an
> alerting policy decides and sends.

| Part of an alerting policy | Meaning |
|:----------------------------------|:------------------------------------------------------------------|
| **Condition** | Metric threshold · metric **absence** · **forecast** · **PromQL** query · **log match** (log-based alert) |
| **Duration / retest window** | How long the condition must hold — *"for 5 minutes"* avoids flapping |
| **Notification channels** | Email, SMS, mobile app, Slack, PagerDuty, webhooks, **Pub/Sub** — defined once, reused |
| Documentation | Markdown sent with the notification — the runbook link |
| Incident | Opened when the condition fires; closes automatically when it clears |

| Requirement | Construct |
|:----------------------------------------------|:------------------------------------------------------------------|
| Page when p95 latency > 800 ms for 5 minutes | **Alerting policy**, threshold condition on the latency metric, 5-min duration |
| Tell us if the public endpoint is unreachable from several regions | **Uptime check + an alerting policy on it** |
| Notify **each time** a specific error line appears | **Log-based alert** (alerting policy with a log-match condition) |
| Alert when an error line appears **more than 50 times in 10 minutes** | **Log-based metric (counter) + a metric alerting policy** |
| Alert when the error budget burns too fast | **SLO** + **burn-rate** alerting policy |
| Alert when a metric **stops arriving** | **Metric-absence** condition |

{: .watch }
> **Log-based alert versus log-based metric.** A **log-based alert** notifies on individual matching entries (with a
> notification rate limit) — the simplest answer to *"tell us whenever X is logged"*. A **log-based metric** turns
> matching entries into a **time series** — needed for **rates and thresholds** (*"more than N per window"*),
> charts, and SLOs. Error Reporting groups exceptions but cannot express *"more than 50 in 10 minutes of this plain
> line"*.

**Uptime checks** probe HTTP(S), TCP or ICMP endpoints from several Google locations (or privately, inside a VPC),
and chart availability and latency; they alert only through an attached policy. **SLOs** are defined on a
**service** with an **SLI** (availability or latency), a target and a window (rolling or calendar); the **error
budget** is the allowed failure; a **burn-rate** alert fires when the budget is being consumed too fast.


<a id="s9-4"></a>

## 9.4 Custom metrics and Managed Service for Prometheus

| Way in | When |
|:------------------------------------------|:------------------------------------------------------------------|
| **Log-based metric** | The signal is already in logs — no code change |
| **OpenTelemetry** (SDK → Ops Agent / collector / OTLP endpoint) | New instrumentation; vendor-neutral |
| **Monitoring API** `timeSeries.create` → `custom.googleapis.com/...` | Direct writes from code |
| **Prometheus exporters / `/metrics` endpoints** | Kubernetes and Prometheus-ecosystem apps → Managed Service for Prometheus |

**Managed Service for Prometheus** stores Prometheus metrics in Google's global time-series store (Monarch),
retains them long-term, and lets you query with **PromQL** in Metrics Explorer, alerting policies and Grafana.

| Collection mode | How |
|:----------------------------------|:------------------------------------------------------------------|
| **Managed collection** (GKE, the default on new clusters) | You declare **`PodMonitoring`** / `ClusterPodMonitoring` resources; Google runs the collectors |
| Self-deployed collection | A drop-in replacement Prometheus binary you run |
| On VMs | The **Ops Agent's Prometheus receiver** |



<a id="s9-5"></a>

## 9.5 Cloud Logging: routing, buckets, Log Analytics

```
Log entries --> Log Router --> sinks (inclusion filter, exclusion filters)
                                 |-- _Required bucket   400 days, cannot change, free
                                 |-- _Default bucket    30 days by default, configurable
                                 |-- custom log bucket  your region, retention (1 day - 10 years), CMEK
                                 |-- BigQuery dataset   query constantly, join with other data
                                 |-- Cloud Storage      cheap long-term archive
                                 |-- Pub/Sub topic      stream out: SIEM, Splunk, on-premises
                                 |-- another project    central logging project
```

| Bucket | Retention | Holds |
|:----------------------|:------------------------------|:------------------------------------------------------------|
| **`_Required`** | **400 days, fixed, free** | **Admin Activity** and **System Event** audit logs (and Access Transparency) |
| **`_Default`** | **30 days** by default, configurable | Everything else not excluded — including **Data Access** audit logs |
| **Custom buckets** | You choose (1–3,650 days), can be **locked** | Anything a sink routes there |

**Sinks** live on a project, folder, organization or billing account. An **aggregated sink** on a folder or
organization with `--include-children` routes every project's logs beneath it — the answer to *"central logging
for all projects"*. Each sink has a **writer identity** (a service account) that <mark markdown="span">**must be granted write access at
the destination**</mark> (`bigquery.dataEditor`, `storage.objectCreator`, `pubsub.publisher`, or `logging.bucketWriter`)
— a sink that "does nothing" usually lacks this grant.

**Exclusion filters** drop entries **before storage** — the lever for the logging bill (*"we do not need debug
logs from dev"*). Routing is free; ingestion and retention beyond the defaults cost money.

**Log views** restrict who sees which logs **inside** a bucket (`roles/logging.viewAccessor` on a view).

A log bucket's **region is fixed at creation**: to store logs elsewhere, create a bucket in the new region and
point the sinks at it. A **log view** exposes a subset of a bucket, and IAM on the view limits a team to that
subset. Among the Monitoring roles, Monitoring Viewer is read-only and Monitoring Editor creates dashboards and
alerting policies.

### Log Analytics

Upgrading a log bucket to **Log Analytics** lets you query logs with **SQL**, and optionally create a **linked
BigQuery dataset** that queries the same data **from BigQuery without copying it**. *"Analysts want SQL over our
logs and to join them with business data, without a second pipeline"* — Log Analytics with a linked dataset.

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| Central bucket with Log Analytics | `gcloud logging buckets create central --location=europe-west4 --retention-days=365 --enable-analytics` |
| Every project's logs into it | `gcloud logging sinks create all-to-central logging.googleapis.com/projects/LOGS_P/locations/europe-west4/buckets/central --organization=ORG_ID --include-children` |
| Who to grant on the destination | the sink's `writerIdentity`: `gcloud logging sinks describe all-to-central` |
| Stop paying for debug logs | `gcloud logging sinks update _Default --add-exclusion=name=no-debug,filter='severity<INFO'` |
| Keep `_Default` longer | `gcloud logging buckets update _Default --location=global --retention-days=90` |

### Exporting to external systems

| Destination | Right when |
|:----------------------------------|:------------------------------------------------------------------|
| **Pub/Sub** | Stream to a **SIEM**, Splunk (via a Dataflow template), or an **on-premises** collector |
| **BigQuery** | Query constantly, join, dashboard |
| **Cloud Storage** | **Retain cheaply for years**, read rarely — with lifecycle to Archive |
| A log bucket with long retention | Keep logs in Logging's own tools and Log Analytics |

<a id="s9-6"></a>

## 9.6 Reading logs

**Logs Explorer** (and `gcloud logging read`) use the Logging query language:

```
resource.type="gce_instance" AND severity>=ERROR
resource.type="cloud_run_revision" AND resource.labels.service_name="api"
logName="projects/P/logs/cloudaudit.googleapis.com%2Factivity"
protoPayload.methodName="v1.compute.firewalls.patch"
protoPayload.authenticationInfo.principalEmail="mara@kestrel.io"
jsonPayload.orderId="A-1042"          textPayload:"timeout"          httpRequest.status>=500
timestamp>="2026-09-20T14:00:00Z" AND timestamp<"2026-09-20T15:00:00Z"
```

`=` equals, `:` has / contains, `=~` regular expression, `AND` / `OR` / `NOT`.

**A log entry's fields**, which "view log message details" means: `logName`; `resource` (type and labels —
which VM, service, cluster); `timestamp` and `receiveTimestamp`; `severity`; `insertId`; `labels`; `trace` and
`spanId` (link to Cloud Trace); `httpRequest`; and one payload — `textPayload`, `jsonPayload`, or **`protoPayload`
for audit logs** (`methodName`, `serviceName`, `resourceName`, `authenticationInfo.principalEmail`, `status`).

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| Query logs from the CLI | `gcloud logging read 'resource.type="k8s_container" AND severity>=ERROR' --freshness=1h` |

<a id="s9-7"></a>

## 9.7 Audit, flow and firewall logs

| Audit log type | Records | Default | Cost | Bucket |
|:--------------------|:------------------------------------|:------------------------|:--------------|:------------|
| **Admin Activity** | Calls that **change** configuration or metadata | **Always on; cannot be disabled** | Free | `_Required` |
| **Data Access** | Calls that **read** configuration, or **read or write user data** | **Off** (except **BigQuery**, on) | Charged | `_Default` |
| **System Event** | Google-initiated changes (live migration, autoscaler) | Always on | Free | `_Required` |
| **Policy Denied** | Requests **denied by a security policy** (e.g. VPC Service Controls) | On | Charged (can exclude) | `_Default` |

**Enabling Data Access logs** is part of the IAM policy (`auditConfigs`) at the organization, folder or project, per
service and per type — `ADMIN_READ`, `DATA_READ`, `DATA_WRITE` — with optional **exempted principals** (e.g. a
noisy batch service account). Console: **IAM & Admin → Audit Logs**. Reading Data Access logs needs
**`roles/logging.privateLogViewer`**.

{: .key }
> *"Who changed this firewall rule?"* — **Admin Activity**, always there. *"Who read these objects?"* — **Data
> Access**, which exists <mark markdown="span">**only if it was enabled before** the reads</mark>. *"We have no record of who downloaded the file"*
> usually means Data Access logging was never turned on.

**VPC Flow Logs** (sampled flows per subnet or network) and **Firewall Rules Logging** (per rule, allowed or denied
connections) are not audit logs, but the guide groups them here because they answer the same kind of question —
*what happened on the network* — and are configured and read the same way, in Cloud Logging ([§4.11](04-networking.md#s4-11)). Both are
charged by volume: tune sampling and aggregation for flow logs, and log only the rules you need.

<a id="s9-8"></a>

## 9.8 Diagnosing an application

| Symptom | Tool |
|:----------------------------------------------|:------------------------------------------------------------------|
| A request is slow — **which service** in the chain? | **Cloud Trace** (spans per service; automatic for Cloud Run and App Engine requests, OpenTelemetry elsewhere) |
| One service is slow or expensive — **why, inside the code**? | **Cloud Profiler** (continuous CPU, heap, thread and contention profiles in production, low overhead) |
| A new **exception** started appearing | **Error Reporting** (groups stack traces, counts, first seen, notifies) |
| The **database** is slow — which queries, from which app or user? | **Query Insights** (Cloud SQL, AlloyDB): top queries, load, plans, tags |
| A slow query needs an index | **Index advisor** (Cloud SQL, AlloyDB) recommends indexes from the real workload |
| **What changed?** | Admin Activity audit logs; deploy history; **Gemini Cloud Assist investigations**, which correlate logs, metrics and config changes |
| Is it **Google**? | **Personalized Service Health** ([§9.9](#s9-9)) |

{: .tip }
> <mark markdown="span">**Trace tells you *which*; Profiler tells you *why*.**</mark> A latency jump across four services is Trace first. CPU
> utilisation tells you neither — a service can be slow while idle, waiting on a dependency.

<a id="s9-9"></a>

## 9.9 Service health and Cloud Hub

{: .new-title }
> New in the June 2026 guide — Personalized Service Health and Cloud Hub
>
> **The public Google Cloud Service Health dashboard** lists broad incidents for everyone. **Personalized Service
> Health** shows the incidents and planned events **that affect your projects and products** — per project, and in
> an **organization-level view across every project** — with history, an API and logs — and you can **alert on them** with Cloud Monitoring alerting policies. *"Tell on-call automatically when
> a Google incident affects our Cloud SQL instances in europe-west4"* is Personalized Service Health with an alerting
> policy, not someone watching the status page. Least-privilege access to it is
> **`roles/servicehealth.viewer`** on the project or organization (the Service Health API must be enabled); basic
> Viewer also works but grants far more.
>
> **Cloud Hub** is an **application-centric operations home** in the console: for applications defined in **App Hub**
> (their services and workloads) it brings together **health** (open alerts, Service Health events), **active events
> and maintenance**, deployments, cost and optimisation, and support cases. *"One view of the health of our checkout
> application across its projects"* — Cloud Hub.

<a id="s9-10"></a>

## 9.10 Optimising: Active Assist and Gemini Cloud Assist

**Active Assist** is the family of **recommenders** that analyse usage and suggest changes, each with estimated
savings or risk reduction:

| Recommender | Suggests |
|:----------------------------------|:------------------------------------------------------------------|
| **VM machine-type (rightsizing)** | A smaller or larger machine type from observed use |
| **Idle resources** | Idle VMs, unattached disks, unused static IPs, old images |
| **Committed use discounts** | Commitments that fit your steady usage |
| **IAM role recommender** | Removing permissions a principal has not used (~90 days) |
| **Unattended project** | Projects nobody uses — delete or reclaim |
| Cloud SQL / GKE | Over-provisioned instances, idle clusters, container requests |
| Firewall Insights | Shadowed and unused rules |

They appear in the **Recommendation Hub**, on resource pages, in the **FinOps hub**, and via the Recommender API.


**Gemini Cloud Assist for Cloud Monitoring** helps you **build and read** observability in natural language:
drafting PromQL and alerting conditions, explaining a chart or a log entry, summarising an incident, and running
**investigations** that propose likely root causes. As in [§8.5](08-tooling.md#s8-5), its output is a starting point you verify, bounded
by your permissions.

### More to recognise

- **Alerting that matches intent.** An **SLO burn-rate** alert pages on fast error-budget consumption, not on
  every blip. A **synthetic monitor** runs a scripted, multi-step journey on a schedule. A **private uptime check**
  reaches an internal endpoint through **Service Directory**.
- **Open standards.** Grafana keeps its **PromQL** dashboards against Managed Service for Prometheus. An
  **OpenTelemetry Collector** exports OTLP metrics and traces to Cloud Monitoring and Cloud Trace.
- **Cost and clarity.** Lower **VPC Flow Logs** sampling and lengthen aggregation to cut volume. **Explain this log
  entry** asks Gemini Cloud Assist what an entry means. Cloud Hub's **Deployments** page shows failed App Hub
  deployments; its **Optimization** page shows cost per project or application.

<a id="s9-11"></a>

## 9.11 Part 9 recall card

| Prompt | Answer |
|:------------------------------------------------|:--------------------------------------------------------|
| Only thing that notifies | **Alerting policy** |
| Endpoint down, from several regions | **Uptime check + alerting policy** |
| Notify each time a line is logged | **Log-based alert** |
| More than N log lines per window | **Log-based metric + alerting policy** |
| Memory missing on VM charts | **Ops Agent** |
| Agent on every prod VM | **OS policy** (VM Manager) |
| Prometheus metrics on GKE, managed | **Managed Service for Prometheus** + `PodMonitoring` |
| One dashboard over many projects | **Metrics scope** |
| Central logs for all projects | **Aggregated sink** (org/folder, `--include-children`) |
| Sink writes nothing | Grant the sink's **writer identity** at the destination |
| Cut logging bill | **Exclusion filter** |
| Retention of `_Required` / `_Default` | **400 days fixed** / **30 days default** |
| Logs to on-prem SIEM | Sink to **Pub/Sub** |
| Keep logs 7 years cheaply | Sink to **Cloud Storage** + lifecycle |
| SQL over logs, join in BigQuery | **Log Analytics** + linked dataset |
| Who changed it | **Admin Activity** |
| Who read it | **Data Access** — enable it first |
| Which service is slow / why | **Trace** / **Profiler** |
| Slow SQL, missing index | **Query Insights** / **index advisor** |
| Google incident affecting us, alert on it | **Personalized Service Health** + alerting policy |
| Health of one application across projects | **Cloud Hub** (App Hub applications) |
| Rightsize VMs, remove idle resources | **Active Assist** recommenders |


