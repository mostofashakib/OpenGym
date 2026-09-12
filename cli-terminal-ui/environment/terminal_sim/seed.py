"""High-fidelity seed data for the terminal environment."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from terminal_sim.clock import VIRTUAL_CLOCK
from terminal_sim.sqlite_common import init_db

CONFIG_YAML_BROKEN = """# Production Payment Processing Service Configuration
# Managed by Infrastructure Team -- Do not edit manually without review.

server:
  host: 0.0.0.0
  port: 8080
  workers: 4
  keepalive_timeout: 65

database:
  host: db-replica-invalid.internal
  port: 9999
  name: payments_prod
  user: payments_app
  pool_size: 25
  max_overflow: 10
  timeout_seconds: 5

security:
  ssl_enabled: true
  private_key: /etc/ssl/certs/payment-api.key
  cert_file: /etc/ssl/certs/payment-api.crt
  token_expiry_hours: 24

telemetry:
  log_level: DEBUG
  metrics_port: 9100
"""

CONFIG_YAML_CORRECT = """# Production Payment Processing Service Configuration
# Managed by Infrastructure Team -- Do not edit manually without review.

server:
  host: 0.0.0.0
  port: 8080
  workers: 4
  keepalive_timeout: 65

database:
  host: db-primary.internal
  port: 5432
  name: payments_prod
  user: payments_app
  pool_size: 25
  max_overflow: 10
  timeout_seconds: 5

security:
  ssl_enabled: true
  private_key: /etc/ssl/certs/payment-api.key
  cert_file: /etc/ssl/certs/payment-api.crt
  token_expiry_hours: 24

telemetry:
  log_level: DEBUG
  metrics_port: 9100
"""

PAYMENT_API_KEY = """-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEA0Y9k4v2K9M1xXp3Qz4vW2L9vQ1mJ7v4k2A==
PROD_KEY_PAYMENT_NODE4_SECURE_AUTH_CREDENTIALS_REDACTED
-----END RSA PRIVATE KEY-----
"""

PAYMENT_API_CRT = """-----BEGIN CERTIFICATE-----
MIIDdzCCAl+gAwIBAgIUQz4vW2L9vQ1mJ7v4k2AMIIEowIBAAKCAQEA0Y9k4v2K9M1x
PAYMENT_PROCESSOR_SSL_CERTIFICATE_NODE4_PROD
-----END CERTIFICATE-----
"""

DEBUG_TRACE_LOG_RUNAWAY = """2026-09-12T02:14:15.102Z [DEBUG] worker-leak.py: pid=4921 spawning unmonitored thread allocation pool=4096
2026-09-12T02:14:15.105Z [TRACE] worker-leak.py: dumping buffer memory frame chunk #0001 - 1048576 bytes
2026-09-12T02:14:15.110Z [TRACE] worker-leak.py: dumping buffer memory frame chunk #0002 - 1048576 bytes
2026-09-12T02:14:15.120Z [TRACE] worker-leak.py: dumping buffer memory frame chunk #0003 - 1048576 bytes
2026-09-12T02:14:15.130Z [TRACE] worker-leak.py: dumping buffer memory frame chunk #0004 - 1048576 bytes
2026-09-12T02:14:15.140Z [TRACE] worker-leak.py: memory pressure critical - worker failed to flush garbage collector
[RUNAWAY REPETITIVE DEBUG LOG DATA OVERFLOWING DISK - 19,000 MB ACCUMULATED]
"""

SYSLOG_CONTENT = """Sep 12 02:10:01 app-node-04 CRON[4011]: (root) CMD (/usr/local/bin/metrics-collector > /dev/null 2>&1)
Sep 12 02:12:44 app-node-04 kernel: [  891.120] disk_mon: warning /dev/sda1 (/) usage exceeded 95% threshold
Sep 12 02:14:18 app-node-04 systemd[1]: Starting payment-processor.service - Production Payment Processing Engine...
Sep 12 02:14:19 app-node-04 payment-processor[3102]: [FATAL] Insecure file permissions: /etc/ssl/certs/payment-api.key has mode 0666. Must be 0600 or 0400.
Sep 12 02:14:19 app-node-04 payment-processor[3102]: [ERROR] Database connection failed: could not connect to server "db-replica-invalid.internal" on port 9999. Connection refused.
Sep 12 02:14:19 app-node-04 systemd[1]: payment-processor.service: Main process exited, code=exited, status=1/FAILURE
Sep 12 02:14:19 app-node-04 systemd[1]: payment-processor.service: Failed with result 'exit-code'.
Sep 12 02:14:19 app-node-04 systemd[1]: Failed to start payment-processor.service - Production Payment Processing Engine.
"""

PAYMENT_SERVICE_UNIT = """[Unit]
Description=Production Payment Processing Engine
Documentation=https://docs.corp.internal/services/payment-processor
After=network.target

