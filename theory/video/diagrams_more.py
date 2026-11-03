# ── Part 2 ─────────────────────────────────────────────────────────────────────────────────
d = c4.Diagram(1600, 780)
d.node("o", 560, 10, 480, 110, "focus", "Organization", "root", "", size=30)
d.node("f1", 120, 190, 400, 110, "system", "Folder: Finance", "up to 10 levels", "", size=28)
d.node("f2", 600, 190, 400, 110, "system", "Folder: Engineering", "", "", size=28)
d.node("pd", 1120, 190, 420, 110, "container", "Project directly under org", "", "", size=26)
d.node("p1", 20, 370, 300, 110, "container", "Project fin-prod", "", "", size=26)
d.node("p2", 350, 370, 300, 110, "container", "Project fin-dev", "", "", size=26)
d.node("f3", 680, 370, 340, 110, "system", "Folder: Platform", "", "", size=28)
d.node("p3", 700, 550, 300, 100, "container", "Project plat-prod", "", "", size=26)
d.node("r1", 20, 550, 300, 100, "component", "VM · bucket", "resources", "", size=26)
d.node("r2", 350, 550, 300, 100, "component", "Cloud SQL · topic", "resources", "", size=26)
for a, b in [("o","f1"),("o","f2"),("o","pd"),("f1","p1"),("f1","p2"),("f2","f3"),("f3","p3"),("p1","r1"),("p2","r2")]:
    d.edge(a, b, "", src="b", dst="t", dashed=False)
d.note(1060, 400, 510, "The project is the boundary for billing linkage, quota, API enablement and, by default, networking.", size=26, colour=BLUE, bg=BLUE_BG)
d.text(40, 730, "IAM allow policies and organization policies both flow downward from every node to everything beneath it.", size=29, colour=RED, bold=True)
d.save(OUT / "p2-hierarchy.svg")
row("p2-two-routes", [
    ("Cloud Identity or Workspace", "verify a domain", "Org created when the customer makes the first project or billing account. Named after the domain. Holds managed users and groups."),
    ("Standalone organization", "new in the guide", "Created automatically for a new Free Trial customer. Named after the user, never a domain. Google accounts and workforce pool principals.", "focus"),
], box=350, h=430, size=33)
d = c4.Diagram(1600, 560)
d.node("p", 60, 90, 420, 170, "container", "Project P", "needs a grant here", "Project Billing Manager, or Owner", size=30)
d.node("b", 1120, 90, 420, 170, "focus", "Billing account B", "and a grant here", "Billing Account User", size=30)
d.node("u", 620, 90, 360, 170, "ask", "The person linking", "", "", size=30)
d.edge("u", "p", "permission on P", "", src="l", dst="r", at=(490, 70), width=130)
d.edge("u", "b", "permission on B", "", src="r", dst="l", at=(990, 70), width=130)
d.note(60, 330, 1480, "Owner of the project alone cannot attach it to an account it has no role on. This two-sided rule is the most examined billing fact.", size=29, colour=RED, bg=RED_BG)
d.save(OUT / "p2-link-both.svg")
row("p2-budget-flow", [
    ("Budget", "threshold rules", "50, 90, 100% of actual or forecast spend"),
    ("Pub/Sub topic", "programmatic route", "The budget publishes a message"),
    ("Cloud Run function", "your code", "Subscribes, decides, acts"),
    ("Action", "with a cost", "Scale down, notify, or disable billing", "focus"),
], arrows=True, note="There is no built-in stop switch. And disabling billing shuts services down and can delete resources.", tone="r", box=300, h=520)
row("p2-three-errors", [
    ("API not enabled", "\"has not been used in project\"", "Enablement problem. Fix: gcloud services enable"),
    ("403 PERMISSION_DENIED", "authenticated, not allowed", "An IAM grant is missing. Fix: grant the role"),
    ("401 UNAUTHENTICATED", "no valid credentials", "Nobody is logged in. Fix: authenticate", "focus"),
], box=320, h=390)

