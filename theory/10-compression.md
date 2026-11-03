---
title: "Part 10 — Compression for the last 48 hours"
parent: Theory
nav_order: 10
---

# Part 10 — Compression for the last 48 hours
{: .no_toc }

1. TOC
{:toc}

Nothing here is new. It is the booklet folded into the four shapes that are fastest to re-read: pairs that the
distractors are built from, the numbers worth knowing, the command grammar, and the words in a stem that point at
an answer.

## <a id="s10-1"></a>10.1 Confusion pairs

| A | B | What separates them |
|:--------------------------|:--------------------------|:----------------------------------------------------------------|
| **Budget** | **Quota** | Budget **alerts**, never caps · quota **hard-stops** |
| **Label** | **Network tag** | Cost attribution, in the billing export · firewall/route matching, never in billing |
| **Network tag** | **Secure tag** | Anyone who edits the VM can set it; VPC rules only · IAM-controlled; firewall **policies** |
| **Super admin** | **Organization Administrator** | Users, groups, domain (Admin console) · IAM on the hierarchy |
| **GCDS / SCIM** | **Workforce Identity Federation** | Copy identities into Cloud Identity · no copies; IdP stays the source |
| **Workforce** federation | **Workload** federation | People, org-level pool · software outside Google, project-level pool |
| **IAM allow** | **Organization policy** | Who may act · what may be configured, **including by owners** |
| **Allow policy** | **Deny policy** | Additive union · subtracts, **evaluated first** |
| **IAM condition** | **PAM** | Grant with a built-in expiry or scope · request-and-approve, just-in-time elevation |
| **Policy Troubleshooter** | **Policy Analyzer** | *Why* can this principal (not) do it · *who* can do it |
| Service Account **User** | Service Account **Token Creator** | **Attach** an SA to a resource · **act as** it now |
| **Default SA** | **Service agent** | Your workload's legacy identity (Editor) · Google's product acting in your project |
| **Disable SA** | **Delete SA** | Reversible, bindings intact · orphaned bindings; same name ≠ same principal |
| **Secret Manager** | **SA key** | Secrets Google cannot mint · a credential Google mints on demand — don't store one |
| **`gcloud auth login`** | **`application-default login`** | Credentials for the CLI · for client-library code |
| **VPC** | **Subnet** | Global · regional |
| **Expand subnet** | **New subnet** | More IPs, same range, never shrink · another region or tier |
| **Shared VPC** | **Peering** | One network, many projects · two networks joined |
| **Peering** | **NCC** | Non-transitive pair · transitive hub |
| **HA VPN** | **Interconnect** | Encrypted over internet, quick, a few Gbps · private circuits, 10–100 Gbps, not encrypted by default |
| **Dedicated** | **Partner** Interconnect | You are in a Google colo · you are not |
| **Interconnect** | **Direct Peering** | Private VPC reach · Google public services only |
| **Private Google Access** | **Cloud NAT** | Google APIs only · the internet |
| **PSC** | **Private services access** | Endpoint to a service, no peering · peered producer VPC (Cloud SQL private IP) |
| **Forwarding zone** | **Inbound server policy** | Cloud resolves on-prem names · on-prem resolves Cloud names |
| **Proxy** LB | **Passthrough** LB | Terminates, rewrites client IP · preserves client IP |
| **Application** LB | **Network** LB | HTTP(S) at layer 7 · any TCP/UDP at layer 4 |
| **Premium** tier | **Standard** tier | Google backbone, global · public internet, regional, cheaper |
| **Flow logs** | **Firewall logs** | What traffic flowed (sampled) · which rule decided |
| **Spot** | **Preemptible** | No max runtime · 24-hour cap (legacy) |
| **MIGRATE** | **TERMINATE** | Live-migrate during maintenance · stop (required for GPUs) |
| **Snapshot** | **Image** | One disk's data · one bootable disk |
| **Image** | **Machine image** | One disk · all disks + VM configuration |
| **Template** | **Machine image** | A spec for new VMs · a capture of an existing VM |
| **Regional PD** | **Snapshot** | HA across zones · backup |
| **Autohealing** | **Autoscaling** | Recreate a sick VM · change the count |
| **MIG health check** | **LB health check** | Recreates · only stops sending traffic |
| **Metadata SSH keys** | **OS Login** | Keys you remove by hand · IAM-governed accounts |
| **GPU** | **TPU** | CUDA, variety, graphics, inference · large XLA/JAX training at scale |
| **Autopilot** | **Standard + automation** | Google's nodes, pay per Pod request · still your nodes |
| **HPA** | **VPA** | More Pods · bigger Pods |
| **HPA** | **Cluster autoscaler** | Pods · nodes |
| **Ingress / Gateway** | **LoadBalancer Service** | One IP, path routing, many Services · one IP per Service, layer 4 |
| **Node SA** | **Workload Identity** | Pulls images, writes logs · the app's access to APIs |
| **IAM** (GKE) | **RBAC** | Project-wide rights · per-namespace rights |
| **Cloud Run service** | **Cloud Run job** | Serves requests · runs to completion |
| **Min instances** | **Max instances** | Avoid cold starts · protect downstream, cap cost |
| **Request-based billing** | **Instance-based billing** | CPU only during requests · CPU always (background work) |
| **App Engine standard** | **App Engine flexible** | Scales to zero · minimum one instance |
| **Filestore** | **NetApp Volumes** | Managed NFS · NFS **and SMB**, NetApp features |
| **Nearline** | **Archive** | ~monthly, 30 days · yearly or less, 365 days |
| **Storage class** | **Latency** | Classes differ in price and minimum duration — latency is the same |
| **Versioning / soft delete** | **Bucket Lock** | Recover from accidents · immutability even against admins |
| **Transfer Appliance** | **Storage Transfer Service** | The pipe cannot carry it in time · it can |
| **Cloud SQL HA** | **Read replica** | Zone failover, standby serves nothing · read capacity |
| **Read replica** | **PITR** | Replays the bad `DELETE` · restores to before it |
| **Cloud SQL / AlloyDB** | **Spanner** | One write primary · horizontal writes, global strong consistency |
| **Bigtable** | **BigQuery** | Millisecond key/range lookups · analytical scans |
| **Pub/Sub** | **Managed Kafka** | Serverless, per-message ack · Kafka protocol, partitions, offsets |
| **Topic** | **Subscription** | Fan-out needs one subscription per consumer |
| **Dataflow drain** | **cancel** | Finish in-flight, no loss · stop now, lose in-flight |
| **Dataflow** | **Dataproc** | Beam, batch + stream · Spark/Hadoop lift-and-shift |
| **CMEK** | **CSEK** | Key in Cloud KMS, scheduled rotation, revocable · raw key per request, Storage/Compute only |
| **Disable** key version | **Destroy** | Reversible unreadable · permanent after the delay |
| **Terraform** | **Config Connector** | Reconciles when run · reconciles continuously in a cluster |
| **Terraform** | **Deployment Manager** | Current · deprecated |
| **Gemini Cloud Assist** | **Gemini CLI / Antigravity** | In the console, about your resources · in your terminal / IDE, as an agent |
| **Alerting policy** | Everything else | Only it notifies |
| **Log-based alert** | **Log-based metric** | Notify per matching entry · a time series for rates and thresholds |
| **Trace** | **Profiler** | Which service · why, inside it |
| `compute.googleapis.com` | `agent.googleapis.com` | Hypervisor sees it · needs the Ops Agent (memory) |
| **Admin Activity** | **Data Access** | Always on, free, 400 days · off by default, charged |
| **Public status dashboard** | **Personalized Service Health** | Everyone's incidents · the ones affecting you, alertable |
| `401` | `403` | No valid credentials · missing IAM permission |

