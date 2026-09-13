import { NextRequest, NextResponse } from "next/server"
import { listCalendarEvents, createCalendarEvent } from "@/lib/workstation-client"

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const startIso = searchParams.get("start") || ""
  const endIso = searchParams.get("end") || ""

  try {
    const res = await listCalendarEvents(startIso, endIso)
    return NextResponse.json(res)
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { title, start_iso, end_iso, attendees } = body
    const res = await createCalendarEvent(title, start_iso, end_iso, attendees || "")
    return NextResponse.json(res)
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}