# ── Part 3 ─────────────────────────────────────────────────────────────────────────────────
row("p3-three-systems", [
    ("Does it exist?", "identity", "Cloud Identity, Workspace, an external IdP via federation, or a service account"),
    ("What may it do, where?", "IAM", "Allow policies, deny policies, conditions"),
    ("What is permitted at all?", "organization policy", "Configurations removed for everyone, owners included", "focus"),
], note="Three questions, three systems. Keep them apart and most distractors fall away.", box=330, h=530)
d = c4.Diagram(1600, 700)
d.node("o", 60, 20, 420, 110, "system", "Organization", "", "Sam: Viewer", size=28)
d.node("f", 60, 190, 420, 110, "system", "Folder: Finance", "", "group finance-eng: Editor", size=28)
d.node("p", 60, 360, 420, 110, "container", "Project fin-prod", "", "Sam: Storage Admin", size=28)
d.node("b", 60, 530, 420, 110, "component", "Bucket fin-data", "", "Ana: Object Viewer", size=28)
for a, b in [("o","f"),("f","p"),("p","b")]: d.edge(a, b, "", src="b", dst="t", dashed=False)
d.node("eff", 760, 150, 780, 200, "focus", "Sam's effective access on the bucket", "union of every binding that reaches Sam", "Viewer + Editor (through the group) + Storage Admin", size=30)
d.note(760, 400, 780, "A lower policy cannot remove a higher grant. There is no \"most specific wins\" and no negative binding.", size=27, colour=RED, bg=RED_BG)
d.note(760, 540, 780, "Only a deny policy or an organization policy subtracts.", size=27, colour=BLUE, bg=BLUE_BG)
d.save(OUT / "p3-inheritance.svg")
d = c4.Diagram(1600, 560)
d.node("po", 60, 70, 420, 160, "person", "Principal", "who", "user, group, serviceAccount, principalSet", size=30)
d.node("ro", 590, 70, 420, 160, "focus", "Role", "what", "a bundle of permissions", size=30)
d.node("re", 1120, 70, 420, 160, "container", "Resource", "where", "org, folder, project, or one resource", size=30)
d.edge("po", "ro", "bound to", "", src="r", dst="l", at=(490, 55), width=90)
d.edge("ro", "re", "on", "", src="r", dst="l", at=(1050, 55), width=40)
d.note(60, 300, 1480, "A policy is a list of bindings, plus an etag for safe concurrent edits, and version 3 when conditions are present. Each resource has at most one allow policy.", size=28, colour=BLUE, bg=BLUE_BG)
d.save(OUT / "p3-binding.svg")
seq("p3-workforce", [("u","Employee (Entra ID)","person"),("idp","External IdP","ext"),("g","Google sign-in / STS","system"),("pool","Workforce pool provider","container"),("iam","IAM on the resource","focus")], [
    ("m","u","g","open console via federated sign-in"),
    ("m","g","idp","redirect: authenticate me (OIDC or SAML)"),
    ("r","idp","g","assertion with subject and groups"),
    ("m","g","pool","check attribute condition, map attributes"),
    ("n","pool","pool","google.groups must be mapped","a"),
    ("r","pool","u","session, 15 min to 12 h, set per pool"),
    ("m","u","iam","action as principalSet .../group/finance","hl"),
    ("r","iam","u","allowed if a binding matches"),
])
seq("p3-attach", [("dev","Engineer","person"),("run","Cloud Run or VM","container"),("md","Metadata server","system"),("api","Google API","ext")], [
    ("n","dev","dev","holds Service Account User on app@","a"),
    ("m","dev","run","deploy with --service-account=app@","hl"),
    ("m","run","md","give me a token for app@"),
    ("r","md","run","short-lived access token"),
    ("m","run","api","call with token"),
    ("r","api","run","allowed by roles granted to app@"),
    ("n","run","api","nothing stored, nothing rotated by hand","g"),
])
seq("p3-impersonate", [("ci","ci@ or an engineer","person"),("cred","IAM Credentials API","system"),("api","Google API","ext"),("log","Audit log","container")], [
    ("n","ci","ci","holds Token Creator on deployer@","a"),
    ("m","ci","cred","generateAccessToken for deployer@","hl"),
    ("r","cred","ci","short-lived token, 1 hour by default"),
    ("m","ci","api","call as deployer@"),
    ("a","api","log","records both deployer@ and the caller"),
    ("n","log","log","serviceAccountDelegationInfo names the original caller","g"),
])
seq("p3-wif", [("gh","GitHub Actions job","ext"),("sts","Google STS","system"),("pool","Pool and provider (project)","container"),("sa","deployer@ service account","focus"),("api","Google API","ext")], [
    ("n","gh","gh","permissions: id-token: write","a"),
    ("m","gh","sts","present the job's OIDC token"),
    ("m","sts","pool","validate; apply attribute condition","hl"),
    ("r","sts","gh","federated token"),
    ("f","alt","direct grant, or via a service account"),
    ("m","gh","api","(a) call directly as principal"),
    ("m","gh","sa","(b) impersonate, needs workloadIdentityUser"),
    ("m","sa","api","call with a short-lived token"),
    ("e",),
])
row("p3-federations", [
    ("Workforce", "people", "Users from Entra ID, Okta, AD FS. Pool at the organization. No Google account, no sync."),
    ("Workload", "software", "AWS, Azure, GitHub, on-premises. Pool in a project. No service-account key.", "focus"),
], note="Same machinery, different subjects. Read who is signing in, and where the pool lives.", box=320, h=500)
row("p3-secret-forms", [
    ("Env variable", "resolved at instance start", "A new version arrives only with a new instance or revision"),
    ("File volume", "read at access time", "A new version is picked up without a redeploy", "focus"),
    ("Direct API call", "your code chooses", "Pass a version, or latest"),
], box=300, h=350)

