"""Seed corpus and bundled scenario for the task-tracker world.

This module is the deterministic generator: it defines the rows written into
SQLite, which is the single source of truth for state. No parallel in-memory
state is built from these constants.

Everything the workspace starts with is here, including the two design tasks a
previous revision created from the Dockerfile after seeding. Building the
initial state in one place is what lets `seed_database` be the only path to a
workspace and lets two reseeds produce byte-identical snapshots.
"""

from __future__ import annotations

from task_sim.clock import ONE_DAY_MS, START_MS
from task_sim.models import (
    LatentComment,
    LatentDependency,
    LatentTask,
    ScenarioEvent,
    ScenarioRule,
)
from task_sim.scenario import Scenario

# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

TRACKER_USERS = [
    ("U001", "Avery Chen",    "avery@example.local",   "admin",  "research",    "avery"),
    ("U002", "Morgan Patel",  "morgan@example.local",  "member", "product",     "morgan"),
    ("U003", "Riley Stone",   "riley@example.local",   "member", "engineering", "riley"),
    ("U004", "Jordan Kim",    "jordan@example.local",  "member", "design",      "jordan"),
    ("U005", "Sam Wu",        "sam@example.local",     "member", "platform",    "sam"),
    ("U006", "Alex Rivera",   "alex@example.local",    "admin",  "engineering", "alex"),
    ("U007", "Elena Rostova", "elena@example.local",   "member", "sre",         "elena"),
    ("U008", "Marcus Vance",  "marcus@example.local",  "member", "security",    "marcus"),
    ("U009", "Priya Sharma",  "priya@example.local",   "admin",  "release",     "priya"),
    ("U010", "Devon Reed",    "devon@example.local",   "member", "qa",          "devon"),
]

# ---------------------------------------------------------------------------
# Projects  (project_id, name, description, owner_id, step, archived)
# ---------------------------------------------------------------------------

TRACKER_PROJECTS = [
    ("P001", "ML Platform v2",          "Next-gen ML compute and serving infrastructure.",                     "U001", 1, False),
    ("P002", "Agent Eval Framework",    "Deterministic evaluation framework for LLM agents.",                  "U002", 2, False),
    ("P003", "Infrastructure Overhaul", "Platform reliability and scalability improvements.",                  "U006", 3, False),
    ("P004", "Product Dashboard",       "User-facing analytics and reporting dashboard.",                      "U002", 4, False),
    ("P005", "Titanium Enterprise v3.0","Core enterprise platform upgrade with zero-trust auth and cache bus.","U009", 5, False),
]

# ---------------------------------------------------------------------------
# Milestones  (milestone_id, project_id, title, description, due_at_ms, step)
# ---------------------------------------------------------------------------

TRACKER_MILESTONES = [
    ("M001", "P001", "Alpha Release",       "First public alpha of ML Platform v2.",                  START_MS + 60 * ONE_DAY_MS, 5),
    ("M002", "P001", "Beta Release",        "Feature-complete beta with performance baseline.",       START_MS + 90 * ONE_DAY_MS, 6),
    ("M003", "P002", "v1.0 Launch",         "Production-ready eval framework release.",               START_MS + 45 * ONE_DAY_MS, 7),
    ("M004", "P003", "Phase 1 Complete",    "Core infrastructure hardening -- already overdue.",      START_MS -  5 * ONE_DAY_MS, 8),
    ("M005", "P004", "Q1 Goals",            "All Q1 product deliverables shipped -- already overdue.", START_MS - 10 * ONE_DAY_MS, 9),
    ("M006", "P005", "v3.0 Cutover Gate",   "Release blocker gate for enterprise production cutover.", START_MS +  2 * ONE_DAY_MS, 10),
    ("M007", "P005", "v3.1 Post-Launch",    "Follow-up enhancements and non-critical refactors.",      START_MS + 30 * ONE_DAY_MS, 11),
]

# ---------------------------------------------------------------------------
# Tasks
# (task_id, title, description, creator_id, assignee_id, status,
#  project_id, milestone_id, due_at_ms, priority, labels, step)
# ---------------------------------------------------------------------------

