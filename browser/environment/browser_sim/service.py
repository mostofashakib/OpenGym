"""Headless browser engine and DOM routing for browser environment."""

from __future__ import annotations

import json
import posixpath
import sqlite3
from pathlib import Path
from typing import Any

from browser_sim.clock import VIRTUAL_CLOCK
from browser_sim.sqlite_common import get_connection
from browser_sim.tracker import BrowserTracker

# Session input buffer for form fields
SESSION_INPUTS: dict[str, str] = {}


def export_state(conn: sqlite3.Connection) -> dict[str, Any]:
    orders = [dict(r) for r in conn.execute("SELECT * FROM orders").fetchall()]
    vendors = [dict(r) for r in conn.execute("SELECT * FROM vendors").fetchall()]
    filings = [dict(r) for r in conn.execute("SELECT * FROM compliance_filings").fetchall()]
    session_row = conn.execute("SELECT * FROM browser_session WHERE id = 1").fetchone()
    session = dict(session_row) if session_row else {}
    action_log = [dict(r) for r in conn.execute("SELECT * FROM action_log ORDER BY id ASC").fetchall()]
    sub_row = conn.execute("SELECT * FROM task_submission WHERE id = 1").fetchone()
    submission = dict(sub_row) if sub_row else None
    traces = [dict(r) for r in conn.execute("SELECT * FROM event_traces ORDER BY id ASC").fetchall()]

    return {
        "orders": orders,
        "vendors": vendors,
        "compliance_filings": filings,
        "browser_session": session,
        "action_log": action_log,
        "task_submission": submission,
        "event_traces": traces,
    }


def _normalize_url(url: str) -> str:
    url = url.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        if not url.startswith("/"):
            url = "/" + url
        url = f"https://procure.corp{url}"
    return url


