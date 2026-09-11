"use client"

import { useEffect, useMemo, useState } from "react"
import { useParams, useRouter, useSearchParams } from "next/navigation"
import { EmailThreadView } from "@/components/email-thread-view"
import { decodeForDisplay } from "@/lib/utils"
import { ComposeModal } from "@/components/compose-modal"

interface ThreadEmail {
  id: string
  sender: string
  senderEmail: string
  recipient: string
  to: string[]
  cc?: string[]
  bcc?: string[]
  subject: string
  body: string
  bodyHtml?: string
  timestamp: string
  isRead: boolean
  isStarred: boolean
  hasAttachment?: boolean
  attachments?: Array<{ name: string; size: string }>
  labels?: string[]
}

interface EmailThread {
  id: string
  subject: string
  participants: string[]
  messageCount: number
  lastActivity: string
  messages: ThreadEmail[]
  isStarred: boolean
}

const parseSenderName = (from: string) => {
  const match = from.match(/^([^<]+)</)
  return match ? match[1].trim() : from
}

export default function ThreadPage() {
  const params = useParams<{ id: string }>()
  const router = useRouter()
  const search = useSearchParams()
  const [thread, setThread] = useState<EmailThread | null>(null)
  const [showCompose, setShowCompose] = useState(false)
  const [composeMode, setComposeMode] = useState<"compose" | "reply" | "replyAll" | "forward">("compose")
  const [composeInitials, setComposeInitials] = useState<{
    to?: string
    cc?: string
    bcc?: string
    subject?: string
    body?: string
  }>({})
  const [showDraftEditor, setShowDraftEditor] = useState(false)
  const [ownEmail, setOwnEmail] = useState<string>("you@example.com")
  const [composeCloseSignal, setComposeCloseSignal] = useState(0)
  const [pendingBackAfterClose, setPendingBackAfterClose] = useState(false)

  const threadId = useMemo(() => (typeof params?.id === "string" ? params.id : Array.isArray(params?.id) ? params.id[0] : ""), [params])

  const extractEmail = (from: unknown): string => {
    const s = typeof from === "string" ? from : ""
    const m = s.match(/<([^>]+)>/)
    if (m && m[1]) return m[1].trim()
    const trimmed = s.trim()
    return trimmed.includes("@") ? trimmed : ""
  }

  const ensureReplyPrefix = (subject: string | undefined | null): string => {
    const s = (subject || "").trim()
    // If subject already starts with some form of "Re:", don't add again
    if (/^re\s*:/i.test(s)) return s
    return `Re: ${s}`
  }

  useEffect(() => {
    if (!threadId) return

    let cancelled = false
    const load = async () => {
      try {
        // Try to load as a thread first
        const res = await fetch(`/api/threads/${threadId}`)
        if (res.ok) {
          const data = await res.json()
          const t = data.thread
          const mapped: EmailThread = {
            id: t.id,
            subject: t.subject,
            participants: t.participants ?? [],
            messageCount: t.messageIds ? t.messageIds.length : t.messageCount ?? 1,
            lastActivity: t.lastActivity ?? "",
            isStarred: Boolean(t.isStarred),
            messages: (t.messages || []).map((m: any) => ({
              id: m.id,
              sender: parseSenderName(m.from || ""),
              senderEmail: extractEmail(m.from),
              recipient: (m.to || []).join(", "),
              to: Array.isArray(m.to) ? m.to : [],
              cc: Array.isArray(m.cc) ? m.cc : [],
              bcc: Array.isArray(m.bcc) ? m.bcc : [],
              subject: m.subject ?? "",
              body: decodeForDisplay(m.text || ""),
              bodyHtml: typeof m.html === "string" ? decodeForDisplay(m.html) : undefined,
              timestamp: m.date ?? "",
              isRead: Boolean(m.isRead),
              isStarred: Boolean(m.isStarred),
              hasAttachment: Array.isArray(m.attachments) && m.attachments.length > 0,
              attachments: Array.isArray(m.attachments)
                ? m.attachments.map((a: any) => ({ name: a.filename, size: `${Math.round((a.size || 0) / 1024)} KB` }))
                : [],
              labels: Array.isArray(m.labelIds) ? m.labelIds : [],
            })),
          }
          if (!cancelled) {
            setThread(mapped)
            const drafts = mapped.messages.filter((m: any) => Array.isArray(m?.labels) && m.labels.includes("DRAFTS"))
            setShowDraftEditor(drafts.length > 0)
          }
          return
        }
        // Fallback: try loading as a single message and synthesize thread
        const mres = await fetch(`/api/emails/${threadId}`)
        if (mres.ok) {
          const { message: msg } = await mres.json()
          const mapped: EmailThread = {
            id: (msg?.threadId as string) || threadId,
            subject: msg?.subject ?? "",
            participants: [],
            messageCount: 1,
            lastActivity: msg?.date ?? "",
            isStarred: Boolean(msg?.isStarred),
            messages: [
              {
                id: msg?.id,
                sender: parseSenderName(msg?.from || ""),
                senderEmail: extractEmail(msg?.from),
                recipient: (msg?.to || []).join(", "),
                to: Array.isArray(msg?.to) ? msg.to : [],
                cc: Array.isArray(msg?.cc) ? msg.cc : [],
                bcc: Array.isArray(msg?.bcc) ? msg.bcc : [],
                subject: msg?.subject ?? "",
                body: decodeForDisplay(msg?.text || ""),
                bodyHtml: typeof msg?.html === "string" ? decodeForDisplay(msg.html as string) : undefined,
                timestamp: msg?.date ?? "",
                isRead: Boolean(msg?.isRead),
                isStarred: Boolean(msg?.isStarred),
                hasAttachment: Array.isArray(msg?.attachments) && msg.attachments.length > 0,
                attachments: Array.isArray(msg?.attachments)
                  ? msg.attachments.map((a: any) => ({ name: a.filename, size: `${Math.round((a.size || 0) / 1024)} KB` }))
                  : [],
              },
            ],
          }
          if (!cancelled) {
            setThread(mapped)
            const drafts = mapped.messages.filter((m: any) => Array.isArray(m?.labels) && m.labels.includes("DRAFTS"))
            setShowDraftEditor(drafts.length > 0)
          }
          return
        }
        // If neither thread nor message exists, navigate back to list view
        const from = (search?.get("from") || "inbox").toLowerCase()
        const sp = new URLSearchParams()
        sp.set("folder", from)
        for (const k of ["search", "ps", "pi"]) {
          const v = search?.get(k)
          if (v) sp.set(k, v)
        }
        router.replace(`/?${sp.toString()}`)
      } catch {}
    }
    load()
    return () => {
      cancelled = true
    }
  }, [threadId])

  // Load own email for reply-all exclusion
  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const res = await fetch("/api/settings")
        const data = await res.json()
        if (!cancelled && data?.settings?.email) setOwnEmail(String(data.settings.email))
      } catch {}
    })()
    return () => {
      cancelled = true
    }
  }, [])

  // Mark messages as read when viewing
  useEffect(() => {
    if (!thread) return
    thread.messages.forEach((m) => {
      if (!m.isRead) {
        fetch(`/api/emails/${m.id}`, {
          method: "PUT",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ isRead: true }),
        }).catch(() => {})
      }
    })
  }, [thread])

  const navigateBack = () => {
    const from = (search?.get("from") || "inbox").toLowerCase()
    const sp = new URLSearchParams()
    sp.set("folder", from)
    for (const k of ["search", "ps", "pi"]) {
      const v = search?.get(k)
      if (v) sp.set(k, v)
    }
    router.replace(`/?${sp.toString()}`)
  }

  const handleBack = () => {
    // If a reply/forward composer is open, request it to save as draft before navigating
    if (showCompose && (composeMode === "reply" || composeMode === "replyAll" || composeMode === "forward")) {
      setPendingBackAfterClose(true)
      setComposeCloseSignal((s) => s + 1)
      return
    }
    navigateBack()
  }

  const handleReply = (messageId: string) => {
    if (!thread) return
    const target = thread.messages.find((m) => m.id === messageId) || thread.messages[thread.messages.length - 1]
    const to = extractEmail(target?.senderEmail || target?.sender || target?.recipient || "")
    setComposeMode("reply")
    setComposeInitials({
      to,
      subject: ensureReplyPrefix(thread.subject),
      body: "\n\n",
    })
    setShowCompose(true)
  }

  const handleReplyAll = (messageId: string) => {
    if (!thread) return
    const target = thread.messages.find((m) => m.id === messageId) || thread.messages[thread.messages.length - 1]
    const recipientsSet = new Set<string>()
    // include sender
    const senderAddr = extractEmail(target?.senderEmail || target?.sender || "")
    if (senderAddr) recipientsSet.add(senderAddr)
    // include all original to and cc for the target message
    for (const r of target?.to || []) recipientsSet.add(r)
    for (const r of target?.cc || []) recipientsSet.add(r)
    // exclude self
    for (const r of Array.from(recipientsSet)) {
      if (r.toLowerCase().includes(ownEmail)) recipientsSet.delete(r)
    }
    const to = Array.from(recipientsSet).join(", ")
    setComposeMode("replyAll")
    setComposeInitials({
      to,
      subject: ensureReplyPrefix(thread.subject),
      body: "\n\n",
    })
    setShowCompose(true)
  }

  const handleForward = (messageId: string) => {
    if (!thread) return
    const target = thread.messages.find((m) => m.id === messageId) || thread.messages[thread.messages.length - 1]
    const headerLines = [
      "---------- Forwarded message ----------",
      target?.sender && target?.senderEmail ? `From: ${target.sender} <${target.senderEmail}>` : "",
      target?.timestamp ? `Date: ${new Date(target.timestamp).toLocaleString()}` : "",
      thread.subject ? `Subject: ${thread.subject}` : "",
      target?.recipient ? `To: ${target.recipient}` : "",
    ].filter(Boolean)
    const quoted = `${headerLines.join("\n")}\n\n${target?.body || ""}`
    setComposeMode("forward")
    setComposeInitials({
      to: "",
      subject: thread.subject ? `Fwd: ${thread.subject}` : "Fwd:",
      body: `\n\n${quoted}`,
    })
    setShowCompose(true)
  }

  const handleStar = async (tid: string) => {
    try {
      const nextIsStarred = !(thread?.isStarred ?? false)
      const latest = thread?.messages[thread.messages.length - 1]
      if (latest) {
        if (nextIsStarred) {
          await fetch(`/api/emails/${latest.id}`, {
            method: "PUT",
            headers: { "content-type": "application/json" },
            body: JSON.stringify({ addLabel: "STARRED" }),
          })
        } else {
          await fetch(`/api/emails/${latest.id}`, {
            method: "PUT",
            headers: { "content-type": "application/json" },
            body: JSON.stringify({ removeLabel: "STARRED" }),
          })
        }
      }
      if (thread) {
        const updatedMessages = thread.messages.map((m, idx) => {
          if (nextIsStarred) {
            const isLast = idx === thread.messages.length - 1
            return { ...m, isStarred: isLast }
          }
          return { ...m, isStarred: false }
        })
        setThread({ ...thread, isStarred: nextIsStarred, messages: updatedMessages })
      }
    } catch {}
  }

  const handleToggleMessageStar = async (messageId: string, nextIsStarred: boolean) => {
    try {
      await fetch(`/api/emails/${messageId}`, {
        method: "PUT",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ isStarred: nextIsStarred }),
      })
      if (thread) {
        const updatedMessages = thread.messages.map((m) => (m.id === messageId ? { ...m, isStarred: nextIsStarred } : m))
        const anyStarred = updatedMessages.some((m) => m.isStarred)
        setThread({ ...thread, isStarred: anyStarred, messages: updatedMessages })
      }
    } catch {}
  }

  const handleArchive = async (tid: string) => {
    try {
      const latest = thread?.messages[thread.messages.length - 1]
      if (latest) {
        await fetch(`/api/emails/${latest.id}`, {
          method: "PUT",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ action: "archive" }),
        })
      }
      const from = (search?.get("from") || "inbox").toLowerCase()
      const sp = new URLSearchParams()
      sp.set("folder", from)
      for (const k of ["search", "ps", "pi"]) {
        const v = search?.get(k)
        if (v) sp.set(k, v)
      }
      router.replace(`/?${sp.toString()}`)
    } catch {}
  }

  const handleDelete = async (tid: string) => {
    try {
      const latest = thread?.messages[thread.messages.length - 1]
      if (latest) {
        await fetch(`/api/emails/${latest.id}`, {
          method: "PUT",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ action: "trash" }),
        })
      }
      const from = (search?.get("from") || "inbox").toLowerCase()
      const sp = new URLSearchParams()
      sp.set("folder", from)
      for (const k of ["search", "ps", "pi"]) {
        const v = search?.get(k)
        if (v) sp.set(k, v)
      }
      router.replace(`/?${sp.toString()}`)
    } catch {}
  }

  const handleSend = async (emailData: { to: string; cc?: string; bcc?: string; subject: string; body: string; htmlBody?: string }) => {
    try {
      if (!thread) return
      // Draft send path: if any draft exists in the thread, send the newest draft
      const drafts = thread.messages.filter((m: any) => Array.isArray(m?.labels) && m.labels.includes("DRAFTS"))
      const latestDraft = drafts[drafts.length - 1]
      if (latestDraft) {
        await fetch(`/api/drafts/${latestDraft.id}/send`, {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({
            to: (emailData.to || "").split(/[;,]+/).map((s) => s.trim()).filter(Boolean),
            cc: (emailData.cc || "").split(/[;,]+/).map((s) => s.trim()).filter(Boolean) || undefined,
            bcc: (emailData.bcc || "").split(/[;,]+/).map((s) => s.trim()).filter(Boolean) || undefined,
            subject: emailData.subject,
            text: emailData.body,
            html: emailData.htmlBody,
          }),
        })
        setShowCompose(false)
        setShowDraftEditor(false)
        // Reload thread
        const res = await fetch(`/api/threads/${thread.id}`)
        if (res.ok) {
          const data = await res.json()
          const t = data.thread
          const mapped: EmailThread = {
            id: t.id,
            subject: t.subject,
            participants: t.participants ?? [],
            messageCount: t.messageIds ? t.messageIds.length : t.messageCount ?? 1,
            lastActivity: t.lastActivity ?? "",
            isStarred: Boolean(t.isStarred),
            messages: (t.messages || []).map((m: any) => ({
              id: m.id,
              sender: parseSenderName(m.from || ""),
              senderEmail: extractEmail(m.from),
              recipient: (m.to || []).join(", "),
              to: Array.isArray(m.to) ? m.to : [],
              cc: Array.isArray(m.cc) ? m.cc : [],
              bcc: Array.isArray(m.bcc) ? m.bcc : [],
              subject: m.subject ?? "",
              body: decodeForDisplay(m.text || ""),
              bodyHtml: typeof m.html === "string" ? decodeForDisplay(m.html) : undefined,
              timestamp: m.date ?? "",
              isRead: Boolean(m.isRead),
              isStarred: Boolean(m.isStarred),
              hasAttachment: Array.isArray(m.attachments) && m.attachments.length > 0,
              attachments: Array.isArray(m.attachments)
                ? m.attachments.map((a: any) => ({ name: a.filename, size: `${Math.round((a.size || 0) / 1024)} KB` }))
                : [],
              labels: Array.isArray(m.labelIds) ? m.labelIds : [],
            })),
          }
          setThread(mapped)
        }
        return
      }
      if (composeMode === "forward") {
        // Create a new thread with same parent id
        await fetch(`/api/emails`, {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({
            to: (emailData.to || "").split(/[;,]+/).map((s) => s.trim()).filter(Boolean),
            cc: (emailData.cc || "").split(/[;,]+/).map((s) => s.trim()).filter(Boolean) || undefined,
            bcc: (emailData.bcc || "").split(/[;,]+/).map((s) => s.trim()).filter(Boolean) || undefined,
            subject: emailData.subject,
            text: emailData.body,
            html: emailData.htmlBody,
            parentThreadId: (thread as any).parentThreadId || thread.id,
          }),
        })
        setShowCompose(false)
        return
      }

      // Reply or reply all within the same thread
      await fetch(`/api/threads/${thread.id}/messages`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          body: emailData.body,
          html: emailData.htmlBody,
          to: (emailData.to || "").split(/[;,]+/).map((s) => s.trim()).filter(Boolean),
          cc: (emailData.cc || "").split(/[;,]+/).map((s) => s.trim()).filter(Boolean) || undefined,
          bcc: (emailData.bcc || "").split(/[;,]+/).map((s) => s.trim()).filter(Boolean) || undefined,
        }),
      })
      setShowCompose(false)
      // Reload thread to include the new message
      const res = await fetch(`/api/threads/${thread.id}`)
      if (res.ok) {
        const data = await res.json()
        const t = data.thread
        const mapped: EmailThread = {
          id: t.id,
          subject: t.subject,
          participants: t.participants ?? [],
          messageCount: t.messageIds ? t.messageIds.length : t.messageCount ?? 1,
          lastActivity: t.lastActivity ?? "",
          isStarred: Boolean(t.isStarred),
          messages: (t.messages || []).map((m: any) => ({
            id: m.id,
            sender: parseSenderName(m.from || ""),
            senderEmail: extractEmail(m.from),
            recipient: (m.to || []).join(", "),
            to: Array.isArray(m.to) ? m.to : [],
            cc: Array.isArray(m.cc) ? m.cc : [],
            bcc: Array.isArray(m.bcc) ? m.bcc : [],
            subject: m.subject ?? "",
            body: decodeForDisplay(m.text || ""),
            bodyHtml: typeof m.html === "string" ? decodeForDisplay(m.html) : undefined,
            timestamp: m.date ?? "",
            isRead: Boolean(m.isRead),
            isStarred: Boolean(m.isStarred),
            hasAttachment: Array.isArray(m.attachments) && m.attachments.length > 0,
            attachments: Array.isArray(m.attachments)
              ? m.attachments.map((a: any) => ({ name: a.filename, size: `${Math.round((a.size || 0) / 1024)} KB` }))
              : [],
          })),
        }
        setThread(mapped)
      }
    } catch {}
  }

  const handleDraftClose = () => {
    // While editing a draft inside a thread, closing should keep you on the thread view.
    setShowDraftEditor(false)
  }

  const handleComposeClose = () => {
    // When replying/forwarding within a thread, closing should show the thread view; if back was pressed, navigate
    setShowCompose(false)
    if (pendingBackAfterClose) {
      setPendingBackAfterClose(false)
      navigateBack()
    }
  }

  if (!thread) return null

  return (
    <div className="h-screen flex flex-col ">
      {/* If latest message is a draft, show compose UI prefilled for editing */}
      {(() => {
        const draftMessages = thread.messages.filter((m: any) => Array.isArray(m?.labels) && m.labels.includes("DRAFTS"))
        const hasDraft = draftMessages.length > 0
        if (hasDraft) {
          const latestDraft = draftMessages[draftMessages.length - 1]
          const hasNonDraft = thread.messages.some(
            (m: any) => !Array.isArray(m?.labels) || !(m as any).labels!.includes("DRAFTS"),
          )
          return (
            <>
              <EmailThreadView
                thread={thread}
                onBack={handleBack}
                onReply={handleReply}
                onReplyAll={handleReplyAll}
                onForward={handleForward}
                onStar={handleStar}
                onArchive={handleArchive}
                onDelete={handleDelete}
                onMessageStarToggle={handleToggleMessageStar}
                hideMessageIds={draftMessages.map((d: any) => d.id)}
              />
              <ComposeModal
                isOpen={showDraftEditor}
                onClose={handleDraftClose}
                onSend={handleSend}
                mode={"compose"}
                variant={hasNonDraft ? "inline" : "overlay"}
                initialTo={(latestDraft.to || []).join(", ")}
                initialCc={(latestDraft.cc || []).join(", ")}
                initialBcc={""}
                initialSubject={latestDraft.subject || ""}
                initialBody={latestDraft.body || ""}
                draftId={latestDraft.id}
                parentThreadId={thread.id}
              />
            </>
          )
        }
        return (
          <>
            <EmailThreadView
              thread={thread}
              onBack={handleBack}
              onReply={handleReply}
              onReplyAll={handleReplyAll}
              onForward={handleForward}
              onStar={handleStar}
              onArchive={handleArchive}
              onDelete={handleDelete}
              onMessageStarToggle={handleToggleMessageStar}
            />
            <ComposeModal
              isOpen={showCompose}
              onClose={handleComposeClose}
              onSend={handleSend}
              mode={composeMode}
              variant={"inline"}
              externalCloseSignal={composeCloseSignal}
              initialTo={composeInitials.to}
              initialCc={composeInitials.cc}
              initialBcc={composeInitials.bcc}
              initialSubject={composeInitials.subject}
              initialBody={composeInitials.body}
              parentThreadId={thread.id}
            />
          </>
        )
      })()}
    </div>
  )
}