TRACKER_TASKS = [
    # -- Agent Eval Framework (P002) ----------------------------------------
    (
        "TASK001", "Draft benchmark plan",
        "Create a deterministic task matrix for provider comparison.",
        "U001", None, "PENDING",
        "P002", "M003", None, "HIGH", (), 1,
    ),
    (
        "TASK002", "Review tool schemas",
        "Confirm tool contracts are stable and versioned.",
        "U002", "U003", "IN_PROGRESS",
        "P002", "M003", None, "MEDIUM", (), 2,
    ),
    (
        "TASK006", "Write API documentation",
        "Document all REST endpoints in standard API schema format.",
        "U002", "U004", "PENDING",
        "P002", "M003", None, "LOW", ("docs",), 6,
    ),
    (
        "TASK012", "Agent trajectory logger",
        "Log full ATIF-v1.7 trajectories to structured storage.",
        "U001", "U001", "COMPLETED",
        "P002", "M003", None, "HIGH", ("eval",), 12,
    ),
    (
        "TASK013", "Benchmark provider A",
        "Run full eval suite against provider A. Blocked until plan and logger are done.",
        "U001", "U003", "PENDING",
        "P002", "M003", None, "MEDIUM", ("eval", "benchmark"), 13,
    ),
    (
        "TASK014", "Benchmark provider B",
        "Run full eval suite against provider B. Blocked until plan and logger are done.",
        "U001", "U002", "PENDING",
        "P002", "M003", None, "MEDIUM", ("eval", "benchmark"), 14,
    ),
    (
        "TASK023", "Review tool schemas v2",
        "Second-pass schema review for agent tool contracts.",
        "U002", None, "PENDING",
        "P002", "M003", None, "LOW", ("docs",), 23,
    ),
    (
        "TASK029", "Update API contracts",
        "Align REST and gRPC contracts after schema changes.",
        "U002", "U003", "BLOCKED",
        "P002", "M003", None, "HIGH", ("backend", "api"), 29,
    ),
    # -- ML Platform v2 (P001) ----------------------------------------------
    (
        "TASK004", "Design database schema",
        "Model entity relationships for the ML platform.",
        "U001", "U003", "COMPLETED",
        "P001", "M001", None, "URGENT", ("backend", "database"), 4,
    ),
    (
        "TASK010", "ML model pipeline",
        "Build distributed processing pipeline with checkpointing.",
        "U001", "U003", "PENDING",
        "P001", "M001", None, "URGENT", ("ml", "backend"), 10,
    ),
    (
        "TASK015", "Data pipeline refactor",
        "Migrate ETL jobs from Airflow 1.x to Airflow 2.x.",
        "U001", "U005", "BLOCKED",
        "P001", "M002", None, "HIGH", ("backend", "data"), 15,
    ),
    (
        "TASK027", "Performance optimization",
        "Profile and reduce P99 inference latency by 30%.",
        "U001", "U005", "IN_PROGRESS",
        "P001", "M002", None, "HIGH", ("backend", "perf"), 27,
    ),
    # -- Infrastructure Overhaul (P003) -------------------------------------
    (
        "TASK003", "Set up CI pipeline",
        "Configure GitHub Actions for automated testing.",
        "U006", "U005", "COMPLETED",
        "P003", "M004", None, "HIGH", ("infra", "devops"), 3,
    ),
    (
        "TASK005", "Implement auth service",
        "Build JWT-based authentication with role management.",
        "U006", "U003", "IN_PROGRESS",
        "P003", "M004", START_MS - 3 * ONE_DAY_MS, "HIGH", ("backend", "security"), 5,
    ),
    (
        "TASK007", "Set up monitoring dashboards",
        "Create Grafana dashboards for service health. Blocked on auth service.",
        "U006", "U005", "BLOCKED",
        "P003", "M004", None, "MEDIUM", ("infra",), 7,
    ),
    (
        "TASK011", "Feature flag service",
        "Implement feature flag evaluation with targeting rules.",
        "U006", "U005", "IN_PROGRESS",
        "P003", None, None, "HIGH", ("backend", "platform"), 11,
    ),
    (
        "TASK016", "Deploy to staging",
        "Promote auth service and feature flags to staging environment.",
        "U006", "U005", "PENDING",
        "P003", "M004", START_MS - 2 * ONE_DAY_MS, "URGENT", ("infra", "devops"), 16,
    ),
    (
        "TASK017", "Load testing",
        "Run k6 load tests against staging with 10k concurrent users.",
        "U006", "U005", "PENDING",
        "P003", None, None, "MEDIUM", ("infra",), 17,
    ),
    (
        "TASK020", "Security audit",
        "Third-party pen test and code review for P003 services.",
        "U006", None, "PENDING",
        "P003", None, None, "URGENT", ("security",), 20,
    ),
    (
        "TASK021", "Notification service",
        "Push/email notification delivery pipeline.",
        "U006", "U005", "CANCELLED",
        "P003", None, None, "LOW", ("backend",), 21,
    ),
    (
        "TASK028", "Add rate limiting",
        "Implement per-user rate limiting on all API endpoints.",
        "U006", "U003", "PENDING",
        "P003", None, None, "MEDIUM", ("backend", "security"), 28,
    ),
    # -- Product Dashboard (P004) -------------------------------------------
    (
        "TASK008", "User research interviews",
        "Conduct 10 interviews with target users.",
        "U002", "U004", "COMPLETED",
        "P004", "M005", None, "MEDIUM", ("research", "ux"), 8,
    ),
    (
        "TASK009", "Create wireframes",
        "Design lo-fi and hi-fi wireframes for dashboard views.",
        "U004", "U004", "IN_PROGRESS",
        "P004", "M005", None, "HIGH", ("design", "ux"), 9,
    ),
    (
        "TASK018", "Product onboarding flow",
        "Implement step-by-step onboarding for new users.",
        "U002", "U003", "IN_PROGRESS",
        "P004", "M005", None, "HIGH", ("frontend", "ux"), 18,
    ),
    (
        "TASK019", "Analytics integration",
        "Integrate Mixpanel events into the dashboard backend.",
        "U002", "U002", "PENDING",
        "P004", None, None, "LOW", ("backend", "analytics"), 19,
    ),
    (
        "TASK022", "Mobile app setup",
        "Initialize React Native project with navigation and auth stubs.",
        "U004", None, "PENDING",
        "P004", None, None, "MEDIUM", ("mobile",), 22,
    ),
    (
        "TASK026", "Fix login redirect bug",
        "POST /login redirecting to 404 on first sign-in.",
        "U003", "U003", "COMPLETED",
        "P004", "M005", None, "HIGH", ("frontend", "bug"), 26,
    ),
    # Jordan's two design tasks. TASK031 is the only one of the five with no
    # milestone, which is what makes the instruction's branch a real decision
    # rather than a bulk update.
    (
        "TASK031", "Component design tokens",
        "Define and document the design token system for the dashboard component library.",
        "U004", "U004", "PENDING",
        "P004", None, None, "MEDIUM", ("design", "frontend"), 31,
    ),
    (
        "TASK032", "Brand refresh mockups",
        "High-fidelity mockups applying brand refresh guidelines to all dashboard views.",
        "U004", "U004", "PENDING",
        "P004", "M005", None, "MEDIUM", ("design",), 32,
    ),
    # -- Stale / closed tasks (distractors) ---------------------------------
    (
        "TASK024", "Draft benchmark plan (stale)",
        "Outdated copy of benchmark plan. Superseded by TASK001.",
        "U001", None, "ARCHIVED",
        "P002", None, None, "LOW", (), 24,
    ),
    (
        "TASK025", "Legacy data migration",
        "One-time migration of v1 data to new schema. Duplicate of existing effort.",
        "U001", None, "DUPLICATE",
        "P001", None, None, "LOW", ("data",), 25,
    ),
    # -- Cross-project / unassigned -----------------------------------------
    (
        "TASK030", "Quarterly review rollup",
        "Compile cross-team Q4 progress report for leadership.",
        "U001", None, "PENDING",
        None, None, None, "LOW", ("admin",), 30,
    ),
    # -- Titanium Enterprise v3.0 (P005) ------------------------------------
    (
        "TASK033", "Titanium v3 release blocker triage",
        "Audit all cutover blockers across security, SRE, and platform before production deployment.",
        "U009", "U009", "IN_PROGRESS",
        "P005", "M006", START_MS + 1 * ONE_DAY_MS, "URGENT", ("release", "cutover"), 33,
    ),
    (
        "TASK034", "Audit TLS 1.3 cipher suites",
        "Verify cipher suite negotiation and deprecate legacy CBC modes across gateway ingresses.",
        "U008", "U008", "COMPLETED",
        "P005", "M006", None, "HIGH", ("security",), 34,
    ),
    (
        "TASK035", "SOC2 compliance audit gate",
        "Final compliance audit signoff. Blocked on third-party vendor security attestation (TASK047).",
        "U008", "U008", "BLOCKED",
        "P005", "M006", START_MS + 1 * ONE_DAY_MS, "URGENT", ("compliance", "security"), 35,
    ),
    (
        "TASK036", "Distributed cache invalidation",
        "Fix distributed cache cluster invalidation bus and connection pool eviction.",
        "U007", "U007", "IN_PROGRESS",
        "P005", "M006", None, "HIGH", ("sre", "cache"), 36,
    ),
    (
        "TASK037", "Database schema migration v3",
        "Execute zero-downtime partitioning and index migration on production customer tables.",
        "U003", "U003", "COMPLETED",
        "P005", "M006", None, "URGENT", ("database",), 37,
    ),
    (
        "TASK038", "Pre-cutover data replication check",
        "Verify cross-region read replica lag remains below 10ms during burst traffic.",
        "U007", "U007", "BLOCKED",
        "P005", "M006", START_MS + 2 * ONE_DAY_MS, "HIGH", ("sre", "database"), 38,
    ),
    (
        "TASK039", "Zero-trust session token revocation",
        "Implement instantaneous token revocation on tenant privilege boundary changes.",
        "U005", "U005", "IN_PROGRESS",
        "P005", "M006", None, "HIGH", ("security", "auth"), 39,
    ),
    (
        "TASK040", "Staging end-to-end integration suite",
        "Run comprehensive integration suite in pre-production staging environment.",
        "U010", "U010", "BLOCKED",
        "P005", "M006", START_MS + 2 * ONE_DAY_MS, "HIGH", ("qa", "release"), 40,
    ),
    (
        "TASK041", "Canary deployment pipeline",
        "Configure automated canary analysis with 1% traffic step-up and rollback triggers.",
        "U007", "U007", "COMPLETED",
        "P005", "M006", None, "HIGH", ("infra", "devops"), 41,
    ),
    (
        "TASK042", "Token revocation race condition under load",
        "Concurrency race condition detected during simultaneous refresh and revoke requests.",
        "U009", "U005", "PENDING",
        "P005", "M006", None, "HIGH", ("bug", "auth"), 42,
    ),
    (
        "TASK043", "Backup verification and recovery drill",
        "Execute simulated disaster recovery failover drill using production snapshot copies.",
        "U007", "U007", "BLOCKED",
        "P005", "M006", START_MS + 1 * ONE_DAY_MS, "URGENT", ("sre", "dr"), 43,
    ),
    (
        "TASK044", "Snapshot rollback automation script",
        "Build idempotent rollback automation script for instant volume restores.",
        "U007", "U007", "BLOCKED",
        "P005", "M006", None, "URGENT", ("sre", "automation"), 44,
    ),
    (
        "TASK045", "Customer maintenance notification banner",
        "Publish schedule maintenance banner on customer support portal and status page.",
        "U002", "U002", "COMPLETED",
        "P005", "M006", None, "LOW", ("product",), 45,
    ),
    (
        "TASK046", "API gateway rate limiter sync",
        "Synchronize Redis sliding window rate limits across multi-region edge gateways.",
        "U003", "U003", "PENDING",
        "P005", "M006", None, "MEDIUM", ("backend", "network"), 46,
    ),
    (
        "TASK047", "Third-party vendor security attestation",
        "Collect independent SOC2 Type II audit report and penetration testing attestation.",
        "U008", "U008", "COMPLETED",
        "P005", "M006", None, "HIGH", ("security", "audit"), 47,
    ),
    (
        "TASK048", "Disaster recovery runbook validation",
        "Peer review and operational validation of cutover and rollback step-by-step procedures.",
        "U009", "U009", "BLOCKED",
        "P005", "M006", None, "HIGH", ("runbook", "release"), 48,
    ),
    (
        "TASK049", "Telemetry dashboard alerting rules",
        "Set up PromQL alerting rules for P99 latency, error rate spikes, and pod restarts.",
        "U007", "U007", "COMPLETED",
        "P005", "M006", None, "MEDIUM", ("infra", "observability"), 49,
    ),
    (
        "TASK050", "Load balancer healthcheck tuning",
        "Tune keep-alive timeout and health check threshold for zero connection drops.",
        "U005", "U005", "COMPLETED",
        "P005", "M006", None, "LOW", ("infra",), 50,
    ),
    (
        "TASK051", "Redis connection pool timeout spike",
        "Intermittent connection timeout exceptions observed in cache cluster during load bursts.",
        "U007", "U007", "PENDING",
        "P005", "M006", None, "HIGH", ("bug", "cache"), 51,
    ),
    (
        "TASK052", "Cache cluster pool exhaustion bug",
        "QA discovered pool exhaustion causing 504 gateway timeouts under simulated traffic.",
        "U003", "U003", "PENDING",
        "P005", "M006", None, "HIGH", ("bug", "cache"), 52,
    ),
    (
        "TASK053", "Post-release dark launch toggle",
        "Dark launch feature gate configuration for enterprise reporting dashboard.",
        "U002", "U002", "PENDING",
        "P005", "M007", None, "LOW", ("feature-flag",), 53,
    ),
    (
        "TASK054", "Non-critical GraphQL query optimization",
        "Optimize nested query resolution for tenant settings page.",
        "U003", "U003", "PENDING",
        "P005", "M007", None, "LOW", ("backend", "perf"), 54,
    ),
    (
        "TASK055", "Update user onboarding tour copy",
        "Refresh in-app guide text and tooltips for updated enterprise navigation layout.",
        "U002", "U002", "PENDING",
        "P005", "M007", None, "LOW", ("ux", "docs"), 55,
    ),
]

