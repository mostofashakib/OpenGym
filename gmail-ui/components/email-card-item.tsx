"use client"

import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { LabelChips } from "@/components/label-chips"
import { Star, Archive, Trash2, MailOpen, Mail, Clock, Sparkles, Box, Trash } from "lucide-react"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { useRandomization } from "@/lib/randomization-context"
import { nowDate, snoozeLaterTodayISO, snoozeNextWeekISO, snoozeThisWeekendISO, snoozeTomorrowISO, buildFixedZonedISOFromInputs } from "@/lib/clock"

interface Email {
  id: string
  sender: string
  subject: string
  preview: string
  time: string
  isRead: boolean
  isStarred: boolean
  isImportant: boolean
  hasAttachment?: boolean
  labels?: string[]
  threadId?: string
  messageCount?: number
  participants?: string[]
  hasDraft?: boolean
  snoozeUntil?: string | null
}

interface EmailCardItemProps {
  email: Email
  selected: boolean
  onEmailSelect: (emailId: string) => void
  onEmailStar: (emailId: string) => void
  onEmailToggleImportant?: (emailId: string) => void
  onThreadClick?: (threadId: string) => void
  showInboxLabelChip?: boolean
  labelMetaById?: Record<string, { id: string; name: string; type: "SYSTEM" | "USER"; color?: string }>
  onEmailArchive?: (emailId: string) => void
  onEmailDelete?: (emailId: string) => void
  onEmailToggleRead?: (emailId: string, threadId?: string) => void
  onEmailSnooze?: (emailId: string, untilISO: string) => void
  inTrashView?: boolean
}

