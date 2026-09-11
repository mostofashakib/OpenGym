import { type NextRequest, NextResponse } from "next/server"
import { getState, setState, type GlobalState } from "@/lib/store"

export const dynamic = "force-dynamic"
export const runtime = "nodejs"

// Return state; if ?ascii=true, escape non-ASCII as \uXXXX for deterministic files
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const ascii = (searchParams.get("ascii") || "").toLowerCase()
  const state = getState()
  if (ascii === "1" || ascii === "true" || ascii === "yes") {
    const body = toAsciiJson(state) + "\n"
    return new Response(body, { status: 200, headers: { "content-type": "application/json; charset=utf-8" } })
  }
  return NextResponse.json(state)
}

function toAsciiJson(value: unknown): string {
  const json = JSON.stringify(value)
  return json.replace(/[\u0080-\uFFFF]/g, (ch) => {
    const code = ch.charCodeAt(0)
    return "\\u" + code.toString(16).padStart(4, "0")
  })
}

export async function POST(request: NextRequest) {
  try {
    const incoming = (await request.json()) as any
    const newState = normalizeIncomingState(incoming) as GlobalState

    const validation = validateGlobalState(newState)
    if (!validation.valid) {
      return NextResponse.json(
        { error: "Invalid state", details: validation.errors },
        { status: 400 },
      )
    }

    setState(newState)
    return NextResponse.json({ success: true })
  } catch (error) {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 })
  }
}

function validateGlobalState(data: unknown): { valid: boolean; errors: string[] } {
  if (!data || typeof data !== "object") {
    return { valid: false, errors: ["State must be an object"] }
  }
  const obj = data as any
  const errors: string[] = []

  if (!Array.isArray(obj.messages)) errors.push("messages must be an array")
  if (!Array.isArray(obj.threads)) errors.push("threads must be an array")
  if (!Array.isArray(obj.labels)) errors.push("labels must be an array")
  if (!obj.settings || typeof obj.settings !== "object") errors.push("settings must be an object")

  const hasContacts =
    (obj.contacts && typeof obj.contacts === "object") ||
    (obj.users && typeof obj.users === "object")
  if (!hasContacts) errors.push("contacts must be an object")

  return { valid: errors.length === 0, errors }
}

function normalizeIncomingState(raw: any): any {
  try {
    if (!raw || typeof raw !== "object") return raw
    if (!raw.contacts && raw.users && typeof raw.users === "object") {
      raw.contacts = raw.users
    }
  } catch {}
  return raw
}