# ---------------------------------------------------------------------------
# Assignments  (assignment_id, task_id, user_id, assigned_by, step)
# ---------------------------------------------------------------------------

TRACKER_ASSIGNMENTS = [
    ("ASSIGN001", "TASK002", "U003", "U002",  3),
    ("ASSIGN002", "TASK003", "U005", "U006",  4),
    ("ASSIGN003", "TASK004", "U003", "U001",  5),
    ("ASSIGN004", "TASK005", "U003", "U006",  6),
    ("ASSIGN005", "TASK006", "U004", "U002",  7),
    ("ASSIGN006", "TASK007", "U005", "U006",  8),
    ("ASSIGN007", "TASK008", "U004", "U002",  9),
    ("ASSIGN008", "TASK009", "U004", "U004", 10),
    ("ASSIGN009", "TASK010", "U003", "U001", 11),
    ("ASSIGN010", "TASK011", "U005", "U006", 12),
    ("ASSIGN011", "TASK012", "U001", "U001", 13),
    ("ASSIGN012", "TASK013", "U003", "U001", 14),
    ("ASSIGN013", "TASK014", "U002", "U001", 15),
    ("ASSIGN014", "TASK015", "U005", "U001", 16),
    ("ASSIGN015", "TASK016", "U005", "U006", 17),
    ("ASSIGN016", "TASK017", "U005", "U006", 18),
    ("ASSIGN017", "TASK018", "U003", "U002", 19),
    ("ASSIGN018", "TASK019", "U002", "U002", 20),
    ("ASSIGN019", "TASK026", "U003", "U003", 27),
    ("ASSIGN020", "TASK027", "U005", "U001", 28),
    ("ASSIGN021", "TASK028", "U003", "U006", 29),
    ("ASSIGN022", "TASK029", "U003", "U002", 30),
    ("ASSIGN023", "TASK031", "U004", "U004", 31),
    ("ASSIGN024", "TASK032", "U004", "U004", 32),
    ("ASSIGN025", "TASK033", "U009", "U009", 33),
    ("ASSIGN026", "TASK034", "U008", "U008", 34),
    ("ASSIGN027", "TASK035", "U008", "U008", 35),
    ("ASSIGN028", "TASK036", "U007", "U007", 36),
    ("ASSIGN029", "TASK037", "U003", "U003", 37),
    ("ASSIGN030", "TASK038", "U007", "U007", 38),
    ("ASSIGN031", "TASK039", "U005", "U005", 39),
    ("ASSIGN032", "TASK040", "U010", "U010", 40),
    ("ASSIGN033", "TASK041", "U007", "U007", 41),
    ("ASSIGN034", "TASK042", "U005", "U009", 42),
    ("ASSIGN035", "TASK043", "U007", "U007", 43),
    ("ASSIGN036", "TASK044", "U007", "U007", 44),
    ("ASSIGN037", "TASK045", "U002", "U002", 45),
    ("ASSIGN038", "TASK046", "U003", "U003", 46),
    ("ASSIGN039", "TASK047", "U008", "U008", 47),
    ("ASSIGN040", "TASK048", "U009", "U009", 48),
    ("ASSIGN041", "TASK049", "U007", "U007", 49),
    ("ASSIGN042", "TASK050", "U005", "U005", 50),
    ("ASSIGN043", "TASK051", "U007", "U007", 51),
    ("ASSIGN044", "TASK052", "U003", "U003", 52),
    ("ASSIGN045", "TASK053", "U002", "U002", 53),
    ("ASSIGN046", "TASK054", "U003", "U003", 54),
    ("ASSIGN047", "TASK055", "U002", "U002", 55),
]

