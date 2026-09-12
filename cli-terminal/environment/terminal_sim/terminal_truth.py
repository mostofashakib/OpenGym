"""Ground truth definitions and constants for terminal environment verification."""

from __future__ import annotations

TARGET_PID = 4921
TARGET_PROCESS_NAME = "python3"
TARGET_PROCESS_CMD = "worker-leak.py"

TARGET_LOG_PATH = "/var/log/app/debug_trace.log"
TARGET_CONFIG_PATH = "/etc/payment-processor/config.yaml"
TARGET_KEY_PATH = "/etc/ssl/certs/payment-api.key"
TARGET_SERVICE_NAME = "payment-processor"

EXPECTED_DB_HOST = "db-primary.internal"
EXPECTED_DB_PORT = 5432
EXPECTED_KEY_PERMISSIONS = {"0600", "0400", "600", "400"}

# Required milestones for grading progression
MILESTONES = (
    "rogue_process_identified",
    "rogue_process_killed",
    "disk_space_reclaimed",
    "config_database_repaired",
    "private_key_secured",
    "service_restarted_active",
    "remediation_report_submitted",
)
