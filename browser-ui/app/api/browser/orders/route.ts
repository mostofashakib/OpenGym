import { NextRequest, NextResponse } from "next/server"
import { getDashboardData, approveOrder, rejectOrder } from "@/lib/browser-client"

export async function GET() {
  try {
    const data = await getDashboardData()
    return NextResponse.json(data.orders || [])
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    const { action, order_id, reason } = body

    if (!order_id) {
      return NextResponse.json({ error: "Missing 'order_id'" }, { status: 400 })
    }

    if (action === "approve") {
      const res = await approveOrder(order_id)
      return NextResponse.json(res)
    } else if (action === "reject") {
      const res = await rejectOrder(order_id, reason || "Rejected by compliance auditor")
      return NextResponse.json(res)
    } else {
      return NextResponse.json({ error: `Unsupported action: ${action}` }, { status: 400 })
    }
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}