# ── Part 4 ─────────────────────────────────────────────────────────────────────────────────
d = c4.Diagram(1600, 660)
d.boundary(20, 20, 1560, 540, "VPC vpc-prod: global, firewall rules and routes belong here", "one network, all regions")
d.boundary(60, 60, 680, 380, "Region europe-central2", "subnet web-euc2 10.10.0.0/20", colour="#2d8a4e")
d.boundary(860, 60, 680, 380, "Region us-central1", "subnet web-usc1 10.20.0.0/20", colour="#2d8a4e")
d.node("a", 110, 110, 260, 130, "container", "VM in zone a", "", "10.10.0.5", size=27)
d.node("b", 430, 110, 260, 130, "container", "VM in zone b", "", "10.10.0.6", size=27)
d.node("c", 1090, 110, 260, 130, "container", "VM in zone c", "", "10.20.0.7", size=27)
d.edge("b", "c", "", "", src="r", dst="l", dashed=False, colour="#c8341f")
d.text(800, 300, "internal IPs: no VPN, no peering", size=25, colour="#c8341f", bold=True, anchor="middle")
d.note(20, 590, 1560, "Subnets are regional, spanning all zones of the region. VPCs are isolated from each other by default, even within one project.", size=27, colour=BLUE, bg=BLUE_BG)
d.save(OUT / "p4-vpc.svg")
row("p4-firewall-order", [
    ("1 Org hierarchical", "policy", "Applies to every VPC beneath"),
    ("2 Folder hierarchical", "top down", "Then each folder in turn"),
    ("3 VPC rules + global policy", "order configurable", "On the one network"),
    ("4 Regional policy", "", "One VPC, one region"),
    ("5 Implied rules", "lowest priority", "Allow egress, deny ingress", "focus"),
], arrows=True, note="Evaluated top to bottom, and it stops at the first allow or deny. goto_next hands evaluation down to the next level.", box=300, h=500, size=24)
row("p4-tag-vs-sa", [
    ("Network tag", "plain string", "Anyone able to edit the VM can add it. Adding web silently opens the VM to the web rule."),
    ("Target service account", "guarded by IAM", "Only someone who may attach that account, while the VM is stopped."),
    ("Secure tag", "guarded by IAM", "Attaching a value needs tagUser. Works in firewall policies.", "focus"),
], note="Network tags work only in VPC firewall rules. Firewall policies use secure tags, not network tags.", tone="r", box=340, h=530)
d = c4.Diagram(1600, 700)
d.boundary(20, 20, 720, 650, "Host project", "owns the VPC", colour="#c8341f")
d.node("v", 70, 60, 620, 130, "focus", "Shared VPC network", "subnets, routes, firewalls", "central network team", size=30)
d.node("s1", 70, 220, 620, 100, "container", "subnet web", "", "", size=28)
d.node("s2", 70, 350, 620, 100, "container", "subnet data", "", "", size=28)
d.note(70, 480, 620, "Network User on one subnet is the least-privilege grant.", size=25, colour=AMBER, bg=AMBER_BG)
d.node("p1", 960, 190, 600, 150, "system", "Service project: team A", "own IAM, own billing", "its VMs live in subnet web", size=28)
d.node("p2", 960, 370, 600, 150, "system", "Service project: team B", "own IAM, own billing", "its VMs live in subnet data", size=28)
d.edge("p1", "s1", "attached", "", src="l", dst="r", at=(830, 235), width=120, size=24)
d.edge("p2", "s2", "attached", "", src="l", dst="r", at=(830, 425), width=120, size=24)
d.note(960, 545, 600, "A service project attaches to one host. A host cannot also be a service project. Needs an organization.", size=24, colour=BLUE, bg=BLUE_BG)
d.save(OUT / "p4-shared-vpc.svg")
d = c4.Diagram(1600, 560)
d.node("a", 60, 90, 340, 170, "container", "VPC A", "", "", size=34)
d.node("b", 630, 90, 340, 170, "container", "VPC B", "", "", size=34)
d.node("c", 1200, 90, 340, 170, "container", "VPC C", "", "", size=34)
d.edge("a", "b", "peered", "", src="r", dst="l", at=(430, 70), width=170, size=26, dashed=False, both=True)
d.edge("b", "c", "peered", "", src="r", dst="l", at=(1000, 70), width=170, size=26, dashed=False, both=True)
d.edge("a", "c", "A cannot reach C", "", src="b", dst="b", via=[(230, 340), (1370, 340)], at=(640, 330), width=320, size=30, colour="#c8341f")
d.note(60, 400, 1480, "Both sides must create it. No overlapping ranges. Subnet routes are exchanged; custom routes only with export and import; firewall rules are never exchanged.", size=27, colour=AMBER, bg=AMBER_BG)
d.save(OUT / "p4-peering.svg")
row("p4-hybrid-pick", [
    ("HA VPN", "2 Gbps, encrypted, next week", "IPsec over the internet. 99.99% with two interfaces, two tunnels. Needs Cloud Router."),
    ("Dedicated Interconnect", "20 Gbps, in a Google colo", "Your own 10 or 100 Gbps circuits. High, steady bandwidth."),
    ("Partner Interconnect", "5 Gbps, no colo nearby", "Through a provider, 50 Mbps to 50 Gbps per attachment."),
], note="Interconnect is not encrypted by default: add MACsec on Dedicated, or HA VPN over Interconnect.", tone="r", box=360, h=540, size=30)
row("p4-pga-vs-nat", [
    ("Private VM", "no external IP", "needs to reach something outside", "person"),
    ("Private Google Access", "per-subnet setting", "Reaches Google APIs only: Cloud Storage, BigQuery."),
    ("Cloud NAT", "regional, on Cloud Router", "Reaches the internet, outbound only: package mirrors, a partner API.", "focus"),
], note="A private VM that needs only Cloud Storage and BigQuery needs PGA and nothing else.", box=340, h=530)
row("p4-dns-direction", [
    ("Forwarding zone", "Cloud → on-premises", "Cloud VMs must resolve corp.local: send queries to on-premises resolvers."),
    ("Inbound server policy", "on-premises → Cloud", "On-premises hosts must resolve Cloud private zones: give them an address to query.", "focus"),
    ("Peering zone", "VPC → VPC", "Resolve a domain using another VPC's DNS configuration."),
], note="Direction decides the DNS object.", box=350, h=500, size=30)
row("p4-lb-anatomy", [
    ("Forwarding rule", "IP and port", "the address users hit"),
    ("Target proxy", "HTTP or HTTPS", "holds the certificate"),
    ("URL map", "host and path rules", "which backend service"),
    ("Backend service", "the policy point", "health check, affinity, CDN, Armor", "focus"),
    ("Backends", "the targets", "MIGs, NEGs, buckets"),
], arrows=True, box=280, h=330, size=25)
d = c4.Diagram(1600, 700)
d.node("q", 40, 20, 330, 120, "ask", "Which load balancer?", "", "", size=28)
d.node("a", 40, 240, 420, 140, "container", "UDP, or not HTTP?", "", "removes every Application LB", size=28)
d.node("b", 590, 240, 420, 140, "container", "Must see client source IP?", "", "removes every proxy", size=28)
d.node("c", 1140, 240, 420, 140, "container", "One IP worldwide, failover?", "", "", size=28)
d.node("a2", 40, 500, 420, 150, "system", "Network LB", "proxy or passthrough", "", size=30)
d.node("b2", 590, 500, 420, 150, "focus", "Passthrough Network LB", "external or internal", "", size=30)
d.node("c2", 1140, 500, 420, 150, "focus", "Global external Application LB", "Premium Tier", "", size=30)
for x, y in [("a","a2"),("b","b2"),("c","c2")]: d.edge(x, y, "yes", "", src="b", dst="t", dashed=False, size=25)
d.edge("q", "a", "", "", src="b", dst="t", dashed=False)
d.edge("q", "b", "", "", src="r", dst="t", via=[(800, 80)], dashed=False)
d.edge("q", "c", "", "", src="r", dst="t", via=[(1350, 80)], dashed=False)
d.save(OUT / "p4-lb-pick.svg")
seq("p4-health", [("p","Google probers","system"),("fw","VPC firewall","focus"),("vm","Backend VMs","container"),("lb","Load balancer","ext"),("u","User","person")], [
    ("n","p","p","sources 35.191.0.0/16 and 130.211.0.0/22","a"),
    ("m","p","fw","health check on the serving port"),
    ("f","alt","no firewall rule allows the probe ranges"),
    ("r","fw","p","dropped by the implied deny ingress","hl"),
    ("a","p","lb","every backend marked unhealthy"),
    ("m","u","lb","request"),
    ("r","lb","u","errors, though the VMs are fine","hl"),
    ("e",),
])

