import { nanoid } from "nanoid"
import { htmlToPlainText, decodeForDisplay } from "@/lib/utils"
import { nowDate, nowTs } from "@/lib/clock"

// Domain types for the Gmail-like environment (merged union schema)
export type Attachment = {
  id: string
  filename: string
  mimeType: string
  dataBase64: string
  size: number
}

export type EmailMessage = {
  id: string
  threadId: string
  replyToId?: string
  from: string
  to: string[]
  cc?: string[]
  bcc?: string[]
  subject: string
  date: string // RFC3339
  text?: string
  html?: string
  attachments?: Attachment[]
  labelIds: string[] // e.g., INBOX, SENT, DRAFTS, TRASH, USER labels
  isRead: boolean
  isStarred: boolean
  isImportant: boolean
  snoozeUntil?: string | null
  isDraftDeleted?: boolean
}

export type Label = {
  id: string
  name: string
  type: "SYSTEM" | "USER"
  color?: string
}

export type EmailThread = {
  id: string
  subject: string
  participants: string[]
  messageIds: string[]
  lastActivity: string
  isStarred: boolean
  // Parent thread identifier to support branching (e.g., forwards start new threads)
  // For root threads, parentThreadId === id
  parentThreadId?: string
}

export type Settings = {
  displayName: string
  signature: string
  email?: string
}

export type ContactRecord = {
  email: string
  name?: string
}

export type ContactsDirectory = Record<string, ContactRecord>

export type GlobalState = {
  messages: EmailMessage[]
  threads: EmailThread[]
  labels: Label[]
  settings: Settings
  contacts: ContactsDirectory
}

export type UnreadCounts = {
  system: {
    inbox: number
    starred: number
    important: number
    snoozed: number
    sent: number
    drafts: number
    spam: number
    trash: number
    archive: number
    all: number
  }
  labels: Record<string, number>
}

declare global {
  // eslint-disable-next-line no-var
  var __GMAIL_STATE__: GlobalState | undefined
}

const initialState: GlobalState = {
  messages: [],
  threads: [],
  // Start with only system labels; user labels can be added via the generator or API
  labels: [
    { id: "INBOX", name: "INBOX", type: "SYSTEM" },
    { id: "SENT", name: "SENT", type: "SYSTEM" },
    { id: "DRAFTS", name: "DRAFTS", type: "SYSTEM" },
    { id: "TRASH", name: "TRASH", type: "SYSTEM" },
    { id: "SPAM", name: "SPAM", type: "SYSTEM" },
    { id: "ARCHIVE", name: "ARCHIVE", type: "SYSTEM" },
    { id: "STARRED", name: "STARRED", type: "SYSTEM" },
    { id: "IMPORTANT", name: "IMPORTANT", type: "SYSTEM" },
    // Virtual system label representing "All Mail" (messages you've received and any messages in those threads)
    { id: "ALL", name: "ALL MAIL", type: "SYSTEM" },
  ],
  settings: { displayName: "User", signature: "" },
  contacts: {},
}

let state: GlobalState = globalThis.__GMAIL_STATE__ ?? initialState
globalThis.__GMAIL_STATE__ = state

export function getState(): GlobalState {
  return state
}

export function setState(newState: GlobalState): void {
  const systemLabels = ["INBOX", "SENT", "DRAFTS", "TRASH", "SPAM", "ARCHIVE", "STARRED", "IMPORTANT", "ALL"]
  const normalizedMessages: EmailMessage[] = Array.isArray((newState as any).messages)
    ? (newState as any).messages.map((m: any) => {
        const id = typeof m?.id === "string" && m.id.length > 0 ? m.id : nanoid(8)
        const date = typeof m?.date === "string" && m.date.length > 0 ? m.date : nowDate().toISOString()
        const from = typeof m?.from === "string" && m.from.length > 0 ? m.from : "Unknown Sender <unknown@example.com>"
        const to = Array.isArray(m?.to) ? m.to.filter((x: any) => typeof x === "string") : []
        const subject = typeof m?.subject === "string" ? m.subject : "No subject"
        const text = typeof m?.text === "string" ? m.text : ""
        const labels = Array.isArray(m?.labelIds) ? m.labelIds.filter((x: any) => typeof x === "string") : []
        const hasSystem = labels.some((l: string) => systemLabels.includes(l.toUpperCase()))
        const labelIds = hasSystem ? labels : ["INBOX", ...labels]
        const threadId = typeof m?.threadId === "string" && m.threadId.length > 0 ? m.threadId : id
        const replyToId = typeof m?.replyToId === "string" && m.replyToId.length > 0 ? m.replyToId : undefined
        return {
          id,
          threadId,
          replyToId,
          from,
          to,
          cc: Array.isArray(m?.cc) ? m.cc.filter((x: any) => typeof x === "string") : undefined,
          bcc: Array.isArray(m?.bcc) ? m.bcc.filter((x: any) => typeof x === "string") : undefined,
          subject,
          date,
          text,
          html: typeof m?.html === "string" ? m.html : undefined,
          attachments: Array.isArray(m?.attachments) ? m.attachments : [],
          labelIds,
          isRead: typeof m?.isRead === "boolean" ? m.isRead : false,
          isStarred: typeof m?.isStarred === "boolean" ? m.isStarred : false,
          isImportant: typeof m?.isImportant === "boolean" ? m.isImportant : false,
          snoozeUntil: typeof m?.snoozeUntil === "string" || m?.snoozeUntil === null ? m.snoozeUntil : null,
          isDraftDeleted: typeof m?.isDraftDeleted === "boolean" ? m.isDraftDeleted : false,
        }
      })
    : []
  // Ensure "ALL" (All Mail) labeling: any received message (not from me)
  // and any message in a thread that contains a received message should carry the ALL label.
  const receivedThreadIds = new Set(
    normalizedMessages
      .filter((m) => typeof m.from === "string" && !isFromMeAddress(m.from))
      .map((m) => m.threadId)
      .filter((tid): tid is string => typeof tid === "string" && tid.length > 0),
  )
  const withAllLabel: EmailMessage[] = normalizedMessages.map((m) => {
    const labels = new Set<string>(Array.isArray(m.labelIds) ? m.labelIds : [])
    const isReceived = typeof m.from === "string" && !isFromMeAddress(m.from)
    const threadHasReceived = receivedThreadIds.has(m.threadId)
    const shouldHaveAll = isReceived || threadHasReceived
    if (shouldHaveAll) labels.add("ALL")
    else labels.delete("ALL")
    return { ...m, labelIds: Array.from(labels) }
  })
  state = {
    messages: withAllLabel,
    threads: Array.isArray(newState.threads) ? newState.threads : [],
    labels: Array.isArray(newState.labels) ? normalizeLabels(newState.labels as Label[]) : [],
    settings: newState.settings ?? { displayName: "User", signature: "" },
    // Accept either contacts or legacy users for address book input
    contacts: sanitizeContacts((newState as any).contacts ?? (newState as any).users),
  }
  // Ensure the ALL system label exists in the label registry
  if (!state.labels.some((l) => l.id === "ALL")) {
    state.labels.push({ id: "ALL", name: "ALL MAIL", type: "SYSTEM" })
  }
  globalThis.__GMAIL_STATE__ = state
}