# ---------------------------------------------------------------------------
# Dependencies  (dep_id, task_id, depends_on_task_id)
# task_id is blocked until depends_on_task_id is COMPLETED.
# ---------------------------------------------------------------------------

TRACKER_DEPENDENCIES = [
    ("DEP001", "TASK005", "TASK003"),   # auth service needs CI pipeline
    ("DEP002", "TASK007", "TASK005"),   # monitoring needs auth service
    ("DEP003", "TASK009", "TASK008"),   # wireframes need research interviews
    ("DEP004", "TASK013", "TASK001"),   # benchmark A needs plan
    ("DEP005", "TASK013", "TASK012"),   # benchmark A needs trajectory logger
    ("DEP006", "TASK014", "TASK001"),   # benchmark B needs plan
    ("DEP007", "TASK014", "TASK012"),   # benchmark B needs trajectory logger
    ("DEP008", "TASK016", "TASK005"),   # staging deploy needs auth service
    ("DEP009", "TASK016", "TASK011"),   # staging deploy needs feature flags
    ("DEP010", "TASK017", "TASK016"),   # load testing needs staging deploy
    ("DEP011", "TASK018", "TASK009"),   # onboarding flow needs wireframes
    ("DEP012", "TASK028", "TASK005"),   # rate limiting needs auth service
    ("DEP013", "TASK029", "TASK002"),   # API contracts need schema review
    ("DEP014", "TASK038", "TASK037"),   # replication check needs schema migration
    ("DEP015", "TASK038", "TASK036"),   # replication check needs cache invalidation
    ("DEP016", "TASK035", "TASK047"),   # SOC2 gate needs vendor attestation
    ("DEP017", "TASK040", "TASK039"),   # staging suite needs token revocation
    ("DEP018", "TASK043", "TASK044"),   # recovery drill needs rollback script
    ("DEP019", "TASK044", "TASK048"),   # CIRCULAR: rollback script depends on runbook validation
    ("DEP020", "TASK048", "TASK044"),   # CIRCULAR: runbook validation depends on rollback script
    ("DEP021", "TASK040", "TASK042"),   # staging suite blocked by race condition
]


