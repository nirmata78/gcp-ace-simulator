"""Content for the exam-eve recap booklet.

Structure: one dict per page, one page per topic. Text is ReportLab mini-HTML
(``<b>``, ``<i>``, ``<font color=...>``), so literal ``<`` and ``&`` must be
written as entities.

Selection principle: this is a *recall* booklet, not a course. A fact earns a
line here only if it decides an exam item — a discriminator between two
plausible products, an exact limit, or a behaviour that surprises people.
"""

from __future__ import annotations

from typing import Any, Dict, List

TITLE = "Google Cloud Associate Cloud Engineer — Exam-Eve Recap"
SUBTITLE = "Every fact worth recalling, one topic per page"

PAGES: List[Dict[str, Any]] = []


# ==========================================================================
# 1 — Start here
# ==========================================================================
PAGES.append({
    "id": "start",
    "num": 1,
    "label": "Start here",
    "title": "The paper, the clock, and how to pick an answer",
    "accent": "ink",
    "blocks": [
        ("lede",
         '<b>Read this booklet twice.</b> First pass, front to back, ~50 minutes — you are '
         'refreshing recognition, not learning. Second pass, ~20 minutes, read only the '
         'coloured panels and the tables. Read <b>page 2 and the final card</b> last, closest to '
         'the exam — they change how you answer rather than what you know.'),
        ("facts", [("50", "questions"), ("2 h", "on the clock"),
                   ("2m24s", "per question"), ("~70%", "working cut score"),
                   ("0", "penalty for a wrong guess")]),
        ("cols", {"ratio": (52, 48), "cols": [
            [
                ("h", "What the paper covers"),
                ("table", {"w": (60, 14, 26), "head": ["Exam-guide section", "Weight", "Items (of 50)"],
                           "rows": [
                               ["1 — Setting up a cloud solution environment", "~20%", "~10"],
                               ["2 — Planning and configuring a cloud solution", "~17.5%", "~9"],
                               ["3 — Deploying and implementing", "<b>~25%</b>", "<b>~12</b>"],
                               ["4 — Ensuring successful operation", "~20%", "~10"],
                               ["5 — Configuring access and security", "~17.5%", "~9"],
                           ]}),
                ("p", '<b>Deploying is the biggest single section</b>, and it is mostly "which command '
                      '/ which object / what happens next" — the cheapest marks on the paper. Coverage '
                      'here is proportional to these weightings.'),
                ("panel", {"kind": "note", "label": "ABOUT THE CUT SCORE",
                           "text": 'Google does not publish the passing mark. 70% is the working '
                                   'convention — plan to be <b>comfortably</b> above it.'}),
            ],
            [
                ("h", "The three-pass clock"),
                ("table", {"w": (16, 16, 68), "head": ["Pass", "Time", "What you do"],
                           "rows": [
                               ["1st", "70 min",
                                "Answer everything you know on sight. <b>Anything past 90 seconds gets a "
                                "guess and a flag</b> — never an empty box, and never a long think."],
                               ["2nd", "35 min",
                                "Work the flagged items. Arithmetic, multi-select and 'which of these two "
                                "products' belong here, where you have room to be slow."],
                               ["3rd", "15 min",
                                "Re-read only: every multi-select, and every item where you changed your "
                                "answer. Do not re-open settled items."],
                           ]}),
                ("panel", {"kind": "trap", "label": "THE TWO MECHANICAL LOSSES",
                           "text": '<b>Multi-select.</b> The stem says <i>Choose two</i>. Selecting one, or '
                                   'three, scores zero — there is no part credit. '
                                   '<b>Blank answers.</b> There is no negative marking, so a blank is a '
                                   'strictly worse guess. Sweep for blanks before you submit.'}),
            ]]}),
        ("h", "How to read a stem — the 30-second routine"),
        ("table", {"w": (6, 24, 70), "accent_color": None, "head": ["#", "Step", "What you are looking for"],
                   "rows": [
                       ["1", "Read the <b>last sentence first</b>",
                        "The requirement lives in the question, not the scenario. <i>Least privilege · "
                        "minimum operational overhead · lowest cost · without downtime · without storing "
                        "credentials</i> — one of these is almost always present, and it alone separates "
                        "two otherwise-correct options."],
                       ["2", "Name the <b>deciding constraint</b>",
                        "Write it in your head as one word before you look at the options. Looking at "
                        "options first is how a plausible-but-heavier answer wins."],
                       ["3", "Eliminate on <b>violations</b>, not on taste",
                        "Cross out anything that breaks a stated constraint (downloads a key, requires "
                        "downtime, needs a public IP, changes the resource in place). Usually two options "
                        "die instantly."],
                       ["4", "Between the last two, pick the <b>narrower, more managed</b> one",
                        "Fewer moving parts, narrower role, purpose-built product — worth more marks "
                        "than any single product fact."],
                   ]}),
        ("__contents__", None),
    ],
})


# ==========================================================================
# 2 — The eight reflexes
# ==========================================================================
PAGES.append({
    "id": "reflexes",
    "num": 2,
    "label": "The decision habits",
    "title": "Eight reflexes that answer the question for you",
    "accent": "purple",
    "blocks": [
        ("lede",
         'When two options both look defensible, one of these decides it. They are ordered by how '
         'often they matter on the ACE paper. <b>If you read only one page tonight, read this one.</b>'),
        ("table", {"w": (5, 27, 68), "head": ["", "Reflex", "How it plays out"],
                   "rows": [
                       ["<b>R1</b>", "<b>Prefer the managed primitive over the assembled equivalent</b>",
                        "The product built for this exact job beats infrastructure you wire together, and "
                        "beats the newer/bigger service that merely <i>can</i> do it. IAP TCP forwarding "
                        "over a bastion host; Managed Service for Prometheus over a self-run one; a plain "
                        "Pub/Sub push subscription over Eventarc; Cloud Run over a GKE cluster for one "
                        "stateless container."],
                       ["<b>R2</b>", "<b>Find the one deciding constraint before reading the options</b>",
                        "Scenarios are padded on purpose. Exactly one clause — <i>must scale to zero</i>, "
                        "<i>no downtime</i>, <i>data must stay in the EU</i>, <i>the key must never leave "
                        "our premises</i> — is load-bearing; the rest is scenery."],
                       ["<b>R3</b>", "<b>Least privilege = the narrowest <i>named</i> thing</b>",
                        "Narrowest <i>role</i> (predefined over basic; custom only if no predefined fits), "
                        "at the narrowest <i>node</i> (resource &lt; project &lt; folder &lt; org), to a "
                        "<i>group</i> rather than to users. It does <b>not</b> mean the most machinery — "
                        "a wall of conditions and deny policies is usually the wrong answer."],
                       ["<b>R4</b>", "<b>Access frequency picks a storage class; latency never does</b>",
                        "All four Cloud Storage classes have the same millisecond first-byte latency. "
                        "Nearline / Coldline / Archive differ in <i>price shape and minimum duration</i>, "
                        "not speed. 'Must be retrieved quickly' rules out nothing."],
                       ["<b>R5</b>", "<b>Immutable artefacts: change means create-new-then-roll</b>",
                        "Instance templates, container images and Cloud Run revisions cannot be edited. "
                        "The right answer creates a new version and rolls it out; an option that 'updates' "
                        "one in place is wrong by construction."],
                       ["<b>R6</b>", "<b>On recovery, lose the least — and keep the evidence</b>",
                        "Prefer the option that restores service with the smallest data loss <i>and</i> "
                        "preserves logs/snapshots for the post-mortem. Deleting or recreating the broken "
                        "thing first is the distractor."],
                       ["<b>R7</b>", "<b>Credentials: the answer never involves key material</b>",
                        "Inside Google Cloud → attach a service account, or impersonate one. On GKE → "
                        "Workload Identity Federation for GKE. Outside Google Cloud (AWS, Azure, GitHub, "
                        "on-prem with an IdP) → Workload Identity Federation. A downloaded JSON key is "
                        "the last resort and is almost never the exam's answer."],
                       ["<b>R8</b>", "<b>If you are given numbers, do the arithmetic</b>",
                        "Bandwidth × time, GB × price, vCPU-hours. A question that hands you figures is "
                        "testing whether you will compute rather than estimate — and the options are "
                        "spaced so estimating lands between two of them."],
                   ]}),
        ("h", "Distractor shapes you can cross out on sight"),
        ("table", {"w": (30, 70), "accent_color": None, "head": ["The option says…", "Why it is usually wrong"],
                   "rows": [
                       ["<b>Grant a basic role</b> (Owner/Editor/Viewer)",
                        "Any question containing the words <i>least privilege</i> has a predefined role as "
                        "its answer. Basic roles are there to be eliminated."],
                       ["<b>Download / distribute a service-account key</b>",
                        "R7. There is nearly always a keyless option in the same list."],
                       ["<b>Build a VM to do a managed service's job</b>",
                        "A bastion, a cron VM, a self-run Prometheus, a polling script. R1."],
                       ["<b>Edit an immutable object in place</b>",
                        "Instance templates, images and Cloud Run revisions cannot be modified. R5."],
                       ["<b>Give the resource a public IP</b> so you can reach it",
                        "IAP, Cloud NAT, Private Google Access and Private Service Connect exist precisely "
                        "so you do not."],
                       ["<b>Recreate / delete and redeploy</b> during an incident",
                        "It destroys the evidence and usually loses more data than the alternative. R6."],
                       ["<b>Do it manually in the console</b>, for something repeatable",
                        "If the stem says <i>repeatable</i>, <i>auditable</i> or <i>consistent across "
                        "environments</i>, the answer is IaC or a template."],
                   ]}),
        ("cols", {"ratio": (1, 1), "cols": [
            [("panel", {"kind": "tip", "label": "THE UNIVERSAL TIEBREAKER",
                        "text": 'Between two survivors, pick the one with <b>fewer things that can '
                                'break</b>: fewer components, fewer credentials, fewer manual steps, '
                                'less new infrastructure. Google writes ACE answers to reward the '
                                'operationally boring choice.'})],
            [("panel", {"kind": "trap", "label": "THE MIRROR-IMAGE TRAP",
                        "text": 'R1 cuts both ways. Reaching <i>past</i> a simple primitive for a '
                                'bigger managed service — Eventarc where a push subscription does, '
                                'Dataflow where a scheduled query does — is the same error wearing '
                                'the opposite coat.'})],
        ]}),
    ],
})


# ==========================================================================
# 3 — Hierarchy and the IAM model
# ==========================================================================
PAGES.append({
    "id": "hierarchy",
    "num": 3,
    "label": "The spine of the exam",
    "title": "Resource hierarchy, IAM evaluation, organisation policy",
    "accent": "blue",
    "blocks": [
        ("lede",
         'Almost every access question is answered by knowing <b>where a thing attaches</b> and '
         '<b>which direction it flows</b>. Get this page cold and Sections 1 and 5 — nearly 40% of '
         'the paper — become mechanical.'),
        ("cols", {"ratio": (47, 53), "cols": [
            [
                ("h", "The hierarchy"),
                ("code",
                 "Organisation        one per Cloud Identity /\n"
                 "  |                 Workspace domain; root of\n"
                 "  |                 IAM and org policy\n"
                 "  +-- Folder        optional, nestable (10 deep)\n"
                 "  |     |           a department or environment\n"
                 "  |     +-- Folder\n"
                 "  |     |     +-- Project\n"
                 "  |     |           |\n"
                 "  |     |           +-- Resource\n"
                 "  |     |            (VM, bucket, instance...)\n"
                 "  |     +-- Project\n"
                 "  +-- Project       may hang off the org direct"),
                ("panel", {"kind": "key", "label": "THE PROJECT IS THE BOUNDARY",
                           "text": 'Billing · quota · API enablement · default network · IAM '
                                   'isolation all stop at the project. <b>"So that one team cannot '
                                   'exhaust the other\'s quota" always means separate projects.</b>'}),
            ],
            [
                ("h", "Four rules examined constantly"),
                ("num", [
                    '<b>IAM is inherited downward and is additive.</b> A binding at the folder grants on '
                    'every project inside it — including projects created later. Effective policy is the '
                    '<b>union</b> of every level.',
                    '<b>A lower level cannot take a grant away.</b> There is no "more specific wins". The '
                    'only subtraction mechanisms are <b>IAM deny policies</b> and <b>org policy '
                    'constraints</b>.',
                    '<b>Pick the smallest node that satisfies the requirement <i>including its future</i>.</b> '
                    '"All of the department\'s projects, including new ones" = one folder binding, not forty '
                    'project bindings. Single most repeated D1 pattern.',
                    '<b>Grant to a group, not to a person.</b> Joiners and leavers are then a group '
                    'membership change, with no IAM edit at all — which is what "minimise administrative '
                    'overhead" means in an identity question.',
                ]),
            ]]}),
        ("h", "How a request is actually evaluated"),
        ("table", {"w": (20, 46, 34), "head": ["Layer", "What it does", "Beats"],
                   "rows": [
                       ["<b>Org policy</b> (constraints)",
                        "Restricts <i>what can be configured</i> on resources — no external IPs, allowed "
                        "regions, no SA key creation. Applies regardless of who you are, even Owner.",
                        "Everything. Checked against the configuration, not the caller."],
                       ["<b>IAM deny policy</b>",
                        "Explicitly denies named permissions to named principals. Evaluated <b>before</b> "
                        "allow policies.",
                        "Any allow binding, at any level."],
                       ["<b>IAM allow policy</b>",
                        "The familiar bindings: role + members (+ optional condition). Union of all levels "
                        "from org down to resource.",
                        "Nothing — it only ever grants."],
                   ]}),
        ("cols", {"ratio": (50, 50), "cols": [
            [
                ("h", "A binding, precisely"),
                ("p", 'An allow policy is a list of <b>bindings</b>, each one <b>role + members '
                      '(+ condition)</b>. Member prefixes the exam expects you to recognise:'),
                ("table", {"w": (44, 56), "head": ["Member", "Meaning"],
                           "rows": [
                               ["<font face='Courier'>user:</font>", "One human identity"],
                               ["<font face='Courier'>group:</font>", "A Google group — the preferred target"],
                               ["<font face='Courier'>serviceAccount:</font>", "A workload identity"],
                               ["<font face='Courier'>domain:</font>", "Everyone in a Workspace/Cloud Identity domain"],
                               ["<font face='Courier'>allAuthenticatedUsers</font>",
                                "Any Google account, anywhere — <b>not</b> your org"],
                               ["<font face='Courier'>allUsers</font>",
                                "<b>The public internet.</b> On a bucket this is how data leaks"],
                           ]}),
            ],
            [
                ("h", "Organisation policy — the other lever"),
                ("p", 'Constraints are <b>boolean</b> (on/off) or <b>list</b> (allow/deny values). Set at '
                      'org, folder or project; children inherit, and a child may <b>override</b> only if '
                      'the parent did not enforce <i>deny-with-no-override</i>. The ones to recognise:'),
                ("table", {"w": (56, 44), "head": ["Constraint", "Effect"],
                           "rows": [
                               ["<font face='Courier' size='6.4'>compute.vmExternalIpAccess</font>",
                                "No public IPs on VMs"],
                               ["<font face='Courier' size='6.4'>gcp.resourceLocations</font>",
                                "Data residency — restrict regions"],
                               ["<font face='Courier' size='6.4'>iam.disableServiceAccountKeyCreation</font>",
                                "Kills downloaded keys org-wide"],
                               ["<font face='Courier' size='6.4'>storage.publicAccessPrevention</font>",
                                "Blocks allUsers on buckets"],
                               ["<font face='Courier' size='6.4'>iam.allowedPolicyMemberDomains</font>",
                                "Domain-restricted sharing"],
                           ]}),
            ]]}),
        ("panel", {"kind": "watch", "label": "THREE THINGS THAT LOOK ALIKE",
                   "text": '<b>Deny policy</b> = this principal may not use this permission. '
                           '<b>Org policy</b> = nobody may configure the resource that way. '
                           '<b>IAM condition</b> = this grant applies only when (time / resource name / '
                           'request attribute) matches. When a question says <i>"prevent, even for '
                           'project owners"</i>, it is an <b>org policy</b>.'}),
    ],
})


# ==========================================================================
# 4 — Domain 1
# ==========================================================================


# ==========================================================================
# 5 — Domain 5
# ==========================================================================


# ==========================================================================
# 6 — Choosing compute
# ==========================================================================
PAGES.append({
    "id": "compute-choice",
    "num": 6,
    "label": "Section 2 · planning",
    "title": "Choosing compute, and what it costs",
    "accent": "green",
    "blocks": [
        ("lede",
         'Two questions decide it, in order: <b>what is the unit of deployment</b> (container, code, VM '
         'image, cluster) and <b>what must it do at idle</b> (scale to zero, or stay warm). Everything '
         'else on this page is a tiebreak.'),
        ("cols", {"ratio": (53, 47), "cols": [
            [
                ("h", "The chooser"),
                ("table", {"w": (24, 40, 36), "head": ["Product", "Choose when", "Gives up"],
                           "rows": [
                               ["<b>Cloud Run</b>",
                                "A stateless <b>container</b>, HTTP/event driven, bursty or spiky traffic, "
                                "<b>must scale to zero</b>. Default answer for 'containerised web service, "
                                "minimum ops'.",
                                "Long-lived state, direct node control"],
                               ["<b>Cloud Run functions</b><br/>(Cloud Functions)",
                                "A <b>single function</b> reacting to one event — an object landing, a "
                                "Pub/Sub message, an HTTP hook.",
                                "Anything multi-endpoint or long-running"],
                               ["<b>App Engine</b>",
                                "Existing web app, standard runtime, versions + traffic splitting wanted "
                                "out of the box. <b>Standard</b> scales to zero; <b>Flexible</b> runs VMs "
                                "and does not.",
                                "Flexibility; it is the legacy answer"],
                               ["<b>GKE</b>",
                                "Many containers with real orchestration needs: service mesh, DaemonSets, "
                                "StatefulSets, custom schedulers, portability.",
                                "Simplicity — you now own a cluster"],
                               ["<b>Compute Engine</b>",
                                "Lift-and-shift, licensed or legacy software, an OS-level dependency, GPUs "
                                "with specific drivers, or anything needing full machine control.",
                                "Managed scaling and patching"],
                           ]}),
                ("panel", {"kind": "tip", "label": "SCALE TO ZERO — THE SHORT LIST",
                           "text": '<b>Cloud Run · Cloud Run functions · App Engine <i>standard</i></b>. '
                                   'Not App Engine flexible, not GKE Standard node pools, not a MIG '
                                   '(minimum size ≥ 1 in practice). If the stem says <i>"costs nothing '
                                   'when idle"</i>, only the short list survives.'}),
            ],
            [
                ("h", "What things cost — and the four discounts"),
                ("table", {"w": (32, 68), "head": ["Discount", "How it works"],
                           "rows": [
                               ["<b>Sustained use</b>",
                                "Automatic on Compute Engine when an instance runs a large share of the "
                                "month. No commitment, no action."],
                               ["<b>Committed use</b>",
                                "You commit to 1 or 3 years of spend/resources for a large discount. "
                                "<b>The answer for steady, predictable baseline load.</b>"],
                               ["<b>Spot / preemptible VMs</b>",
                                "Up to ~60–91% off, but can be reclaimed at any time (preemptible also "
                                "caps at 24 h). <b>Only for fault-tolerant, restartable batch work.</b>"],
                               ["<b>Right-sizing</b>",
                                "Active Assist machine-type recommendations, based on observed utilisation."],
                           ]}),
                ("panel", {"kind": "key", "label": "COST ARITHMETIC — R8",
                           "text": 'If a question gives you numbers, compute rather than estimate. '
                                   'A VM billed per second that is genuinely needed <b>one hour a day</b> '
                                   'is ~4% utilisation — the answer is a schedule, a MIG that scales to a '
                                   'floor, or a serverless product, never "a smaller always-on VM".'}),
                ("h", "Machine families to recognise"),
                ("table", {"w": (22, 78), "head": ["Family", "For"],
                           "rows": [
                               ["<b>E2</b>", "Cheapest general purpose, day-to-day workloads"],
                               ["<b>N2 / N2D / N4</b>", "Balanced general purpose, more consistent performance"],
                               ["<b>C2 / C3</b>", "Compute-optimised — high per-core performance, gaming, HPC"],
                               ["<b>M1 / M2 / M3</b>", "Memory-optimised — SAP HANA, large in-memory databases"],
                               ["<b>A2 / A3 / G2</b>", "Accelerator-optimised — GPUs, ML training and inference"],
                           ]}),
            ]]}),
        ("h", "Global, regional, zonal — knowing the scope eliminates options"),
        ("table", {"w": (14, 43, 43), "head": ["Scope", "Resources", "What it means for the answer"],
                   "rows": [
                       ["<b>Global</b>",
                        "VPC network · firewall rules · routes · images · snapshots · global external "
                        "Application LB and its IP · Cloud DNS · IAM policy",
                        "Usable from anywhere; no region flag. A global LB with one anycast IP is the "
                        "answer to \"users worldwide, one address\"."],
                       ["<b>Regional</b>",
                        "Subnets · regional MIGs · regional persistent disks · Cloud Run services · "
                        "App Engine app · Cloud SQL instance · static regional IPs · Filestore",
                        "Survives a zone failure; costs cross-zone traffic. \"Survive a zone outage\" "
                        "almost always means \"choose the regional form\"."],
                       ["<b>Zonal</b>",
                        "VM instances · standard persistent disks · zonal MIGs · GKE zonal clusters · "
                        "local SSD",
                        "Dies with the zone. Any single-zone option loses a high-availability question by "
                        "construction."],
                   ]}),
        ("panel", {"kind": "watch", "label": "THE R1 TRAP, IN BOTH DIRECTIONS",
                   "text": 'Do not build a cluster for one container (too much), and do not reach for a '
                           'heavier managed product than the job needs (Eventarc where a Pub/Sub push '
                           'subscription does; Dataflow where a scheduled BigQuery query does). '
                           '<b>The right answer is the product built for exactly this job.</b>'}),
    ],
})


