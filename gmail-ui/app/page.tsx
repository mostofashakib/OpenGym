"use client"

import { useEffect, useMemo, useRef, useState } from "react"
import { Button } from "@/components/ui/button"
import { useRandomization } from "@/lib/randomization-context"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { EmailList } from "@/components/email-list"
import { decodeForDisplay, htmlToPlainText } from "@/lib/utils"
import { ComposeModal } from "@/components/compose-modal"
import { SidebarNavigation } from "@/components/sidebar-navigation"
import { EmailThreadView } from "@/components/email-thread-view"
import ThreadModal from "@/components/thread-modal"
import { SearchFilters, type SearchFilter } from "@/components/search-filters"
import { LoadingSpinner } from "@/components/loading-spinner"
import { nowDate, nowTs as getNowTs, snoozeLaterTodayISO, snoozeNextWeekISO, snoozeThisWeekendISO, snoozeTomorrowISO, buildFixedZonedISOFromInputs } from "@/lib/clock"
import { useSearchParams } from "next/navigation"
import {
  Settings,
  HelpCircle,
  Grid3X3,
  Menu,
  ChevronDown,
  ChevronRight,
  ChevronLeft,
  Calendar,
  FileText,
  StickyNote,
  ListTodo,
  RefreshCw,
  Archive,
  Trash2,
  Trash,
  MoreHorizontal,
  Star,
  StarOff,
  Box,
  CheckSquare,
  Square,
  AlertCircle,
  MailOpen,
  Mail,
  Clock,
  Folder as FolderIcon,
  Tag as TagIcon,
} from "lucide-react"
import { Badge } from "@/components/ui/badge"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu"

interface Email {
  id: string
  sender: string
  subject: string
  preview: string
  time: string
  dateISO: string
  isRead: boolean
  isStarred: boolean
  isImportant: boolean
  hasAttachment?: boolean
  labels?: string[]
  threadId?: string
  messageCount?: number
  participants?: string[]
  snoozeUntil?: string | null
  hasDraft?: boolean
}

interface ThreadEmail {
  id: string
  sender: string
  senderEmail: string
  recipient: string
  to?: string[]
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

// All data below is now loaded from the API endpoints under /api/*

function LogoIcon({ variant }: { variant: string }) {
  if (variant === "paperplane") {
    return (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M3 12L21 3L14 21L11 13L3 12Z" fill="#1A73E8"/>
        <path d="M21 3L11 13" stroke="#0C47A1" strokeWidth="2"/>
      </svg>
    )
  }
  if (variant === "spark") {
    return (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 2L14 8L20 10L14 12L12 18L10 12L4 10L10 8L12 2Z" fill="#FBBC04"/>
      </svg>
    )
  }
  if (variant === "quill") {
    return (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M19 3C14 3 8 9 8 14C8 16 8.5 18 10 19.5C11.5 21 13.5 21.5 15.5 21C20 20 21 5 19 3Z" fill="#34A853"/>
        <path d="M8 14C10 14 14 12 16 10" stroke="#166534" strokeWidth="2"/>
      </svg>
    )
  }
  if (variant === "orb") {
    return (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="12" cy="12" r="9" fill="#EA4335"/>
        <path d="M3 12C7 10 17 10 21 12" stroke="#F9FAFB" strokeWidth="2"/>
        <path d="M12 3C14 7 14 17 12 21" stroke="#F9FAFB" strokeWidth="2"/>
      </svg>
    )
  }
  // default envelope
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="2" y="5" width="20" height="14" rx="2" fill="#1A73E8"/>
      <path d="M3 7L12 12L21 7" stroke="#E5F0FF" strokeWidth="2"/>
    </svg>
  )
}

const parseSenderName = (from: string) => {
  const match = from.match(/^([^<]+)</)
  return match ? match[1].trim() : from
}

const formatDateTime = (iso: string) => {
  try {
    const date = new Date(iso)
    return date.toLocaleString([], {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    })
  } catch {
    return ""
  }
}

// Parser for Gmail-like operators: in:, from:, to:, cc:, bcc:, subject:, label:, has:, is:, before:, after:, newer_than:, older_than:, filename:, size:, larger:, smaller:, list:
const parseSearch = (
  input: string,
): {
  base: string
  ops: Partial<{
    in: string
    from: string
    to: string
    cc: string
    bcc: string
    subject: string
    label: string
    has: string[]
    is: string[]
    before: string
    after: string
    newer_than: string
    older_than: string
    filename: string
    size: string
    larger: string
    smaller: string
    list: string
  }>
} => {
  const text = (input || "").trim()
  const ops: any = { has: [] as string[], is: [] as string[] }
  // Capture key:value tokens, supporting quoted values
  const tokenRe = /(\b(?:in|from|to|cc|bcc|subject|label|has|is|before|after|newer_than|older_than|filename|size|larger|smaller|list)):("[^"]+"|[^\s]+)/gi
  let base = text
  let m: RegExpExecArray | null
  while ((m = tokenRe.exec(text)) !== null) {
    const key = m[1].toLowerCase()
    let value = m[2]
    if (value.startsWith('"') && value.endsWith('"')) value = value.slice(1, -1)
    if (key === "has" || key === "is") {
      if (!Array.isArray(ops[key])) ops[key] = []
      if (value) ops[key].push(value)
    } else {
      ops[key] = value
    }
  }
  base = base.replace(tokenRe, "").replace(/\s+/g, " ").trim()
  return { base, ops }
}

