"""The exam blueprint: Google's Associate Cloud Engineer guide, live from 30 June 2026.

This module is the single place the simulator learns what the exam covers. It
holds three layers, each derived from the guide's own structure:

``SECTIONS``    the four weighted sections (20 / 30 / 30 / 20)
``OBJECTIVES``  the twelve numbered objectives (1.1 … 4.2)
``BULLETS``     every "considerations include" bullet, numbered in guide order
                (``2.3.3`` is the third bullet of objective 2.3), flagged when
                the June 2026 guide introduced it

and one layer of our own:

``SUBTOPICS``   the closed vocabulary a question's ``subtopic`` must come from.
                Each subtopic belongs to exactly one objective and names the
                guide bullets it teaches, which is how ``kb.py blueprint``
                reports coverage bullet by bullet. Anything outside the guide
                has no subtopic, so it cannot enter the bank.

The guide gives no weights below section level. The sampler therefore splits
each section's share across its objectives in proportion to their bullet
counts — breadth is the only published signal of emphasis.

Source: the June 2026 edition of Google's official guide, at ``GUIDE_URL`` below.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

GUIDE_DATE = "2026-06-30"
GUIDE_URL = "https://services.google.com/fh/files/misc/associate_cloud_engineer_exam_guide_english.pdf"


@dataclass(frozen=True)
class Section:
    number: int
    title: str
    weight: float
    short: str
    slug: str

    @property
    def label(self) -> str:
        """The full label stored on every question, e.g. ``Section 2: Planning …``."""
        return f"Section {self.number}: {self.title}"


@dataclass(frozen=True)
class Objective:
    id: str            # "2.3"
    title: str

    @property
    def section(self) -> int:
        return int(self.id.split(".")[0])


@dataclass(frozen=True)
class Bullet:
    id: str            # "2.3.3"
    text: str
    new: bool = False  # introduced (or materially widened) by the June 2026 guide

    @property
    def objective(self) -> str:
        return self.id.rsplit(".", 1)[0]


@dataclass(frozen=True)
class Subtopic:
    name: str
    objective: str
    bullets: Tuple[str, ...] = field(default_factory=tuple)


# --------------------------------------------------------------------------
# Sections
# --------------------------------------------------------------------------

SECTION_LIST: List[Section] = [
    Section(1, "Setting up a cloud solution environment", 0.20, "S1 · Setup", "setup"),
    Section(2, "Planning and implementing a cloud solution", 0.30, "S2 · Plan & build", "planning"),
    Section(3, "Ensuring the successful operation of a cloud solution", 0.30, "S3 · Operate", "operations"),
    Section(4, "Configuring access and security", 0.20, "S4 · Access", "security"),
]
SECTIONS: Dict[int, Section] = {s.number: s for s in SECTION_LIST}

# --------------------------------------------------------------------------
# Objectives
# --------------------------------------------------------------------------

OBJECTIVE_LIST: List[Objective] = [
    Objective("1.1", "Setting up cloud projects and accounts"),
    Objective("1.2", "Managing billing configuration"),
    Objective("2.1", "Planning and implementing compute resources"),
    Objective("2.2", "Planning and implementing storage and data solutions"),
    Objective("2.3", "Planning and implementing networking resources"),
    Objective("2.4", "Planning and implementing resources using tooling"),
    Objective("3.1", "Managing compute resources"),
    Objective("3.2", "Managing storage and data solutions"),
    Objective("3.3", "Managing networking resources"),
    Objective("3.4", "Monitoring and logging"),
    Objective("4.1", "Managing IAM"),
    Objective("4.2", "Managing service accounts"),
]
OBJECTIVES: Dict[str, Objective] = {o.id: o for o in OBJECTIVE_LIST}

# --------------------------------------------------------------------------
# Bullets — the guide's "considerations include", in guide order
# --------------------------------------------------------------------------

_B = Bullet
BULLET_LIST: List[Bullet] = [
    # 1.1
    _B("1.1.1", "Creating a resource hierarchy"),
    _B("1.1.2", "Applying organizational policies to the resource hierarchy"),
    _B("1.1.3", "Granting members IAM roles within a project"),
    _B("1.1.4", "Managing users and groups in Cloud Identity (manually and automated)"),
    _B("1.1.5", "Enabling APIs within projects"),
    _B("1.1.6", "Provisioning and setting up products in Google Cloud Observability"),
    _B("1.1.7", "Assessing quotas and requesting increases"),
    _B("1.1.8", "Setting up standalone organizations", new=True),
    _B("1.1.9", "Setting up cloud networking"),
    _B("1.1.10", "Verifying product availability across geographical locations"),
    _B("1.1.11", "Configuring Cloud Asset Inventory and using Gemini Cloud Assist to analyze resources", new=True),
    _B("1.1.12", "Configuring Workforce Identity Federation", new=True),
    # 1.2
    _B("1.2.1", "Creating one or more billing accounts"),
    _B("1.2.2", "Linking projects to a billing account"),
    _B("1.2.3", "Establishing billing budgets and alerts"),
    _B("1.2.4", "Setting up billing exports"),
    # 2.1
    _B("2.1.1", "Selecting compute (Compute Engine, GKE, Cloud Run, Cloud Run functions, Agent Runtime)", new=True),
    _B("2.1.2", "Launching a compute instance (availability policy, SSH keys)"),
    _B("2.1.3", "Choosing storage for Compute Engine (zonal PD, regional PD, Hyperdisk)"),
    _B("2.1.4", "Creating an autoscaled managed instance group from an instance template"),
    _B("2.1.5", "Configuring OS Login"),
    _B("2.1.6", "Configuring VM Manager"),
    _B("2.1.7", "Using Spot VM instances and custom machine types"),
    _B("2.1.8", "Installing and configuring kubectl"),
    _B("2.1.9", "Deploying GKE clusters (Autopilot, regional, private)"),
    _B("2.1.10", "Deploying a containerized application to GKE"),
    _B("2.1.11", "Deploying to serverless platforms, including Pub/Sub, Cloud Storage and Eventarc events"),
    _B("2.1.12", "Identifying whether to use GPUs or TPUs", new=True),
    # 2.2
    _B("2.2.1", "Choosing and deploying data products (Cloud SQL, BigQuery, Firestore, Spanner, Bigtable, "
                "AlloyDB, Dataflow, Pub/Sub, Managed Kafka, Memorystore)", new=True),
    _B("2.2.2", "Choosing and deploying storage products (Cloud Storage, Filestore, NetApp Volumes, "
                "Managed Lustre) and storage classes", new=True),
    _B("2.2.3", "Loading data (command line, from Cloud Storage, Storage Transfer Service)"),
    _B("2.2.4", "Maintaining multi-region redundancy across data solutions", new=True),
    # 2.3
    _B("2.3.1", "Creating a VPC with subnets (custom mode, Shared VPC, VPC Network Peering)"),
    _B("2.3.2", "VPC firewall rules and Cloud NGFW policies (action, source, destination, targets, "
                "protocols, ports)", new=True),
    _B("2.3.3", "Using Tags (secure Tags) and service accounts in Cloud NGFW policy rules", new=True),
    _B("2.3.4", "Establishing network connectivity (Cloud VPN, VPC Network Peering, Cloud Interconnect)"),
    _B("2.3.5", "Choosing and deploying load balancers"),
    _B("2.3.6", "Differentiating Network Service Tiers"),
    # 2.4
    _B("2.4.1", "Infrastructure as Code tooling (Fabric FAST, Config Connector, Terraform, Helm)"),
    _B("2.4.2", "AI-assisted planning and implementation (Gemini CLI, Antigravity, Gemini Cloud Assist, "
                "Application Design Center)", new=True),
    # 3.1
    _B("3.1.1", "Remotely connecting to a Compute Engine instance"),
    _B("3.1.2", "Viewing current running Compute Engine instances"),
    _B("3.1.3", "Working with snapshots and images (create, view, delete, schedule)"),
    _B("3.1.4", "Viewing current running GKE cluster inventory (nodes, Pods, Services)"),
    _B("3.1.5", "Configuring GKE to access Artifact Registry"),
    _B("3.1.6", "Working with GKE node pools (add, edit, remove, autoscale)"),
    _B("3.1.7", "Working with Kubernetes resources (Pods, Services, StatefulSets)"),
    _B("3.1.8", "Managing horizontal and vertical Pod autoscaling"),
    _B("3.1.9", "Managing GKE Autopilot Pod resource requests", new=True),
    _B("3.1.10", "Deploying new versions of a Cloud Run application"),
    _B("3.1.11", "Adjusting traffic splitting (Cloud Run, Cloud Run functions, GKE)"),
    _B("3.1.12", "Configuring autoscaling for a Cloud Run application"),
    _B("3.1.13", "Attaching GPUs and TPUs", new=True),
    _B("3.1.14", "Deploying an agent to Agent Runtime on Gemini Enterprise Agent Platform", new=True),
    _B("3.1.15", "Managing notebooks in Agent Platform Workbench and BigQuery", new=True),
    _B("3.1.16", "Managing developer environments (Cloud Workstations)", new=True),
    # 3.2
    _B("3.2.1", "Managing and securing objects in Cloud Storage buckets"),
    _B("3.2.2", "Setting object lifecycle management policies"),
    _B("3.2.3", "Executing queries against data instances (Cloud SQL, BigQuery, Bigtable, Spanner, "
                "Firestore, AlloyDB)"),
    _B("3.2.4", "Estimating costs of data storage resources"),
    _B("3.2.5", "Backing up and restoring database instances"),
    _B("3.2.6", "Reviewing job status (Dataflow, BigQuery)"),
    _B("3.2.7", "Using Database Center to manage the database fleet", new=True),
    _B("3.2.8", "Configuring customer-managed encryption keys (CMEK)", new=True),
    # 3.3
    _B("3.3.1", "Resizing a subnet's IPv4 address range"),
    _B("3.3.2", "Reserving static external or internal IP addresses"),
    _B("3.3.3", "Adding custom static routes in a VPC", new=True),
    _B("3.3.4", "Using Cloud DNS and Cloud NAT"),
    _B("3.3.5", "Managing VPC firewall rules and Cloud NGFW policies", new=True),
    # 3.4
    _B("3.4.1", "Creating Cloud Monitoring alerts based on resource metrics"),
    _B("3.4.2", "Creating and ingesting custom metrics (from applications or logs)"),
    _B("3.4.3", "Configuring audit logs (VPC Flow Logs, audit logs, firewall logs)"),
    _B("3.4.4", "Exporting logs to external systems (on-premises, BigQuery)"),
    _B("3.4.5", "Configuring log buckets, log analytics and log routers"),
    _B("3.4.6", "Viewing and filtering logs in Cloud Logging"),
    _B("3.4.7", "Viewing specific log message details in Cloud Logging"),
    _B("3.4.8", "Using diagnostic tools (Cloud Trace, Cloud Profiler, Query Insights, index advisor)"),
    _B("3.4.9", "Viewing the Personalized Service Health dashboard", new=True),
    _B("3.4.10", "Configuring and deploying Ops Agent"),
    _B("3.4.11", "Deploying Google Cloud Managed Service for Prometheus"),
    _B("3.4.12", "Using Gemini Cloud Assist for Cloud Monitoring", new=True),
    _B("3.4.13", "Using Active Assist to optimize resource utilization"),
    _B("3.4.14", "Using Cloud Hub to monitor active events and application health", new=True),
    # 4.1
    _B("4.1.1", "Viewing and creating IAM policies"),
    _B("4.1.2", "Attaching roles and policy inheritance in the Organization hierarchy"),
    _B("4.1.3", "Managing the various role types and defining custom IAM roles"),
    # 4.2
    _B("4.2.1", "Creating service accounts, including Google-managed service accounts"),
    _B("4.2.2", "Using service accounts in IAM policies with minimum permissions"),
    _B("4.2.3", "Assigning service accounts to resources"),
    _B("4.2.4", "Managing IAM permissions of a service account"),
    _B("4.2.5", "Managing service account impersonation"),
    _B("4.2.6", "Creating and managing short-lived service account credentials"),
    _B("4.2.7", "Using a Google Cloud service account with a GKE application"),
    _B("4.2.8", "Provisioning Workload Identity Federation", new=True),
]
BULLETS: Dict[str, Bullet] = {b.id: b for b in BULLET_LIST}

# --------------------------------------------------------------------------
# Subtopics — the closed vocabulary for Question.subtopic
# --------------------------------------------------------------------------

_S = Subtopic
SUBTOPIC_LIST: List[Subtopic] = [
    # 1.1
    _S("Resource Hierarchy", "1.1", ("1.1.1",)),
    _S("Organization Policy", "1.1", ("1.1.2",)),
    _S("Project IAM Grants", "1.1", ("1.1.3",)),
    _S("Cloud Identity and Users", "1.1", ("1.1.4",)),
    _S("APIs and Quotas", "1.1", ("1.1.5", "1.1.7")),
    _S("Observability Setup", "1.1", ("1.1.6",)),
    _S("Standalone Organizations", "1.1", ("1.1.8",)),
    _S("Foundation Networking", "1.1", ("1.1.9",)),
    _S("Regions and Zones", "1.1", ("1.1.10",)),
    _S("Asset Inventory and Gemini Cloud Assist", "1.1", ("1.1.11",)),
    _S("Workforce Identity Federation", "1.1", ("1.1.12",)),
    _S("gcloud CLI and Configurations", "1.1", ()),
    # 1.2
    _S("Billing Accounts", "1.2", ("1.2.1", "1.2.2")),
    _S("Budgets and Alerts", "1.2", ("1.2.3",)),
    _S("Billing Export and Cost Attribution", "1.2", ("1.2.4",)),
    # 2.1
    _S("Compute Platform Selection", "2.1", ("2.1.1",)),
    _S("Launching Instances", "2.1", ("2.1.2",)),
    _S("Storage for Compute Engine", "2.1", ("2.1.3",)),
    _S("Managed Instance Groups", "2.1", ("2.1.4",)),
    _S("OS Login", "2.1", ("2.1.5",)),
    _S("VM Manager", "2.1", ("2.1.6",)),
    _S("Spot and Custom Machine Types", "2.1", ("2.1.7",)),
    _S("kubectl Setup", "2.1", ("2.1.8",)),
    _S("GKE Cluster Configurations", "2.1", ("2.1.9",)),
    _S("Deploying to GKE", "2.1", ("2.1.10",)),
    _S("Serverless Deployment and Events", "2.1", ("2.1.11",)),
    _S("GPUs or TPUs", "2.1", ("2.1.12",)),
    # 2.2
    _S("Database Selection", "2.2", ("2.2.1",)),
    _S("Data Pipelines and Messaging", "2.2", ("2.2.1",)),
    _S("Storage Products", "2.2", ("2.2.2",)),
    _S("Cloud Storage Classes", "2.2", ("2.2.2",)),
    _S("Loading Data", "2.2", ("2.2.3",)),
    _S("Multi-region Redundancy", "2.2", ("2.2.4",)),
    # 2.3
    _S("VPC Design", "2.3", ("2.3.1",)),
    _S("Firewall Rules and Policies", "2.3", ("2.3.2",)),
    _S("Secure Tags and Service Accounts in Rules", "2.3", ("2.3.3",)),
    _S("Hybrid Connectivity", "2.3", ("2.3.4",)),
    _S("Load Balancer Selection", "2.3", ("2.3.5",)),
    _S("Network Service Tiers", "2.3", ("2.3.6",)),
    # 2.4
    _S("Infrastructure as Code", "2.4", ("2.4.1",)),
    _S("AI-assisted Planning", "2.4", ("2.4.2",)),
    # 3.1
    _S("Connecting to Instances", "3.1", ("3.1.1",)),
    _S("Instance Inventory and Lifecycle", "3.1", ("3.1.2",)),
    _S("Snapshots and Images", "3.1", ("3.1.3",)),
    _S("GKE Inventory", "3.1", ("3.1.4",)),
    _S("Artifact Registry Access", "3.1", ("3.1.5",)),
    _S("GKE Node Pools", "3.1", ("3.1.6",)),
    _S("Kubernetes Resources", "3.1", ("3.1.7",)),
    _S("Pod Autoscaling", "3.1", ("3.1.8",)),
    _S("Autopilot Resource Requests", "3.1", ("3.1.9",)),
    _S("Cloud Run Releases", "3.1", ("3.1.10",)),
    _S("Traffic Splitting", "3.1", ("3.1.11",)),
    _S("Cloud Run Autoscaling", "3.1", ("3.1.12",)),
    _S("Attaching Accelerators", "3.1", ("3.1.13",)),
    _S("Agent Runtime", "3.1", ("3.1.14",)),
    _S("Notebooks", "3.1", ("3.1.15",)),
    _S("Developer Environments", "3.1", ("3.1.16",)),
    # 3.2
    _S("Securing Cloud Storage Objects", "3.2", ("3.2.1",)),
    _S("Object Lifecycle", "3.2", ("3.2.2",)),
    _S("Querying Data", "3.2", ("3.2.3",)),
    _S("Storage Cost Estimation", "3.2", ("3.2.4",)),
    _S("Backup and Restore", "3.2", ("3.2.5",)),
    _S("Job Status", "3.2", ("3.2.6",)),
    _S("Database Center", "3.2", ("3.2.7",)),
    _S("CMEK and Key Management", "3.2", ("3.2.8",)),
    # 3.3
    _S("Subnets, Addresses and Routes", "3.3", ("3.3.1", "3.3.2", "3.3.3")),
    _S("Cloud DNS and Cloud NAT", "3.3", ("3.3.4",)),
    _S("Firewall Operations", "3.3", ("3.3.5",)),
    # 3.4
    _S("Resource Alerts", "3.4", ("3.4.1",)),
    _S("Custom Metrics", "3.4", ("3.4.2",)),
    _S("Audit, Flow and Firewall Logs", "3.4", ("3.4.3",)),
    _S("Log Export", "3.4", ("3.4.4",)),
    _S("Log Buckets and Routing", "3.4", ("3.4.5",)),
    _S("Viewing and Filtering Logs", "3.4", ("3.4.6", "3.4.7")),
    _S("Diagnostic Tools", "3.4", ("3.4.8",)),
    _S("Service Health and Cloud Hub", "3.4", ("3.4.9", "3.4.14")),
    _S("Ops Agent", "3.4", ("3.4.10",)),
    _S("Managed Prometheus", "3.4", ("3.4.11",)),
    _S("Gemini and Active Assist", "3.4", ("3.4.12", "3.4.13")),
    # 4.1
    _S("IAM Policies and Inheritance", "4.1", ("4.1.1", "4.1.2")),
    _S("Role Types and Custom Roles", "4.1", ("4.1.3",)),
    # 4.2
    _S("Creating Service Accounts", "4.2", ("4.2.1",)),
    _S("Service Accounts and Least Privilege", "4.2", ("4.2.2", "4.2.3")),
    _S("Service Account Permissions and Impersonation", "4.2", ("4.2.4", "4.2.5")),
    _S("Short-lived Credentials", "4.2", ("4.2.6",)),
    _S("Service Accounts for GKE", "4.2", ("4.2.7",)),
    _S("Workload Identity Federation", "4.2", ("4.2.8",)),
]
SUBTOPICS: Dict[str, Subtopic] = {s.name: s for s in SUBTOPIC_LIST}


# --------------------------------------------------------------------------
# Derived views
# --------------------------------------------------------------------------


def section_of(objective_id: str) -> Section:
    return SECTIONS[OBJECTIVES[objective_id].section]


def objectives_in(section_number: int) -> List[Objective]:
    return [o for o in OBJECTIVE_LIST if o.section == section_number]


def bullets_in(objective_id: str) -> List[Bullet]:
    return [b for b in BULLET_LIST if b.objective == objective_id]


def subtopics_in(objective_id: str) -> List[Subtopic]:
    return [s for s in SUBTOPIC_LIST if s.objective == objective_id]


def objective_weights() -> Dict[str, float]:
    """Each objective's share of the whole exam.

    The section weight is published; the split inside a section is ours: in
    proportion to the number of guide bullets per objective.
    """
    out: Dict[str, float] = {}
    for sec in SECTION_LIST:
        objs = objectives_in(sec.number)
        total = sum(len(bullets_in(o.id)) for o in objs)
        for o in objs:
            out[o.id] = sec.weight * len(bullets_in(o.id)) / total
    return out


def is_new_subtopic(name: str) -> bool:
    """True when any bullet the subtopic teaches is new in the June 2026 guide."""
    sub = SUBTOPICS.get(name)
    return bool(sub) and any(BULLETS[b].new for b in sub.bullets)


def _self_check() -> None:
    assert abs(sum(s.weight for s in SECTION_LIST) - 1.0) < 1e-9
    for b in BULLET_LIST:
        assert b.objective in OBJECTIVES, b.id
    for s in SUBTOPIC_LIST:
        assert s.objective in OBJECTIVES, s.name
        for b in s.bullets:
            assert b in BULLETS and BULLETS[b].objective == s.objective, (s.name, b)
    uncovered = [b.id for b in BULLET_LIST if not any(b.id in s.bullets for s in SUBTOPIC_LIST)]
    assert not uncovered, f"bullets with no subtopic: {uncovered}"


_self_check()
