"""Procedural seed generator for Workstation simulation.

Generates a realistic, interconnected enterprise dataset of 50 employees, 200 customers,
500 email threads, 100 calendar events, 1,000 files, 300 tickets, 200 invoices, and
CRM deals, with deliberate noise, ambiguity, and cross-application references.
"""

from __future__ import annotations

import datetime
import json
import random
import sqlite3
from pathlib import Path
from typing import Any

from workstation_sim.clock import DEFAULT_ANCHOR_ISO, VirtualClock
from workstation_sim.sqlite_common import connect, initialize_database, set_system_state

LOGGED_IN_EMPLOYEE_ID = "emp_ops_01"
LOGGED_IN_EMAIL = "alex.mercer@apexglobal.io"
LOGGED_IN_NAME = "Alex Mercer"


def _deterministic_sample(rng: random.Random, population: list[Any], k: int) -> list[Any]:
    if k <= 0:
        return []
    if k > len(population):
        k = len(population)
    return rng.sample(population, k)


def seed_database(
    db_path: Path | str,
    seed: int = 42,
    task_id: str = "account-cancellation-refund",
) -> dict[str, Any]:
    """Populate database deterministically based on seed and task_id."""
    rng = random.Random(seed)
    db_path = Path(db_path)
    if db_path.exists():
        db_path.unlink()

    with connect(db_path) as conn:
        initialize_database(conn)

        # 1. System state & metadata
        set_system_state(conn, "seed", str(seed))
        set_system_state(conn, "task_id", task_id)
        set_system_state(conn, "virtual_time_iso", DEFAULT_ANCHOR_ISO)
        set_system_state(conn, "clock_ticks", "0")
        set_system_state(conn, "logged_in_user_id", LOGGED_IN_EMPLOYEE_ID)
        set_system_state(conn, "logged_in_email", LOGGED_IN_EMAIL)
        set_system_state(conn, "logged_in_name", LOGGED_IN_NAME)
        set_system_state(conn, "company_name", "Apex Global Solutions")
        set_system_state(conn, "company_domain", "apexglobal.io")

        first_names = [
            "Alex", "Jordan", "Taylor", "Morgan", "Casey", "Sam", "Chris", "Pat", "Riley", "Jamie",
            "Sarah", "Sara", "Michael", "David", "James", "Robert", "John", "Jonathan", "Emily", "Emma",
            "Daniel", "Matthew", "Jessica", "Amanda", "Ashley", "Brian", "Kevin", "Jason", "Eric", "Steven",
            "Laura", "Rachel", "Megan", "Hannah", "Nicole", "Andrew", "Joshua", "Justin", "Brandon", "Tyler",
            "Stephanie", "Melissa", "Rebecca", "Michelle", "Kimberly", "Anthony", "Mark", "Paul", "Donald", "George"
        ]
        last_names = [
            "Mercer", "Smith", "Smyth", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis", "Garcia",
            "Rodriguez", "Wilson", "Martinez", "Anderson", "Taylor", "Thomas", "Hernandez", "Moore", "Martin", "Jackson",
            "Thompson", "White", "Lopez", "Lee", "Gonzalez", "Harris", "Clark", "Lewis", "Robinson", "Walker",
            "Perez", "Hall", "Young", "Allen", "Sanchez", "Wright", "King", "Scott", "Green", "Baker",
            "Adams", "Nelson", "Carter", "Mitchell", "Perez", "Roberts", "Turner", "Phillips", "Campbell", "Parker"
        ]

        departments = [
            ("Executive", ["Chief Executive Officer", "Chief Operating Officer", "VP Engineering", "VP Sales"]),
            ("Sales", ["Account Executive", "Senior Account Executive", "Sales Manager", "BDR Specialist"]),
            ("Customer Support", ["Support Engineer", "Senior Support Specialist", "Support Team Lead", "Escalation Manager"]),
            ("Engineering", ["Software Engineer", "Staff Engineer", "DevOps Engineer", "QA Engineer"]),
            ("Finance", ["Financial Analyst", "Billing Specialist", "Controller", "Head of Accounting"]),
            ("HR", ["HR Generalist", "Recruiter", "People Operations Director", "Talent Specialist"])
        ]

        # 2. Employees (50 total)
        employees: list[dict[str, Any]] = []
        # Main logged-in user
        employees.append({
            "id": LOGGED_IN_EMPLOYEE_ID,
            "name": LOGGED_IN_NAME,
            "email": LOGGED_IN_EMAIL,
            "role": "Senior Operations & Support Specialist",
            "department": "Customer Support",
            "manager_id": "emp_mgmt_01",
            "phone": "+1-555-0100",
            "permissions": json.dumps(["mail.all", "crm.read_write", "billing.refund_standard", "drive.read_write", "tickets.all", "cal.all"]),
        })
        # Manager for Alex Mercer
        employees.append({
            "id": "emp_mgmt_01",
            "name": "David Miller",
            "email": "david.miller@apexglobal.io",
            "role": "Director of Customer Operations",
            "department": "Customer Support",
            "manager_id": "emp_exec_01",
            "phone": "+1-555-0101",
            "permissions": json.dumps(["admin", "billing.refund_all", "crm.all"]),
        })
        # Key Account Executive for Acme Corp
        employees.append({
            "id": "emp_sales_01",
            "name": "Marcus Vance",
            "email": "marcus.vance@apexglobal.io",
            "role": "Principal Account Executive",
            "department": "Sales",
            "manager_id": "emp_exec_02",
            "phone": "+1-555-0102",
            "permissions": json.dumps(["crm.all", "mail.all", "drive.all"]),
        })

        emp_count = len(employees)
        while emp_count < 50:
            dept_name, roles = rng.choice(departments)
            fname = rng.choice(first_names)
            lname = rng.choice(last_names)
            email = f"{fname.lower()}.{lname.lower()}{emp_count}@apexglobal.io"
            employees.append({
                "id": f"emp_{emp_count:03d}",
                "name": f"{fname} {lname}",
                "email": email,
                "role": rng.choice(roles),
                "department": dept_name,
                "manager_id": "emp_mgmt_01" if dept_name == "Customer Support" else "emp_exec_01",
                "phone": f"+1-555-{1000 + emp_count}",
                "permissions": json.dumps(["mail.standard", "drive.read"]),
            })
            emp_count += 1

        for emp in employees:
            conn.execute(
                """INSERT INTO employees (id, name, email, role, department, manager_id, phone, permissions)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (emp["id"], emp["name"], emp["email"], emp["role"], emp["department"], emp["manager_id"], emp["phone"], emp["permissions"]),
            )

        # 3. Customers (200 total)
        company_names = [
            "Acme Corp", "Globex Corporation", "Soylent Corp", "Initech", "Umbrella Corporation",
            "Hooli", "Pied Piper", "Massive Dynamic", "Cyberdyne Systems", "Stark Industries",
            "Wayne Enterprises", "Oscorp", "Wonka Industries", "Dunder Mifflin", "Aperture Science",
            "Black Mesa", "Tyrell Corporation", "Weyland-Yutani", "Omni Consumer Products", "Virtucon"
        ]
        suffixes = ["Technologies", "Logistics", "Digital", "Solutions", "Capital", "Media", "Analytics", "Networks", "Labs", "Holdings"]

        customers: list[dict[str, Any]] = []
        # Target customer: Acme Corp
        acme_cust_id = "CUST-1042"
        customers.append({
            "id": acme_cust_id,
            "name": "Acme Corp",
            "domain": "acme.com",
            "account_tier": "enterprise",
            "status": "active",
            "phone": "+1-415-555-0199",
            "primary_contact_id": "cont_acme_01",
            "msa_date": "2024-01-15",
            "created_ts": "2024-01-15T10:00:00Z",
        })

        for i in range(1, 201):
            if i == 42:
                continue
            cid = f"CUST-{1000 + i}"
            base = rng.choice(company_names) if i < len(company_names) else f"{rng.choice(last_names)} {rng.choice(suffixes)}"
            dom = base.lower().replace(" ", "").replace("-", "")[:12] + ".com"
            customers.append({
                "id": cid,
                "name": base,
                "domain": dom,
                "account_tier": rng.choice(["standard", "growth", "enterprise"]),
                "status": "active" if rng.random() > 0.08 else "churned",
                "phone": f"+1-800-555-{i:04d}",
                "primary_contact_id": f"cont_{cid}_01",
                "msa_date": f"202{rng.randint(2, 5)}-{rng.randint(1, 12):02d}-15",
                "created_ts": f"202{rng.randint(2, 5)}-01-10T09:00:00Z",
            })

        for cust in customers:
            conn.execute(
                """INSERT INTO customers (id, name, domain, account_tier, status, phone, primary_contact_id, msa_date, created_ts)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (cust["id"], cust["name"], cust["domain"], cust["account_tier"], cust["status"], cust["phone"], cust["primary_contact_id"], cust["msa_date"], cust["created_ts"]),
            )

        # 4. CRM Contacts (~300 contacts)
        # Acme primary contact: Sarah Jenkins
        conn.execute(
            """INSERT INTO crm_contacts (id, customer_id, name, email, phone, title, notes, is_primary)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ("cont_acme_01", acme_cust_id, "Sarah Jenkins", "sarah.jenkins@acme.com", "+1-415-555-0188", "VP of Technology & Procurement", "Key executive buyer. Prefers email.", 1),
        )
        # Acme secondary contact (stale contact)
        conn.execute(
            """INSERT INTO crm_contacts (id, customer_id, name, email, phone, title, notes, is_primary)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ("cont_acme_02", acme_cust_id, "Robert Vance", "robert.vance@acme.com", "+1-415-555-0011", "Senior IT Manager", "Former primary contact. Handed off to Sarah Jenkins.", 0),
        )
        # Noise contact: Sara Jenkens at another customer
        conn.execute(
            """INSERT INTO crm_contacts (id, customer_id, name, email, phone, title, notes, is_primary)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ("cont_noise_01", "CUST-1002", "Sara Jenkens", "sara.jenkens@globex.com", "+1-415-555-9999", "Finance Lead", "Noise contact with similar spelling.", 1),
        )

        contact_idx = 10
        for cust in customers[1:]:
            c_name = f"{rng.choice(first_names)} {rng.choice(last_names)}"
            c_email = f"{c_name.lower().replace(' ', '.')}@{cust['domain']}"
            conn.execute(
                """INSERT INTO crm_contacts (id, customer_id, name, email, phone, title, notes, is_primary)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (f"cont_{contact_idx}", cust["id"], c_name, c_email, f"+1-555-{contact_idx:04d}", "Account Admin", "", 1),
            )
            contact_idx += 1

        # 5. CRM Deals & Activity
        # Acme Deal
        conn.execute(
            """INSERT INTO crm_deals (id, customer_id, title, value_cents, stage, owner_id, close_date, contract_file_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ("DEAL-1042", acme_cust_id, "Acme Enterprise Annual Platform Expansion", 1200000, "closed_won", "emp_sales_01", "2026-08-15", "FILE-ACME-MSA-2026"),
        )
        conn.execute(
            """INSERT INTO crm_activity_logs (id, customer_id, author_id, activity_type, body, created_ts)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("ACT-1042-01", acme_cust_id, "emp_sales_01", "note", "Executed 2026 Enterprise renewal with pro-rated exit clause.", "2026-08-15T16:30:00Z"),
        )

        deal_idx = 100
        for cust in customers[1:80]:
            deal_val = rng.randint(20, 250) * 10000
            stage = rng.choice(["prospect", "proposal", "negotiation", "closed_won", "closed_won"])
            conn.execute(
                """INSERT INTO crm_deals (id, customer_id, title, value_cents, stage, owner_id, close_date, contract_file_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (f"DEAL-{deal_idx}", cust["id"], f"{cust['name']} Expansion", deal_val, stage, "emp_sales_01", "2026-09-01", ""),
            )
            deal_idx += 1

        # 6. Invoices (200 total)
        # Acme Target Invoice INV-3817
        # Annual enterprise subscription: $12,000.00 (1,200,000 cents), issued 2026-08-15, paid 2026-08-15
        acme_items = json.dumps([
            {"description": "Apex Enterprise Workstation Platform - Annual License", "quantity": 1, "unit_price_cents": 1200000}
        ])
        conn.execute(
            """INSERT INTO invoices (id, invoice_number, customer_id, amount_cents, currency, status, issued_date, due_date, paid_date, items)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            ("INV-3817", "INV-3817", acme_cust_id, 1200000, "USD", "paid", "2026-08-15", "2026-08-30", "2026-08-15", acme_items),
        )

        for inv_i in range(1, 200):
            inv_no = f"INV-{3000 + inv_i}"
            if inv_no == "INV-3817":
                inv_no = "INV-3999"
            cust_target = rng.choice(customers)
            amt = rng.randint(15, 300) * 10000
            status = rng.choice(["paid", "paid", "unpaid", "overdue"])
            conn.execute(
                """INSERT INTO invoices (id, invoice_number, customer_id, amount_cents, currency, status, issued_date, due_date, paid_date, items)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (inv_no, inv_no, cust_target["id"], amt, "USD", status, "2026-08-01", "2026-08-31", "2026-08-10" if status == "paid" else None, json.dumps([{"description": "Monthly Platform License", "quantity": 1, "unit_price_cents": amt}])),
            )

        # 7. Knowledge Base & Policies
        # Standard Operating Procedure for Account Cancellation & Refund calculation
        refund_sop_body = """# Standard Operating Procedure: Account Cancellation & Refund Processing
Document ID: SOP-OPS-042
Effective Date: 2026-01-01
Owner: Finance & Customer Operations

1. CANCELLATION REQUESTS
All formal cancellation requests received via email or support ticket must be verified against the signed Master Services Agreement (MSA) in Drive.

2. ELIGIBILITY & REFUND FORMULA
- For Annual Contracts: If cancellation is formally requested within the first 90 days of the contract period, the customer is eligible for a pro-rated refund for the unexpired portion of the term, subject to a 10% administrative processing fee on the unexpired amount.
- Formula:
  Unexpired_Days = Contract_Duration_Days (365) - Elapsed_Days
  Base_Pro_Rata = (Invoice_Amount * Unexpired_Days) / 365
  Admin_Fee = Base_Pro_Rata * 0.10
  Allowed_Refund_Amount = Base_Pro_Rata - Admin_Fee
- All amounts must be calculated to the nearest integer cent.

3. REQUIRED ACTIONS ON CONFIRMATION
Upon calculating and confirming the refund:
a. Issue the refund via the Billing API / tool referencing the specific invoice ID and reason.
b. Update the customer's CRM account status to 'churned' and log an activity note detailing the cancellation.
c. Draft and send a polite confirmation email to the customer's primary contact summarizing the refund amount and confirmation.
d. CC or notify the assigned Account Executive (Marcus Vance <marcus.vance@apexglobal.io>).
e. Schedule a 30-minute internal post-churn account debrief on the calendar 3 days after cancellation.
"""
        conn.execute(
            """INSERT INTO kb_articles (id, category, title, body, author_id, tags, updated_iso)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            ("KB-OPS-042", "Finance & Operations", "Account Cancellation & Pro-Rated Refund Policy", refund_sop_body, "emp_mgmt_01", json.dumps(["cancellation", "refund", "billing", "sop", "acme"]), "2026-08-01T09:00:00Z"),
        )
        conn.execute(
            """INSERT INTO kb_articles (id, category, title, body, author_id, tags, updated_iso)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            ("KB-SEC-010", "Security", "Workstation Hygiene and Privacy Compliance", "Employees must never access customer accounts or documents unrelated to active assigned support tickets.", "emp_mgmt_01", json.dumps(["privacy", "security", "gdpr"]), "2026-01-10T09:00:00Z"),
        )

        # 8. Files (1,000 files in virtual filesystem)
        # Key task contract file:
        acme_contract_body = """MASTER SERVICES AGREEMENT AMENDMENT (2026)
Contract Ref: ACME-MSA-2026-EXP
Customer: Acme Corp (CUST-1042)
Provider: Apex Global Solutions

Term: 365 days commencing August 15, 2026 through August 14, 2027.
Annual Contract Fee: $12,000.00 (Invoice: INV-3817)

Section 4.2 Early Termination:
Customer may terminate this agreement within the first 90 days by written notice. In the event of early termination under this section, Provider shall refund the unexpired portion of the annual fee, less a standard 10% administrative processing charge. Pro-rata calculation shall be based on elapsed calendar days from commencement (August 15, 2026) to formal notice date (October 14, 2026 = 60 elapsed days).
"""
        conn.execute(
            """INSERT INTO files (id, name, virtual_path, mime_type, size_bytes, owner_email, customer_id, content_text, version, created_iso, updated_iso)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            ("FILE-ACME-MSA-2026", "Acme_Corp_MSA_Amendment_2026_Signed.pdf", "/contracts/Acme_Corp_MSA_Amendment_2026_Signed.pdf", "application/pdf", len(acme_contract_body), "marcus.vance@apexglobal.io", acme_cust_id, acme_contract_body, 2, "2026-08-15T14:00:00Z", "2026-08-15T14:00:00Z"),
        )
        # Noise / outdated contract (Section 4 states no refunds - intentionally superseded by 2026 amendment)
        acme_old_contract = """MASTER SERVICES AGREEMENT (2023 - SUPERSEDED)
Customer: Acme Corp (CUST-1042)
Section 4: All fees non-refundable after 30 days. NOTE: Superseded by 2026 Amendment."""
        conn.execute(
            """INSERT INTO files (id, name, virtual_path, mime_type, size_bytes, owner_email, customer_id, content_text, version, created_iso, updated_iso)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            ("FILE-ACME-MSA-2023", "Acme_Corp_MSA_2023_Archived.pdf", "/contracts/archive/Acme_Corp_MSA_2023_Archived.pdf", "application/pdf", len(acme_old_contract), "marcus.vance@apexglobal.io", acme_cust_id, acme_old_contract, 1, "2023-01-10T09:00:00Z", "2023-01-10T09:00:00Z"),
        )

        # Policy document in /finance/
        conn.execute(
            """INSERT INTO files (id, name, virtual_path, mime_type, size_bytes, owner_email, customer_id, content_text, version, created_iso, updated_iso)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            ("FILE-FIN-SOP-01", "cancellation_and_refund_matrix.txt", "/finance/cancellation_and_refund_matrix.txt", "text/plain", len(refund_sop_body), "david.miller@apexglobal.io", None, refund_sop_body, 1, "2026-01-15T09:00:00Z", "2026-01-15T09:00:00Z"),
        )

        # Populate remaining files up to 1,000 files across directories
        dirs = ["/contracts/", "/finance/", "/reports/", "/templates/", "/compliance/", "/scratch/", "/engineering/", "/archive/"]
        file_count = 3
        while file_count < 1000:
            d = rng.choice(dirs)
            target_cust = rng.choice(customers) if rng.random() > 0.4 else None
            cid_tag = target_cust["id"] if target_cust else "internal"
            fname = f"{cid_tag}_doc_{file_count:04d}"
            ext = rng.choice([".pdf", ".xlsx", ".docx", ".txt", ".csv", ".json"])
            full_path = f"{d}{fname}{ext}"
            mtype = "application/pdf" if ext == ".pdf" else ("application/vnd.ms-excel" if ext == ".xlsx" else "text/plain")
            content = f"Synthetic enterprise content for {full_path}. Customer reference: {cid_tag}."
            conn.execute(
                """INSERT INTO files (id, name, virtual_path, mime_type, size_bytes, owner_email, customer_id, content_text, version, created_iso, updated_iso)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f"FILE-{file_count:04d}", f"{fname}{ext}", full_path, mtype, len(content), LOGGED_IN_EMAIL, target_cust["id"] if target_cust else None, content, 1, "2026-05-01T09:00:00Z", "2026-05-01T09:00:00Z"),
            )
            file_count += 1

        # 9. Email Threads & Emails (500 threads total)
        # Critical incoming task email from Sarah Jenkins at Acme Corp
        acme_thread_id = "THREAD-ACME-CANCEL-01"
        acme_email_body = """Hi Alex and Apex Global Support Team,

Following our internal quarterly strategic review and budget reorganization, Acme Corp will regrettably need to cancel our Enterprise Workstation subscription under CUST-1042 effective today (October 14, 2026).

We signed our 2026 renewal on August 15, 2026 (Invoice INV-3817 for $12,000.00). According to Section 4.2 of our signed agreement, we are within the allowed 90-day early termination window. Please calculate our pro-rated refund minus the 10% administrative fee, process the refund to our account on file, update our account records, and send us written confirmation once completed.

Please also ensure Marcus Vance is kept in the loop as our account executive.

Thank you for your partnership over the past years.

Warm regards,
Sarah Jenkins
VP of Technology & Procurement
Acme Corp | sarah.jenkins@acme.com | Direct: +1-415-555-0188
"""
        conn.execute(
            """INSERT INTO email_threads (id, subject, customer_id, last_activity_iso, snippet)
               VALUES (?, ?, ?, ?, ?)""",
            (acme_thread_id, "Urgent: Acme Corp - Formal Subscription Cancellation & Refund Request", acme_cust_id, "2026-10-14T08:45:00Z", "Acme Corp will regrettably need to cancel our Enterprise Workstation subscription..."),
        )
        conn.execute(
            """INSERT INTO emails (id, thread_id, from_addr, to_addrs, cc_addrs, bcc_addrs, subject, body, date_iso, is_read, is_starred, is_archived, is_trash, folder, attachments)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            ("EMAIL-ACME-01", acme_thread_id, "sarah.jenkins@acme.com", json.dumps([LOGGED_IN_EMAIL, "support@apexglobal.io"]), json.dumps(["marcus.vance@apexglobal.io"]), json.dumps([]), "Urgent: Acme Corp - Formal Subscription Cancellation & Refund Request", acme_email_body, "2026-10-14T08:45:00Z", 0, 1, 0, 0, "inbox", json.dumps(["Acme_Corp_MSA_Amendment_2026_Signed.pdf"])),
        )

        thread_count = 1
        while thread_count < 500:
            tid = f"THREAD-{thread_count:04d}"
            target_cust = rng.choice(customers) if rng.random() > 0.3 else None
            sender = f"{rng.choice(first_names).lower()}@{target_cust['domain']}" if target_cust else f"{rng.choice(first_names).lower()}@apexglobal.io"
            subj = f"Update regarding {target_cust['name'] if target_cust else 'quarterly review'}"
            body = f"Hello, following up on our discussion for ticket and milestones. Best regards."
            ts = f"2026-10-{rng.randint(1, 13):02d}T{rng.randint(8, 17):02d}:00:00Z"
            conn.execute(
                """INSERT INTO email_threads (id, subject, customer_id, last_activity_iso, snippet)
                   VALUES (?, ?, ?, ?, ?)""",
                (tid, subj, target_cust["id"] if target_cust else None, ts, body[:60]),
            )
            conn.execute(
                """INSERT INTO emails (id, thread_id, from_addr, to_addrs, cc_addrs, bcc_addrs, subject, body, date_iso, is_read, is_starred, is_archived, is_trash, folder, attachments)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f"EMAIL-{thread_count:04d}", tid, sender, json.dumps([LOGGED_IN_EMAIL]), json.dumps([]), json.dumps([]), subj, body, ts, 1, 0, 0, 0, "inbox", json.dumps([])),
            )
            thread_count += 1

        # 10. Calendar Events (100 total)
        for cal_i in range(1, 101):
            cid = f"CAL-{cal_i:03d}"
            day = (cal_i % 25) + 1
            start = f"2026-10-{day:02d}T10:00:00Z"
            end = f"2026-10-{day:02d}T10:30:00Z"
            conn.execute(
                """INSERT INTO calendar_events (id, title, organizer_email, start_iso, end_iso, location, description, status, attendees)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (cid, f"Team Standup #{cal_i}", "david.miller@apexglobal.io", start, end, "Room 402 / Meet", "Recurring team synchronization.", "confirmed", json.dumps([LOGGED_IN_EMAIL, "david.miller@apexglobal.io"])),
            )

        # 11. Support Tickets (300 total)
        # Acme support ticket
        conn.execute(
            """INSERT INTO tickets (id, customer_id, requester_email, assignee_id, subject, description, priority, status, created_iso, updated_iso)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            ("TICK-2042", acme_cust_id, "sarah.jenkins@acme.com", LOGGED_IN_EMPLOYEE_ID, "Acme Corp - Contract Cancellation & Final Invoice Settlement", "Requested cancellation per email thread THREAD-ACME-CANCEL-01.", "high", "open", "2026-10-14T08:50:00Z", "2026-10-14T08:50:00Z"),
        )

        for tick_i in range(1, 300):
            tid = f"TICK-{2000 + tick_i}"
            if tid == "TICK-2042":
                tid = "TICK-2999"
            cust_target = rng.choice(customers)
            stat = rng.choice(["open", "in_progress", "resolved", "closed"])
            conn.execute(
                """INSERT INTO tickets (id, customer_id, requester_email, assignee_id, subject, description, priority, status, created_iso, updated_iso)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (tid, cust_target["id"], f"contact@{cust_target['domain']}", LOGGED_IN_EMPLOYEE_ID if rng.random() > 0.7 else "emp_mgmt_01", f"Inquiry for {cust_target['name']}", "Support question regarding service.", "medium", stat, "2026-10-05T09:00:00Z", "2026-10-05T09:00:00Z"),
            )

    return {
        "seed": seed,
        "task_id": task_id,
        "employees_count": len(employees),
        "customers_count": len(customers),
        "files_count": file_count,
        "threads_count": thread_count,
    }
