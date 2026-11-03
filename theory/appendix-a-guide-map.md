---
title: "Appendix A — The exam guide, mapped to this booklet"
parent: Theory
nav_order: 11
---

# Appendix A — The exam guide, mapped to this booklet
{: .no_toc }

1. TOC
{:toc}

Every bullet of the guide that went live on 30 June 2026, in the guide's own order, and where it is taught.
Magenta panels in the body mark the bullets that are new in that guide.

## <a id="sA-1"></a>A.1 Section 1 — Setting up a cloud solution environment (~20%)

| Guide bullet | Taught in |
|:----------------------------------------------------------------|:----------------------------|
| **1.1** Creating a resource hierarchy | [§2.1](02-organization-projects-billing.md#s2-1), [§2.3](02-organization-projects-billing.md#s2-3) |
| Applying organizational policies to the resource hierarchy | [§3.7](03-identity-access.md#s3-7) |
| Granting members IAM roles within a project | [§3.3](03-identity-access.md#s3-3), [§3.5](03-identity-access.md#s3-5) |
| Managing users and groups in Cloud Identity (manually and automated) | [§3.1](03-identity-access.md#s3-1) |
| Enabling APIs within projects | [§2.4](02-organization-projects-billing.md#s2-4) |
| Provisioning and setting up products in Google Cloud Observability | [§9.1](09-operations.md#s9-1), [§9.2](09-operations.md#s9-2) |
| Assessing quotas and requesting increases | [§2.5](02-organization-projects-billing.md#s2-5) |
| Setting up standalone organizations | [§2.2](02-organization-projects-billing.md#s2-2) |
| Setting up cloud networking | [§2.2](02-organization-projects-billing.md#s2-2), [§4.1](04-networking.md#s4-1) |
| Verifying product availability across geographical locations | [§1.4](01-exam-locations-tools.md#s1-4) |
| Configuring Cloud Asset Inventory and using Gemini Cloud Assist to analyse resources | [§2.9](02-organization-projects-billing.md#s2-9) |
| Configuring Workforce Identity Federation | [§3.2](03-identity-access.md#s3-2) |
| **1.2** Creating one or more billing accounts | [§2.6](02-organization-projects-billing.md#s2-6) |
| Linking projects to a billing account | [§2.6](02-organization-projects-billing.md#s2-6) |
| Establishing billing budgets and alerts | [§2.7](02-organization-projects-billing.md#s2-7) |
| Setting up billing exports | [§2.7](02-organization-projects-billing.md#s2-7) |

## <a id="sA-2"></a>A.2 Section 2 — Planning and implementing a cloud solution (~30%)

| Guide bullet | Taught in |
|:----------------------------------------------------------------|:----------------------------|
| **2.1** Selecting compute (Compute Engine, GKE, Cloud Run, Cloud Run functions, Agent Runtime) | [§5.1](05-compute-engine.md#s5-1), [§8.6](08-tooling.md#s8-6) |
| Launching a compute instance (availability policy, SSH keys) | [§5.3](05-compute-engine.md#s5-3), [§5.5](05-compute-engine.md#s5-5) |
| Choosing storage for Compute Engine (zonal PD, regional PD, Hyperdisk) | [§5.4](05-compute-engine.md#s5-4) |
| Creating an autoscaled MIG from an instance template | [§5.8](05-compute-engine.md#s5-8) |
| Configuring OS Login | [§5.5](05-compute-engine.md#s5-5) |
| Configuring VM Manager | [§5.6](05-compute-engine.md#s5-6) |
| Using Spot VMs and custom machine types | [§5.2](05-compute-engine.md#s5-2) |
| Installing and configuring kubectl | [§6.2](06-containers-serverless.md#s6-2) |
| Deploying GKE clusters (Autopilot, regional, private) | [§6.1](06-containers-serverless.md#s6-1) |
| Deploying a containerised application to GKE | [§6.3](06-containers-serverless.md#s6-3), [§6.4](06-containers-serverless.md#s6-4) |
| Serverless deployments, including Pub/Sub, Cloud Storage and Eventarc events | [§6.9](06-containers-serverless.md#s6-9), [§6.11](06-containers-serverless.md#s6-11) |
| Identifying whether to use GPUs or TPUs | [§5.9](05-compute-engine.md#s5-9) |
| **2.2** Choosing and deploying data products (Cloud SQL, BigQuery, Firestore, Spanner, Bigtable, AlloyDB, Dataflow, Pub/Sub, Managed Kafka, Memorystore) | [§7.6](07-storage-data.md#s7-6)–[§7.10](07-storage-data.md#s7-10), [§7.12](07-storage-data.md#s7-12) |
| Choosing and deploying storage products (Cloud Storage, Filestore, NetApp Volumes, Managed Lustre) and classes | [§7.1](07-storage-data.md#s7-1), [§7.2](07-storage-data.md#s7-2) |
| Loading data (command line, from Cloud Storage, Storage Transfer Service) | [§7.11](07-storage-data.md#s7-11) |
| Maintaining multi-region redundancy across data solutions | [§7.13](07-storage-data.md#s7-13) |
| **2.3** Creating a VPC with subnets (custom mode, Shared VPC, peering) | [§4.1](04-networking.md#s4-1), [§4.2](04-networking.md#s4-2), [§4.5](04-networking.md#s4-5) |
| VPC firewall rules and Cloud NGFW policies (action, source, destination, targets, protocols, ports) | [§4.4](04-networking.md#s4-4) |
| Tags (secure tags) and service accounts in Cloud NGFW rules | [§4.4](04-networking.md#s4-4) |
| Network connectivity (Cloud VPN, peering, Cloud Interconnect) | [§4.5](04-networking.md#s4-5), [§4.6](04-networking.md#s4-6) |
| Choosing and deploying load balancers | [§4.9](04-networking.md#s4-9) |
| Differentiating Network Service Tiers | [§4.10](04-networking.md#s4-10) |
| **2.4** IaC tooling (Fabric FAST, Config Connector, Terraform, Helm) | [§8.1](08-tooling.md#s8-1)–[§8.4](08-tooling.md#s8-4) |
| AI-assisted planning (Gemini CLI, Antigravity, Gemini Cloud Assist, Application Design Center) | [§8.5](08-tooling.md#s8-5) |

## <a id="sA-3"></a>A.3 Section 3 — Ensuring the successful operation of a cloud solution (~30%)

| Guide bullet | Taught in |
|:----------------------------------------------------------------|:----------------------------|
| **3.1** Remotely connecting to a Compute Engine instance | [§5.5](05-compute-engine.md#s5-5) |
| Viewing running Compute Engine instances | [§5.6](05-compute-engine.md#s5-6) |
| Snapshots and images (create, view, delete, schedule) | [§5.7](05-compute-engine.md#s5-7) |
| Viewing GKE cluster inventory | [§6.2](06-containers-serverless.md#s6-2) |
| Configuring GKE to access Artifact Registry | [§6.7](06-containers-serverless.md#s6-7) |
| GKE node pools (add, edit, remove, autoscale) | [§6.6](06-containers-serverless.md#s6-6) |
| Kubernetes resources (Pods, Services, StatefulSets) | [§6.3](06-containers-serverless.md#s6-3), [§6.4](06-containers-serverless.md#s6-4) |
| Horizontal and vertical Pod autoscaling | [§6.5](06-containers-serverless.md#s6-5) |
| Autopilot Pod resource requests | [§6.5](06-containers-serverless.md#s6-5) |
| Deploying new Cloud Run versions | [§6.9](06-containers-serverless.md#s6-9), [§6.10](06-containers-serverless.md#s6-10) |
| Traffic splitting (Cloud Run, Cloud Run functions, GKE) | [§6.4](06-containers-serverless.md#s6-4), [§6.10](06-containers-serverless.md#s6-10), [§6.11](06-containers-serverless.md#s6-11) |
| Autoscaling a Cloud Run application | [§6.10](06-containers-serverless.md#s6-10) |
| Attaching GPUs and TPUs | [§5.9](05-compute-engine.md#s5-9), [§6.6](06-containers-serverless.md#s6-6) |
| Deploying an agent to Agent Runtime | [§8.6](08-tooling.md#s8-6) |
| Notebooks in Workbench and BigQuery | [§8.6](08-tooling.md#s8-6) |
| Developer environments (Cloud Workstations) | [§8.6](08-tooling.md#s8-6) |
| **3.2** Managing and securing objects in Cloud Storage | [§7.2](07-storage-data.md#s7-2), [§7.4](07-storage-data.md#s7-4) |
| Object lifecycle management policies | [§7.3](07-storage-data.md#s7-3) |
| Executing queries (Cloud SQL, BigQuery, Bigtable, Spanner, Firestore, AlloyDB) | [§7.7](07-storage-data.md#s7-7)–[§7.9](07-storage-data.md#s7-9) |
| Estimating costs of data storage | [§7.5](07-storage-data.md#s7-5) |
| Backing up and restoring databases (Cloud SQL, Firestore, Spanner, AlloyDB, Bigtable) | [§7.7](07-storage-data.md#s7-7), [§7.8](07-storage-data.md#s7-8), [§7.13](07-storage-data.md#s7-13) |
| Reviewing job status (Dataflow, BigQuery) | [§7.9](07-storage-data.md#s7-9), [§7.12](07-storage-data.md#s7-12) |
| Database Center | [§7.10](07-storage-data.md#s7-10) |
| Configuring CMEK | [§7.14](07-storage-data.md#s7-14) |
| **3.3** Resizing a subnet's IPv4 range | [§4.2](04-networking.md#s4-2) |
| Reserving static external or internal IPs | [§4.8](04-networking.md#s4-8) |
| Adding custom static routes | [§4.3](04-networking.md#s4-3) |
| Cloud DNS and Cloud NAT | [§4.8](04-networking.md#s4-8) |
| Managing VPC firewall rules and Cloud NGFW policies | [§4.4](04-networking.md#s4-4) |
| **3.4** Cloud Monitoring alerts on resource metrics | [§9.3](09-operations.md#s9-3) |
| Custom metrics (from applications or logs) | [§9.4](09-operations.md#s9-4), [§9.3](09-operations.md#s9-3) |
| Configuring audit logs (VPC Flow Logs, audit logs, firewall logs) | [§9.7](09-operations.md#s9-7), [§4.11](04-networking.md#s4-11) |
| Exporting logs to external systems | [§9.5](09-operations.md#s9-5) |
| Log buckets, Log Analytics and log routers | [§9.5](09-operations.md#s9-5) |
| Viewing and filtering logs; viewing log message details | [§9.6](09-operations.md#s9-6) |
| Diagnostic tools (Trace, Profiler, Query Insights, index advisor) | [§9.8](09-operations.md#s9-8) |
| Personalized Service Health | [§9.9](09-operations.md#s9-9) |
| Configuring and deploying the Ops Agent | [§9.2](09-operations.md#s9-2) |
| Managed Service for Prometheus | [§9.4](09-operations.md#s9-4) |
| Gemini Cloud Assist for Cloud Monitoring | [§9.10](09-operations.md#s9-10) |
| Active Assist | [§9.10](09-operations.md#s9-10) |
| Cloud Hub | [§9.9](09-operations.md#s9-9) |

## <a id="sA-4"></a>A.4 Section 4 — Configuring access and security (~20%)

| Guide bullet | Taught in |
|:----------------------------------------------------------------|:----------------------------|
| **4.1** Viewing and creating IAM policies | [§3.3](03-identity-access.md#s3-3), [§3.5](03-identity-access.md#s3-5) |
| Attaching roles and policy inheritance in the organization hierarchy | [§3.3](03-identity-access.md#s3-3), [§2.1](02-organization-projects-billing.md#s2-1) |
| Managing role types and defining custom roles | [§3.4](03-identity-access.md#s3-4) |
| **4.2** Creating service accounts, including Google-managed service accounts | [§3.9](03-identity-access.md#s3-9) |
| Using service accounts in IAM policies with minimum permissions | [§3.9](03-identity-access.md#s3-9), [§3.10](03-identity-access.md#s3-10) |
| Assigning service accounts to resources | [§3.10](03-identity-access.md#s3-10) |
| Managing IAM permissions of a service account | [§3.10](03-identity-access.md#s3-10) |
| Managing service-account impersonation | [§3.10](03-identity-access.md#s3-10) |
| Creating and managing short-lived service-account credentials | [§3.11](03-identity-access.md#s3-11) |
| Using a Google Cloud service account with a GKE application | [§6.8](06-containers-serverless.md#s6-8) |
| Provisioning Workload Identity Federation | [§3.12](03-identity-access.md#s3-12) |

