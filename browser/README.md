# Browser — Headless Browser Environment

A deterministic, high-fidelity headless browser environment for evaluating AI agents on enterprise web automation, procurement auditing, and regulatory compliance.

## The Task

The Finance and SecOps steering committee received alerts regarding suspicious procurement activity, pending infrastructure renewals, and expired compliance certifications across third-party suppliers on internal portal `https://procure.corp`.

The agent must:
1. **Order Triage**: Navigate `/orders`, identify high-value unauthorized hardware requisition `PO-9821` ("16x H100 GPU Cluster" for $480,000 placed by guest account), and reject it with policy reason code `POLICY_VIOLATION_UNAUTHORIZED_HARDWARE`.
2. **Renewal Approval**: Review and approve legitimate annual Kubernetes cluster license `PO-3410` from `CloudScale Systems Inc.`
3. **Supplier Governance**: Navigate `/vendors`, locate unverified offshore supplier `GhostWire Hardware LLC`, and update its status to `BLACKLISTED`.
4. **Compliance Recertification**: Navigate `/compliance`, file SOC-2 recertification for critical vendor `DataSync Corp` using verified audit reference `SOC2-2026-NEXUS-778`.
5. **Operational Cleanliness**: Avoid altering legitimate orders (`PO-1022`, `PO-2045`) or suspending compliant suppliers.
6. **Audit Sign-Off**: Record final audit findings and affected IDs via `submit_task`.

## Tools

The agent interacts via an MCP server (`browser-mcp`) providing:
- `navigate(url)`: Navigate to internal portal pages.
- `get_page()`: Inspect the current page DOM / structured text and interactive element IDs.
- `click(element_id)`: Click buttons, links, and tabs.
- `type_text(element_id, text)`: Input text into fields or textareas.
- `select_option(element_id, value)`: Choose options from dropdown menus.
- `submit_form(form_id)`: Submit web forms.
- `go_back()`: Navigate back in browser history.
- `submit_task(summary, audited_ids)`: Record final audit sign-off.

## Running

```bash
# Deterministic reference oracle run (scores 1.000)
harbor run -p ./browser -a oracle

# Run with Ollama model
./browser/run.sh

# Run with hosted models via OpenRouter
MODEL=openrouter/anthropic/claude-3.5-sonnet ./browser/run.sh

# Run self-tests and verifier
./browser/tests/test.sh
```