// Email helpers
export function listEmails(filters?: {
  folder?: "inbox" | "sent" | "drafts" | "trash" | "archive" | "spam" | "all"
  starred?: boolean
  important?: boolean
  unread?: boolean
  label?: string
  q?: string
  // Extended operator-style filters
  from?: string
  to?: string
  cc?: string
  bcc?: string
  subject?: string
  hasAttachment?: boolean
  // Date bounds: ISO-like dates (YYYY-MM-DD or YYYY/MM/DD) or full ISO
  after?: string
  before?: string
  // Relative windows: e.g., "7d", "3m", "1y"
  newerThan?: string
  olderThan?: string
  // Additional operators
  filename?: string
  size?: string
  larger?: string
  smaller?: string
  hasType?: "drive" | "document" | "spreadsheet" | "presentation"
  snoozed?: boolean
  includeTrashSpam?: boolean
  list?: string
}): EmailMessage[] {
  let emails = state.messages
    .filter((m) => !m.isDraftDeleted)
    .slice()
    .sort((a, b) => (a.date === b.date ? (a.id < b.id ? 1 : a.id > b.id ? -1 : 0) : a.date < b.date ? 1 : -1))

  // While in TRASH, messages should not appear in any other folder/label views
  // Only include TRASH messages when explicitly viewing the trash folder
  const hasQuery = typeof filters?.q === "string" && filters.q.trim().length > 0
  const includeTrashSpam = filters?.includeTrashSpam === true
  const shouldExcludeTrash = !includeTrashSpam && !hasQuery && (!filters?.folder || filters.folder !== "trash")
  if (shouldExcludeTrash) {
    emails = emails.filter((e) => !(Array.isArray(e.labelIds) ? e.labelIds.map((x) => x.toUpperCase()) : []).includes("TRASH"))
  }

  if (filters?.folder && filters.folder !== "all") {
    if (filters.folder === "archive") {
      emails = emails.filter((e) => {
        const lids = Array.isArray(e.labelIds) ? e.labelIds.map((x) => x.toUpperCase()) : []
        return !lids.includes("INBOX") && !lids.includes("TRASH") && !lids.includes("SPAM")
      })
    } else {
      const sys = folderToSystemLabel(filters.folder)
      emails = emails.filter((e) => (Array.isArray(e.labelIds) ? e.labelIds.map((x) => x.toUpperCase()) : []).includes(sys))
    }
  }
  if (typeof filters?.starred === "boolean") {
    emails = emails.filter((e) => e.isStarred === filters.starred)
  }
  if (filters?.unread === true) {
    emails = emails.filter((e) => !e.isRead)
  }
  if (typeof filters?.important === "boolean") {
    emails = emails.filter((e) => e.isImportant === filters.important)
  }
  if (filters?.label) {
    const l = filters.label.toLowerCase()
    emails = emails.filter((e) => (Array.isArray(e.labelIds) ? e.labelIds.map((x) => x.toLowerCase()) : []).includes(l))
  }
  if (filters?.snoozed === true) {
    const now = nowTs()
    emails = emails.filter((e) => {
      if (typeof e.snoozeUntil !== "string") return false
      const t = Date.parse(e.snoozeUntil)
      return Number.isFinite(t) && t > now
    })
  }
  // Operator-style filters
  if (filters?.from) {
    const needle = String(filters.from).toLowerCase().trim()
    if (needle)
      emails = emails.filter((e) => {
        const fromStr = String(e.from || "").toLowerCase()
        if (fromStr.includes(needle)) return true
        try {
          const addr = extractEmailAddress(e.from)
          if (!addr) return false
          const name = state.contacts?.[addr]?.name
          return typeof name === "string" && name.toLowerCase().includes(needle)
        } catch {
          return false
        }
      })
  }
  if (filters?.to) {
    const needle = String(filters.to).toLowerCase().trim()
    if (needle) emails = emails.filter((e) => (Array.isArray(e.to) ? e.to : []).some((t) => String(t).toLowerCase().includes(needle)))
  }
  if (filters?.cc) {
    const needle = String(filters.cc).toLowerCase().trim()
    if (needle)
      emails = emails.filter((e) => (Array.isArray(e.cc) ? e.cc : []).some((t) => String(t).toLowerCase().includes(needle)))
  }
  if (filters?.bcc) {
    const needle = String(filters.bcc).toLowerCase().trim()
    if (needle)
      emails = emails.filter((e) => (Array.isArray(e.bcc) ? e.bcc : []).some((t) => String(t).toLowerCase().includes(needle)))
  }
  if (filters?.subject) {
    const needle = String(filters.subject).toLowerCase().trim()
    if (needle) emails = emails.filter((e) => String(e.subject || "").toLowerCase().includes(needle))
  }
  if (typeof filters?.hasAttachment === "boolean") {
    const want = filters.hasAttachment
    emails = emails.filter((e) => (Array.isArray(e.attachments) && e.attachments.length > 0) === want)
  }
  if (filters?.hasType) {
    const want = String(filters.hasType).toLowerCase()
    const isDocMime = (mt: string) =>
      [
        "application/vnd.google-apps.document",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      ].includes(mt)
    const isSheetMime = (mt: string) =>
      [
        "application/vnd.google-apps.spreadsheet",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      ].includes(mt)
    const isSlideMime = (mt: string) =>
      [
        "application/vnd.google-apps.presentation",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
      ].includes(mt)
    emails = emails.filter((e) =>
      (Array.isArray(e.attachments) ? e.attachments : []).some((a) => {
        const mt = String((a as any)?.mimeType || "").toLowerCase()
        if (!mt) return false
        if (want === "drive") return mt.startsWith("application/vnd.google-apps.")
        if (want === "document") return isDocMime(mt)
        if (want === "spreadsheet") return isSheetMime(mt)
        if (want === "presentation") return isSlideMime(mt)
        return false
      }),
    )
  }
  if (filters?.filename) {
    const needle = String(filters.filename).toLowerCase().trim()
    if (needle)
      emails = emails.filter((e) =>
        (Array.isArray(e.attachments) ? e.attachments : []).some((a) =>
          String((a as any)?.filename || "").toLowerCase().includes(needle),
        ),
      )
  }
  if (filters?.list) {
    const needle = String(filters.list).toLowerCase().trim()
    if (needle)
      emails = emails.filter((e) => {
        const inFrom = String(e.from || "").toLowerCase().includes(needle)
        const inTo = (Array.isArray(e.to) ? e.to : []).some((t) => String(t).toLowerCase().includes(needle))
        const inCc = (Array.isArray(e.cc) ? e.cc : []).some((t) => String(t).toLowerCase().includes(needle))
        const inBcc = (Array.isArray(e.bcc) ? e.bcc : []).some((t) => String(t).toLowerCase().includes(needle))
        return inFrom || inTo || inCc || inBcc
      })
  }
  // Date filters
  const parseAbsoluteDateStart = (s: string | undefined): number | null => {
    const raw = (s || "").trim()
    if (!raw) return null
    // Support YYYY-MM-DD, YYYY/MM/DD, YYYY.MM.DD, or full ISO
    const norm = raw.match(/^\d{4}[-\/.]\d{2}[-\/.]\d{2}$/)
      ? raw.replace(/[\.\/]/g, "-") + "T00:00:00"
      : raw
    const t = Date.parse(norm)
    return Number.isFinite(t) ? t : null
  }
  const parseRelativeWindowMs = (s: string | undefined): number | null => {
    const raw = (s || "").trim().toLowerCase()
    if (!raw) return null
    const m = raw.match(/^(\d+)\s*([dmy])$/)
    if (!m) return null
    const num = parseInt(m[1], 10)
    if (!Number.isFinite(num) || num <= 0) return null
    const unit = m[2]
    const oneDay = 24 * 60 * 60 * 1000
    if (unit === "d") return num * oneDay
    if (unit === "m") return num * 30 * oneDay
    if (unit === "y") return num * 365 * oneDay
    return null
  }
  const now = nowTs()
  const parseSizeString = (s: string | undefined): number | null => {
    const raw = (s || "").trim().toLowerCase()
    if (!raw) return null
    const m = raw.match(/^(\d+)([kmg])?$/)
    if (!m) return null
    const num = parseInt(m[1], 10)
    if (!Number.isFinite(num)) return null
    const unit = m[2]
    if (unit === "k") return num * 1024
    if (unit === "m") return num * 1024 * 1024
    if (unit === "g") return num * 1024 * 1024 * 1024
    return num
  }
  const computeMsgSize = (e: EmailMessage): number => {
    try {
      return (Array.isArray(e.attachments) ? e.attachments : []).reduce((acc, a) => acc + (typeof (a as any)?.size === "number" ? (a as any).size : 0), 0)
    } catch { return 0 }
  }
  const afterTs = parseAbsoluteDateStart(filters?.after)
  const beforeTs = parseAbsoluteDateStart(filters?.before)
  const newerMs = parseRelativeWindowMs(filters?.newerThan)
  const olderMs = parseRelativeWindowMs(filters?.olderThan)
  const sizeMin = parseSizeString(filters?.size ?? filters?.larger)
  const sizeMax = parseSizeString(filters?.smaller)
  if (afterTs !== null) {
    emails = emails.filter((e) => {
      const t = Date.parse(String(e.date || ""))
      return Number.isFinite(t) && t >= afterTs
    })
  }
  if (beforeTs !== null) {
    emails = emails.filter((e) => {
      const t = Date.parse(String(e.date || ""))
      return Number.isFinite(t) && t < beforeTs
    })
  }
  if (newerMs !== null) {
    const threshold = now - newerMs
    emails = emails.filter((e) => {
      const t = Date.parse(String(e.date || ""))
      return Number.isFinite(t) && t >= threshold
    })
  }
  if (olderMs !== null) {
    const threshold = now - olderMs
    emails = emails.filter((e) => {
      const t = Date.parse(String(e.date || ""))
      return Number.isFinite(t) && t < threshold
    })
  }
  if (sizeMin !== null) {
    emails = emails.filter((e) => computeMsgSize(e) >= sizeMin)
  }
  if (sizeMax !== null) {
    emails = emails.filter((e) => computeMsgSize(e) < sizeMax)
  }
  if (filters?.q) {
    const q = filters.q.toLowerCase()
    const tokens = q.split(/\s+/).filter(Boolean)
    emails = emails.filter((e) => {
      const subject = (e.subject || "").toLowerCase()
      const from = (e.from || "").toLowerCase()
      const to = (Array.isArray(e.to) ? e.to.join(", ") : "").toLowerCase()
      const cc = (Array.isArray(e.cc) ? e.cc.join(", ") : "").toLowerCase()
      const bcc = (Array.isArray(e.bcc) ? e.bcc.join(", ") : "").toLowerCase()
      // Augment search surface with contact names from the address book
      const nameTokens = new Set<string>()
      try {
        const addNameFor = (raw: string | undefined) => {
          const addr = extractEmailAddress(raw)
          if (!addr) return
          const name = state.contacts?.[addr]?.name
          if (name && name.trim().length > 0) nameTokens.add(name.toLowerCase())
        }
        addNameFor(e.from)
        for (const t of e.to || []) addNameFor(t)
        for (const t of e.cc || []) addNameFor(t)
        for (const t of e.bcc || []) addNameFor(t)
      } catch {}
      const textBody = decodeForDisplay(e.text || "").toLowerCase()
      const htmlBody = htmlToPlainText(e.html || "").toLowerCase()
      const combined = [subject, from, to, cc, bcc, textBody, htmlBody, Array.from(nameTokens).join(" ")].join(" \u241F ") // unit separator
      // Match if full phrase appears OR all tokens appear (order-agnostic)
      if (combined.includes(q)) return true
      return tokens.every((t) => combined.includes(t))
    })
  }
  return emails
}

