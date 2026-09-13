import { spawn } from 'child_process';
import path from 'path';

const BRIDGE_PATH = path.resolve(process.cwd(), 'scripts/enterprise_bridge.py');
const PYTHON_BIN = '/opt/homebrew/opt/python@3.11/bin/python3.11';

export interface Employee {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  title: string;
  department: string;
  team: string;
  manager_id?: string;
  role_id: string;
  approval_limit_usd: number;
}

export interface Customer {
  id: string;
  company_name: string;
  tier: string;
  account_owner_id: string;
  status: string;
  arr_usd: number;
  created_date: string;
}

export interface SupportTicket {
  id: string;
  customer_id: string;
  contact_id: string;
  title: string;
  description: string;
  priority: string;
  status: string;
  assignee_id?: string;
  created_iso: string;
  resolved_iso?: string;
  customer_name?: string;
}

export interface ApprovalRequest {
  id: string;
  workflow_instance_id?: string;
  request_type: string;
  requester_id: string;
  approver_id: string;
  amount_usd: number;
  reason: string;
  status: string;
  decision_notes: string;
  created_iso: string;
  decided_iso?: string;
  requester_name?: string;
  approver_name?: string;
}

export interface AuditEvent {
  id: number;
  timestamp_iso: string;
  actor_id: string;
  actor_role: string;
  action: string;
  resource_type: string;
  resource_id: string;
  authorized: number;
  details_json: string;
}

export async function runEnterpriseBridge(command: string, args: string[] = []): Promise<any> {
  return new Promise((resolve, reject) => {
    const py = spawn(PYTHON_BIN, [BRIDGE_PATH, command, ...args]);
    let stdout = '';
    let stderr = '';

    py.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    py.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    py.on('close', (code) => {
      if (code !== 0) {
        try {
          const errObj = JSON.parse(stdout);
          return reject(new Error(errObj.error || `Bridge exited with code ${code}`));
        } catch {
          return reject(new Error(stderr || stdout || `Bridge exited with code ${code}`));
        }
      }
      try {
        const parsed = JSON.parse(stdout);
        resolve(parsed);
      } catch (err: any) {
        reject(new Error(`Failed to parse bridge JSON output: ${err.message}`));
      }
    });
  });
}
