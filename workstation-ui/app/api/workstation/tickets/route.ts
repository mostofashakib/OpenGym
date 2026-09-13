import { NextRequest, NextResponse } from "next/server"
import { listTickets, updateTicket } from "@/lib/workstation-client"

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const status = searchParams.get("status") || "all"
  const customerId = searchParams.get("customerId") || ""

  try {
    const res = await listTickets(status, customerId)
    return NextResponse.json(res)
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { ticket_id, status, priority, comment } = body
    const res = await updateTicket(ticket_id, status, priority, comment)
    return NextResponse.json(res)
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}