# ── Part 5 ─────────────────────────────────────────────────────────────────────────────────
d = c4.Diagram(1600, 800)
d.node("q0", 30, 10, 500, 110, "ask", "An AI agent to host?", "", "managed sessions, memory", size=27)
d.node("a0", 1020, 10, 550, 110, "focus", "Agent Runtime", "Gemini Enterprise Agent Platform", "", size=29)
d.node("q1", 30, 180, 500, 110, "ask", "A container, or can it be one?", "", "", size=27)
d.node("a1", 1020, 180, 550, 110, "system", "Compute Engine VM + MIG", "no: OS, kernel, licences, Windows", "", size=29)
d.node("q2", 30, 350, 500, 110, "ask", "Request or event driven, stateless?", "", "", size=27)
d.node("a2", 1020, 350, 550, 110, "system", "Cloud Run · jobs · functions", "scale to zero", "", size=29)
d.node("q3", 30, 520, 500, 110, "ask", "Need Kubernetes?", "", "operators, DaemonSets, Helm, mesh", size=27)
d.node("a3", 1020, 520, 550, 110, "system", "GKE Autopilot, or Standard", "Standard for node-level control", "", size=29)
for q, a, l in [("q0","a0","yes"),("q1","a1","no"),("q2","a2","yes"),("q3","a3","yes")]:
    d.edge(q, a, l, "", src="r", dst="l", dashed=False, size=27, at=(740, {"q0":40,"q1":210,"q2":380,"q3":550}[q]), width=80)
for a, b, l in [("q0","q1","no"),("q1","q2","yes"),("q2","q3","no")]:
    d.edge(a, b, l, "", src="b", dst="t", dashed=False, size=24)
