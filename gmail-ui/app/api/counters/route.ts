import { NextResponse } from "next/server"
import { getUnreadCounts } from "@/lib/store"

export async function GET() {
  const counts = getUnreadCounts()
  return NextResponse.json(counts)
}

export const dynamic = "force-dynamic"
export const runtime = "nodejs"
