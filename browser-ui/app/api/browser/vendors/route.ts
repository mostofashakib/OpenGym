import { NextRequest, NextResponse } from "next/server"
import { getDashboardData, blacklistVendor } from "@/lib/browser-client"

export async function GET() {
  try {
    const data = await getDashboardData()
    return NextResponse.json(data.vendors || [])
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    const { action, vendor_id, notes } = body

    if (!vendor_id) {
      return NextResponse.json({ error: "Missing 'vendor_id'" }, { status: 400 })
    }

    if (action === "blacklist") {
      const res = await blacklistVendor(
        vendor_id,
        notes || "Blacklisted following fraud risk audit inspection."
      )
      return NextResponse.json(res)
    } else {
      return NextResponse.json({ error: `Unsupported action: ${action}` }, { status: 400 })
    }
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}