d.note(30, 680, 1540, "Read top to bottom and take the first exit that fits. Heavy parallel maths: add GPUs or TPUs to the platform you chose.", size=28, colour=AMBER, bg=AMBER_BG)
d.save(OUT / "p5-compute-tree.svg")
row("p5-disk-survive", [
    ("Local SSD", "ephemeral", "Highest speed. Lost when the VM stops or is deleted", "ext"),
    ("Zonal PD / Hyperdisk", "one zone", "Attaches only to VMs in its zone"),
    ("Regional PD / Balanced HA", "synchronous, two zones", "Survives a zone failure, force-attach to a standby", "focus"),
    ("Snapshot", "backup", "Point-in-time, restore anywhere; recent writes can be lost"),
], note="Regional disks are high availability. Snapshots are backup. Local SSD plus a durability requirement is always wrong.", tone="r", box=340, h=520)
seq("p5-iap", [("u","Engineer","person"),("iap","Identity-Aware Proxy","system"),("fw","VPC firewall","container"),("vm","Private VM (no external IP)","focus")], [
    ("m","u","iap","gcloud compute ssh vm --tunnel-through-iap"),
    ("n","iap","fw","checks the role iap.tunnelResourceAccessor","a"),
    ("m","iap","fw","connects from 35.235.240.0/20 to port 22","hl"),
    ("m","fw","vm","allowed by your firewall rule"),
    ("n","vm","vm","OS Login checks compute.osLogin for the user","g"),
    ("r","vm","u","a shell, with no bastion and no public IP"),
])
row("p5-artefacts", [
    ("Snapshot", "one disk's data", "Back up or clone that disk, anywhere"),
    ("Custom image", "one bootable disk", "Boot new VMs from a golden state; a template references it"),
    ("Machine image", "the whole VM", "All disks plus configuration: type, metadata, tags, service account", "focus"),
    ("Instance template", "a recipe, no data", "Tells a MIG what to create"),
], box=340, h=400)
row("p5-mig-features", [
    ("Autohealing", "application broken", "Health check on the MIG recreates the VM"),
    ("Autoscaling", "wrong capacity", "Changes the count of VMs"),
    ("Rolling updates", "new template", "Rolls out with no outage; canary first"),
    ("Regional MIG", "zone failure", "Spreads VMs across zones", "focus"),
], note="A load balancer's health check only stops sending traffic. The MIG's autohealing check recreates the VM. Set an initial delay.", tone="r", box=300, h=510)
seq("p5-rolling", [("op","You","person"),("mig","Regional MIG","focus"),("a","Old VMs (v1)","container"),("b","New VMs (v2)","system"),("lb","Load balancer","ext")], [
    ("m","op","mig","canary: 20% on v2"),
    ("m","mig","b","create 20% from template v2"),
    ("a","b","lb","health check passes: receives traffic"),
    ("n","op","mig","watch errors; healthy? continue","a"),
    ("m","op","mig","full: surge 3, unavailable 0","hl"),
    ("m","mig","b","surge new VMs first"),
    ("m","mig","a","delete old VMs as new ones pass"),
    ("n","op","mig","rollback: another start-update to v1","g"),
])
row("p5-gpu-tpu", [
    ("GPU", "NVIDIA, general parallel", "Any CUDA: PyTorch, TensorFlow, custom kernels. Inference, rendering, video, smaller jobs."),
    ("TPU", "Google ASIC, tensors", "JAX, PyTorch/XLA, TensorFlow via XLA. Large-scale training and serving, cost at scale.", "focus"),
], note="No framework constraint and a general workload: GPU is the safer answer. TPUs never render graphics.", box=330, h=500)

# ── Part 6 ─────────────────────────────────────────────────────────────────────────────────
row("p6-gcloud-kubectl", [
    ("gcloud container", "manages the cluster", "create, resize, upgrade, delete, node pools"),
    ("get-credentials", "the bridge", "writes a kubeconfig entry; auth by gke-gcloud-auth-plugin", "focus"),
    ("kubectl", "manages what runs in it", "Deployments, Services, Pods"),
], arrows=True, box=300, h=350)
row("p6-expose", [
    ("ClusterIP", "default", "A stable internal IP, inside the cluster. No LB"),
    ("NodePort", "", "A port on every node's IP. No LB"),
    ("LoadBalancer", "one IP, one Service", "Layer 4: a passthrough Network LB"),
    ("Ingress", "one IP, many Services", "Host and path rules: an Application LB", "focus"),
    ("Gateway API", "Ingress's successor", "Role separation, weighted traffic splitting", "focus"),
], note="Path or host routing, or one IP for many Services, means Ingress or Gateway.", box=330, h=500, size=25)
row("p6-scaling", [
    ("HPA", "Pods, horizontally", "Replica count, on CPU, memory, custom or external metrics"),
    ("VPA", "Pods, vertically", "Each Pod's requests: recommend, or apply by recreating Pods"),
    ("Cluster autoscaler", "nodes, Standard", "Node count to fit pending Pods; auto-provisioning creates pools"),
    ("Autopilot", "nodes, automatic", "Whatever the Pods request", "focus"),
], note="HPA and VPA must not both act on the same CPU or memory metric for one workload: they fight.", tone="r", box=340, h=520)
seq("p6-image-pull", [("k","kubelet on a node","container"),("sa","Node service account","focus"),("ar","Artifact Registry","system"),("p","Pod","component")], [
    ("m","k","sa","pull image as the node pool's account"),
    ("m","sa","ar","GET the image from pkg.dev"),
    ("f","alt","no artifactregistry.reader for that account"),
    ("r","ar","k","403: Pod stuck in ImagePullBackOff","hl"),
    ("e",),
    ("f","alt","reader granted on the repository"),
    ("r","ar","k","image layers"),
    ("m","k","p","start container"),
    ("e",),
])
seq("p6-wi", [("pod","Pod (KSA web)","container"),("md","GKE metadata server","system"),("sts","Google STS","system"),("gsa","Google SA (option b)","focus"),("api","Cloud Storage","ext")], [
    ("m","pod","md","ADC asks for a token"),
    ("m","md","sts","exchange the KSA's token"),
    ("r","sts","pod","federated token"),
    ("f","alt","(a) IAM granted to the KSA directly"),
    ("m","pod","api","call as principal://.../sa/web","hl"),
    ("e",),
    ("f","alt","(b) KSA annotated, workloadIdentityUser on GSA"),
    ("m","pod","gsa","impersonate"),
    ("m","gsa","api","call as the Google service account"),
    ("e",),
])
seq("p6-canary", [("op","You","person"),("run","Cloud Run service","focus"),("r1","Revision v1","container"),("r2","Revision v2","system"),("u","Users","ext")], [
    ("m","op","run","deploy --no-traffic --tag=canary","hl"),
    ("m","run","r2","create revision: 0%, own tag URL"),
    ("n","op","r2","test on the revision's own tag URL","a"),
    ("m","op","run","update-traffic --to-tags=canary=10","hl"),
    ("a","u","r1","90% of requests"),
    ("a","u","r2","10% of requests"),
    ("m","op","run","promote: --to-latest"),
    ("n","op","run","roll back: --to-revisions=api-00041-xyz=100","g"),
])
row("p6-gcs-event", [
    ("Bucket upload", "object finalized", "Cloud Storage service agent needs pubsub.publisher"),
    ("Eventarc trigger", "must be in the bucket's region", "Filters by event type and bucket", "focus"),
    ("Pub/Sub", "under the hood", "At-least-once: make handlers idempotent"),
    ("Function", "as a Cloud Run service", "Trigger account needs eventReceiver and run.invoker"),
], arrows=True, note="It never fires? Check in order: region, service agent's publisher role, trigger's invoker role, event type.", tone="r", box=340, h=520)
row("p6-autopilot-standard", [
    ("Autopilot", "Google owns the nodes", "You pay for Pod requests. Always regional. Best-practice defaults on and enforced.", "focus"),
    ("Standard", "you own the node pools", "You pay for nodes, full or not. Zonal or regional. Node access and privileged Pods allowed."),
], note="\"Do not want to manage nodes\" is Autopilot, not Standard with node auto-provisioning and autoscaling.", tone="r", box=330, h=510)

