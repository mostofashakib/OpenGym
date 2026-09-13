import { NextRequest, NextResponse } from "next/server"
import { resetApp, submitTask } from "@/lib/software-client"

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { action, domain, split, seed, summary, affected_ids } = body

    if (action === "reset") {
      const res = await resetApp(domain || "logistics", split || "iid", seed || 42)
      return NextResponse.json(res)
    } else if (action === "submit") {
      const res = await submitTask(summary || "Software task completed", affected_ids || "")
      return NextResponse.json(res)
    } else {
      return NextResponse.json({ error: `Unknown action '${action}'` }, { status: 400 })
    }
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}
