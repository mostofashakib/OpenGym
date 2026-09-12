import { execFile } from "child_process"
import path from "path"

const BRIDGE_SCRIPT = path.join(process.cwd(), "scripts", "terminal_bridge.py")

export interface CommandResult {
  command?: string
  stdout?: string
  stderr?: string
  exit_code?: number
  error?: string
}

export interface SystemMetrics {
  hostname: string
  uptime: string
  disk: {
    total_mb: number
    used_mb: number
    free_mb: number
    used_percent: number
  }
  memory: {
    total_mb: number
    used_mb: number
  }
  services: Array<{
    name: string
    status: string
    description: string
    pid: number | null
    enabled: number
  }>
  running_processes_count: number
}

export interface ProcessItem {
  pid: number
  name: string
  command: string
  user: string
  cpu_percent: number
  memory_mb: number
  status: string
}

export interface ServiceItem {
  name: string
  status: string
  description: string
  pid: number | null
  enabled: number
}

export interface SystemStateResponse {
  system: SystemMetrics
  processes: ProcessItem[]
  services: ServiceItem[]
  submission: {
    id?: number
    timestamp?: number
    summary?: string
    actions_taken?: string
    submitted?: number
  }
}

export function runBridge(cmd: string, args: string[] = []): Promise<any> {
  const dbPath = process.env.TERMINAL_DB || path.join(process.cwd(), "terminal.db")

  return new Promise((resolve, reject) => {
    execFile(
      "python3",
      [BRIDGE_SCRIPT, cmd, ...args],
      {
        cwd: process.cwd(),
        env: {
          ...process.env,
          TERMINAL_DB: dbPath,
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

export async function executeTerminalCommand(command: string, cwd = "/home/admin"): Promise<CommandResult> {
  return runBridge("call_tool", ["run_command", JSON.stringify({ command, cwd })])
}

export async function getSystemState(): Promise<SystemStateResponse> {
  return runBridge("get_system")
}

export async function listSystemFiles(dir = "/"): Promise<any[]> {
  return runBridge("list_files", [dir])
}

export async function submitResolution(summary: string, actions: string[]): Promise<any> {
  return runBridge("call_tool", ["submit_task", JSON.stringify({ summary, actions_taken: actions })])
}