# ── Part 7 ─────────────────────────────────────────────────────────────────────────────────
row("p7-file-family", [
    ("Filestore", "managed NFS", "Shared file system, lift-and-shift, ReadWriteMany in GKE. Tiers to regional."),
    ("NetApp Volumes", "NFS and SMB", "Windows shares, NetApp ONTAP, volume replication, Active Directory."),
    ("Managed Lustre", "parallel file system", "AI training data, HPC scratch, checkpoints from thousands of GPUs.", "focus"),
], note="None of them is object storage, and none is the answer to \"cheap archive\".", box=340, h=510)
row("p7-classes", [
    ("Standard", "0 days", "Hot. Highest storage price, no retrieval fee."),
    ("Nearline", "30 days", "About once a month."),
    ("Coldline", "90 days", "About once a quarter."),
    ("Archive", "365 days", "Once a year or less. Lowest storage price, highest retrieval.", "focus"),
], note="All four have the same millisecond latency to the first byte. No thaw, no restore step, no waiting.", tone="r", box=320, h=500, size=30)
row("p7-protect", [
    ("Versioning", "accidents", "Keeps noncurrent versions on overwrite or delete."),
    ("Soft delete", "accidents", "Deleted objects restorable: 7 days default, up to 90."),
    ("Retention policy", "time-based", "No delete or overwrite until the age is reached."),
    ("Bucket Lock", "intent", "Locks retention permanently: nobody, including Owner, can shorten it.", "focus"),
], note="Versioning and soft delete protect against accidents. A locked retention policy protects against intent.", box=340, h=510)
d = c4.Diagram(1600, 800)
d.node("q", 30, 20, 470, 110, "ask", "What does the data need?", "", "", size=28)
L = [("a","Transactions, one primary","Cloud SQL","managed MySQL, Postgres, SQL Server"),
     ("b","Postgres, faster, analytics too","AlloyDB","read pools, columnar engine"),
     ("c","Global relational, scale writes","Spanner","strong consistency, 99.999%"),
     ("d","Time series, huge key lookups","Bigtable","row-key design is everything"),
     ("e","Documents, mobile real-time","Firestore","listeners, offline SDKs"),
     ("f","Analytics over terabytes","BigQuery","serverless warehouse"),
     ("g","Cache, session, leaderboard","Memorystore","never the system of record")]
y = 150
for k, a, b, c in L:
    d.node("l"+k, 30, y, 620, 78, "container", a, "", "", size=24)
    d.node("r"+k, 760, y, 810, 78, "focus" if k == "c" else "system", b, "", c, size=24)
    d.edge("l"+k, "r"+k, "", "", src="r", dst="l", dashed=False); y += 90