# ==========================================================================
# 7 — Compute Engine mechanics
# ==========================================================================
PAGES.append({
    "id": "gce",
    "num": 7,
    "label": "Section 3 · deploying",
    "title": "Compute Engine mechanics, images and instance groups",
    "accent": "blue",
    "blocks": [
        ("lede",
         'This page is <b>recall, not reasoning</b> — the exam asks what the platform actually does, and '
         'the options are written so that a plausible-sounding wrong behaviour is always on offer.'
         ''),
        ("cols", {"ratio": (50, 50), "cols": [
            [
                ("h", "What needs a stop, and what does not"),
                ("table", {"w": (56, 44), "head": ["Change", "Downtime?"],
                           "rows": [
                               ["<b>Change machine type (resize CPU/RAM)</b>",
                                "<b>Yes — stop the VM first.</b> Never live"],
                               ["Grow a persistent disk", "<b>No</b> — online; then grow the filesystem inside the guest"],
                               ["Shrink a persistent disk", "<b>Not possible.</b> Create a new smaller disk and copy"],
                               ["Attach / detach a non-boot disk", "No"],
                               ["Add or change network tags / labels", "No"],
                               ["Change the static internal IP", "Yes — the NIC must be reconfigured"],
                               ["Add a GPU to an existing VM", "Yes — stop first"],
                               ["Change the service account on a VM", "Yes — stop first"],
                           ]}),
                ("panel", {"kind": "trap", "label": "THE DISK PANEL DOES NOT MOVE DISKS",
                           "text": 'In the console, a VM\'s disk section offers <b>create and attach</b>. '
                                   'There is no "move this disk to another VM" action — you <b>detach</b> '
                                   'from one and <b>attach</b> to the other, and a boot disk can only be '
                                   'swapped while the VM is stopped.'}),
                ("h", "Lifecycle words that are not synonyms"),
                ("bul", [
                    '<b>Stop / terminate</b> — compute stops, <b>you stop paying for the vCPU and RAM</b>, '
                    'you keep paying for disks and any reserved static IP. The VM and its disks survive.',
                    '<b>Suspend</b> — RAM is saved to storage, resumes faster, still billed for that storage.',
                    '<b>Reset</b> — a hard power cycle. Memory is lost; the disk is untouched.',
                    '<b>Delete</b> — the boot disk goes too <i>unless</i> "keep boot disk" was set.',
                ]),
            ],
            [
                ("h", "Snapshots, images, machine images — the three-way"),
                ("table", {"w": (25, 75), "head": ["Artefact", "What it is for"],
                           "rows": [
                               ["<b>Snapshot</b>",
                                "Incremental, <b>differential</b> backup of <b>one disk</b>. Backup and "
                                "restore, and cross-region disk copies. Schedule them for routine backup."],
                               ["<b>Custom image</b>",
                                "A bootable, reusable template of <b>one boot disk</b>. What you build with "
                                "Packer and feed to an instance template for a golden image."],
                               ["<b>Machine image</b>",
                                "<b>The whole VM</b> — all disks, machine type, metadata, network config. "
                                "The answer for cloning or moving an entire multi-disk VM."],
                               ["<b>Instance template</b>",
                                "The configuration a MIG stamps instances from. <b>Immutable</b> — to "
                                "change it you create a new one."],
                           ]}),
                ("h", "Managed instance groups"),
                ("bul", [
                    '<b>MIG = instance template + size + policies.</b> It gives you autoscaling, '
                    'autohealing (a health check recreates unhealthy VMs), rolling updates and regional '
                    'spread.',
                    '<b>Regional MIG</b> spreads instances across zones in a region — the standard answer '
                    'to "survive a zone failure".',
                    '<b>Autohealing needs a health check.</b> Without one, a hung application keeps '
                    'serving; with one, the VM is recreated.',
                    '<b>Rolling update</b>: new template → <font face="Courier" size="6.4">maxSurge</font> / '
                    '<font face="Courier" size="6.4">maxUnavailable</font> control the pace. A '
                    '<b>canary</b> is the same update targeted at a subset of instances.',
                    'Autoscale on CPU, on load-balancer serving capacity, or on a Cloud Monitoring metric. '
                    'Set a <b>cool-down</b> long enough for a new instance to actually start serving.',
                ]),
                ("panel", {"kind": "key", "label": "R5 — IMMUTABILITY",
                           "text": 'Templates and images cannot be edited. Any option that "modifies the '
                                   'existing instance template" is wrong. The pattern is always '
                                   '<b>create new → set on the group → roll out</b>.'}),
            ]]}),
        ("h", "Metadata, startup scripts and SSH"),
        ("cols", {"ratio": (1, 1), "cols": [
            [("bul", [
                '<b>Startup scripts</b> are instance (or project) metadata — '
                '<font face="Courier" size="6.4">startup-script</font> — and run as root on every boot. '
                'The standard answer to "configure the VM at launch without baking an image".',
                'The <b>metadata server</b> at '
                '<font face="Courier" size="6.4">169.254.169.254</font> serves instance metadata and '
                '<b>short-lived access tokens</b> for the attached service account. This is why an '
                'attached SA needs no key file.',
                'Metadata can be set per <b>project</b> (applies to all VMs) or per <b>instance</b>.',
             ])],
            [("bul", [
                '<b>OS Login</b> ties SSH access to IAM — '
                '<font face="Courier" size="6.4">roles/compute.osLogin</font> or '
                '<font face="Courier" size="6.4">osAdminLogin</font> — instead of scattering keys in '
                'metadata. Enable it with metadata '
                '<font face="Courier" size="6.4">enable-oslogin=TRUE</font>; it is the manageable, '
                'auditable answer for a fleet.',
                '<font face="Courier" size="6.4">gcloud compute ssh</font> generates and pushes a key for '
                'you. If it fails on a VM with no external IP, the answer is '
                '<font face="Courier" size="6.4">--tunnel-through-iap</font>, not a public address.',
             ])],
        ]}),
        ("panel", {"kind": "watch", "label": "IP ADDRESSING — THE ONE-LINE RULES",
                   "text": '<b>RFC 1918 ranges (10.x, 172.16–31.x, 192.168.x) are private and can never be '
                           'an external IP.</b> · An <b>ephemeral</b> IP changes when the VM stops; a '
                           '<b>static</b> one survives and is billed when reserved but unattached. · '
                           'Internal IPs can be static too — that is the answer to "the address must not '
                           'change across restarts" for internal traffic. · A VM with <b>no external IP</b> '
                           'reaches Google APIs via <b>Private Google Access</b> and the internet via '
                           '<b>Cloud NAT</b>.'}),
    ],
})


# ==========================================================================
# 8 — GKE
# ==========================================================================
PAGES.append({
    "id": "gke",
    "num": 8,
    "label": "Section 3 · deploying",
    "title": "Google Kubernetes Engine",
    "accent": "blue",
    "blocks": [
        ("cols", {"ratio": (48, 52), "cols": [
            [
                ("h", "Cluster shapes"),
                ("table", {"w": (30, 70), "head": ["Mode / type", "What it means"],
                           "rows": [
                               ["<b>Autopilot</b>",
                                "Google runs the nodes. You are billed per <b>pod</b> resource request, not "
                                "per node. Default answer for 'minimum cluster operations'."],
                               ["<b>Standard</b>",
                                "You own node pools, machine types and upgrades. Needed for DaemonSets, "
                                "node-level tuning, GPUs with special drivers."],
                               ["<b>Zonal</b>", "Single control plane in one zone — cheaper, no control-plane HA"],
                               ["<b>Regional</b>",
                                "Control plane replicated across zones; nodes spread across zones. The "
                                "answer for production HA."],
                               ["<b>Private cluster</b>",
                                "Nodes have no public IPs. Combine with authorised networks to restrict who "
                                "may reach the control plane."],
                           ]}),
                ("h", "Workload objects"),
                ("table", {"w": (30, 70), "head": ["Object", "Use"],
                           "rows": [
                               ["<b>Deployment</b>", "Stateless replicas, rolling updates. The default"],
                               ["<b>StatefulSet</b>", "Stable network identity and per-pod storage — databases"],
                               ["<b>DaemonSet</b>", "One pod on <b>every node</b> — log/metric agents"],
                               ["<b>Job / CronJob</b>", "Run to completion / on a schedule"],
                               ["<b>ConfigMap / Secret</b>", "Non-secret and secret configuration, mounted or injected"],
                               ["<b>HPA</b>", "Scales <b>pods</b> on CPU/memory/custom metrics"],
                               ["<b>Cluster autoscaler</b>", "Scales <b>nodes</b> when pods cannot be scheduled"],
                           ]}),
            ],
            [
                ("h", "Exposing a workload — pick by the requirement"),
                ("table", {"w": (30, 70), "head": ["Service type", "Reachable from"],
                           "rows": [
                               ["<b>ClusterIP</b>", "Inside the cluster only. The default"],
                               ["<b>NodePort</b>", "A port on every node — a building block, rarely the answer alone"],
                               ["<b>LoadBalancer</b>",
                                "A cloud load balancer for <b>one</b> service. L4 by default; internal with "
                                "an annotation"],
                               ["<b>Ingress / Gateway</b>",
                                "<b>HTTP(S) routing for many services behind one IP</b> — host and path "
                                "rules, TLS termination. The answer whenever several services must share "
                                "one address"],
                           ]}),
                ("panel", {"kind": "key", "label": "WORKLOAD IDENTITY — THE GKE CREDENTIALS ANSWER",
                           "text": 'Bind the <b>Kubernetes</b> service account to a <b>Google</b> service '
                                   'account, annotate the KSA, and the pod gets short-lived tokens from the '
                                   'metadata server. Grant '
                                   '<font face="Courier" size="6.4">roles/iam.workloadIdentityUser</font> on '
                                   'the GSA to the KSA principal. <b>Never a JSON key in a Kubernetes '
                                   'secret</b> — that is the distractor.'}),
                ("h", "Operational facts worth having"),
                ("bul", [
                    '<font face="Courier" size="6.4">gcloud container clusters get-credentials</font> is what '
                    'writes your kubeconfig. Without it, <font face="Courier" size="6.4">kubectl</font> has '
                    'no cluster — a very common "why does this fail" item.',
                    '<b>Node pools</b> let one cluster mix machine types. Changing a node pool\'s machine '
                    'type means <b>creating a new pool and migrating (cordon + drain)</b>, not editing it.',
                    '<b>Node auto-upgrade</b> keeps nodes near the control-plane version; <b>release '
                    'channels</b> (Rapid / Regular / Stable) choose how fast that happens.',
                    '<b>PodDisruptionBudget</b> is how you keep a minimum number of pods available during '
                    'voluntary disruptions such as an upgrade or a drain.',
                    'Images come from <b>Artifact Registry</b>; the cluster\'s node service account needs '
                    'read access to the repository (<font face="Courier" size="6.4">artifactregistry.reader</font>).',
                ]),
            ]]}),
        ("h", "Pod states, and what each one actually means"),
        ("table", {"w": (18, 38, 44), "head": ["Symptom", "Cause", "The fix the exam wants"],
                   "rows": [
                       ["<b>Pending</b>", "No node has room for the pod's resource requests",
                        "Cluster autoscaler, a bigger machine type, or smaller requests — <b>never the "
                        "HPA</b>"],
                       ["<b>ImagePullBackOff</b>", "Wrong image name, or no permission on the repository",
                        "Fix the tag, or grant "
                        "<font face='Courier' size='6.4'>roles/artifactregistry.reader</font> to the node "
                        "service account"],
                       ["<b>CrashLoopBackOff</b>", "The container starts and exits repeatedly",
                        "<font face='Courier' size='6.4'>kubectl logs POD --previous</font> — an "
                        "application problem, not a cluster one"],
                       ["<b>403 calling a Google API</b>", "The workload has no usable identity",
                        "Workload Identity: annotate the KSA, grant "
                        "<font face='Courier' size='6.4'>workloadIdentityUser</font> — not a mounted key"],
                       ["<b>kubectl cannot connect</b>", "No kubeconfig, or a private control plane",
                        "<font face='Courier' size='6.4'>get-credentials</font>, and check the authorised "
                        "networks"],
                   ]}),
        ("panel", {"kind": "watch", "label": "HPA vs CLUSTER AUTOSCALER vs MIG AUTOSCALER",
                   "text": 'HPA adds <b>pods</b>. Cluster autoscaler adds <b>nodes</b>, and only because '
                           'pods are pending. A MIG autoscaler adds <b>VMs</b> and knows nothing about '
                           'Kubernetes. A question about "pods stuck in Pending" is the cluster autoscaler '
                           'or a resource-request problem — never the HPA.'}),
    ],
})


# ==========================================================================
# 9 — Serverless and the build chain
# ==========================================================================
PAGES.append({
    "id": "serverless",
    "num": 9,
    "label": "Section 3 · deploying",
    "title": "Cloud Run, functions, App Engine — and the build chain",
    "accent": "blue",
    "blocks": [
        ("cols", {"ratio": (50, 50), "cols": [
            [
                ("h", "Cloud Run"),
                ("bul", [
                    'Deploys a <b>container image</b> (from Artifact Registry) or builds from source for '
                    'you. Each deploy creates an <b>immutable revision</b>.',
                    '<b>Traffic is split across revisions by percentage</b> — that is how you do canary and '
                    'blue/green, and <b>rollback is pointing 100% at the previous revision</b>. There is no '
                    '"edit the running revision".',
                    'Scales <b>to zero</b> by default. <font face="Courier" size="6.4">--min-instances</font> '
                    'keeps instances warm (kills cold starts, costs money at idle); '
                    '<font face="Courier" size="6.4">--max-instances</font> caps blast radius and spend.',
                    'Concurrency is <b>requests per container</b> (default 80) — unlike functions, one '
                    'instance serves many requests at once.',
                    'Auth: <font face="Courier" size="6.4">--allow-unauthenticated</font> for public; '
                    'otherwise callers need <font face="Courier" size="6.4">roles/run.invoker</font> — that '
                    'is the mechanism for service-to-service calls.',
                    'Runs as a <b>service account</b> you attach. Give it a narrow one rather than the '
                    'default.',
                ]),
                ("h", "Cloud Run functions (Cloud Functions)"),
                ("bul", [
                    'One function, one trigger: <b>HTTP</b>, <b>Pub/Sub</b>, <b>Cloud Storage</b> object '
                    'events, Firestore, or anything via <b>Eventarc</b>.',
                    'The classic exam shape: <i>an object lands in a bucket → process it</i>. The answer is '
                    'a storage-triggered function, not a VM polling the bucket.',
                    'Stateless and time-bounded; long or multi-step work belongs in Cloud Run, a Job, or '
                    'Workflows.',
                ]),
                ("panel", {"kind": "watch", "label": "APP ENGINE: STANDARD vs FLEXIBLE",
                           "text": '<b>Standard</b> — sandboxed runtimes, very fast scaling, <b>scales to '
                                   'zero</b>. <b>Flexible</b> — your container on managed VMs, custom '
                                   'runtimes and background processes, <b>does not scale to zero</b>, '
                                   'slower to deploy. Both give you <b>versions with traffic splitting</b>, '
                                   'and one app per project.'}),
            ],
            [
                ("h", "The build chain"),
                ("table", {"w": (30, 70), "head": ["Product", "Job"],
                           "rows": [
                               ["<b>Cloud Source Repositories</b>", "Hosted git. Usually the repo is on GitHub instead"],
                               ["<b>Cloud Build</b>",
                                "CI/CD. Steps in <font face='Courier' size='6.4'>cloudbuild.yaml</font>, "
                                "triggered on push/tag/PR. Runs as a service account you can narrow"],
                               ["<b>Artifact Registry</b>",
                                "<b>The current registry</b> for container images <i>and</i> language "
                                "packages (Maven, npm, Python), regional, with IAM per repository. "
                                "Container Registry is the deprecated predecessor"],
                               ["<b>Cloud Deploy</b>", "Progressive delivery pipelines into Run/GKE"],
                               ["<b>Binary Authorization</b>", "Only signed/attested images may be deployed"],
                           ]}),
                ("panel", {"kind": "key", "label": "DOCKER AUTH, THE ONE COMMAND",
                           "text": 'Pushing locally to Artifact Registry fails until you run '
                                   '<font face="Courier" size="6.4">gcloud auth configure-docker '
                                   'REGION-docker.pkg.dev</font>. Image names are '
                                   '<font face="Courier" size="6.4">REGION-docker.pkg.dev/PROJECT/REPO/IMAGE:TAG</font>.'}),
                ("h", "Infrastructure as code"),
                ("table", {"w": (30, 70), "head": ["Tool", "Status"],
                           "rows": [
                               ["<b>Terraform</b>",
                                "<b>The answer</b> for declarative, repeatable, reviewable infrastructure. "
                                "Config Controller / Infrastructure Manager run it for you"],
                               ["<b>Deployment Manager</b>", "Google's legacy IaC — deprecated; do not pick it"],
                               ["<b>Helm</b>",
                                "Packaging and templating <b>Kubernetes manifests</b>. When the question is "
                                "about repeatable <i>app</i> deployment into a cluster, this is the layer — "
                                "not Terraform"],
                               ["<b>gcloud scripts</b>", "Imperative. Fine for one-offs, wrong for 'repeatable and auditable'"],
                           ]}),
                ("h", "Serverless networking, in three lines"),
                ("bul", [
                    '<b>Ingress settings</b> decide who may call the service: all traffic · internal only · '
                    'internal and Cloud Load Balancing. The answer to "reachable only from inside the VPC".',
                    '<b>Direct VPC egress</b> (or a Serverless VPC Access connector) is how a Cloud Run '
                    'service or function reaches <b>private</b> resources — a Cloud SQL private IP, a '
                    'Memorystore instance, an internal endpoint.',
                    'Without one of those, a serverless workload has no route into your VPC at all — which '
                    'is the hidden failure in several "why can it not connect" items.',
                ]),
                ("panel", {"kind": "trap", "label": "PICK THE RIGHT LAYER",
                           "text": 'Terraform provisions the <b>cluster</b>; Helm/manifests deploy the '
                                   '<b>workload into</b> it. An option that uses one to do the other\'s job '
                                   'is the distractor.'}),
            ]]}),
    ],
})


