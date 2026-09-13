import { execFile } from "child_process"
import path from "path"

const BRIDGE_SCRIPT = path.join(process.cwd(), "scripts", "software_bridge.py")

export function runSoftwareBridge(cmd: string, args: string[] = []): Promise<any> {
  const dbPath = process.env.SOFTWARE_DB || path.join(process.cwd(), "..", "software.db")

  return new Promise((resolve, reject) => {
    execFile(
      "python3",
      [BRIDGE_SCRIPT, cmd, ...args],
      {
        cwd: process.cwd(),
        env: {
          ...process.env,
          SOFTWARE_DB: dbPath,
          PYTHONPATH: `${path.join(process.cwd(), "..")}:${path.join(process.cwd(), "..", "software")}:${process.env.PYTHONPATH || ""}`,
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

export async function listDomains() {
  return runSoftwareBridge("list_domains")
}

export async function getSchema() {
  return runSoftwareBridge("get_schema")
}

export async function searchEntities(entityName: string, query = "", filters: any = null, page = 1, pageSize = 25) {
  const filtersJson = filters ? JSON.stringify(filters) : ""
  return runSoftwareBridge("search_entities", [entityName, query, filtersJson, page.toString(), pageSize.toString()])
}

export async function getEntity(entityName: string, entityId: string) {
  return runSoftwareBridge("get_entity", [entityName, entityId])
}

export async function createEntity(entityName: string, fields: any) {
  return runSoftwareBridge("create_entity", [entityName, JSON.stringify(fields)])
}

export async function updateEntity(entityName: string, entityId: string, fields: any) {
  return runSoftwareBridge("update_entity", [entityName, entityId, JSON.stringify(fields)])
}

export async function transitionEntity(entityName: string, entityId: string, action: string, fields: any = {}) {
  return runSoftwareBridge("transition_entity", [entityName, entityId, action, JSON.stringify(fields)])
}

export async function getAuditLog() {
  return runSoftwareBridge("get_audit_log")
}

export async function getStateHash() {
  return runSoftwareBridge("get_state_hash")
}

export async function resetApp(domain: string, split = "iid", seed = 42) {
  return runSoftwareBridge("reset_app", [domain, split, seed.toString()])
}

export async function submitTask(summary: string, affectedIds = "") {
  return runSoftwareBridge("submit_task", [summary, affectedIds])
}
