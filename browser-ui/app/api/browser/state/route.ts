import { NextResponse } from "next/server"
import { exportStateData } from "@/lib/browser-client"

export async function GET() {
  try {
    const data = await exportStateData()
    return NextResponse.json(data)
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}