# ==========================================================================
# 10 — Storage
# ==========================================================================
PAGES.append({
    "id": "storage",
    "num": 10,
    "label": "Section 2 · planning",
    "title": "Cloud Storage, disks, file storage and transfer",
    "accent": "amber",
    "blocks": [
        ("h", "Cloud Storage: the four classes"),
        ("table", {"w": (16, 20, 22, 22, 20),
                   "head": ["Class", "Access pattern", "Minimum duration", "Cost shape", "Latency"],
                   "rows": [
                       ["<b>Standard</b>", "Frequent, or short-lived", "none", "Highest storage, lowest access",
                        "milliseconds"],
                       ["<b>Nearline</b>", "≈ once a month", "<b>30 days</b>", "Cheaper storage, retrieval fee",
                        "milliseconds"],
                       ["<b>Coldline</b>", "≈ once a quarter", "<b>90 days</b>", "Cheaper still, higher retrieval",
                        "milliseconds"],
                       ["<b>Archive</b>", "≈ once a year, or never", "<b>365 days</b>", "Cheapest storage, highest retrieval",
                        "milliseconds"],
                   ]}),
        ("panel", {"kind": "trap", "label": "R4 — LATENCY NEVER CHOOSES A CLASS",
                   "text": 'All four serve the first byte in milliseconds. There is no thaw, no restore '
                           'job, no waiting. <b>"Must be available immediately" eliminates nothing.</b> '
                           'What eliminates a class is the <b>minimum storage duration</b>: delete or '
                           'overwrite an Archive object after a week and you still pay for 365 days. '
                           'Frequency of access, not speed of access, is the discriminator.'}),
        ("cols", {"ratio": (50, 50), "cols": [
            [
                ("h", "Buckets, objects, lifecycle"),
                ("bul", [
                    'Bucket names are <b>globally unique</b>; location is <b>region</b>, <b>dual-region</b> '
                    'or <b>multi-region</b> and is <b>fixed at creation</b>.',
                    '<b>Objects are immutable.</b> "Editing" an object means overwriting it with a new '
                    'version — which is why versioning matters.',
                    '<b>Object versioning</b> keeps noncurrent versions, so delete becomes recoverable. It '
                    'also means you now pay for the old versions.',
                    '<b>Lifecycle rules</b> act on age, creation date, number of newer versions, and '
                    '<font face="Courier" size="6.4">isLive</font>. Actions: <b>SetStorageClass</b> '
                    '(transition down the tiers) and <b>Delete</b>.',
                    '<font face="Courier" size="6.4">isLive:false</font> targets <b>noncurrent</b> versions '
                    '— the idiom for "keep old versions cheaply for N days, then remove them".',
                    '<b>Retention policy</b> forbids deletion for a period; <b>bucket lock</b> makes that '
                    'policy permanent — the compliance/WORM answer.',
                    '<b>Signed URL</b> = time-limited access for someone with <b>no Google identity</b>. '
                    'Making the bucket public is the wrong answer to that stem.',
                ]),
            ],
            [
                ("h", "Block and file storage"),
                ("table", {"w": (30, 70), "head": ["Option", "Choose when"],
                           "rows": [
                               ["<b>Balanced PD</b>", "The sensible default boot/data disk"],
                               ["<b>SSD PD</b>", "Higher IOPS — databases"],
                               ["<b>Standard PD</b>", "Cheap, throughput-oriented, cold data"],
                               ["<b>Hyperdisk</b>", "Independently tunable IOPS/throughput, highest performance"],
                               ["<b>Local SSD</b>",
                                "<b>Ephemeral</b>, physically attached, fastest. <b>Data is lost when the VM "
                                "stops.</b> Scratch and caches only"],
                               ["<b>Filestore</b>",
                                "Managed <b>NFS</b> — many VMs need a shared POSIX filesystem"],
                           ]}),
                ("h", "Getting data in"),
                ("table", {"w": (32, 68), "head": ["Service", "For"],
                           "rows": [
                               ["<b>Storage Transfer Service</b>",
                                "Online transfers from S3, Azure, another bucket or an on-prem agent — "
                                "scheduled and repeatable"],
                               ["<b>Transfer Appliance</b>",
                                "Physical shipped box — petabyte scale, or a link too slow to finish in time"],
                               ["<b>gcloud storage / gsutil -m</b>", "Ad-hoc, scripted copies"],
                               ["<b>BigQuery Data Transfer</b>", "Scheduled loads from SaaS sources into BigQuery"],
                           ]}),
                ("panel", {"kind": "key", "label": "R8 — THE TRANSFER SUM",
                           "text": 'Do the arithmetic before choosing. <b>TB ÷ (Mbps ÷ 8)</b> gives seconds. '
                                   'A 100 TB dataset over 1 Gbps is ~9 days at 100% utilisation — if the '
                                   'deadline is shorter, it is <b>Transfer Appliance</b>, whatever the '
                                   'other options claim.'}),
            ]]}),
    ],
})


# ==========================================================================
# 11 — Databases and analytics
# ==========================================================================


# ==========================================================================
# 12 — VPC
# ==========================================================================
PAGES.append({
    "id": "vpc",
    "num": 12,
    "label": "Section 2 and 3 · networking",
    "title": "VPC, subnets, firewalls and private access",
    "accent": "purple",
    "blocks": [
        ("cols", {"ratio": (50, 50), "cols": [
            [
                ("h", "The model"),
                ("bul", [
                    'A <b>VPC is global</b>; a <b>subnet is regional</b> and owns an IP range. A VM in any '
                    'zone of that region can sit in that subnet.',
                    '<b>Auto mode</b> creates a subnet in every region with fixed ranges; <b>custom mode</b> '
                    'is what production uses — you choose regions and CIDRs. Auto → custom is one-way.',
                    'Subnet ranges can be <b>expanded</b>, never shrunk, and must not overlap within the '
                    'VPC — or with any network you peer with.',
                    '<b>Routes</b> send traffic; the <b>default route</b> to 0.0.0.0/0 via the internet '
                    'gateway is what makes external IPs work. Deleting it is how you force all egress '
                    'through an appliance.',
                    '<b>Alias IP ranges</b> give a VM (or GKE pods) additional internal addresses from a '
                    'secondary range.',
                ]),
                ("h", "Firewall rules"),
                ("table", {"w": (30, 70), "head": ["Property", "Behaviour"],
                           "rows": [
                               ["Defaults",
                                "<b>Ingress denied, egress allowed.</b> Two implied rules you cannot delete"],
                               ["Evaluation",
                                "Lowest <b>priority number wins</b> (0–65535, default 1000). A deny at 900 "
                                "beats an allow at 1000"],
                               ["Targets",
                                "All instances, a <b>network tag</b>, or a <b>service account</b>. Service "
                                "account targeting is the more secure answer — tags can be set by anyone "
                                "who can edit the VM"],
                               ["Sources",
                                "IP ranges, tags, or service accounts. <b>Stateful</b> — a reply to an "
                                "allowed connection is allowed"],
                               ["Scope", "Rules live on the <b>VPC</b>, not on the subnet"],
                           ]}),
            ],
            [
                ("h", "Reaching things privately"),
                ("table", {"w": (32, 68), "head": ["Mechanism", "What it solves"],
                           "rows": [
                               ["<b>Private Google Access</b>",
                                "A VM <b>with no external IP</b> reaches Google APIs and services. A "
                                "per-subnet switch, and free"],
                               ["<b>Cloud NAT</b>",
                                "Those same VMs reach <b>the internet</b> outbound, still with no external "
                                "IP and with no inbound exposure"],
                               ["<b>Private Service Connect</b>",
                                "A private endpoint inside your VPC for Google or third-party services"],
                               ["<b>Private Service Access</b>",
                                "Peered range for managed services such as Cloud SQL private IP"],
                               ["<b>IAP TCP forwarding</b>",
                                "<b>SSH/RDP to a VM with no external IP, with no bastion host.</b> "
                                "Authorised by IAM, audited, and the traffic arrives from "
                                "<font face='Courier' size='6.4'>35.235.240.0/20</font> — allow that range "
                                "in the firewall"],
                           ]}),
                ("panel", {"kind": "trap", "label": "R1 — THE BASTION IS THE DISTRACTOR",
                           "text": 'When a stem asks for administrative access to private VMs with minimum '
                                   'operational overhead, <b>IAP TCP forwarding</b> beats building and '
                                   'patching a bastion every time. The two '
                                   'things to remember with it: grant '
                                   '<font face="Courier" size="6.4">roles/iap.tunnelResourceAccessor</font>, '
                                   'and open <font face="Courier" size="6.4">35.235.240.0/20</font>.'}),
                ("panel", {"kind": "watch", "label": "PGA vs NAT",
                           "text": '<b>Private Google Access → Google APIs.</b> <b>Cloud NAT → the '
                                   'internet.</b> A VM that must <font face="Courier" size="6.4">apt '
                                   'install</font> from a public mirror needs NAT; one that only writes to '
                                   'Cloud Storage needs PGA.'}),
            ]]}),
        ("h", "IP addresses — the table that settles a whole family of items"),
        ("table", {"w": (20, 26, 26, 28),
                   "head": ["Address", "Range", "Survives a stop?", "Billing and use"],
                   "rows": [
                       ["<b>Ephemeral internal</b>", "RFC 1918, from the subnet", "No — reassigned",
                        "Free. The default for a VM"],
                       ["<b>Static internal</b>", "RFC 1918, reserved from the subnet", "<b>Yes</b>",
                        "Free. The answer to \"the internal address must not change\""],
                       ["<b>Ephemeral external</b>", "Public, from Google's pool", "No",
                        "Charged while in use"],
                       ["<b>Static external</b>", "Public, reserved", "<b>Yes</b>",
                        "<b>Charged even when reserved and unattached</b> — the classic \"why are we "
                        "paying for this\" item"],
                   ]}),
        ("panel", {"kind": "trap", "label": "PRIVATE MEANS PRIVATE",
                   "text": 'A 10.x / 172.16–31.x / 192.168.x address is <b>RFC 1918 private and can never '
                           'be an external IP</b>, in any configuration, on any product. An option that '
                           'assigns one as a public address is wrong on sight — it needs no further '
                           'analysis.'}),
        ("panel", {"kind": "key", "label": "TAGS ARE NOT LABELS",
                   "text": '<b>Network tags</b> attach to VMs and are the target/source of firewall rules '
                           'and routes. <b>Labels</b> are key:value metadata for billing, filtering and '
                           'organisation, and have no network effect whatsoever. Questions mix the two words '
                           'deliberately.'}),
    ],
})


# ==========================================================================
# 13 — Connectivity and load balancing
# ==========================================================================
PAGES.append({
    "id": "connect",
    "num": 13,
    "label": "Section 2 and 3 · networking",
    "title": "Connecting networks, and balancing load",
    "accent": "purple",
    "blocks": [
        ("h", "Joining networks — pick by who owns what"),
        ("table", {"w": (20, 44, 36), "head": ["Mechanism", "What it is", "The stem that selects it"],
                   "rows": [
                       ["<b>Shared VPC</b>",
                        "One <b>host project</b> owns the network; <b>service projects</b> attach and run "
                        "resources in it. Central network team, decentralised app teams.",
                        "\"Central control of the network while teams keep their own projects\""],
                       ["<b>VPC Network Peering</b>",
                        "Two VPCs exchange internal traffic. <b>Non-transitive</b> (A–B and B–C does not "
                        "give A–C) and ranges must not overlap.",
                        "\"Two networks, possibly different orgs, must talk privately\""],
                       ["<b>Cloud VPN (HA VPN)</b>",
                        "IPsec over the public internet. Quick, cheap, bandwidth limited per tunnel.",
                        "\"Connect on-prem soon / modest bandwidth / encrypted over internet\""],
                       ["<b>Dedicated Interconnect</b>",
                        "A physical circuit into a Google colocation facility, 10/100 Gbps.",
                        "\"High, consistent bandwidth, private, not over the internet\""],
                       ["<b>Partner Interconnect</b>",
                        "Interconnect via a service provider, smaller increments.",
                        "\"Private connectivity but we are not in a colocation facility\""],
                   ]}),
        ("cols", {"ratio": (54, 46), "cols": [
            [
                ("h", "The load-balancer chooser"),
                ("table", {"w": (26, 30, 44),
                           "head": ["Traffic", "Reach", "Use"],
                           "rows": [
                               ["<b>HTTP(S)</b>", "External, global",
                                "<b>Global external Application LB</b> — one anycast IP worldwide, URL/path "
                                "routing, TLS termination, Cloud CDN and Cloud Armor attach here"],
                               ["<b>HTTP(S)</b>", "Internal",
                                "Internal Application LB — microservices inside the VPC"],
                               ["<b>TCP/UDP/other</b>", "External",
                                "External <b>proxy</b> Network LB (terminates) or <b>passthrough</b> "
                                "(preserves client IP)"],
                               ["<b>TCP/UDP</b>", "Internal",
                                "Internal passthrough Network LB — the internal L4 front door"],
                           ]}),
                ("panel", {"kind": "key", "label": "THE TWO DECIDING WORDS",
                           "text": '<b>Layer</b> — is the stem about URLs, paths, host headers or '
                                   'certificates (L7 Application LB), or about ports and protocols (L4 '
                                   'Network LB)? <b>Reach</b> — is the client on the internet (external) or '
                                   'inside the VPC (internal)? Those two answers pick the product with no '
                                   'further thought.'}),
                ("bul", [
                    '<b>Backend service + health check + backend (MIG or NEG)</b> is the shape of every '
                    'load balancer. An unhealthy backend takes no traffic — a missing or wrong health check '
                    'is the usual "why is it 502" item.',
                    '<b>Managed SSL certificates</b> are provisioned and renewed by Google, attached to the '
                    'HTTPS proxy. DNS must point at the LB IP first, or provisioning never completes.',
                ]),
            ],
            [
                ("h", "Edge services"),
                ("table", {"w": (30, 70), "head": ["Service", "Job"],
                           "rows": [
                               ["<b>Cloud DNS</b>",
                                "Managed authoritative DNS, 100% SLA. <b>Public</b> zones serve the "
                                "internet; <b>private</b> zones resolve only inside named VPCs"],
                               ["<b>Cloud CDN</b>",
                                "Caches at the edge — enabled on a <b>backend service of the global "
                                "external Application LB</b>, not standalone"],
                               ["<b>Cloud Armor</b>",
                                "WAF and DDoS protection with IP/geo/rule-based policies, attached to the "
                                "same LB backend services. The answer to 'block this traffic before it "
                                "reaches my app'"],
                               ["<b>Network Intelligence Center</b>",
                                "Connectivity Tests — the diagnostic answer to 'why can this VM not reach "
                                "that one'"],
                           ]}),
                ("h", "Hybrid connectivity mechanics"),
                ("bul", [
                    '<b>Cloud Router</b> is what makes hybrid links dynamic: it exchanges routes with your '
                    'on-prem router over <b>BGP</b>, so new subnets on either side are learned '
                    'automatically instead of being configured by hand.',
                    '<b>HA VPN</b> gives two interfaces and a 99.99% SLA when configured with two tunnels; '
                    'Classic VPN is the older single-interface form.',
                    '<b>Dedicated Interconnect</b> is 10 or 100 Gbps circuits into a colocation facility; '
                    '<b>Partner Interconnect</b> comes in smaller increments through a provider. Both are '
                    'private — traffic never touches the public internet.',
                    'Redundancy is the usual exam angle: a single tunnel or a single circuit is a single '
                    'point of failure, so the higher-SLA answer pairs them across zones or edge '
                    'availability domains.',
                    '<b>Network Connectivity Center</b> joins many spokes — VPCs, VPNs, Interconnects — '
                    'into a hub, which is the modern answer to the non-transitivity of peering.',
                ]),
                ("panel", {"kind": "watch", "label": "PEERING IS NOT TRANSITIVE",
                           "text": 'If A peers with B and B peers with C, <b>A cannot reach C</b>. Options '
                                   'that assume otherwise are wrong. The fix is a full mesh, a Shared VPC, '
                                   'or Network Connectivity Center.'}),
                ("panel", {"kind": "tip", "label": "CHEAP ELIMINATION",
                           "text": 'Anything "global with a single anycast IP" is the <b>global external '
                                   'Application LB</b>. Anything needing the original <b>client IP</b> '
                                   'preserved is a <b>passthrough</b> Network LB. Anything about '
                                   'certificates is L7.'}),
            ]]}),
    ],
})


# ==========================================================================
# 14 — Operations
# ==========================================================================


# ==========================================================================
# 15 — The final card
# ==========================================================================
PAGES.append({
    "id": "final",
    "num": 15,
    "label": "Read this last",
    "title": "Thirty facts that decide questions, and the last five minutes",
    "accent": "ink",
    "blocks": [
        ("lede",
         'Everything here is a single sentence that has settled an item for someone. Read it in the car '
         'park. If one of them does not land, go back to the page it came from — <b>do not start '
         'learning something new tonight.</b>'),
        ("cols", {"ratio": (1, 1), "gutter": 10, "cols": [
            [
                ("h", "Identity and access"),
                ("bul", [
                    'IAM is <b>additive and inherited</b>; nothing below can take a grant away.',
                    'Only <b>deny policies</b> and <b>org policy</b> subtract. Org policy binds even Owners.',
                    'Grant to <b>groups</b>, at the <b>smallest node that includes the future</b>.',
                    '<font face="Courier" size="6.4">allUsers</font> = the public internet. '
                    '<font face="Courier" size="6.4">allAuthenticatedUsers</font> = any Google account, not your org.',
                    '<b>serviceAccountUser</b> attaches an SA; <b>serviceAccountTokenCreator</b> impersonates one.',
                    'Keyless first: attach an SA · impersonate · Workload Identity (GKE) · federation (outside). '
                    'A downloaded key is the last resort.',
                    'CMEK = your key in Cloud KMS. CSEK = your key never in Google Cloud. EKM = your external HSM.',
                    'Destroying a KMS key version is <b>scheduled (24 h)</b>, not instant.',
                ]),
                ("h", "Compute"),
                ("bul", [
                    'Resizing a machine type <b>requires a stop</b>. Growing a disk does not.',
                    'Disks grow, never shrink. Local SSD data dies with the VM.',
                    'Instance templates and images are <b>immutable</b> — create new, then roll.',
                    'Regional MIG + health check = survives a zone failure and self-heals.',
                    'Scale to zero: <b>Cloud Run, Cloud Run functions, App Engine standard</b>. Nothing else.',
                    'Spot/preemptible only for restartable work; committed use for steady baseline.',
                    'Snapshot = one disk · Custom image = one boot disk · Machine image = the whole VM.',
                ]),
                ("h", "Cloud Storage"),
                ("bul", [
                    'All storage classes are millisecond-latency; <b>frequency and minimum duration</b> decide.',
                    'Nearline 30 · Coldline 90 · Archive 365 days minimum, billed even if deleted early.',
                    '<font face="Courier" size="6.4">isLive:false</font> lifecycle rules target noncurrent versions.',
                    'Signed URL = access for someone with no Google identity. Never make the bucket public.',
                    'Cloud SQL <b>read replica ≠ HA</b>. HA is a regional instance with automatic failover.',
                    'Relational <b>and</b> global <b>and</b> horizontally scalable = <b>Spanner</b>, always.',
                    'Bigtable hotspotting is a sequential row-key prefix; fix with field promotion or salting.',
                    'BigQuery cost: name your columns, partition by date, cluster on filters.',
                ]),
            ],
            [
                ("h", "Networking"),
                ("bul", [
                    'VPC is global, subnet is regional; firewall rules live on the VPC.',
                    'Default firewall: <b>ingress denied, egress allowed</b>; lowest priority number wins.',
                    'Target rules at <b>service accounts</b> rather than tags when the stem says "secure".',
                    'RFC 1918 addresses can <b>never</b> be external IPs.',
                    'Private Google Access → Google APIs. Cloud NAT → the internet. Neither gives inbound access.',
                    '<b>IAP TCP forwarding</b> replaces the bastion; allow '
                    '<font face="Courier" size="6.4">35.235.240.0/20</font>.',
                    'VPC peering is <b>not transitive</b> and ranges must not overlap.',
                    'One global anycast IP with URL routing = global external Application LB.',
                ]),
                ("h", "Operations"),
                ("bul", [
                    'Exception → Error Reporting · latency → Trace · CPU/memory → Profiler · idle → Active Assist.',
                    '<b>Memory and disk-space metrics need the Ops Agent.</b> CPU and network do not.',
                    'An alerting policy without a <b>notification channel</b> tells nobody.',
                    'Admin Activity audit logs are always on; <b>Data Access logs are off by default</b>.',
                    '<font face="Courier" size="6.4">_Required</font> keeps audit logs 400 days and cannot be changed.',
                    'SQL over existing logs with no pipeline = <b>Log Analytics</b>, not a BigQuery sink.',
                    'Budgets <b>alert</b>; only Pub/Sub plus a function can <b>act</b>.',
                ]),
                ("h", "The last five minutes"),
                ("num", [
                    'Sweep for <b>blank answers</b>. There is no penalty — a guess strictly beats a blank.',
                    'Re-check every <b>multi-select</b>: exactly as many boxes as the stem asked for.',
                    'On anything still open, apply the tiebreaker: <b>narrower role, fewer moving parts, '
                    'the purpose-built managed product</b>.',
                    'Do not re-open items you answered confidently on the first pass. Second-guessing a '
                    'recognised answer is how a pass becomes a near miss.',
                ]),
                ("panel", {"kind": "tip", "label": "ONE LAST THING",
                           "text": 'You scored 35/50 — <b>exactly</b> at the working cut — with seven misses '
                                   'answered in under 25 seconds and an hour left on the clock. You do not '
                                   'need more knowledge to clear this. <b>You need to spend the time you '
                                   'already have.</b> Page 1 and this page are what turn '
                                   'it into marks.'}),
            ]]}),
    ],
})


