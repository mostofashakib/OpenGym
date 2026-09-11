import { NextResponse } from "next/server"
import { listThreads } from "@/lib/store"

// GET /api/threads
export async function GET() {
  return NextResponse.json({ threads: listThreads() })
}

export const dynamic = "force-dynamic"
