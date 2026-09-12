import { NextRequest, NextResponse } from "next/server"
import { getDashboardData, submitCompliance } from "@/lib/browser-client"

export async function GET() {
  try {
    const data = await getDashboardData()
    return NextResponse.json(data.compliance_filings || [])
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    const { vendor_id, cert_reference, cert_type } = body

    if (!vendor_id || !cert_reference) {
      return NextResponse.json({ error: "Missing vendor_id or cert_reference" }, { status: 400 })
    }

    const res = await submitCompliance(vendor_id, cert_reference, cert_type || "SOC2_TYPE2")
    return NextResponse.json(res)
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}