# ---------------------------------------------------------------------------
# Comments  (comment_id, task_id, author_id, content, step)
# ---------------------------------------------------------------------------

TRACKER_COMMENTS = [
    ("CMT001", "TASK035", "U002", "Attached vendor SOC2 Type II report for auth provider. Attestation recorded under TASK047. Waiting for release lead sign-off.", 12),
    ("CMT002", "TASK042", "U003", "Intermittent token invalidation failure detected under concurrency in staging cluster. Need Marcus Vance (U008) to apply mutex lock patch.", 15),
    ("CMT003", "TASK044", "U007", "Rollback automation script completed and tested against staging backup snapshot.", 18),
    ("CMT004", "TASK048", "U001", "Runbook steps validated against disaster recovery staging cluster. Waiting for circular link resolution to mark complete.", 20),
    ("CMT005", "TASK051", "U005", "Identical symptoms to TASK036 redis eviction bug. Recommend deduplicating.", 22),
    ("CMT006", "TASK052", "U006", "Duplicate report of cache cluster invalidation TASK036.", 25),
    ("CMT007", "TASK040", "U001", "Staging suite waiting for rollback automation and DR runbook before executing dry-run rehearsal.", 28),
]


# ---------------------------------------------------------------------------
# Titanium v3 Enterprise Release Reconciliation Scenario
# ---------------------------------------------------------------------------

