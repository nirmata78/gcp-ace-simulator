---
title: "Part 7 — Storage and data"
parent: Theory
nav_order: 7
---

# Part 7 — Storage and data
{: .no_toc }

1. TOC
{:toc}

{: .objectives }
> 2.2 choosing and deploying data products (Cloud SQL, BigQuery, Firestore, Spanner, Bigtable, AlloyDB, Dataflow, Pub/Sub, Managed Kafka, Memorystore) and storage products (Cloud Storage and its classes, Filestore, NetApp Volumes, Managed Lustre) · loading data · multi-region redundancy · 3.2 all of managing storage and data, including Database Center and CMEK

<a id="s7-1"></a>

## 7.1 Choosing a storage product

Start with the **access model** the application needs; the product follows.

| Access model | Product | Pick it when the stem says |
|:----------------------|:------------------------------------|:--------------------------------------------------------|
| **Objects** over HTTP(S), any size, any number | **Cloud Storage** | "files", "images", "backups", "data lake", "static website", "archive" |
| **Block** device for one VM (or read-many) | **Persistent Disk / Hyperdisk** ([§5.4](05-compute-engine.md#s5-4)) | "boot disk", "database on a VM" |
| **Shared POSIX file system (NFS)** for many VMs or Pods | **Filestore** | "shared file system", "lift-and-shift app that expects NFS", "ReadWriteMany in GKE" |
| **Enterprise NAS: NFS and SMB**, Windows shares, NetApp features | **Google Cloud NetApp Volumes** | "SMB", "Windows file shares", "migrate our NetApp ONTAP", snapshots and cross-region replication of volumes |
| **Parallel file system** with very high throughput for thousands of clients | **Google Cloud Managed Lustre** | "AI training data loading", "HPC scratch", "checkpoints from thousands of GPUs" |
| Ephemeral, ultra-fast local scratch | **Local SSD** | "temporary", "cache", "scratch" |

{: .new-title }
> New in the June 2026 guide — the file-storage family
>
> **Filestore** is managed NFS in tiers from basic HDD to **zonal**, **regional** (survives a zone) and enterprise
> instances. **NetApp Volumes** is NetApp's storage run by Google — NFSv3/v4.1 **and SMB**, with Active Directory
> integration, volume snapshots, backups and replication — the answer whenever **Windows/SMB** or **NetApp** appears.
> **Managed Lustre** is a fully managed **parallel** file system for AI/ML and HPC, where aggregate throughput to
> many clients matters more than anything else. None of them is object storage, and none is the answer to "cheap
> archive".

<a id="s7-2"></a>

## 7.2 Cloud Storage: buckets, locations, classes

| Concept | Fact |
|:----------------------|:----------------------------------------------------------------------|
| **Bucket names** | **Globally unique**, immutable; a bucket's **location** is also fixed at creation |
| **Objects** | Immutable: a change writes a new object (or a new *generation*); no partial updates |
| Consistency | **Strong** read-after-write and list consistency |
| **Location type** | **Region** · **dual-region** (two regions — a predefined pair, or a **configurable** pair you choose within one continent, e.g. `--location=EU --placement=europe-west3,europe-central2`; optional **turbo replication** — replicated within 15 minutes) · **multi-region** (`US`, `EU`, `ASIA`) |
| Storage class | A bucket **default**, overridable **per object** |

### The four classes

| Class | Designed for | **Minimum storage duration** | Storage price | Retrieval fee |
|:----------------|:------------------------------|:--------------|:----------|:----------|
| **Standard** | Frequently accessed, "hot" | **None** | Highest | None |
| **Nearline** | About **once a month** | **30 days** | Lower | Low |
| **Coldline** | About **once a quarter** | **90 days** | Lower still | Higher |
| **Archive** | **Once a year or less** | **365 days** | **Lowest** | Highest |

<mark markdown="span">**Memorise 0 / 30 / 90 / 365.**</mark> Deleting, overwriting or moving an object before its minimum is billed as if it
had stayed the full minimum (the **early-deletion charge**).

{: .key }
> <mark markdown="span">**All four classes have the same millisecond latency to the first byte.**</mark> There is no thaw, no restore step, no
> waiting — that is a different cloud's archive model. Classes differ only in **storage price, retrieval price,
> minimum duration** (and availability SLA). A stem that says *"read once a year but must be available immediately
> when requested"* is still **Archive**; the "immediately" clause decides nothing.

**Autoclass** moves each object between classes automatically based on its access pattern, with no retrieval or
early-deletion charges — the answer to *"access patterns are unknown or change"*. It replaces lifecycle class
transitions on that bucket.

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| Bucket with a location and default class | `gcloud storage buckets create gs://kestrel-archive --location=EU --default-storage-class=ARCHIVE --uniform-bucket-level-access` |
| Let Autoclass choose the class | `gcloud storage buckets create gs://kestrel-media --location=EUR4 --enable-autoclass` |
| Copy; mirror a directory | `gcloud storage cp -r ./exports gs://kestrel-archive/2026/` · `gcloud storage rsync ./site gs://kestrel-web --recursive` |
| Change one object's class | `gcloud storage objects update gs://B/big.mov --storage-class=COLDLINE` |

<a id="s7-3"></a>

## 7.3 Lifecycle, versioning, soft delete and retention

| Feature | Does | Typical stem |
|:------------------------------|:------------------------------------------------------------|:------------------------------------------|
| **Lifecycle rules** | **Delete** objects, or **SetStorageClass** to a colder class, by age, date, number of newer versions, current class, prefix... | "Nearline after 30 days, delete after a year" |
| **Object versioning** | Keeps **noncurrent versions** when an object is overwritten or deleted | "recover a file someone overwrote" |
| **Soft delete** | Keeps **deleted** objects restorable for a window — **7 days by default** on new buckets, configurable (up to 90) | "undo an accidental delete from yesterday" |
| **Retention policy** | Objects **cannot be deleted or overwritten** until they reach the retention age | "keep every record for 7 years" |
| **Bucket Lock** | **Locks** the retention policy **permanently** — it can be lengthened, never shortened or removed | "WORM", "regulator requires immutability, even from admins" |
| **Object holds** / **object retention lock** | Per-object holds (temporary or event-based) and per-object retention settings | "legal hold on these files" |

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| Lifecycle rules (a JSON file of `SetStorageClass` / `Delete` actions on conditions such as `age`, `isLive`, `numNewerVersions`) | `gcloud storage buckets update gs://B --lifecycle-file=lifecycle.json` |
| Versioning; soft-delete window | `gcloud storage buckets update gs://B --versioning` · `... --soft-delete-duration=30d` |
| Retention policy, then lock it (irreversible) | `... --retention-period=7y` · `... --lock-retention-period` |
| Hold one object | `gcloud storage objects update gs://B/contract.pdf --temporary-hold` |


{: .watch }
> **Versioning, soft delete and a locked retention policy protect against different things.** Versioning and soft
> delete protect against **accidents** — someone with permission can still remove versions. A **locked retention
> policy** protects against **intent**: nobody, including an Owner, can delete the object early, and nobody can
> unlock the policy. Lifecycle rules only move objects to **colder** classes; they never warm them up, and changes
> can take up to 24 hours to act.
>
> **Lifecycle on a versioned bucket.** `Delete` on a live object makes it noncurrent, and its `age` still counts from
> creation. A plain `age` rule therefore deletes the noncurrent version too, on a later run. With `isLive: true` the rule
> never matches noncurrent versions, so they stay and stay billed until another rule removes them, such as
> `daysSinceNoncurrentTime`. `numNewerVersions` never matches the newest noncurrent version once the live one is gone.

<a id="s7-4"></a>

## 7.4 Securing objects

| Mechanism | Use |
|:------------------------------------------|:------------------------------------------------------------------|
| **Uniform bucket-level access** | **IAM only**, no object ACLs — the recommended setting. Reversible for 90 days, then permanent |
| Fine-grained access | IAM plus per-object **ACLs** — legacy needs only |
| **Public access prevention** | Blocks `allUsers` / `allAuthenticatedUsers` on the bucket (also enforceable by org policy) |
| **Signed URL** | **Time-limited** access to one object for someone **with no Google identity** — download or upload; V4 URLs last at most 7 days |
| Signed policy document | Browser **form uploads** with constraints (size, type) |
| HMAC keys | S3-compatible access for tools that speak the S3 API |
| CMEK default key | Customer-managed encryption for the bucket ([§7.14](#s7-14)) |

| Role | Grants |
|:--------------------------------------|:----------------------------------------------------------|
| `roles/storage.objectViewer` | Read and list objects |
| `roles/storage.objectCreator` | Create objects — **not** read, overwrite or delete them |
| `roles/storage.objectUser` | Read, create, update, delete objects |
| `roles/storage.objectAdmin` | Full control of **objects**, not bucket settings |
| `roles/storage.admin` | Full control of buckets **and** objects |

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| Read access to one bucket | `gcloud storage buckets add-iam-policy-binding gs://B --member=group:analysts@example.com --role=roles/storage.objectViewer` |
| Time-limited link, no key file | `gcloud storage sign-url gs://B/report.pdf --duration=2h --impersonate-service-account=SA_EMAIL` |

{: .tip }
> *"A partner with no Google account must download one file this week"* — **signed URL**. *"A drop box where
> uploaders must not read each other's files"* — **`objectCreator`**. *"Manage objects but never change the
> bucket's settings"* — **`objectAdmin`**, not `admin`.

<a id="s7-5"></a>

## 7.5 Estimating storage cost

| Product | You pay for | Levers |
|:----------------------|:------------------------------------------------------------|:------------------------------------------------|
| **Cloud Storage** | GB-months by class and location · **operations** (Class A writes/lists cost more than Class B reads) · **retrieval** (Nearline and colder) · early deletion · network egress and inter-region replication | Class, lifecycle, Autoclass, location |
| **Persistent Disk / Hyperdisk** | **Provisioned** size (not used size); Hyperdisk also provisioned IOPS and throughput; snapshots by stored data | Right-size; delete unattached disks |
| **Cloud SQL / AlloyDB** | Instance vCPU and memory · storage · **HA roughly doubles** the instance · backups beyond the free allowance | Size, HA only where needed, committed use |
| **BigQuery** | **Storage** (active vs **long-term** after 90 days unmodified at about half price; logical or physical billing) · **compute**: on-demand **per TiB scanned** or capacity **slots** (editions) | Partition, cluster, select only needed columns |
| **Spanner / Bigtable** | Compute capacity (nodes / processing units) · storage · replication | Autoscaling |

**Tools:** the **Pricing Calculator** before building; a BigQuery **dry run** before querying; **billing export**
after; **Storage Insights** and Active Assist recommendations to find waste.

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| Bytes a query would scan, free | `bq query --use_legacy_sql=false --dry_run 'SELECT ...'` |
| Hard cap on one query's cost | `bq query --maximum_bytes_billed=10000000000 'SELECT ...'` |

{: .trap }
> <mark markdown="span">**`LIMIT` does not reduce BigQuery on-demand cost**</mark> — the bytes scanned are the columns read across the
> partitions touched. Selecting fewer columns, filtering on the **partition** column, and **clustering** are what
> reduce it. `--maximum_bytes_billed` makes an expensive query **fail** instead of running.

<a id="s7-6"></a>

## 7.6 Choosing a database

| Product | Model | Scale and consistency | Pick it when the stem says |
|:----------------|:----------------------------------|:----------------------------------|:------------------------------------------|
| **Cloud SQL** | Managed MySQL, PostgreSQL, SQL Server | **One primary for writes**; read replicas | "managed relational", "migrate our MySQL/Postgres/SQL Server", "regional is fine" |
| **AlloyDB** | **PostgreSQL-compatible**, high performance | One primary + **read pools**; columnar engine for analytics | "Postgres, much faster", "transactions and analytics on the same data" |
| **Spanner** | Relational, SQL, **horizontally scalable** | **Strong (external) consistency, global**, up to 99.999% | "**global** relational", "scale **writes**", "strong consistency across regions" |
| **Bigtable** | Wide-column NoSQL, **row-key and range** access | Millions of ops/s, single-digit ms, petabytes | "time series", "IoT", "hundreds of thousands of writes/s", "ad-tech", "key lookups" |
| **Firestore** | **Document** NoSQL, serverless | Strong consistency, auto-scaling; real-time listeners, offline SDKs | "mobile / web app", "documents", "sync clients in real time" |
| **BigQuery** | Serverless **analytical warehouse**, columnar | Scans terabytes–petabytes | "analytics", "data warehouse", "SQL over huge datasets", "BI dashboards" |
| **Memorystore** | Managed **Redis, Valkey, Memcached** | Sub-millisecond, in memory | "cache", "session store", "leaderboard" |

{: .key }
> **Four eliminations decide most database items.**
> **1.** Cloud SQL and AlloyDB **cannot scale writes horizontally** — any stem about write throughput beyond one
> primary, or relational data spanning continents with strong consistency, is **Spanner**.
> **2.** BigQuery is **not** a low-latency point-lookup or OLTP store.
> **3.** Bigtable has **no joins, no multi-row transactions, no secondary indexes** in the relational sense — design
> is row-key design.
> **4.** Memorystore is a **cache**, never the system of record.

<a id="s7-7"></a>

## 7.7 Cloud SQL and AlloyDB

### Cloud SQL

| Topic | Fact |
|:------------------------------|:----------------------------------------------------------------------|
| Editions | **Enterprise** and **Enterprise Plus** (higher SLA, data cache, near-zero-downtime maintenance) |
| **High availability** | A **regional** instance: synchronous **standby in another zone**, automatic failover. **The standby serves no reads** |
| **Read replicas** | **Asynchronous** copies for **read scaling**, in the same or **another region**; a cross-region replica can be **promoted** for DR |
| **Backups** | **Automated** daily (retention configurable, default 7) and **on-demand**; restoring **to an instance overwrites it** |
| **Point-in-time recovery** | Needs **binary logging** (MySQL) or **WAL archiving** (PostgreSQL) enabled **beforehand**; recovers by **cloning to a new instance** at a timestamp |
| Connecting | **Cloud SQL Auth Proxy** or language **connectors** (IAM-authorised, TLS, no IP allow-lists) · **private IP** via private services access or PSC · public IP with authorized networks (discouraged) · **IAM database authentication** |
| Storage | Automatic storage increase; storage **cannot shrink** |
| Maintenance | Maintenance window and deny periods you set |

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| HA primary, PITR, private IP only | `gcloud sql instances create orders --database-version=POSTGRES_16 --region=R --availability-type=REGIONAL --enable-point-in-time-recovery --no-assign-ip --network=vpc-prod` |
| Read replica (in another region: DR) | `gcloud sql instances create orders-replica --master-instance-name=orders --region=R2` |
| Restore to a moment, as a new instance | `gcloud sql instances clone orders orders-restored --point-in-time='2026-09-20T14:04:00Z'` |
| Make the replica the primary | `gcloud sql instances promote-replica orders-replica` |
| Connect; export | `gcloud sql connect orders --user=postgres` · `gcloud sql export sql orders gs://B/orders.sql.gz --database=shop` |

{: .watch }
> <mark markdown="span">**High availability is not read capacity, and a replica is not a backup.**</mark> HA's standby exists only to take over
> from a failed zone. A read replica serves reads — and **replicates a destructive `DELETE` within seconds**, so it
> cannot undo one. *"A bad statement ran at 14:05; lose the least data"* is **PITR to a new instance** at 14:04,
> leaving the damaged original untouched for comparison.

### AlloyDB for PostgreSQL

A **cluster** holds a **primary instance** (highly available by default across zones) and optional **read pool
instances** that scale reads. Its **columnar engine** accelerates analytical queries on live transactional data.
**Continuous backup and recovery** allows restore to any point in its window (14 days by default, *verify*) plus
scheduled backups; **cross-region secondary clusters** provide DR. It connects like Cloud SQL (Auth Proxy, private
IP, PSC). *AlloyDB Omni* runs the same engine anywhere.

<a id="s7-8"></a>

## 7.8 Spanner, Bigtable and Firestore

### Spanner

- An **instance** has a **configuration** — **regional** (99.99%), **dual-region** or **multi-region** (99.999%) —
  and **compute capacity** in **nodes** or **processing units** (1 node = 1,000 PU; small instances from 100 PU).
  Managed **autoscaling** adjusts capacity.
- **GoogleSQL** or **PostgreSQL** dialect; ACID transactions across rows, tables and regions; **interleaved tables**
  to co-locate parent and child rows.
- **Hotspots:** a monotonically increasing primary key (a timestamp, a sequence) sends all inserts to one split —
  use UUIDv4, bit-reversed sequences or a hashed prefix.
- **Backups** (full and incremental; copies to other regions) and **PITR** within the version-retention period (up
  to 7 days).


### Bigtable

- An **instance** has one or more **clusters** (one per zone; several clusters = **replication**, across regions if
  you like), each with **nodes** that scale throughput linearly; SSD or HDD storage.
- **App profiles** route traffic: **single-cluster routing** (strong read-your-writes) or **multi-cluster routing**
  (automatic failover, **eventual** consistency between clusters).
- **Row-key design is everything**: queries are by key or key range. Avoid keys that start with a timestamp or a
  sequential ID (hotspots); use `device#reverse_timestamp` shapes; keep related data adjacent.
- Tables are sparse; time-series data is often "tall and narrow". **Backups** per table restore into a new table.
- Data access with **`cbt`** or client libraries; Bigtable also supports **GoogleSQL** queries (*recognise*).


### Firestore

- **Native mode** (documents in collections, real-time listeners, offline mobile/web SDKs) or **Datastore mode**
  (server workloads using the Datastore API).
- **Firestore with MongoDB compatibility** (Enterprise edition) accepts **standard MongoDB drivers and MQL** on
  serverless Firestore — *"move a MongoDB app to a serverless managed database with minimal code change"*.
- The **location** — a region or a multi-region such as `eur3` — is **permanent**. A project can hold several
  **named databases**.
- **Indexes**: single-field indexes are automatic; **composite indexes** must be created for multi-field queries
  (the error message links to create one). **TTL policies** delete expired documents.
- **Recovery**: **PITR** (when enabled, reads and exports as of any minute in the last 7 days), **scheduled
  backups** (daily or weekly, restore into a **new** database), and managed **export/import** to Cloud Storage.


<a id="s7-9"></a>

## 7.9 BigQuery

| Concept | Fact |
|:------------------------------|:----------------------------------------------------------------------|
| Hierarchy | Project → **dataset** (has a **location** — a region or `US`/`EU` multi-region, fixed) → tables, views, materialized views |
| **Partitioning** | By ingestion time, a date/timestamp column, or an integer range — queries filtering on it scan less; partition expiration drops old data |
| **Clustering** | Sorts data within partitions by up to four columns — cheaper filters and aggregations on them |
| **Compute pricing** | **On-demand** (per TiB scanned) or **capacity** (**editions**: slots in reservations, with autoscaling) |
| **Storage pricing** | Active vs **long-term** (unmodified 90 days, about half price); logical or physical billing |
| **Time travel** | Query or restore a table as of up to **7 days** ago (configurable 2–7), then **7 days of fail-safe** |
| Table snapshots / clones | Cheap point-in-time copies |
| Access | `bigquery.dataViewer` on the **data** + `bigquery.jobUser` on the **project that runs the query** |

### Jobs, and reviewing their status

Every load, query, export and copy is a **job**.

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| Recent jobs; one job's state and bytes | `bq ls -j -a` · `bq show -j JOB_ID` |
| The most expensive queries | `region-eu.INFORMATION_SCHEMA.JOBS`, ordered by `total_bytes_billed` |

{: .tip }
> *"Which queries cost the most yesterday?"* — `INFORMATION_SCHEMA.JOBS`. *"Did last night's load succeed?"* —
> `bq show -j` or the console's job history. *"Stop analysts running a 50 TB query by mistake"* —
> **maximum bytes billed** or a **custom query quota**; a budget only alerts afterwards.

<a id="s7-10"></a>

## 7.10 Memorystore and Database Center

**Memorystore** runs **Redis** (standalone Basic tier, or Standard tier with a replica and automatic failover),
**Redis Cluster**, **Valkey** and **Memcached**, reached over private networking. Typical jobs: caching query
results, session state, rate limiting, leaderboards. Persistence options exist on some offerings, but the exam's
rule stands: **a cache in front of a database, not the database**.

{: .new-title }
> New in the June 2026 guide — Database Center
>
> **Database Center** is one console view of the **whole database fleet** across projects — Cloud SQL, AlloyDB,
> Spanner, Bigtable, Firestore, Memorystore. It inventories every instance and surfaces **health, availability,
> security and cost issues**: no automated backups, no HA, outdated versions, public IPs, missing deletion protection,
> over-provisioning. It needs no agents, and Gemini can answer fleet questions in natural language (*"which Cloud SQL
> instances in production have no backups?"*). *"One place to see and fix risk across all our databases"* is Database
> Center; a spreadsheet or per-product consoles are the distractors.

<a id="s7-11"></a>

## 7.11 Loading and moving data

**Do the arithmetic before comparing tools.** <mark markdown="span">1 Gbps moves about **10 TB per day**</mark> at full, uncontended speed; 100
Mbps about **1 TB per day**.

```
Volume / usable bandwidth = days.  Acceptable?
   NO  -->  Transfer Appliance (ship a device, load it on site, send it back)
   YES -->  Where is the data?
              Another cloud (S3, Azure Blob), HTTP URLs, another bucket  -->  Storage Transfer Service
              On-premises file systems                                   -->  STS with agents
              Small, one-off, scripted                                    -->  gcloud storage cp / rsync
              Into BigQuery, recurring from SaaS / GCS / S3  -->  BigQuery Data Transfer Service
```

| Tool | Right when |
|:----------------------------------|:------------------------------------------------------------------|
| **`gcloud storage cp / rsync`** | Small or scripted transfers; parallel composite uploads for big files are automatic |
| **Storage Transfer Service** | Large or **recurring** transfers from other clouds, URL lists, on-premises (with **agent pools**), or between buckets; scheduling, retries, integrity checks, bandwidth limits |
| **Transfer Appliance** | Hundreds of TB or more, a **thin or busy link**, or a deadline the network cannot meet |
| **`bq load`** | One-off or batch loads of CSV, JSON, Avro, Parquet, ORC **from Cloud Storage** — batch loading is free |
| **External tables / BigLake** | **Query in place** without loading |
| **BigQuery Data Transfer Service** | **Scheduled** loads into BigQuery from SaaS, Cloud Storage, S3, other warehouses |
| **Storage Write API**, Pub/Sub BigQuery subscriptions, Dataflow | **Streaming** into BigQuery |
| **Datastream** | Change data capture from MySQL, PostgreSQL, Oracle into BigQuery or Cloud Storage |
| **Database Migration Service** | Migrating databases into Cloud SQL / AlloyDB |

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| Load files into a table | `bq load --source_format=PARQUET --autodetect sales.orders gs://kestrel-lake/orders/*.parquet` |

<a id="s7-12"></a>

## 7.12 Messaging and pipelines: Pub/Sub, Managed Kafka, Dataflow

### Pub/Sub

| Concept | Fact |
|:----------------------------------|:------------------------------------------------------------------|
| **Topic** | Where publishers send messages; a global resource (with an optional message-storage-location policy) |
| **Subscription** | **Each subscription gets every message**; subscribers **sharing** one subscription **split** the messages |
| Delivery types | **Pull** (StreamingPull), **push** to an HTTPS endpoint (with OIDC auth), or **export** straight into **BigQuery** or **Cloud Storage** |
| Acknowledgement | At-least-once by default; **ack deadline** 10 s default, up to 600 s; **exactly-once** available for pull |
| Retention | Unacked messages kept **7 days** by default (up to 31); topics can retain messages for replay |
| Failure handling | Retry policy (immediate or exponential backoff); **dead-letter topic** after N delivery attempts |
| Ordering | **Ordering keys** preserve order per key |
| Replay | **Snapshots** and **seek** to a time |

{: .key }
> <mark markdown="span">**Fan-out needs one subscription per consumer.**</mark> Four services that must each process every order need **four
> subscriptions** on one topic. Four workers sharing **one** subscription compete, and each message goes to one of
> them — that is load-balancing, not fan-out.

{: .new-title }
> New in the June 2026 guide — Managed Service for Apache Kafka
>
> **Managed Service for Apache Kafka** runs Apache Kafka clusters for you — sizing in vCPU and memory, automatic
> broker management and rebalancing, topics and partitions, Kafka Connect clusters — speaking the **native Kafka
> protocol**. Choose it when you already have **Kafka clients, connectors or skills**, need **partition-ordered
> logs** replayed by **offset**, or are migrating from self-managed Kafka. Choose **Pub/Sub** for a serverless,
> global service with per-message acknowledgement and no partitions to plan.

### Dataflow

**Dataflow runs Apache Beam pipelines** — batch and streaming, one programming model — as a managed,
autoscaling service. **Templates** (classic and Flex, and Google-provided ones such as *Pub/Sub to BigQuery*) let
people launch pipelines without code.

| Job action | Effect |
|:----------------------|:----------------------------------------------------------------------|
| **Drain** | Stop reading new input, **finish in-flight data**, then stop — **no data loss** |
| **Cancel** | Stop **immediately**; in-flight data is lost |
| **Update** | Replace a running streaming job with compatible new code, keeping state |


Job health is in the **Dataflow monitoring UI** (job graph, stage throughput, **system lag**, **data freshness**,
worker logs), with metrics in Cloud Monitoring. Workers run as a service account that needs `roles/dataflow.worker`.

**Recognise the neighbours:** **Dataproc** (managed Spark and Hadoop — *lift-and-shift existing Spark jobs*),
**Cloud Composer** (managed Airflow — *orchestrate a DAG of dependent steps*), **Workflows** (orchestrate API
calls), **Cloud Scheduler** (managed cron — *one job on a timer*), **Cloud Tasks** (queued calls with rate
limits).

<a id="s7-13"></a>

## 7.13 Backup, restore and multi-region redundancy

### Backup and restore

| Service | Backup mechanisms | Restores to |
|:----------------------|:------------------------------------------------------------|:------------------------------------------|
| Compute Engine | Snapshot schedules, machine images, **Backup and DR Service** | New disk / VM |
| Cloud Storage | Versioning, soft delete, retention, dual-/multi-region | Previous generation, undeleted object |
| **Cloud SQL** | Automated + on-demand backups, **PITR** | Same instance (overwrites) or **clone** to a new one |
| **AlloyDB** | Continuous backup + scheduled backups | **New cluster** at a point in time |
| **Spanner** | Backups (full / incremental, cross-region copies), PITR ≤ 7 days | New database |
| **Bigtable** | Table backups | New table |
| **Firestore** | PITR (7 days), scheduled backups, export/import | **New database** / imported data |
| BigQuery | Time travel, fail-safe, table snapshots, dataset replication | Table as of a time |

**Backup and DR Service** centralises backup policy for VMs, disks, databases and file shares, with **backup
vaults** that make backups immutable and indelible for a set period — the answer to *"backups ransomware cannot
delete"*.

### Multi-region redundancy across data solutions

| Product | Multi-region option | What it gives |
|:----------------------|:------------------------------------------------------------|:------------------------------------------|
| Cloud Storage | **Dual-region** (turbo replication: RPO 15 min) or **multi-region** bucket | Data survives a region; no failover action. Default replication: 99.9% of new objects in 1 h, **RPO 12 h**; turbo is **dual-region only** |
| Cloud SQL | **Cross-region read replica**, promoted on disaster. **Enterprise Plus advanced DR**: a designated **DR replica**, **switchover** (planned, zero loss) and **replica failover** (outage), plus a **write endpoint** — a DNS name that follows the primary | Minutes of RPO; apps need no reconfiguration with the write endpoint |
| Cloud SQL backups | **Custom backup location** (another region or a multi-region) | Backups outlive the instance's region, no replica needed |
| AlloyDB | **Cross-region secondary cluster** (HA alone is two zones of one region) | Promote on disaster |
| **Spanner** | **Multi-region** or **dual-region** configuration (two regions in one country, e.g. `dual-region-germany1`) | Synchronous, strongly consistent, **99.999%** for both (regional: 99.99%). Move the **default leader** to where writes originate — no data moves |
| Bigtable | **Clusters in several regions** + multi-cluster routing; **backup copies** to another region's cluster | Automatic failover, **eventual consistency** — read-your-writes needs a **single-cluster routing** app profile |
| Firestore | **Multi-region location** (`nam5`, `eur3`) — also for **Firestore with MongoDB compatibility** | Synchronous replication, automatic, 99.999% |
| BigQuery | **Cross-region dataset replication** (read-only secondary, promotable); **managed disaster recovery** (Enterprise Plus **failover reservation** — slots fail over with the data) | **Trap:** a **multi-region dataset** (`US`, `EU`) is stored in **one region** of that geography — **no cross-region redundancy** by itself |
| Persistent Disk | **Asynchronous Replication** to a disk in a second region | Target **RPO ≈ 1 minute**; fail over by attaching the secondary disk |
| Filestore | **Regional tier** (zones); **backups stored in another region** (restorable anywhere) | Regional = zone failures only; cross-region backup = region loss |
| NetApp Volumes | **Volume replication** to a storage pool in another region | Destination is read-only until replication is stopped |
| Memorystore | Cross-region replicas on some offerings (*verify*) | Promote on disaster |

{: .tip }
> *"Zero RPO, automatic failover, relational, across regions"* — **Spanner multi-region**; *"... and the data must
> stay in one country"* — **Spanner dual-region**. *"Survive a region with a few minutes' data loss, keep Postgres"*
> — **cross-region replica** (Cloud SQL) or **secondary cluster** (AlloyDB). *"Objects must be readable if a region
> is lost, and replicated within 15 minutes"* — **dual-region with turbo replication**. *"The data came back but the
> jobs had no slots"* — **BigQuery managed disaster recovery**. *"Apps had to be reconfigured after failover"* —
> **Cloud SQL write endpoint**.

<a id="s7-14"></a>

## 7.14 Encryption and customer-managed keys

**Everything at rest is encrypted by default with Google-managed keys**, using envelope encryption; you cannot
turn it off. The questions are about what to choose when default is not enough.

| Model | Key held by | Rotation | Revocation | Choose when |
|:------------------------------|:------------------------------|:----------------|:----------------------------|:------------------------------|
| **Google-managed** (default) | Google | Automatic | Not available to you | No stated key requirement |
| **CMEK** — customer-managed | **You, in Cloud KMS** | **On a schedule you set** | **Disable or destroy the key version** | "we must control, rotate and be able to revoke the key" |
| **CSEK** — customer-supplied | You, sent **with every request** | Manual | Stop supplying it | Cloud Storage and Compute Engine only; you keep raw keys |
| **Cloud EKM** | **An external key manager** outside Google | Yours | Yours | "Keys must never be stored in Google Cloud" |
| Client-side | You, before upload | Yours | Yours | Provider must never see plaintext |

### Cloud KMS vocabulary

```
Key ring   location is permanent: a region, a multi-region (eu, us) or global
  +-- Key           purpose (symmetric encrypt/decrypt, asymmetric sign, MAC); rotation period;
                    protection level: SOFTWARE | HSM (FIPS 140-2 Level 3) | EXTERNAL | EXTERNAL_VPC
        +-- Key version   the key material; enabled | disabled | scheduled for destruction | destroyed
```

{: .new-title }
> New in the June 2026 guide — configuring CMEK
>
> **Three rules make CMEK work, and each is a favourite distractor.**
> <mark markdown="span">**1. The service agent needs the key.**</mark> The product's **Google-managed service account** — not your user, not your
> workload's service account — needs **`roles/cloudkms.cryptoKeyEncrypterDecrypter`** on the key ([§3.9](03-identity-access.md#s3-9)).
> **2. Locations must match.** The key's location must be compatible with the resource's: a bucket in `EU` needs a
> key in `eu` (or a region inside it, per product rules); a regional Cloud SQL instance needs a key in that region.
> <mark markdown="span">**3. Rotation is not re-encryption.**</mark> Rotating creates a **new primary version** for new data; existing data stays
> readable with the older versions, which must stay enabled. **Disabling** a version makes data encrypted with it
> unreadable (reversible); **destroying** it is permanent after the scheduled-destruction delay (30 days by default)
> — *crypto-shredding*.
>
> **Cloud KMS Autokey** creates key rings and keys for CMEK automatically, per resource, in a dedicated key project
> — the answer to *"enforce CMEK everywhere without hand-creating hundreds of keys"*, paired with the org policy
> `gcp.restrictNonCmekServices`, which **blocks creating** resources in the listed services unless they use CMEK
> (preventive, unlike an alert on audit logs). A **BigQuery dataset in the `EU` multi-region needs a key in `eu`** —
> a `europe-west1` key fails with a location error however the permissions are set.

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| Key ring and key (HSM, 90-day rotation) | `gcloud kms keyrings create data-eu --location=europe-central2` · `gcloud kms keys create sql-key --keyring=data-eu --location=europe-central2 --purpose=encryption --rotation-period=90d --protection-level=hsm` |
| Let the product use the key | grant `roles/cloudkms.cryptoKeyEncrypterDecrypter` on the key to the product's **service agent** — create it first if absent: `gcloud beta services identity create --service=sqladmin.googleapis.com` |
| Use the key | `gcloud sql instances create ... --disk-encryption-key=KEY` · `gcloud storage buckets update gs://B --default-encryption-key=KEY` |
| Stop data being readable | `gcloud kms keys versions disable 3 --key=sql-key --keyring=data-eu --location=europe-central2` |

### More to recognise

- **More redundancy mechanics.** **Filestore instance replication** keeps a standby in another region (about
  30-minute RPO; promote the replica). **Memorystore Standard Tier** fails over between zones of **one** region.
  Watch a Cloud SQL replica's **replication lag** — it is the data you would lose. Spanner **custom instance
  configurations** add **read-only replicas** for distant readers; Spanner and Bigtable **backups can be copied**
  to another region. A BigQuery **dataset copy** (Data Transfer Service) is a one-off or scheduled copy, not a
  replica. A Firestore location is **permanent** — a new database and an export/import change it. A second
  Bigtable cluster also **isolates batch reads** from serving traffic.
- **Newer data products.** Spanner's **PostgreSQL interface**; AlloyDB **vector search** (pgvector, ScaNN) beside
  operational rows; **Memorystore for Valkey** (open-source, Redis-compatible); a Pub/Sub **BigQuery
  subscription** writes messages to a table with no pipeline; **Dataflow templates** run standard pipelines
  from parameters.
- **Newer storage features.** **Hierarchical namespace** buckets give real folders and atomic renames.
  **Anywhere Cache** is a zonal SSD read cache in front of a bucket. **Autoclass** moves each object by its own
  access. **Storage Transfer Service agents** copy from on-premises file systems. **Soft delete** keeps deleted
  objects (7 days by default) even without versioning.
- **Operating data.** A Backup and DR **backup vault** with enforced minimum retention holds backups nobody can
  delete early. Spanner **`version_retention_period`** (up to 7 days) allows reads at a past timestamp. BigQuery
  **`EXTERNAL_QUERY`** joins live Cloud SQL rows. The **physical** storage billing model bills compressed bytes.
  Database Center also covers **databases on Compute Engine VMs**. Rotating a key never re-encrypts: **rewrite**
  old data onto the new version; a version scheduled for destruction can be **restored** during the delay.

<a id="s7-15"></a>

## 7.15 Part 7 recall card

| Prompt | Answer |
|:------------------------------------------------|:--------------------------------------------------------|
| Minimum durations | **0 / 30 / 90 / 365** days |
| Read once a year, needed "immediately" | **Archive** — same latency as Standard |
| Unknown access pattern | **Autoclass** |
| Undo yesterday's accidental delete | **Soft delete** (7 days default) or versioning |
| Immutable for 7 years, even for admins | **Retention policy + Bucket Lock** |
| File for someone with no Google account | **Signed URL** (impersonated signer, no key file) |
| Upload-only drop box | `storage.objectCreator` |
| SMB shares for Windows | **NetApp Volumes** |
| NFS for many VMs / RWX in GKE | **Filestore** |
| Feed thousands of GPUs with training data | **Managed Lustre** |
| Global relational, scale writes, strong consistency | **Spanner** |
| Time series, 500k writes/s, key lookups | **Bigtable** (design the row key) |
| Mobile app, real-time sync | **Firestore** |
| Warehouse SQL over TBs | **BigQuery** |
| Postgres plus analytics on live data | **AlloyDB** |
| Bad DELETE at 14:05 | Cloud SQL **PITR clone** to 14:04 |
| HA standby serves reads? | **No** — use a read replica |
| Cut BigQuery cost | Partition, cluster, fewer columns; `LIMIT` does not help |
| Which queries were expensive? | `INFORMATION_SCHEMA.JOBS` |
| Fleet-wide database risk view | **Database Center** |
| 500 TB over 100 Mbps | **Transfer Appliance** (≈ 500 days otherwise) |
| S3 to Cloud Storage nightly | **Storage Transfer Service** |
| Four consumers each get every message | **Four subscriptions** |
| Existing Kafka clients, offsets | **Managed Service for Apache Kafka** |
| Stop a streaming job without losing data | Dataflow **drain** |
| CMEK: resource cannot use the key | Grant the **service agent** `cryptoKeyEncrypterDecrypter` |
| Make CMEK data unreadable now | **Disable** the key version |


