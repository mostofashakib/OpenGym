import { execFile } from "child_process"
import path from "path"

const BRIDGE_SCRIPT = path.join(process.cwd(), "scripts", "workstation_bridge.py")

export function runWorkstationBridge(cmd: string, args: string[] = []): Promise<any> {
  const dbPath = process.env.WORKSTATION_DB || path.join(process.cwd(), "..", "workstation.db")

  return new Promise((resolve, reject) => {
    execFile(
      "python3",
      [BRIDGE_SCRIPT, cmd, ...args],
      {
        cwd: process.cwd(),
        env: {
          ...process.env,
          WORKSTATION_DB: dbPath,
          PYTHONPATH: `${path.join(process.cwd(), "..")}:${path.join(process.cwd(), "..", "workstation")}:${process.env.PYTHONPATH || ""}`,
        },
        timeout: 15000,
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

export async function listApps() {
  return runWorkstationBridge("list_apps")
}

export async function listEmails(folder = "inbox", query = "") {
  return runWorkstationBridge("email_list", [folder, query])
}

export async function getEmailThread(threadId: string) {
  return runWorkstationBridge("email_read", [threadId])
}

export async function sendEmail(to: string, subject: string, body: string) {
  return runWorkstationBridge("email_send", [to, subject, body])
}

export async function listCalendarEvents(startIso = "", endIso = "") {
  return runWorkstationBridge("calendar_list_events", [startIso, endIso])
}

export async function createCalendarEvent(title: string, startIso: string, endIso: string, participants = "") {
  return runWorkstationBridge("calendar_create_event", [title, startIso, endIso, participants])
}

export async function listFiles(directory = "/") {
  return runWorkstationBridge("file_list", [directory])
}

export async function readFile(path: string) {
  return runWorkstationBridge("file_read", [path])
}

export async function writeFile(path: string, content: string) {
  return runWorkstationBridge("file_write", [path, content])
}

export async function readSpreadsheet(path: string) {
  return runWorkstationBridge("spreadsheet_read", [path])
}

export async function updateSpreadsheetCell(path: string, cell: string, value: string) {
  return runWorkstationBridge("spreadsheet_update_cell", [path, cell, value])
}

export async function readDocument(path: string) {
  return runWorkstationBridge("document_read", [path])
}

export async function appendDocument(path: string, content: string) {
  return runWorkstationBridge("document_append", [path, content])
}

export async function runTerminalCommand(command: string) {
  return runWorkstationBridge("terminal_execute", [command])
}

export async function getCustomer(customerId: string) {
  return runWorkstationBridge("crm_get_customer", [customerId])
}

export async function updateCustomer(customerId: string, status = "", tier = "") {
  return runWorkstationBridge("crm_update_customer", [customerId, status, tier])
}

export async function listTickets(status = "all", customerId = "") {
  return runWorkstationBridge("ticket_list", [status, customerId])
}

export async function updateTicket(ticketId: string, status = "", priority = "", comment = "") {
  return runWorkstationBridge("ticket_update", [ticketId, status, priority, comment])
}

export async function searchKb(query = "") {
  return runWorkstationBridge("kb_search", [query])
}

export async function getKbArticle(articleId: string) {
  return runWorkstationBridge("kb_read_article", [articleId])
}

export async function getInvoice(invoiceNumber: string) {
  return runWorkstationBridge("billing_get_invoice", [invoiceNumber])
}

export async function issueRefund(invoiceNumber: string, amount: number, reason = "") {
  return runWorkstationBridge("billing_issue_refund", [invoiceNumber, amount.toString(), reason])
}

export async function getAuditEvents() {
  return runWorkstationBridge("get_audit_events")
}

export async function stepSimulation(seconds = 900) {
  return runWorkstationBridge("step_simulation", [seconds.toString()])
}

export async function submitTask(summary: string, affectedIds = "") {
  return runWorkstationBridge("submit_task", [summary, affectedIds])
}

export async function getStateHash() {
  return runWorkstationBridge("get_state_hash")
}