RELEASE_PROJECT = "P005"
CUTOVER_MILESTONE = "M006"
AUDIT_TASKS = (
    "TASK033", "TASK034", "TASK035", "TASK036", "TASK037", "TASK038",
    "TASK039", "TASK040", "TASK041", "TASK042", "TASK043", "TASK044",
    "TASK045", "TASK046", "TASK047", "TASK048", "TASK049", "TASK050",
    "TASK051", "TASK052",
)
RECONCILIATION_TARGET_TASKS = (
    "TASK035", "TASK042", "TASK044", "TASK048", "TASK051", "TASK052",
    "TASK056", "TASK057", "TASK058",
)

RELEASE_RECONCILIATION_EVENTS = (
    ScenarioEvent("release_audit_inspected", "The agent enumerated and inspected Titanium v3 cutover tasks."),
    ScenarioEvent("circular_dep_broken", "The circular dependency between TASK048 and TASK044 was unlinked."),
    ScenarioEvent("task048_completed", "Disaster recovery runbook validation (TASK048) was marked COMPLETED."),
    ScenarioEvent("task044_completed", "Snapshot rollback automation script (TASK044) was marked COMPLETED."),
    ScenarioEvent("compliance_unblocked", "SOC2 compliance audit gate (TASK035) was marked COMPLETED after verifying vendor attestation."),
    ScenarioEvent("race_reassigned", "Token revocation race condition (TASK042) was assigned to Marcus Vance (U008) with URGENT priority."),
    ScenarioEvent("task051_deduplicated", "TASK051 was marked duplicate of TASK036."),
    ScenarioEvent("task052_deduplicated", "TASK052 was marked duplicate of TASK036."),
    ScenarioEvent("rehearsal_dryrun_failed", "Staging dry-run rehearsal detected EU-Central replica sync lag (ERR_REP_LAG_4200)."),
    ScenarioEvent("replica_patch_available", "Agent inspected TASK056, surfacing Elena's replica synchronization fix."),
    ScenarioEvent("task056_resolved", "Replication lag ticket (TASK056) was marked COMPLETED."),
    ScenarioEvent("task057_resolved", "HSM encryption key rotation audit ticket (TASK057) was marked COMPLETED."),
    ScenarioEvent("final_rehearsal_executed", "Final rehearsal executed and external PayCore EU payment maintenance conflict announced."),
    ScenarioEvent("external_blocker_inspected", "The agent discovered and inspected the external PayCore EU maintenance blocker (TASK058)."),
    ScenarioEvent("handover_reported", "A terminal handover report was submitted."),
    ScenarioEvent("reconciliation_complete", "All Titanium v3 cutover blockers were reconciled and verified."),
)

