import { NextResponse, type NextRequest } from "next/server"
import { composeEmail, listEmails, getSettings, getThread } from "@/lib/store"

// GET /api/emails
// Query params:
// - folder: inbox|sent|drafts|trash|archive|spam|all
// - starred: true|false
// - unread: true|false
// - label: string
// - q: string (search)
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const folderParam = searchParams.get("folder") as "inbox" | "sent" | "drafts" | "trash" | "archive" | "spam" | "all" | null
  const starredParam = searchParams.get("starred")
  const importantParam = searchParams.get("important")
  const unreadParam = searchParams.get("unread")
  const label = searchParams.get("label") || undefined
  const q = searchParams.get("q") || undefined
  const fromParam = searchParams.get("from") || undefined
  const toParam = searchParams.get("to") || undefined
  const ccParam = searchParams.get("cc") || undefined
  const bccParam = searchParams.get("bcc") || undefined
  const subjectParam = searchParams.get("subject") || undefined
  const hasAttachmentParam = (() => {
    const v = searchParams.get("hasAttachment") ?? searchParams.get("has")
    if (!v) return undefined
    if (v.toLowerCase() === "attachment" || v.toLowerCase() === "attachments") return true
    if (v.toLowerCase() === "true") return true
    if (v.toLowerCase() === "false") return false
    return undefined
  })()
  const beforeParam = searchParams.get("before") || undefined
  const afterParam = searchParams.get("after") || undefined
  const newerThanParam = searchParams.get("newer_than") || undefined
  const olderThanParam = searchParams.get("older_than") || undefined
  const filenameParam = searchParams.get("filename") || undefined
  const sizeParam = searchParams.get("size") || undefined
  const largerParam = searchParams.get("larger") || undefined
  const smallerParam = searchParams.get("smaller") || undefined
  const hasTypeParam = searchParams.get("hasType") || undefined
  const listParam = searchParams.get("list") || undefined
  const snoozedParam = searchParams.get("snoozed") || undefined
  const anywhereParam = searchParams.get("anywhere") || undefined
  const exprParam = searchParams.get("expr") || undefined

  const baseFilters = {
    folder: (folderParam as any) || undefined,
    starred: starredParam === null ? undefined : starredParam === "true",
    important: importantParam === null ? undefined : importantParam === "true",
    unread: unreadParam === null ? undefined : unreadParam === "true",
    label,
    q,
    from: fromParam,
    to: toParam,
    cc: ccParam,
    bcc: bccParam,
    subject: subjectParam,
    hasAttachment: hasAttachmentParam,
    before: beforeParam,
    after: afterParam,
    newerThan: newerThanParam,
    olderThan: olderThanParam,
    filename: filenameParam,
    size: sizeParam,
    larger: largerParam,
    smaller: smallerParam,
    hasType: (hasTypeParam as any) || undefined,
    list: listParam,
    snoozed: snoozedParam === "true",
    includeTrashSpam: anywhereParam === "true",
  } as const

  // Advanced boolean/exclude handling for expression input (minimal OR and minus support)
  const evaluateExpr = (expr: string) => {
    // Split on uppercase OR at top level (basic)
    const parts = expr
      .replace(/[()]/g, " ")
      .split(/\s+OR\s+/)
      .map((s) => s.trim())
      .filter(Boolean)
    const union = new Map<string, any>()
    const tokenRe = new RegExp(
      String.raw`(?:^|\s)(-?)(in|from|to|cc|bcc|subject|label|has|is|before|after|newer_than|older_than|filename|size|larger|smaller|list):(\"[^\"]+\"|[^\s]+)`,
      "gi",
    )
    for (const part of parts.length > 0 ? parts : [expr]) {
      const ops: Record<string, any> = { has: [] as string[], is: [] as string[] }
      let m: RegExpExecArray | null
      while ((m = tokenRe.exec(part)) !== null) {
        const neg = (m[1] || "").length > 0
        const key = (m[2] || "").toLowerCase()
        let value = m[3] || ""
        if (value.startsWith('"') && value.endsWith('"')) value = value.slice(1, -1)
        if (neg) {
          const arrKey = `exclude_${key}`
          if (!Array.isArray((ops as any)[arrKey])) (ops as any)[arrKey] = []
          ;(ops as any)[arrKey].push(value)
        } else if (key === "has" || key === "is") {
          ;(ops as any)[key].push(value)
        } else {
          ;(ops as any)[key] = value
        }
      }
      // Build filters for this disjunct
      const f: any = { ...baseFilters }
      if (ops.in) {
        const v = String(ops.in).toLowerCase()
        if (["inbox", "sent", "drafts", "trash", "spam", "all", "important"].includes(v)) f.folder = v
        else if (v === "anywhere") {
          f.folder = "all"
          f.includeTrashSpam = true
        } else f.label = ops.in
      }
      if (ops.from) f.from = ops.from
      if (ops.to) f.to = ops.to
      if (ops.cc) f.cc = ops.cc
      if (ops.bcc) f.bcc = ops.bcc
      if (ops.subject) f.subject = ops.subject
      if (ops.label) f.label = ops.label
      if (ops.filename) f.filename = ops.filename
      if (ops.size) f.size = ops.size
      if (ops.larger) f.larger = ops.larger
      if (ops.smaller) f.smaller = ops.smaller
      if (ops.list) f.list = ops.list
      if (ops.before) f.before = ops.before
      if (ops.after) f.after = ops.after
      if (ops.newer_than) f.newerThan = ops.newer_than
      if (ops.older_than) f.olderThan = ops.older_than
      if (Array.isArray(ops.has)) {
        if (ops.has.includes("attachment")) f.hasAttachment = true
        const map: Record<string, string> = { drive: "drive", document: "document", spreadsheet: "spreadsheet", presentation: "presentation" }
        for (const k of Object.keys(map)) if (ops.has.includes(k)) (f as any).hasType = map[k]
      }
      if (Array.isArray(ops.is)) {
        if (ops.is.includes("unread")) f.unread = true
        if (ops.is.includes("starred")) f.starred = true
        if (ops.is.includes("important")) f.important = true
        if (ops.is.includes("snoozed")) f.snoozed = true
      }
      // Base text for this part: remove tokens
      const base = part.replace(tokenRe, " ").replace(/\s+/g, " ").trim()
      if (base.length > 0) f.q = base
      // Evaluate and union
      const res = listEmails(f)
      for (const m of res) union.set(m.id, m)
      // Apply excludes
      const matchesNeedle = (s: string | undefined, n: string) => String(s || "").toLowerCase().includes(n)
      const excludeFrom: string[] = (ops as any).exclude_from || []
      const excludeTo: string[] = (ops as any).exclude_to || []
      const excludeCc: string[] = (ops as any).exclude_cc || []
      const excludeBcc: string[] = (ops as any).exclude_bcc || []
      const excludeSubject: string[] = (ops as any).exclude_subject || []
      const excludeLabel: string[] = (ops as any).exclude_label || []
      const excludeFilename: string[] = (ops as any).exclude_filename || []
      const excludeList: string[] = (ops as any).exclude_list || []
      if (
        excludeFrom.length || excludeTo.length || excludeCc.length || excludeBcc.length || excludeSubject.length || excludeLabel.length || excludeFilename.length || excludeList.length
      ) {
        for (const id of Array.from(union.keys())) {
          const msg: any = union.get(id)
          const toArr = Array.isArray(msg?.to) ? msg.to : []
          const ccArr = Array.isArray(msg?.cc) ? msg.cc : []
          const bccArr = Array.isArray(msg?.bcc) ? msg.bcc : []
          const labels = Array.isArray(msg?.labelIds) ? msg.labelIds : []
          const files = Array.isArray(msg?.attachments) ? msg.attachments : []
          const fail =
            excludeFrom.some((n) => matchesNeedle(msg?.from, n.toLowerCase())) ||
            excludeTo.some((n) => toArr.some((t: any) => matchesNeedle(String(t), n.toLowerCase()))) ||
            excludeCc.some((n) => ccArr.some((t: any) => matchesNeedle(String(t), n.toLowerCase()))) ||
            excludeBcc.some((n) => bccArr.some((t: any) => matchesNeedle(String(t), n.toLowerCase()))) ||
            excludeSubject.some((n) => matchesNeedle(msg?.subject, n.toLowerCase())) ||
            excludeLabel.some((n) => labels.map((l: any) => String(l).toLowerCase()).includes(n.toLowerCase())) ||
            excludeFilename.some((n) => files.some((a: any) => matchesNeedle(String(a?.filename || ""), n.toLowerCase()))) ||
            excludeList.some((n) =>
              matchesNeedle(msg?.from, n.toLowerCase()) ||
              toArr.some((t: any) => matchesNeedle(String(t), n.toLowerCase())) ||
              ccArr.some((t: any) => matchesNeedle(String(t), n.toLowerCase())) ||
              bccArr.some((t: any) => matchesNeedle(String(t), n.toLowerCase())),
            )
          if (fail) union.delete(id)
        }
      }
    }
    return Array.from(union.values())
  }

  const emails = exprParam ? evaluateExpr(exprParam) : listEmails(baseFilters as any)
  let messages = emails
  // Special handling for "Inbox": include your Sent messages that belong to these inbox threads
  if (folderParam === "inbox") {
    const inboxThreadIds = new Set(
      emails
        .map((m: any) => (typeof m.threadId === "string" ? m.threadId : null))
        .filter(Boolean) as string[],
    )
    if (inboxThreadIds.size > 0) {
      const sentForThreads = listEmails({ folder: "sent" }).filter((m: any) => inboxThreadIds.has(m.threadId))
      // merge without duplicates
      const byId = new Map<string, any>()
      for (const m of [...emails, ...sentForThreads]) byId.set(m.id, m)
      // overwrite messages with merged view
      messages = Array.from(byId.values())
    }
  }
  
  // Operator-only expansion for thread context: when using address/subject/attachment operators
  // without a free-text query, include all messages from matching threads so the UI can
  // display the latest message in each matching thread (Gmail-like behavior).
  if (folderParam === "all" && !exprParam) {
    const operatorApplied = Boolean(
      fromParam || toParam || ccParam || bccParam || subjectParam || typeof hasAttachmentParam === "boolean",
    )
    const hasFreeText = Boolean(q && q.trim().length > 0)
    if (operatorApplied && !hasFreeText) {
      const tids = new Set(
        (messages || [])
          .map((m: any) => (typeof m?.threadId === "string" ? m.threadId : typeof m?.id === "string" ? m.id : null))
          .filter(Boolean) as string[],
      )
      if (tids.size > 0) {
        const baseAll = listEmails({}) as any[]
        const hasLabel = (m: any, l: string) => Array.isArray(m?.labelIds) && m.labelIds.includes(l)
        const notTrashOrSpam = (m: any) => !hasLabel(m, "TRASH") && !hasLabel(m, "SPAM")
        const expanded = baseAll.filter((m: any) => notTrashOrSpam(m) && tids.has(m.threadId))
        if (expanded.length > 0) messages = expanded
      }
    }
  }
  // Special handling for "All Mail":
  // - When searching (q present), treat as a global search across ALL folders (including Trash/Spam)
  //   while still respecting other filters (starred, important, unread, label).
  // - Otherwise, only include messages you've received and their associated threads, excluding TRASH and SPAM.
  if (folderParam === "all" && !exprParam) {
    if (q && q.trim().length > 0) {
      const starred = starredParam === null ? undefined : starredParam === "true"
      const important = importantParam === null ? undefined : importantParam === "true"
      const unread = unreadParam === null ? undefined : unreadParam === "true"
      messages = listEmails({ q, starred, important, unread, label: label || undefined })
      return NextResponse.json({ messages })
    }
    const me = String(getSettings().email || "you@example.com").toLowerCase()
    const extract = (from: string | undefined) => {
      if (typeof from !== "string") return ""
      const match = from.match(/<([^>]+)>/)
      const addr = (match ? match[1] : from).trim().toLowerCase()
      return addr
    }
    const notYou = (from: string | undefined) => {
      const addr = extract(from)
      return addr !== me
    }
    const hasLabel = (m: any, label: string) => Array.isArray(m?.labelIds) && m.labelIds.includes(label)
    const notTrashOrSpam = (m: any) => !hasLabel(m, "TRASH") && !hasLabel(m, "SPAM")
    const receivedThreadIds = new Set(
      emails
        .filter((m: any) => notYou(m.from) && notTrashOrSpam(m))
        .map((m: any) => (typeof m.threadId === "string" ? m.threadId : null))
        .filter(Boolean),
    )
    messages = emails.filter(
      (m: any) =>
        notTrashOrSpam(m) &&
        (notYou(m.from) || (typeof m.threadId === "string" && receivedThreadIds.has(m.threadId))),
    )

    // When performing a search (q present), also include Sent messages that match q
    // even if they don't belong to a thread with received mail. Exclude TRASH/SPAM.
    if (q && q.trim().length > 0) {
      const searchMatches = listEmails({ q })
      const extraSent = searchMatches.filter(
        (m: any) => hasLabel(m, "SENT") && notTrashOrSpam(m),
      )
      // Merge without duplicates
      const byId = new Map<string, any>()
      for (const m of [...messages, ...extraSent]) byId.set(m.id, m)
      messages = Array.from(byId.values())
    }
  }
  // Attach thread-level star aggregation so the UI can render star if any message is starred
  const threadIsStarredById: Record<string, boolean> = {}
  try {
    for (const m of messages || []) {
      const tid = (m as any)?.threadId || (m as any)?.id
      if (typeof tid === "string" && threadIsStarredById[tid] === undefined) {
        const t = getThread(tid)
        threadIsStarredById[tid] = Boolean(t?.isStarred)
      }
    }
  } catch {}
  return NextResponse.json({ messages, threadIsStarredById })
}