export function getEmailById(id: string): EmailMessage | undefined {
  return state.messages.find((e) => e.id === id)
}

export function updateEmail(
  id: string,
  updates: Partial<
    Pick<
      EmailMessage,
      | "isRead"
      | "isStarred"
      | "isImportant"
      | "labelIds"
      | "to"
      | "cc"
      | "bcc"
      | "subject"
      | "text"
      | "html"
      | "attachments"
      | "snoozeUntil"
    >
  >,
): EmailMessage | undefined {
  const idx = state.messages.findIndex((e) => e.id === id)
  if (idx === -1) return undefined
  const current = state.messages[idx]
  // Only apply fields that are explicitly defined to avoid clobbering existing values
  const definedUpdates = Object.fromEntries(
    Object.entries(updates).filter(([, v]) => v !== undefined),
  ) as typeof updates
  const next: EmailMessage = { ...current, ...definedUpdates, id: current.id }
  // Keep IMPORTANT label in sync with isImportant flag updates
  if (typeof definedUpdates.isImportant === "boolean") {
    const labelsSet = new Set<string>(Array.isArray(next.labelIds) ? next.labelIds : [])
    if (definedUpdates.isImportant) labelsSet.add("IMPORTANT")
    else labelsSet.delete("IMPORTANT")
    next.labelIds = Array.from(labelsSet)
  }
  // Keep STARRED label in sync with isStarred flag updates
  if (typeof definedUpdates.isStarred === "boolean") {
    const labelsSet = new Set<string>(Array.isArray(next.labelIds) ? next.labelIds : [])
    if (definedUpdates.isStarred) labelsSet.add("STARRED")
    else labelsSet.delete("STARRED")
    next.labelIds = Array.from(labelsSet)
  }
  state.messages[idx] = next
  // If this email is part of a thread and subject changed to empty, keep thread subject
  if (next.threadId) {
    const t = state.threads.find((th) => th.id === next.threadId)
    if (t) {
      t.lastActivity = nowDate().toISOString()
      if (typeof updates.isStarred === "boolean") {
        // if any message is starred inside the thread, consider thread starred
        const anyStarred = t.messageIds.some((mid) => state.messages.find((m) => m.id === mid)?.isStarred)
        t.isStarred = anyStarred
      }
    }
  }
  return state.messages[idx]
}

