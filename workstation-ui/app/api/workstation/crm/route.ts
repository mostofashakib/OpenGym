import { NextRequest, NextResponse } from "next/server"
import { getCustomer, updateCustomer } from "@/lib/workstation-client"

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const customerId = searchParams.get("id") || "CUST-001"

  try {
    const res = await getCustomer(customerId)
    return NextResponse.json(res)
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { customer_id, status, account_tier } = body
    const res = await updateCustomer(customer_id, status, account_tier)
    return NextResponse.json(res)
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}