// POST /api/emails
// Body: { to: string[]; cc?: string[]; bcc?: string[]; subject: string; text: string; html?: string; attachments?: Attachment[] }
export async function POST(request: NextRequest) {
  try {
    const payload = (await request.json()) as {
      to?: string[]
      cc?: string[]
      bcc?: string[]
      subject?: string
      text?: string
      html?: string
      attachments?: Array<{ id: string; filename: string; mimeType: string; dataBase64: string; size: number }>
      parentThreadId?: string
    }

    // Allow empty body; require at least one recipient and a subject string
    if (
      !Array.isArray(payload.to) ||
      payload.to.length === 0 ||
      typeof payload.subject !== "string" ||
      typeof payload.text !== "string"
    ) {
      return NextResponse.json({ error: "Missing required fields" }, { status: 400 })
    }

    const { message, thread } = composeEmail({
      to: payload.to,
      cc: payload.cc,
      bcc: payload.bcc,
      subject: payload.subject,
      text: payload.text,
      html: typeof payload.html === "string" ? payload.html : undefined,
      attachments: payload.attachments,
      parentThreadId: payload.parentThreadId,
    })
    return NextResponse.json({ message, thread }, { status: 201 })
  } catch (err) {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 })
  }
}
export const dynamic = "force-dynamic"
export const runtime = "nodejs"