export function moveEmailToSystemFolder(id: string, folder: "inbox" | "sent" | "drafts" | "trash" | "archive" | "spam"): EmailMessage | undefined {
  const email = getEmailById(id)
  if (!email) return undefined
  let labels = new Set(email.labelIds)
  const INBOX = "INBOX"
  const TRASH = "TRASH"
  const ARCHIVE = "ARCHIVE"
  const SPAM = "SPAM"
  const SENT = "SENT"
  const DRAFTS = "DRAFTS"
  switch (folder) {
    case "archive":
      labels.delete(INBOX)
      labels.delete(TRASH)
      break
    case "trash":
      // When moving to trash, remove INBOX but retain all other labels; add TRASH
      labels.delete(INBOX)
      labels.add(TRASH)
      break
    case "inbox":
      labels.delete(TRASH)
      labels.delete(ARCHIVE)
      labels.delete(SPAM)
      labels.add(INBOX)
      break
    case "spam":
      labels.delete(INBOX)
      labels.add(SPAM)
      break
    case "sent":
      labels.add(SENT)
      break
    case "drafts":
      labels.add(DRAFTS)
      break
  }
  return updateEmail(id, { labelIds: Array.from(labels) })
}

export function moveThreadToSystemFolder(
  threadId: string,
  folder: "inbox" | "sent" | "drafts" | "trash" | "archive" | "spam",
): Array<EmailMessage | undefined> {
  const thread = getThread(threadId)
  if (!thread) return []
  const INBOX = "INBOX"
  const TRASH = "TRASH"
  const ARCHIVE = "ARCHIVE"
  const SPAM = "SPAM"
  const SENT = "SENT"
  const DRAFTS = "DRAFTS"
  const updated: Array<EmailMessage | undefined> = []
  for (const m of thread.messages) {
    const labels = new Set(m.labelIds)
    switch (folder) {
      case "archive":
        labels.delete(INBOX)
        labels.delete(TRASH)
        break
      case "trash":
        // When moving to trash, remove INBOX but retain all other labels; add TRASH
        labels.delete(INBOX)
        labels.add(TRASH)
        break
      case "inbox":
        labels.delete(TRASH)
        labels.delete(ARCHIVE)
        labels.delete(SPAM)
        labels.add(INBOX)
        break
      case "spam":
        labels.delete(INBOX)
        labels.add(SPAM)
        break
      case "sent":
        labels.add(SENT)
        break
      case "drafts":
        labels.add(DRAFTS)
        break
    }
    updated.push(updateEmail(m.id, { labelIds: Array.from(labels) }))
  }
  return updated
}

export function addLabelToEmail(id: string, label: string): EmailMessage | undefined {
  const email = getEmailById(id)
  if (!email) return undefined
  const labels = Array.from(new Set([...(email.labelIds ?? []), label]))
  const isStar = label.trim().toUpperCase() === "STARRED"
  const isImp = label.trim().toUpperCase() === "IMPORTANT"
  return updateEmail(id, { labelIds: labels, isStarred: isStar ? true : undefined, isImportant: isImp ? true : undefined })
}

export function addLabelToThread(threadId: string, label: string): Array<EmailMessage | undefined> {
  const thread = getThread(threadId)
  if (!thread) return []
  const updates: Array<EmailMessage | undefined> = []
  for (const m of thread.messages) {
    const labels = Array.from(new Set([...(m.labelIds ?? []), label]))
    const isStar = label.trim().toUpperCase() === "STARRED"
    const isImp = label.trim().toUpperCase() === "IMPORTANT"
    updates.push(updateEmail(m.id, { labelIds: labels, isStarred: isStar ? true : undefined, isImportant: isImp ? true : undefined }))
  }
  return updates
}

export function removeLabelFromEmail(id: string, label: string): EmailMessage | undefined {
  const email = getEmailById(id)
  if (!email) return undefined
  const labels = (email.labelIds ?? []).filter((l) => l.toLowerCase() !== label.toLowerCase())
  const isStar = label.trim().toUpperCase() === "STARRED"
  const isImp = label.trim().toUpperCase() === "IMPORTANT"
  return updateEmail(id, { labelIds: labels, isStarred: isStar ? false : undefined, isImportant: isImp ? false : undefined })
}

