import { NextRequest, NextResponse } from "next/server"
import { stepSimulation, submitTask } from "@/lib/healthcare-client"

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { action, minutes, summary, affected_ids } = body

    if (action === "step") {
      const res = await stepSimulation(minutes ? parseInt(minutes, 10) : 15)
      return NextResponse.json(res)
    } else if (action === "submit") {
      const res = await submitTask(summary || "Clinical EHR workflow completed", affected_ids || "")
      return NextResponse.json(res)
    } else {
      return NextResponse.json({ error: `Unknown action '${action}'` }, { status: 400 })
    }
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}
