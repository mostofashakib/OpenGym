"use client"

import type React from "react"
import { useEffect, useMemo, useState, useRef } from "react"
import { htmlToPlainText, decodeForDisplay } from "@/lib/utils"

import { Input } from "@/components/ui/input"
import { useRandomization } from "@/lib/randomization-context"
import { Search, Folder as FolderIcon, Tag as TagIcon, User as UserIcon } from "lucide-react"

interface SearchFiltersProps {
  searchQuery: string
  onSearchChange: (query: string) => void
  activeFilters: SearchFilter[]
  onFilterAdd: (filter: SearchFilter) => void
  onFilterRemove: (filterId: string) => void
  onClearAll: () => void
  onSubmit?: (finalQuery?: string) => void
  externalCloseSignal?: number
}

export interface SearchFilter {
  id: string
  type: "sender" | "subject" | "has" | "label" | "date" | "starred" | "unread"
  value: string
  label: string
}

type Suggestion =
  | { kind: "folder"; id: string; name: string }
  | { kind: "label"; id: string; name: string }
  | { kind: "sender"; email: string; name: string }
  | { kind: "operator"; key: string; value: string; display: string }

const SYSTEM_FOLDERS: Array<{ id: string; name: string }> = [
  { id: "inbox", name: "Inbox" },
  { id: "sent", name: "Sent" },
  { id: "drafts", name: "Drafts" },
  { id: "trash", name: "Trash" },
  { id: "spam", name: "Spam" },
  { id: "all", name: "All Mail" },
  { id: "important", name: "Important" },
  { id: "anywhere", name: "Anywhere" },
]