[Service]
Type=simple
User=payments
Group=payments
WorkingDirectory=/opt/payment-processor
ExecStart=/opt/payment-processor/bin/payment-processor --config /etc/payment-processor/config.yaml
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
"""

INITIAL_FILES = [
    # Path, content, owner, group, perms, type, size
    ("/etc/hostname", "app-node-04.prod.corp\n", "root", "root", "0644", "file", 23),
    ("/etc/hosts", "127.0.0.1 localhost\n10.0.1.14 app-node-04.prod.corp\n10.0.2.20 db-primary.internal\n10.0.2.21 db-replica.internal\n", "root", "root", "0644", "file", 112),
    ("/etc/os-release", "NAME=\"Ubuntu\"\nVERSION=\"24.04 LTS (Noble Numbat)\"\nID=ubuntu\nID_LIKE=debian\n", "root", "root", "0644", "file", 75),
    ("/etc/payment-processor/config.yaml", CONFIG_YAML_BROKEN, "payments", "payments", "0644", "file", len(CONFIG_YAML_BROKEN)),
    ("/etc/ssl/certs/payment-api.key", PAYMENT_API_KEY, "payments", "payments", "0666", "file", len(PAYMENT_API_KEY)),
    ("/etc/ssl/certs/payment-api.crt", PAYMENT_API_CRT, "payments", "payments", "0644", "file", len(PAYMENT_API_CRT)),
    ("/etc/systemd/system/payment-processor.service", PAYMENT_SERVICE_UNIT, "root", "root", "0644", "file", len(PAYMENT_SERVICE_UNIT)),
    ("/var/log/app/debug_trace.log", DEBUG_TRACE_LOG_RUNAWAY, "payments", "payments", "0644", "file", 18800000),
    ("/var/log/syslog", SYSLOG_CONTENT, "root", "adm", "0640", "file", len(SYSLOG_CONTENT)),
    ("/var/log/nginx/access.log", "10.0.1.2 - - [12/Sep/2026:02:14:01 +0000] \"GET /healthz HTTP/1.1\" 200 12\n", "www-data", "adm", "0640", "file", 74),
    ("/var/log/nginx/error.log", "", "www-data", "adm", "0640", "file", 0),
    ("/home/admin/.bashrc", "# ~/.bashrc: executed by bash(1) for non-login shells.\nexport PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin\n", "admin", "admin", "0644", "file", 110),
    ("/opt/payment-processor/bin/payment-processor", "#!/usr/bin/env bash\necho 'Starting payment-processor...'\n", "payments", "payments", "0755", "file", 65),
    ("/opt/workers/worker-leak.py", "#!/usr/bin/env python3\n# Leaking worker script\n", "payments", "payments", "0755", "file", 50),
]

INITIAL_PROCESSES = [
    # pid, name, command, user, cpu, mem, status, started_at
    (1, "systemd", "/sbin/init", "root", 0.1, 24.5, "running", 1773350000.0),
    (102, "systemd-journald", "/lib/systemd/systemd-journald", "root", 0.2, 18.2, "running", 1773350005.0),
    (412, "sshd", "/usr/sbin/sshd -D", "root", 0.0, 12.0, "running", 1773350010.0),
    (889, "nginx: master", "nginx: master process /usr/sbin/nginx -g daemon on; master_process on;", "root", 0.1, 35.0, "running", 1773350015.0),
    (890, "nginx: worker", "nginx: worker process", "www-data", 0.3, 42.0, "running", 1773350016.0),
    (4921, "python3", "python3 /opt/workers/worker-leak.py --worker-id=wk-49 --flush-all", "payments", 94.8, 1420.0, "running", 1773351000.0),
]

INITIAL_SERVICES = [
    ("sshd", "active", "OpenSSH server daemon", 412, 1),
    ("nginx", "active", "A high performance web server and a reverse proxy server", 889, 1),
    ("systemd-journald", "active", "Journal Service", 102, 1),
    ("payment-processor", "failed", "Production Payment Processing Engine", None, 1),
]

INITIAL_RULES = [
    ("rule_kill_leak", "kill", "pid=4921", "leak_terminated", 0),
    ("rule_truncate_log", "truncate", "file=/var/log/app/debug_trace.log", "disk_reclaimed", 0),
    ("rule_fix_config", "write_file", "file=/etc/payment-processor/config.yaml", "config_fixed", 0),
    ("rule_chmod_key", "chmod", "file=/etc/ssl/certs/payment-api.key", "key_secured", 0),
    ("rule_restart_service", "systemctl", "service=payment-processor", "service_restored", 0),
]


def seed_database(db_path: Path | str) -> sqlite3.Connection:
    conn = init_db(db_path)
    now = VIRTUAL_CLOCK.now()

    # Clear any existing rows
    conn.execute("DELETE FROM files")
    conn.execute("DELETE FROM processes")
    conn.execute("DELETE FROM services")
    conn.execute("DELETE FROM system_metrics")
    conn.execute("DELETE FROM action_log")
    conn.execute("DELETE FROM scenario_rules")
    conn.execute("DELETE FROM event_traces")
    conn.execute("DELETE FROM task_submission")

    # Insert files
    for path, content, owner, group, perms, ftype, size in INITIAL_FILES:
        conn.execute(
            """
            INSERT INTO files (path, content, owner, group_owner, permissions, file_type, size, modified_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (path, content, owner, group, perms, ftype, size, now),
        )

    # Insert processes
    for pid, name, cmd, user, cpu, mem, status, started in INITIAL_PROCESSES:
        conn.execute(
            """
            INSERT INTO processes (pid, name, command, user, cpu_percent, memory_mb, status, started_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (pid, name, cmd, user, cpu, mem, status, started),
        )

    # Insert services
    for name, status, desc, pid, enabled in INITIAL_SERVICES:
        conn.execute(
            """
            INSERT INTO services (name, status, description, pid, enabled)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, status, desc, pid, enabled),
        )

    # Insert system metrics (Initial: disk 19,800MB used out of 20,480MB = 96.7% full!)
    conn.execute(
        """
        INSERT INTO system_metrics (id, disk_total_mb, disk_used_mb, memory_total_mb, memory_used_mb)
        VALUES (1, 20480, 19800, 8192, 4200)
        """
    )

    # Insert scenario rules
    for rule_id, trigger, cond, effect, act in INITIAL_RULES:
        conn.execute(
            """
            INSERT INTO scenario_rules (rule_id, trigger, condition, effect, activated)
            VALUES (?, ?, ?, ?, ?)
            """,
            (rule_id, trigger, cond, effect, act),
        )

    conn.commit()
    return conn