d.save(OUT / "p7-db-pick.svg")
row("p7-ha-replica-backup", [
    ("HA standby", "survive a zone", "Synchronous, automatic failover. Serves no reads."),
    ("Read replica", "scale reads, DR", "Asynchronous. Replicates a bad DELETE within seconds."),
    ("PITR", "undo a bad statement", "Clones to a new instance at a timestamp. Needs logs enabled beforehand.", "focus"),
], note="High availability is not read capacity, and a replica is not a backup.", tone="r", box=340, h=510)
seq("p7-pitr", [("dev","Engineer","person"),("db","Cloud SQL orders","focus"),("rep","Read replica","container"),("cl","orders-restored (new)","system")], [
    ("m","dev","db","14:05 a bad DELETE runs"),
    ("a","db","rep","replicated within seconds: the replica is damaged too","hl"),
    ("m","dev","db","instances clone --point-in-time=14:04:00"),
    ("m","db","cl","build a new instance as of 14:04"),
    ("n","db","db","the damaged original stays, for comparison","a"),
    ("r","cl","dev","verify, then repoint the app"),
])
d = c4.Diagram(1600, 700)
d.node("q", 40, 20, 620, 130, "ask", "Volume ÷ usable bandwidth = days", "", "1 Gbps ≈ 10 TB a day · 100 Mbps ≈ 1 TB a day", size=28)
d.node("no", 900, 20, 660, 130, "focus", "Transfer Appliance", "not acceptable", "ship a device, load on site, send it back", size=28)
d.edge("q", "no", "too long", "", src="r", dst="l", at=(780, 45), width=160, size=26, dashed=False)
items = [("s1","Other cloud, URLs, another bucket","Storage Transfer Service"),("s2","On-premises file systems","STS with agent pools"),("s3","Small, one-off, scripted","gcloud storage cp, rsync"),("s4","Into BigQuery, recurring","BigQuery Data Transfer Service")]
for i, (k, a, b) in enumerate(items):
    d.node(k, 40 + i * 390, 300, 360, 200, "system", b, "", a, size=27)
d.edge("q", "s1", "acceptable: where is the data?", "", src="b", dst="t", at=(250, 200), width=380, size=26, dashed=False)
d.note(40, 550, 1520, "500 TB over 100 Mbps is about 500 days, so the sum eliminates every network tool before you read the options.", size=28, colour=RED, bg=RED_BG)
d.save(OUT / "p7-transfer.svg")
d = c4.Diagram(1600, 700)
d.node("t", 40, 240, 330, 150, "queue", "Topic: orders", "", "", size=30)
d.node("s1", 560, 20, 360, 110, "container", "Subscription billing", "", "", size=26)
d.node("s2", 560, 170, 360, 110, "container", "Subscription shipping", "", "", size=26)
d.node("s3", 560, 340, 360, 180, "focus", "Subscription analytics", "one subscription, 3 workers", "", size=26)
d.node("c1", 1160, 20, 400, 110, "system", "Billing service: every message", "", "", size=25)
d.node("c2", 1160, 170, 400, 110, "system", "Shipping service: every message", "", "", size=25)
d.node("c3", 1160, 340, 400, 180, "component", "Workers 1, 2, 3", "compete: each gets a share", "", size=25)
for s in ("s1","s2","s3"): d.edge("t", s, "", "", src="r", dst="l", dashed=False)
for a, b in (("s1","c1"),("s2","c2"),("s3","c3")): d.edge(a, b, "", "", src="r", dst="l", dashed=False)
d.note(40, 560, 1520, "Each subscription gets every message. Subscribers sharing one subscription split the messages. Fan-out needs one subscription per consumer.", size=27, colour=AMBER, bg=AMBER_BG)
d.save(OUT / "p7-fanout.svg")
row("p7-kms", [
    ("Key ring", "permanent location", "A region, a multi-region such as eu, or global"),
    ("Key", "purpose and rotation", "Protection: SOFTWARE, HSM, EXTERNAL, EXTERNAL_VPC"),
    ("Key version", "the key material", "Enabled, disabled, scheduled for destruction, destroyed", "focus"),
], arrows=True, box=320, h=380)
seq("p7-cmek", [("you","You","person"),("res","Bucket or Cloud SQL","container"),("ag","Product's service agent","focus"),("kms","Cloud KMS key","system")], [
    ("n","you","ag","first: grant cryptoKeyEncrypterDecrypter on the key to the agent","a"),
    ("m","you","res","create with the key: locations must match"),
    ("m","res","ag","write data"),
    ("m","ag","kms","encrypt the data key","hl"),
    ("r","kms","ag","wrapped key, if the role and location are right"),
    ("f","alt","you disable the key version"),
    ("r","kms","res","decrypt fails: data unreadable, reversibly","hl"),
    ("e",),
])