## <a id="s10-2"></a>10.2 The numbers worth knowing

| Number | Meaning |
|:------------------------------|:----------------------------------------------------------------------|
| **20 / 30 / 30 / 20** | Section weights of the June 2026 exam guide |
| **0 / 30 / 90 / 365 days** | Minimum storage duration: Standard / Nearline / Coldline / Archive |
| **7 days** | Default Cloud Storage soft-delete window; BigQuery time travel (max); Spanner PITR (max); Firestore PITR |
| **90 days** | Uniform bucket-level access is reversible for 90 days; BigQuery long-term storage after 90 days unmodified |
| **30 days** | Project undelete window; service-account undelete; KMS default destruction delay |
| **400 days / 30 days** | `_Required` (fixed) / `_Default` (default) log retention |
| **5 GB** | Cloud Shell `$HOME` |
| **~30 s** | Spot preemption notice; **24 h** preemptible cap |
| **0–65535, default 1000, lower wins** | Firewall rule priority |
| **4** | Reserved addresses in every subnet range |
| **3 zones** | Regional GKE control plane; `--num-nodes` is per zone |
| **99.99%** | HA VPN with two interfaces and tunnels |
| **10 / 100 Gbps** | Dedicated Interconnect circuits; Partner **50 Mbps – 50 Gbps** |
| **`35.191.0.0/16`, `130.211.0.0/22`** | Load-balancer health-check ranges |
| **`35.235.240.0/20`** | IAP TCP forwarding source range |
| **80 / 1000** | Cloud Run default / maximum concurrency |
| **1 h** (to 12 h) | Default short-lived access-token lifetime (extendable by policy) |
| **15 min** | Dual-region turbo replication RPO |
| **1 Gbps ≈ 10 TB/day** | Transfer arithmetic |
| **1 node = 1,000 PU** | Spanner compute capacity |

