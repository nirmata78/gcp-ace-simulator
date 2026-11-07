---
title: "Part 6 — Containers and serverless"
parent: Theory
nav_order: 6
---

# Part 6 — Containers and serverless
{: .no_toc }

1. TOC
{:toc}

{: .objectives }
> 2.1 kubectl · deploying GKE clusters (Autopilot, regional, private) · deploying containerised applications · serverless deployments and event processing (Pub/Sub, Cloud Storage, Eventarc) · 3.1 cluster inventory · GKE and Artifact Registry · node pools · Kubernetes resources · HPA and VPA · Autopilot Pod resource requests · Cloud Run versions, traffic splitting (Cloud Run, functions, GKE), autoscaling · 4.2 service accounts with a GKE application

<a id="s6-1"></a>

## 6.1 GKE architecture and cluster modes

A GKE cluster is a **Google-managed control plane** (API server, scheduler, etcd) plus **nodes** — Compute Engine
VMs running your Pods. The two modes differ in who owns those nodes.

| | **Autopilot** | **Standard** |
|:------------------------------|:------------------------------------------------|:------------------------------------------------|
| Nodes | **Google** provisions, scales, upgrades, repairs and secures them | **You** configure node pools (with automation you enable) |
| You pay for | **Pod resource requests** (CPU, memory, storage) | **Nodes**, whether Pods fill them or not |
| Topology | Always **regional** | Zonal, multi-zonal or regional |
| Node access, privileged Pods, custom node config | Restricted | Allowed |
| Best-practice defaults (Workload Identity, Shielded nodes, auto-upgrade) | **On and enforced** | Available, you choose |
| Right when | *"We do not want to manage nodes"* | Node-level control, special hardware set-ups, DaemonSets that need host access |

{: .trap }
> <mark markdown="span">**"Do not want to manage nodes" is Autopilot — not Standard with node auto-provisioning and autoscaling.**</mark>
> Automation on a Standard cluster changes how much work the nodes are, not who owns them or how you are billed.

### Cluster topology and access

| Choice | Meaning |
|:----------------------------------|:------------------------------------------------------------------|
| **Zonal** | One control-plane replica in one zone — a zone outage takes the control plane |
| **Regional** | Control plane replicated across **three zones**; nodes spread across them. <mark markdown="span">`--num-nodes` is **per zone**, so `--num-nodes=2` creates **six** nodes</mark> |
| **Private nodes** | Nodes have **internal IPs only** (`--enable-private-nodes`); they need **Cloud NAT** to pull images from the internet, and Private Google Access for Artifact Registry |
| **Control-plane endpoint** | Public endpoint limited by **authorized networks**, a private endpoint only (`--enable-private-endpoint`), or the **DNS-based endpoint** secured by IAM |
| **VPC-native** | Pods and Services take IPs from subnet **secondary ranges** (alias IPs) — the default |
| **Release channel** | Rapid · **Regular** (default) · Stable · Extended; with maintenance windows and exclusions. An exclusion's scope is *no upgrades*, *no minor upgrades* or *no minor or node upgrades* (control-plane patches still allowed); channel clusters can't turn off node auto-upgrade |

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| Autopilot cluster | `gcloud container clusters create-auto shop --location=R` |
| Standard regional cluster — `--num-nodes` is per zone | `gcloud container clusters create batch --location=R --num-nodes=1 --release-channel=regular` |
| Private nodes, control plane limited to a range | `... --enable-private-nodes --enable-master-authorized-networks --master-authorized-networks=203.0.113.0/24` |

<a id="s6-2"></a>

## 6.2 kubectl and cluster access

`gcloud` manages the **cluster** (create, resize, upgrade, delete, node pools); **`kubectl` manages what runs in it**
(Deployments, Services, Pods). `get-credentials` is the bridge: it writes a kubeconfig entry.

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| kubectl and its auth plugin | `gcloud components install kubectl gke-gcloud-auth-plugin` |
| Point kubectl at a cluster | `gcloud container clusters get-credentials shop --location=R` |

**kubectl authenticates with the `gke-gcloud-auth-plugin`**, which uses your gcloud credentials — a missing plugin
is the modern *"kubectl cannot authenticate"* error. Cloud Shell has both pre-installed.