RELEASE_RECONCILIATION_LATENT_TASKS = (
    LatentTask(
        task_id="TASK056",
        event_id="rehearsal_dryrun_failed",
        title="Resolve EU-Central replica sync lag under cache warm-up",
        description="Staging cutover dry-run failed at step 4/7: replication lag spiked to 4,200ms during cache warm-up (ERR_REP_LAG_4200). Elena Rostova investigating database batch chunk size.",
        creator_id="U001",
        assignee_id="U007",
        status="IN_PROGRESS",
        project_id="P005",
        milestone_id="M006",
        priority="HIGH",
        labels=("database", "release-blocker"),
    ),
    LatentTask(
        task_id="TASK057",
        event_id="rehearsal_dryrun_failed",
        title="Verify HSM encryption key rotation audit trail",
        description="SOC2 CC6.8 audit requirement for production cutover sign-off. Cross-reference with KMS key rotation schedule.",
        creator_id="U002",
        assignee_id="U002",
        status="PENDING",
        project_id="P005",
        milestone_id="M006",
        priority="MEDIUM",
        labels=("compliance", "security"),
    ),
    LatentTask(
        task_id="TASK058",
        event_id="final_rehearsal_executed",
        title="PayCore EU payment gateway unscheduled maintenance overlap",
        description="Upstream payment provider PayCore EU announced emergency unscheduled maintenance for Thursday 22:00-02:00 UTC, overlapping completely with the Titanium v3 cutover window. In-flight payment authorizations will fail during this period.",
        creator_id="U001",
        assignee_id="U001",
        status="BLOCKED",
        project_id="P005",
        milestone_id="M006",
        priority="URGENT",
        labels=("upstream", "external-blocker"),
    ),
)

RELEASE_RECONCILIATION_LATENT_DEPS = (
    LatentDependency("DEP030", "rehearsal_dryrun_failed", "TASK043", "TASK056"),
    LatentDependency("DEP031", "rehearsal_dryrun_failed", "TASK040", "TASK057"),
    LatentDependency("DEP032", "final_rehearsal_executed", "TASK040", "TASK058"),
)

RELEASE_RECONCILIATION_LATENT_COMMENTS = (
    LatentComment(
        comment_id="CMT010",
        event_id="rehearsal_dryrun_failed",
        task_id="TASK040",
        author_id="U001",
        content="AUTOMATED CI/CD ALERT: Staging cutover dry-run failed at Step 4/7: Database replication lag on EU-Central read replica spiked to 4,200ms during cache warm-up (ERR_REP_LAG_4200). Threshold is <500ms. Release blocked.",
        created_step=35,
    ),
    LatentComment(
        comment_id="CMT011",
        event_id="rehearsal_dryrun_failed",
        task_id="TASK035",
        author_id="U002",
        content="COMPLIANCE NOTICE: Vendor attestation verified, but SOC2 CC6.8 requires confirmation of the secondary HSM encryption key rotation audit ticket before production cutover.",
        created_step=35,
    ),
    LatentComment(
        comment_id="CMT012",
        event_id="replica_patch_available",
        task_id="TASK056",
        author_id="U007",
        content="Elena Rostova: Identified batch flush bottleneck in db_pool.py. Hotfix patch committed to branch release-v3.0. Rehearsal test in staging shows lag dropped to 85ms. Release lead: please review staging test results, post an approval comment on this ticket confirming the lag threshold (<500ms) is satisfied, and mark COMPLETED so final dry-run can proceed.",
        created_step=40,
    ),
    LatentComment(
        comment_id="CMT013",
        event_id="final_rehearsal_executed",
        task_id="TASK040",
        author_id="U001",
        content="STAGING DRILL SUCCESS: Internal dry-run rehearsal passed 7/7 steps. Recovery drill verified.",
        created_step=45,
    ),
    LatentComment(
        comment_id="CMT014",
        event_id="final_rehearsal_executed",
        task_id="TASK058",
        author_id="U001",
        content="CRITICAL EXTERNAL BLOCKER: PayCore EU maintenance cannot be rescheduled. Cutover at Thursday 22:00 UTC will cause customer-visible payment processing failures. Release MUST be held (NO-GO / BLOCKED) until a new cutover window is agreed.",
        created_step=46,
    ),
)

