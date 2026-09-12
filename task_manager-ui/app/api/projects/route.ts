import { NextResponse } from "next/server"
import { listProjects } from "@/lib/task-client"

export async function GET() {
  try {
    const data = await listProjects()
    return NextResponse.json(data)
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}