class BrowserService:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn
        self.tracker = BrowserTracker(conn)

    def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        handler = getattr(self, f"_tool_{tool_name}", None)
        if handler is None:
            res = {"error": f"Unknown tool: {tool_name}"}
        else:
            try:
                res = handler(arguments)
            except Exception as exc:
                res = {"error": str(exc)}

        self.tracker.record_action(tool_name, arguments, res)
        return res

    # -------------------------------------------------------------
    # Tool Handlers
    # -------------------------------------------------------------

    def _tool_navigate(self, args: dict[str, Any]) -> dict[str, Any]:
        url = _normalize_url(args["url"])
        session_row = self.conn.execute("SELECT history_json FROM browser_session WHERE id = 1").fetchone()
        history: list[str] = json.loads(session_row[0]) if session_row else []
        history.append(url)

        self.conn.execute(
            """
            UPDATE browser_session
            SET current_url = ?, history_json = ?
            WHERE id = 1
            """,
            (url, json.dumps(history)),
        )
        self.conn.commit()

        page = self._render_page(url)
        return {"success": True, "url": url, "page": page}

    def _tool_get_page(self, args: dict[str, Any]) -> dict[str, Any]:
        row = self.conn.execute("SELECT current_url FROM browser_session WHERE id = 1").fetchone()
        url = row[0] if row else "https://procure.corp/dashboard"
        return self._render_page(url)

    def _tool_go_back(self, args: dict[str, Any]) -> dict[str, Any]:
        row = self.conn.execute("SELECT history_json FROM browser_session WHERE id = 1").fetchone()
        history: list[str] = json.loads(row[0]) if row else []
        if len(history) > 1:
            history.pop()
            new_url = history[-1]
            self.conn.execute(
                """
                UPDATE browser_session
                SET current_url = ?, history_json = ?
                WHERE id = 1
                """,
                (new_url, json.dumps(history)),
            )
            self.conn.commit()
            return {"success": True, "url": new_url, "page": self._render_page(new_url)}
        return {"error": "No previous page in history"}

    def _tool_type_text(self, args: dict[str, Any]) -> dict[str, Any]:
        el_id = args["element_id"]
        text = args["text"]
        SESSION_INPUTS[el_id] = text
        return {"success": True, "element_id": el_id, "value": text}

    def _tool_select_option(self, args: dict[str, Any]) -> dict[str, Any]:
        el_id = args["element_id"]
        val = args["value"]
        SESSION_INPUTS[el_id] = val
        return {"success": True, "element_id": el_id, "selected": val}

    def _tool_submit_form(self, args: dict[str, Any]) -> dict[str, Any]:
        form_id = args.get("form_id", "")
        if "compliance" in form_id or form_id == "form-compliance-renewal":
            return self._handle_compliance_submission()
        return {"success": True, "form_id": form_id}

    def _tool_click(self, args: dict[str, Any]) -> dict[str, Any]:
        el_id = args["element_id"]
        now = VIRTUAL_CLOCK.now()

        if el_id in ("link-orders", "tab-orders"):
            return self._tool_navigate({"url": "https://procure.corp/orders"})
        elif el_id in ("link-vendors", "tab-vendors"):
            return self._tool_navigate({"url": "https://procure.corp/vendors"})
        elif el_id in ("link-compliance", "tab-compliance"):
            return self._tool_navigate({"url": "https://procure.corp/compliance"})
        elif el_id in ("link-dashboard", "tab-dashboard"):
            return self._tool_navigate({"url": "https://procure.corp/dashboard"})
        elif el_id == "link-order-po-9821":
            return self._tool_navigate({"url": "https://procure.corp/orders/PO-9821"})
        elif el_id == "link-order-po-3410":
            return self._tool_navigate({"url": "https://procure.corp/orders/PO-3410"})
        elif el_id == "link-back-orders":
            return self._tool_navigate({"url": "https://procure.corp/orders"})
        elif el_id == "link-recertify-datasync":
            return self._tool_navigate({"url": "https://procure.corp/compliance"})

        # Button: Reject PO-9821
        elif el_id in ("btn-reject-po-9821", "reject-po-9821"):
            reason = SESSION_INPUTS.get("input-rejection-reason", "POLICY_VIOLATION_UNAUTHORIZED_HARDWARE")
            self.conn.execute(
                """
                UPDATE orders
                SET status = 'REJECTED', rejection_reason = ?, updated_at = ?
                WHERE id = 'PO-9821'
                """,
                (reason, now),
            )
            self.conn.commit()
            return {
                "success": True,
                "message": f"Order PO-9821 rejected with reason: {reason}",
                "order_id": "PO-9821",
                "status": "REJECTED",
            }

        # Button: Approve PO-3410
        elif el_id in ("btn-approve-po-3410", "approve-po-3410"):
            self.conn.execute(
                """
                UPDATE orders
                SET status = 'APPROVED', updated_at = ?
                WHERE id = 'PO-3410'
                """,
                (now,),
            )
            self.conn.commit()
            return {
                "success": True,
                "message": "Order PO-3410 approved for renewal.",
                "order_id": "PO-3410",
                "status": "APPROVED",
            }

        # Button: Blacklist Vendor GhostWire
        elif el_id in ("btn-blacklist-vend-ghostwire", "blacklist-ghostwire"):
            self.conn.execute(
                """
                UPDATE vendors
                SET status = 'BLACKLISTED'
                WHERE id = 'VEND-GHOSTWIRE'
                """
            )
            self.conn.commit()
            return {
                "success": True,
                "message": "Vendor GhostWire Hardware LLC updated to BLACKLISTED.",
                "vendor_id": "VEND-GHOSTWIRE",
                "status": "BLACKLISTED",
            }

        # Button: Submit Compliance Filing
        elif el_id in ("btn-submit-compliance", "submit-compliance"):
            return self._handle_compliance_submission()

        return {"error": f"Unknown or non-interactive element: {el_id}"}

    def _handle_compliance_submission(self) -> dict[str, Any]:
        now = VIRTUAL_CLOCK.now()
        cert_code = SESSION_INPUTS.get("input-cert-code", "SOC2-2026-NEXUS-778")
        vendor_id = SESSION_INPUTS.get("input-vendor-id", "VEND-DATASYNC")

        self.conn.execute(
            """
            INSERT INTO compliance_filings (vendor_id, cert_type, cert_reference, status, submitted_at)
            VALUES (?, 'SOC-2 Type II', ?, 'APPROVED', ?)
            """,
            (vendor_id, cert_code, now),
        )
        self.conn.execute(
            """
            UPDATE vendors
            SET soc2_certified = 1, soc2_cert_id = ?, soc2_expires = '2027-09-12'
            WHERE id = ?
            """,
            (cert_code, vendor_id),
        )
        self.conn.commit()
        return {
            "success": True,
            "message": f"Compliance filing for {vendor_id} approved with reference {cert_code}.",
            "vendor_id": vendor_id,
            "cert_reference": cert_code,
        }

    def _tool_submit_task(self, args: dict[str, Any]) -> dict[str, Any]:
        now = VIRTUAL_CLOCK.now()
        summary = args["summary"]
        audited_ids = json.dumps(args.get("audited_ids", []))

        self.conn.execute("DELETE FROM task_submission")
        self.conn.execute(
            """
            INSERT INTO task_submission (id, timestamp, summary, audited_ids)
            VALUES (1, ?, ?, ?)
            """,
            (now, summary, audited_ids),
        )
        self.conn.commit()
        return {"success": True, "message": "Procurement audit sign-off recorded."}

    # -------------------------------------------------------------
    # DOM / Page Content Renderer
    # -------------------------------------------------------------

    def _render_page(self, url: str) -> dict[str, Any]:
        path = url.replace("https://procure.corp", "").rstrip("/")
        if not path or path == "/dashboard":
            return self._render_dashboard(url)
        elif path == "/orders":
            return self._render_orders(url)
        elif path.startswith("/orders/"):
            oid = path.split("/")[-1]
            return self._render_order_detail(url, oid)
        elif path == "/vendors":
            return self._render_vendors(url)
        elif path == "/compliance":
            return self._render_compliance(url)

        return {
            "url": url,
            "title": "404 Not Found - Enterprise Procurement",
            "content": "# 404 Not Found\nThe requested portal page does not exist.",
            "interactive_elements": [{"id": "link-dashboard", "type": "link", "label": "Return to Dashboard"}],
        }

    def _render_dashboard(self, url: str) -> dict[str, Any]:
        pending_orders = self.conn.execute("SELECT count(*) FROM orders WHERE status = 'PENDING_APPROVAL'").fetchone()[0]
        critical_vendors = self.conn.execute("SELECT count(*) FROM vendors WHERE risk_level = 'CRITICAL'").fetchone()[0]
        expired_soc2 = self.conn.execute("SELECT count(*) FROM vendors WHERE soc2_certified = 0").fetchone()[0]

        content = f"""# Enterprise Procurement & Compliance Portal

Welcome, **audit-officer@corp.internal** | Role: *Procurement & Compliance Auditor*

## Executive Overview
- **Pending Purchase Orders**: {pending_orders} awaiting review
- **High/Critical Risk Vendors**: {critical_vendors} requiring investigation
- **Expired SOC-2 Certifications**: {expired_soc2} blocking release gating

## Quick Navigation
- [#link-orders] [Go to Purchase Orders]
- [#link-vendors] [Go to Vendor Directory]
- [#link-compliance] [Go to Compliance Center]
"""
        elements = [
            {"id": "link-orders", "type": "link", "label": "Go to Purchase Orders"},
            {"id": "link-vendors", "type": "link", "label": "Go to Vendor Directory"},
            {"id": "link-compliance", "type": "link", "label": "Go to Compliance Center"},
        ]
        return {"url": url, "title": "Dashboard - Enterprise Procurement", "content": content, "interactive_elements": elements}

    def _render_orders(self, url: str) -> dict[str, Any]:
        rows = self.conn.execute("SELECT * FROM orders ORDER BY created_at DESC").fetchall()
        lines = [
            "# Purchase Orders Registry",
            "",
            "| Order ID | Vendor | Item Description | Amount | Status | Actions |",
            "|---|---|---|---|---|---|",
        ]
        elements = [
            {"id": "link-dashboard", "type": "link", "label": "Dashboard"},
            {"id": "link-vendors", "type": "link", "label": "Vendors"},
            {"id": "link-compliance", "type": "link", "label": "Compliance"},
        ]

        for r in rows:
            oid = r["id"]
            amt = f"${r['amount']:,.2f}"
            status = r["status"]
            actions = f"[#link-order-{oid.lower()}] [Inspect]"
            if status == "PENDING_APPROVAL":
                if oid == "PO-9821":
                    actions += " | [#btn-reject-po-9821] [Reject]"
                    elements.append({"id": "btn-reject-po-9821", "type": "button", "label": f"Reject {oid}"})
                elif oid == "PO-3410":
                    actions += " | [#btn-approve-po-3410] [Approve]"
                    elements.append({"id": "btn-approve-po-3410", "type": "button", "label": f"Approve {oid}"})

            elements.append({"id": f"link-order-{oid.lower()}", "type": "link", "label": f"Inspect {oid}"})
            lines.append(f"| {oid} | {r['vendor_id']} | {r['item']} | {amt} | **{status}** | {actions} |")

        return {"url": url, "title": "Purchase Orders - Enterprise Procurement", "content": "\n".join(lines), "interactive_elements": elements}

    def _render_order_detail(self, url: str, order_id: str) -> dict[str, Any]:
        row = self.conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        if not row:
            return {"url": url, "title": "Order Not Found", "content": f"Order {order_id} not found.", "interactive_elements": []}

        amt = f"${row['amount']:,.2f}"
        status = row["status"]
        reason = row["rejection_reason"] or "N/A"

        content = f"""# Purchase Order Details: {order_id}

- **Requisition ID**: {order_id}
- **Vendor ID**: {row['vendor_id']}
- **Line Item**: {row['item']}
- **Total Amount**: {amt}
- **Requested By**: {row['requested_by']}
- **Current Status**: **{status}**
- **Rejection Reason**: {reason}

## Available Actions
"""
        elements = [{"id": "link-back-orders", "type": "link", "label": "Back to Orders"}]
        if status == "PENDING_APPROVAL":
            if order_id == "PO-9821":
                content += """
- [#input-rejection-reason] [Input Field: Enter policy rejection reason]
- [#btn-reject-po-9821] [Reject Requisition]
"""
                elements.extend([
                    {"id": "input-rejection-reason", "type": "input", "label": "Rejection Reason"},
                    {"id": "btn-reject-po-9821", "type": "button", "label": "Reject Requisition"},
                ])
            elif order_id == "PO-3410":
                content += """
- [#btn-approve-po-3410] [Approve Requisition]
"""
                elements.append({"id": "btn-approve-po-3410", "type": "button", "label": "Approve Requisition"})

        content += "\n- [#link-back-orders] [Back to Orders List]"
        return {"url": url, "title": f"Order {order_id} - Enterprise Procurement", "content": content, "interactive_elements": elements}

    def _render_vendors(self, url: str) -> dict[str, Any]:
        rows = self.conn.execute("SELECT * FROM vendors ORDER BY id ASC").fetchall()
        lines = [
            "# Supplier Governance & Vendor Directory",
            "",
            "| Vendor ID | Supplier Name | Risk Tier | Status | SOC-2 Status | Actions |",
            "|---|---|---|---|---|---|",
        ]
        elements = [
            {"id": "link-dashboard", "type": "link", "label": "Dashboard"},
            {"id": "link-orders", "type": "link", "label": "Orders"},
            {"id": "link-compliance", "type": "link", "label": "Compliance"},
        ]

        for r in rows:
            vid = r["id"]
            risk = r["risk_level"]
            status = r["status"]
            soc2 = "CERTIFIED" if r["soc2_certified"] == 1 else "EXPIRED / UNVERIFIED"

            actions = ""
            if vid == "VEND-GHOSTWIRE" and status != "BLACKLISTED":
                actions = "[#btn-blacklist-vend-ghostwire] [Blacklist Supplier]"
                elements.append({"id": "btn-blacklist-vend-ghostwire", "type": "button", "label": "Blacklist Supplier"})
            elif vid == "VEND-DATASYNC" and r["soc2_certified"] == 0:
                actions = "[#link-recertify-datasync] [Recertify SOC-2]"
                elements.append({"id": "link-recertify-datasync", "type": "link", "label": "Recertify SOC-2"})
            else:
                actions = "Active"

            lines.append(f"| {vid} | {r['name']} | {risk} | **{status}** | {soc2} | {actions} |")

        return {"url": url, "title": "Vendor Directory - Enterprise Procurement", "content": "\n".join(lines), "interactive_elements": elements}

    def _render_compliance(self, url: str) -> dict[str, Any]:
        datasync = self.conn.execute("SELECT * FROM vendors WHERE id = 'VEND-DATASYNC'").fetchone()
        soc2_status = "CERTIFIED" if datasync and datasync["soc2_certified"] == 1 else "EXPIRED"

        content = f"""# Regulatory Compliance Center

## Vendor Recertification Filing: DataSync Corp (`VEND-DATASYNC`)
- **Current Certification**: {soc2_status}
- **Required Standard**: SOC-2 Type II (Annual Enterprise Recertification)
- **Status Gating**: Production release deployment compliance check

### Recertification Form
- Vendor: **DataSync Corp**
- Form ID: `form-compliance-renewal`
- [#input-vendor-id] [Field: VEND-DATASYNC]
- [#input-cert-code] [Input: Enter SOC-2 Recertification Reference]
- [#btn-submit-compliance] [Submit Filing]

## Navigation
- [#link-dashboard] [Dashboard]
- [#link-orders] [Orders]
- [#link-vendors] [Vendors]
"""
        elements = [
            {"id": "input-vendor-id", "type": "input", "label": "Vendor ID", "value": "VEND-DATASYNC"},
            {"id": "input-cert-code", "type": "input", "label": "Cert Code"},
            {"id": "btn-submit-compliance", "type": "button", "label": "Submit Filing"},
            {"id": "link-dashboard", "type": "link", "label": "Dashboard"},
            {"id": "link-orders", "type": "link", "label": "Orders"},
            {"id": "link-vendors", "type": "link", "label": "Vendors"},
        ]
        return {"url": url, "title": "Compliance Center - Enterprise Procurement", "content": content, "interactive_elements": elements}


def execute_tool(db_path: Path | str, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    with get_connection(db_path) as conn:
        svc = BrowserService(conn)
        return svc.execute_tool(tool_name, arguments)
