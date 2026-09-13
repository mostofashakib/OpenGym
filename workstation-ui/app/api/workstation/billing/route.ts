import { NextRequest, NextResponse } from "next/server"
import { getInvoice, issueRefund } from "@/lib/workstation-client"

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const invoiceNumber = searchParams.get("id") || "INV-2026-0001"

  try {
    const res = await getInvoice(invoiceNumber)
    return NextResponse.json(res)
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { invoice_number, amount, reason } = body
    const res = await issueRefund(invoice_number, parseFloat(amount || "0"), reason || "")
    return NextResponse.json(res)
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}