# ==========================================================================
# Appendix — gcloud reference (outside the theory page budget)
# ==========================================================================
PAGES.append({
    "id": "appx-a",
    "part": "appendix",
    "label": "Appendix A · command reference",
    "title": "Config, projects, IAM and service accounts",
    "accent": "ink",
    "blocks": [
        ("lede",
         '<b>The grammar is the point.</b> Every command is '
         '<font face="Courier"><b>gcloud</b> GROUP [SUBGROUP] COMMAND NAME --flags</font>, and the exam '
         'frequently tests whether you know the <i>group</i> rather than the exact flag: '
         '<font face="Courier">compute instances</font>, <font face="Courier">container clusters</font>, '
         '<font face="Courier">projects</font>, <font face="Courier">iam service-accounts</font>. '
         'If you can place the noun, you can usually eliminate three options.'),
        ("cols", {"ratio": (1, 1), "gutter": 10, "cols": [
            [
                ("h", "Config, auth and context"),
                ("cmds", {"rows": [
                    ("gcloud init", "Interactive first-time setup"),
                    ("gcloud auth login", "Authenticate a human"),
                    ("gcloud auth application-default login", "Credentials for local SDKs/Terraform"),
                    ("gcloud auth activate-service-account\n  --key-file=key.json", "Authenticate as an SA from a key"),
                    ("gcloud auth list", "Which identities are available"),
                    ("gcloud config list", "Current config"),
                    ("gcloud config set project PROJECT_ID", "Set the default project"),
                    ("gcloud config set compute/zone ZONE", "Set the default zone"),
                    ("gcloud config configurations create NAME", "A named profile"),
                    ("gcloud config configurations activate NAME", "Switch profiles"),
                    ("gcloud components update", "Update the SDK (not in Cloud Shell)"),
                    ("gcloud --impersonate-service-account=SA", "<b>Run any command as an SA — keyless</b>"),
                    ("gcloud info / gcloud version", "Diagnose the installation"),
                ]}),
                ("h", "Projects, billing, APIs, quotas"),
                ("cmds", {"rows": [
                    ("gcloud projects create ID\n  --folder=FOLDER_ID", "Create inside a folder"),
                    ("gcloud projects list", "List visible projects"),
                    ("gcloud projects describe ID", "Project number, state, labels"),
                    ("gcloud resource-manager folders create\n  --display-name=X --organization=ORG", "Create a folder"),
                    ("gcloud billing accounts list", "Billing accounts you can see"),
                    ("gcloud billing projects link ID\n  --billing-account=ACCOUNT", "Attach a project to billing"),
                    ("gcloud services list --available", "APIs that can be enabled"),
                    ("gcloud services enable compute.googleapis.com", "<b>Enable an API — per project</b>"),
                    ("gcloud organizations list", "Find the org ID"),
                ]}),
            ],
            [
                ("h", "IAM"),
                ("cmds", {"rows": [
                    ("gcloud projects add-iam-policy-binding ID\n  --member=user:a@b.com --role=roles/viewer",
                     "<b>The binding command — memorise this shape</b>"),
                    ("gcloud projects remove-iam-policy-binding ...", "Revoke one binding"),
                    ("gcloud projects get-iam-policy ID\n  --format=json", "Read the whole policy"),
                    ("gcloud resource-manager folders\n  add-iam-policy-binding FOLDER_ID ...", "Grant at the folder — inherited down"),
                    ("gcloud organizations add-iam-policy-binding ...", "Grant at the org"),
                    ("gcloud iam roles create NAME --project=ID\n  --permissions=a.b.c,d.e.f", "Create a custom role"),
                    ("gcloud iam roles describe roles/NAME", "What a predefined role contains"),
                    ("gcloud iam list-testable-permissions RESOURCE", "Permissions valid on a resource"),
                ]}),
                ("h", "Service accounts and secrets"),
                ("cmds", {"rows": [
                    ("gcloud iam service-accounts create NAME\n  --display-name=\"X\"", "Create an SA"),
                    ("gcloud iam service-accounts list", "List SAs in the project"),
                    ("gcloud iam service-accounts\n  add-iam-policy-binding SA_EMAIL\n  --member=user:a@b.com\n  --role=roles/iam.serviceAccountTokenCreator",
                     "<b>Let someone impersonate it</b>"),
                    ("gcloud iam service-accounts keys create k.json\n  --iam-account=SA_EMAIL",
                     "Create a key — <b>last resort</b>"),
                    ("gcloud iam service-accounts keys list\n  --iam-account=SA_EMAIL", "Audit existing keys"),
                    ("gcloud iam workload-identity-pools create ...", "Federation from an external IdP"),
                    ("gcloud secrets create NAME\n  --replication-policy=automatic", "Create a secret"),
                    ("gcloud secrets versions add NAME\n  --data-file=-", "Add a version (rotation)"),
                    ("gcloud secrets versions access latest\n  --secret=NAME", "Read the payload"),
                    ("gcloud kms keyrings create / keys create", "Key ring, then key — location is fixed"),
                ]}),
            ]]}),
    ],
})


PAGES.append({
    "id": "appx-b",
    "part": "appendix",
    "label": "Appendix B · command reference",
    "title": "Compute Engine and networking",
    "accent": "ink",
    "blocks": [
        ("cols", {"ratio": (1, 1), "gutter": 10, "cols": [
            [
                ("h", "Instances"),
                ("cmds", {"rows": [
                    ("gcloud compute instances create NAME\n  --machine-type=e2-medium --zone=ZONE", "Create a VM"),
                    ("  --service-account=SA --scopes=cloud-platform", "Attach an identity at create time"),
                    ("  --no-address", "<b>No external IP</b> — pair with NAT/PGA"),
                    ("  --metadata-from-file startup-script=s.sh", "Startup script"),
                    ("  --tags=web,prod", "Network tags for firewall rules"),
                    ("  --preemptible / --provisioning-model=SPOT", "Cheap, interruptible"),
                    ("gcloud compute instances list", "All VMs in the project"),
                    ("gcloud compute instances stop NAME", "Stop — required before a resize"),
                    ("gcloud compute instances set-machine-type NAME\n  --machine-type=e2-standard-4",
                     "<b>Resize — only while stopped</b>"),
                    ("gcloud compute instances add-tags NAME --tags=x", "Add a network tag"),
                    ("gcloud compute ssh NAME --zone=ZONE", "SSH, managing keys for you"),
                    ("gcloud compute ssh NAME --tunnel-through-iap", "<b>SSH to a VM with no external IP</b>"),
                    ("gcloud compute reset / suspend / resume NAME", "Power actions"),
                ]}),
                ("h", "Disks, snapshots, images"),
                ("cmds", {"rows": [
                    ("gcloud compute disks create NAME --size=100GB\n  --type=pd-balanced", "Create a disk"),
                    ("gcloud compute disks resize NAME --size=200GB", "Grow online — then grow the filesystem"),
                    ("gcloud compute instances attach-disk VM\n  --disk=DISK", "Attach"),
                    ("gcloud compute instances detach-disk VM\n  --disk=DISK", "Detach — the 'move' is these two"),
                    ("gcloud compute disks snapshot NAME\n  --snapshot-names=SNAP", "Take a snapshot"),
                    ("gcloud compute images create IMG\n  --source-disk=DISK", "Custom image from a boot disk"),
                    ("gcloud compute machine-images create MI\n  --source-instance=VM", "<b>The whole VM</b>"),
                    ("gcloud compute resource-policies create\n  snapshot-schedule ...", "Scheduled backups"),
                ]}),
            ],
            [
                ("h", "Templates and managed instance groups"),
                ("cmds", {"rows": [
                    ("gcloud compute instance-templates create T\n  --machine-type=e2-medium --image-family=...",
                     "<b>Immutable</b> — new version, never an edit"),
                    ("gcloud compute instance-groups managed create G\n  --template=T --size=3 --region=REGION",
                     "<b>Regional</b> MIG = multi-zone"),
                    ("gcloud compute instance-groups managed\n  set-autoscaling G --max-num-replicas=10\n  --target-cpu-utilization=0.6", "Autoscale"),
                    ("gcloud compute instance-groups managed\n  rolling-action start-update G\n  --version=template=T2", "Rolling update to a new template"),
                    ("gcloud compute instance-groups managed\n  set-named-ports G --named-ports=http:8080", "Named port for the load balancer"),
                    ("gcloud compute health-checks create http HC\n  --port=80", "Required for autohealing and LBs"),
                ]}),
                ("h", "Networking"),
                ("cmds", {"rows": [
                    ("gcloud compute networks create VPC\n  --subnet-mode=custom", "Custom-mode VPC"),
                    ("gcloud compute networks subnets create SUB\n  --network=VPC --range=10.0.0.0/24\n  --region=REGION", "Subnet"),
                    ("  --enable-private-ip-google-access", "<b>Private Google Access</b>"),
                    ("gcloud compute networks subnets expand-ip-range", "Grow a range — never shrink"),
                    ("gcloud compute firewall-rules create R\n  --allow=tcp:22 --source-ranges=35.235.240.0/20\n  --target-tags=web", "<b>The IAP SSH rule</b>"),
                    ("  --priority=900 --action=DENY", "Lower number wins"),
                    ("gcloud compute addresses create IP\n  --region=REGION", "Reserve a static IP"),
                    ("gcloud compute routers create R --network=VPC\ngcloud compute routers nats create NAT ...", "Cloud NAT, in two steps"),
                    ("gcloud compute networks peerings create P\n  --network=A --peer-network=B", "Peering — non-transitive"),
                    ("gcloud compute shared-vpc enable HOST_PROJECT", "Shared VPC host"),
                    ("gcloud compute backend-services / url-maps /\n  target-http-proxies / forwarding-rules", "The load-balancer chain, in order"),
                    ("gcloud dns managed-zones create Z --dns-name=...", "Cloud DNS zone"),
                ]}),
            ]]}),
    ],
})


PAGES.append({
    "id": "appx-c",
    "part": "appendix",
    "label": "Appendix C · command reference",
    "title": "GKE, serverless, storage and data",
    "accent": "ink",
    "blocks": [
        ("cols", {"ratio": (1, 1), "gutter": 10, "cols": [
            [
                ("h", "GKE and kubectl"),
                ("cmds", {"rows": [
                    ("gcloud container clusters create-auto NAME\n  --region=REGION", "Autopilot cluster"),
                    ("gcloud container clusters create NAME\n  --num-nodes=3 --zone=ZONE", "Standard cluster"),
                    ("  --workload-pool=PROJECT.svc.id.goog", "<b>Enable Workload Identity</b>"),
                    ("gcloud container clusters get-credentials NAME\n  --region=REGION",
                     "<b>Writes kubeconfig — kubectl fails without it</b>"),
                    ("gcloud container node-pools create POOL\n  --cluster=NAME --machine-type=...", "New pool (you cannot edit a type)"),
                    ("gcloud container clusters resize NAME\n  --num-nodes=5", "Resize a pool"),
                    ("kubectl apply -f manifest.yaml", "Declarative — the preferred form"),
                    ("kubectl create deployment web --image=IMG", "Imperative create"),
                    ("kubectl expose deployment web --type=LoadBalancer\n  --port=80", "Service in front of it"),
                    ("kubectl scale deployment web --replicas=5", "Manual scale"),
                    ("kubectl autoscale deployment web --min=2 --max=10\n  --cpu-percent=70", "HPA — scales pods"),
                    ("kubectl set image deployment/web c=IMG:v2", "Rolling update"),
                    ("kubectl rollout status / undo deployment/web", "Watch, then roll back"),
                    ("kubectl get pods -o wide / describe pod P /\n  logs P -c CONTAINER", "The debugging trio"),
                    ("kubectl drain NODE --ignore-daemonsets", "Evict before node maintenance"),
                ]}),
                ("h", "Databases and messaging"),
                ("cmds", {"rows": [
                    ("gcloud sql instances create I --tier=db-n1-standard-1\n  --availability-type=REGIONAL", "<b>REGIONAL = HA</b>"),
                    ("gcloud sql instances create R --master-instance-name=I", "Read replica (not HA)"),
                    ("gcloud sql backups create --instance=I", "On-demand backup"),
                    ("bq mk --dataset PROJECT:DS", "Create a dataset"),
                    ("bq query --use_legacy_sql=false 'SELECT ...'", "Run a query"),
                    ("bq load --source_format=CSV DS.T gs://B/f.csv", "Load data"),
                    ("gcloud pubsub topics create T\ngcloud pubsub subscriptions create S --topic=T", "Topic, then subscription"),
                    ("  --push-endpoint=https://...", "Push instead of pull"),
                ]}),
            ],
            [
                ("h", "Serverless and build"),
                ("cmds", {"rows": [
                    ("gcloud run deploy SVC --image=IMG --region=R", "Deploy a revision"),
                    ("  --allow-unauthenticated", "Public; otherwise grant run.invoker"),
                    ("  --min-instances=1 --max-instances=10", "Warm floor / spend ceiling"),
                    ("gcloud run services update-traffic SVC\n  --to-revisions=REV=10", "<b>Canary by percentage</b>"),
                    ("  --to-latest / --to-revisions=PREV=100", "Promote / <b>roll back</b>"),
                    ("gcloud functions deploy FN --trigger-topic=T\n  --runtime=python312", "Pub/Sub-triggered function"),
                    ("  --trigger-bucket=B / --trigger-http", "Object event / HTTP"),
                    ("gcloud app deploy / browse / versions list", "App Engine"),
                    ("gcloud app services set-traffic S\n  --splits=v2=0.1,v1=0.9", "Traffic splitting"),
                    ("gcloud builds submit --tag REGION-docker.pkg.dev/...", "Build and push"),
                    ("gcloud artifacts repositories create R\n  --repository-format=docker --location=REGION", "Create a repo"),
                    ("gcloud auth configure-docker REGION-docker.pkg.dev", "<b>Needed before a local push</b>"),
                ]}),
                ("h", "Storage and data"),
                ("cmds", {"rows": [
                    ("gcloud storage buckets create gs://B\n  --location=REGION --uniform-bucket-level-access", "Create a bucket"),
                    ("gcloud storage cp -r LOCAL gs://B/path", "Copy in"),
                    ("gcloud storage rsync -r SRC gs://B", "Sync a tree"),
                    ("gcloud storage buckets update gs://B\n  --lifecycle-file=rules.json", "Apply lifecycle rules"),
                    ("gcloud storage buckets update gs://B\n  --versioning", "Turn on object versioning"),
                    ("gcloud storage objects update gs://B/o\n  --storage-class=NEARLINE", "Change one object's class"),
                    ("gcloud storage sign-url gs://B/o --duration=1h", "<b>Signed URL</b>"),
                    ("gcloud storage buckets add-iam-policy-binding\n  gs://B --member=... --role=roles/storage.objectViewer", "Bucket IAM"),
                ]}),
            ]]}),
    ],
})