export function EmailCardItem({
  email,
  selected,
  onEmailSelect,
  onEmailStar,
  onEmailToggleImportant,
  onThreadClick,
  showInboxLabelChip,
  labelMetaById,
  onEmailArchive,
  onEmailDelete,
  onEmailToggleRead,
  onEmailSnooze,
  inTrashView,
}: EmailCardItemProps) {
  const rnd = useRandomization()
  const threadIcons = (rnd?.threadIcons || {}) as { star?: string; archive?: string; trash?: string }

  const formatSnoozeUntil = (iso?: string | null) => {
    if (!iso) return ""
    try {
      const d = new Date(iso)
      const now = nowDate()
      const isToday =
        d.getFullYear() === now.getFullYear() && d.getMonth() === now.getMonth() && d.getDate() === now.getDate()
      const isTomorrow = (() => {
        const t = new Date(now)
        t.setDate(now.getDate() + 1)
        return d.getFullYear() === t.getFullYear() && d.getMonth() === t.getMonth() && d.getDate() === t.getDate()
      })()
      if (isToday) return `Today ${d.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}`
      if (isTomorrow) return `Tomorrow ${d.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}`
      return d.toLocaleString([], { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" })
    } catch {
      return ""
    }
  }
  const getInitials = (name: string) => {
    return (name || "")
      .split(" ")
      .filter(Boolean)
      .slice(0, 2)
      .map((n) => n[0]?.toUpperCase() || "")
      .join("") || "?"
  }

  return (
    <div
      className={`relative border rounded-lg p-3 hover:shadow-sm transition cursor-pointer ${selected ? "ring-1 ring-blue-500" : ""}`}
      onClick={() => (onThreadClick ? onThreadClick(email.id) : onEmailSelect(email.id))}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <input
            type="checkbox"
            className="mr-1 rounded border-gray-300  focus:ring-blue-500 focus:ring-1 transition-colors"
            checked={selected}
            onClick={(e) => e.stopPropagation()}
            onChange={(e) => {
              e.stopPropagation()
              onEmailSelect(email.id)
            }}
          />
          <Avatar className="h-8 w-8">
            <AvatarFallback className="text-xs">{getInitials(email.sender)}</AvatarFallback>
          </Avatar>
          <div className="min-w-0">
            <div className={`text-sm truncate ${!email.isRead ? "font-semibold" : "font-normal"}`}>
              {!email.isRead && (
                <span className="inline-block w-2 h-2 bg-red-500 rounded-full mr-2 align-[-1px]" aria-label="Unread" />
              )}
              {email.sender}
              {typeof email.messageCount === "number" && email.messageCount > 0 && (
                <span className={`ml-2 text-xs`}>{email.messageCount}</span>
              )}
            </div>
            <div className="text-xs text-gray-600 truncate">
              {email.snoozeUntil ? (
                <>
                  <Clock className="inline-block h-3.5 w-3.5 align-[-2px] mr-1" />
                  {formatSnoozeUntil(email.snoozeUntil)}
                </>
              ) : (
                email.time
              )}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-1 flex-shrink-0">
          {!inTrashView && (
            <button
              className={`p-1 rounded ${email.isStarred ? "text-yellow-500" : "text-gray-400 hover:text-yellow-500"}`}
              onClick={(e) => {
                e.stopPropagation()
                onEmailStar(email.id)
              }}
              aria-label={email.isStarred ? "Unstar" : "Star"}
              title={email.isStarred ? "Unstar" : "Star"}
            >
              {threadIcons.star === "sparkles" ? (
                <Sparkles className={`h-4 w-4 ${email.isStarred ? "scale-110" : ""}`} />
              ) : (
                <Star className="h-4 w-4" fill={email.isStarred ? "currentColor" : "none"} />
              )}
            </button>
          )}
          <button
            className={`p-1 rounded ${email.isImportant ? "text-yellow-500" : "text-gray-400 hover:text-yellow-500"}`}
            onClick={(e) => {
              e.stopPropagation()
              onEmailToggleImportant?.(email.id)
            }}
            aria-label={email.isImportant ? "Marked important" : "Mark as important"}
            title={email.isImportant ? "Marked important" : "Mark as important"}
          >
            <svg
              className={`h-4 w-4 ${email.isImportant ? "scale-110" : ""}`}
              viewBox="0 0 16 16"
              aria-hidden="true"
              focusable="false"
            >
              <path
                d="M2.25 3.25h7.1l4.4 4.75-4.4 4.75h-7.1c-.69 0-1.25-.56-1.25-1.25V4.5c0-.69.56-1.25 1.25-1.25z"
                fill={email.isImportant ? "currentColor" : "none"}
                stroke={"currentColor"}
                strokeWidth="1"
                strokeLinejoin="round"
              />
            </svg>
          </button>
          <button
            className="p-1 rounded text-gray-400 hover:text-gray-700"
            onClick={(e) => {
              e.stopPropagation()
              onEmailArchive?.(email.id)
            }}
            aria-label="Archive"
            title="Archive"
          >
            {threadIcons.archive === "box" ? <Box className="h-4 w-4" /> : <Archive className="h-4 w-4" />}
          </button>
          <button
            className="p-1 rounded text-gray-400 hover:text-red-600"
            onClick={(e) => {
              e.stopPropagation()
              onEmailDelete?.(email.id)
            }}
            aria-label="Delete"
            title="Delete"
          >
            {threadIcons.trash === "trash" ? <Trash className="h-4 w-4" /> : <Trash2 className="h-4 w-4" />}
          </button>
          <button
            className="p-1 rounded text-gray-400 hover:text-gray-700"
            onClick={(e) => {
              e.stopPropagation()
              onEmailToggleRead?.(email.id, email.threadId)
            }}
            aria-label={email.isRead ? "Mark as unread" : "Mark as read"}
            title={email.isRead ? "Mark as unread" : "Mark as read"}
          >
            {!email.isRead ? <MailOpen className="h-4 w-4" /> : <Mail className="h-4 w-4" />}
          </button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                className="p-1 rounded text-gray-400 hover:text-gray-700"
                onClick={(e) => {
                  e.stopPropagation()
                }}
                aria-label="Snooze"
                title="Snooze"
              >
                <Clock className="h-4 w-4" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>Snooze</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={(e) => {
                  e.stopPropagation()
                  onEmailSnooze?.(email.id, snoozeLaterTodayISO())
                }}
              >
                Later today
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={(e) => {
                  e.stopPropagation()
                  onEmailSnooze?.(email.id, snoozeTomorrowISO())
                }}
              >
                Tomorrow
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={(e) => {
                  e.stopPropagation()
                  onEmailSnooze?.(email.id, snoozeThisWeekendISO())
                }}
              >
                This weekend
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={(e) => {
                  e.stopPropagation()
                  onEmailSnooze?.(email.id, snoozeNextWeekISO())
                }}
              >
                Next week
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={(e) => {
                  e.stopPropagation()
                  const input = window.prompt("Pick date/time (YYYY-MM-DD HH:MM, 24h)", "")
                  if (!input) return
                  const [datePart, timePart] = input.split(" ")
                  if (!datePart || !timePart) return
                  const iso = buildFixedZonedISOFromInputs(datePart, timePart)
                  onEmailSnooze?.(email.id, iso)
                }}
              >
                Pick date & time…
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
      <div className="mt-2">
        <div className={`text-sm truncate ${!email.isRead ? "font-semibold" : "font-normal"}`}>{email.subject}</div>
        <div className="flex items-center gap-2 mt-1">
          {(email.hasDraft || (Array.isArray(email.labels) && email.labels.map((l) => l.toUpperCase()).includes("DRAFTS"))) && (
            <Badge
              variant="secondary"
              className="text-xs bg-red-100 text-red-700 border border-red-200"
              title="Draft exists in this thread"
            >
              Draft
            </Badge>
          )}
          {email.hasAttachment && (
            <div className="text-gray-400">
              <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M8 4a3 3 0 00-3 3v4a5 5 0 0010 0V7a1 1 0 112 0v4a7 7 0 11-14 0V7a5 5 0 0110 0v4a3 3 0 11-6 0V7a1 1 0 012 0v4a1 1 0 102 0V7a3 3 0 00-3-3z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
          )}
        </div>
        <div className="text-xs text-gray-600 mt-1 line-clamp-2">{email.preview}</div>
        <LabelChips
          labels={email.labels}
          labelMetaById={labelMetaById}
          showInboxLabelChip={showInboxLabelChip}
          className="mt-2"
        />
      </div>
    </div>
  )
}