RELEASE_RECONCILIATION_RULES = (
    ScenarioRule(
        "rel_r010_audit", "release_audit_inspected", "observed",
        observed_ids=("TASK035", "TASK044", "TASK048"),
    ),
    ScenarioRule(
        "rel_r020_unlink", "circular_dep_broken", "tool_called",
        tools=("unlink_tasks",),
    ),
    ScenarioRule(
        "rel_r030_task048", "task048_completed", "field_equals",
        table="tasks", row_id="TASK048", field="status", value="COMPLETED",
    ),
    ScenarioRule(
        "rel_r031_task044", "task044_completed", "field_equals",
        table="tasks", row_id="TASK044", field="status", value="COMPLETED",
    ),
    ScenarioRule(
        "rel_r032_task035", "compliance_unblocked", "field_equals",
        table="tasks", row_id="TASK035", field="status", value="COMPLETED",
    ),
    ScenarioRule(
        "rel_r033_task042", "race_reassigned", "field_equals",
        table="tasks", row_id="TASK042", field="assignee_id", value="U008",
    ),
    ScenarioRule(
        "rel_r034_task051", "task051_deduplicated", "field_equals",
        table="tasks", row_id="TASK051", field="status", value="DUPLICATE",
    ),
    ScenarioRule(
        "rel_r035_task052", "task052_deduplicated", "field_equals",
        table="tasks", row_id="TASK052", field="status", value="DUPLICATE",
    ),
    ScenarioRule(
        "rel_r040_rehearsal_fail", "rehearsal_dryrun_failed", "all_of",
        requires_activated=("task044_completed", "task048_completed", "compliance_unblocked"),
    ),
    ScenarioRule(
        "rel_r050_replica_patch", "replica_patch_available", "observed",
        observed_ids=("TASK056",),
        requires_activated=("rehearsal_dryrun_failed",),
    ),
    ScenarioRule(
        "rel_r051_task056_done", "task056_resolved", "field_equals",
        table="tasks", row_id="TASK056", field="status", value="COMPLETED",
        requires_activated=("replica_patch_available",),
    ),
    ScenarioRule(
        "rel_r052_task057_done", "task057_resolved", "field_equals",
        table="tasks", row_id="TASK057", field="status", value="COMPLETED",
        requires_activated=("rehearsal_dryrun_failed",),
    ),
    ScenarioRule(
        "rel_r060_final_rehearsal", "final_rehearsal_executed", "all_of",
        requires_activated=("task056_resolved", "task057_resolved"),
    ),
    ScenarioRule(
        "rel_r065_blocker_inspected", "external_blocker_inspected", "observed",
        observed_ids=("TASK058",),
        requires_activated=("final_rehearsal_executed",),
    ),
    ScenarioRule(
        "rel_r070_report", "handover_reported", "tool_called",
        tools=("submit_handover_report",),
    ),
    ScenarioRule(
        "rel_r080_complete", "reconciliation_complete", "all_of",
        requires_activated=(
            "release_audit_inspected", "circular_dep_broken",
            "task048_completed", "task044_completed", "compliance_unblocked",
            "race_reassigned", "task051_deduplicated", "task052_deduplicated",
            "rehearsal_dryrun_failed", "replica_patch_available",
            "task056_resolved", "task057_resolved",
            "final_rehearsal_executed", "external_blocker_inspected",
            "handover_reported",
        ),
    ),
)

RELEASE_RECONCILIATION_SCENARIO = Scenario(
    events=RELEASE_RECONCILIATION_EVENTS,
    rules=RELEASE_RECONCILIATION_RULES,
    latent_tasks=RELEASE_RECONCILIATION_LATENT_TASKS,
    latent_dependencies=RELEASE_RECONCILIATION_LATENT_DEPS,
    latent_comments=RELEASE_RECONCILIATION_LATENT_COMMENTS,
    observation_only=("release_audit_inspected", "replica_patch_available", "reconciliation_complete"),
)



