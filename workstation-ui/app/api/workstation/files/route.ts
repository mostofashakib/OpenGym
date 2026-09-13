import { NextRequest, NextResponse } from "next/server"
import { listFiles, readFile, writeFile } from "@/lib/workstation-client"

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const path = searchParams.get("path")
  const directory = searchParams.get("dir") || "/"

  try {
    if (path) {
      const res = await readFile(path)
      return NextResponse.json(res)
    }
    const res = await listFiles(directory)
    return NextResponse.json(res)
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { path, content } = body
    const res = await writeFile(path, content)
    return NextResponse.json(res)
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}
