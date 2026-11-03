# Theory

**Every objective of the Associate Cloud Engineer exam guide that went live on 30 June 2026, taught once.**

The guide has four sections, weighted 20 / 30 / 30 / 20. It replaced the five-section guide and added new objectives:
Workforce and Workload Identity Federation, Cloud NGFW with secure tags, standalone organizations, GPUs vs TPUs,
AI-assisted tooling, Agent Runtime, Cloud Hub, Database Center, Autopilot resource requests, and more. Anything new
is marked with a purple **New in the June 2026 guide** callout wherever it is taught.

It is organised by dependency rather than by the guide's sections, so each part only assumes the parts before it.

| Part | Covers |
|:--|:--|
| [1 · The exam, locations and the tools](01-exam-locations-tools.md) | The paper, how items are written, regions and zones, the interfaces |
| [2 · Organization, projects, billing and quotas](02-organization-projects-billing.md) | The resource hierarchy, APIs, quotas, budgets, Asset Inventory |
| [3 · Identity and access](03-identity-access.md) | IAM, federation, service accounts, short-lived credentials, Secret Manager |
| [4 · Networking](04-networking.md) | VPCs, firewalls and Cloud NGFW, hybrid connectivity, DNS, NAT, load balancing |
| [5 · Compute Engine](05-compute-engine.md) | Machine families, disks, access, snapshots, managed instance groups, GPUs and TPUs |
| [6 · Containers and serverless](06-containers-serverless.md) | GKE, Artifact Registry, Cloud Run and functions |
| [7 · Storage and data](07-storage-data.md) | Cloud Storage, the databases, BigQuery, pipelines, backup and redundancy, encryption |
| [8 · Tooling](08-tooling.md) | Terraform, AI-assisted planning, AI and developer platforms |
| [9 · Operations](09-operations.md) | Monitoring, logging, audit logs, service health, optimisation |
| [10 · Compression for the last 48 hours](10-compression.md) | Confusion pairs, the numbers, the command atlas, the words in a stem |
| [Appendix A · The guide, mapped](appendix-a-guide-map.md) | Every guide bullet and the section that teaches it |
| [Appendix B · Provenance and limits](appendix-b-provenance.md) | What this was built from, and how far to trust it |
| [Practice scenarios](practice-scenarios.md) | 47 decision paths across eight companies, answers hidden until you open them |

Each part ends in a **recall card**: the whole part on one screen, for the second pass.

**How to read the callouts:**

{: .key }
> The fact to carry into the exam room.

{: .trap }
> The wrong answer the exam is written to attract.

{: .tip }
> The words in a stem that give the answer away.

{: .watch }
> Two things that sound alike and are tested against each other.

{: .note }
> Useful context that is less likely to decide an item.

{: .new }
> Introduced by the June 2026 guide.

<mark markdown="span">Highlighted text</mark> is the single most exam-relevant fact in a section.

## The loop

1. Read a part.
2. Drill that part in the simulator's **Learning mode**, filtered to its objectives.
3. Sit a **Certifying** exam, and reread the parts where you scored under 70%.

{: .note }
> Volatile facts are marked *verify*. Commands show the shape of a call, and were checked against the Google Cloud SDK
> on 29 September 2026. The ~70% pass mark is a community convention: Google publishes no cut score. Found something
> wrong? Every page has a *Suggest a fix* link.

## Building a PDF (optional)

The pages above are the source. A printable booklet can be built locally from them, and PDFs are not committed:

```bash
cd theory/pdf
./build-theory.sh            # assembles the pages, runs the QA gate, then compiles ACE-Theory-Recap.pdf
./build-theory.sh --check    # QA gate only: needs no LaTeX
```

It needs pandoc 3.9+, XeLaTeX and the macOS fonts Helvetica Neue and Menlo. `check-gcloud.py` also checks every
`gcloud` command against the release tracks of your installed SDK.