## <a id="s10-3"></a>10.3 The command atlas

The grammar: `gcloud GROUP [SUBGROUP] VERB NAME --flags`; scope by `--zone`, `--region`, `--global` or
`--location`. The exam tests the **verb and the deciding flag**, not full invocations — this is the index of the
ones worth recognising, each shown in context earlier.

{: .cmds }
| Area | Commands worth recognising |
|:--------------------|:----------------------------------------------------------------------------------------|
| Context | `gcloud config configurations create/activate` · `gcloud config set project P` · `gcloud auth login` (CLI) versus `gcloud auth application-default login` (code) · `gcloud components install kubectl` |
| Hierarchy, billing | `gcloud projects create/delete/undelete` · `gcloud beta projects move P --folder=F` · `gcloud services enable API` · `gcloud billing projects link P --billing-account=B` |
| IAM | `gcloud projects add-iam-policy-binding P --member=M --role=R [--condition=...]` · `set-iam-policy` replaces everything · `gcloud iam roles create/copy/update` |
| Service accounts | `gcloud iam service-accounts create/disable/delete/undelete` · `--impersonate-service-account=SA` · Token Creator on the SA to impersonate it |
| Network | `gcloud compute networks create --subnet-mode=custom` · `subnets expand-ip-range` · `firewall-rules create --target-tags/--target-service-accounts` · `shared-vpc enable` · `networks peerings create` (both sides) · `addresses create` · `routers nats create` |
| Compute | `gcloud compute instances create --provisioning-model=SPOT` · `disks resize` · `snapshots/images/machine-images create` · `instance-groups managed set-autoscaling` · `rolling-action start-update --canary-version / --max-surge` |
| GKE | `gcloud container clusters create-auto` versus `create --num-nodes` (per zone) · `get-credentials` · `node-pools update --enable-autoscaling` · `kubectl apply/rollout undo/scale/autoscale/describe/logs --previous` |
| Serverless | `gcloud run deploy --source . / --image` · `--no-traffic --tag` then `services update-traffic --to-tags` · `--min-instances` · `gcloud functions deploy --trigger-event-filters/--trigger-topic/--trigger-http` · `gcloud app deploy --no-promote` · `gcloud builds submit --tag` |
| Storage and data | `gcloud storage buckets create --default-storage-class` · `buckets update --lifecycle-file/--versioning/--retention-period` · `gcloud storage cp/rsync/sign-url` · `bq query --dry_run` · `bq load` · `gcloud sql instances create --availability-type=REGIONAL` · `sql instances clone --point-in-time` · `promote-replica` |
| Keys and secrets | `gcloud kms keyrings/keys create` · `gcloud beta services identity create --service=S` · `gcloud secrets versions access latest` |
| Operations | `gcloud logging sinks create ... --include-children` · the sink's `writerIdentity` · `gcloud logging buckets create --enable-analytics` · `gcloud logging read FILTER` |

## <a id="s10-4"></a>10.4 The words in a stem, and what they decide