export function SearchFilters({
  searchQuery,
  onSearchChange,
  onSubmit,
  externalCloseSignal,
}: SearchFiltersProps) {
  const randomization = useRandomization()
  const si = randomization?.searchInput || {}
  // Defaults mirror generated/randomization.json so SSR and client match even before context updates
  const placeholderText: string = typeof si.placeholder === "string" && si.placeholder.trim().length > 0 ? si.placeholder : "Type to search"
  const widthClass: string = typeof si.widthClass === "string" ? si.widthClass : "max-w-md"
  const marginClass: string = typeof si.marginClass === "string" ? si.marginClass : "mr-auto"
  const padL: string = typeof si.paddingLeftClass === "string" ? si.paddingLeftClass : "pl-12"
  const padR: string = typeof si.paddingRightClass === "string" ? si.paddingRightClass : "pr-14"
  // Force left-aligned input text regardless of randomization
  const textAlignClass: string = "text-left"
  const initialMode: "expanded" | "icon" = (si?.mode === "icon" ? "icon" : "expanded")
  const [revealed, setRevealed] = useState<boolean>(initialMode === "expanded")
  const [labels, setLabels] = useState<Array<{ id: string; name: string }>>([])
  const [open, setOpen] = useState(false)
  const [mode, setMode] = useState<
    | null
    | "in"
    | "from"
    | "to"
    | "cc"
    | "bcc"
    | "subject"
    | "is"
    | "has"
    | "before"
    | "after"
    | "newer_than"
    | "older_than"
  >(null)
  const [prefix, setPrefix] = useState("")
  const [items, setItems] = useState<Suggestion[]>([])
  const [highlight, setHighlight] = useState(-1)
  const [quickItems, setQuickItems] = useState<Array<{ id: string; threadId?: string; subject: string; sender: string; timestamp: string; snippet: string }>>([])
  const inputRef = useRef<HTMLInputElement | null>(null)
  const previewRef = useRef<{ original: string } | null>(null)

  // Extract plain-text query portion by stripping operator tokens
  const extractBaseQuery = (text: string): string => {
    const token = "(?:in|from|to|cc|bcc|subject|label|has|is|before|after|newer_than|older_than|filename|size|larger|smaller|list)"
    // Remove key:"quoted" or key:value tokens anywhere
    let base = text.replace(new RegExp(`\\b${token}:(?:\"[^\"]+\"|[^\\s]+)`, "gi"), "")
    // Remove trailing incomplete token (e.g., "in:", "from:al")
    base = base.replace(new RegExp(`(?:^|\\s)${token}:([^\\s]*)$`, "gi"), "")
    return base.replace(/\s+/g, " ").trim()
  }

  // Load labels for in: typeahead
  useEffect(() => {
    let ignore = false
    const load = async () => {
      try {
        const res = await fetch("/api/labels")
        const data = await res.json()
        const raw = Array.isArray(data?.labels) ? data.labels : []
        const mapped = raw
          .filter((l: any) => l && typeof l.id === "string" && typeof l.name === "string")
          .map((l: any) => ({ id: String(l.id), name: String(l.name) }))
        if (!ignore) setLabels(mapped)
      } catch {}
    }
    load()
    return () => {
      ignore = true
    }
  }, [])

  // Detect active operator token at the end of the input
  const activeToken = useMemo(() => {
    const trimmedRight = (searchQuery ?? "").replace(/\s+$/, "")
    const m = trimmedRight.match(/(?:^|\s)(in|from|to|cc|bcc|subject|is|has|before|after|newer_than|older_than):([^\s]*)$/i)
    if (!m) return null
    return { type: m[1].toLowerCase() as NonNullable<typeof mode>, raw: m[0], value: m[2] ?? "" }
  }, [searchQuery])

  // Update mode/prefix based on token
  useEffect(() => {
    if (!activeToken) {
      setMode(null)
      setPrefix("")
      // Keep the dropdown open for plain-text results; just clear filter suggestions
      setItems([])
      setHighlight(-1)
      return
    }
    setMode(activeToken.type)
    setPrefix(activeToken.value || "")
    setOpen(true)
    setHighlight(-1)
  }, [activeToken])

  // Close dropdown when instructed externally (e.g., after Enter submits search)
  useEffect(() => {
    if (typeof externalCloseSignal === "number") {
      setOpen(false)
      try { inputRef.current?.blur() } catch {}
    }
  }, [externalCloseSignal])

  // Build suggestions for in:
  useEffect(() => {
    if (mode !== "in") return
    const q = prefix.toLowerCase()
    const folders = SYSTEM_FOLDERS.filter(
      (f) => f.id.includes(q) || f.name.toLowerCase().includes(q),
    ).map<Suggestion>((f) => ({ kind: "folder", id: f.id, name: f.name }))
    const SYSTEM_LABEL_IDS = new Set(SYSTEM_FOLDERS.map((f) => f.id.toUpperCase()))
    const labelItems = labels
      // Exclude system labels that correspond to folders to avoid duplicates (e.g., INBOX vs Inbox)
      .filter((l) => !SYSTEM_LABEL_IDS.has(String(l.id || "").toUpperCase()))
      .filter((l) => l.id.toLowerCase().includes(q) || l.name.toLowerCase().includes(q))
      .map<Suggestion>((l) => ({ kind: "label", id: l.id, name: l.name }))
    setItems([...folders, ...labelItems].slice(0, 2))
  }, [mode, prefix, labels])

  // Build suggestions for is:
  useEffect(() => {
    if (mode !== "is") return
    const opts = ["unread", "starred", "important", "snoozed"]
    const q = prefix.toLowerCase()
    const items: Suggestion[] = opts
      .filter((o) => o.includes(q))
      .map((o) => ({ kind: "operator", key: "is", value: o, display: o }))
    const complete = opts.includes(prefix.toLowerCase())
    setItems(complete ? [] : items.slice(0, 2))
  }, [mode, prefix])

  // Build suggestions for has:
  useEffect(() => {
    if (mode !== "has") return
    const opts = ["attachment", "drive", "document", "spreadsheet", "presentation"]
    const q = prefix.toLowerCase()
    const items: Suggestion[] = opts
      .filter((o) => o.includes(q))
      .map((o) => ({ kind: "operator", key: "has", value: o, display: o }))
    const complete = opts.includes(prefix.toLowerCase())
    setItems(complete ? [] : items.slice(0, 2))
  }, [mode, prefix])

  // Build suggestions for before/after (absolute date quick-picks)
  useEffect(() => {
    if (mode !== "before" && mode !== "after") return
    const fmt = (d: Date) => {
      const y = d.getFullYear()
      const m = String(d.getMonth() + 1).padStart(2, "0")
      const day = String(d.getDate()).padStart(2, "0")
      return `${y}-${m}-${day}`
    }
    const now = new Date()
    const yesterday = new Date(now)
    yesterday.setDate(now.getDate() - 1)
    const last7 = new Date(now)
    last7.setDate(now.getDate() - 7)
    const candidates = [fmt(now), fmt(yesterday), fmt(last7)]
    const q = prefix.toLowerCase()
    const items: Suggestion[] = candidates
      .filter((s) => s.includes(q))
      .map((s) => ({ kind: "operator", key: mode, value: s, display: s }))
    const complete = /^\d{4}-\d{2}-\d{2}$/.test(prefix)
    setItems(complete ? [] : items.slice(0, 2))
  }, [mode, prefix])

  // Build suggestions for newer_than/older_than (relative windows)
  useEffect(() => {
    if (mode !== "newer_than" && mode !== "older_than") return
    const opts = ["7d", "30d", "3m", "6m", "1y"]
    const q = prefix.toLowerCase()
    const items: Suggestion[] = opts
      .filter((o) => o.includes(q))
      .map((o) => ({ kind: "operator", key: mode, value: o, display: o }))
    const complete = /^\d+\s*[dmy]$/.test(prefix.toLowerCase())
    setItems(complete ? [] : items.slice(0, 2))
  }, [mode, prefix])

  // Quick results while typing: top 5 matches across all mail (uses base text only)
  useEffect(() => {
    // Build quick results regardless of active operator; they render after filter suggestions
    const base = extractBaseQuery((searchQuery || "").trim())
    if (base.length === 0) {
      setQuickItems([])
      return
    }
    const controller = new AbortController()
    const t = setTimeout(async () => {
      try {
        const res = await fetch(`/api/search?q=${encodeURIComponent(base)}&folder=all`, { signal: controller.signal })
        const data = await res.json()
        const arr = Array.isArray(data?.messages) ? data.messages.slice(0, 5) : []
        const items = arr.map((m: any) => {
          const from = String(m?.from || "")
          const match = from.match(/^([^<]+)</)
          const sender = (match ? match[1] : from).trim()
          const rawText = typeof m?.text === "string" && m.text.trim().length > 0 ? m.text : undefined
          const plainFromHtml = typeof m?.html === "string" && m.html.trim().length > 0 ? htmlToPlainText(m.html) : ""
          const combined = decodeForDisplay((rawText || plainFromHtml || "").replace(/\s+/g, " ")).trim()
          const snippet = combined.slice(0, 120)
          return {
            id: String(m.id),
            threadId: typeof m.threadId === "string" ? m.threadId : undefined,
            subject: String(m?.subject || "(no subject)"),
            sender,
            timestamp: String(m?.date || ""),
            snippet,
          }
        })
        setQuickItems(items)
      } catch {
        // ignore
      }
    }, 150)
    return () => {
      controller.abort()
      clearTimeout(t)
    }
  }, [searchQuery, mode])

  // Build suggestions for from: (debounced fetch)
  useEffect(() => {
    if (mode !== "from") return
    const controller = new AbortController()
    const t = setTimeout(async () => {
      try {
        const res = await fetch(`/api/senders?q=${encodeURIComponent(prefix)}`, { signal: controller.signal })
        const data = await res.json()
        const arr = Array.isArray(data?.senders) ? data.senders : []
        const suggestions: Suggestion[] = arr.map((s: any) => ({
          kind: "sender",
          email: String(s?.email || ""),
          name: String(s?.name || s?.email || ""),
        }))
        setItems(suggestions.slice(0, 2))
      } catch {}
    }, 150)
    return () => {
      controller.abort()
      clearTimeout(t)
    }
  }, [mode, prefix])

  const buildReplacedQuery = (token: string, trailingSpace: boolean): string => {
    if (!mode) return searchQuery || ""
    const trimmedRight = (searchQuery || "").replace(/\s+$/, "")
    const re = new RegExp(`(?:^|\\s)${mode}:([^\\s]*)$`, "i")
    const m = re.exec(trimmedRight)
    if (!m || typeof m.index !== "number") return searchQuery || ""
    const hasLeadingSpace = m[0].startsWith(" ")
    const start = m.index + (hasLeadingSpace ? 1 : 0)
    const before = trimmedRight.slice(0, start)
    const next = `${before}${mode}:${token}${trailingSpace ? " " : ""}`
    return next
  }

  const getTokenValFromSuggestion = (s: Suggestion): string => {
    return mode === "in"
      ? (s.kind === "folder" || s.kind === "label" ? (s as any).id : "")
      : mode === "from"
      ? (s.kind === "sender" ? (s.email || s.name || "").trim() : "")
      : s.kind === "operator"
      ? s.value
      : ""
  }

  const applySuggestion = (s: Suggestion) => {
    if (!mode) return
    const tokenVal = getTokenValFromSuggestion(s)
    if (!tokenVal) return
    const next = buildReplacedQuery(tokenVal, true)
    onSearchChange(next)
    setOpen(false)
    previewRef.current = null
    setHighlight(-1)
  }

  const onKeyDown: React.KeyboardEventHandler<HTMLInputElement> = (e) => {
    const total = (items?.length || 0) + (quickItems?.length || 0)
    const filtersCount = items.length
    if (e.key === "ArrowDown" && open && total > 0) {
      e.preventDefault()
      const nextIndex = Math.min((highlight ?? -1) + 1, total - 1)
      setHighlight(nextIndex)
    } else if (e.key === "ArrowUp" && open && total > 0) {
      e.preventDefault()
      const nextIndex = Math.max((highlight ?? -1) - 1, -1)
      setHighlight(nextIndex)
    } else if ((e.key === "Tab" || e.key === "ArrowRight" || e.key === " ") && open && highlight >= 0) {
      // Commit filter suggestion only if the highlight is within the filters section
      if (highlight < filtersCount) {
        e.preventDefault()
        const tokenVal = getTokenValFromSuggestion(items[highlight])
        if (tokenVal) {
          const trailingSpace = e.key === " "
          onSearchChange(buildReplacedQuery(tokenVal, trailingSpace))
          setHighlight(-1)
        }
      }
    } else if (e.key === "Enter") {
      if (highlight >= 0) {
        // If a filter suggestion is highlighted, commit it then submit
        if (highlight < filtersCount) {
          e.preventDefault()
          const tokenVal = getTokenValFromSuggestion(items[highlight])
          if (tokenVal) {
            const nextQuery = buildReplacedQuery(tokenVal, false)
            onSearchChange(nextQuery)
            setOpen(false)
            setHighlight(-1)
            previewRef.current = null
            onSubmit?.(nextQuery)
          }
          return
        }
        // If a quick result is selected, open it
        if (highlight >= filtersCount) {
          e.preventDefault()
          const q = quickItems[highlight - filtersCount]
          if (q) {
            const tid = q.threadId || q.id
            if (tid && typeof window !== "undefined") {
              const sp = new URLSearchParams(window.location.search)
              const from = sp.get("folder") || "inbox"
              window.location.assign(`/thread/${tid}?from=${encodeURIComponent(from)}`)
            }
          }
          return
        }
      }
      // Otherwise submit the search as-is
      e.preventDefault()
      setOpen(false)
      try { inputRef.current?.blur() } catch {}
      onSubmit?.()
    } else if (e.key === "Escape") {
      setOpen(false)
    }
  }

  return (
    <div className={`flex-1 ${widthClass} ${marginClass} mx-8`}>
      {revealed ? (
        <form onSubmit={(e) => e.preventDefault()} className="relative">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              ref={inputRef as any}
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder={placeholderText}
              className={`${padL} ${padR} ${textAlignClass} bg-gray-100 border-0 rounded-full`}
              onBlur={() => setTimeout(() => {
                setOpen(false)
                if (initialMode === "icon") setRevealed(false)
              }, 100)}
              onFocus={() => {
                setOpen(true)
              }}
            />
          </div>

          {(open && (items.length > 0 || quickItems.length > 0)) && (
            <div className="absolute left-0 right-0 mt-2 z-50 border border-gray-200 rounded-md shadow-md overflow-hidden">
              <div className="max-h-72 overflow-auto py-1">
              {items.length > 0 && (
                <div className="py-1">
                  <div className="px-3 py-1 text-[11px] uppercase tracking-wide ">Filters</div>
                  {items.map((s, i) => {
                    const isActive = i === highlight
                    return (
                      <button
                        key={
                          s.kind === "sender"
                            ? `sender:${s.email}:${i}`
                            : s.kind === "operator"
                            ? `op:${(s as any).key}:${(s as any).value}:${i}`
                            : `${s.kind}:${(s as any).id}:${i}`
                        }
                        type="button"
                        className={`w-full px-3 py-2 flex items-center gap-2 text-left ${isActive ? "bg-gray-100" : ""}`}
                        onMouseDown={(e) => {
                          e.preventDefault()
                          applySuggestion(s)
                        }}
                      >
                        {s.kind === "folder" ? (
                          <>
                            <FolderIcon className="h-4 w-4 " />
                            <span className="text-sm ">{s.name}</span>
                            <span className="ml-auto text-xs ">in:{s.id}</span>
                          </>
                        ) : s.kind === "label" ? (
                          <>
                            <TagIcon className="h-4 w-4 " />
                            <span className="text-sm ">{s.name}</span>
                            <span className="ml-auto text-xs ">in:{s.id}</span>
                          </>
                        ) : s.kind === "sender" ? (
                          <>
                            <UserIcon className="h-4 w-4 " />
                            <span className="text-sm ">{s.name}</span>
                            {s.email && <span className="ml-auto text-xs ">{s.email}</span>}
                            {!s.email && <span className="ml-auto text-xs ">from:{s.name}</span>}
                          </>
                        ) : (
                          <>
                            <span className="text-sm ">{(s as any).display}</span>
                            <span className="ml-auto text-xs ">{(s as any).key}:{(s as any).value}</span>
                          </>
                        )}
                      </button>
                    )
                  })}
                </div>
              )}
              {quickItems.length > 0 && (
                <div className="py-1">
                  {items.length > 0 && <div className="my-1 border-t border-gray-100" />}
                  <div className="px-3 py-1 text-[11px] uppercase tracking-wide ">Results</div>
                  {quickItems.map((q, i) => {
                    const isActive = (items.length + i) === highlight
                    return (
                    <button
                      key={`quick:${q.id}`}
                      type="button"
                      className={`w-full px-3 py-2 flex flex-col text-left ${isActive ? "bg-gray-100" : "hover:bg-gray-100"}`}
                      onMouseDown={(e) => {
                        e.preventDefault()
                        const tid = q.threadId || q.id
                        if (tid && typeof window !== "undefined") {
                          const sp = new URLSearchParams(window.location.search)
                          const from = sp.get("folder") || "inbox"
                          window.location.assign(`/thread/${tid}?from=${encodeURIComponent(from)}`)
                        }
                      }}
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-sm  truncate flex-1">{q.subject}</span>
                        <span className="text-xs  truncate">{q.sender}</span>
                      </div>
                      {q.snippet && (
                        <span className="text-xs  truncate mt-0.5">{q.snippet}</span>
                      )}
                    </button>
                  )})}
                </div>
              )}
              </div>
            </div>
          )}
        </form>
      ) : (
        <div className={`relative`}> 
          <button
            type="button"
            aria-label="Open search"
            className="p-2 rounded-full hover:bg-gray-100 "
            onClick={() => {
              setRevealed(true)
              setTimeout(() => { try { (inputRef as any)?.current?.focus?.() } catch {} }, 0)
            }}
          >
            <Search className="h-5 w-5" />
          </button>
        </div>
      )}
    </div>
  )
}
