import { NextResponse } from "next/server"
import { getSystemState } from "@/lib/terminal-client"

export async function GET() {
  try {
    const data = await getSystemState()
    return NextResponse.json(data)
  } catch (err: any) {
    return NextResponse.json({ error: err.message || "Failed to fetch system state" }, { status: 500 })
  }
}