| If the stem says | Reach for |
|:------------------------------------------------|:--------------------------------------------------------|
| "including projects created later" | Bind on the **folder** |
| "including project owners", "even administrators" | **Organization policy** (or deny policy for permissions) |
| "never interrupt the workload" (about spend) | **Budget** |
| "must not exceed", "hard limit" | **Quota** |
| "chargeback by team" | **Labels** + billing export |
| "Free Trial, no domain, want folders" | **Standalone organization** |
| "employee has left, immediately" | **Suspend** the identity |
| "users stay in Entra ID / Okta, no copies" | **Workforce Identity Federation** |
| "GitHub / AWS / on-prem workload, no keys" | **Workload Identity Federation** |
| "no key material", "act as another SA" | **Impersonation** (Token Creator) |
| "expires automatically" | **IAM condition** |
| "elevation only when needed, with approval" | **PAM** |
| "between two predefined roles" | **Custom role** |
| "rotate without redeploying" | **Secret Manager** (volume mount) |
| "control, rotate, revoke the key" | **CMEK** |
| "keys outside Google" | **Cloud EKM** |
| "subnet out of IPs" | **Expand** the range |
| "through the inspection appliance" | **Custom static route** |
| "developers must not widen firewall exposure by editing VMs" | **Secure tags** / service-account targets |
| "every VPC in the org must block X" | **Hierarchical firewall policy** |
| "transitive is not required" | **Peering** |
| "central team owns network" | **Shared VPC** |
| "encrypted, quick, a few Gbps" | **HA VPN** |
| "cannot reach a colocation facility" | **Partner Interconnect** |
| "no external IP, needs internet" | **Cloud NAT** |
| "no external IP, only Google APIs" | **Private Google Access** |
| "partner must allow-list our egress IP" | Cloud NAT with **static IPs** |
| "UDP", "preserve client IP" | **Passthrough** NLB |
| "one anycast IP worldwide" | **Global external ALB**, Premium Tier |
| "cheapest network, one region" | **Standard Tier** |
| "all backends unhealthy" | Allow the **health-check ranges** |
| "scale to zero" | **Cloud Run** |
| "don't manage nodes" | **GKE Autopilot** |
| "OS, kernel, licence, lift-and-shift" | **Compute Engine** |
| "interruptible, checkpoints" | **Spot VMs** |
| "steady 24×7 for three years" | **3-year CUD** |
| "GPU VM fails on maintenance" | `--maintenance-policy=TERMINATE` |
| "JAX, large-scale training" | **TPU** |
| "SSH, no public IP, no bastion" | **IAP** + OS Login |
| "patch the fleet, compliance report" | **VM Manager** |
| "whole VM to another zone" | **Machine image** |
| "boot already hardened" | **Custom image** family |
| "app hung, VM up" | MIG **autohealing** |
| "survive a zone failure" | **Regional** MIG / cluster / disk / Cloud SQL HA |
| "one IP, route by path" | **Ingress / Gateway** |
| "10% to the new version" | Cloud Run **traffic split** / Gateway **weights** / MIG **canary** |
| "fewest steps to a URL" | `gcloud run deploy --source .` |
| "first request slow" | Cloud Run **min instances** |
| "ImagePullBackOff 403" | Node SA `artifactregistry.reader` |
| "Pod needs a bucket, no key" | **Workload Identity Federation for GKE** |
| "on every upload" | **Eventarc** Cloud Storage trigger |
| "read once a year" | **Archive** |
| "access pattern unknown" | **Autoclass** |
| "immutable for N years" | **Retention + Bucket Lock** |
| "no Google account, temporary" | **Signed URL** |
| "SMB", "Windows shares" | **NetApp Volumes** |
| "shared NFS" | **Filestore** |
| "global, strongly consistent, scale writes" | **Spanner** |
| "time series, huge write rate" | **Bigtable** |
| "mobile, real-time sync" | **Firestore** |
| "reports may be seconds stale" | **Read replica** |
| "bad DELETE at a known time" | **PITR** to a new instance |
| "risk across all our databases" | **Database Center** |
| "hundreds of TB, thin pipe" | **Transfer Appliance** |
| "each consumer gets every message" | One **subscription** per consumer |
| "existing Kafka clients" | **Managed Kafka** |
| "reviewable diff before change" | **Terraform plan** |
| "cloud resources as Kubernetes YAML" | **Config Connector** |
| "governed templates for developers" | **Application Design Center** |
| "host our agent" | **Agent Runtime** |
| "no source code on laptops" | **Cloud Workstations** |
| "page someone" | **Alerting policy** |
| "memory metric missing" | **Ops Agent** |
| "which service added latency" | **Cloud Trace** |
| "keep logs N years cheaply" | Sink to **Cloud Storage** |
| "SQL over logs" | **Log Analytics** |
| "who read the data" | **Data Access** logs (enable first) |
| "is it a Google incident" | **Personalized Service Health** |
| "save money on what we run" | **Active Assist** |

