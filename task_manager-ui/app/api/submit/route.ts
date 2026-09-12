import { NextRequest, NextResponse } from "next/server"
import { submitHandoverReport } from "@/lib/task-client"

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    const { task_ids, summary } = body
    if (!task_ids || !Array.isArray(task_ids)) {
      return NextResponse.json({ error: "Missing or invalid 'task_ids'" }, { status: 400 })
    }
    const data = await submitHandoverReport(task_ids, summary || "Cutover assessment submitted")
    return NextResponse.json(data)
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}