PAGES.append({
    "id": "appx-d",
    "part": "appendix",
    "label": "Appendix D · command reference",
    "title": "Operations, flag patterns, and lookalike commands",
    "accent": "ink",
    "blocks": [
        ("cols", {"ratio": (50, 50), "cols": [
            [
                ("h", "Flags that appear on almost every command"),
                ("cmds", {"rows": [
                    ("--project=ID", "Override the configured project"),
                    ("--zone=ZONE / --region=REGION", "Zonal vs regional resources — a common trap"),
                    ("--format=json|yaml|table|value", "Machine-readable output"),
                    ("--format='value(name)'", "Just one field — for shell loops"),
                    ("--filter='labels.env=prod AND status=RUNNING'", "Server-side filtering"),
                    ("--quiet", "Accept prompts — required in scripts"),
                    ("--dry-run / --validate-only", "Check without applying (where supported)"),
                    ("--impersonate-service-account=SA", "Keyless elevation on any command"),
                    ("--async", "Return immediately; poll the operation"),
                    ("--help", "The group's own list of subcommands"),
                ]}),
                ("panel", {"kind": "tip", "label": "READING AN OPTION FAST",
                           "text": 'If two options differ only by <b>zonal vs regional</b>, or by '
                                   '<b>create vs update</b>, the stem almost always contains the word that '
                                   'picks one — "survive a zone outage", "without recreating". Find that '
                                   'word before comparing flags.'}),
                ("h", "Operations"),
                ("cmds", {"rows": [
                    ("gcloud logging read 'resource.type=gce_instance\n  severity>=ERROR' --limit=20 --freshness=1h",
                     "<b>Read logs with a filter</b>"),
                    ("gcloud logging sinks create S DESTINATION\n  --log-filter='...'", "Route logs onward"),
                    ("gcloud logging sinks create S ... \n  --include-children --folder=F", "<b>Aggregated sink</b>"),
                    ("gcloud logging metrics create M --log-filter='...'", "Log-based metric to alert on"),
                    ("gcloud monitoring dashboards create\n  --config-from-file=d.json", "Dashboards as code"),
                    ("gcloud alpha monitoring policies create\n  --policy-from-file=p.yaml", "Alerting policy"),
                    ("gcloud recommender recommendations list\n  --recommender=google.compute.instance.IdleResourceRecommender\n  --location=ZONE",
                     "<b>Active Assist — idle resources</b>"),
                ]}),
            ],
            [
                ("h", "Three-step chains worth remembering"),
                ("cmds", {"rows": [
                    ("networks create → subnets create →\nfirewall-rules create", "Build a VPC"),
                    ("routers create → routers nats create", "Cloud NAT"),
                    ("instance-templates create →\ninstance-groups managed create →\nset-autoscaling", "A scalable tier"),
                    ("health-checks create → backend-services create →\nurl-maps create → target-http-proxies create →\nforwarding-rules create",
                     "An external HTTP(S) load balancer, in order"),
                    ("keyrings create → keys create →\nadd-iam-policy-binding", "CMEK for a service"),
                ]}),
                ("h", "Pairs the exam deliberately confuses"),
                ("table", {"w": (50, 50), "head": ["This", "Not this"],
                           "rows": [
                               ["<font face='Courier' size='6.4'>gcloud compute instances\nset-machine-type</font> (stopped VM)",
                                "Any option implying a live resize"],
                               ["<font face='Courier' size='6.4'>detach-disk</font> then "
                                "<font face='Courier' size='6.4'>attach-disk</font>",
                                "A non-existent \"move disk\" action"],
                               ["<font face='Courier' size='6.4'>instance-templates create</font> (a new one)",
                                "\"Update the existing template\" — it is immutable"],
                               ["<font face='Courier' size='6.4'>clusters get-credentials</font>",
                                "Assuming kubectl already knows the cluster"],
                               ["<font face='Courier' size='6.4'>run services update-traffic</font>",
                                "\"Edit the running revision\""],
                               ["<font face='Courier' size='6.4'>add-iam-policy-binding</font>",
                                "<font face='Courier' size='6.4'>set-iam-policy</font>, which <b>replaces "
                                "the whole policy</b>"],
                               ["<font face='Courier' size='6.4'>gcloud storage</font>",
                                "<font face='Courier' size='6.4'>gsutil</font> — still works, but it is the "
                                "older surface"],
                               ["<font face='Courier' size='6.4'>--tunnel-through-iap</font>",
                                "Adding an external IP so you can SSH"],
                           ]}),
                ("panel", {"kind": "trap", "label": "set-iam-policy IS DESTRUCTIVE",
                           "text": '<font face="Courier" size="6.4">set-iam-policy</font> overwrites every '
                                   'existing binding with the file you hand it. The additive, safe, '
                                   'exam-correct verb for granting one role is '
                                   '<font face="Courier" size="6.4">add-iam-policy-binding</font>.'}),
                ("h", "If you have five minutes left tonight"),
                ("p", 'Type these three and read the output — they anchor the three shapes you will be '
                      'asked about most:'),
                ("code",
                 "gcloud projects get-iam-policy $PROJECT \\\n"
                 "    --format=json\n\n"
                 "gcloud compute instances list \\\n"
                 "    --format='table(name,zone,status,\n"
                 "              networkInterfaces[0].networkIP)'\n\n"
                 "gcloud logging read 'severity>=ERROR' \\\n"
                 "    --limit=5 --freshness=24h"),
                ("panel", {"kind": "note", "label": "AND THEN STOP",
                           "text": 'Sleep is worth more than the last hour of revision. You have the '
                                   'knowledge for this paper — <b>page 1 and the final card</b> are what '
                                   'turn it into marks.'}),
            ]]}),
    ],
})


# ==========================================================================
# Section 1 — identity
# ==========================================================================
PAGES.append({
    "id": "d1-identity",
    "label": "Section 1 · setting up",
    "title": "Identity, organisations, projects and folders",
    "accent": "teal",
    "blocks": [
        ("lede",
         'Section 1 is about <b>getting an account into a usable, governed shape</b>: where identities come '
         'from, how the hierarchy is laid out, and what each node is for. It is also where the most '
         'mechanical marks on the paper live — the answers are definitions, not judgement calls.'),
        ("cols", {"ratio": (50, 50), "cols": [
            [
                ("h", "Where identities come from"),
                ("table", {"w": (30, 70), "head": ["Thing", "What it is"],
                           "rows": [
                               ["<b>Cloud Identity</b>",
                                "Free identity provider for Google Cloud — accounts and groups, no "
                                "Gmail/Docs. What you create when the company has no Workspace. A domain of "
                                "either kind is <b>required before an organisation can exist</b>."],
                               ["<b>Google Workspace</b>",
                                "The same identity layer plus the productivity apps. Either one can be the "
                                "org's identity source."],
                               ["<b>Google Cloud Directory Sync</b>",
                                "One-way sync <b>from on-prem LDAP/Active Directory into</b> Cloud "
                                "Identity. Never the other way, and it syncs identities — not passwords."],
                               ["<b>SSO / SAML federation</b>",
                                "Sign-in is redirected to your existing IdP (AD FS, Okta, Ping). The "
                                "identity still exists in Cloud Identity; the <i>credential</i> lives at "
                                "the IdP. The standard answer to \"users must keep using corporate "
                                "credentials\"."],
                               ["<b>Consumer Gmail accounts</b>",
                                "Work, but are outside your control — you cannot suspend them. Migrating "
                                "them into the domain is the governance answer."],
                           ]}),
                ("panel", {"kind": "watch", "label": "SUPER ADMIN IS NOT AN IAM ROLE",
                           "text": '<b>Super admin</b> is a Cloud Identity / Workspace account role. It '
                                   'creates the organisation and assigns the first '
                                   '<b>Organization Administrator</b> — which <i>is</i> an IAM role. After '
                                   'that, day-to-day Google Cloud work is done with IAM roles, not with the '
                                   'super admin account.'}),
                ("h", "Groups"),
                ("bul", [
                    '<b>Grant roles to groups, never to individuals.</b> Joiners and leavers then become a '
                    'membership change with no IAM edit at all — which is exactly what "minimise '
                    'administrative overhead" means in an access question.',
                    'Groups can nest. A role on a parent group reaches every member of every child group.',
                    'A group is a <b>member</b> in a binding: '
                    '<font face="Courier" size="6.4">group:devs@example.com</font>.',
                ]),
            ],
            [
                ("h", "The nodes, and what each is for"),
                ("table", {"w": (22, 78), "head": ["Node", "What it is the boundary of"],
                           "rows": [
                               ["<b>Organisation</b>",
                                "The root. One per Cloud Identity/Workspace domain. Owns org policy and the "
                                "top of every IAM chain. Cannot be deleted while it has children."],
                               ["<b>Folder</b>",
                                "Optional grouping — a department, a subsidiary, an environment. Nestable "
                                "(up to 10 deep). <b>The answer whenever a grant must cover projects that "
                                "do not exist yet.</b>"],
                               ["<b>Project</b>",
                                "<b>Billing · quota · API enablement · default network · resource "
                                "isolation.</b> Almost every resource lives in exactly one project, and "
                                "moving between projects is rarely a simple operation."],
                               ["<b>Resource</b>",
                                "The leaf — a VM, a bucket, a Cloud SQL instance. Some support IAM "
                                "bindings of their own, which is where least privilege bottoms out."],
                           ]}),
                ("h", "Project lifecycle facts that get asked"),
                ("bul", [
                    'Creating a project needs <b>'
                    '<font face="Courier" size="6.4">roles/resourcemanager.projectCreator</font></b>, '
                    'granted at the org or a folder — not at a project.',
                    'A deleted project sits in a <b>pending-deletion state for ~30 days</b> and can be '
                    'restored. After that it is gone, and the ID is never reusable.',
                    'A project can be <b>moved</b> between folders — its IAM inheritance changes with it, '
                    'which is a quiet way to grant or remove a lot of access at once.',
                    '<b>Liens</b> prevent accidental project deletion — the answer to "make sure nobody '
                    'deletes the production project".',
                    'Resources are <b>labelled</b> (key:value) for billing and filtering. Labels are '
                    'inherited by nothing — they are set per resource.',
                ]),
                ("h", "Setting up a new organisation, in order"),
                ("num", [
                    'Verify a <b>domain</b> and create <b>Cloud Identity</b> or Workspace — the '
                    'organisation appears automatically once a domain exists.',
                    'The <b>super admin</b> grants <b>Organization Administrator</b> to a small group, '
                    'then stops being used day to day.',
                    'Create the <b>folder</b> structure — environments or departments — before projects, '
                    'because moving projects later is how inheritance surprises happen.',
                    'Link a <b>billing account</b> and set <b>budgets</b>.',
                    'Set <b>organisation policies</b> (locations, external IPs, key creation) while the '
                    'estate is small enough to fix.',
                    'Grant roles <b>to groups at folders</b>, and only then start creating projects.',
                ]),
                ("panel", {"kind": "key", "label": "THE THREE IDENTIFIERS",
                           "text": '<b>Project ID</b> — globally unique, chosen at creation, '
                                   '<b>immutable</b>, what <font face="Courier" size="6.4">gcloud</font> '
                                   'wants. <b>Project name</b> — display only, mutable, not unique. '
                                   '<b>Project number</b> — auto-assigned, immutable, appears inside '
                                   'default service-account addresses. gcloud accepts the ID or the number, '
                                   'never the display name.'}),
            ]]}),
    ],
})


# ==========================================================================
# Section 1 — roles
# ==========================================================================
PAGES.append({
    "id": "d1-roles",
    "label": "Section 1 · setting up",
    "title": "Roles: the three kinds, and the ones worth knowing by name",
    "accent": "teal",
    "blocks": [
        ("cols", {"ratio": (46, 54), "cols": [
            [
                ("h", "The three kinds"),
                ("table", {"w": (26, 74), "head": ["Kind", "When it is the answer"],
                           "rows": [
                               ["<b>Basic</b><br/>Owner · Editor · Viewer",
                                "Legacy, project-wide, enormously broad. <b>Almost always the wrong answer "
                                "in a least-privilege question.</b> Owner additionally manages billing "
                                "links and can grant roles to others."],
                               ["<b>Predefined</b><br/><font face='Courier' size='6.4'>roles/service.role</font>",
                                "<b>The default right answer.</b> Maintained by Google, scoped to one "
                                "product and one job, and updated automatically as the product gains "
                                "permissions."],
                               ["<b>Custom</b>",
                                "Only when <b>no predefined role fits</b>. Defined at org or project level, "
                                "maintained by you — new API permissions do <b>not</b> appear in it "
                                "automatically. Cannot be defined at folder level."],
                           ]}),
                ("panel", {"kind": "key", "label": "THE LEAST-PRIVILEGE LADDER",
                           "text": 'Work down it in order and stop at the first rung that satisfies the '
                                   'requirement: <b>a predefined role</b> → <b>at the narrowest node</b> '
                                   '(resource, then project, then folder, then org) → <b>granted to a '
                                   'group</b> → <b>with an IAM condition</b> if the access must be '
                                   'time-bound or resource-bound → and only then a custom role.'}),
                ("h", "Permissions, and how to find the right role"),
                ("bul", [
                    'A permission is <font face="Courier" size="6.4">service.resource.verb</font> — '
                    '<font face="Courier" size="6.4">compute.instances.start</font>, '
                    '<font face="Courier" size="6.4">storage.objects.get</font>. Roles are bundles of them.',
                    'Some permissions are only grantable <b>above</b> the resource — creating projects, '
                    'setting org policy, managing folders.',
                    '<b>Policy Troubleshooter</b> answers "why can this person do this / not do this". '
                    '<b>Policy Simulator</b> answers "what breaks if I remove this binding" — the safe way '
                    'to tighten access.',
                    '<b>Role recommendations</b> (Active Assist) propose narrower roles from 90 days of '
                    'observed usage — the mechanical answer to "reduce over-provisioned access".',
                ]),
            ],
            [
                ("h", "Roles the exam expects you to recognise"),
                ("table", {"w": (46, 54), "head": ["Role", "Grants"],
                           "rows": [
                               ["<font face='Courier' size='6.4'>roles/browser</font>",
                                "See the hierarchy — nothing inside it"],
                               ["<font face='Courier' size='6.4'>roles/resourcemanager.projectCreator</font>",
                                "Create projects (granted at org or folder)"],
                               ["<font face='Courier' size='6.4'>roles/resourcemanager.projectIamAdmin</font>",
                                "Manage IAM on a project without other power"],
                               ["<font face='Courier' size='6.4'>roles/billing.admin</font>",
                                "Manage a billing account and its budgets"],
                               ["<font face='Courier' size='6.4'>roles/billing.user</font>",
                                "<b>Attach</b> projects to a billing account"],
                               ["<font face='Courier' size='6.4'>roles/billing.viewer</font>",
                                "See spend — the finance-analyst answer"],
                               ["<font face='Courier' size='6.4'>roles/iam.serviceAccountUser</font>",
                                "<b>Attach</b> an SA to a resource (deploy as it)"],
                               ["<font face='Courier' size='6.4'>roles/iam.serviceAccountTokenCreator</font>",
                                "<b>Impersonate</b> an SA — short-lived tokens"],
                               ["<font face='Courier' size='6.4'>roles/iam.securityAdmin</font>",
                                "Set IAM policy on resources"],
                               ["<font face='Courier' size='6.4'>roles/compute.instanceAdmin.v1</font>",
                                "Full control of VMs and disks"],
                               ["<font face='Courier' size='6.4'>roles/compute.viewer</font>",
                                "Read compute resources, no changes"],
                               ["<font face='Courier' size='6.4'>roles/compute.osLogin</font> / "
                                "<font face='Courier' size='6.4'>osAdminLogin</font>",
                                "SSH to VMs as a normal / sudo user"],
                               ["<font face='Courier' size='6.4'>roles/storage.objectViewer</font>",
                                "Read objects — <b>not</b> bucket settings"],
                               ["<font face='Courier' size='6.4'>roles/storage.objectCreator</font>",
                                "Write objects without being able to read them"],
                               ["<font face='Courier' size='6.4'>roles/storage.admin</font>",
                                "Buckets <i>and</i> objects — broader than it looks"],
                               ["<font face='Courier' size='6.4'>roles/container.developer</font>",
                                "Deploy workloads into GKE, not manage clusters"],
                               ["<font face='Courier' size='6.4'>roles/run.invoker</font>",
                                "Call a private Cloud Run service"],
                               ["<font face='Courier' size='6.4'>roles/logging.viewer</font> / "
                                "<font face='Courier' size='6.4'>privateLogViewer</font>",
                                "Read logs / also read Data Access logs"],
                               ["<font face='Courier' size='6.4'>roles/monitoring.editor</font>",
                                "Dashboards and alerting policies"],
                               ["<font face='Courier' size='6.4'>roles/secretmanager.secretAccessor</font>",
                                "Read a secret payload"],
                           ]}),
            ]]}),
        ("h", "Custom roles — the lifecycle vocabulary"),
        ("cols", {"ratio": (58, 42), "cols": [
            [("bul", [
                'A custom role has a <b>launch stage</b>: ALPHA → BETA → GA, plus DISABLED. Disabling is '
                'how you take a role out of service without deleting it and breaking every binding.',
                'Deleting is <b>soft for 7 days</b>, then a 30-day purge — bindings that reference it stop '
                'granting immediately.',
                'Roles are defined at the <b>organisation</b> (usable anywhere in it) or at a <b>project</b> '
                '(usable only there). <b>Not at a folder.</b>',
                'Build one by copying a predefined role and removing permissions, not by listing '
                'permissions from scratch.',
                'You cannot include permissions the service has not made available for custom roles — some '
                'are marked NOT_SUPPORTED.',
             ])],
            [("panel", {"kind": "tip", "label": "THE MAINTENANCE COST IS THE POINT",
                        "text": 'A predefined role gains permissions automatically when the product gains '
                                'features. <b>A custom role does not</b> — someone must notice and edit '
                                'it. That ongoing cost is exactly why the exam prefers predefined roles, '
                                'and why "create a custom role" is wrong whenever a predefined one fits.'})],
        ]}),
        ("panel", {"kind": "trap", "label": "THREE ROLE MISTAKES THE OPTIONS ARE BUILT FROM",
                   "text": '<b>Granting Editor because it "obviously works".</b> It does, and it loses the '
                           'mark. · <b>Inventing a custom role when a predefined one exists</b> — custom '
                           'roles are the answer only when the stem rules the predefined ones out. · '
                           '<b>Granting at the project when the requirement names one bucket or one VM.</b> '
                           'Read the noun in the requirement: it tells you the node.'}),
    ],
})


# ==========================================================================
# Section 1 — billing, quotas, tooling
# ==========================================================================
PAGES.append({
    "id": "d1-billing",
    "label": "Section 1 · setting up",
    "title": "Billing, budgets, quotas, APIs and the tooling",
    "accent": "teal",
    "blocks": [
        ("cols", {"ratio": (52, 48), "cols": [
            [
                ("h", "Billing accounts"),
                ("bul", [
                    'A <b>billing account pays for many projects</b>; a project has <b>exactly one</b> (or '
                    'none, in which case its resources stop working).',
                    '<b>Self-serve</b> (credit card, monthly) vs <b>invoiced</b> (billed on terms, needs '
                    'eligibility). A <b>subaccount</b> re-bills a slice under one payer — the answer for a '
                    'reseller or a chargeback structure.',
                    'Linking a project needs <b>'
                    '<font face="Courier" size="6.4">roles/billing.user</font> on the billing account</b> '
                    'plus project-level rights. That split — one permission on each side — is a favourite '
                    'exam detail.',
                    'A billing account lives <b>outside</b> the project hierarchy. It can be attached to '
                    'the organisation for centralised control.',
                ]),
                ("h", "Seeing and controlling spend"),
                ("table", {"w": (30, 70), "head": ["Mechanism", "What it does — and its limit"],
                           "rows": [
                               ["<b>Budget + alerts</b>",
                                "Emails billing admins and users at percentage thresholds, on actual or "
                                "<b>forecast</b> spend. <b>It does not cap spend or stop anything.</b>"],
                               ["<b>Budget → Pub/Sub → function</b>",
                                "The <b>only</b> way to make a budget act — e.g. disable the billing link "
                                "or shut down resources. If an option claims a budget prevents overspend "
                                "without this, it is wrong."],
                               ["<b>Billing export to BigQuery</b>",
                                "The answer to any <i>analyse / break down / trend over time</i> cost "
                                "question. Console reports are for a glance; BigQuery is for analysis."],
                               ["<b>Labels</b>",
                                "key:value on resources, carried into the billing export — the mechanism "
                                "for per-team, per-environment or per-customer chargeback."],
                               ["<b>Pricing calculator</b>",
                                "Estimating <i>before</i> you build. Not a monitoring tool."],
                               ["<b>Committed use discounts</b>",
                                "1- or 3-year commitments for steady baseline load."],
                           ]}),
                ("panel", {"kind": "trap", "label": "ALERTS NOTIFY, CODE ACTS",
                           "text": 'The single most repeated billing trap: a budget threshold sends a '
                                   'message. It never turns anything off. The exam offers the passive '
                                   'option and the wired-up one side by side.'}),
            ],
            [
                ("h", "Quotas"),
                ("table", {"w": (30, 70), "head": ["Kind", "Behaviour"],
                           "rows": [
                               ["<b>Rate quota</b>",
                                "Resets every interval — API requests per minute. Exceeding it returns "
                                "429/RESOURCE_EXHAUSTED and usually just needs a retry with backoff."],
                               ["<b>Allocation quota</b>",
                                "A standing ceiling — VMs, CPUs, IP addresses, disks. Does not reset; you "
                                "either release resources or request an increase."],
                           ]}),
                ("bul", [
                    'Quotas are <b>per project and often per region</b>. "One team exhausted the quota and '
                    'blocked another" is answered by <b>separate projects</b>, every time.',
                    'Increases are requested per quota, per region, in <b>IAM &amp; Admin → Quotas</b>; '
                    'some need a support case.',
                    'Quotas protect you <b>and</b> Google. They are not a billing control — a budget is.',
                ]),
                ("h", "APIs and services"),
                ("bul", [
                    'Every API is <b>disabled until enabled, per project</b>. A permission-looking failure '
                    'on a fresh project is usually a disabled API, not IAM.',
                    'Enabling an API can create a <b>service agent</b> service account that the product '
                    'uses on your behalf — do not delete those.',
                    'Disabling an API breaks everything already using it; the exam likes this as a '
                    'consequence question.',
                ]),
                ("h", "The three ways to drive Google Cloud"),
                ("table", {"w": (26, 74), "head": ["Surface", "Notes"],
                           "rows": [
                               ["<b>Console</b>", "Discoverable, good for one-off work, poor for repeatability"],
                               ["<b>gcloud CLI</b>",
                                "Scriptable. Installed locally with the SDK, or ready-made in Cloud Shell. "
                                "Configurations hold project/region/account sets"],
                               ["<b>Client libraries / REST</b>",
                                "For applications. Authenticate with Application Default Credentials, which "
                                "find the attached service account automatically"],
                           ]}),
                ("panel", {"kind": "note", "label": "CLOUD SHELL",
                           "text": 'A free ephemeral VM with gcloud, kubectl, terraform and an editor '
                                   'preinstalled, plus <b>5 GB of persistent <font face="Courier" '
                                   'size="6.4">$HOME</font></b>. Anything outside $HOME is wiped between '
                                   'sessions, and the instance itself is recycled after inactivity. It is '
                                   'the answer to "administer with no local setup".'}),
            ]]}),
    ],
})


