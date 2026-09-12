import { NextRequest, NextResponse } from "next/server"
import { listTasks, runTaskBridge } from "@/lib/task-client"

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url)
    const filters: any = {}
    if (searchParams.get("project_id")) filters.project_id = searchParams.get("project_id")
    if (searchParams.get("milestone_id")) filters.milestone_id = searchParams.get("milestone_id")
    if (searchParams.get("status")) filters.status = searchParams.get("status")
    if (searchParams.get("priority")) filters.priority = searchParams.get("priority")
    if (searchParams.get("assignee")) filters.assignee = searchParams.get("assignee")

    const data = await listTasks(filters)
    return NextResponse.json(data)
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    const data = await runTaskBridge("call_tool", ["create_task", JSON.stringify(body)])
    return NextResponse.json(data)
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}