export default function GmailClone() {
  const randomization = useRandomization()
  // Use stable defaults for SSR to avoid hydration mismatches, then sync from randomization on mount/update
  const [navPosition, setNavPosition] = useState<"top" | "side">("side")
  const [threadOpenMode, setThreadOpenMode] = useState<"page" | "modal">("page")
  const [paginationPosition, setPaginationPosition] = useState<"top" | "bottom">("top")
  const [appLogo, setAppLogo] = useState<string>("")
  const [appName, setAppName] = useState<string>("Gmail")
  const [selectedEmails, setSelectedEmails] = useState<string[]>([])
  const [emails, setEmails] = useState<Email[]>([])
  const [showCompose, setShowCompose] = useState(false)
  const [composeDraftId, setComposeDraftId] = useState<string | null>(null)
  const [composeParentThreadId, setComposeParentThreadId] = useState<string | null>(null)
  const [composeInitials, setComposeInitials] = useState<{ to?: string; cc?: string; bcc?: string; subject?: string; body?: string }>({})
  const searchParams = useSearchParams()
  const [sidebarpsed, setSidebarpsed] = useState<boolean>(() => randomization?.sidebar?.collapsed ?? false)
  // Mode: true => collapsed by default; false => expanded by default
  const [sidebarDefaultCollapsed, setSidebarDefaultCollapsed] = useState<boolean>(() => randomization?.sidebar?.collapsed ?? false)
  const [sidebarHoverLockUntil, setSidebarHoverLockUntil] = useState<number>(0)
  const [currentFolder, setCurrentFolder] = useState<string>(() => {
    try {
      const f = searchParams.get("folder")
      if (f && typeof f === "string") return f
    } catch {}
    return "inbox"
  })
  const [currentThread, setCurrentThread] = useState<EmailThread | null>(null)
  const [showThreadModal, setShowThreadModal] = useState(false)
  const [modalThread, setModalThread] = useState<EmailThread | null>(null)
  const [threadComposeMode, setThreadComposeMode] = useState<"compose" | "reply" | "replyAll" | "forward">("compose")
  const [threadComposeInitials, setThreadComposeInitials] = useState<{ to?: string; cc?: string; bcc?: string; subject?: string; body?: string }>({})
  const [threadComposeCloseSignal, setThreadComposeCloseSignal] = useState(0)
  // Sync layout switches from randomization after mount
  useEffect(() => {
    try {
      setNavPosition((randomization?.layout?.headerPosition === "top" ? "top" : "side"))
      setThreadOpenMode((randomization?.threadOpenMode === "modal" ? "modal" : "page"))
      setPaginationPosition((randomization?.selectionToolbar?.paginationPosition === "bottom" ? "bottom" : "top"))
      setSidebarDefaultCollapsed(randomization?.sidebar?.collapsed ?? false)
      setAppLogo((randomization?.appLogo || ""))
      setAppName((randomization?.appName || "Gmail"))
      setSidebarpsed(randomization?.sidebar?.collapsed ?? false)
    } catch {}
  }, [randomization])
  // Close thread modal with Escape key
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && showThreadModal) {
        e.preventDefault()
        setShowThreadModal(false)
      }
    }
    window.addEventListener("keydown", onKeyDown)
    return () => window.removeEventListener("keydown", onKeyDown)
  }, [showThreadModal])
  const [searchQuery, setSearchQuery] = useState("")
  const [activeFilters, setActiveFilters] = useState<SearchFilter[]>([])
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [isChangingFolder, setIsChangingFolder] = useState(false)
  const [unreadpsed, setUnreadpsed] = useState(false)
  const [folderUnreadCounts, setFolderUnreadCounts] = useState<Record<string, number>>({})
  const [labelUnreadCounts, setLabelUnreadCounts] = useState<Record<string, number>>({})
  const [userLabels, setUserLabels] = useState<Array<{ id: string; name: string; color?: string }>>([])
  const [labelsById, setLabelsById] = useState<Record<string, { id: string; name: string; type: "SYSTEM" | "USER"; color?: string }>>({})
  const [userSettings, setUserSettings] = useState<{ displayName: string; email?: string } | null>(null)
  const [pageSize, setPageSize] = useState<number>(() => {
    if (typeof window !== "undefined") {
      try {
        const sp = new URLSearchParams(window.location.search)
        const psStr = sp.get("ps")
        const parsedFromUrl = psStr ? parseInt(psStr, 10) : NaN
        const allowed = [2, 10, 20, 50]
        if (allowed.includes(parsedFromUrl)) return parsedFromUrl
        const saved = window.localStorage.getItem("gmailPageSize")
        const parsed = saved ? parseInt(saved, 10) : NaN
        if (allowed.includes(parsed)) return parsed
      } catch {}
    }
    return 10
  })
  const [pageIndex, setPageIndex] = useState<number>(() => {
    if (typeof window !== "undefined") {
      try {
        const sp = new URLSearchParams(window.location.search)
        const piStr = sp.get("pi")
        const parsed = piStr ? parseInt(piStr, 10) : NaN
        if (Number.isFinite(parsed) && parsed >= 0) return parsed
      } catch {}
    }
    return 0
  })

  // Submitted search mode: only show results after Enter
  // If URL contains a search param, initialize in submitted mode to preserve deep links and back-navigation
  const [searchSubmitted, setSearchSubmitted] = useState<boolean>(false)
  const [submittedSearchQuery, setSubmittedSearchQuery] = useState<string>("")
  useEffect(() => {
    // Sync initial search state from URL on mount to avoid SSR/client mismatch
    try {
      const sp = new URLSearchParams(window.location.search)
      const s = sp.get("search")
      if (s && typeof s === "string" && s.trim().length > 0) {
        setSearchQuery(s)
        setSearchSubmitted(true)
        setSubmittedSearchQuery(s)
      }
    } catch {}
  }, [])
  const [searchCloseSignal, setSearchCloseSignal] = useState(0)

  // Exit search mode when query clears
  useEffect(() => {
    if ((searchQuery || "").trim().length === 0 && searchSubmitted) {
      setSearchSubmitted(false)
      setSubmittedSearchQuery("")
    }
  }, [searchQuery])

  // (Initialized from URL in useState initializer)
  const folderInitRef = useRef(false)

  // Load labels (user + system); store user-labels list and byId map
  useEffect(() => {
    const loadLabels = async () => {
      try {
        const res = await fetch("/api/labels")
        const data = await res.json()
        const labels = Array.isArray(data?.labels) ? data.labels : []
        const userOnly = labels
          .filter((l: any) => l?.type === "USER")
          .map((l: any) => ({ id: String(l.id), name: String(l.name), color: typeof l?.color === "string" ? l.color : undefined }))
        setUserLabels(userOnly)
        const byId = Object.fromEntries(
          labels.map((l: any) => [String(l.id), { id: String(l.id), name: String(l.name), type: l.type === "USER" ? "USER" : "SYSTEM", color: typeof l?.color === "string" ? l.color : undefined }]),
        ) as Record<string, { id: string; name: string; type: "SYSTEM" | "USER"; color?: string }>
        setLabelsById(byId)
      } catch {}
    }
    loadLabels()
    // Also load draft thread IDs on mount
    loadDraftThreads()
  }, [])

  // Load user settings for avatar/name/email
  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const res = await fetch("/api/settings")
        const data = await res.json()
        const s = data?.settings
        if (!cancelled && s) {
          setUserSettings({ displayName: String(s.displayName || "User"), email: typeof s.email === "string" ? s.email : undefined })
        }
      } catch {}
    })()
    return () => {
      cancelled = true
    }
  }, [])

  const avatarText = useMemo(() => {
    const name = (userSettings?.displayName || "").trim()
    if (name && name !== "User") {
      const parts = name.split(/\s+/).filter(Boolean)
      return parts.slice(0, 2).map((p) => p.charAt(0).toUpperCase()).join("") || "Y"
    }
    const email = (userSettings?.email || "").trim()
    if (email) {
      const local = email.split("@")[0]
      const parts = local.replace(/[._-]+/g, " ").split(" ").filter(Boolean)
      return parts.slice(0, 2).map((p) => p.charAt(0).toUpperCase()).join("") || "Y"
    }
    return "Y"
  }, [userSettings])

  // Keep folder in URL for back-navigation (only after initial URL -> state sync)
  useEffect(() => {
    if (!folderInitRef.current) return
    try {
      const sp = new URLSearchParams(window.location.search)
      sp.set("folder", currentFolder)
      const newUrl = `${window.location.pathname}?${sp.toString()}`
      window.history.replaceState(null, "", newUrl)
    } catch {}
  }, [currentFolder])

  // Initialize folder from URL on mount (avoid SSR/client mismatch)
  useEffect(() => {
    try {
      const sp = new URLSearchParams(window.location.search)
      // Only write default if folder missing; avoid overriding real folder from SSR
      if (!sp.get("folder")) {
        sp.set("folder", currentFolder)
        const newUrl = `${window.location.pathname}?${sp.toString()}`
        window.history.replaceState(null, "", newUrl)
      }
    } catch {}
    folderInitRef.current = true
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  

  // Persist page size across navigations (URL + localStorage)
  useEffect(() => {
    try {
      window.localStorage.setItem("gmailPageSize", String(pageSize))
    } catch {}
    try {
      const sp = new URLSearchParams(window.location.search)
      sp.set("ps", String(pageSize))
      const newUrl = `${window.location.pathname}?${sp.toString()}`
      window.history.replaceState(null, "", newUrl)
    } catch {}
  }, [pageSize])

  // Keep search query in URL for back-navigation and reloads
  useEffect(() => {
    try {
      const sp = new URLSearchParams(window.location.search)
      if (searchQuery && searchQuery.trim().length > 0) sp.set("search", searchQuery)
      else sp.delete("search")
      const newUrl = `${window.location.pathname}?${sp.toString()}`
      window.history.replaceState(null, "", newUrl)
    } catch {}
  }, [searchQuery])

  // Keep page index in URL
  useEffect(() => {
    try {
      const sp = new URLSearchParams(window.location.search)
      sp.set("pi", String(pageIndex))
      const newUrl = `${window.location.pathname}?${sp.toString()}`
      window.history.replaceState(null, "", newUrl)
    } catch {}
  }, [pageIndex])

  // Auto-refresh when tab regains focus or becomes visible.
  // Avoid auto-refresh while in search mode to prevent snapping away from results.
  useEffect(() => {
    if (searchSubmitted) return
    const refreshIfVisible = () => {
      try {
        refreshEmails()
      } catch {}
    }
    const onVisibility = () => {
      if (document.visibilityState === "visible") refreshIfVisible()
    }
    window.addEventListener("pageshow", refreshIfVisible)
    window.addEventListener("focus", refreshIfVisible)
    document.addEventListener("visibilitychange", onVisibility)
    return () => {
      window.removeEventListener("pageshow", refreshIfVisible)
      window.removeEventListener("focus", refreshIfVisible)
      document.removeEventListener("visibilitychange", onVisibility)
    }
  }, [searchSubmitted])

  const loadCounts = async () => {
    try {
      const res = await fetch("/api/counters")
      const data = await res.json()
      setFolderUnreadCounts(data?.system || {})
      setLabelUnreadCounts(data?.labels || {})
    } catch {}
  }

  // Track which threads have drafts so we can surface a Draft chip outside the Drafts folder
  const [draftThreadIds, setDraftThreadIds] = useState<Set<string>>(new Set())
  const loadDraftThreads = async () => {
    try {
      const res = await fetch("/api/drafts")
      const data = await res.json()
      const drafts = Array.isArray(data?.drafts) ? data.drafts : []
      const tids = new Set<string>()
      for (const m of drafts) {
        const tid = typeof m?.threadId === "string" ? m.threadId : typeof m?.id === "string" ? m.id : ""
        if (tid) tids.add(tid)
      }
      setDraftThreadIds(tids)
    } catch {}
  }

  const groupMessagesToThreads = (messages: any[]): Email[] => {
    const byThread = new Map<string, any[]>()
    for (const m of messages) {
      const tid = m.threadId || m.id
      if (!byThread.has(tid)) byThread.set(tid, [])
      byThread.get(tid)!.push(m)
    }
    const results: Email[] = []
    // Helpers to treat drastic subject changes as new conversations even with same threadId
    const normalizeSubjectBase = (s: string | undefined): string => {
      const raw = String(s || "")
      let t = raw.replace(/^(\s*(re|fw|fwd)\s*:\s*)+/gi, "")
      t = t.replace(/^(\s*\[[^\]]+\]\s*)+/g, "")
      t = t.toLowerCase().replace(/\s+/g, " ").trim()
      return t
    }
    const similarSubject = (a: string, b: string): boolean => {
      if (a === b) return true
      if (!a || !b) return false
      if (a.includes(b) || b.includes(a)) return true
      const at = a.split(/\W+/).filter((w) => w.length >= 3)
      const bt = b.split(/\W+/).filter((w) => w.length >= 3)
      if (at.length === 0 || bt.length === 0) return false
      const setA = new Set(at)
      let overlap = 0
      for (const w of bt) if (setA.has(w)) overlap += 1
      const j = overlap / Math.max(setA.size, bt.length)
      return j >= 0.6
    }
    for (const [threadId, msgsRaw] of byThread.entries()) {
      const msgsDesc = msgsRaw.slice().sort((a, b) => (a.date === b.date ? (a.id < b.id ? 1 : a.id > b.id ? -1 : 0) : a.date < b.date ? 1 : -1))
      const msgsAsc = msgsDesc.slice().reverse()
      const clusters: any[][] = []
      let current: any[] = []
      let base: string | null = null
      for (const m of msgsAsc) {
        const nb = normalizeSubjectBase(m?.subject)
        if (base === null) {
          base = nb
          current.push(m)
        } else if (similarSubject(base, nb)) {
          current.push(m)
        } else {
          clusters.push(current)
          current = [m]
          base = nb
        }
      }
      if (current.length > 0) clusters.push(current)
      // Newest cluster first
      for (const clusterAsc of clusters.reverse()) {
        const msgs = clusterAsc.slice().sort((a, b) => (a.date === b.date ? (a.id < b.id ? 1 : a.id > b.id ? -1 : 0) : a.date < b.date ? 1 : -1))
        const latest = msgs[0]
        const nonDrafts = msgs.filter((x) => !((Array.isArray(x.labelIds) ? x.labelIds : []).map((l: string) => l.toUpperCase()).includes("DRAFTS")))
        const displayLatest = nonDrafts.length > 0 ? nonDrafts[0] : latest
        const root = msgs.find((x) => !x.replyToId) || msgs[msgs.length - 1]
        const sendersSet = new Set<string>()
        for (const x of msgs) {
          const name = parseSenderName(x.from || "")
          if (name) sendersSet.add(name)
        }
        const senders = Array.from(sendersSet)
        const senderStr = senders.length > 3 ? `${senders.slice(0, 3).join(", ")}…` : senders.join(", ")
        const unreadCount = msgs.filter((x) => !x.isRead).length
        const anyStarred = msgs.some((x) => Boolean(x.isStarred))
        const hasAttachment = msgs.some((x) => Array.isArray(x.attachments) && x.attachments.length > 0)
        const labelUnion = Array.from(new Set(msgs.flatMap((x) => Array.isArray(x.labelIds) ? x.labelIds : [])))
        const nowTs = getNowTs()
        const snoozeCandidates: number[] = msgs
          .map((x) => (typeof x.snoozeUntil === "string" ? Date.parse(x.snoozeUntil) : NaN))
          .filter((t) => Number.isFinite(t) && t > nowTs) as number[]
        const earliestSnooze = snoozeCandidates.length > 0 ? new Date(Math.min(...snoozeCandidates)).toISOString() : null
        const labelsForDisplay = (() => {
          const set = new Set(labelUnion)
          if (earliestSnooze) {
            for (const v of Array.from(set)) if (String(v).toUpperCase() === "INBOX") set.delete(v)
          }
          return Array.from(set)
        })()
        const latestSubject = (displayLatest?.subject ?? "").trim()
        const fallbackSubject =
          latestSubject.length > 0
            ? latestSubject
            : [...msgs]
                .sort((a, b) => (a.date === b.date ? (a.id < b.id ? 1 : a.id > b.id ? -1 : 0) : a.date < b.date ? 1 : -1))
                .find((m) => (m.subject ?? "").trim().length > 0)?.subject ?? (root?.subject ?? "")
        const previewRaw = (() => {
          const t = (displayLatest?.text || "").trim()
          if (t.length > 0) return t
          const h = typeof displayLatest?.html === "string" ? displayLatest.html : ""
          return h ? htmlToPlainText(h) : ""
        })()
        const hasDraft = draftThreadIds.has(threadId)
        results.push({
          id: displayLatest.id,
          sender: senderStr,
          subject: fallbackSubject,
          preview: decodeForDisplay(previewRaw).replace(/\s+/g, " ").slice(0, 140),
          time: displayLatest?.date ? formatDateTime(displayLatest.date) : "",
          dateISO: displayLatest?.date || "",
          isRead: unreadCount === 0,
          isStarred: anyStarred,
          isImportant: Boolean(displayLatest?.isImportant),
          hasAttachment,
          labels: labelsForDisplay,
          threadId,
          messageCount: unreadCount,
          participants: senders,
          snoozeUntil: earliestSnooze,
          hasDraft,
        })
      }
    }
    // Sort threads by latest activity (already sorted by latest in results order)
    results.sort((a, b) => (a.dateISO === b.dateISO ? (a.id < b.id ? 1 : a.id > b.id ? -1 : 0) : a.dateISO < b.dateISO ? 1 : -1))
    return results
  }

  // Load emails from API based on folder, search, and filters
  useEffect(() => {
    const controller = new AbortController()
    const load = async () => {
      setIsChangingFolder(true)
      try {
        let grouped: Email[] = []
        if (currentFolder === "snoozed" && !searchSubmitted) {
          const res = await fetch(`/api/snoozed`, { signal: controller.signal })
          const data = await res.json()
          grouped = groupMessagesToThreads(data.messages || [])
          if (data?.threadIsStarredById && typeof data.threadIsStarredById === "object") {
            grouped = grouped.map((e) => ({
              ...e,
              isStarred: Boolean(data.threadIsStarredById?.[e.threadId || ""] ?? e.isStarred),
            }))
          }
        } else {
          const params = new URLSearchParams()
          if (searchSubmitted) {
            // Use submitted query
            const parsed = parseSearch(submittedSearchQuery)
            params.set("folder", "all")
            for (const f of activeFilters) {
              if (f.type === "label") params.set("label", f.value)
              if (f.type === "starred" && f.value === "true") params.set("starred", "true")
              if (f.type === "unread" && f.value === "true") params.set("unread", "true")
            }
            const ops = parsed.ops || {}
            if (ops.in) {
              const v = String(ops.in).toLowerCase()
              if (["inbox", "sent", "drafts", "trash", "spam", "all", "important", "anywhere"].includes(v)) {
                params.delete("label")
                if (v === "important") params.set("important", "true")
                else if (v === "anywhere") {
                  params.set("folder", "all")
                  params.set("anywhere", "true")
                } else params.set("folder", v === "all" ? "all" : v)
                if (v === "inbox") params.delete("starred")
              } else {
                params.delete("folder")
                params.set("label", String(ops.in))
              }
            }
            if (ops.from) params.set("from", String(ops.from))
            if (ops.to) params.set("to", String(ops.to))
            if (ops.cc) params.set("cc", String(ops.cc))
            if (ops.bcc) params.set("bcc", String(ops.bcc))
            if (ops.subject) params.set("subject", String(ops.subject))
            if (ops.label) params.set("label", String(ops.label))
            if (Array.isArray(ops.has)) {
              if (ops.has.includes("attachment")) params.set("has", "attachment")
              const hasMap: Record<string, string> = { drive: "drive", document: "document", spreadsheet: "spreadsheet", presentation: "presentation" }
              for (const k of Object.keys(hasMap)) if (ops.has.includes(k)) params.set("hasType", hasMap[k])
            }
            if (Array.isArray(ops.is)) {
              if (ops.is.includes("unread")) params.set("unread", "true")
              if (ops.is.includes("starred")) params.set("starred", "true")
              if (ops.is.includes("important")) params.set("important", "true")
              if (ops.is.includes("snoozed")) params.set("snoozed", "true")
            }
            if (ops.before) params.set("before", String(ops.before))
            if (ops.after) params.set("after", String(ops.after))
            if (ops.newer_than) params.set("newer_than", String(ops.newer_than))
            if (ops.older_than) params.set("older_than", String(ops.older_than))
            if (ops.filename) params.set("filename", String(ops.filename))
            if (ops.size) params.set("size", String(ops.size))
            if (ops.larger) params.set("larger", String(ops.larger))
            if (ops.smaller) params.set("smaller", String(ops.smaller))
            if (ops.list) params.set("list", String(ops.list))
            if (parsed.base.length > 0) params.set("q", parsed.base)
            params.set("expr", submittedSearchQuery)
          } else {
            // No active search: scope to current view
            if (currentFolder === "starred") params.set("starred", "true")
            else if (currentFolder === "important") params.set("important", "true")
            else if (currentFolder === "all") params.set("folder", "all")
            else if (["inbox", "sent", "drafts", "trash", "spam"].includes(currentFolder))
              params.set("folder", currentFolder)
            else params.set("label", currentFolder)
            for (const f of activeFilters) {
              if (f.type === "label") params.set("label", f.value)
              if (f.type === "starred" && f.value === "true") params.set("starred", "true")
              if (f.type === "unread" && f.value === "true") params.set("unread", "true")
            }
          }
          const res = await fetch(`/api/emails?${params.toString()}`, { signal: controller.signal })
          const data = await res.json()
          grouped = groupMessagesToThreads(data.messages || [])
          if (data?.threadIsStarredById && typeof data.threadIsStarredById === "object") {
            grouped = grouped.map((e) => ({
              ...e,
              isStarred: Boolean(data.threadIsStarredById?.[e.threadId || ""] ?? e.isStarred),
            }))
          }
        }
        setEmails(grouped)
        // Refresh counts alongside list load
        loadCounts()
      } catch (e) {
        // ignore abort errors
      } finally {
        setIsChangingFolder(false)
        setIsRefreshing(false)
      }
    }
    load()
    return () => controller.abort()
  }, [currentFolder, searchSubmitted, submittedSearchQuery, activeFilters])

  const toggleEmailSelection = (emailId: string) => {
    setSelectedEmails((prev) => (prev.includes(emailId) ? prev.filter((id) => id !== emailId) : [...prev, emailId]))
  }

  const selectAllEmails = () => {
    setSelectedEmails((prev) => {
      const ids = new Set(prev)
      for (const e of visibleEmails) ids.add(e.id)
      return Array.from(ids)
    })
  }

  const deselectAllEmails = () => {
    setSelectedEmails([])
  }

  const toggleEmailStar = async (emailId: string) => {
    const target = emails.find((e) => e.id === emailId)
    if (!target) return
    setEmails((prev) => prev.map((e) => (e.id === emailId ? { ...e, isStarred: !e.isStarred } : e)))
    try {
      const next = !target.isStarred
      if (next) {
        // Add STARRED only to the most recent message (row id is latest message id)
        await fetch(`/api/emails/${emailId}`, {
          method: "PUT",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ addLabel: "STARRED" }),
        })
      } else {
        // Removing from list item removes from ALL messages in the thread
        await fetch(`/api/emails/${emailId}`, {
          method: "PUT",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ removeLabel: "STARRED" }),
        })
      }
      loadCounts()
    } catch {}
  }

  const toggleEmailImportant = async (emailId: string) => {
    const target = emails.find((e) => e.id === emailId)
    if (!target) return
    const next = !target.isImportant
    setEmails((prev) => prev.map((e) => (e.id === emailId ? { ...e, isImportant: next } : e)))
    try {
      if (next) {
        // Add IMPORTANT only to the most recent message (row id is latest message id)
        await fetch(`/api/emails/${emailId}`, {
          method: "PUT",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ addLabel: "IMPORTANT" }),
        })
      } else {
        // Removing from list item removes IMPORTANT from ALL messages in the thread
        await fetch(`/api/emails/${emailId}`, {
          method: "PUT",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ removeLabel: "IMPORTANT" }),
        })
      }
      loadCounts()
    } catch {}
  }

  const archiveEmail = async (emailId: string) => {
    setEmails((prev) => prev.filter((email) => email.id !== emailId))
    setSelectedEmails((prev) => prev.filter((id) => id !== emailId))
    try {
      await fetch(`/api/emails/${emailId}`, {
        method: "PUT",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ action: "archive" }),
      })
      loadCounts()
    } catch {}
  }

  const deleteEmail = async (emailId: string) => {
    setEmails((prev) => prev.filter((email) => email.id !== emailId))
    setSelectedEmails((prev) => prev.filter((id) => id !== emailId))
    try {
      await fetch(`/api/emails/${emailId}`, {
        method: "PUT",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ action: "trash" }),
      })
      loadCounts()
    } catch {}
  }

  const toggleEmailRead = async (emailId: string, threadId?: string) => {
    const target = emails.find((e) => e.id === emailId)
    if (!target) return
    const nextIsRead = !target.isRead
    // Optimistic UI update
    setEmails((prev) =>
      prev.map((e) =>
        e.id === emailId ? { ...e, isRead: nextIsRead, messageCount: nextIsRead ? 0 : Math.max(e.messageCount || 0, 1) } : e,
      ),
    )
    try {
      // Always persist the exact message toggle to avoid folder-specific inconsistencies
      await fetch(`/api/emails/${emailId}`, {
        method: "PUT",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ isRead: nextIsRead }),
      })
      // Additionally, when we know the thread, mirror the state across the whole conversation
      if (threadId) {
        await fetch(`/api/threads/${threadId}`, {
          method: "PUT",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ isRead: nextIsRead }),
        })
      }
      loadCounts()
    } catch {}
  }

  // Bulk actions
  const bulkMarkRead = async (ids: string[]) => {
    if (ids.length === 0) return
    setEmails((prev) =>
      prev.map((e) => (ids.includes(e.id) ? { ...e, isRead: true, messageCount: 0 } : e)),
    )
    try {
      await Promise.all(
        ids.map((id) =>
          fetch(`/api/emails/${id}`, {
            method: "PUT",
            headers: { "content-type": "application/json" },
            body: JSON.stringify({ isRead: true }),
          }),
        ),
      )
      loadCounts()
    } catch {}
  }

  const bulkMarkUnread = async (ids: string[]) => {
    if (ids.length === 0) return
    setEmails((prev) =>
      prev.map((e) => (ids.includes(e.id) ? { ...e, isRead: false, messageCount: Math.max(e.messageCount || 0, 1) } : e)),
    )
    try {
      await Promise.all(
        ids.map((id) =>
          fetch(`/api/emails/${id}`, {
            method: "PUT",
            headers: { "content-type": "application/json" },
            body: JSON.stringify({ isRead: false }),
          }),
        ),
      )
      loadCounts()
    } catch {}
  }

  const bulkReportSpam = async (ids: string[]) => {
    if (ids.length === 0) return
    // Optimistic remove from current list
    setEmails((prev) => prev.filter((e) => !ids.includes(e.id)))
    setSelectedEmails((prev) => prev.filter((id) => !ids.includes(id)))
    try {
      await fetch(`/api/folders/spam`, {
        method: "PUT",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ messageIds: ids }),
      })
      loadCounts()
    } catch {}
  }

  const bulkSnooze = async (ids: string[], untilISO: string) => {
    if (ids.length === 0) return
    // If we're in a search results view, keep items visible (they remain searchable)
    if (!searchSubmitted) {
      // Optimistically remove from current list (snoozed view will show them)
      setEmails((prev) => prev.filter((e) => !ids.includes(e.id)))
      setSelectedEmails((prev) => prev.filter((id) => !ids.includes(id)))
    } else {
      // Optimistically update snooze + remove INBOX chip, but keep visible in results
      setEmails((prev) =>
        prev.map((e) =>
          ids.includes(e.id)
            ? {
                ...e,
                snoozeUntil: untilISO,
                labels: Array.isArray(e.labels)
                  ? e.labels.filter((l) => String(l).toUpperCase() !== "INBOX")
                  : e.labels,
              }
            : e,
        ),
      )
      setSelectedEmails((prev) => prev.filter((id) => !ids.includes(id)))
    }
    try {
      await Promise.all(
        ids.map((id) =>
          fetch(`/api/snoozed`, {
            method: "POST",
            headers: { "content-type": "application/json" },
            body: JSON.stringify({ id, snoozeUntil: untilISO }),
          }),
        ),
      )
      loadCounts()
      if (searchSubmitted) await refreshEmails()
    } catch {}
  }

  const snoozeSingle = async (id: string, untilISO: string) => {
    if (!searchSubmitted) {
      setEmails((prev) => prev.filter((e) => e.id !== id))
    } else {
      // Optimistically update snooze + remove INBOX chip, but keep in the list
      setEmails((prev) =>
        prev.map((e) =>
          e.id === id
            ? {
                ...e,
                snoozeUntil: untilISO,
                labels: Array.isArray(e.labels)
                  ? e.labels.filter((l) => String(l).toUpperCase() !== "INBOX")
                  : e.labels,
              }
            : e,
        ),
      )
    }
    setSelectedEmails((prev) => prev.filter((x) => x !== id))
    try {
      await fetch(`/api/snoozed`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ id, snoozeUntil: untilISO }),
      })
      loadCounts()
      if (searchSubmitted) await refreshEmails()
    } catch {}
  }

  const bulkMoveToFolder = async (ids: string[], folder: "inbox" | "archive" | "spam" | "trash") => {
    if (ids.length === 0) return
    setEmails((prev) => prev.filter((e) => !ids.includes(e.id)))
    setSelectedEmails((prev) => prev.filter((id) => !ids.includes(id)))
    try {
      await fetch(`/api/folders/${folder}`, {
        method: "PUT",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ messageIds: ids }),
      })
      loadCounts()
      // After server-side batch move, refresh to ensure pagination and counts stay in sync
      await refreshEmails()
    } catch {}
  }

  const bulkAddLabel = async (ids: string[], label: string) => {
    if (ids.length === 0) return
    setEmails((prev) =>
      prev.map((e) =>
        ids.includes(e.id)
          ? { ...e, labels: Array.from(new Set([...(Array.isArray(e.labels) ? e.labels : []), label])) }
          : e,
      ),
    )
    try {
      await Promise.all(
        ids.map((id) =>
          fetch(`/api/emails/${id}`, {
            method: "PUT",
            headers: { "content-type": "application/json" },
            body: JSON.stringify({ addLabel: label }),
          }),
        ),
      )
      loadCounts()
      // Ensure thread-level label unions and pagination reflect on the next render
      await refreshEmails()
    } catch {}
  }

  const bulkSetStar = async (ids: string[], nextIsStarred: boolean) => {
    if (ids.length === 0) return
    // Optimistic update: if removing stars in Starred view, hide them immediately
    if (!nextIsStarred && currentFolder === "starred") {
      setEmails((prev) => prev.filter((e) => !ids.includes(e.id)))
      setSelectedEmails((prev) => prev.filter((id) => !ids.includes(id)))
    } else {
      setEmails((prev) => prev.map((e) => (ids.includes(e.id) ? { ...e, isStarred: nextIsStarred } : e)))
    }
    try {
      await Promise.all(
        ids.map((id) =>
          fetch(`/api/emails/${id}`, {
            method: "PUT",
            headers: { "content-type": "application/json" },
            body: JSON.stringify(nextIsStarred ? { addLabel: "STARRED" } : { removeLabel: "STARRED" }),
          }),
        ),
      )
      loadCounts()
      if (!nextIsStarred && currentFolder === "starred") await refreshEmails()
    } catch {}
  }

  const createNewLabel = async (): Promise<{ id: string; name: string; color?: string } | null> => {
    const name = window.prompt("New label name", "")?.trim()
    if (!name) return null
    try {
      const res = await fetch("/api/labels", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ name }),
      })
      if (!res.ok) return null
      const data = await res.json()
      const label = data?.label as { id: string; name: string; color?: string }
      if (!label || !label.id) return null
      setUserLabels((prev) => [...prev, { id: label.id, name: label.name, color: label.color }])
      setLabelsById((prev) => ({ ...prev, [label.id]: { id: label.id, name: label.name, type: "USER", color: label.color } }))
      loadCounts()
      return label
    } catch {
      return null
    }
  }

  const refreshEmails = async () => {
    setIsRefreshing(true)
    // Trigger effect by toggling a no-op filter change (or re-run load)
    const params = new URLSearchParams()
    if (searchSubmitted) {
      const parsed = parseSearch(submittedSearchQuery)
      params.set("folder", "all")
      for (const f of activeFilters) {
        if (f.type === "label") params.set("label", f.value)
        if (f.type === "starred" && f.value === "true") params.set("starred", "true")
        if (f.type === "unread" && f.value === "true") params.set("unread", "true")
      }
      const ops = parsed.ops || {}
      if (ops.in) {
        const v = String(ops.in).toLowerCase()
        if (["inbox", "sent", "drafts", "trash", "spam", "all", "important", "anywhere"].includes(v)) {
          params.delete("label")
          if (v === "important") params.set("important", "true")
          else if (v === "anywhere") {
            params.set("folder", "all")
            params.set("anywhere", "true")
          } else params.set("folder", v === "all" ? "all" : v)
          if (v === "inbox") params.delete("starred")
        } else {
          params.delete("folder")
          params.set("label", String(ops.in))
        }
      }
      if (ops.from) params.set("from", String(ops.from))
      if (ops.to) params.set("to", String(ops.to))
      if (ops.cc) params.set("cc", String(ops.cc))
      if (ops.bcc) params.set("bcc", String(ops.bcc))
      if (ops.subject) params.set("subject", String(ops.subject))
      if (ops.label) params.set("label", String(ops.label))
      if (Array.isArray(ops.has)) {
        if (ops.has.includes("attachment")) params.set("has", "attachment")
        const hasMap: Record<string, string> = { drive: "drive", document: "document", spreadsheet: "spreadsheet", presentation: "presentation" }
        for (const k of Object.keys(hasMap)) if (ops.has.includes(k)) params.set("hasType", hasMap[k])
      }
      if (Array.isArray(ops.is)) {
        if (ops.is.includes("unread")) params.set("unread", "true")
        if (ops.is.includes("starred")) params.set("starred", "true")
        if (ops.is.includes("important")) params.set("important", "true")
        if (ops.is.includes("snoozed")) params.set("snoozed", "true")
      }
      if (ops.before) params.set("before", String(ops.before))
      if (ops.after) params.set("after", String(ops.after))
      if (ops.newer_than) params.set("newer_than", String(ops.newer_than))
      if (ops.older_than) params.set("older_than", String(ops.older_than))
      if (ops.filename) params.set("filename", String(ops.filename))
      if (ops.size) params.set("size", String(ops.size))
      if (ops.larger) params.set("larger", String(ops.larger))
      if (ops.smaller) params.set("smaller", String(ops.smaller))
      if (ops.list) params.set("list", String(ops.list))
      if (parsed.base.length > 0) params.set("q", parsed.base)
      params.set("expr", submittedSearchQuery)
    } else {
      if (currentFolder === "starred") params.set("starred", "true")
      else if (currentFolder === "important") params.set("important", "true")
      else if (currentFolder === "all") params.set("folder", "all")
      else if (["inbox", "sent", "drafts", "trash", "spam"].includes(currentFolder)) params.set("folder", currentFolder)
      else params.set("label", currentFolder)
      for (const f of activeFilters) {
        if (f.type === "label") params.set("label", f.value)
        if (f.type === "starred" && f.value === "true") params.set("starred", "true")
        if (f.type === "unread" && f.value === "true") params.set("unread", "true")
      }
    }
    try {
      const res = await fetch(`/api/emails?${params.toString()}`)
      const data = await res.json()
      let grouped = groupMessagesToThreads(data.messages || [])
      if (data?.threadIsStarredById && typeof data.threadIsStarredById === "object") {
        grouped = grouped.map((e) => ({
          ...e,
          isStarred: Boolean(data.threadIsStarredById?.[e.threadId || ""] ?? e.isStarred),
        }))
      }
      setEmails(grouped)
      loadCounts()
      loadDraftThreads()
    } catch {}
    setIsRefreshing(false)
  }

  const handleFolderChange = async (folder: string) => {
    if (folder === currentFolder) {
      // Refresh same folder: clear search and selection
      setSelectedEmails([])
      setSearchQuery("")
      setSearchSubmitted(false)
      return
    }
    setCurrentFolder(folder)
    setSelectedEmails([])
    setSearchQuery("")
    setSearchSubmitted(false)
  }

  const handleSendEmail = async (emailData: { to: string; cc?: string; bcc?: string; subject: string; body: string; htmlBody?: string }) => {
    try {
      const split = (v: string) => (v || "").split(/[;,]+/).map((s) => s.trim()).filter(Boolean)
      const to = split(emailData.to)
      const cc = split(emailData.cc || "")
      const bcc = split(emailData.bcc || "")
      if (composeDraftId) {
        await fetch(`/api/drafts/${composeDraftId}/send`, {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ to, cc: cc.length ? cc : undefined, bcc: bcc.length ? bcc : undefined, subject: emailData.subject, text: emailData.body, html: emailData.htmlBody }),
        })
      } else {
        await fetch("/api/emails", {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ to, cc: cc.length ? cc : undefined, bcc: bcc.length ? bcc : undefined, subject: emailData.subject, text: emailData.body, html: emailData.htmlBody, parentThreadId: composeParentThreadId || undefined }),
        })
      }
      // After sending, if viewing sent/all, refresh list
      if (["sent", "all", "drafts"].includes(currentFolder)) {
        await refreshEmails()
      }
      // Reset compose context
      setComposeDraftId(null)
      setComposeParentThreadId(null)
      setComposeInitials({})
    } catch {}
  }

  const loadThreadForModal = async (id: string) => {
    try {
      // Try thread first
      const tRes = await fetch(`/api/threads/${id}`)
      if (tRes.ok) {
        const data = await tRes.json()
        const t = data.thread
        const mapped: EmailThread = {
          id: t.id,
          subject: t.subject,
          participants: Array.isArray(t.participants) ? t.participants : [],
          messageCount: t.messageIds ? t.messageIds.length : t.messageCount ?? 1,
          lastActivity: t.lastActivity ?? "",
          isStarred: Boolean(t.isStarred),
          messages: (t.messages || []).map((m: any) => ({
            id: m.id,
            sender: parseSenderName(m.from || ""),
            senderEmail: (m.from || "").match(/<([^>]+)>/)?.[1]?.trim() || "",
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
            attachments: Array.isArray(m.attachments) ? m.attachments.map((a: any) => ({ name: a.filename, size: `${Math.round((a.size || 0) / 1024)} KB` })) : [],
          })),
        }
        setModalThread(mapped)
        return
      }
      // Fallback: treat as message id
      const mRes = await fetch(`/api/emails/${id}`)
      if (mRes.ok) {
        const { message: msg } = await mRes.json()
        const mapped: EmailThread = {
          id: (msg?.threadId as string) || id,
          subject: msg?.subject ?? "",
          participants: [],
          messageCount: 1,
          lastActivity: msg?.date ?? "",
          isStarred: Boolean(msg?.isStarred),
          messages: [
            {
              id: msg?.id,
              sender: parseSenderName(msg?.from || ""),
              senderEmail: (msg?.from || "").match(/<([^>]+)>/)?.[1]?.trim() || "",
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
              attachments: Array.isArray(msg?.attachments) ? msg.attachments.map((a: any) => ({ name: a.filename, size: `${Math.round((a.size || 0) / 1024)} KB` })) : [],
            },
          ],
        }
        setModalThread(mapped)
      }
    } catch {}
  }

  const handleThreadClick = async (messageId: string) => {
    // Optimistically mark as read in UI
    setEmails((prev) => prev.map((e) => (e.id === messageId ? { ...e, isRead: true } : e)))
    try {
      // Persist read state
      fetch(`/api/emails/${messageId}`, {
        method: "PUT",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ isRead: true }),
      }).catch(() => {})

      // Resolve email to determine destination and handle drafts specially
      const emailRes = await fetch(`/api/emails/${messageId}`)
      if (!emailRes.ok) return
      const emailData = await emailRes.json()
      const msg = emailData.message
      const threadId = msg?.threadId || null

      if (currentFolder === "drafts" && Array.isArray(msg?.labelIds) && msg.labelIds.includes("DRAFTS")) {
        // Check if thread has any non-draft messages
        let hasNonDraft = false
        if (threadId) {
          try {
            const tRes = await fetch(`/api/threads/${threadId}`)
            if (tRes.ok) {
              const tData = await tRes.json()
              const t = tData.thread
              hasNonDraft = Array.isArray(t?.messages) && t.messages.some((m: any) => !(Array.isArray(m?.labelIds) && m.labelIds.includes("DRAFTS")))
            }
          } catch {}
        }
        if (!hasNonDraft) {
          // Open overlay composer on top of current list view
          setComposeDraftId(msg.id)
          setComposeParentThreadId(threadId)
          setComposeInitials({
            to: Array.isArray(msg.to) ? msg.to.join(", ") : "",
            cc: Array.isArray(msg.cc) ? msg.cc.join(", ") : "",
            bcc: Array.isArray(msg.bcc) ? msg.bcc.join(", ") : "",
            subject: msg.subject || "",
            body: msg.text || "",
          })
          setShowCompose(true)
          return
        }
      }

      if (threadOpenMode === "modal") {
        setShowThreadModal(true)
        await loadThreadForModal(threadId || messageId)
        return
      } else {
        // Navigate to dedicated thread page (falls back to single-message rendering there)
        if (typeof window !== "undefined") {
          const params = new URLSearchParams(window.location.search)
          params.set("from", currentFolder)
          const destId = threadId || messageId
          window.location.assign(`/thread/${destId}?${params.toString()}`)
        }
      }
    } catch {}
  }

  // Thread modal handlers (feature parity with thread page)
  const modalNavigateBack = () => setShowThreadModal(false)
  const modalHandleStar = async (tid: string) => {
    try {
      const nextIsStarred = !(modalThread?.isStarred ?? false)
      const latest = modalThread?.messages[modalThread.messages.length - 1]
      if (latest) {
        await fetch(`/api/emails/${latest.id}`, {
          method: "PUT",
          headers: { "content-type": "application/json" },
          body: JSON.stringify(nextIsStarred ? { addLabel: "STARRED" } : { removeLabel: "STARRED" }),
        })
      }
      if (modalThread) {
        const updatedMessages = modalThread.messages.map((m, idx) => (nextIsStarred ? { ...m, isStarred: idx === modalThread.messages.length - 1 } : { ...m, isStarred: false }))
        setModalThread({ ...modalThread, isStarred: nextIsStarred, messages: updatedMessages })
      }
    } catch {}
  }
  const modalHandleMessageStarToggle = async (messageId: string, nextIsStarred: boolean) => {
    try {
      await fetch(`/api/emails/${messageId}`, { method: "PUT", headers: { "content-type": "application/json" }, body: JSON.stringify({ isStarred: nextIsStarred }) })
      if (modalThread) {
        const updated = modalThread.messages.map((m) => (m.id === messageId ? { ...m, isStarred: nextIsStarred } : m))
        const anyStar = updated.some((m) => m.isStarred)
        setModalThread({ ...modalThread, isStarred: anyStar, messages: updated })
      }
    } catch {}
  }
  const modalHandleMessageReadToggle = async (messageId: string, nextIsRead: boolean) => {
    try {
      await fetch(`/api/emails/${messageId}`, { method: "PUT", headers: { "content-type": "application/json" }, body: JSON.stringify({ isRead: nextIsRead }) })
      if (modalThread) {
        const updated = modalThread.messages.map((m) => (m.id === messageId ? { ...m, isRead: nextIsRead } : m))
        setModalThread({ ...modalThread, messages: updated })
        setEmails((prev) =>
          prev.map((e) =>
            e.threadId === modalThread.id
              ? { ...e, isRead: nextIsRead, messageCount: nextIsRead ? 0 : Math.max(e.messageCount || 0, 1) }
              : e,
          ),
        )
      }
      loadCounts()
    } catch {}
  }
  const modalHandleArchive = async (tid: string) => {
    try {
      const latest = modalThread?.messages[modalThread.messages.length - 1]
      if (latest) await fetch(`/api/emails/${latest.id}`, { method: "PUT", headers: { "content-type": "application/json" }, body: JSON.stringify({ action: "archive" }) })
    } catch {}
    setShowThreadModal(false)
    await refreshEmails()
  }
  const modalHandleDelete = async (tid: string) => {
    try {
      const latest = modalThread?.messages[modalThread.messages.length - 1]
      if (latest) await fetch(`/api/emails/${latest.id}`, { method: "PUT", headers: { "content-type": "application/json" }, body: JSON.stringify({ action: "trash" }) })
    } catch {}
    setShowThreadModal(false)
    await refreshEmails()
  }
  const modalHandleReply = (messageId: string) => {
    const target = modalThread?.messages.find((m) => m.id === messageId) || modalThread?.messages[modalThread!.messages.length - 1]
    const to = (target?.senderEmail || target?.sender || target?.recipient || "").replace(/^.*<|>.*$/g, "")
    setThreadComposeMode("reply")
    setThreadComposeInitials({ to, subject: modalThread ? (/^re\s*:/i.test(modalThread.subject) ? modalThread.subject : `Re: ${modalThread.subject}`) : "", body: "\n\n" })
    setShowCompose(true)
  }
  const modalHandleReplyAll = (messageId: string) => {
    const target = modalThread?.messages.find((m) => m.id === messageId) || modalThread?.messages[modalThread!.messages.length - 1]
    const recipients = new Set<string>()
    if (target?.senderEmail) recipients.add(target.senderEmail)
    for (const t of (target as any)?.to || []) recipients.add(t)
    for (const t of (target as any)?.cc || []) recipients.add(t)
    setThreadComposeMode("replyAll")
    setThreadComposeInitials({ to: Array.from(recipients).join(", "), subject: modalThread ? (/^re\s*:/i.test(modalThread.subject) ? modalThread.subject : `Re: ${modalThread.subject}`) : "", body: "\n\n" })
    setShowCompose(true)
  }
  const modalHandleForward = (messageId: string) => {
    const target = modalThread?.messages.find((m) => m.id === messageId) || modalThread?.messages[modalThread!.messages.length - 1]
    const headerLines = [
      "---------- Forwarded message ----------",
      target?.sender && target?.senderEmail ? `From: ${target.sender} <${target.senderEmail}>` : "",
      target?.timestamp ? `Date: ${new Date(target.timestamp).toLocaleString()}` : "",
      modalThread?.subject ? `Subject: ${modalThread.subject}` : "",
      target?.recipient ? `To: ${target.recipient}` : "",
    ].filter(Boolean)
    const quoted = `${headerLines.join("\n")}\n\n${target?.body || ""}`
    setThreadComposeMode("forward")
    setThreadComposeInitials({ to: "", subject: modalThread?.subject ? `Fwd: ${modalThread.subject}` : "Fwd:", body: `\n\n${quoted}` })
    setShowCompose(true)
  }
  const modalHandleSend = async (emailData: { to: string; cc?: string; bcc?: string; subject: string; body: string; htmlBody?: string }) => {
    try {
      if (!modalThread) return
      await fetch(`/api/threads/${modalThread.id}/messages`, {
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
      const res = await fetch(`/api/threads/${modalThread.id}`)
      if (res.ok) {
        const data = await res.json()
        const t = data.thread
        const mapped: EmailThread = {
          id: t.id,
          subject: t.subject,
          participants: Array.isArray(t.participants) ? t.participants : [],
          messageCount: t.messageIds ? t.messageIds.length : t.messageCount ?? 1,
          lastActivity: t.lastActivity ?? "",
          isStarred: Boolean(t.isStarred),
          messages: (t.messages || []).map((m: any) => ({
            id: m.id,
            sender: parseSenderName(m.from || ""),
            senderEmail: (m.from || "").match(/<([^>]+)>/)?.[1]?.trim() || "",
            recipient: (m.to || []).join(", "),
            to: Array.isArray(m.to) ? m.to : [],
            cc: Array.isArray(m.cc) ? m.cc : [],
            bcc: Array.isArray(m.bcc) ? m.bcc : [],
            subject: m.subject ?? "",
            body: decodeForDisplay(m.text || ""),
            timestamp: m.date ?? "",
            isRead: Boolean(m.isRead),
            isStarred: Boolean(m.isStarred),
            hasAttachment: Array.isArray(m.attachments) && m.attachments.length > 0,
            attachments: Array.isArray(m.attachments) ? m.attachments.map((a: any) => ({ name: a.filename, size: `${Math.round((a.size || 0) / 1024)} KB` })) : [],
          })),
        }
        setModalThread(mapped)
      }
    } catch {}
  }

  const handleBackToList = () => {
    setCurrentThread(null)
  }

  const handleThreadReply = (messageId: string) => {
    console.log("Reply to message:", messageId)
    setShowCompose(true)
  }

  const handleThreadReplyAll = (messageId: string) => {
    console.log("Reply all to message:", messageId)
    setShowCompose(true)
  }

  const handleThreadForward = (messageId: string) => {
    console.log("Forward message:", messageId)
    setShowCompose(true)
  }

  const handleThreadStar = async (threadId: string) => {
    try {
      await fetch(`/api/threads/${threadId}`, {
        method: "PUT",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ isStarred: !(currentThread?.isStarred ?? false) }),
      })
      if (currentThread) setCurrentThread({ ...currentThread, isStarred: !currentThread.isStarred })
    } catch {}
  }

  const handleMessageStarToggle = async (messageId: string, nextIsStarred: boolean) => {
    try {
      await fetch(`/api/emails/${messageId}`, {
        method: "PUT",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ isStarred: nextIsStarred }),
      })
      if (currentThread) {
        const updatedMessages = currentThread.messages.map((m) =>
          m.id === messageId ? { ...m, isStarred: nextIsStarred } : m,
        )
        const anyStarred = updatedMessages.some((m) => m.isStarred)
        setCurrentThread({ ...currentThread, messages: updatedMessages, isStarred: anyStarred })
        setEmails((prev) => prev.map((e) => (e.threadId === currentThread.id ? { ...e, isStarred: anyStarred } : e)))
      }
      loadCounts()
    } catch {}
  }
  const handleMessageReadToggle = async (messageId: string, nextIsRead: boolean) => {
    try {
      await fetch(`/api/emails/${messageId}`, {
        method: "PUT",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ isRead: nextIsRead }),
      })
      if (currentThread) {
        const updatedMessages = currentThread.messages.map((m) => (m.id === messageId ? { ...m, isRead: nextIsRead } : m))
        setCurrentThread({ ...currentThread, messages: updatedMessages })
      }
      if (currentThread) {
        setEmails((prev) =>
          prev.map((e) =>
            e.threadId === currentThread.id
              ? { ...e, isRead: nextIsRead, messageCount: nextIsRead ? 0 : Math.max(e.messageCount || 0, 1) }
              : e,
          ),
        )
      }
      loadCounts()
    } catch {}
  }

  const handleThreadArchive = async (threadId: string) => {
    // Move all messages in thread to archive by archiving the most recent
    try {
      const latest = emails.find((e) => e.threadId === threadId)
      if (latest) await archiveEmail(latest.id)
    } catch {}
    setCurrentThread(null)
  }

  const handleThreadDelete = async (threadId: string) => {
    try {
      const latest = emails.find((e) => e.threadId === threadId)
      if (latest) await deleteEmail(latest.id)
    } catch {}
    setCurrentThread(null)
  }

  const handleFilterAdd = (filter: SearchFilter) => {
    setActiveFilters((prev) => [...prev, filter])
  }

  const handleFilterRemove = (filterId: string) => {
    setActiveFilters((prev) => prev.filter((f) => f.id !== filterId))
  }

  const handleClearAllFilters = () => {
    setActiveFilters([])
    setSearchQuery("")
  }

  const getFilteredEmails = () => {
    let filtered = emails

    // Server already filters by folder/label; keep client filters minimal
    switch (currentFolder) {
      case "starred":
        filtered = emails.filter((email) => email.isStarred)
        break
      case "important":
        filtered = emails.filter((email) => email.isImportant)
        break
      default:
        filtered = emails
    }

    // Server applies text + operator filters; avoid client-side duplication

    activeFilters.forEach((filter) => {
      switch (filter.type) {
        case "sender":
          filtered = filtered.filter((email) => email.sender.toLowerCase().includes(filter.value.toLowerCase()))
          break
        case "subject":
          filtered = filtered.filter((email) => email.subject.toLowerCase().includes(filter.value.toLowerCase()))
          break
        case "has":
          if (filter.value === "attachment") {
            filtered = filtered.filter((email) => email.hasAttachment)
          }
          break
        case "label":
          filtered = filtered.filter((email) =>
            email.labels?.some((label) => label.toLowerCase() === filter.value.toLowerCase()),
          )
          break
        case "starred":
          if (filter.value === "true") {
            filtered = filtered.filter((email) => email.isStarred)
          }
          break
        case "unread":
          if (filter.value === "true") {
            filtered = filtered.filter((email) => !email.isRead)
          }
          break
        case "date":
          break
      }
    })

    return filtered
  }

  const filteredEmails = useMemo(() => getFilteredEmails(), [emails, currentFolder, searchQuery, activeFilters])

  // Reset to first page when critical filters change or pageSize updates
  const didMountRef = useRef(false)
  useEffect(() => {
    if (!didMountRef.current) {
      didMountRef.current = true
      return
    }
    setPageIndex(0)
  }, [currentFolder, searchQuery, activeFilters, pageSize])

  const totalCount = filteredEmails.length
  const totalPages = Math.max(1, Math.ceil(Math.max(totalCount, 0) / Math.max(pageSize, 1)))
  const clampedPageIndex = Math.min(Math.max(pageIndex, 0), totalPages - 1)
  const pageStart = clampedPageIndex * pageSize
  const pageEnd = Math.min(pageStart + pageSize, totalCount)

  const visibleEmails = useMemo(() => filteredEmails.slice(pageStart, pageEnd), [filteredEmails, pageStart, pageEnd])

  // Clear any selections when changing pages or page size
  useEffect(() => {
    setSelectedEmails([])
  }, [clampedPageIndex, pageSize])

  // Also clear selections when a new search is submitted or search mode toggles
  useEffect(() => {
    setSelectedEmails([])
  }, [submittedSearchQuery, searchSubmitted])

  const allSelected = visibleEmails.length > 0 && visibleEmails.every((e) => selectedEmails.includes(e.id))
  const someSelected = visibleEmails.some((e) => selectedEmails.includes(e.id)) && !allSelected

  const allSelectedAreStarred = useMemo(
    () => selectedEmails.length > 0 && selectedEmails.every((id) => Boolean(emails.find((e) => e.id === id)?.isStarred)),
    [selectedEmails, emails],
  )

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="flex items-center justify-between px-4 py-2 border-b border-gray-200">
        <div className="flex items-center gap-4">
          {navPosition === "side" && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                // Toggle mode between collapsed-by-default and expanded-by-default
                setSidebarDefaultCollapsed((prev) => {
                  const nextModeCollapsed = !prev
                  // When switching mode, immediately set the visual state to match the new default
                  setSidebarpsed(nextModeCollapsed)
                  return nextModeCollapsed
                })
              }}
              className="hover:bg-gray-100 transition-colors p-2 rounded-full"
            >
              <Menu className="h-5 w-5 " />
            </Button>
          )}
          <div className="flex items-center gap-2">
            <LogoIcon variant={appLogo} />
            <span className="text-xl font-normal">{appName}</span>
          </div>
        </div>

        <SearchFilters
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          onSubmit={(finalQ?: string) => {
            const q = (typeof finalQ === "string" ? finalQ : (searchQuery || "")).trim()
            if (q.length === 0) {
              setSearchSubmitted(false)
              setSubmittedSearchQuery("")
            } else {
              setSearchSubmitted(true)
              setSubmittedSearchQuery(q)
            }
            // Clear any previous selections when running a new query
            setSelectedEmails([])
            setSearchCloseSignal((s) => s + 1)
          }}
          externalCloseSignal={searchCloseSignal}
          activeFilters={activeFilters}
          onFilterAdd={handleFilterAdd}
          onFilterRemove={handleFilterRemove}
          onClearAll={handleClearAllFilters}
        />

        <div className="flex items-center gap-1">
          <Button variant="ghost" size="sm" className="hover:bg-gray-100 transition-colors p-2 rounded-full">
            <HelpCircle className="h-5 w-5 " />
          </Button>
          <Button variant="ghost" size="sm" className="hover:bg-gray-100 transition-colors p-2 rounded-full">
            <Settings className="h-5 w-5 " />
          </Button>
          <Button variant="ghost" size="sm" className="hover:bg-gray-100 transition-colors p-2 rounded-full">
            <Grid3X3 className="h-5 w-5 " />
          </Button>
          <div className="flex items-center gap-2 ml-2">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <div>
                  <Avatar className="h-8 w-8 hover:ring-2 hover:ring-gray-200 transition-all cursor-pointer" title={userSettings?.email || userSettings?.displayName || undefined}>
                    <AvatarFallback className="bg-blue-500 text-white text-sm font-medium">{avatarText}</AvatarFallback>
                  </Avatar>
                </div>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-64">
                <DropdownMenuLabel>{userSettings?.displayName || "User"}</DropdownMenuLabel>
                <DropdownMenuSeparator />
                {userSettings?.email && (
                  <DropdownMenuItem asChild>
                    <span className="text-gray-700 truncate" title={userSettings.email}>{userSettings.email}</span>
                  </DropdownMenuItem>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar or Top nav */}
        {navPosition === "side" ? (
          <div
            onPointerEnter={() => {
              // Only auto-expand on hover in collapsed-by-default mode
              if (sidebarDefaultCollapsed && Date.now() >= sidebarHoverLockUntil) setSidebarpsed(false)
            }}
            onPointerLeave={() => {
              // Only auto-collapse on leave in collapsed-by-default mode
              if (sidebarDefaultCollapsed && Date.now() >= sidebarHoverLockUntil) setSidebarpsed(true)
            }}
          >
            <SidebarNavigation
              ispsed={sidebarpsed}
              currentFolder={searchSubmitted ? "__none__" : currentFolder}
              emails={emails}
              folderUnreadCounts={folderUnreadCounts}
              labelUnreadCounts={labelUnreadCounts}
              labels={userLabels}
              onFolderChange={handleFolderChange}
              onCompose={() => {
                // Prevent hover collapse during compose click/open animation
                setSidebarHoverLockUntil(Date.now() + 1200)
                setShowCompose(true)
              }}
              onCreateLabel={async () => {
                try {
                  await createNewLabel()
                } catch {}
              }}
              position="side"
            />
          </div>
        ) : null}

        {/* Content + Right rail */}
        <div className="flex flex-1 overflow-hidden">
          {currentThread ? (
            <EmailThreadView
              thread={currentThread}
              onBack={handleBackToList}
              onReply={handleThreadReply}
              onReplyAll={handleThreadReplyAll}
              onForward={handleThreadForward}
              onStar={handleThreadStar}
              onArchive={handleThreadArchive}
              onDelete={handleThreadDelete}
              onMessageStarToggle={handleMessageStarToggle}
              onMessageToggleRead={handleMessageReadToggle}
            />
          ) : (
            <main className="flex-1 flex flex-col min-w-0">
              {navPosition === "top" ? (
                <SidebarNavigation
                  ispsed={false}
                  currentFolder={searchSubmitted ? "__none__" : currentFolder}
                  emails={emails}
                  folderUnreadCounts={folderUnreadCounts}
                  labelUnreadCounts={labelUnreadCounts}
                  labels={userLabels}
                  onFolderChange={handleFolderChange}
                  onCompose={() => setShowCompose(true)}
                  onCreateLabel={async () => {
                    try {
                      await createNewLabel()
                    } catch {}
                  }}
                  position="top"
                />
              ) : null}
              {/* Selection toolbar (top bar) */}
              <div className="flex items-center justify-between px-4 py-2 border-b border-gray-200 ">
                <div className="flex items-center gap-2">
                  <Button variant="ghost" size="sm" onClick={allSelected ? deselectAllEmails : selectAllEmails} className="p-1" title={allSelected ? "Deselect all" : "Select all"} aria-label={allSelected ? "Deselect all emails" : "Select all emails"}>
                    {allSelected ? (
                      <CheckSquare className="h-4 w-4" />
                    ) : someSelected ? (
                      <div className="h-4 w-4 border-2 border-gray-400 bg-gray-400 rounded-sm flex items-center justify-center">
                        <div className="h-1 w-2 "></div>
                      </div>
                    ) : (
                      <Square className="h-4 w-4" />
                    )}
                  </Button>

                  <Button variant="ghost" size="sm" onClick={refreshEmails} title="Refresh" aria-label="Refresh">
                    <RefreshCw className="h-4 w-4" />
                  </Button>

                  {selectedEmails.length > 0 && (
                    <>
                      <div className="h-4 w-px bg-gray-300 mx-1"></div>

                      <Button variant="ghost" size="sm" onClick={() => bulkMoveToFolder(selectedEmails, "archive")} title="Archive">
                        {randomization?.threadIcons?.archive === "box" ? (
                          <Box className="h-4 w-4" />
                        ) : (
                          <Archive className="h-4 w-4" />
                        )}
                      </Button>

                      <Button variant="ghost" size="sm" onClick={() => bulkMoveToFolder(selectedEmails, "trash")} title="Trash">
                        {randomization?.threadIcons?.trash === "trash" ? (
                          <Trash className="h-4 w-4" />
                        ) : (
                          <Trash2 className="h-4 w-4" />
                        )}
                      </Button>

                      <Button variant="ghost" size="sm" onClick={() => bulkReportSpam(selectedEmails)} title="Report spam">
                        <AlertCircle className="h-4 w-4" />
                      </Button>

                      <Button variant="ghost" size="sm" onClick={() => bulkMarkRead(selectedEmails)} title="Mark as read">
                        <MailOpen className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => bulkMarkUnread(selectedEmails)} title="Mark as unread">
                        <Mail className="h-4 w-4" />
                      </Button>

                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm" title="Snooze">
                            <Clock className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="start">
                          <DropdownMenuLabel>Snooze</DropdownMenuLabel>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            onClick={() => {
                              bulkSnooze(selectedEmails, snoozeLaterTodayISO())
                            }}
                          >
                            Later today
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() => {
                              bulkSnooze(selectedEmails, snoozeTomorrowISO())
                            }}
                          >
                            Tomorrow
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() => {
                              bulkSnooze(selectedEmails, snoozeThisWeekendISO())
                            }}
                          >
                            This weekend
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() => {
                              bulkSnooze(selectedEmails, snoozeNextWeekISO())
                            }}
                          >
                            Next week
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            onClick={() => {
                              const input = window.prompt("Pick date/time (YYYY-MM-DD HH:MM, 24h)", "")
                              if (!input) return
                              const [datePart, timePart] = input.split(" ")
                              if (!datePart || !timePart) return
                              const iso = buildFixedZonedISOFromInputs(datePart, timePart)
                              bulkSnooze(selectedEmails, iso)
                            }}
                          >
                            Pick date & time…
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>

                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm" title="Move to">
                            <FolderIcon className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="start">
                          <DropdownMenuLabel>Move to</DropdownMenuLabel>
                          <DropdownMenuSeparator />
                          {([
                            { id: "inbox", name: "Inbox" },
                            { id: "spam", name: "Spam" },
                            { id: "trash", name: "Trash" },
                          ] as const).map((f) => (
                            <DropdownMenuItem key={f.id} onClick={() => bulkMoveToFolder(selectedEmails, f.id)}>
                              {f.name}
                            </DropdownMenuItem>
                          ))}
                        </DropdownMenuContent>
                      </DropdownMenu>

                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm" title="Add label">
                            <TagIcon className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="start" key={userLabels.length}>
                          <DropdownMenuLabel>Add label</DropdownMenuLabel>
                          <DropdownMenuSeparator />
                          {(userLabels || []).map((l) => (
                            <DropdownMenuItem key={l.id} onClick={() => bulkAddLabel(selectedEmails, l.id)}>
                              {l.name}
                            </DropdownMenuItem>
                          ))}
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            onClick={async () => {
                              const created = await createNewLabel()
                              if (created && selectedEmails.length > 0) {
                                await bulkAddLabel(selectedEmails, created.id)
                              }
                            }}
                          >
                            Create new label…
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>

                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm" title="More">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="start">
                          <DropdownMenuItem onClick={() => bulkSetStar(selectedEmails, !allSelectedAreStarred)}>
                            {allSelectedAreStarred ? (
                              <StarOff className="h-4 w-4 mr-2" />
                            ) : (
                              <Star className="h-4 w-4 mr-2" />
                            )}
                            {allSelectedAreStarred ? "Remove star" : "Add star"}
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>

                      {selectedEmails.length > 0 && (
                        <Badge variant="secondary" className="ml-2">
                          {selectedEmails.length} selected
                        </Badge>
                      )}
                    </>
                  )}
                </div>
                <div className="flex items-center gap-3 text-sm ">
                  <span className="hidden sm:inline">Rows per page</span>
                  <select
                    className="border border-gray-300 rounded px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
                    value={pageSize}
                    onChange={(e) => setPageSize(parseInt(e.target.value, 10))}
                  >
                    {[2, 10, 20, 50].map((n) => (
                      <option key={n} value={n}>
                        {n}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Primary bar (second bar) */}
              <div className="px-6 py-3 ">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <h2 className="text-sm font-medium ">{searchSubmitted ? "Mail" : "Primary"}</h2>
                  </div>
                  {paginationPosition === "top" && (
                    <div className="flex items-center gap-2 text-sm ">
                      <span>
                        {totalCount === 0 ? 0 : pageStart + 1}-{pageEnd} of {totalCount}
                      </span>
                      <Button
                        variant="ghost"
                        size="sm"
                        disabled={clampedPageIndex === 0 || totalCount === 0}
                        onClick={() => setPageIndex((p) => Math.max(p - 1, 0))}
                        title="Previous page"
                      >
                        <ChevronLeft className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        disabled={pageEnd >= totalCount}
                        onClick={() => setPageIndex((p) => (pageEnd >= totalCount ? p : p + 1))}
                        title="Next page"
                      >
                        <ChevronRight className="h-4 w-4" />
                      </Button>
                    </div>
                  )}
                </div>
              </div>

              <div className="flex-1 relative min-h-0">
                {isChangingFolder && (
                  <div className="absolute inset-0 bg-opacity-75 flex items-center justify-center z-10">
                    <div className="flex items-center gap-3 ">
                      <LoadingSpinner size="md" />
                      <span>Loading emails...</span>
                    </div>
                  </div>
                )}

                <EmailList
                  emails={visibleEmails}
                  selectedEmails={selectedEmails}
                  onEmailSelect={toggleEmailSelection}
                  onEmailStar={toggleEmailStar}
                  onEmailToggleImportant={toggleEmailImportant}
                  onEmailArchive={archiveEmail}
                  onEmailDelete={deleteEmail}
                  onThreadClick={handleThreadClick}
                  showInboxLabelChip={currentFolder === "all" || searchSubmitted}
                  inTrashView={currentFolder === "trash"}
                  onEmailToggleRead={toggleEmailRead}
                  labelMetaById={labelsById}
                  onEmailSnooze={snoozeSingle}
                />
              </div>

              {paginationPosition === "bottom" && (
                <div className="px-6 py-3">
                  <div className="flex items-center justify-end gap-2 text-sm ">
                    <span>
                      {totalCount === 0 ? 0 : pageStart + 1}-{pageEnd} of {totalCount}
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      disabled={clampedPageIndex === 0 || totalCount === 0}
                      onClick={() => setPageIndex((p) => Math.max(p - 1, 0))}
                      title="Previous page"
                    >
                      <ChevronLeft className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      disabled={pageEnd >= totalCount}
                      onClick={() => setPageIndex((p) => (pageEnd >= totalCount ? p : p + 1))}
                      title="Next page"
                    >
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}
            </main>
          )}

          {/* Right rail */}
          <aside className="w-12 shrink-0 border-l border-gray-200 flex flex-col items-center py-2 gap-2 relative z-20">
            <button className="p-2 hover:bg-gray-100 rounded">
              <Calendar className="h-4 w-4 " />
            </button>
            <button className="p-2 hover:bg-gray-100 rounded">
              <FileText className="h-4 w-4 " />
            </button>
            <button className="p-2 hover:bg-gray-100 rounded">
              <StickyNote className="h-4 w-4 " />
            </button>
            <button className="p-2 hover:bg-gray-100 rounded">
              <ListTodo className="h-4 w-4 " />
            </button>
          </aside>
        </div>
      </div>

      {threadOpenMode === "modal" && showThreadModal && (
        <ThreadModal
          isOpen={true}
          onClose={() => setShowThreadModal(false)}
          thread={modalThread}
          onBack={modalNavigateBack}
          onReply={modalHandleReply}
          onReplyAll={modalHandleReplyAll}
          onForward={modalHandleForward}
          onStar={modalHandleStar}
          onArchive={modalHandleArchive}
          onDelete={modalHandleDelete}
          onMessageStarToggle={modalHandleMessageStarToggle}
          onMessageToggleRead={modalHandleMessageReadToggle}
          showCompose={showCompose}
          onComposeClose={() => setShowCompose(false)}
          onComposeSend={modalHandleSend}
          threadComposeMode={threadComposeMode}
          threadComposeInitials={threadComposeInitials}
          threadComposeCloseSignal={threadComposeCloseSignal}
        />
      )}

      {/* Compose Modal (overlay). If thread modal mode is active, only show overlay when thread modal is not open. */}
      <ComposeModal
        isOpen={(threadOpenMode !== "modal" || !showThreadModal) && showCompose}
        onClose={() => {
          setShowCompose(false)
          // Clear overlay context when closing
          setComposeDraftId(null)
          setComposeParentThreadId(null)
          setComposeInitials({})
          // Update draft chip state and drafts list if relevant
          loadDraftThreads()
          if (currentFolder === "drafts") {
            // Refresh to reflect possible discard
            refreshEmails()
          }
        }}
        onSend={handleSendEmail}
        mode="compose"
        variant="overlay"
        initialTo={composeInitials.to}
        initialCc={composeInitials.cc}
        initialBcc={composeInitials.bcc}
        initialSubject={composeInitials.subject}
        initialBody={composeInitials.body}
        draftId={composeDraftId || undefined}
        parentThreadId={composeParentThreadId || undefined}
      />
    </div>
  )
}