# ==========================================================================
# Section 5 — IAM in depth
# ==========================================================================
PAGES.append({
    "id": "d5-iam",
    "label": "Section 5 · access and security",
    "title": "IAM policies: bindings, conditions, deny and inheritance",
    "accent": "red",
    "blocks": [
        ("lede",
         'An <b>allow policy</b> is attached to a resource and is a list of <b>bindings</b>, each one '
         '<b>role + members (+ an optional condition)</b>. Everything else in this section is a '
         'consequence of that one sentence.'),
        ("cols", {"ratio": (48, 52), "cols": [
            [
                ("h", "Members — the prefixes to recognise"),
                ("table", {"w": (44, 56), "head": ["Member", "Meaning"],
                           "rows": [
                               ["<font face='Courier' size='6.4'>user:</font>", "One human identity"],
                               ["<font face='Courier' size='6.4'>group:</font>",
                                "A Google group — the preferred target"],
                               ["<font face='Courier' size='6.4'>serviceAccount:</font>", "A workload identity"],
                               ["<font face='Courier' size='6.4'>domain:</font>",
                                "Everyone in a Workspace / Cloud Identity domain"],
                               ["<font face='Courier' size='6.4'>principalSet:</font>",
                                "A federated external identity or a Kubernetes SA"],
                               ["<font face='Courier' size='6.4'>allAuthenticatedUsers</font>",
                                "Any Google account anywhere — <b>not</b> your org"],
                               ["<font face='Courier' size='6.4'>allUsers</font>",
                                "<b>The public internet.</b> On a bucket, this is how data leaks"],
                           ]}),
                ("h", "How inheritance actually behaves"),
                ("num", [
                    '<b>Additive and downward.</b> The effective policy at a resource is the <b>union</b> '
                    'of every binding from the organisation down. There is no "more specific wins".',
                    '<b>A child cannot subtract.</b> Removing a binding at the project does nothing if the '
                    'grant came from a folder.',
                    '<b>Future resources are included.</b> A folder binding covers projects created '
                    'tomorrow — which is why it is the answer to "including any new projects".',
                    '<b>Some resources have their own policies</b> — buckets, Pub/Sub topics, KMS keys, '
                    'service accounts, BigQuery datasets. That is where least privilege bottoms out.',
                ]),
                ("panel", {"kind": "trap", "label": "add- vs set-",
                           "text": '<font face="Courier" size="6.4">add-iam-policy-binding</font> adds one '
                                   'binding. <font face="Courier" size="6.4">set-iam-policy</font> '
                                   '<b>replaces the entire policy</b> with the file you supply — the way '
                                   'people accidentally delete everyone else\'s access. The additive verb '
                                   'is the exam-correct one unless the stem is explicitly doing a '
                                   'read-modify-write.'}),
            ],
            [
                ("h", "The two subtraction mechanisms"),
                ("table", {"w": (22, 40, 38), "head": ["", "IAM deny policy", "Organisation policy"],
                           "rows": [
                               ["<b>Subject</b>", "Named principals", "The resource configuration — "
                                "<b>everyone</b>, including Owners"],
                               ["<b>Expressed as</b>", "Denied permissions, with optional conditions",
                                "Constraints: boolean, or a list of allowed/denied values"],
                               ["<b>Evaluated</b>", "<b>Before</b> allow policies — a deny always wins",
                                "At configuration time — the operation is simply refused"],
                               ["<b>Typical use</b>",
                                "\"Contractors must never delete buckets, whatever else they are granted\"",
                                "\"No VM anywhere may have an external IP\"; \"resources only in "
                                "europe-central2\""],
                           ]}),
                ("h", "Conditions"),
                ("bul", [
                    'A condition is a CEL expression on the binding: time '
                    '(<font face="Courier" size="6.4">request.time</font>), resource name or type, or '
                    'request attributes. The grant applies <b>only</b> when it evaluates true.',
                    '<b>Temporary access</b> — "give the contractor access until the end of the month" — is '
                    'a condition, not a calendar reminder to remove a binding.',
                    'Conditions are supported on most, not all, services. If a question hinges on a '
                    'resource-name condition, it is testing that you reach for this rather than a custom '
                    'role.',
                ]),
                ("h", "Constraints worth recognising"),
                ("table", {"w": (56, 44), "head": ["Constraint", "Effect"],
                           "rows": [
                               ["<font face='Courier' size='6.4'>compute.vmExternalIpAccess</font>",
                                "No public IPs on VMs"],
                               ["<font face='Courier' size='6.4'>gcp.resourceLocations</font>",
                                "Data residency — restrict regions"],
                               ["<font face='Courier' size='6.4'>iam.disableServiceAccountKeyCreation</font>",
                                "Kills downloaded keys org-wide"],
                               ["<font face='Courier' size='6.4'>storage.publicAccessPrevention</font>",
                                "Blocks allUsers / allAuthenticatedUsers on buckets"],
                               ["<font face='Courier' size='6.4'>iam.allowedPolicyMemberDomains</font>",
                                "Domain-restricted sharing"],
                               ["<font face='Courier' size='6.4'>compute.requireShieldedVm</font>",
                                "Only Shielded VMs may be created"],
                               ["<font face='Courier' size='6.4'>sql.restrictPublicIp</font>",
                                "Cloud SQL instances must use private IP"],
                           ]}),
            ]]}),
        ("panel", {"kind": "key", "label": "THE ORDER OF EVALUATION, IN ONE LINE",
                   "text": '<b>Organisation policy</b> decides whether the configuration is permitted at '
                           'all → <b>deny policies</b> remove permissions from named principals → '
                           '<b>allow policies</b>, unioned from the org down, grant the rest. When a stem '
                           'says <i>"prevent this even for project owners"</i>, it is an organisation '
                           'policy. When it says <i>"this team specifically must never…"</i>, it is a deny '
                           'policy.'}),
    ],
})


# ==========================================================================
# Section 5 — service accounts
# ==========================================================================
PAGES.append({
    "id": "d5-sa",
    "label": "Section 5 · access and security",
    "title": "Service accounts, impersonation and revoking access",
    "accent": "red",
    "blocks": [
        ("lede",
         'A service account is <b>two things at once</b>: an <b>identity</b> that holds roles on resources, '
         'and a <b>resource</b> that principals hold roles on. Nearly every service-account question is '
         'really asking which of those two surfaces you need.'),
        ("cols", {"ratio": (50, 50), "cols": [
            [
                ("h", "Roles granted ON a service account"),
                ("table", {"w": (42, 58), "head": ["To let someone…", "Grant on the SA"],
                           "rows": [
                               ["Deploy a VM/function <b>running as</b> it",
                                "<font face='Courier' size='6.4'>roles/iam.serviceAccountUser</font>"],
                               ["<b>Impersonate</b> it / mint its tokens",
                                "<font face='Courier' size='6.4'>roles/iam.serviceAccountTokenCreator</font>"],
                               ["Create and manage service accounts",
                                "<font face='Courier' size='6.4'>roles/iam.serviceAccountAdmin</font>"],
                               ["Bind a Kubernetes SA to it",
                                "<font face='Courier' size='6.4'>roles/iam.workloadIdentityUser</font>"],
                               ["Sign blobs/JWTs as it",
                                "<font face='Courier' size='6.4'>roles/iam.serviceAccountTokenCreator</font>"],
                           ]}),
                ("panel", {"kind": "watch", "label": "USER vs TOKENCREATOR",
                           "text": '<b>serviceAccountUser</b> = attach it to a resource at deploy time. '
                                   '<b>serviceAccountTokenCreator</b> = become it right now, from a CLI or '
                                   'a job. Different questions, adjacent names, and both appear in the same '
                                   'option list.'}),
                ("h", "Default service accounts and scopes"),
                ("bul", [
                    'The <b>Compute Engine default service account</b> historically carried <b>Editor</b> '
                    'on the whole project, and is attached to VMs unless you say otherwise. "This VM can do '
                    'far too much" → create a dedicated SA with a narrow role and attach that.',
                    '<b>Access scopes</b> are the legacy VM-level limiter applied <i>on top of</i> IAM — '
                    'the effective permission is the <b>intersection</b>. Modern practice is '
                    '<font face="Courier" size="6.4">cloud-platform</font> scope plus a narrow IAM role.',
                    'Scopes can only be changed while the VM is <b>stopped</b>.',
                    '<b>Service agents</b> (created when you enable an API) are Google-managed accounts the '
                    'product uses on your behalf. Leave them alone.',
                ]),
            ],
            [
                ("h", "Impersonation — what it buys you"),
                ("bul", [
                    'Add <font face="Courier" size="6.4">--impersonate-service-account=SA</font> to <b>any '
                    'gcloud command</b> and it runs with that identity, using <b>short-lived credentials</b> '
                    'minted on the spot.',
                    'Nothing is downloaded, the action is <b>attributed to the human</b> in audit logs as '
                    'well as to the SA, and revocation is removing one role binding.',
                    'It is the correct answer to "let an engineer run a job with elevated rights without '
                    'giving them the rights permanently, and without a key file".',
                    '<b>Short-lived credentials</b> are the general pattern: access tokens (~1 hour), ID '
                    'tokens for authenticating to services, signed URLs for storage.',
                ]),
                ("h", "Revoking access — four mechanisms, ranked"),
                ("table", {"w": (32, 68), "head": ["Mechanism", "When it is the right one"],
                           "rows": [
                               ["<b>Remove the IAM binding</b>",
                                "The normal answer. Effective within seconds to a couple of minutes"],
                               ["<b>Disable or delete the SA</b>",
                                "Kills every credential it holds at once. Disable first — deletion is "
                                "recoverable for 30 days but breaks everything using it"],
                               ["<b>Deny policy</b>",
                                "When the grant is inherited from above and you cannot remove it"],
                               ["<b>Delete the key</b>",
                                "Only relevant if keys exist at all — and if they do, that is the finding"],
                           ]}),
                ("panel", {"kind": "trap", "label": "A DELETED SERVICE ACCOUNT LEAVES HOLES",
                           "text": 'Deleting an SA does not remove the bindings that reference it — they '
                                   'linger as <font face="Courier" size="6.4">deleted:</font> members. And '
                                   'anything running as it stops immediately. When a stem asks how to '
                                   '<i>pause</i> a workload\'s access, the answer is <b>disable</b>, not '
                                   'delete.'}),
            ]]}),
        ("h", "Where each product gets its identity"),
        ("table", {"w": (18, 34, 48), "head": ["Product", "Attach with", "Default if you do not"],
                   "rows": [
                       ["<b>Compute Engine</b>", "<font face='Courier' size='6.4'>--service-account</font> "
                        "at create time (VM must be stopped to change it)",
                        "The <b>Compute Engine default SA</b>, historically Editor on the project"],
                       ["<b>GKE</b>", "Workload Identity, per Kubernetes SA",
                        "The <b>node</b> service account — shared by every pod on the node, which is why "
                        "Workload Identity exists"],
                       ["<b>Cloud Run / functions</b>",
                        "<font face='Courier' size='6.4'>--service-account</font> on deploy",
                        "The default compute service account"],
                       ["<b>Cloud Build</b>", "A specified build service account",
                        "The Cloud Build service account, which is broad by default"],
                       ["<b>App Engine</b>", "The app's service account",
                        "The App Engine default service account"],
                   ]}),
        ("panel", {"kind": "note", "label": "APPLICATION DEFAULT CREDENTIALS — THE LOOKUP ORDER",
                   "text": 'Client libraries resolve an identity in this order: '
                           '<b>1.</b> the <font face="Courier" size="6.4">GOOGLE_APPLICATION_CREDENTIALS</font> '
                           'environment variable (a key file) → <b>2.</b> credentials from '
                           '<font face="Courier" size="6.4">gcloud auth application-default login</font> → '
                           '<b>3.</b> the <b>attached service account</b>, via the metadata server. On '
                           'Google Cloud, step 3 is what makes keyless work with no code changes — and it '
                           'is why a stray key file in an environment variable silently overrides it.'}),
        ("panel", {"kind": "key", "label": "ONE SERVICE ACCOUNT PER WORKLOAD",
                   "text": 'The standing best practice, and the answer to a whole family of questions: give '
                           'each application its own service account with only the roles it needs, rather '
                           'than sharing one account (or the default one) across several. It makes both '
                           'least privilege and audit attribution possible at all.'}),
    ],
})


# ==========================================================================
# Section 5 — federation and keys
# ==========================================================================
PAGES.append({
    "id": "d5-federation",
    "label": "Section 5 · access and security",
    "title": "Keyless access: Workload Identity, federation, and keys",
    "accent": "red",
    "blocks": [
        ("lede",
         '<b>R7: the answer never involves key material.</b> Google Cloud provides a keyless mechanism for '
         'every place a workload can run, and the exam consistently rewards it. This page is that map.'),
        ("h", "The credentials decision table"),
        ("table", {"w": (24, 30, 46), "head": ["Where the workload runs", "The answer", "Why"],
                   "rows": [
                       ["<b>On a Google Cloud resource</b><br/>(VM, Cloud Run, Cloud Functions, App Engine)",
                        "<b>Attach a service account</b>",
                        "The metadata server at "
                        "<font face='Courier' size='6.4'>169.254.169.254</font> mints short-lived tokens "
                        "automatically. No key exists, so none can leak, and Application Default "
                        "Credentials find it with no configuration."],
                       ["<b>On GKE</b>",
                        "<b>Workload Identity Federation for GKE</b>",
                        "Binds a <b>Kubernetes</b> SA to a <b>Google</b> SA. Pods get tokens from the "
                        "metadata server, per workload rather than per node. <b>Never a key mounted as a "
                        "Kubernetes secret.</b>"],
                       ["<b>A human, or a job, needing another identity briefly</b>",
                        "<b>Impersonation</b> — "
                        "<font face='Courier' size='6.4'>roles/iam.serviceAccountTokenCreator</font>",
                        "Short-lived, fully audited, revoked by removing one binding."],
                       ["<b>Outside Google Cloud</b><br/>(AWS, Azure, GitHub Actions, on-prem with an IdP)",
                        "<b>Workload Identity Federation</b>",
                        "The external token is exchanged at Google's <b>STS</b> for short-lived Google "
                        "credentials. This is the entire point of federation: <b>keyless access from "
                        "anywhere</b>."],
                       ["<b>A human signing in</b>",
                        "<b>SSO / federated sign-in</b> to Cloud Identity",
                        "Corporate credentials stay at the IdP; Google Cloud sees a normal user identity."],
                       ["<b>Genuinely no federation possible</b>",
                        "A service-account key — last resort",
                        "Then rotate it, store it in Secret Manager, and expect a better option to be "
                        "sitting in the same list."],
                   ]}),
        ("cols", {"ratio": (50, 50), "cols": [
            [
                ("h", "Workload Identity Federation, in five steps"),
                ("num", [
                    'Create a <b>workload identity pool</b> to represent the external identity source.',
                    'Add a <b>provider</b> (OIDC or SAML) — for AWS, GitHub Actions, Azure AD, or any '
                    'OIDC IdP.',
                    'Map the external claims to Google attributes, and write a <b>condition</b> so that '
                    'only the intended repository, role or account is accepted.',
                    'Grant the federated principal '
                    '<font face="Courier" size="6.4">roles/iam.workloadIdentityUser</font> on a service '
                    'account — or, with direct resource access, grant roles to the principal itself.',
                    'The workload exchanges its own token at Google STS and receives short-lived Google '
                    'credentials. <b>No key ever exists.</b>',
                ]),
                ("panel", {"kind": "key", "label": "GKE WORKLOAD IDENTITY, THE SHORT VERSION",
                           "text": 'Enable it on the cluster '
                                   '(<font face="Courier" size="6.4">--workload-pool=PROJECT.svc.id.goog</font>) '
                                   '→ annotate the Kubernetes SA with the Google SA address → grant '
                                   '<font face="Courier" size="6.4">roles/iam.workloadIdentityUser</font> on '
                                   'the Google SA to the KSA principal → run the pod under that KSA. Three '
                                   'objects, one binding, zero keys.'}),
            ],
            [
                ("h", "If a key really must exist"),
                ("bul", [
                    'A key is a <b>JSON file containing a private key</b> that never expires by itself. It '
                    'is a long-lived credential in a file, which is why the exam treats it as a last '
                    'resort.',
                    'Control the risk at the org level: <b>'
                    '<font face="Courier" size="6.4">iam.disableServiceAccountKeyCreation</font></b>, plus '
                    '<font face="Courier" size="6.4">disableServiceAccountKeyUpload</font>.',
                    '<b>Rotate</b> by creating a new key, rolling it out, then deleting the old one — and '
                    'audit existing keys with '
                    '<font face="Courier" size="6.4">gcloud iam service-accounts keys list</font>.',
                    'Store the key in <b>Secret Manager</b>, never in a repository, a container image, or a '
                    'config map.',
                ]),
                ("h", "Human access to machines"),
                ("bul", [
                    '<b>OS Login</b> ties SSH to IAM — '
                    '<font face="Courier" size="6.4">roles/compute.osLogin</font> or '
                    '<font face="Courier" size="6.4">osAdminLogin</font> — instead of scattering public '
                    'keys through instance metadata. Enable with metadata '
                    '<font face="Courier" size="6.4">enable-oslogin=TRUE</font>, project-wide or per '
                    'instance. <b>The manageable, auditable, revocable answer for a fleet.</b>',
                    '<b>IAP TCP forwarding</b> reaches SSH/RDP on a VM with <b>no external IP and no '
                    'bastion</b>; grant '
                    '<font face="Courier" size="6.4">roles/iap.tunnelResourceAccessor</font> and allow '
                    '<font face="Courier" size="6.4">35.235.240.0/20</font>.',
                    'Together they are the standard "secure administrative access" answer: IAP for '
                    'reachability, OS Login for authorisation.',
                ]),
                ("panel", {"kind": "trap", "label": "KEY-SHAPED DISTRACTORS",
                           "text": 'Watch for options that <i>sound</i> managed but still move key '
                                   'material: "store the key in a ConfigMap", "bake the credentials into '
                                   'the image", "share the key through Secret Manager with the partner". '
                                   'Federation removes the key entirely — that is the distinction being '
                                   'tested.'}),
            ]]}),
    ],
})


