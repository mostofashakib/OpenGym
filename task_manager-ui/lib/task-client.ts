import { execFile } from "child_process"
import path from "path"

const BRIDGE_SCRIPT = path.join(process.cwd(), "scripts", "task_bridge.py")

export function runTaskBridge(cmd: string, args: string[] = []): Promise<any> {
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

export async function listTasks(filters: any = {}) {
  return runTaskBridge("list_tasks", [JSON.stringify(filters)])
}

export async function getTask(taskId: string) {
  return runTaskBridge("get_task", [taskId])
}

export async function listProjects() {
  return runTaskBridge("list_projects")
}

export async function listUsers() {
  return runTaskBridge("list_users")
}

export async function updateTask(taskId: string, updates: any) {
  return runTaskBridge("call_tool", [
    "update_task",
    JSON.stringify({ task_id: taskId, ...updates }),
  ])
}

export async function linkTasks(taskId: string, dependsOnTaskId: string) {
  return runTaskBridge("call_tool", [
    "link_tasks",
    JSON.stringify({ task_id: taskId, depends_on_task_id: dependsOnTaskId }),
  ])
}

export async function unlinkTasks(taskId: string, dependsOnTaskId: string) {
  return runTaskBridge("call_tool", [
    "unlink_tasks",
    JSON.stringify({ task_id: taskId, depends_on_task_id: dependsOnTaskId }),
  ])
}

export async function submitHandoverReport(taskIds: string[], summary: string) {
  return runTaskBridge("call_tool", [
    "submit_handover_report",
    JSON.stringify({ task_ids: taskIds, summary }),
  ])
}

export async function exportState() {
  return runTaskBridge("export_state")
}
