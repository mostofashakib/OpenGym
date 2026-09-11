"use client"

import type React from "react"

import { useState, useRef } from "react"
import { useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

// Simple recipients input: plain text field, recipients separated by commas/semicolons.
// Defined at module scope so React preserves focus between renders.
export const RecipientsInput: React.FC<{
  label: string
  value: string
  onChange: (next: string) => void
  placeholder?: string
}> = ({ label, value, onChange, placeholder }) => {
  return (
    <div className="flex items-start gap-2">
      <label className="text-sm  w-12 mt-1.5">{label}</label>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder || ""}
        className="flex-1 outline-none text-sm py-1 border-0"
      />
    </div>
  )
}

type Contact = { email: string; name?: string }

function extractEmailAddress(value: string | undefined): string {
  if (typeof value !== "string" || value.length === 0) return ""
  const match = value.match(/<([^>]+)>/)
  const addr = (match ? match[1] : value).trim().toLowerCase()
  return addr
}

const RecipientsChipsInput: React.FC<{
  label: string
  value: string
  onChange: (next: string) => void
  placeholder?: string
  suggestions?: Contact[]
}> = ({ label, value, onChange, placeholder, suggestions }) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const [draft, setDraft] = useState("")
  const [open, setOpen] = useState(false)
  const [activeIndex, setActiveIndex] = useState(0)

  const tokens = (value || "")
    .split(/[;,]+/)
    .map((s) => s.trim())
    .filter(Boolean)

  const isLikelyRecipientToken = (s: string): boolean => {
    const trimmed = (s || "").trim()
    if (!trimmed) return false
    // If in display-name format like "Name <email@example.com>"
    if (/<[^>]+>/.test(trimmed)) return true
    // Simple email heuristic
    if (!trimmed.includes("@")) return false
    const [local, domain] = trimmed.split("@")
    if (!local || !domain) return false
    if (domain.length < 3 || !domain.includes(".")) return false
    return true
  }

  const commit = (token: string) => {
    const trimmed = (token || "").trim()
    if (!trimmed) return
    const next = Array.from(new Set([...
      tokens,
      trimmed,
    ]))
    onChange(next.join(", "))
    setDraft("")
    setActiveIndex(0)
  }

  const removeAt = (idx: number) => {
    const next = tokens.filter((_, i) => i !== idx)
    onChange(next.join(", "))
  }

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" || e.key === "," || e.key === ";") {
      e.preventDefault()
      if (open && filtered.length > 0) {
        const c = filtered[Math.max(0, Math.min(activeIndex, filtered.length - 1))]
        commit(c.name ? `${c.name} <${c.email}>` : c.email)
      } else {
        commit(draft)
      }
      return
    }
    if (e.key === " ") {
      // On space, commit only if suggestion is open or input looks like a valid recipient token
      if (open && filtered.length > 0) {
        e.preventDefault()
        const c = filtered[Math.max(0, Math.min(activeIndex, filtered.length - 1))]
        commit(c.name ? `${c.name} <${c.email}>` : c.email)
        return
      }
      if (isLikelyRecipientToken(draft)) {
        e.preventDefault()
        commit(draft)
        return
      }
    }
    if (e.key === "Backspace" && draft.length === 0 && tokens.length > 0) {
      e.preventDefault()
      removeAt(tokens.length - 1)
      return
    }
    if (e.key === "ArrowDown") {
      if (filtered.length > 0) {
        e.preventDefault()
        setActiveIndex((i) => Math.min(i + 1, filtered.length - 1))
      }
    }
    if (e.key === "ArrowUp") {
      if (filtered.length > 0) {
        e.preventDefault()
        setActiveIndex((i) => Math.max(i - 1, 0))
      }
    }
    if (e.key === "Tab" && draft.trim().length > 0) {
      if (filtered.length > 0) {
        const c = filtered[Math.max(0, Math.min(activeIndex, filtered.length - 1))]
        commit(c.name ? `${c.name} <${c.email}>` : c.email)
        e.preventDefault()
      }
    }
  }

  const onPaste: React.ClipboardEventHandler<HTMLInputElement> = (e) => {
    const text = e.clipboardData?.getData("text") || ""
    if (/[;,]+/.test(text)) {
      e.preventDefault()
      const parts = text
        .split(/[;,]+/)
        .map((s) => s.trim())
        .filter(Boolean)
      for (const p of parts) commit(p)
    }
  }

  useEffect(() => {
    const onDocClick = (ev: MouseEvent) => {
      if (!containerRef.current) return
      if (containerRef.current.contains(ev.target as Node)) return
      setOpen(false)
      // Commit draft on blur
      if (draft.trim().length > 0) commit(draft)
    }
    document.addEventListener("mousedown", onDocClick)
    return () => document.removeEventListener("mousedown", onDocClick)
  }, [draft, tokens.join(", ")])

  const lower = draft.toLowerCase()
  const filtered = (suggestions || [])
    .filter((c) => {
      if (!lower) return false
      const name = (c.name || "").toLowerCase()
      const mail = (c.email || "").toLowerCase()
      return name.includes(lower) || mail.includes(lower)
    })
    .slice(0, 6)

  return (
    <div className="flex items-start gap-2 relative w-full" ref={containerRef}>
      <label className="text-sm  w-12 mt-1.5">{label}</label>
      <div className="flex-1 min-h-[28px] flex items-center gap-1 flex-wrap border-0 focus-within:ring-0 py-1">
        {tokens.map((t, i) => (
          <span key={`${t}-${i}`} className="flex items-center gap-1 px-2 py-0.5 bg-gray-100 rounded-full text-xs text-gray-800 border border-gray-200">
            <span>{t}</span>
            <button
              type="button"
              onClick={() => removeAt(i)}
              className=" hover:text-gray-700"
              aria-label="Remove recipient"
            >
              ×
            </button>
          </span>
        ))}
        <input
          ref={inputRef}
          type="text"
          value={draft}
          onChange={(e) => {
            setDraft(e.target.value)
            setOpen(true)
            setActiveIndex(0)
          }}
          onKeyDown={onKeyDown}
          onFocus={() => setOpen(true)}
          onPaste={onPaste}
          placeholder={tokens.length === 0 ? (placeholder || "") : ""}
          className="flex-1 outline-none text-sm py-1 border-0 min-w-[8ch]"
        />
      </div>
      {open && filtered.length > 0 && (
        <div className="absolute left-12 right-0 top-full mt-1 border border-gray-200 rounded-md shadow-lg z-50">
          {filtered.map((c, idx) => (
            <div
              key={c.email}
              className={`px-3 py-2 text-sm cursor-pointer ${idx === activeIndex ? "bg-blue-50" : "hover:"}`}
              onMouseEnter={() => setActiveIndex(idx)}
              onMouseDown={(e) => {
                e.preventDefault()
                commit(c.name ? `${c.name} <${c.email}>` : c.email)
                setOpen(false)
                setActiveIndex(0)
                inputRef.current?.focus()
              }}
            >
              <div className="font-medium ">{c.name || c.email}</div>
              {c.name && <div className="text-xs ">{c.email}</div>}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
import { LoadingSpinner } from "@/components/loading-spinner"
import {
  X,
  Minimize2,
  Maximize2,
  Paperclip,
  Link,
  ImageIcon,
  Smile,
  MoreHorizontal,
  Bold,
  Italic,
  Underline,
  AlignLeft,
  AlignCenter,
  AlignRight,
  List,
  ListOrdered,
  Type,
  Palette,
  Send,
  Trash2,
} from "lucide-react"

type ComposeMode = "compose" | "reply" | "replyAll" | "forward"
type ComposeVariant = "overlay" | "inline"

interface ComposeModalProps {
  isOpen: boolean
  onClose: () => void
  onSend: (email: { to: string; cc?: string; bcc?: string; subject: string; body: string; htmlBody?: string }) => void
  mode?: ComposeMode
  variant?: ComposeVariant
  externalCloseSignal?: number
  initialTo?: string
  initialCc?: string
  initialBcc?: string
  initialSubject?: string
  initialBody?: string
  draftId?: string
  parentThreadId?: string
}

export function ComposeModal({ isOpen, onClose, onSend, mode = "compose", variant = "overlay", externalCloseSignal, initialTo, initialCc, initialBcc, initialSubject, initialBody, draftId, parentThreadId }: ComposeModalProps) {
  // Normalize editor HTML: only trim leading/trailing breaks; preserve user-inserted new lines
  const normalizeHtml = (html: string): string => {
    try {
      let s = String(html || "")
      // Trim only leading/trailing breaks and whitespace, keep internal breaks intact
      s = s.replace(/^(?:\s|&nbsp;|<br\s*\/?>)+/i, "").replace(/(?:\s|&nbsp;|<br\s*\/?>)+$/i, "")
      return s
    } catch {
      return html || ""
    }
  }

  // Normalize plain text to remove only leading/trailing blank lines; preserve internal newlines exactly
  const normalizePlain = (text: string): string => {
    try {
      let t = (text || "").replace(/\r\n/g, "\n")
      // Trim leading/trailing whitespace lines only
      t = t.replace(/^\s*\n+/g, "").replace(/\n+\s*$/g, "")
      return t
    } catch {
      return text || ""
    }
  }
  const [to, setTo] = useState("")
  const [cc, setCc] = useState("")
  const [bcc, setBcc] = useState("")
  const [subject, setSubject] = useState("")
  const [body, setBody] = useState("") // holds HTML when using rich text editor
  const [showCc, setShowCc] = useState(false)
  const [showBcc, setShowBcc] = useState(false)
  const [isMaximized, setIsMaximized] = useState(false)
  const [showFormatting, setShowFormatting] = useState(false)
  const [attachments, setAttachments] = useState<File[]>([])
  const [isSending, setIsSending] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const editorRef = useRef<HTMLDivElement>(null)
  const initialSnapshotRef = useRef<{ to: string; cc: string; bcc: string; subject: string; body: string } | null>(null)
  const [contacts, setContacts] = useState<Contact[]>([])

  // Initialize or re-initialize fields every time the modal opens or seed props change
  useEffect(() => {
    if (!isOpen) return
    const toSeed = typeof initialTo === "string" ? initialTo : ""
    const ccSeed = typeof initialCc === "string" ? initialCc : ""
    const bccSeed = typeof initialBcc === "string" ? initialBcc : ""
    const subjSeed = typeof initialSubject === "string" ? initialSubject : ""
    const bodySeed = typeof initialBody === "string" ? initialBody : ""
    setTo(toSeed)
    setCc(ccSeed)
    setBcc(bccSeed)
    setSubject(subjSeed)
    setShowCc(Boolean(ccSeed))
    setShowBcc(Boolean(bccSeed))
    // Treat initialBody as plain text; convert to basic HTML (then normalize)
    const html = normalizeHtml(
      bodySeed
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/\n/g, "<br>")
    )
    setBody(html)
    queueMicrotask(() => {
      if (editorRef.current) {
        editorRef.current.innerHTML = html
        // Clear stray leading <br> the browser may insert into empty contentEditables
        const el = editorRef.current
        while (el.firstChild && (el.firstChild.nodeName === "BR" || (el.firstChild.nodeType === 3 && !el.firstChild.textContent?.trim()))) {
          el.removeChild(el.firstChild)
        }
      }
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, initialTo, initialCc, initialBcc, initialSubject, initialBody])

  // Load contacts for typeahead
  useEffect(() => {
    if (!isOpen) return
    let cancelled = false
    ;(async () => {
      try {
        const res = await fetch("/api/contacts")
        const data = await res.json()
        const list = Array.isArray(data?.contacts) ? (data.contacts as any[]).map((c) => ({ email: String(c.email), name: typeof c.name === "string" ? c.name : undefined })) : []
        if (!cancelled) setContacts(list)
      } catch {}
    })()
    return () => {
      cancelled = true
    }
  }, [isOpen])

  // Auto-focus editor when opening
  useEffect(() => {
    if (!isOpen) return
    const focusAtEnd = () => {
      const el = editorRef.current
      if (!el) return
      el.focus()
      try {
        const range = document.createRange()
        range.selectNodeContents(el)
        range.collapse(false)
        const sel = window.getSelection()
        if (sel) {
          sel.removeAllRanges()
          sel.addRange(range)
        }
      } catch {}
    }
    // Let DOM paint then focus
    const id = window.setTimeout(focusAtEnd, 0)
    return () => window.clearTimeout(id)
  }, [isOpen])

  // Allow parent to request a close that triggers auto-save logic
  useEffect(() => {
    if (!isOpen) return
    if (typeof externalCloseSignal !== "number") return
    // Trigger the same behavior as clicking the close button (auto-save if dirty)
    void (async () => {
      await handleClose()
    })()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [externalCloseSignal])

  // Capture initial snapshot for dirty-checking
  useEffect(() => {
    if (!isOpen) return
    // Snapshot based on provided initial props; fall back to current if props undefined
    const snap = {
      to: (initialTo ?? to ?? "").trim(),
      cc: (initialCc ?? cc ?? "").trim(),
      bcc: (initialBcc ?? bcc ?? "").trim(),
      subject: (initialSubject ?? subject ?? "").trim(),
      body: (initialBody ?? body ?? "").trim(),
    }
    initialSnapshotRef.current = snap
    // We intentionally do not include state fields in deps to avoid updating snapshot on every keystroke
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, initialTo, initialCc, initialBcc, initialSubject, initialBody])

  if (!isOpen) return null

  const overlayShell = variant === "overlay"
  const containerClass = overlayShell ? "fixed inset-0 z-50 pointer-events-none" : "relative z-0"
  const panelClass = (() => {
    if (variant === "inline") {
      return "pointer-events-auto border border-gray-200 rounded-xl shadow-md w-full max-w-4xl mx-auto my-4 flex flex-col bg-white"
    }
    if (isMaximized) {
      // Large floating panel nearly full-screen with comfortable margins
      return "pointer-events-auto rounded-xl shadow-2xl border border-gray-200 flex flex-col absolute inset-0 m-6 bg-white/90 backdrop-blur-[2px]"
    }
    // Small compose anchored bottom-right, offset from scrollbar/right rail
    return "pointer-events-auto rounded-xl shadow-2xl border border-gray-200 flex flex-col w-[min(640px,calc(100%_-_2rem))] max-h-[85vh] absolute bottom-2 right-16 bg-white/90 backdrop-blur-[2px]"
  })()

  const hasUnsavedChanges = (): boolean => {
    const snap = initialSnapshotRef.current
    if (!snap) return false
    const cur = {
      to: (to || "").trim(),
      cc: (cc || "").trim(),
      bcc: (bcc || "").trim(),
      subject: (subject || "").trim(),
      body: (body || "").trim(),
    }
    return cur.to !== snap.to || cur.cc !== snap.cc || cur.bcc !== snap.bcc || cur.subject !== snap.subject || cur.body !== snap.body
  }

  const parseList = (value: string): string[] =>
    (value || "")
      // Support comma or semicolon delimiters; keep spaces inside names intact
      .split(/[;,]+/)
      .map((s) => s.trim())
      .filter(Boolean)

  // (RecipientsInput moved to module scope to avoid remounting on every parent render)

  const handleClose = async () => {
    try {
      if (hasUnsavedChanges()) {
        const plain = normalizePlain(editorRef.current?.innerText || "")
        const payload = {
          to: parseList(to),
          cc: parseList(cc),
          bcc: parseList(bcc),
          subject: (subject || "").trim(),
          text: plain,
          html: normalizeHtml(body || ""),
        }
        if (draftId) {
          await fetch(`/api/drafts/${draftId}`, {
            method: "PUT",
            headers: { "content-type": "application/json" },
            body: JSON.stringify(payload),
          }).catch(() => {})
        } else {
          await fetch("/api/drafts", {
            method: "POST",
            headers: { "content-type": "application/json" },
            body: JSON.stringify({ ...payload, parentThreadId }),
          }).catch(() => {})
        }
      }
    } finally {
      onClose()
    }
  }

  const handleSend = async () => {
    const toList = parseList(to)
    const ccList = parseList(cc)
    const bccList = parseList(bcc)
    const totalRecipients = toList.length + ccList.length + bccList.length
    if (totalRecipients === 0 || !subject.trim()) {
      alert("Please include a subject and at least one recipient")
      return
    }

    setIsSending(true)

    // Simulate sending delay
    await new Promise((resolve) => setTimeout(resolve, 1500))

    const plain = normalizePlain(editorRef.current?.innerText || "")
    onSend({
      to: to.trim(),
      cc: cc.trim() || undefined,
      bcc: bcc.trim() || undefined,
      subject: subject.trim(),
      body: plain,
      htmlBody: normalizeHtml(body || ""),
    })

    // Reset form
    setTo("")
    setCc("")
    setBcc("")
    setSubject("")
    setBody("")
    setAttachments([])
    setIsSending(false)
    onClose()
  }

  const handleAttachment = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || [])
    setAttachments((prev) => [...prev, ...files])
  }

  const removeAttachment = (index: number) => {
    setAttachments((prev) => prev.filter((_, i) => i !== index))
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes"
    const k = 1024
    const sizes = ["Bytes", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
  }

  const exec = (command: string, value?: string) => {
    if (!editorRef.current) return
    editorRef.current.focus()
    try {
      // eslint-disable-next-line deprecation/deprecation
      document.execCommand(command, false, value)
      setBody(editorRef.current.innerHTML)
    } catch {}
  }

  return (
    // <div className={containerClass}>
      <div className={`${panelClass}`}>
        {/* Header */}
        <div className="flex items-center justify-between p-3 border-b  rounded-t-xl">
          <h3 className="font-medium ">New Message</h3>
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsMaximized(!isMaximized)}
              className="hover:bg-gray-200 transition-colors"
            >
              {isMaximized ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
            </Button>
            {(mode === "compose") && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleClose}
                className="hover:bg-gray-200 transition-colors"
              >
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>

        {/* Recipients */}
            <div className="p-4 space-y-3 border-b">
              <div className="flex items-start gap-2">
                <div className="flex-1 flex items-center gap-2 relative">
                  <RecipientsChipsInput
                    label="To"
                    value={to}
                    onChange={setTo}
                    placeholder="Recipients (type to search)"
                    suggestions={contacts}
                  />
                  <div className="shrink-0 flex gap-1 mt-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      className=" text-sm hover:bg-blue-50 transition-colors"
                      onClick={() => setShowCc(!showCc)}
                    >
                      Cc
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className=" text-sm hover:bg-blue-50 transition-colors"
                      onClick={() => setShowBcc(!showBcc)}
                    >
                      Bcc
                    </Button>
                  </div>
                </div>
              </div>
              

              <div className={`transition-all duration-300 overflow-visible ${showCc ? "max-h-28 opacity-100" : "max-h-0 opacity-0"}`}>
                {showCc && (
                  <RecipientsChipsInput
                    label="Cc"
                    value={cc}
                    onChange={setCc}
                    placeholder="Carbon copy"
                    suggestions={contacts}
                  />
                )}
              </div>

              <div className={`transition-all duration-300 overflow-visible ${showBcc ? "max-h-28 opacity-100" : "max-h-0 opacity-0"}`}>
                {showBcc && (
                  <RecipientsChipsInput
                    label="Bcc"
                    value={bcc}
                    onChange={setBcc}
                    placeholder="Blind carbon copy"
                    suggestions={contacts}
                  />
                )}
              </div>

              <div className="flex items-center gap-2">
                <label className="text-sm  w-12">Subject</label>
                <Input
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  placeholder="Subject"
                  className="flex-1 border-0 focus:ring-0 px-0 focus:ring-2 focus:ring-blue-500 transition-all"
                />
              </div>
            </div>

            {/* Formatting Toolbar */}
            {showFormatting && (
              <div className="px-4 py-2 border-b ">
                <div className="flex items-center gap-1">
                  <Button variant="ghost" size="sm" onClick={() => exec("bold")}>
                    <Bold className="h-4 w-4" />
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => exec("italic")}>
                    <Italic className="h-4 w-4" />
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => exec("underline")}>
                    <Underline className="h-4 w-4" />
                  </Button>
                  <div className="w-px h-4 bg-gray-300 mx-1"></div>
                  <Button variant="ghost" size="sm" onClick={() => exec("justifyLeft")}>
                    <AlignLeft className="h-4 w-4" />
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => exec("justifyCenter")}>
                    <AlignCenter className="h-4 w-4" />
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => exec("justifyRight")}>
                    <AlignRight className="h-4 w-4" />
                  </Button>
                  <div className="w-px h-4 bg-gray-300 mx-1"></div>
                  <Button variant="ghost" size="sm" onClick={() => exec("insertUnorderedList")}>
                    <List className="h-4 w-4" />
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => exec("insertOrderedList")}>
                    <ListOrdered className="h-4 w-4" />
                  </Button>
                  <div className="w-px h-4 bg-gray-300 mx-1"></div>
                  <Button variant="ghost" size="sm" onClick={() => exec("removeFormat")}>
                    <Type className="h-4 w-4" />
                  </Button>
                  <label className="inline-flex items-center gap-1 cursor-pointer px-2 py-1 rounded hover:bg-gray-200">
                    <Palette className="h-4 w-4" />
                    <input
                      type="color"
                      className="w-6 h-6 p-0 border-0 bg-transparent cursor-pointer"
                      onChange={(e) => exec("foreColor", e.target.value)}
                    />
                  </label>
                </div>
              </div>
            )}

            {/* Message Body */}
            <div className="flex-1 p-4 overflow-y-auto">
              <div
                ref={editorRef}
                contentEditable
                className={`w-full border-0 focus:outline-none focus:ring-0 min-h-[16rem] text-sm leading-relaxed ${
                  variant === "inline" ? "h-48" : isMaximized ? "h-[calc(100vh-12rem)]" : "h-64"
                }`}
                onInput={() => setBody(editorRef.current?.innerHTML || "")}
                onFocus={() => {
                  // Remove an initial stray <br> so the caret starts at the very top with no blank line
                  const el = editorRef.current
                  if (!el) return
                  const html = (el.innerHTML || "").trim()
                  if (html === "<br>" || html === "<div><br></div>") {
                    el.innerHTML = ""
                  }
                }}
                data-placeholder="Compose email..."
                style={{ whiteSpace: "pre-wrap" }}
                suppressContentEditableWarning
              />

              {/* Attachments */}
              {attachments.length > 0 && (
                <div className="mt-4 space-y-2">
                  <div className="text-sm  font-medium">Attachments:</div>
                  {attachments.map((file, index) => (
                    <div key={index} className="flex items-center gap-2 p-2  rounded">
                      <Paperclip className="h-4 w-4 " />
                      <span className="text-sm flex-1">{file.name}</span>
                      <span className="text-xs ">{formatFileSize(file.size)}</span>
                      <Button variant="ghost" size="sm" onClick={() => removeAttachment(index)}>
                        <X className="h-3 w-3" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between p-4 border-t  rounded-b-xl">
              <div className="flex items-center gap-2">
                <Button
                  onClick={handleSend}
                  disabled={isSending}
                  className="bg-blue-600 hover:bg-blue-700 text-white transition-all duration-200 disabled:opacity-50"
                >
                  {isSending ? (
                    <>
                      <LoadingSpinner size="sm" />
                      <span className="ml-2">Sending...</span>
                    </>
                  ) : (
                    <>
                      <Send className="h-4 w-4 mr-2" />
                      Send
                    </>
                  )}
                </Button>
                <Button variant="ghost" size="sm" onClick={() => setShowFormatting(!showFormatting)}>
                  <Type className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="sm" onClick={() => fileInputRef.current?.click()}>
                  <Paperclip className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="sm">
                  <Link className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="sm">
                  <Smile className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="sm">
                  <ImageIcon className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="sm">
                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  className="hover:bg-red-100 hover:text-red-600"
                  onClick={async () => {
                    // If editing an existing draft, delete it; otherwise, just close without saving
                    if (draftId) {
                      try {
                        await fetch(`/api/drafts/${draftId}`, { method: "DELETE" })
                      } catch {}
                    }
                    onClose()
                  }}
                  title={draftId ? "Discard draft" : "Discard"}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
        

        {/* Hidden file input */}
        <input ref={fileInputRef} type="file" multiple className="hidden" onChange={handleAttachment} accept="*/*" />
      </div>
    // </div>
  )
}
