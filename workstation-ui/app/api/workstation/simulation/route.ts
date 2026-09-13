import { NextRequest, NextResponse } from "next/server"
import { getStateHash, stepSimulation, submitTask, getAuditEvents } from "@/lib/workstation-client"

export async function GET() {
  try {
    const hashRes = await getStateHash()
    const auditRes = await getAuditEvents()
    return NextResponse.json({
      ok: true,
      state_hash: hashRes?.state_hash || "unknown",
      audit_events: auditRes?.audit_events || [],
    })
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { action, seconds, summary, affected_ids } = body

    if (action === "step") {
      const res = await stepSimulation(seconds ? parseInt(seconds, 10) : 900)
      return NextResponse.json(res)
    } else if (action === "submit") {
      const res = await submitTask(summary || "Workstation task completed", affected_ids || "")
      return NextResponse.json(res)
    } else {
      return NextResponse.json({ error: `Unknown action '${action}'` }, { status: 400 })
    }
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}
