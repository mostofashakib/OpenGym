import { execFile } from "child_process"
import path from "path"

const BRIDGE_SCRIPT = path.join(process.cwd(), "scripts", "browser_bridge.py")

export function runBrowserBridge(cmd: string, args: string[] = []): Promise<any> {
  return new Promise((resolve, reject) => {
    execFile(
      "python3",
      [BRIDGE_SCRIPT, cmd, ...args],
      {
        cwd: process.cwd(),
        env: {
          ...process.env,
          PYTHONPATH: `${path.join(process.cwd(), "environment")}:${process.env.PYTHONPATH || ""}`,
        },
        timeout: 10000,
      },
      (error, stdout, stderr) => {
        if (error) {
          try {
            const parsed = JSON.parse(stdout)
            return resolve(parsed)
          } catch {
            return reject(new Error(stderr || error.message))
          }
        }
        try {
          const parsed = JSON.parse(stdout)
          resolve(parsed)
        } catch (e) {
          resolve({ raw: stdout, stderr })
        }
      }
    )
  })
}

export async function getDashboardData() {
  return runBrowserBridge("get_dashboard")
}

export async function exportStateData() {
  return runBrowserBridge("export_state")
}

export async function approveOrder(orderId: string) {
  return runBrowserBridge("call_tool", ["approve_order", JSON.stringify({ order_id: orderId })])
}

export async function rejectOrder(orderId: string, reason: string) {
  return runBrowserBridge("call_tool", ["reject_order", JSON.stringify({ order_id: orderId, reason })])
}

export async function blacklistVendor(vendorId: string, notes: string) {
  return runBrowserBridge("call_tool", [
    "update_vendor",
    JSON.stringify({ vendor_id: vendorId, status: "BLACKLISTED", notes }),
  ])
}

export async function submitCompliance(vendorId: string, certRef: string, certType = "SOC2_TYPE2") {
  return runBrowserBridge("call_tool", [
    "compliance_filing",
    JSON.stringify({ vendor_id: vendorId, cert_reference: certRef, cert_type: certType }),
  ])
}

export async function submitAudit(summary: string, auditedIds: string[]) {
  return runBrowserBridge("call_tool", [
    "submit_audit_report",
    JSON.stringify({ summary, audited_ids: auditedIds }),
  ])
}