export function removeLabelFromThread(threadId: string, label: string): Array<EmailMessage | undefined> {
  const thread = getThread(threadId)
  if (!thread) return []
  const updates: Array<EmailMessage | undefined> = []
  for (const m of thread.messages) {
    const labels = (m.labelIds ?? []).filter((l) => l.toLowerCase() !== label.toLowerCase())
    const isStar = label.trim().toUpperCase() === "STARRED"
    const isImp = label.trim().toUpperCase() === "IMPORTANT"
    updates.push(updateEmail(m.id, { labelIds: labels, isStarred: isStar ? false : undefined, isImportant: isImp ? false : undefined }))
  }
  return updates
}

// Determine if any recipient matches the current user's email
function recipientsIncludeMe(to?: string[], cc?: string[], bcc?: string[]): boolean {
  const me = (state.settings?.email || "you@example.com").toLowerCase()
  if (!me) return false
  const check = (list?: string[]) => Array.isArray(list) && list.some((s) => extractEmailAddress(s) === me)
  return check(to) || check(cc) || check(bcc)
}

export function composeEmail(data: {
  to: string[]
  cc?: string[]
  bcc?: string[]
  subject: string
  text: string
  html?: string
  attachments?: Attachment[]
  parentThreadId?: string
}): { message: EmailMessage; thread: EmailThread } {
  const now = nowDate().toISOString()
  const newThreadId = nanoid(8)
  const meName = (state.settings?.displayName || "You").trim() || "You"
  const meEmail = (state.settings?.email || "you@example.com").trim() || "you@example.com"
  const message: EmailMessage = {
    id: nanoid(8),
    threadId: newThreadId,
    replyToId: undefined,
    from: `${meName} <${meEmail}>`,
    to: data.to,
    cc: data.cc,
    bcc: data.bcc,
    subject: data.subject,
    date: now,
    text: data.text,
    html: typeof data.html === "string" ? data.html : undefined,
    isRead: true,
    isStarred: false,
    isImportant: false,
    labelIds: ["SENT"],
    attachments: data.attachments ?? [],
    snoozeUntil: null,
  }

  // If sending to yourself, also place the message in INBOX
  if (recipientsIncludeMe(data.to, data.cc, data.bcc)) {
    message.labelIds = Array.from(new Set([...(message.labelIds ?? []), "INBOX"]))
  }

  // Participants are tracked as unique email addresses for stable thread identity
  const participants = Array.from(
    new Set([
      extractEmailAddress(`${meName} <${meEmail}>`) || meEmail,
      ...data.to.map((t) => extractEmailAddress(t) || t),
    ].filter(Boolean)),
  ).slice(0, 5)

  const thread: EmailThread = {
    id: newThreadId,
    subject: data.subject,
    participants,
    messageIds: [message.id],
    lastActivity: now,
    isStarred: false,
    parentThreadId: data.parentThreadId ?? newThreadId,
  }

  state.messages.push(message)
  state.threads.push(thread)
  return { message, thread }
}

export function replyToThread(
  threadId: string,
  data: { body: string; html?: string; to?: string[]; cc?: string[]; bcc?: string[]; replyToId?: string },
): { message: EmailMessage; thread: EmailThread } | undefined {
  let thread = state.threads.find((t) => t.id === threadId)
  if (!thread) {
    // If a persisted thread record does not exist (e.g., replying from a single message view),
    // synthesize it from existing messages and persist it before replying.
    const synthesized = getThread(threadId)
    if (!synthesized) return undefined
    const participants = Array.isArray(synthesized.participants) ? synthesized.participants.slice(0, 5) : []
    const newThread: EmailThread = {
      id: synthesized.id,
      subject: synthesized.subject,
      participants,
      messageIds: synthesized.messages.map((m) => m.id),
      lastActivity: synthesized.lastActivity,
      isStarred: synthesized.isStarred,
      parentThreadId: synthesized.id,
    }
    state.threads.push(newThread)
    thread = newThread
  }
  const now = nowDate().toISOString()
  const parentId = (typeof data.replyToId === "string" && data.replyToId.length > 0)
    ? data.replyToId
    : thread.messageIds[thread.messageIds.length - 1]
  const meName = (state.settings?.displayName || "You").trim() || "You"
  const meEmail = (state.settings?.email || "you@example.com").trim() || "you@example.com"
  const ensureReplyPrefix = (s: string): string => {
    const subj = (s || "").trim()
    return /^re\s*:/i.test(subj) ? subj : `Re: ${subj}`
  }
  const message: EmailMessage = {
    id: nanoid(8),
    threadId: threadId,
    replyToId: parentId,
    from: `${meName} <${meEmail}>`,
    to: data.to ?? [],
    cc: data.cc,
    bcc: data.bcc,
    subject: ensureReplyPrefix(thread.subject),
    date: now,
    text: data.body,
    html: typeof data.html === "string" ? data.html : undefined,
    isRead: true,
    isStarred: false,
    isImportant: false,
    labelIds: ["SENT"],
    attachments: [],
    snoozeUntil: null,
  }
  // If replying to yourself (recipient includes me), also place the message in INBOX
  if (recipientsIncludeMe(message.to, message.cc, message.bcc)) {
    message.labelIds = Array.from(new Set([...(message.labelIds ?? []), "INBOX"]))
  }
  // Inherit user-defined thread labels onto the new reply so labels persist across new messages
  try {
    const userLabelIds = new Set(state.labels.filter((l) => l.type === "USER").map((l) => l.id))
    const threadUserLabels = new Set<string>()
    for (const mid of thread.messageIds) {
      const mm = state.messages.find((m) => m.id === mid)
      if (!mm || !Array.isArray(mm.labelIds)) continue
      for (const lid of mm.labelIds) if (userLabelIds.has(lid)) threadUserLabels.add(lid)
    }
    if (threadUserLabels.size > 0) {
      const merged = new Set<string>(message.labelIds)
      for (const lid of threadUserLabels) merged.add(lid)
      message.labelIds = Array.from(merged)
    }
  } catch {}
  // If this thread contains any received messages, ensure this new reply also carries the ALL label
  const threadHasReceived = thread.messageIds.some((mid) => {
    const mm = state.messages.find((m) => m.id === mid)
    return mm ? (typeof mm.from === "string" && !isFromMeAddress(mm.from)) : false
  })
  if (threadHasReceived) {
    message.labelIds = Array.from(new Set([...(message.labelIds ?? []), "ALL"]))
  }
  state.messages.push(message)
  thread.messageIds.push(message.id)
  thread.lastActivity = now
  // Do not modify thread.participants here; preserve existing participants list
  return { message, thread }
}

