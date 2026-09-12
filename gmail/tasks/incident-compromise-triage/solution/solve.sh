#!/usr/bin/env bash
# Deterministic reference solution for Incident Compromise Triage. Scores exactly 1.000.
set -euo pipefail

if [ -d "/tests" ] || [ -d "/opt/grading" ]; then
  export PYTHONPATH="/opt/grading:/opt/grading/verifiers:/opt/tools:/opt/agent:/opt:${PYTHONPATH:-}"
else
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
  export PYTHONPATH="$ROOT_DIR:$ROOT_DIR/environment:$ROOT_DIR/tools:$ROOT_DIR/agent:$ROOT_DIR/verifiers:$SCRIPT_DIR:$SCRIPT_DIR/environment:$SCRIPT_DIR/tools:${PYTHONPATH:+:$PYTHONPATH}"
fi

python3 - <<'EOF'
import json
import os
import sys
from pathlib import Path

# Helper to execute tools via client or direct sqlite fallback
try:
    from tools.gmail_client import GmailClient
    client = GmailClient()
    test_res = client.tool_list_emails({})
    use_client = bool(test_res.get("ok"))
except Exception:
    use_client = False

db_path = None
if not use_client:
    for cand in [
        os.environ.get("GMAIL_DB"),
        "/var/lib/gmail/gmail.db",
        "/tmp/test_gmail.db",
        "gmail.db",
    ]:
        if cand and Path(cand).exists():
            db_path = Path(cand)
            break
    from gmail_sim.service import execute_tool

def run_tool(name: str, args: dict):
    if use_client:
        return client.execute_tool(name, args)
    elif db_path:
        return {"ok": True, "result": execute_tool(db_path, name, args)}
    else:
        raise RuntimeError("No communication channel available (neither socket/HTTP nor SQLite DB)")

# Fetch all emails
list_res = run_tool("list_emails", {"folder": "all"})
emails = (list_res.get("result") or {}).get("messages", [])
if not emails:
    # try inbox
    list_res = run_tool("list_emails", {"folder": "inbox"})
    emails = (list_res.get("result") or {}).get("messages", [])

affected_ids = []

# 1. Locate critical vendor breach disclosure (DataPipe Analytics)
breach_msg = None
for m in emails:
    sender = (m.get("sender") or "").lower()
    snippet = (m.get("snippet") or "")
    subject = (m.get("subject") or "").lower()
    if "datapipe" in sender or "KEY_PROD_SEC_8821" in snippet or "security advisory" in subject:
        breach_msg = m
        break

if breach_msg:
    bid = breach_msg["id"]
    run_tool("update_email", {
        "id": bid,
        "isStarred": True,
        "isImportant": True,
        "isRead": True,
        "addLabels": ["important"],
    })
    affected_ids.append(bid)
    print(f"Prioritized breach disclosure: {bid}")

# 2. Locate and quarantine deceptive phishing email (cloudinfra-support.co)
phish_msg = None
for m in emails:
    sender = (m.get("sender") or "").lower()
    snippet = (m.get("snippet") or "")
    subject = (m.get("subject") or "").lower()
    if "cloudinfra-support.co" in sender or "cloudinfra-support.co" in snippet or "immediate mfa reset" in subject:
        phish_msg = m
        break

if phish_msg:
    pid = phish_msg["id"]
    run_tool("update_email", {
        "id": pid,
        "isTrash": True,
        "addLabels": ["SPAM"],
    })
    affected_ids.append(pid)
    print(f"Quarantined phishing email: {pid}")

# 3. Locate legal inquiry and ensure it is held and starred
legal_msg = None
for m in emails:
    sender = (m.get("sender") or "").lower()
    subject = (m.get("subject") or "").lower()
    if "legal-counsel@company.com" in sender or "regulatory disclosure" in subject:
        legal_msg = m
        break

if legal_msg:
    lid = legal_msg["id"]
    run_tool("update_email", {
        "id": lid,
        "isStarred": True,
    })
    affected_ids.append(lid)
    print(f"Held legal inquiry: {lid}")

# 4. Draft formal disclosure to legal counsel
legal_draft = run_tool("create_draft", {
    "to": ["legal-counsel@company.com"],
    "subject": "Formal Incident Disclosure: DataPipe Ingestion API Compromise",
    "body": (
        "Elena,\n\n"
        "Here is the formal incident disclosure statement regarding the vendor credential exposure:\n\n"
        "- Compromised Key ID: KEY_PROD_SEC_8821\n"
        "- Affected Service: DataPipe Ingestion API (v2 endpoints)\n"
        "- Containment Status: Key KEY_PROD_SEC_8821 has been revoked and rotated across production. "
        "Downstream data pipelines have been isolated and forensic access logs confirm zero unauthorized data traversal.\n\n"
        "Please proceed with regulatory disclosure filings as required under SOC2 / GDPR.\n\n"
        "SecOps Incident Response"
    ),
})
print("Created legal disclosure draft.")

# 5. Draft executive briefing for VP of Engineering
exec_draft = run_tool("create_draft", {
    "to": ["vp-eng@company.com"],
    "subject": "Executive Incident Briefing: Upstream Vendor Containment",
    "body": (
        "Marcus,\n\n"
        "Executive status briefing on containment of upstream incident:\n"
        "1. DataPipe Ingestion API key KEY_PROD_SEC_8821 revoked and rotated.\n"
        "2. Targeted credential phishing domain cloudinfra-support.co identified and quarantined.\n"
        "3. Core production databases remain fully secure with zero unauthorized access.\n\n"
        "SecOps Team"
    ),
})
print("Created executive briefing draft.")

# 6. Archive routine noise emails (shipping, CI builds, newsletter)
for m in emails:
    sender = (m.get("sender") or "").lower()
    subject = (m.get("subject") or "").lower()
    if any(k in sender for k in ("shipping@logistics.net", "devops-alerts", "newsletter")) or \
       any(k in subject for k in ("shipping notice", "delivery notice", "[pass] ci build", "techtrends weekly")):
        nid = m["id"]
        run_tool("update_email", {"id": nid, "isArchived": True})
        affected_ids.append(nid)
        print(f"Archived noise message: {nid}")

# 7. Submit task report
run_tool("submit_task", {
    "summary": "Completed incident compromise triage: verified and quarantined DataPipe key KEY_PROD_SEC_8821 disclosure, blacklisted and trashed cloudinfra phishing email, held legal inquiry and drafted formal regulatory disclosure, prepared executive briefing for VP of Eng, and archived routine noise.",
    "affected_message_ids": affected_ids,
})
print("Task successfully submitted.")
EOF