# ==========================================================================
# Section 5 — secrets, encryption, security products
# ==========================================================================
PAGES.append({
    "id": "d5-secrets",
    "label": "Section 5 · access and security",
    "title": "Secrets, encryption keys and the security products",
    "accent": "red",
    "blocks": [
        ("cols", {"ratio": (50, 50), "cols": [
            [
                ("h", "Secret Manager"),
                ("bul", [
                    'Secrets have <b>versions</b>. Applications read '
                    '<font face="Courier" size="6.4">latest</font> or a pinned version; <b>rotation</b> is '
                    'adding a new version, then disabling and later destroying the old one.',
                    'Access is IAM: <font face="Courier" size="6.4">roles/secretmanager.secretAccessor</font> '
                    'to read a payload. Grant it to the <b>workload\'s service account</b>, at the '
                    '<b>secret</b>, not at the project.',
                    'Replication is <b>automatic</b>, or <b>user-managed</b> where you name the regions — '
                    'the latter is the answer for data-residency stems.',
                    'Supports <b>CMEK</b>, rotation schedules, expiry, and audit logging of every access.',
                    'It is the right home for API keys, database passwords and third-party tokens — '
                    '<b>not</b> environment variables in a deployment config, and <b>not</b> a bucket.',
                ]),
                ("h", "Encryption — the four-way"),
                ("table", {"w": (14, 44, 42), "head": ["Option", "Who holds the key", "The stem that selects it"],
                           "rows": [
                               ["<b>Default</b>",
                                "Google, automatically. Always on, at rest, nothing to configure",
                                "No mention of keys at all"],
                               ["<b>CMEK</b>",
                                "You, in <b>Cloud KMS</b> — Google-hosted; you control rotation, versions "
                                "and destruction",
                                "<i>\"We must control the key / rotate it / destroy the data by destroying "
                                "the key.\"</i> The usual right answer"],
                               ["<b>CSEK</b>",
                                "You, <b>entirely outside</b> — supplied with every API call. Compute "
                                "Engine and Cloud Storage only",
                                "<i>\"The key must never be stored in Google Cloud.\"</i> Lose it and the "
                                "data is gone"],
                               ["<b>EKM</b>",
                                "You, in an <b>external key manager</b>, reached through Cloud KMS",
                                "<i>\"Keys must remain in our existing on-prem or third-party HSM\"</i>"],
                           ]}),
            ],
            [
                ("h", "Cloud KMS shape"),
                ("bul", [
                    '<b>Key ring → key → key version.</b> A key ring is created in a location (regional, '
                    'dual-region, multi-region or global) and <b>can never be moved or deleted</b>.',
                    '<b>Rotation</b> can be automatic on a schedule. Old versions stay available to decrypt '
                    'existing data; new data uses the primary version.',
                    'Destroying a version is <b>scheduled, not immediate</b> — 24 hours by default, so it '
                    'can be restored. That delay is deliberately examinable.',
                    'A service needs '
                    '<font face="Courier" size="6.4">roles/cloudkms.cryptoKeyEncrypterDecrypter</font> on '
                    'the key — usually granted to the product\'s <b>service agent</b>, which is why CMEK '
                    'setups have a "grant the agent access" step.',
                    '<b>HSM</b> protection level for FIPS 140-2 Level 3; <b>software</b> otherwise.',
                ]),
                ("h", "Data access on Cloud Storage"),
                ("bul", [
                    '<b>Uniform bucket-level access</b> turns off per-object ACLs so IAM is the only '
                    'mechanism — the recommended, and usually correct, setting.',
                    '<b>Signed URL</b> = time-limited access for someone with <b>no Google identity</b>. '
                    'Making the bucket public is the wrong answer to that stem.',
                    '<b>Public access prevention</b> blocks '
                    '<font face="Courier" size="6.4">allUsers</font> regardless of other settings — the '
                    'org-policy-backed guarantee against accidental exposure.',
                ]),
                ("h", "Security products to recognise by name"),
                ("table", {"w": (34, 66), "head": ["Product", "One line"],
                           "rows": [
                               ["<b>Security Command Center</b>",
                                "Central findings: misconfigurations, vulnerabilities, exposure"],
                               ["<b>VPC Service Controls</b>",
                                "A perimeter around services to stop <b>data exfiltration</b> — distinct "
                                "from IAM, which is about identity"],
                               ["<b>Cloud Armor</b>", "WAF and DDoS policies at the load balancer"],
                               ["<b>Binary Authorization</b>", "Only signed/attested images may be deployed"],
                               ["<b>Shielded VM</b>", "Secure boot, vTPM, integrity monitoring"],
                               ["<b>Confidential VM</b>", "Encryption of data <i>in use</i>"],
                               ["<b>Sensitive Data Protection</b> (DLP)",
                                "Discover, classify and redact sensitive data"],
                               ["<b>reCAPTCHA / Identity Platform</b>", "Abuse protection; end-user identity for apps"],
                           ]}),
            ]]}),
        ("panel", {"kind": "watch", "label": "IAM vs VPC SERVICE CONTROLS",
                   "text": 'IAM answers <i>who may call this API</i>. VPC Service Controls answers <i>from '
                           'where, and may the data leave</i>. A stem about a legitimate user copying data '
                           'to a personal project is a <b>perimeter</b> problem, not a role problem — that '
                           'distinction is the whole reason the product exists.'}),
    ],
})


# ==========================================================================
# Section 4 — logging
# ==========================================================================
PAGES.append({
    "id": "d4-logging",
    "label": "Section 4 · operating",
    "title": "Cloud Logging: buckets, sinks, filters and audit logs",
    "accent": "teal",
    "blocks": [
        ("lede",
         'Logging questions are almost always one of four things: <b>where do logs go</b>, <b>how long are '
         'they kept</b>, <b>how do I get them somewhere else</b>, and <b>who did that</b>. Knowing the four '
         'audit-log types and the sink destinations answers most of them outright.'),
        ("cols", {"ratio": (50, 50), "cols": [
            [
                ("h", "Where logs live"),
                ("table", {"w": (30, 70), "head": ["Log bucket", "Behaviour"],
                           "rows": [
                               ["<font face='Courier' size='6.4'>_Default</font>",
                                "Everything not otherwise routed. <b>30 days</b> by default, configurable "
                                "up to 10 years. Can be disabled by routing around it"],
                               ["<font face='Courier' size='6.4'>_Required</font>",
                                "<b>Admin Activity and System Event audit logs. 400 days. Cannot be "
                                "changed, disabled or deleted, and is free</b>"],
                               ["<b>User-defined buckets</b>",
                                "Your own retention (1 day – 10 years), your own region — the answer to "
                                "\"logs must stay in the EU\" or \"keep security logs for seven years\""],
                           ]}),
                ("h", "Sinks — routing logs onward"),
                ("bul", [
                    'A <b>sink</b> = an inclusion filter + a destination. Matching entries are copied as '
                    'they arrive; a sink is not retroactive.',
                    '<b>Cloud Storage</b> — cheap long-term archive and compliance retention.',
                    '<b>BigQuery</b> — SQL analysis, joins against other data, long-term reporting.',
                    '<b>Pub/Sub</b> — streaming to a third-party SIEM (Splunk, Datadog) or custom '
                    'processing.',
                    '<b>Another log bucket</b>, or another project — for centralisation.',
                    'A sink has a <b>writer identity</b>; it must be granted write access on the '
                    'destination or the sink silently drops everything. A favourite exam detail.',
                    '<b>Aggregated sink</b> at the folder or organisation level, with '
                    '<font face="Courier" size="6.4">--include-children</font>, captures every project '
                    'underneath — <b>the answer to "centralise logs from all projects, including future '
                    'ones"</b>.',
                ]),
                ("panel", {"kind": "tip", "label": "CUTTING LOGGING COST",
                           "text": '<b>Exclusion filters</b> drop entries <i>before</i> ingestion, so you '
                                   'are not billed for them — the correct answer to "reduce our logging '
                                   'bill". Shortening retention helps storage only. Turning off Data Access '
                                   'logs is the other big lever.'}),
            ],
            [
                ("h", "Audit logs — the four types"),
                ("table", {"w": (26, 74), "head": ["Type", "Records"],
                           "rows": [
                               ["<b>Admin Activity</b>",
                                "Configuration and metadata changes. <b>Always on, free, cannot be "
                                "disabled</b>. \"Who created/deleted/changed this?\""],
                               ["<b>Data Access</b>",
                                "Reads and writes of <b>user data</b>. <b>Off by default</b> (except "
                                "BigQuery), chargeable, and enabled per service in the IAM audit config. "
                                "\"Who read this object?\""],
                               ["<b>System Event</b>",
                                "Google-initiated actions — live migration, automatic restarts. Always on, "
                                "free"],
                               ["<b>Policy Denied</b>",
                                "A request refused by a security policy (VPC Service Controls, org "
                                "policy). Charged"],
                           ]}),
                ("panel", {"kind": "trap", "label": "\"WHO READ THE DATA?\"",
                           "text": 'If nobody enabled <b>Data Access</b> logs beforehand, the answer is '
                                   'that <b>you cannot tell</b> — and the correct option is to enable them '
                                   'now. Admin Activity logs record the configuration change, never the '
                                   'read.'}),
                ("h", "Filters worth recognising"),
                ("code",
                 'resource.type="gce_instance"\n'
                 'severity>=ERROR\n'
                 'timestamp>="2026-09-18T00:00:00Z"\n'
                 '\n'
                 'protoPayload.methodName="v1.compute.instances.delete"\n'
                 'protoPayload.authenticationInfo.principalEmail=\n'
                 '    "someone@example.com"\n'
                 '\n'
                 'logName="projects/P/logs/cloudaudit.googleapis.com\n'
                 '    %2Factivity"'),
                ("h", "Finding things in logs"),
                ("bul", [
                    'The <b>Logs Explorer</b> query language filters on '
                    '<font face="Courier" size="6.4">resource.type</font>, '
                    '<font face="Courier" size="6.4">severity</font>, '
                    '<font face="Courier" size="6.4">logName</font>, '
                    '<font face="Courier" size="6.4">jsonPayload.*</font>, and free text. Severity ladder: '
                    'DEBUG · INFO · NOTICE · WARNING · ERROR · CRITICAL · ALERT · EMERGENCY.',
                    '<b>Log Analytics</b> runs <b>SQL over a log bucket in place</b>, with no sink and no '
                    'copy. When a stem says "query our existing logs with SQL without building a pipeline", '
                    'that is it — <b>not</b> a BigQuery sink.',
                    '<b>Log-based metrics</b> turn a matching log pattern into a counter or distribution '
                    'you can chart and alert on — the bridge when the only signal is a log line.',
                    '<b>The Ops Agent</b> is what ships <b>application and system logs</b> (and guest '
                    'metrics) from a VM. Without it, you get the hypervisor\'s view and nothing from '
                    'inside.',
                ]),
            ]]}),
    ],
})


# ==========================================================================
# Section 4 — monitoring
# ==========================================================================
PAGES.append({
    "id": "d4-monitoring",
    "label": "Section 4 · operating",
    "title": "Cloud Monitoring: metrics, agents, alerts and SLOs",
    "accent": "teal",
    "blocks": [
        ("cols", {"ratio": (50, 50), "cols": [
            [
                ("h", "What you get, and what needs an agent"),
                ("table", {"w": (44, 56), "head": ["Signal", "Source"],
                           "rows": [
                               ["CPU utilisation, disk and network I/O, uptime",
                                "<b>Free, no agent</b> — the hypervisor sees it"],
                               ["<b>Memory used, free disk space, swap, per-process</b>",
                                "<b>Ops Agent required</b> — these live inside the guest OS"],
                               ["Application logs from a VM", "<b>Ops Agent</b>"],
                               ["Custom application metrics",
                                "The Monitoring API, OpenTelemetry, or a log-based metric"],
                               ["Managed-service metrics (Cloud SQL, Run, GKE, Pub/Sub)",
                                "Automatic — the platform emits them"],
                           ]}),
                ("panel", {"kind": "key", "label": "THE SINGLE MOST REPEATED D4 FACT",
                           "text": '<b>Memory and disk-space metrics require the Ops Agent.</b> Any stem '
                                   'about alerting on memory pressure or a filling disk has "install the '
                                   'Ops Agent" somewhere in the correct answer.'}),
                ("h", "Alerting"),
                ("bul", [
                    '<b>Alerting policy = condition + notification channel.</b> Without a channel, nobody '
                    'is told — and a dashboard is not a notification.',
                    'Channels: email, SMS, Slack, PagerDuty, Pub/Sub, webhooks. They are configured '
                    'separately and then referenced.',
                    'A condition has a <b>duration</b> ("above 90% for 5 minutes") — that is what stops a '
                    'transient spike paging someone.',
                    '<b>Uptime checks</b> probe a URL, IP or resource from several global locations; pair '
                    'one with an alerting policy for "tell me when the site is unreachable from outside".',
                    '<b>Notification on log entries</b> is done by creating a log-based metric and alerting '
                    'on it, or by routing through Pub/Sub.',
                ]),
            ],
            [
                ("h", "Seeing many projects at once"),
                ("bul", [
                    'A <b>metrics scope</b> belongs to a <b>scoping project</b> and can include many '
                    'monitored projects. You then see all of them in one place, with <b>no data copying '
                    'and no agents changed</b>.',
                    'This is the answer to "one dashboard across our twelve projects". Creating a sink to a '
                    'central project is the <i>logging</i> answer; the monitoring answer is a metrics '
                    'scope.',
                    '<b>Dashboards</b> can be defined as JSON and deployed as code, which is the '
                    'repeatable-and-auditable answer.',
                    '<b>Groups</b> organise resources by name, tag or region so a policy can target them as '
                    'a set.',
                ]),
                ("h", "SLIs, SLOs and error budgets"),
                ("table", {"w": (26, 74), "head": ["Term", "Meaning"],
                           "rows": [
                               ["<b>SLI</b>", "The measurement — availability, latency, correctness"],
                               ["<b>SLO</b>", "The target for that measurement over a window — 99.9% of "
                                              "requests under 300 ms over 28 days"],
                               ["<b>Error budget</b>",
                                "<b>1 − SLO.</b> The permitted amount of failure. At 99.9% over 30 days it "
                                "is about 43 minutes"],
                               ["<b>Burn rate</b>",
                                "How fast the budget is being consumed. <b>Burn-rate alerts</b> page only "
                                "when the trajectory actually threatens the SLO — the sophisticated answer "
                                "to alert fatigue"],
                               ["<b>SLA</b>",
                                "The contractual promise, with money attached. Always <b>looser</b> than "
                                "the internal SLO"],
                           ]}),
                        ("h", "What to alert on — the four golden signals"),
                ("table", {"w": (22, 78), "head": ["Signal", "Typical condition"],
                           "rows": [
                               ["<b>Latency</b>", "95th percentile request time above the SLO for 5 minutes"],
                               ["<b>Traffic</b>", "Requests per second collapsing or spiking beyond capacity"],
                               ["<b>Errors</b>", "5xx rate above a percentage of total, not an absolute count"],
                               ["<b>Saturation</b>",
                                "CPU, memory (Ops Agent), disk space, connection-pool or queue depth "
                                "approaching a limit"],
                           ]}),
                ("p", 'Alert on <b>symptoms users feel</b>, not on every resource metric. A page that '
                      'nobody can act on is the thing burn-rate alerting exists to remove.'),
        ("panel", {"kind": "watch", "label": "MONITORING vs LOGGING vs DIAGNOSTICS",
                           "text": '<b>Monitoring</b> tells you something is wrong (a metric crossed a '
                                   'line). <b>Logging</b> tells you what happened (the entries around it). '
                                   'The <b>diagnostic tools</b> on the next page tell you why (which '
                                   'exception, which span, which function). Options usually offer one of '
                                   'each — match the tool to the verb in the stem.'}),
            ]]}),
    ],
})


# ==========================================================================
# Section 4 — diagnostics and cost/resource optimisation
# ==========================================================================
PAGES.append({
    "id": "d4-diagnostics",
    "label": "Section 4 · operating",
    "title": "The diagnostic tools, and Active Assist",
    "accent": "teal",
    "blocks": [
        ("lede",
         'These products consume <b>different signals and barely overlap</b>, so the noun in the stem '
         'decides the answer almost mechanically. Read the first table until the mapping is automatic.'),
        ("table", {"w": (20, 26, 54), "head": ["The stem says", "The answer", "Why nothing else fits"],
                   "rows": [
                       ["<b>Exception · stack trace · crash · error rate</b>", "<b>Error Reporting</b>",
                        "It groups identical stack traces into one issue, counts occurrences, and can "
                        "notify on a <b>newly seen</b> error. Trace and Profiler never see exceptions at "
                        "all."],
                       ["<b>Latency · slow request · which call is slow · across services</b>",
                        "<b>Cloud Trace</b>",
                        "Per-request spans, end to end, including downstream calls. It tells you "
                        "<i>where</i> the time went — not why the CPU is busy."],
                       ["<b>CPU · memory · which function is expensive · in production</b>",
                        "<b>Cloud Profiler</b>",
                        "Continuous statistical profiling of running code at very low overhead. It answers "
                        "\"which function burns the time\", which Trace cannot."],
                       ["<b>Idle · underused · oversized · could save money · unattended</b>",
                        "<b>Active Assist recommenders</b>",
                        "Idle VM, idle disk, idle address, machine-type right-sizing, unattended project, "
                        "IAM role recommendations, commitment analysis. It is the waste-and-risk tool, not "
                        "a monitoring tool."],
                       ["<b>Is it up · from outside · from several regions</b>", "<b>Uptime check</b>",
                        "A synthetic probe, not a metric the workload emits."],
                   ]}),
        ("cols", {"ratio": (50, 50), "cols": [
            [
                ("h", "Active Assist in more detail"),
                ("bul", [
                    'Recommenders are queried per <b>project and location</b>, from the console, '
                    '<font face="Courier" size="6.4">gcloud recommender</font>, or the API — so they can be '
                    'reported on at scale.',
                    'The ones worth naming: <b>idle VM</b>, <b>idle persistent disk</b>, <b>idle IP '
                    'address</b>, <b>machine-type right-sizing</b>, <b>unattended project</b>, <b>IAM role '
                    'recommendations</b>, <b>commitment (CUD) recommendations</b>.',
                    'Each recommendation carries an estimated impact — cost, security or performance — '
                    'which is what makes "which of these saves money" answerable.',
                ]),
                ("h", "The standard cost-reduction ladder"),
                ("num", [
                    '<b>Delete what nobody uses</b> — idle disks, unattached static IPs, forgotten '
                    'snapshots and old images. Active Assist finds them.',
                    '<b>Right-size</b> what remains, using observed utilisation rather than the original '
                    'guess.',
                    '<b>Schedule</b> non-production resources off outside working hours — a VM billed per '
                    'second that is needed one hour a day is ~4% utilisation.',
                    '<b>Commit</b> to the steady baseline (CUDs) and use <b>Spot</b> for the '
                    'interruption-tolerant remainder.',
                    '<b>Move cold data down the storage tiers</b> with lifecycle rules.',
                ]),
            ],
            [
                ("h", "Managing resources at scale"),
                ("bul", [
                    '<b>Labels</b> are the organising primitive: environment, team, cost-centre, '
                    'application. They flow into billing export and drive filters everywhere.',
                    '<b>Resource Manager search</b> and '
                    '<font face="Courier" size="6.4">--filter</font> on gcloud list commands answer "find '
                    'every untagged VM across the org".',
                    '<b>Cloud Asset Inventory</b> holds a searchable, exportable, five-week history of '
                    'resources and their IAM — the answer to "what did we have, and what changed".',
                    '<b>Organisation policy</b> is the preventive control; recommenders and Asset '
                    'Inventory are the detective ones.',
                ]),
                ("h", "When a workload is misbehaving — the order to look"),
                ("num", [
                    '<b>Is it up?</b> Uptime check, load-balancer health check, pod status.',
                    '<b>What changed?</b> Admin Activity audit logs, deployment or revision history.',
                    '<b>What is the metric doing?</b> CPU, memory (Ops Agent), request rate, error rate.',
                    '<b>What do the logs say?</b> Logs Explorer at ERROR and above, around the change.',
                    '<b>Why is the code slow or failing?</b> Trace for latency, Profiler for CPU, Error '
                    'Reporting for exceptions.',
                ]),
                ("panel", {"kind": "tip", "label": "R6 — RECOVERY ORDER",
                           "text": 'When the options are recovery actions, prefer the one that <b>loses '
                                   'the least data</b> and <b>preserves the evidence</b> — take a snapshot '
                                   'or capture the logs before you rebuild. Delete-and-recreate is usually '
                                   'the distractor: it restores service and destroys the post-mortem.'}),
            ]]}),
    ],
})