# ── Part 8 ─────────────────────────────────────────────────────────────────────────────────
row("p8-terraform-loop", [
    ("Code in git", "desired end state", "Reviewed by pull request"),
    ("terraform plan", "the diff", "Attach it to the review. Shows drift."),
    ("terraform apply", "from a pipeline", "As a deploy account, by impersonation or federation", "focus"),
    ("State in GCS", "backend with locking", "Versioned, restricted, never in git"),
], arrows=True, note="Two engineers with local state means two truths. Store state remotely, with locking.", tone="r", box=320, h=510)
row("p8-ai-tools", [
    ("Gemini Cloud Assist", "the console", "Ask about your resources; generate gcloud and Terraform; investigations; draft alerts."),
    ("Gemini CLI / Antigravity CLI", "your terminal", "An agent that reads code, runs commands with approval, writes IaC."),
    ("Google Antigravity", "desktop platform", "Agent-first IDE: multi-step tasks across editor, terminal, browser."),
    ("Application Design Center", "the console", "Approved Terraform-backed templates, a visual canvas, App Hub.", "focus"),
], note="Generated commands and IaC are drafts. The assistant acts with your permissions. Review before applying.", tone="r", box=390, h=590, size=27)
row("p8-tf-vs-kcc", [
    ("Terraform", "when you run it", "Declarative. Reconciles at apply. Drift appears on the next plan."),
    ("Config Connector", "continuously", "Kubernetes custom resources, in a cluster. A console change is reverted.", "focus"),
    ("Helm", "applications", "Charts, values, releases with rollback. Does not create the cluster."),
], box=340, h=400)
row("p8-workstations", [
    ("Workstation cluster", "region + VPC subnet", "Where workstations run: private networking"),
    ("Workstation configuration", "the template", "Machine type, image, persistent disk, timeouts, who may use it", "focus"),
    ("Workstation", "one developer", "An instance of that configuration"),
], arrows=True, note="Only /home persists. Anything else is recreated from the image on every start.", tone="r", box=330, h=510)

# ── Part 9 ─────────────────────────────────────────────────────────────────────────────────
row("p9-hypervisor", [
    ("compute.googleapis.com", "the hypervisor", "CPU, disk and network I/O. No agent needed."),
    ("agent.googleapis.com", "the Ops Agent", "Memory, swap, disk space used, processes.", "focus"),
    ("workload.googleapis.com", "apps via the agent", "OpenTelemetry and third-party receivers."),
    ("custom, logging, prometheus", "yours", "Custom metrics, log-based metrics, Managed Prometheus."),
], note="The hypervisor cannot see inside the guest. Memory appears only after the Ops Agent is installed.", tone="r", box=320, h=510, size=25)
row("p9-alert-only", [
    ("Dashboard", "measures", ""),
    ("Uptime check", "measures", ""),
    ("Log-based metric", "measures", ""),
    ("SLO", "measures", ""),
    ("Alerting policy", "decides and sends", "", "focus"),
], arrows=False, note="Only an alerting policy notifies anyone.", tone="r", box=190, h=350, size=27)
d = c4.Diagram(1600, 790)
d.node("e", 30, 300, 250, 130, "container", "Log entries", "", "", size=28)
d.node("r", 370, 270, 290, 190, "focus", "Log Router", "sinks", "inclusion and exclusion filters", size=30)
dest = [("d1","_Required bucket","400 days, fixed, free"),("d2","_Default bucket","30 days by default"),("d3","Custom bucket","1 day to 10 years, CMEK"),("d4","BigQuery dataset","query, join"),("d5","Cloud Storage","cheap, long-term archive"),("d6","Pub/Sub topic","SIEM, Splunk, on-premises"),("d7","Another project","central logging")]
y = 8
for k, a, b in dest:
    d.node(k, 860, y, 710, 94, "system" if k not in ("d1",) else "ext", a, "", b, size=26); d.edge("r", k, "", "", src="r", dst="l", dashed=False); y += 110
d.edge("e", "r", "", "", src="r", dst="l", dashed=False)
d.save(OUT / "p9-router.svg")
seq("p9-sink", [("p","Projects under the org","container"),("s","Aggregated sink","focus"),("w","Sink's writer identity","system"),("b","Destination bucket","ext")], [
    ("m","p","s","logs, with --include-children"),
    ("m","s","w","write as the writer identity"),
    ("f","alt","no grant at the destination"),
    ("r","b","w","denied: the sink silently does nothing","hl"),
    ("e",),
    ("f","alt","grant logging.bucketWriter at the destination"),
    ("m","w","b","entries land in the central bucket"),
    ("e",),
])
row("p9-audit", [
    ("Admin Activity", "changes", "Always on, cannot be disabled, free, _Required"),
    ("Data Access", "reads", "Off by default, except BigQuery. Charged. _Default", "focus"),
    ("System Event", "Google's changes", "Always on, free, _Required"),
    ("Policy Denied", "denied by policy", "On. Charged, can exclude. _Default"),
], note="Who read these objects? Data Access exists only if it was enabled before the reads.", tone="r", box=320, h=500, size=28)
row("p9-diagnose", [
    ("Cloud Trace", "which service", "Spans across services, for one request"),
    ("Cloud Profiler", "why, inside the code", "Continuous CPU, heap, contention profiles"),
    ("Error Reporting", "new exceptions", "Groups stack traces, counts, notifies"),
    ("Query Insights", "which SQL", "Plus index advisor, on Cloud SQL and AlloyDB", "focus"),
], note="A service can be slow while idle, waiting on a dependency. CPU utilisation tells you neither.", box=310, h=500, size=28)
row("p9-health", [
    ("Public dashboard", "everyone's incidents", "Broad status page; nobody is paged by it", "ext"),
    ("Personalized Service Health", "incidents affecting you", "Per project and org-wide. API, logs, alert with a policy.", "focus"),
    ("Cloud Hub", "per application", "App Hub apps: health, events, deployments, cost, support cases."),
], box=340, h=400)
