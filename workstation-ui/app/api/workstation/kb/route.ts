import { NextRequest, NextResponse } from "next/server"
import { searchKb, getKbArticle } from "@/lib/workstation-client"

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const articleId = searchParams.get("id")
  const query = searchParams.get("q") || ""

  try {
    if (articleId) {
      const res = await getKbArticle(articleId)
      return NextResponse.json(res)
    }
    const res = await searchKb(query)
    return NextResponse.json(res)
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}