**Authorisation is two layers.** **IAM** grants cluster-wide Kubernetes rights at the project
(`roles/container.viewer`, `container.developer`, `container.admin`). **Kubernetes RBAC** (Roles and RoleBindings)
grants rights **per namespace**, and can bind Google Groups. *"Team A may deploy only in namespace `team-a`"* is
RBAC.

### Viewing cluster inventory

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| What runs, and where | `kubectl get pods -o wide` · `kubectl get deployments,services -n shop` |
| Why a Pod is not running (events) | `kubectl describe pod POD` |
| Logs of the crashed container | `kubectl logs POD --previous` |
| Live CPU and memory | `kubectl top pods` |
| The cluster's node pools | `gcloud container node-pools list --cluster=shop --location=R` |

<a id="s6-3"></a>

## 6.3 Workloads

| Object | For |
|:------------------------------|:------------------------------------------------------------------------|
| **Pod** | One or more containers sharing a network namespace; the smallest unit |
| **Deployment** | **Stateless** replicas, rolling updates, rollback. **The default** |
| **StatefulSet** | **Stable names** (`db-0`, `db-1`), **per-Pod persistent volumes** (`volumeClaimTemplates`), ordered start-up — databases, queues |
| **DaemonSet** | **One Pod per node** — log shippers, node agents |
| **Job / CronJob** | Run to completion, once or on a schedule |
| **ConfigMap / Secret** | Configuration injected as env vars or files (a Secret is only base64 unless encrypted) |
| **PersistentVolumeClaim** | A request for storage, provisioned by a **StorageClass** (`standard-rwo` = balanced PD; Filestore for ReadWriteMany) |

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| Create and expose imperatively | `kubectl create deployment web --image=IMG` · `kubectl expose deployment web --port=80 --target-port=8080` |
| Apply manifests (the normal way) | `kubectl apply -f k8s/` |
| New image, watch it, roll it back | `kubectl set image deployment/web web=IMG:1.5` · `kubectl rollout status deployment/web` · `kubectl rollout undo deployment/web` |
| Scale by hand | `kubectl scale deployment web --replicas=6` |

{: .tip }
> *"Each replica needs its own disk and a stable hostname"* — **StatefulSet**. *"Run exactly one collector on every
> node, including new ones"* — **DaemonSet**. *"Nightly clean-up at 02:00"* — **CronJob**.

<a id="s6-4"></a>

## 6.4 Exposing workloads and splitting traffic

| Object | Gives you | Load balancer |
|:------------------------------|:----------------------------------------------------------|:------------------------------------------|
| Service **ClusterIP** (default) | A stable internal virtual IP inside the cluster | None |
| Service **NodePort** | A port on every node's IP | None |
| Service **LoadBalancer** | An IP for **one** Service | An external **passthrough Network LB** — or an internal one with the annotation `networking.gke.io/load-balancer-type: "Internal"` |
| **Ingress** | **One** HTTP(S) entry point with **host and path rules** to many Services | An **Application LB** (external; `gce-internal` class for internal) |
| **Gateway API** (Gateway + HTTPRoute) | Ingress's successor: role separation, header matching, **weighted traffic splitting** | An Application LB chosen by GatewayClass |

GKE uses **container-native load balancing** — the LB targets Pod IPs directly through NEGs — which removes a hop
and makes health checks per Pod.

{: .key }
> <mark markdown="span">**Path or host routing, or one IP for many Services, means Ingress or Gateway.**</mark> A `LoadBalancer` Service is one IP
> for one Service at layer 4 — three apps behind *"one external IP routed by URL path"* is one Ingress, not three
> LoadBalancer Services.

### Traffic splitting on GKE