export function getThread(threadId: string): (EmailThread & { messages: EmailMessage[] }) | undefined {
  const thread = state.threads.find((t) => t.id === threadId)
  if (!thread) {
    // Synthesize a thread from messages if no thread record exists
    const messages = state.messages
      .filter((m) => !m.isDraftDeleted && m.threadId === threadId)
      .slice()
      .sort((a, b) => (a.date === b.date ? (a.id < b.id ? -1 : a.id > b.id ? 1 : 0) : a.date < b.date ? -1 : 1))
    if (messages.length === 0) return undefined

    const lastActivity = messages[messages.length - 1]?.date ?? nowDate().toISOString()
    // Prefer the latest message's subject when present; fall back to the most recent non-empty subject
    const lastSubject = (messages[messages.length - 1]?.subject ?? "").trim()
    const subjectCandidate =
      lastSubject.length > 0
        ? lastSubject
        : [...messages]
            .reverse()
            .find((m) => (m.subject ?? "").trim().length > 0)?.subject ?? ""
    // Participants are unique email addresses derived from from/to fields
    const participantsSet = new Set<string>()
    for (const m of messages) {
      const fromAddr = extractEmailAddress(m.from)
      if (fromAddr) participantsSet.add(fromAddr)
      for (const t of m.to) {
        const toAddr = extractEmailAddress(t)
        if (toAddr) participantsSet.add(toAddr)
      }
    }
    const isStarred = messages.some((m) => m.isStarred)
    const synthesized: EmailThread & { messages: EmailMessage[] } = {
      id: threadId,
      subject: subjectCandidate,
      participants: Array.from(participantsSet).slice(0, 5),
      messageIds: messages.map((m) => m.id),
      lastActivity,
      isStarred,
      messages,
    }
    return synthesized
  }
  const messages = thread.messageIds
    .map((mid) => state.messages.find((m) => m.id === mid))
    .filter((m): m is EmailMessage => Boolean(m))
    .filter((m) => !m.isDraftDeleted)
    .sort((a, b) => (a.date === b.date ? (a.id < b.id ? -1 : a.id > b.id ? 1 : 0) : a.date < b.date ? -1 : 1))
  if (messages.length === 0) return undefined
  // Compute effective subject from latest message to keep list and thread views consistent
  const lastSubject = (messages[messages.length - 1]?.subject ?? "").trim()
  const effectiveSubject =
    lastSubject.length > 0
      ? lastSubject
      : [...messages]
          .reverse()
          .find((m) => (m.subject ?? "").trim().length > 0)?.subject ?? thread.subject
  // Ensure persisted thread participants are normalized to emails as well
  const participantsSet = new Set<string>(
    messages.flatMap((m) => {
      const res: string[] = []
      const fa = extractEmailAddress(m.from)
      if (fa) res.push(fa)
      for (const t of m.to) {
        const ta = extractEmailAddress(t)
        if (ta) res.push(ta)
      }
      return res
    }),
  )
  return { ...thread, subject: effectiveSubject, messages }
}

export function listThreads(): Array<EmailThread & { messageCount: number }> {
  return state.threads
    .slice()
    .sort((a, b) =>
      a.lastActivity === b.lastActivity
        ? a.id < b.id
          ? 1
          : a.id > b.id
          ? -1
          : 0
        : a.lastActivity < b.lastActivity
        ? 1
        : -1,
    )
    .map((t) => ({ ...t, messageCount: t.messageIds.length }))
}

export function updateThread(
  threadId: string,
  updates: Partial<Pick<EmailThread, "isStarred" | "subject">>,
): EmailThread | undefined {
  const idx = state.threads.findIndex((t) => t.id === threadId)
  if (idx === -1) return undefined
  const current = state.threads[idx]
  const next: EmailThread = { ...current, ...updates, id: current.id }
  state.threads[idx] = next
  if (typeof updates.isStarred === "boolean") {
    // New semantics:
    // - When turning ON from a thread/list item, star ONLY the most recent message in the thread
    // - When turning OFF from a thread/list item, remove star from ALL messages in the thread
    const messageIds = current.messageIds.slice()
    if (updates.isStarred) {
      const lastId = messageIds[messageIds.length - 1]
      if (lastId) updateEmail(lastId, { isStarred: true })
    } else {
      for (const mid of messageIds) updateEmail(mid, { isStarred: false })
    }
    // Reflect aggregate thread starred state based on any message starred
    const anyStarred = messageIds.some((mid) => state.messages.find((m) => m.id === mid)?.isStarred)
    next.isStarred = anyStarred
    state.threads[idx] = next
  }
  return next
}

// Label normalization and colors
const DEFAULT_LABEL_COLORS: Record<string, string> = {
  work: "#1E88E5", // blue
  personal: "#10B981", // green
  important: "#F59E0B", // amber
  travel: "#8B5CF6", // purple
  receipts: "#F97316", // orange
}

function getDefaultLabelColor(id: string, name?: string): string {
  const key = (id || name || "").toLowerCase()
  if (DEFAULT_LABEL_COLORS[key]) return DEFAULT_LABEL_COLORS[key]
  const palette = [
    "#1E88E5",
    "#10B981",
    "#F59E0B",
    "#8B5CF6",
    "#F97316",
    "#EF4444",
    "#EC4899",
    "#06B6D4",
    "#84CC16",
    "#A855F7",
  ]
  let hash = 0
  for (let i = 0; i < key.length; i++) {
    hash = ((hash << 5) - hash + key.charCodeAt(i)) | 0
  }
  const idx = Math.abs(hash) % palette.length
  return palette[idx]
}

function sanitizeContacts(raw: unknown): ContactsDirectory {
  const out: ContactsDirectory = {}
  if (!raw || typeof raw !== "object") return out
  try {
    const entries = Object.entries(raw as Record<string, any>)
    for (const [key, value] of entries) {
      if (Object.keys(out).length >= 1000) break
      const candidateEmail = (typeof (value?.email) === "string" && value.email) || (typeof key === "string" && key) || ""
      const email = candidateEmail.trim().toLowerCase()
      if (!email || !email.includes("@")) continue
      const name = typeof value?.name === "string" && value.name.trim().length > 0 ? value.name.trim() : undefined
      out[email] = { email, ...(name ? { name } : {}) }
    }
  } catch {}
  return out
}