# ==========================================================================
# Section 4 — resilience
# ==========================================================================
PAGES.append({
    "id": "d4-resilience",
    "label": "Section 4 · operating",
    "title": "Backup, recovery and designing for failure",
    "accent": "teal",
    "blocks": [
        ("cols", {"ratio": (50, 50), "cols": [
            [
                ("h", "The two numbers every DR question turns on"),
                ("table", {"w": (16, 40, 44), "head": ["", "Means", "Decided by"],
                           "rows": [
                               ["<b>RPO</b>", "How much data you can afford to lose",
                                "<b>Backup frequency</b> and replication — hourly snapshots give a "
                                "one-hour RPO"],
                               ["<b>RTO</b>", "How long you can afford to be down",
                                "<b>The restore mechanism</b> — a warm standby beats restoring from an "
                                "archive by hours"],
                           ]}),
                ("p", 'Read which of the two the stem states. "We cannot lose more than five minutes of '
                      'transactions" is an <b>RPO</b> requirement and points at replication or PITR; "we '
                      'must be serving again within an hour" is an <b>RTO</b> requirement and points at a '
                      'standby.'),
                ("h", "Per-product protection"),
                ("table", {"w": (30, 70), "head": ["Resource", "The mechanism"],
                           "rows": [
                               ["<b>Persistent disks</b>",
                                "<b>Scheduled snapshots</b> via a resource policy. Incremental, and "
                                "restorable into any zone or region"],
                               ["<b>Whole VMs</b>",
                                "<b>Machine images</b> — all disks plus configuration. The clone/move "
                                "answer"],
                               ["<b>Cloud SQL</b>",
                                "Automated daily backups + <b>point-in-time recovery</b> (needs binary "
                                "logging / WAL). Restores to a moment, not just to last night"],
                               ["<b>Cloud Storage</b>",
                                "<b>Object versioning</b> for accidental deletes; <b>retention policy + "
                                "bucket lock</b> for compliance; lifecycle rules to age versions out"],
                               ["<b>GKE / Cloud Run</b>",
                                "The state is elsewhere — protect the <b>data</b> and keep the manifests "
                                "or images in source control"],
                               ["<b>Firestore / Bigtable / Spanner</b>",
                                "Managed export/backup features; Spanner and Bigtable also replicate "
                                "across regions"],
                           ]}),
            ],
            [
                ("h", "Designing so the failure does not matter"),
                ("table", {"w": (26, 74), "head": ["Failure", "The standard answer"],
                           "rows": [
                               ["<b>One VM dies</b>",
                                "A managed instance group with a <b>health check</b> — autohealing "
                                "recreates it"],
                               ["<b>A zone fails</b>",
                                "<b>Regional</b> everything: regional MIG, regional cluster, regional "
                                "persistent disk, Cloud SQL with a standby in another zone"],
                               ["<b>A region fails</b>",
                                "Multi-region storage, a second region with a load balancer in front, "
                                "cross-region replicas. Costly — the stem has to ask for it"],
                               ["<b>A bad deployment</b>",
                                "Rolling updates, canary traffic splits, and a one-step rollback (Cloud "
                                "Run revisions, MIG rollback, Deployment undo)"],
                               ["<b>Someone deletes something</b>",
                                "Versioning, liens, retention locks, and <b>least privilege</b> — the "
                                "preventive half of the answer"],
                           ]}),
                        ("h", "Snapshot mechanics — the details that get tested"),
                ("bul", [
                    'Snapshots are <b>incremental</b>: the first captures everything, later ones only the '
                    'changed blocks. Deleting one does not break the others — the data it still needs is '
                    'rolled forward automatically.',
                    'They are <b>global resources</b>: a snapshot taken in one region can create a disk in '
                    'another, which is how you move a disk across regions.',
                    'Use a <b>resource policy</b> to schedule them, with a retention period and an '
                    'auto-delete rule, rather than a cron job on a VM.',
                    'For a consistent snapshot of a running VM, <b>flush the filesystem</b> (or use the '
                    'application\'s own quiesce mechanism) first — otherwise you capture whatever was '
                    'mid-write.',
                    'Storage location can be regional or multi-regional, and it is billed separately from '
                    'the disk.',
                ]),
        ("panel", {"kind": "key", "label": "REGIONAL IS THE DEFAULT ANSWER TO HIGH AVAILABILITY",
                           "text": 'Almost every "survive a failure" item at ACE level is answered by '
                                   'choosing the <b>regional</b> form of the thing already in the question '
                                   '— regional MIG, regional cluster, regional Cloud SQL, multi-region '
                                   'bucket. Multi-region designs appear when the stem explicitly names '
                                   'region-level failure or a global user base.'}),
                ("h", "Testing and operating the plan"),
                ("bul", [
                    'A backup you have never restored is a hypothesis. The exam-correct answer to "how do '
                    'we know the plan works" is <b>rehearse the restore</b> on a schedule.',
                    'Keep backups in a <b>different failure domain</b> — another region, and ideally '
                    'another project with separate IAM, so the same mistake cannot destroy both.',
                    '<b>Infrastructure as code</b> is part of recovery: rebuilding an environment from '
                    'Terraform is faster and more reliable than rebuilding it from memory.',
                ]),
            ]]}),
    ],
})


# ==========================================================================
# Section 2 — databases
# ==========================================================================
PAGES.append({
    "id": "d2-databases",
    "label": "Section 2 · planning",
    "title": "Choosing a data store",
    "accent": "amber",
    "blocks": [
        ("lede",
         'Decided by <b>three words in the stem</b>: the <b>shape</b> (relational, key-value, document, '
         'analytical), the <b>scale</b> (gigabytes or petabytes), and whether it needs <b>horizontal scale '
         'with strong consistency</b> — which is Spanner and nothing else.'),
        ("table", {"w": (15, 27, 32, 26),
                   "head": ["Product", "Shape", "Choose when the stem says", "Do not choose when"],
                   "rows": [
                       ["<b>Cloud SQL</b>", "Managed MySQL / PostgreSQL / SQL Server, one region",
                        "\"Lift and shift our MySQL\", \"relational, up to a few TB\", \"managed backups "
                        "and read replicas\"",
                        "Global writes, or petabyte scale"],
                       ["<b>Spanner</b>", "Horizontally scalable relational, global, strongly consistent",
                        "\"Relational <b>and</b> global <b>and</b> scales horizontally\", \"99.999%\", "
                        "\"strong consistency across regions\"",
                        "The data is small — it is expensive"],
                       ["<b>Bigtable</b>", "Wide-column NoSQL, petabyte scale, single-digit ms",
                        "\"Time series\", \"IoT telemetry\", \"very high write throughput\", \"HBase API\"",
                        "You need SQL, joins, or transactions across rows"],
                       ["<b>Firestore</b>", "Document NoSQL, mobile/web SDKs, offline sync",
                        "\"Mobile app\", \"real-time listeners\", \"flexible documents\"",
                        "Heavy analytical querying"],
                       ["<b>BigQuery</b>", "Serverless analytical warehouse",
                        "\"Analytics\", \"ad-hoc SQL over TB/PB\", \"BI dashboard\", \"no infrastructure\"",
                        "It is an application's transactional store"],
                       ["<b>Memorystore</b>", "Managed Redis / Valkey / Memcached",
                        "\"Cache\", \"session store\", \"reduce database load\"",
                        "It is the system of record"],
                       ["<b>AlloyDB</b>", "PostgreSQL-compatible, high performance, HTAP leaning",
                        "\"PostgreSQL but we have outgrown Cloud SQL\"",
                        "A plain small Postgres workload"],
                   ]}),
        ("cols", {"ratio": (50, 50), "cols": [
            [
                ("h", "Cloud SQL — the facts that get asked"),
                ("bul", [
                    '<b>Read replicas</b> serve reads and can be <b>promoted</b> to standalone primaries. '
                    'They are <b>not</b> a high-availability configuration by themselves — this distinction '
                    'is examined directly.',
                    '<b>HA = a regional instance</b> with a standby in another zone and <b>automatic '
                    'failover</b>. That is the answer to "survive a zone outage".',
                    '<b>Backups</b> are automated (a daily window) plus on-demand. <b>Point-in-time '
                    'recovery</b> needs binary logging / WAL and restores to a moment.',
                    'Connect privately with a <b>private IP</b> (via Private Service Access) or the '
                    '<b>Cloud SQL Auth Proxy</b> — the proxy is the answer to "encrypted, IAM-authorised '
                    'connections without authorising IP ranges".',
                    'Maintenance windows are configurable; a restart is required for some flag changes.',
                    'Storage can <b>auto-grow</b> but never shrink.',
                ]),
                ("panel", {"kind": "watch", "label": "REPLICA vs STANDBY vs BACKUP",
                           "text": '<b>Read replica</b> = extra read capacity. <b>Standby (HA)</b> = '
                                   'automatic failover, invisible to the application. <b>Backup</b> = a '
                                   'point you can return to. A question naming availability wants the '
                                   'standby; one naming reporting load wants the replica; one naming '
                                   'accidental deletion wants the backup.'}),
            ],
            [
                ("h", "Bigtable — the row key is the whole exam"),
                ("bul", [
                    'There is <b>one index: the row key</b>, sorted lexicographically. Queries are a single '
                    'key lookup or a <b>range scan</b>. No secondary indexes, no joins.',
                    '<b>Hotspotting</b> is the classic item: a timestamp or a sequential ID at the '
                    '<b>start</b> of the key sends every write to one tablet.',
                    'The fixes, in the order the exam offers them: <b>field promotion</b> (a '
                    'high-cardinality attribute first — '
                    '<font face="Courier" size="6.4">deviceID#timestamp</font>), <b>salting</b>, and '
                    '<b>reversing</b> a monotonically increasing value.',
                    'Scale by adding <b>nodes</b>; storage and compute scale separately, and it never '
                    'scales to zero. Use the <b>Key Visualizer</b> to see a hotspot.',
                    'Column families group columns; keep the number small and related.',
                ]),
                ("h", "Firestore and Memorystore"),
                ("bul", [
                    'Firestore is <b>document</b>-shaped with collections and subcollections, real-time '
                    'listeners, offline support and strong consistency. Queries need <b>composite '
                    'indexes</b> for multi-field filters — the usual "why is this query rejected" item.',
                    'Firestore in <b>Datastore mode</b> is the answer for server-side workloads migrating '
                    'from Datastore.',
                    'Memorystore for <b>Redis</b> gives data structures and persistence options; for '
                    '<b>Memcached</b>, a simple distributed cache. Both are in-VPC and reachable via '
                    'private IP — which is why a serverless caller needs VPC egress configured.',
                ]),
            ]]}),
    ],
})


# ==========================================================================
# Section 2 — analytics and messaging
# ==========================================================================
PAGES.append({
    "id": "d2-analytics",
    "label": "Section 2 · planning",
    "title": "BigQuery, messaging and data pipelines",
    "accent": "amber",
    "blocks": [
        ("cols", {"ratio": (50, 50), "cols": [
            [
                ("h", "BigQuery"),
                ("bul", [
                    '<b>Storage and compute are billed separately.</b> Queries are priced <b>on demand by '
                    'bytes scanned</b>, or by <b>capacity slots</b> for predictable heavy use.',
                    '<b>Scan less</b> — the standard cost answer, in order: name your columns (never '
                    '<font face="Courier" size="6.4">SELECT *</font>), <b>partition</b> by ingestion date '
                    'or a date column, <b>cluster</b> on the columns you filter by, and preview data with '
                    'the table preview rather than a query.',
                    '<b>Datasets</b> carry the <b>location</b> and the IAM; tables inherit both. Location '
                    'is fixed at creation and you cannot join across regions.',
                    'Loading is <b>free</b>; streaming inserts are not. <b>External tables</b> query files '
                    'in Cloud Storage in place — convenient, slower, and not always cheaper.',
                    '<b>Authorised views</b> and column/row-level policies let you share results without '
                    'granting access to the underlying table — the answer to "share only these columns '
                    'with the analysts".',
                    '<b>Materialised views</b> and <b>scheduled queries</b> handle recurring aggregation '
                    'without a pipeline product.',
                    '<b>Time travel</b> gives 7 days of table history — the answer to an accidental '
                    'overwrite.',
                ]),
                ("panel", {"kind": "tip", "label": "THE R1 CHECK ON PIPELINES",
                           "text": 'Before reaching for Dataflow or Composer, ask whether a '
                                   '<b>scheduled query</b> or a <b>BigQuery Data Transfer</b> job already '
                                   'does it. Reaching past a simple primitive for a heavier managed '
                                   'service is the same error as building infrastructure by hand.'}),
            ],
            [
                ("h", "Pub/Sub"),
                ("bul", [
                    'Publishers write to a <b>topic</b>; each <b>subscription</b> gets its own copy of '
                    'every message. Delivery is <b>at least once</b>, so consumers must be idempotent.',
                    '<b>Pull</b> — the consumer asks for messages. Good for batching, back-pressure and '
                    'workers that control their own rate.',
                    '<b>Push</b> — Pub/Sub POSTs to an HTTPS endpoint. Good for Cloud Run and functions, '
                    'because the endpoint scales from zero on demand. <b>The plain push subscription is '
                    'the primitive</b>; Eventarc is for routing Google Cloud <i>events</i>, not for this.',
                    'Unacknowledged messages are redelivered until the <b>retention window</b> expires '
                    '(default 7 days). The <b>ack deadline</b> controls how long a consumer has.',
                    'A <b>dead-letter topic</b> takes a message after N failed deliveries — the answer to '
                    '"stop one poison message blocking the subscription".',
                    '<b>Ordering keys</b> give per-key ordering when you need it; <b>Pub/Sub Lite</b> is '
                    'the cheaper, capacity-provisioned variant.',
                ]),
                ("h", "Processing and orchestration"),
                ("table", {"w": (30, 70), "head": ["Product", "Job"],
                           "rows": [
                               ["<b>Dataflow</b>",
                                "Managed Apache Beam — <b>the same code for streaming and batch</b> ETL. "
                                "The default answer for transforming a stream"],
                               ["<b>Dataproc</b>",
                                "Managed Spark/Hadoop. The answer when the stem says an <b>existing Spark "
                                "or Hadoop job</b> is being moved"],
                               ["<b>Cloud Composer</b>",
                                "Managed Airflow — orchestrating multi-step, multi-system workflows with "
                                "dependencies"],
                               ["<b>Workflows</b>",
                                "Lightweight serverless orchestration of API calls — cheaper than Composer "
                                "when there is no DAG to speak of"],
                               ["<b>Cloud Scheduler</b>",
                                "Managed cron → HTTP, Pub/Sub or App Engine. The answer to \"run this "
                                "every night\" with no VM"],
                               ["<b>Datastream / Data Transfer</b>",
                                "Change data capture; scheduled loads from SaaS and other clouds"],
                               ["<b>Looker / Looker Studio</b>", "The BI layer over BigQuery"],
                           ]}),
                ("panel", {"kind": "watch", "label": "DATAFLOW vs DATAPROC",
                           "text": 'Both process data at scale. <b>Dataproc</b> is the answer when '
                                   'existing Spark/Hadoop code must keep running; <b>Dataflow</b> is the '
                                   'answer for new work, for streaming, and whenever the stem says "no '
                                   'cluster to manage".'}),
            ]]}),
    ],
})


# ==========================================================================
# Ordering
# ==========================================================================
#: Reading order, grouped by exam-guide section. Coverage is deliberately
#: proportional to the published weightings (20 / 17.5 / 25 / 20 / 17.5) rather
#: than to any one reader's weak spots: four pages each for sections 1, 2, 4
#: and 5, five for the heaviest section 3.
ORDER: List[str] = [
    "start", "reflexes",
    # Section 1 — setting up (~20%)
    "hierarchy", "d1-identity", "d1-roles", "d1-billing",
    # Section 2 — planning and configuring (~17.5%)
    "compute-choice", "storage", "d2-databases", "d2-analytics",
    # Section 3 — deploying and implementing (~25%)
    "gce", "gke", "serverless", "vpc", "connect",
    # Section 4 — ensuring successful operation (~20%)
    "d4-logging", "d4-monitoring", "d4-diagnostics", "d4-resilience",
    # Section 5 — configuring access and security (~17.5%)
    "d5-iam", "d5-sa", "d5-federation", "d5-secrets",
    "final",
    "appx-a", "appx-b", "appx-c", "appx-d",
]

_by_id = {p["id"]: p for p in PAGES}
_missing = [i for i in ORDER if i not in _by_id]
_unplaced = [p["id"] for p in PAGES if p["id"] not in ORDER]
if _missing or _unplaced:
    raise AssertionError(f"ORDER mismatch — missing: {_missing}, unplaced: {_unplaced}")

PAGES[:] = [_by_id[i] for i in ORDER]

#: Theory pages carry the number printed in the header; appendix pages are
#: lettered in their label instead, so they stay outside the theory count.
for _n, _p in enumerate([p for p in PAGES if p.get("part") != "appendix"], 1):
    _p["num"] = _n


#: Short labels for the page-1 map. Full titles wrap to two lines in a narrow
#: column, which doubles the height of the map for no added information.
SHORT: Dict[str, str] = {
    "reflexes": "The eight reflexes",
    "hierarchy": "Hierarchy and IAM model",
    "d1-identity": "Identity and projects",
    "d1-roles": "Roles to know by name",
    "d1-billing": "Billing, quotas, tooling",
    "compute-choice": "Choosing compute and cost",
    "storage": "Storage, disks, transfer",
    "d2-databases": "Choosing a data store",
    "d2-analytics": "BigQuery and pipelines",
    "gce": "Compute Engine and MIGs",
    "gke": "Kubernetes Engine",
    "serverless": "Serverless and the build chain",
    "vpc": "VPC and private access",
    "connect": "Connectivity and load balancing",
    "d4-logging": "Logging and audit logs",
    "d4-monitoring": "Monitoring, alerts, SLOs",
    "d4-diagnostics": "Diagnostics and Active Assist",
    "d4-resilience": "Backup and recovery",
    "d5-iam": "IAM policies and deny",
    "d5-sa": "Service accounts",
    "d5-federation": "Keyless access, federation",
    "d5-secrets": "Secrets and encryption",
    "final": "The final card",
}


def _contents_block():
    """The page-1 map, generated from ORDER so it cannot drift out of date."""
    rows = [(p["num"], SHORT[p["id"]])
            for p in PAGES if p.get("part") != "appendix" and p["id"] != "start"]
    per = (len(rows) + 2) // 3
    cols = [[("table", {"w": (15, 85), "accent_color": None, "compact": True,
                        "head": ["#", "Topic"],
                        "rows": [[f"<b>{n}</b>", t] for n, t in rows[i:i + per]]})]
            for i in range(0, len(rows), per)]
    return ("cols", {"ratio": (1, 1, 1), "gutter": 8, "cols": cols})


_start = PAGES[0]
_blocks = []
for k, v in _start["blocks"]:
    if k == "__contents__":
        _blocks.append(_contents_block())
        _blocks.append(
            ("p", '<b>Appendix A–D</b> is the <font face="Courier">gcloud</font> reference and sits '
                  'outside the theory count — skim it once; do not try to memorise it.'))
    else:
        _blocks.append((k, v))
_start["blocks"] = _blocks
