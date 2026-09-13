import { execFile } from "child_process"
import path from "path"

const BRIDGE_SCRIPT = path.join(process.cwd(), "scripts", "healthcare_bridge.py")

export function runHealthcareBridge(cmd: string, args: string[] = []): Promise<any> {
  const dbPath = process.env.HEALTHCARE_DB || path.join(process.cwd(), "..", "healthcare.db")

  return new Promise((resolve, reject) => {
    execFile(
      "python3",
      [BRIDGE_SCRIPT, cmd, ...args],
      {
        cwd: process.cwd(),
        env: {
          ...process.env,
          HEALTHCARE_DB: dbPath,
          PYTHONPATH: `${path.join(process.cwd(), "..")}:${path.join(process.cwd(), "..", "healthcare")}:${process.env.PYTHONPATH || ""}`,
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

export async function listPatients(query = "") {
  return runHealthcareBridge("list_patients", [query])
}

export async function verifyPatient(identifier: string, dob = "") {
  return runHealthcareBridge("verify_patient", [identifier, dob])
}

export async function getPatientChart(patientId: string) {
  return runHealthcareBridge("get_patient_chart", [patientId])
}

export async function searchClinicalRecords(query: string, resourceType = "", patientId = "") {
  return runHealthcareBridge("search_clinical_records", [query, resourceType, patientId])
}

export async function createClinicalOrder(
  patientId: string,
  orderType: string,
  code: string,
  display: string,
  dosage = "",
  instructions = "",
  isStat = false
) {
  return runHealthcareBridge("create_clinical_order", [
    patientId,
    orderType,
    code,
    display,
    dosage,
    instructions,
    isStat.toString(),
  ])
}

export async function updateOrder(orderId: string, status: string, notes = "") {
  return runHealthcareBridge("update_order", [orderId, status, notes])
}

export async function scheduleAppointment(patientId: string, providerId: string, startIso: string, endIso: string, reason = "") {
  return runHealthcareBridge("schedule_appointment", [patientId, providerId, startIso, endIso, reason])
}

export async function sendPortalMessage(patientId: string, subject: string, body: string, priority = "routine") {
  return runHealthcareBridge("send_portal_message", [patientId, subject, body, priority])
}

export async function escalateEmergency(patientId: string, reason: string, vitals: any = null) {
  const vitalsJson = vitals ? JSON.stringify(vitals) : ""
  return runHealthcareBridge("escalate_emergency", [patientId, reason, vitalsJson])
}

export async function submitPriorAuth(patientId: string, orderId: string, payerId: string, dxCode: string, justification: string) {
  return runHealthcareBridge("submit_prior_auth", [patientId, orderId, payerId, dxCode, justification])
}

export async function getAuditEvents(patientId = "") {
  return runHealthcareBridge("get_audit_events", [patientId])
}

export async function stepSimulation(minutes = 15) {
  return runHealthcareBridge("step_simulation", [minutes.toString()])
}

export async function submitTask(summary: string, affectedIds = "") {
  return runHealthcareBridge("submit_task", [summary, affectedIds])
}

export async function getStateHash() {
  return runHealthcareBridge("get_state_hash")
}