function normalizeLabels(labels: Label[]): Label[] {
  const byId = new Map<string, Label>()
  for (const l of labels) {
    const id = String(l.id)
    const name = String(l.name)
    const type: "SYSTEM" | "USER" = l.type === "USER" ? "USER" : "SYSTEM"
    let color = typeof l.color === "string" ? l.color : undefined
    if (type === "USER" && (!color || color.trim().length === 0)) {
      color = getDefaultLabelColor(id, name)
    }
    if (!byId.has(id)) byId.set(id, { id, name, type, color })
  }
  return Array.from(byId.values())
}

// Labels and Settings
export function listLabels(): Label[] {
  const normalized = normalizeLabels(state.labels)
  state.labels = normalized
  return normalized
}

export function setLabels(labels: Label[]): Label[] {
  state.labels = normalizeLabels(labels)
  return state.labels
}

export function getSettings(): Settings {
  return state.settings
}

export function updateSettings(partial: Partial<Settings>): Settings {
  state.settings = { ...state.settings, ...partial }
  return state.settings
}

export function getUnreadCounts(): UnreadCounts {
  const userLabelIds = new Set(state.labels.filter((l) => l.type === "USER").map((l) => l.id))
  const counts: UnreadCounts = {
    system: {
      inbox: 0,
      starred: 0,
      important: 0,
      snoozed: 0,
      sent: 0,
      drafts: 0,
      spam: 0,
      trash: 0,
      archive: 0,
      all: 0,
    },
    labels: {},
  }

  const now = nowTs()
  for (const m of state.messages) {
    if (m.isDraftDeleted) continue
    const unread = !m.isRead
    const labels = Array.isArray(m.labelIds) ? m.labelIds : []
    const has = (x: string) => labels.map((l) => l.toUpperCase()).includes(x)
    if (!unread) continue
    const inTrash = has("TRASH")
    const inSpam = has("SPAM")
    if (has("INBOX")) counts.system.inbox += 1
    // Exclude TRASH/SPAM from starred and important sidebar counts
    if (!inTrash && !inSpam && m.isStarred) counts.system.starred += 1
    if (!inTrash && !inSpam && (m.isImportant || has("IMPORTANT"))) counts.system.important += 1
    // Exclude TRASH/SPAM from Sent unread count to match list view
    if (!inTrash && !inSpam && has("SENT")) counts.system.sent += 1
    if (has("DRAFTS")) counts.system.drafts += 1
    if (has("SPAM")) counts.system.spam += 1
    if (has("TRASH")) counts.system.trash += 1
    if (!has("INBOX") && !has("TRASH") && !has("SPAM")) counts.system.archive += 1
    // All Mail: unread messages that are part of received threads (marked with ALL) and not in TRASH/SPAM
    if (has("ALL") && !has("TRASH") && !has("SPAM")) counts.system.all += 1
    if (m.snoozeUntil && Date.parse(m.snoozeUntil) > now) counts.system.snoozed += 1
    // Label counts (exclude TRASH and SPAM)
    if (!has("TRASH") && !has("SPAM")) {
      for (const l of labels) {
        if (userLabelIds.has(l)) {
          counts.labels[l] = (counts.labels[l] ?? 0) + 1
        }
      }
    }
  }
  return counts
}

// Snooze helpers
export function listSnoozed(): EmailMessage[] {
  const now = nowTs()
  return state.messages.filter((e) => !e.isDraftDeleted && e.snoozeUntil && Date.parse(e.snoozeUntil) > now)
}

export function snoozeEmail(id: string, untilISO: string | null): EmailMessage | undefined {
  const email = getEmailById(id)
  if (!email) return undefined
  // Snooze the entire thread: set snoozeUntil on all messages in the same thread
  // and remove INBOX label while preserving all other labels/flags
  const threadId = email.threadId || email.id
  for (const m of state.messages) {
    if (m.threadId !== threadId) continue
    const labels = Array.isArray(m.labelIds) ? m.labelIds : []
    const withoutInbox = labels.filter((l) => l.toUpperCase() !== "INBOX")
    updateEmail(m.id, { snoozeUntil: untilISO, labelIds: withoutInbox })
  }
  // Return the specifically targeted message's updated record
  const updated = getEmailById(id)
  return updated
}

// Utilities
function folderToSystemLabel(folder: "inbox" | "sent" | "drafts" | "trash" | "archive" | "spam"): string {
  switch (folder) {
    case "inbox":
      return "INBOX"
    case "sent":
      return "SENT"
    case "drafts":
      return "DRAFTS"
    case "trash":
      return "TRASH"
    case "archive":
      return "ARCHIVE"
    case "spam":
      return "SPAM"
  }
}

