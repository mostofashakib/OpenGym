import { NextRequest, NextResponse } from "next/server"
import { readSpreadsheet, updateSpreadsheetCell } from "@/lib/workstation-client"

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const path = searchParams.get("path") || "financial_tracker.csv"

  try {
    const res = await readSpreadsheet(path)
    return NextResponse.json(res)
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { path, cell, value } = body
    const res = await updateSpreadsheetCell(path, cell, value)
    return NextResponse.json(res)
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}
