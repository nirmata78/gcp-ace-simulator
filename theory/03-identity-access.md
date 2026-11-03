---
title: "Part 3 — Identity and access"
parent: Theory
nav_order: 3
---

# Part 3 — Identity and access
{: .no_toc }

1. TOC
{:toc}

{: .objectives }
> 1.1 Applying organizational policies · granting IAM roles · managing users and groups in Cloud Identity (manually and automated) · configuring Workforce Identity Federation · 4.1 all of IAM · 4.2 all of service accounts, including Workload Identity Federation

Three questions run through every access item, and they are answered by three different systems:

| Question | Answered by |
|:----------------------------------------------|:------------------------------------------------------------|
| **Does this person or workload exist, and can it authenticate?** | Cloud Identity / Workspace, an external IdP via federation, or a service account |
| **What may it do, and where?** | **IAM** — allow policies, deny policies, conditions |
| **What configurations are permitted at all, for anyone?** | **Organization policy** |

Keep the three apart and most distractors fall away by themselves.

## <a id="s3-1"></a>3.1 Where human identities come from

| Source | What it is | When it is the answer |
|:----------------------|:------------------------------------------------------------|:------------------------------|
| **Google account** | A personal account (Gmail or any email registered with Google) | Individuals, standalone orgs, Free Trial |
| **Cloud Identity** (Free or Premium) | Identity-as-a-service: managed users, groups, devices, SSO — without Workspace apps | The organization wants managed identities for Google Cloud only |
| **Google Workspace** | Cloud Identity plus Gmail, Drive and the rest | The company already runs on Workspace |
| **External IdP via Workforce Identity Federation** | Users stay in Entra ID, Okta, etc. and are **not** copied into Google | [§3.2](#s3-2) |

**Groups are the unit of access management.** Grant roles to `group:sre@example.com`, then manage people by
membership. A joiner becomes a membership change, not an IAM change, and the IAM policy stops churning. Groups can
contain users, service accounts and other groups.

### Managing users and groups — manually and automated

| Method | What it does |
|:------------------------------------|:------------------------------------------------------------------|
| **Admin console** (manual) | Create, suspend, delete users; create groups and manage membership |
| **Google Cloud Directory Sync (GCDS)** | **One-way** sync of users and groups **from Active Directory or LDAP into** Cloud Identity / Workspace, run on your own server on a schedule |
| **SAML / OIDC single sign-on** | Users authenticate at the corporate IdP; passwords never live at Google |
| **Automatic provisioning (SCIM)** from Entra ID, Okta and others | The IdP creates, updates and suspends Cloud Identity accounts as HR changes flow through it |
| **Directory API / scripts** | Programmatic account and group management |

{: .watch }
> **Sync versus SSO.** GCDS or SCIM provisioning decides *which accounts exist* in Cloud Identity. SSO decides *where
> people type their password*. A typical enterprise uses both: accounts synced from AD, authentication at AD FS or
> Entra ID. And **Workforce Identity Federation replaces both** — nothing is synced at all.

### Suspend, then delete

| Action | Effect |
|:----------------|:----------------------------------------------------------------------------------|
| <mark markdown="span">**Suspend**</mark> |; sessions and OAuth tokens are revoked; data and group memberships are kept. **Reversible** |
| **Delete** | The account is removed. Transfer Drive and other data first. Restorable only for a short period (*verify*) |

{: .key }
> <mark markdown="span">**A person who has left is removed at the identity layer, not in IAM.**</mark> Suspending the account makes every IAM
> binding, direct or via group, in every project, unusable at once — you cannot miss a binding you never had to
> find. IAM edits are for people who *stay* and whose access changes.

## <a id="s3-2"></a>3.2 Workforce Identity Federation

{: .new-title }
> New in the June 2026 guide — Workforce Identity Federation
>
> **Workforce Identity Federation lets people from an external identity provider — Microsoft Entra ID, Okta, AD FS,
> any OIDC or SAML 2.0 IdP — use Google Cloud without having a Google account and without being synchronised into
> Cloud Identity.** The IdP stays the source of truth: disable a user there and their Google Cloud access ends.

**The objects:**

| Object | What it is |
|:----------------------|:----------------------------------------------------------------------|
| **Workforce identity pool** | A container of external users, created at the **organization** level, location `global` |
| **Provider** | The trust with one IdP — OIDC or SAML — including **attribute mapping** (`google.subject`, `google.groups`, custom `attribute.*`) and an optional **attribute condition** limiting who may federate |
| **Principal identifiers** | How IAM names federated users in bindings |

```
principal://iam.googleapis.com/locations/global/workforcePools/POOL/subject/SUBJECT
principalSet://iam.googleapis.com/locations/global/workforcePools/POOL/group/GROUP_ID
principalSet://iam.googleapis.com/locations/global/workforcePools/POOL/attribute.dept/finance
principalSet://iam.googleapis.com/locations/global/workforcePools/POOL/*
```

**Granting access** uses those identifiers exactly like `user:` or `group:` — typically a `principalSet` for a
group coming from the IdP. **Signing in**: federated users reach a federated sign-in for the console, and
`gcloud` uses a login configuration file created for the pool. <mark markdown="span">**Group bindings only work if the provider maps the
IdP's groups claim to `google.groups`**</mark> — otherwise the `principalSet .../group/...` matches nobody. The pool's
**session duration** (default 1 h, 15 min–12 h, e.g. `--session-duration=1800s`) sets how long console and gcloud
sessions from that pool last — per pool, so contractors can get shorter sessions than employees. Some products and features do not support
workforce identities (*verify* the supported-products list before choosing it).


{: .watch }
> **Workforce versus Workload Identity Federation.** Same machinery, different subjects. **Workforce** is for
> **people** from an external IdP, pools live at the **organization**. **Workload** is for **software** outside
> Google Cloud — AWS, Azure, GitHub Actions, on-premises — pools live in a **project** ([§3.12](#s3-12)).

## <a id="s3-3"></a>3.3 The IAM model and inheritance

> **An allow policy binds a role to a set of principals, on a resource.** Every IAM item is a question about one
> of those three parts.

| Part | Examples | Notes |
|:----------------|:----------------------------------------------------------|:------------------------------------------|
| **Principal** | `user:` · `group:` · `serviceAccount:` · `domain:` · `principal://` / `principalSet://` · `allUsers` · `allAuthenticatedUsers` | Who |
| **Role** | `roles/storage.objectViewer` | A named bundle of **permissions** (`storage.objects.get`). You never grant a bare permission |
| **Resource** | Organization, folder, project, or an individual resource (bucket, topic, secret, service account...) | Where the policy is attached |
| **Condition** (optional) | A CEL expression on time, resource name/type or tags | [§3.6](#s3-6) |

An allow policy is a list of **bindings** plus an **etag** (for safe concurrent edits) and a **version** (3 is
needed when conditions are present). Each resource has at most one allow policy.

### Inheritance — the rules that decide most items

1. **Effective access is the union** of every binding that reaches the principal — directly, through any group, at
   the resource and at every ancestor up to the organization.
2. <mark markdown="span">**A lower allow policy cannot remove a higher grant.**</mark> There is no "most specific wins" and no negative binding.
3. **Only two things subtract from what allow policies grant:** an **IAM deny policy** (removes permissions from
   principals) and an **organization policy** (removes configurations from everyone) — [§3.6](#s3-6) and [§3.7](#s3-7). A
   **principal access boundary** policy also caps *which resources* a principal may reach, but it never grants
   ([§3.13](#s3-13), *More to recognise*).
4. **`allUsers` means anyone on the internet, unauthenticated; `allAuthenticatedUsers` means anyone with any Google
   account** — effectively public too. Both are wrong answers unless the stem is about public content.

{: .trap }
> *"Remove the user's project-level role so the folder grant no longer applies"* — impossible. The folder grant is
> still inherited. To take access away you remove the grant **where it was made**, remove the person from the
> **group** that carries it, or add a **deny** rule.

## <a id="s3-4"></a>3.4 Roles: basic, predefined, custom

| Kind | Examples | When |
|:------------|:----------------------------------------------|:------------------------------------------------------|
| **Basic** | `roles/owner`, `roles/editor`, `roles/viewer` | Legacy, cross-service, far too broad. **Almost never the answer** |
| **Predefined** | `roles/compute.instanceAdmin.v1`, `roles/pubsub.subscriber` | **The default correct answer.** Maintained by Google, per service |
| **Custom** | Your list of permissions | **Only when the need falls strictly between two predefined roles** |

**What Owner has that Editor lacks:** managing IAM on the resource (and a few billing associations). *"Who can grant
roles on this project?"* — an Owner or someone with a Security Admin-type role, never an Editor.

### Predefined roles worth naming on sight

| Area | Roles |
|:--------------|:------------------------------------------------------------------------------------------|
| IAM | `iam.securityAdmin` (manage IAM policies) · `iam.roleAdmin` (custom roles) · `iam.serviceAccountAdmin` · `iam.serviceAccountUser` · `iam.serviceAccountTokenCreator` · `iam.workloadIdentityUser` |
| Compute | `compute.admin` · `compute.instanceAdmin.v1` · `compute.networkAdmin` · `compute.securityAdmin` (firewalls, SSL) · `compute.viewer` · `compute.osLogin` / `compute.osAdminLogin` |
| Storage | `storage.objectViewer` · `storage.objectCreator` · `storage.objectUser` · `storage.objectAdmin` · `storage.admin` |
| GKE | `container.admin` · `container.developer` · `container.viewer` |
| Run / functions | `run.admin` · `run.developer` · `run.invoker` · `cloudfunctions.developer` |
| Data | `bigquery.dataViewer` · `bigquery.dataEditor` · `bigquery.jobUser` · `bigquery.user` · `cloudsql.client` · `spanner.databaseUser` · `pubsub.publisher` · `pubsub.subscriber` |
| Operations | `logging.viewer` · `logging.privateLogViewer` (Data Access logs) · `logging.configWriter` · `monitoring.viewer` · `monitoring.editor` · `monitoring.metricWriter` · `logging.logWriter` |
| Secrets & keys | `secretmanager.secretAccessor` · `cloudkms.cryptoKeyEncrypterDecrypter` · `cloudkms.admin` |

{: .watch }
> **`compute.networkAdmin` versus `compute.securityAdmin`.** Network Admin builds networks, subnets, routes and load
> balancers but **cannot change firewall rules or SSL certificates**; Security Admin manages firewall rules and
> certificates. The separation-of-duties question uses exactly this split.

### Custom roles

- Defined at the **organization** or **project** level — **not at a folder**. An org-level custom role can be
  granted anywhere in the org; a project-level one only in that project.
- Built from permissions whose custom-role support level is *supported* (some are *testing* or *not supported*).
- Carry a **launch stage** (`ALPHA`, `BETA`, `GA`, `DEPRECATED`, `DISABLED`).
- **You maintain them.** When Google adds a permission to a service, predefined roles gain it and your custom role
  does not — the stated reason to prefer predefined roles.

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| Custom role in a project (or `--organization=ORG`) | `gcloud iam roles create vmOperator --project=P --permissions=compute.instances.get,...` |
| Start from a predefined role | `gcloud iam roles copy --source=roles/compute.viewer --destination=myViewer --dest-organization=ORG` |
| Add a permission to a custom role | `gcloud iam roles update vmOperator --project=P --add-permissions=compute.instances.start` |

## <a id="s3-5"></a>3.5 Viewing and changing policies

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| Grant one role (additive, safe) | `gcloud projects add-iam-policy-binding P --member=group:sre@example.com --role=roles/compute.instanceAdmin.v1` |
| Remove one binding | `gcloud projects remove-iam-policy-binding P --member=user:x@example.com --role=roles/viewer` |
| Replace the whole policy | `gcloud projects get-iam-policy P` → edit → `gcloud projects set-iam-policy P policy.json` |
| The same on a folder, organization or bucket | `gcloud resource-manager folders add-iam-policy-binding` · `gcloud organizations add-iam-policy-binding` · `gcloud storage buckets add-iam-policy-binding` |

{: .trap }
> <mark markdown="span">**`set-iam-policy` replaces the whole policy.**</mark> It is a read–modify–write: get the policy, edit it, set it back
> with the same **etag** — if someone changed the policy in between, the etag no longer matches and the write is
> rejected rather than silently overwriting their change. For one grant, `add-iam-policy-binding` is the safer
> answer.

**Attaching a policy lower in the hierarchy** uses the same verbs on the resource itself — a bucket, a topic, a
secret, a service account. Resource-level bindings are how you grant access to *one* bucket rather than all of
them.

## <a id="s3-6"></a>3.6 Conditions, deny policies and Privileged Access Manager

### IAM conditions — scoping a grant

| Need | Condition |
|:----------------------------------------------|:------------------------------------------------------------------|
| Access that **expires** automatically | `request.time < timestamp("2026-12-31T00:00:00Z")` |
| Only business hours | `request.time.getHours("Europe/Warsaw") >= 9 && ...` |
| Only certain resources by name | `resource.name.startsWith("projects/_/buckets/fin-")` |
| Only resources carrying a tag | `resource.matchTag("ORG_ID/env", "prod")` |

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| Grant that expires by itself | `add-iam-policy-binding ... --condition='expression=request.time < timestamp("2026-10-31T00:00:00Z"),title=audit-window'` |

*"The contractor's access must end on 31 October without anyone remembering to remove it"* is a condition.

### Deny policies — the IAM subtraction

A **deny policy** names principals, permissions they may never use, optional **exception principals**, and an
optional condition. It attaches to an **organization, folder or project** and is **evaluated before allow
policies**: <mark markdown="span">a matching deny wins over every allow</mark>, everywhere below its attachment point.


Managing them needs `roles/iam.denyAdmin`. Deny policies name permissions in the form
`storage.googleapis.com/buckets.delete`, and the attachment point is URL-encoded (`/` becomes `%2F`).

{: .watch }
> **Deny policy versus organization policy.** A **deny policy** removes *permissions* from *principals* —
> *"developers must never delete production buckets, whatever roles they hold"*. An **organization policy** removes
> *configurations* from *everyone* — *"no VM in this folder may have an external IP"*. Both bind project Owners.

### Privileged Access Manager

**Privileged Access Manager (PAM)** provides **just-in-time, time-bound elevation**: an administrator defines an
**entitlement** (which roles, on which resource, for how long, who may request, whether approval is needed); an
eligible user **requests a grant** with a justification, an approver approves, and the role is granted for the
window and then removed automatically, with the whole flow audited. It is the answer to *"engineers should hold
production admin rights only while working on an incident, with approval"* — standing Owner grants are the
distractor.

## <a id="s3-7"></a>3.7 Organization policy and tags

**The Organization Policy Service restricts what may be configured**, for every principal including Owners. A
policy sets a **constraint** on a node, and descendants inherit it.

| Constraint shape | Example | Effect |
|:----------------------|:----------------------------------------------|:------------------------------------------------|
| **Boolean** | `iam.disableServiceAccountKeyCreation` | On or off |
| **List** | `gcp.resourceLocations`, `compute.vmExternalIpAccess` | Allow or deny listed values |
| **Managed constraints** | Newer, typed versions of common constraints (e.g. `compute.managed.*`) | Same idea, better validation and dry-run support |
| **Custom constraints** | A CEL condition on a resource's fields, for supported services | *"No GKE cluster without Workload Identity"* |

**Inheritance:** a child node inherits the parent's policy unless its own policy **replaces** it; for list
constraints a child may instead **merge** with the parent. **Dry-run** policies and the **Policy Simulator** show
what a new policy would block before you enforce it. Changing org policies needs
`roles/orgpolicy.policyAdmin`, usually at the organization.

### Constraints worth recognising on sight

| Constraint | Stops |
|:------------------------------------------|:--------------------------------------------------------------|
| `gcp.resourceLocations` | Creating resources outside approved regions — **data residency** |
| `iam.allowedPolicyMemberDomains` | Granting roles to identities outside your organization — *domain restricted sharing* |
| `iam.disableServiceAccountKeyCreation` | Creating service-account keys |
| `iam.disableServiceAccountKeyUpload` | Uploading your own public keys |
| `iam.automaticIamGrantsForDefaultServiceAccounts` | The automatic **Editor** grant to default service accounts |
| `compute.vmExternalIpAccess` | VMs having external IPs (allow-list of VMs, or deny all) |
| `compute.requireOsLogin` | SSH keys in metadata — forces OS Login ([§5.5](05-compute-engine.md#s5-5)) |
| `compute.skipDefaultNetworkCreation` | Creation of the `default` VPC in new projects |
| `compute.restrictVpcPeering` / `compute.restrictSharedVpcHostProjects` | Uncontrolled network connections |
| `storage.uniformBucketLevelAccess` | Buckets using ACLs |
| `storage.publicAccessPrevention` | Buckets or objects being made public |
| `gcp.restrictNonCmekServices` | Resources created without customer-managed keys ([§7.14](07-storage-data.md#s7-14)) |

{: .note }
> **Secure by default.** Organizations created from 2024 onward have several of these enforced automatically —
> among them key creation disabled, uniform bucket-level access, public access prevention, domain restricted
> sharing, and no automatic Editor grant for default service accounts (*verify* the current list). That is why a
> brand-new org may refuse to create a service-account key.

{: .tip }
> *"Prevent anyone — **including project owners** — from ..."* is an organization policy. The moment a stem says
> *including owners* or *even administrators*, stop reading IAM options.

### Tags — the IAM-governed metadata

**Tags** (resource-manager tags) are key–value pairs defined at the organization or a project, attached to
organizations, folders, projects and many resources, and **inherited** down the hierarchy. Unlike labels, **who
may attach a tag value is itself controlled by IAM** (`roles/resourcemanager.tagUser`), so tags can safely drive
policy:

- **Conditional IAM**: `resource.matchTag(...)` in a binding ([§3.6](#s3-6)).
- **Conditional org policy**: enforce a constraint only where `env=prod`.
- **Cloud NGFW**: *secure tags* select firewall-policy sources and targets ([§4.4](04-networking.md#s4-4)).

## <a id="s3-8"></a>3.8 Troubleshooting and right-sizing access

| Question | Tool |
|:----------------------------------------------|:----------------------------------------------------------|
| *Why* can (or can't) this principal do this action on this resource? | **Policy Troubleshooter** |
| *Who* can do X on Y? *What* can this principal reach? | **Policy Analyzer** (Asset Inventory) |
| Which roles are more than this principal actually uses? | **IAM role recommender** (Active Assist) — based on ~90 days of usage |
| Is this service account or key still used? | **Activity Analyzer** / service-account usage insights |
| What would a policy change break? | **Policy Simulator** |


## <a id="s3-9"></a>3.9 Service accounts: kinds and lifecycle

A **service account is both a principal and a resource.** You grant roles **to** it (what it can do) and roles
**on** it (who can use it).

| Kind | Address | Created by | Notes |
|:----------------------|:----------------------------------------------|:------------------|:--------------------------------|
| **User-managed** | `NAME@PROJECT_ID.iam.gserviceaccount.com` | You | The ones you design, one per workload |
| **Default** | Compute: `PROJECT_NUMBER-compute@developer.gserviceaccount.com`; App Engine: `PROJECT_ID@appspot.gserviceaccount.com` | Enabling the API | Historically granted **Editor** — replace with purpose-made accounts |
| **Google-managed (service agents)** | `service-PROJECT_NUMBER@gcp-sa-SERVICE.iam.gserviceaccount.com` (Cloud Storage: `...@gs-project-accounts...`) | Google, when the API is enabled or first used | The product's own identity **acting in your project** |

{: .new-title }
> New in the June 2026 guide — Google-managed service accounts
>
> **Service agents** are how Google services act on your resources: the Cloud Storage service agent publishes bucket
> notifications to Pub/Sub, the Compute Engine service agent attaches disks, a product's agent reads a CMEK key.
> They appear in IAM with a *Service Agent* role. Three things the exam uses: **do not remove their roles** (the
> product breaks); **grant them extra roles when a feature needs it** — most often
> `roles/cloudkms.cryptoKeyEncrypterDecrypter` for CMEK ([§7.14](07-storage-data.md#s7-14)) or `roles/pubsub.publisher` for Cloud Storage events
> ([§6.11](06-containers-serverless.md#s6-11)); and **force-create one** before first use with
> `gcloud beta services identity create --service=SERVICE.googleapis.com`.

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| Create | `gcloud iam service-accounts create app-runtime` |
| Stop it now, reversibly | `gcloud iam service-accounts disable app-runtime@P.iam.gserviceaccount.com` |
| Delete; recover within 30 days | `gcloud iam service-accounts delete SA_EMAIL` · `gcloud iam service-accounts undelete UNIQUE_ID` |

{: .trap }
> <mark markdown="span">**Disable before delete.**</mark> Disabling stops the account immediately and is reversible. Deleting it leaves its role
> bindings behind as orphans, and a new account created with the **same name** is a **different principal** (a new
> unique ID) that does **not** inherit the old bindings. Undelete works for 30 days, by unique ID.

**The account ID is permanent.** The email `NAME@PROJECT_ID.iam.gserviceaccount.com` never changes; only the display
name and description can. "Renaming" a service account means creating a new one, granting it the same roles,
moving workloads to it, then disabling and deleting the old one.

## <a id="s3-10"></a>3.10 Attaching and impersonating

Two different ways to "use" a service account, guarded by two different roles granted **on** the account:

| Role on the service account | Lets the holder | Typical stem |
|:--------------------------------------|:------------------------------------------------|:----------------------------------|
| **`roles/iam.serviceAccountUser`** (`iam.serviceAccounts.actAs`) | **Attach** it to a resource they create — a VM, Cloud Run service, function, Dataflow job | *"Deploy a Cloud Run service that runs as `app@`"* |
| **`roles/iam.serviceAccountTokenCreator`** | **Mint tokens** for it — i.e. act **as** it right now | *"A CI identity must deploy as `deployer@` with no keys"* |

### Attaching — the normal case

A workload on Google Cloud runs **as** an attached service account and receives short-lived credentials from the
**metadata server** automatically. Nothing is stored; nothing rotates by hand.

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| Run a VM as a service account | `gcloud compute instances create vm1 --service-account=SA_EMAIL --scopes=cloud-platform` |
| Run a Cloud Run service as one | `gcloud run deploy api --image=IMG --service-account=SA_EMAIL` |

**Attaching an account from another project** — a central `identities` project is a common design — also
requires that the organization policy `iam.disableCrossProjectServiceAccountUsage` is **not** enforced on the project
that owns the service account; where it is enforced, the attach fails however the IAM grants look.

**Access scopes** are a legacy VM-level filter applied *on top of* IAM. Best practice: the `cloud-platform` scope
plus narrow IAM roles on a dedicated service account. Changing a VM's service account or scopes requires the VM
to be **stopped**.

### Impersonating — acting as another identity

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| Let `ci` impersonate `deployer` | `gcloud iam service-accounts add-iam-policy-binding deployer@P.iam.gserviceaccount.com --member=serviceAccount:ci@P.iam.gserviceaccount.com --role=roles/iam.serviceAccountTokenCreator` |
| Run one command as `deployer` | `gcloud compute instances list --impersonate-service-account=deployer@P.iam.gserviceaccount.com` |
| Make it the default for gcloud | `gcloud config set auth/impersonate_service_account SA_EMAIL` |

Impersonation issues **short-lived tokens**, writes **no key material**, and the audit log records **both** the
caller and the impersonated account — the original principal is in
`protoPayload.authenticationInfo.serviceAccountDelegationInfo`, which is how *"which engineer acted as `deploy-sa`?"* is
answered. It is also the recommended way for *humans* to use a privileged service
account — grant the engineer Token Creator on it rather than handing out a key.

{: .watch }
> **Service Account User versus Token Creator.** *"Create a VM that runs as `sa@`"* needs **User**
> (`actAs`). *"Run this command as `sa@` from my terminal / pipeline"* needs **Token Creator**. <mark markdown="span">Both are granted **on
> the service account**, not on the project</mark>, for least privilege.

## <a id="s3-11"></a>3.11 Short-lived credentials, and keys as a last resort

The **IAM Service Account Credentials API** (`iamcredentials.googleapis.com`) is what impersonation calls:

| Call | Produces | Used for |
|:----------------------|:--------------------------------------------------------|:------------------------------------------|
| `generateAccessToken` | OAuth 2.0 access token, **1 hour** by default (extendable to 12 h by org policy) | Calling Google APIs |
| `generateIdToken` | OIDC ID token for an **audience** | Calling Cloud Run, functions, IAP-protected apps |
| `signBlob` / `signJwt` | A signature by the account's Google-managed key | Signed URLs without a key file ([§7.4](07-storage-data.md#s7-4)), custom JWTs |

**ID tokens only:** `roles/iam.serviceAccountOpenIdTokenCreator` lets a caller mint **ID tokens** for the account —
enough to call Cloud Run or an IAP-protected app — but not access tokens or signatures. It is the least-privilege
choice when that is all a scheduler or caller needs.


### Application Default Credentials

Client libraries find credentials in this order: the file named by **`GOOGLE_APPLICATION_CREDENTIALS`**; the
user credentials written by **`gcloud auth application-default login`**; the **attached service account** via the
metadata server. On Google Cloud, the third needs no configuration at all — which is why "set
`GOOGLE_APPLICATION_CREDENTIALS` to a key file" is almost always the distractor.

### Service-account keys

A **user-managed key** is a long-lived private key that **never expires by default**, can be copied anywhere, and
is rotated only if you rotate it. Google's position, and the exam's: <mark markdown="span">**a key is the last resort.**</mark>

| Situation | Keyless mechanism |
|:----------------------------------------------|:------------------------------------------------------|
| Workload on Google Cloud | **Attached** service account |
| One Google Cloud identity needs another's rights | **Impersonation** |
| Workload on AWS, Azure, GitHub, on-premises | **Workload Identity Federation** ([§3.12](#s3-12)) |
| Pod in GKE | **Workload Identity Federation for GKE** ([§6.8](06-containers-serverless.md#s6-8)) |
| Developer laptop | `gcloud auth application-default login` (+ impersonation) |
| Legacy system that supports none of these | A key — then restrict, rotate, monitor |

**Controls when keys must exist:** `iam.disableServiceAccountKeyCreation` (block them), an expiry constraint
(`iam.serviceAccountKeyExpiryHours`), rotation (`gcloud iam service-accounts keys create` / `delete`), and usage
monitoring (Activity Analyzer, Security Command Center findings).

{: .trap }
> **"Store the JSON key in Secret Manager" does not satisfy "no key material".** It is still a long-lived key that
> anything able to read the secret can exfiltrate. Secret Manager is the right home for secrets Google *cannot* mint
> ([§3.13](#s3-13)); a service-account credential is something Google mints on demand.

## <a id="s3-12"></a>3.12 Workload Identity Federation for external workloads

{: .new-title }
> New in the June 2026 guide — provisioning Workload Identity Federation
>
> **Software running outside Google Cloud exchanges the credential it already has for a short-lived Google token.**
> An AWS role, an Azure managed identity, a GitHub Actions or GitLab OIDC token, a SAML assertion or an X.509
> certificate is presented to Google's **Security Token Service**, validated against a provider you configured, and
> exchanged — no service-account key ever leaves Google.

```
External credential (AWS role · OIDC token from GitHub/GitLab/Azure · SAML · X.509)
      |
      v
Workload identity pool (in a PROJECT)  --  provider: AWS | OIDC | SAML | X.509
      |   attribute mapping:   google.subject = assertion.sub, attribute.repository = ...
      |   attribute condition: assertion.repository == "kestrel/api"
      v
Google STS  -->  federated token  -->  (a) direct IAM grant to the principal, or
                                       (b) impersonate a service account (roles/iam.workloadIdentityUser)
```


The workload is given a **credential configuration file** — it contains no secret, only where to fetch the
external token and which pool and provider to use. **Creating and maintaining** pools and providers needs
`roles/iam.workloadIdentityPoolAdmin`; **using** one to act as a service account needs
`roles/iam.workloadIdentityUser` on that account — two different jobs, two different roles. Use the
service-account path (b) when an API does not accept federated principals directly.

**Kubernetes clusters outside Google Cloud** federate with an **OIDC provider** whose issuer is the cluster's
service-account token issuer. If Google cannot reach that issuer (a private, on-premises cluster), **upload the
cluster's JWKS** with `--jwk-json-path`; the control plane never needs to be exposed.

{: .key }
> <mark markdown="span">**The attribute condition is the security boundary.**</mark> Without one, *any* identity the IdP can issue — any GitHub
> repository in the world, for a public issuer — could federate. *"Only pipelines from our repository"* is an
> attribute condition on the provider.

## <a id="s3-13"></a>3.13 Secret Manager

**Secret Manager stores secrets Google cannot mint for you** — a third-party API key, a database password, a TLS
private key from an outside CA.

| Concept | Meaning |
|:----------------------|:----------------------------------------------------------------------|
| **Secret** | The named container, with its own IAM policy, labels, replication policy |
| **Version** | The actual payload. Versions are immutable; states: enabled, disabled, destroyed |
| **`latest`** | An alias for the newest enabled version — rotation is *add a version* |
| **Replication** | Automatic (Google chooses) or user-managed (you pin regions); also regional secrets |
| **Rotation schedule** | Secret Manager **notifies** a Pub/Sub topic on schedule; **your code rotates** |
| **Expiration** | Delete the secret at a time or after a TTL |

| Role | Grants |
|:--------------------------------------|:----------------------------------------------------------|
| **`roles/secretmanager.secretAccessor`** | **Read the payload.** What a workload needs — grant it **on the one secret** |
| `roles/secretmanager.viewer` | See secrets and versions exist; **not** the payload |
| `roles/secretmanager.secretVersionManager` | Add, disable, destroy versions |
| `roles/secretmanager.admin` | Everything |

{: .cmds }
| Task | Command |
|:------------------------------------|:----------------------------------------------------------------------|
| Create a secret; add a version (rotate) | `gcloud secrets create db-password --data-file=-` · `gcloud secrets versions add db-password --data-file=-` |
| Read the current value | `gcloud secrets versions access latest --secret=db-password` |

**Consuming secrets:** Cloud Run and Cloud Run functions mount a secret **as an environment variable** (resolved
when an instance starts) or **as a file volume** (read at access time, so a new version is picked up without a
redeploy). GKE uses the Secret Manager add-on / CSI driver. Code can call the API directly.

{: .watch }
> **Where a secret must not live, and why.** Baked into the image (cannot rotate without a rebuild), in instance
> **metadata** (readable by every process on the VM and visible in the console), in the repository, or in a plain
> bucket (no versioning semantics, no rotation notifications, generic audit only). Secret Manager is the managed
> product for the job — and a Kubernetes Secret is only base64 unless you add encryption.

### More to recognise

- **Workforce pools.** An **attribute condition** on the provider (`assertion.employee_type == 'staff'`) decides
  who may federate at all. **Disabling the pool** (`--disabled`) stops every federated user at once and can be
  undone. Custom attributes become principal sets: `principalSet://.../workforcePools/POOL/attribute.department/finance`.
  **Microsoft Entra ID** provisions Cloud Identity users through its enterprise application; GCDS is for LDAP /
  on-premises AD.
- **Limits and delegation in IAM.** An allow policy holds at most **1,500 principals** — use groups.
  **Principal access boundary** policies say which resources a set of principals is *eligible* to use; they never
  grant, and they block access outside the boundary whatever roles are granted. A condition on
  `iam.googleapis.com/modifiedGrantsByRole` lets a delegate grant **only** named roles. `request.time` conditions
  with a time zone give business-hours access; `resource.name.startsWith("projects/_/buckets/logs-")` scopes a
  project grant to matching buckets. **`roles/iam.securityReviewer`** reads every IAM policy without data access.
- **Service accounts in operation.** `iam.serviceAccountKeyExpiryHours` makes new keys expire. **Activity
  Analyzer** shows each key's last authentication. **HMAC keys** on a service account serve S3-compatible tools.
  Cloud Scheduler calls a private Cloud Run service with an **OIDC token** for an account holding
  `roles/run.invoker`. A VM's service account changes only while it is **stopped**. Autopilot has Workload
  Identity Federation for GKE on by default.
- **Workload identity federation in practice.** Separate **pools per environment**; **disable a provider**
  during an incident at the IdP; audit logs show the federated principal in
  `authenticationInfo.principalSubject`; a GitHub Actions job needs **`permissions: id-token: write`** or there is
  no token to exchange.

## <a id="s3-14"></a>3.14 Part 3 recall card

| Prompt | Answer |
|:------------------------------------------------|:--------------------------------------------------------|
| Leaver — revoke everything, now | **Suspend** the account (or disable it in the external IdP) |
| Sync AD users into Cloud Identity | **GCDS** (one-way) or SCIM provisioning from the IdP |
| Entra ID users, no copies in Google | **Workforce Identity Federation** (org-level pool) |
| GitHub Actions deploying, no keys | **Workload Identity Federation** + attribute condition |
| Remove an inherited grant from below | Impossible — remove it at the source, or **deny policy** |
| Access that expires by itself | **IAM condition** on `request.time` |
| Admin rights only during an incident, approved | **Privileged Access Manager** |
| Need between two predefined roles | **Custom role** (org or project, never folder) |
| Build networks but not touch firewalls | `compute.networkAdmin` (firewalls = `compute.securityAdmin`) |
| Nobody, including owners, may do X | **Organization policy** |
| Why can't Ana stop this VM? | **Policy Troubleshooter** |
| Who can read this bucket? | **Policy Analyzer** |
| Attach an SA to a VM / service | **Service Account User** on the SA |
| Act as an SA from CI or a terminal | **Token Creator** on the SA + impersonation |
| Product needs to use my KMS key | Grant the product's **service agent** the key role |
| Stop an SA now, reversibly | **Disable** it |
| Third-party password, rotate without redeploy | **Secret Manager**, `secretAccessor` on that secret, mounted as a volume |