{: .new-title }
> New in the June 2026 guide — traffic splitting now includes GKE
>
> Cloud Run and Cloud Run functions split traffic between **revisions** natively ([§6.10](#s6-10)). On GKE, the native
> mechanism is the **Gateway API**: an `HTTPRoute` whose `backendRefs` carry **weights** sends, say, 90% to the
> Service in front of v1 and 10% to the Service in front of v2. The older approximation — two Deployments behind
> one Service, split by replica counts — is coarse and ties the split to capacity.


<a id="s6-5"></a>

## 6.5 Scaling Pods and nodes; Autopilot resource requests

| Layer | Mechanism | Scales |
|:----------------------|:------------------------------------------|:------------------------------------------------------|
| Pods, horizontally | **HorizontalPodAutoscaler** | Replica count on CPU, memory, custom or external metrics |
| Pods, vertically | **VerticalPodAutoscaler** | Each Pod's **requests** — recommend only, or apply by recreating Pods |
| Nodes (Standard) | **Cluster autoscaler** per node pool; **node auto-provisioning** creates pools | Node count to fit pending Pods |
| Nodes (Autopilot) | Automatic | Whatever the Pods request |

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| Horizontal Pod Autoscaler | `kubectl autoscale deployment web --cpu-percent=60 --min=3 --max=30` |
| Vertical Pod Autoscaling (Standard) | `gcloud container clusters update batch --location=R --enable-vertical-pod-autoscaling` |
| Cluster autoscaler on a node pool | `gcloud container node-pools update default-pool --cluster=batch --location=R --enable-autoscaling --min-nodes=1 --max-nodes=10` |

{: .watch }
> **HPA versus VPA.** HPA adds Pods; VPA resizes them. Do not let both act on the **same CPU or memory metric** for
> one workload — they fight. A common pattern is HPA on a custom metric (requests per second) with VPA managing
> requests, or VPA in *recommendation* mode only.

{: .new-title }
> New in the June 2026 guide — managing Autopilot Pod resource requests
>
> **In Autopilot, resource requests are the bill and the scheduling input**, so the platform enforces them:
>
> - A container with **no requests** gets **defaults** applied (for the general-purpose compute class, on the order
>   of 0.5 vCPU and 2 GiB — *verify*).
> - Requests below the **minimums**, or with a **CPU-to-memory ratio** outside the allowed range, are **adjusted
>   upward** automatically; values are rounded to allowed increments. `kubectl get pod -o yaml` shows the result, and
>   a warning explains the change.
> - **Limits** equal requests unless the cluster supports **Pod bursting** (recent versions, cgroup v2): then a
>   **limit above the request** lets the Pod use spare node capacity while you pay only for the request.
> - **Hardware per workload, not per pool**: Arm with `nodeSelector: kubernetes.io/arch: arm64` (an arm64 image; older
>   versions also name an Arm compute class); a machine family with the **Performance** class plus
>   `cloud.google.com/machine-family: c3`. Autopilot has no node pools to create.
> - **Compute classes** select hardware: the default general-purpose class, **Balanced**, **Scale-Out**,
>   **Performance**, **Accelerator** — requested with a `nodeSelector` of `cloud.google.com/compute-class`; Spot Pods
>   with `cloud.google.com/gke-spot: "true"`.
>
> *"Autopilot Pods cost more than expected"* — look for missing or oversized requests, and use VPA
> recommendations to right-size them. *"A Pod was scheduled with more memory than we asked for"* — ratio or
> minimum enforcement.

<a id="s6-6"></a>

## 6.6 Node pools and upgrades (Standard)

A **node pool** is a group of identically configured nodes — a managed instance group under the hood.

| Task | How |
|:------------------------------------------|:----------------------------------------------------------------|
| Add capacity of a **new kind** (GPUs, high memory, Spot, Arm) | `gcloud container node-pools create` with the new machine type and labels / taints |
| Change machine type of existing nodes | `gcloud container node-pools update --machine-type` recreates the nodes with the pool's upgrade strategy (*verify*). To test first and keep a fallback, **create a new pool**, cordon and drain the old one, delete it later |
| Resize | `gcloud container clusters resize CLUSTER --node-pool=POOL --num-nodes=N` |
| Autoscale | `--enable-autoscaling --min-nodes --max-nodes` (per zone), or `--total-min-nodes` / `--total-max-nodes` |
| Keep workloads on the right pool | **Node labels + `nodeSelector` / affinity**; **taints + tolerations** to keep everything else off |
| Remove | `gcloud container node-pools delete` (Pods are rescheduled elsewhere) |
| Upgrades | **Surge** upgrades (`max-surge`, `max-unavailable`) or **blue-green** upgrades per pool |


<a id="s6-7"></a>

## 6.7 Artifact Registry and image access

**Artifact Registry** stores container images and language packages (Maven, npm, Python, Go, apt, yum, Helm charts
as OCI). **Container Registry is shut down** — `gcr.io` paths are now served by Artifact Registry. Repositories are
**regional or multi-regional** and addressed as `LOCATION-docker.pkg.dev/PROJECT/REPO/IMAGE:TAG`.

| Mode | Is |
|:----------------|:----------------------------------------------------------------------|
| **Standard** | Your own artefacts |
| **Remote** | A caching proxy of an upstream (Docker Hub, Maven Central, PyPI) — builds survive upstream rate limits and outages |
| **Virtual** | One endpoint aggregating several repositories |

**Cleanup policies** delete old versions automatically; **Artifact Analysis** scans images for vulnerabilities.

| Role | Grants |
|:--------------------------------------|:----------------------------------------------------|
| `roles/artifactregistry.reader` | Pull |
| `roles/artifactregistry.writer` | Push and pull |
| `roles/artifactregistry.repoAdmin` / `admin` | Manage repositories and artefacts |

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| Docker repository | `gcloud artifacts repositories create shop --repository-format=docker --location=R` |
| Let the local Docker CLI push to it | `gcloud auth configure-docker R-docker.pkg.dev` |

### Configuring GKE to pull from Artifact Registry

<mark markdown="span">**Nodes pull images as the node pool's service account.**</mark> No `imagePullSecrets` are needed; what is needed is
**`roles/artifactregistry.reader` for that service account** on the repository (or its project).

- **Same project, default Compute Engine service account with Editor** — it just works (and is too broad).
- **Recommended: a minimal custom node service account** (`roles/container.defaultNodeServiceAccount`) — then you
  **must grant it `artifactregistry.reader`** explicitly.
- **Repository in another project** — grant the node service account reader **on that repository**.
- **Private nodes** reach Artifact Registry through **Private Google Access**; pulling from Docker Hub needs Cloud
  NAT, or a **remote repository**.

{: .trap }
> *"Pods are stuck in `ImagePullBackOff` with 403 from `pkg.dev`"* is the node service account lacking
> `artifactregistry.reader` — not a missing `docker login`, not a public repository, and not a service-account key
> in an `imagePullSecret`.

<a id="s6-8"></a>

## 6.8 Workload Identity Federation for GKE

{: .new-title }
> New in the June 2026 guide — a Google Cloud service account with a GKE application
>
> **Pods authenticate to Google APIs as a Kubernetes service account (KSA) that IAM recognises**, so no key is mounted
> and Pods do not borrow the node's identity. It is enabled by default on Autopilot; on Standard, enable a
> **workload pool** on the cluster and the **GKE metadata server** on node pools.

**Two ways to grant access, both keyless:**

{: .cmds }
| Step | What you configure |
|:------------------------------------|:----------------------------------------------------------------------|
| Enable it (Standard; on by default in Autopilot) | `gcloud container clusters update batch --location=R --workload-pool=P.svc.id.goog` |
| (a) Grant IAM straight to the Kubernetes service account | member `principal://iam.googleapis.com/projects/NUM/locations/global/workloadIdentityPools/P.svc.id.goog/subject/ns/shop/sa/web` |
| (b) Let it impersonate a Google service account | `roles/iam.workloadIdentityUser` on the Google SA for member `serviceAccount:P.svc.id.goog[shop/web]`, then annotate the KSA with `iam.gke.io/gcp-service-account=GSA_EMAIL` |

The Pod spec names `serviceAccountName: web`. Client libraries then find credentials through ADC with no change.

{: .watch }
> **Node service account versus workload identity.** The **node** service account is for the node's own jobs —
> pulling images, writing logs and metrics. **Application** access to Cloud Storage, Pub/Sub or BigQuery belongs to
> the **Pod's** identity through Workload Identity Federation for GKE. Granting app roles to the node account gives
> them to every Pod on the node.

One limitation is worth knowing: **Pods that use the host network (`hostNetwork: true`) cannot use Workload Identity
Federation for GKE** — they reach the node's metadata server and act as the node's service account.

<a id="s6-9"></a>

## 6.9 Cloud Run services and jobs

**Cloud Run runs containers without servers or clusters**, billed per use, scaling automatically — to zero when
idle.

| Resource | Is |
|:----------------------|:----------------------------------------------------------------------|
| **Service** | Serves **requests** (HTTP, gRPC, WebSockets) at a stable HTTPS URL; scales on load |
| **Job** | Runs **tasks to completion** — in parallel, with retries — on demand or on a schedule via Cloud Scheduler |
| **Worker pool** | Always-on, non-request workloads such as queue consumers (*recognise*) |
| **Revision** | An **immutable** snapshot of a service's code and configuration, created by every deploy |

### Deploying

| Route | Steps | When |
|:--------------------------|:------------------------------|:----------------------------|
| **`gcloud run deploy SVC --source .`** | **One**: Cloud Build builds (Dockerfile or buildpacks), stores in Artifact Registry, deploys | *"Fewest steps from source to a URL"* |
| `gcloud run deploy SVC --image=IMAGE` | One | The image already exists |
| `docker build` + `push` + `deploy` | Three, plus a local Docker daemon | You need control of the build |
| Cloud Build trigger / Cloud Deploy pipeline | A pipeline | **Continuous** delivery on every commit |

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| Deploy from source, private, as its own identity | `gcloud run deploy api --source . --region=R --no-allow-unauthenticated --service-account=SA_EMAIL` |
| Run-to-completion job | `gcloud run jobs create nightly-export --image=IMG --tasks=20 --max-retries=3` · `gcloud run jobs execute nightly-export` |

### Access and networking

| Setting | Options |
|:----------------------------------|:------------------------------------------------------------------|
| **Authentication** | *Require authentication* — callers need **`roles/run.invoker`** and send an **ID token**; or *allow unauthenticated* (`allUsers` invoker) for public sites |
| **Ingress** | `all` · `internal` (VPC and some Google sources only) · `internal-and-cloud-load-balancing` |
| **Egress to a VPC** | **Direct VPC egress** (recommended) or a Serverless VPC Access connector — for private IPs such as Cloud SQL or Memorystore |
| **Static outbound IP** | Route all egress through the VPC and **Cloud NAT** with a static address |
| **Custom domain / CDN / WAF** | A **global external Application LB with a serverless NEG** — then Cloud CDN, Cloud Armor, IAP (enable IAP on the backend service and grant users **IAP-secured Web App User**, `roles/iap.httpsResourceAccessor`; the same works for MIG backends) |
| **Identity** | A **dedicated service account** per service, never the default Compute account |
| **Secrets** | `--set-secrets=DB_PASS=db-password:latest` (env) or `/secrets/db=db-password:latest` (volume) ([§3.13](03-identity-access.md#s3-13)). An env var is resolved when the instance **starts**; a volume is read from Secret Manager **each time the file is read**, so it picks up rotation without a deploy. The runtime service account needs **Secret Accessor** on the secret |

{: .tip }
> *"Service A must call private service B"* — grant **B's `run.invoker` to A's service account**; A attaches an ID
> token for B's URL. Making B public and checking a header is the distractor.

<a id="s6-10"></a>

## 6.10 Cloud Run revisions, traffic and scaling

<mark markdown="span">**Every deploy creates a revision, and by default sends it 100% of traffic immediately.**</mark> A gradual rollout is a
deliberate two-step:

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| 1. Deploy at 0%, reachable on its own tag URL | `gcloud run deploy api --image=IMG:v2 --no-traffic --tag=canary` |
| 2. Send it 10% | `gcloud run services update-traffic api --to-tags=canary=10` |
| Promote; roll back | `gcloud run services update-traffic api --to-latest` · `... --to-revisions=api-00041-xyz=100` |

{: .key }
> **Revisions are immutable and stay addressable**, so a canary is a traffic percentage and a rollback is one
> command that points traffic back — no rebuild, no DNS change. DNS weighting against a native split is always the
> wrong answer: it is cached, coarse and slow to reverse.

### Autoscaling settings

| Setting | Meaning | Default |
|:----------------------------------|:------------------------------------------------------------------|:------------|
| **Minimum instances** | Kept warm to avoid **cold starts**; above 0, the service no longer idles to zero cost | 0 |
| **Maximum instances** | Ceiling — protects a database from connection storms and caps cost | 100 (*verify*) |
| **Concurrency** | Requests handled **at once by one instance** | 80 (max 1000) |
| **Billing / CPU allocation** | **Request-based** (CPU only while handling requests) or **instance-based** (CPU always, for background work) | Request-based |
| Startup CPU boost | Extra CPU during start-up | Off |
| Request timeout | Per request | 5 min (up to 60) |

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| Warm instances, a cap, requests per instance | `gcloud run services update api --min-instances=2 --max-instances=40 --concurrency=50` |
| CPU outside requests (instance-based billing) | `gcloud run services update worker --no-cpu-throttling` |

{: .tip }
> *"First request after idle is slow"* — **minimum instances** (or startup CPU boost). *"The database runs out of
> connections at peak"* — **maximum instances** and/or lower **concurrency**. *"A single-threaded app misbehaves
> under load"* — **concurrency 1**. *"Work continues after the response is sent"* — **instance-based billing**.

<a id="s6-11"></a>

## 6.11 Cloud Run functions and events

**Cloud Run functions** (formerly Cloud Functions) are functions deployed **as Cloud Run services** — you write a
handler; Google builds and runs the container. So revisions, traffic splitting, scaling, concurrency, VPC egress
and IAM work exactly as in [§6.9](#s6-9)–[§6.10](#s6-10).

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| Fire on every upload to a bucket | `gcloud functions deploy thumb --gen2 --runtime=python312 --trigger-event-filters="type=google.cloud.storage.object.v1.finalized" --trigger-event-filters="bucket=lumen-uploads"` |
| Fire on a Pub/Sub message; on HTTP | `--trigger-topic=orders` · `--trigger-http` |

### Where events come from

| Source | Mechanism | Notes |
|:------------------------------------------|:----------------------------------------|:------------------------------------------------|
| **HTTP** | Direct request | Authenticated with an ID token unless public |
| **Pub/Sub message** | Eventarc creates a **push subscription** | At-least-once; make handlers idempotent |
| **Cloud Storage** object *finalized*, *deleted*, *archived*, *metadataUpdated* | Eventarc, via Pub/Sub under the hood | The trigger must be in the **bucket's region**; the **Cloud Storage service agent needs `roles/pubsub.publisher`** |
| **Eventarc direct events** from Google services | Eventarc trigger | Filtered by event type and attributes |
| **Cloud Audit Log events** — *"when anyone creates a VM"* | Eventarc on an audit log entry | Needs the relevant audit log type **enabled** (Data Access for reads) |
| Third-party / custom | Eventarc channels, Eventarc Advanced buses | *Recognise* |

**Eventarc** routes events from sources to targets — Cloud Run services, functions, GKE services, Workflows. A
trigger has **filters**, a **destination**, and a **service account** that needs `roles/eventarc.eventReceiver`
and `roles/run.invoker` on the target.


{: .trap }
> **"The function never fires on uploads."** Check, in order: the trigger's region matches the bucket's; the Cloud
> Storage **service agent** has `pubsub.publisher`; the trigger service account can invoke the function; the event
> type is `finalized`, not `metadataUpdated`. Polling the bucket from a VM is the assembled distractor.

**Deploying from Cloud Run.** A function can also be deployed with the Cloud Run command itself —
`gcloud run deploy thumb --source . --function=make_thumbnail --base-image=python312 --region=R` — which makes
the "a function *is* a Cloud Run service" point concrete.

**Retries.** Event-driven functions may enable **retry on failure** — useful for transient errors, dangerous
without idempotency, because a permanent bug then retries until the event expires.

<a id="s6-12"></a>

## 6.12 App Engine, Cloud Build and delivery

### App Engine — recognise it

App Engine is the original serverless platform. <mark markdown="span">**One App Engine application per project, and its region can
never change.**</mark> **Standard** environment: sandboxed runtimes, scales to zero, fast start. **Flexible**: containers on
VMs, **minimum one instance**, no scale-to-zero. Services have **versions**; traffic splits between versions by
percentage, and `gcloud app deploy --no-promote` deploys without moving traffic.

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| Deploy without moving traffic | `gcloud app deploy --no-promote --version=v7` |
| Split traffic 90/10 | `gcloud app services set-traffic default --splits=v6=0.9,v7=0.1` |

Where App Engine appears on the current exam it is mostly a distractor for *"scale to zero"* (flexible cannot) or
*"a new region"* (the region is permanent).

### Cloud Build and Cloud Deploy

**Cloud Build** runs a `cloudbuild.yaml` of container **steps** — build, test, push, deploy — on **triggers**
(push to a branch, tag, pull request) or on demand. It runs as a **service account**; best practice is a
**user-specified** service account with only the roles the pipeline needs (for example `run.developer` plus
`iam.serviceAccountUser` on the runtime account). **Cloud Deploy** adds managed release pipelines to GKE and Cloud
Run, with promotion between targets, approvals and **canary** strategies.

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| Build and push an image without local Docker | `gcloud builds submit --tag=R-docker.pkg.dev/P/shop/web:1.6 .` |

### More to recognise

- **Operating GKE.** Enrol production in the **Stable** release channel. The control plane's **DNS-based
  endpoint** is authorised by IAM, so no bastion or IP allow-list is needed. A **PodDisruptionBudget** limits
  evictions during drains. **Blue-green node pool upgrades** keep old nodes for a soak period. Environment
  variables from a ConfigMap change only after **`kubectl rollout restart`**. `kubectl get pods -A
  –field-selector=status.phase=Pending` lists every Pending Pod. An HPA on the external metric
  **`num_undelivered_messages`** scales Pub/Sub consumers. HPA utilisation is usage divided by **request**, so
  oversized requests delay scaling.
- **Sharing accelerators.** **GPU time-sharing** gives several Pods turns on one GPU; **multi-instance GPUs**
  partition an A100/H100 into isolated slices with their own memory.
- **Images and serverless.** An Artifact Registry **remote repository** caches Docker Hub and avoids its rate
  limits. Cloud Run **maximum instances** protects a database's connection limit. **Direct VPC egress** reaches
  private IPs without connector instances. Cloud Run functions react to **Firestore document events** through
  Eventarc. Choose the **snapshot storage location** explicitly when residency requires a region.

<a id="s6-13"></a>

## 6.13 Part 6 recall card

| Prompt | Answer |
|:------------------------------------------------|:--------------------------------------------------------|
| No node management | **Autopilot** (always regional) |
| Regional Standard, `--num-nodes=2` | **Six** nodes (per zone × 3) |
| Nodes with internal IPs only | `--enable-private-nodes` (+ Cloud NAT for internet pulls) |
| kubectl cannot authenticate | Install **`gke-gcloud-auth-plugin`**; `get-credentials` |
| Namespace-level permissions | **Kubernetes RBAC** |
| Stable names + per-replica disks | **StatefulSet** |
| One Pod on every node | **DaemonSet** |
| One IP, path routing to many Services | **Ingress** or **Gateway** |
| 10% to v2 on GKE | **Gateway API HTTPRoute weights** |
| More replicas on load | **HPA**; right-size requests: **VPA** |
| Autopilot Pod got more memory than requested | **Minimum / ratio enforcement** on requests |
| Change node machine type | `node-pools update --machine-type` recreates nodes (upgrade strategy); to keep a fallback, **new node pool**, drain old |
| `ImagePullBackOff` 403 from `pkg.dev` | Node SA needs **`artifactregistry.reader`** |
| Pod reads a bucket, no key | **Workload Identity Federation for GKE** |
| Source to URL, one command | `gcloud run deploy --source .` |
| Canary 10% on Cloud Run | `--no-traffic --tag`, then `update-traffic --to-tags=tag=10` |
| Cold starts | **Min instances** |
| DB connection storms | **Max instances** / lower concurrency |
| Service A calls private service B | A's SA gets **`run.invoker`** on B; ID token |
| Custom domain + Cloud Armor for Cloud Run | Global external ALB + **serverless NEG** |
| Function on bucket upload never fires | Region match; GCS **service agent** `pubsub.publisher` |
| React to "VM created" anywhere | **Eventarc** audit-log trigger |