// Draft helpers
export function createDraft(
  data?: Partial<
    Pick<EmailMessage, "to" | "cc" | "bcc" | "subject" | "text" | "html" | "attachments"> & { parentThreadId?: string }
  >,
): EmailMessage {
  const now = nowDate().toISOString()
  const parentThreadId = (data as any)?.parentThreadId
  const threadId = typeof parentThreadId === "string" && parentThreadId.length > 0 ? parentThreadId : nanoid(8)
  const meName = (state.settings?.displayName || "You").trim() || "You"
  const meEmail = (state.settings?.email || "you@example.com").trim() || "you@example.com"
  const msg: EmailMessage = {
    id: nanoid(8),
    threadId: threadId,
    from: `${meName} <${meEmail}>`,
    to: data?.to ?? [],
    cc: data?.cc,
    bcc: data?.bcc,
    subject: data?.subject ?? "",
    text: data?.text ?? "",
    html: typeof data?.html === "string" ? data?.html : undefined,
    date: now,
    isRead: true,
    isStarred: false,
    isImportant: false,
    labelIds: ["DRAFTS"],
    attachments: data?.attachments ?? [],
    snoozeUntil: null,
    isDraftDeleted: false,
  }
  // If this draft belongs to an existing thread, inherit any user labels from that thread
  try {
    if (typeof parentThreadId === "string" && parentThreadId.length > 0) {
      const userLabelIds = new Set(state.labels.filter((l) => l.type === "USER").map((l) => l.id))
      const threadUserLabels = new Set<string>()
      for (const m of state.messages) {
        if (m.threadId !== threadId || !Array.isArray(m.labelIds)) continue
        for (const lid of m.labelIds) if (userLabelIds.has(lid)) threadUserLabels.add(lid)
      }
      if (threadUserLabels.size > 0) {
        const merged = new Set<string>(msg.labelIds)
        for (const lid of threadUserLabels) merged.add(lid)
        msg.labelIds = Array.from(merged)
      }
    }
  } catch {}
  state.messages.push(msg)
  // If creating a draft within an existing thread, attach to that thread
  if (typeof parentThreadId === "string" && parentThreadId.length > 0) {
    let t = state.threads.find((th) => th.id === threadId)
    if (!t) {
      // Synthesize thread from existing messages and persist
      const synthesized = getThread(threadId)
      if (synthesized) {
        t = {
          id: synthesized.id,
          subject: synthesized.subject,
          participants: synthesized.participants.slice(0, 5),
          messageIds: synthesized.messages.map((m) => m.id),
          lastActivity: synthesized.lastActivity,
          isStarred: synthesized.isStarred,
          parentThreadId: synthesized.id,
        }
        state.threads.push(t)
      }
    }
    if (t) {
      if (!t.messageIds.includes(msg.id)) t.messageIds.push(msg.id)
      t.lastActivity = now
    }
  } else {
    // Otherwise persist a new thread record for this new draft thread
    const participants = [extractEmailAddress(`${meName} <${meEmail}>`) || meEmail]
    state.threads.push({
      id: threadId,
      subject: msg.subject,
      participants,
      messageIds: [msg.id],
      lastActivity: now,
      isStarred: false,
      parentThreadId: threadId,
    })
  }
  return msg
}

// Identity helpers for All Mail detection
function extractEmailAddress(from: string | undefined): string {
  if (typeof from !== "string" || from.length === 0) return ""
  const match = from.match(/<([^>]+)>/)
  if (match && match[1]) return match[1].trim().toLowerCase()
  const raw = from.trim().toLowerCase()
  return raw.includes("@") ? raw : ""
}

function isFromMeAddress(from: string | undefined): boolean {
  const me = (state.settings?.email || "you@example.com").toLowerCase()
  if (!me) return false
  const addr = extractEmailAddress(from)
  return addr === me
}

function normalizeParticipantToEmail(value: unknown): string | null {
  const s = typeof value === "string" ? value.trim() : ""
  if (!s) return null
  const addr = extractEmailAddress(s)
  if (addr) return addr
  if (s.includes("@")) return s.toLowerCase()
  return null
}

function normalizeThreadRecord(thread: any): EmailThread {
  const id = String(thread?.id || "")
  const subject = typeof thread?.subject === "string" ? thread.subject : ""
  const rawParticipants: any[] = Array.isArray(thread?.participants) ? thread.participants : []
  const emails = new Set<string>()
  for (const p of rawParticipants) {
    const addr = normalizeParticipantToEmail(p)
    if (addr) emails.add(addr)
  }
  const messageIds: string[] = Array.isArray(thread?.messageIds) ? thread.messageIds.filter((x: any) => typeof x === "string") : []
  const lastActivity = typeof thread?.lastActivity === "string" ? thread.lastActivity : nowDate().toISOString()
  const isStarred = Boolean(thread?.isStarred)
  const parentThreadId = typeof thread?.parentThreadId === "string" && thread.parentThreadId.length > 0 ? thread.parentThreadId : id
  return {
    id,
    subject,
    participants: Array.from(emails).slice(0, 5),
    messageIds,
    lastActivity,
    isStarred,
    parentThreadId,
  }
}

function recomputeThreadParticipants(threadId: string): void {
  const t = state.threads.find((th) => th.id === threadId)
  if (!t) return
  const emails = new Set<string>()
  // Collect from all messages in the thread
  for (const m of state.messages) {
    if (m.threadId !== threadId || m.isDraftDeleted) continue
    const fa = extractEmailAddress(m.from)
    if (fa) emails.add(fa)
    for (const to of m.to || []) {
      const ta = extractEmailAddress(to)
      if (ta) emails.add(ta)
    }
  }
  t.participants = Array.from(emails).slice(0, 5)
}

function normalizeAllThreadsParticipants(): void {
  const threadIds = state.threads.map((t) => t.id)
  for (const tid of threadIds) recomputeThreadParticipants(tid)
}

export function softDeleteEmail(id: string): EmailMessage | undefined {
  const idx = state.messages.findIndex((e) => e.id === id)
  if (idx === -1) return undefined
  const current = state.messages[idx]
  const next: EmailMessage = { ...current, isDraftDeleted: true }
  state.messages[idx] = next
  return next
}

export function sendDraft(
  id: string,
  fields: { to: string[]; cc?: string[]; bcc?: string[]; subject: string; text: string; html?: string },
): { message: EmailMessage; thread?: EmailThread } | undefined {
  const idx = state.messages.findIndex((e) => e.id === id)
  if (idx === -1) return undefined
  const current = state.messages[idx]
  if (!Array.isArray(current.labelIds) || !current.labelIds.includes("DRAFTS")) return undefined
  const now = nowDate().toISOString()
  // Update fields and convert labels
  const nextLabels = new Set(current.labelIds.filter((l) => l !== "DRAFTS" && l !== "TRASH"))
  nextLabels.add("SENT")
  // If sending to yourself, also place the message in INBOX
  if (recipientsIncludeMe(fields.to, fields.cc, fields.bcc)) {
    nextLabels.add("INBOX")
  }
  const updated: EmailMessage = {
    ...current,
    to: Array.isArray(fields.to) ? fields.to : [],
    cc: Array.isArray(fields.cc) ? fields.cc : undefined,
    bcc: Array.isArray(fields.bcc) ? fields.bcc : undefined,
    subject: fields.subject ?? current.subject,
    text: fields.text ?? current.text,
    html: typeof fields.html === "string" ? fields.html : current.html,
    date: now,
    labelIds: Array.from(nextLabels),
    isRead: true,
  }
  state.messages[idx] = updated
  // Update thread lastActivity and participants
  if (updated.threadId) {
    const t = state.threads.find((th) => th.id === updated.threadId)
    if (t) {
      t.lastActivity = now
      if (!t.messageIds.includes(updated.id)) t.messageIds.push(updated.id)
      return { message: updated, thread: t }
    }
  }
  return { message: updated }
}
