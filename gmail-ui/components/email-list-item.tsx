"use client"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { LabelChips } from "@/components/label-chips"
import { Star, Archive, Trash2, MailOpen, Mail, Clock, Sparkles, Box, Trash } from "lucide-react"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { useState } from "react"
import { nowDate, snoozeLaterTodayISO, snoozeNextWeekISO, snoozeThisWeekendISO, snoozeTomorrowISO, buildFixedZonedISOFromInputs } from "@/lib/clock"
import { useRandomization } from "@/lib/randomization-context"

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
  snoozeUntil?: string | null
  hasDraft?: boolean
}

interface EmailListItemProps {
  email: Email
  isSelected: boolean
  onSelect: (emailId: string) => void
  onStar: (emailId: string) => void
  onToggleImportant?: (emailId: string) => void
  onArchive: (emailId: string) => void
  onDelete: (emailId: string) => void
  onThreadClick?: (threadId: string) => void
  showInboxLabelChip?: boolean
  inTrashView?: boolean
  onToggleRead?: (emailId: string, threadId?: string) => void
  labelMetaById?: Record<string, { id: string; name: string; type: "SYSTEM" | "USER"; color?: string }>
  onSnooze?: (emailId: string, untilISO: string) => void
}

export function EmailListItem({
  email,
  isSelected,
  onSelect,
  onStar,
  onToggleImportant,
  onArchive,
  onDelete,
  onThreadClick,
  showInboxLabelChip,
  inTrashView,
  onToggleRead,
  labelMetaById,
  onSnooze,
}: EmailListItemProps) {
  const [isHovered, setIsHovered] = useState(false)
  const rnd = useRandomization() 
  const threadIcons = (rnd?.threadIcons || {}) as { star?: string; archive?: string; trash?: string }
  const order: Array<"sender" | "message" | "time"> = Array.isArray(rnd?.emailListItemOrder)
    ? (rnd.emailListItemOrder as Array<"sender" | "message" | "time">)
    : ["sender", "message", "time"]
  const showInlineTime = order.includes("time")

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
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2)
  }

  const handleClick = () => {
    if (onThreadClick) {
      onThreadClick(email.id)
    } else {
      onSelect(email.id)
    }
  }

  return (
    <div
      className={`relative group flex items-center px-6 py-1 hover:shadow-sm cursor-pointer transition-all duration-150  ${isSelected ? "bg-blue-50 border-blue-200 shadow-sm" : ""} ${isHovered ? "shadow-md " : ""}`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={handleClick}
    >
      <input
        type="checkbox"
        className="mr-4 rounded border-gray-300  focus:ring-blue-500 focus:ring-1 transition-colors"
        checked={isSelected}
        onClick={(e) => e.stopPropagation()}
        onChange={(e) => {
          e.stopPropagation()
          onSelect(email.id)
        }}
      />

      {/* Star control hidden in Trash */}
      {!inTrashView && (
        <Button
          variant="ghost"
          size="sm"
          className={`mr-3 p-1 transition-all duration-200 ${
            email.isStarred ? "text-yellow-500" : "text-gray-400 hover:text-yellow-500"
          }`}
          onClick={(e) => {
            e.stopPropagation()
            onStar(email.id)
          }}
        >
          {threadIcons.star === "sparkles" ? (
            <Sparkles className={`h-4 w-4 transition-all duration-200 ${email.isStarred ? "scale-110" : ""}`} />
          ) : (
            <Star
              className={`h-4 w-4 transition-all duration-200 ${email.isStarred ? "scale-110" : ""}`}
              fill={email.isStarred ? "currentColor" : "none"}
            />
          )}
        </Button>
      )}

      {/* Important toggle chip/icon — a right-pointing pentagon */}
      <Button
        variant="ghost"
        size="sm"
        className={`mr-3 p-1 transition-all duration-200 ${
          email.isImportant ? "text-yellow-500" : "text-gray-400 hover:text-yellow-500"
        }`}
        title={email.isImportant ? "Marked important" : "Mark as important"}
        onClick={(e) => {
          e.stopPropagation()
          onToggleImportant?.(email.id)
        }}
      >
        <svg
          className={`h-4 w-4 ${email.isImportant ? "scale-110" : ""}`}
          viewBox="0 0 16 16"
          aria-hidden="true"
          focusable="false"
        >
          {/* Sideways pentagon (right-pointing). Filled when important, stroked otherwise. */}
          <path
            d="M2.25 3.25h7.1l4.4 4.75-4.4 4.75h-7.1c-.69 0-1.25-.56-1.25-1.25V4.5c0-.69.56-1.25 1.25-1.25z"
            fill={email.isImportant ? "currentColor" : "none"}
            stroke={email.isImportant ? "currentColor" : "currentColor"}
            strokeWidth="1"
            strokeLinejoin="round"
          />
        </svg>
      </Button>

      <div className={`flex-1 min-w-0 transition-all ${isHovered ? "pr-56" : "pr-48"}`}>
        <div className="flex items-center justify-between py-2">
          <div className="flex items-start gap-3 flex-1 min-w-0">
            {order.map((part) => {
              if (part === "sender") {
                return (
                  <span key="sender" className={`text-sm truncate min-w-0 w-48 flex-shrink-0 injectable ${!email.isRead ? "font-bold" : "font-normal"}`}>
                    {email.sender}
                    {typeof email.messageCount === "number" && email.messageCount > 0 && (
                      <span className={`ml-2 text-xs`}>{email.messageCount}</span>
                    )}
                  </span>
                )
              }
              if (part === "message") {
                return (
                  <div key="message" className="flex-1 min-w-0 overflow-hidden">
                    <span className="truncate block text-sm">
                      <span className={`${!email.isRead ? "font-bold" : "font-normal"}  injectable`}>{email.subject}</span>
                      <span className=" injectable"> - {email.preview}</span>
                    </span>
                  </div>
                )
              }
              // time
              return (
                <span key="time" className="text-xs text-gray-600 whitespace-nowrap flex-shrink-0">
                  {email.snoozeUntil ? (
                    <>
                      <Clock className="inline-block h-3.5 w-3.5 align-[-2px] mr-1" />
                      {formatSnoozeUntil(email.snoozeUntil)}
                    </>
                  ) : (
                    email.time
                  )}
                </span>
              )
            })}
          </div>

          <div className="flex items-center gap-2 flex-shrink-0 ml-2">
            {/* Draft chip if any draft exists in this thread (includes drafts outside current folder) */}
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

            <LabelChips labels={email.labels} labelMetaById={labelMetaById} showInboxLabelChip={showInboxLabelChip} />

            {/* time moved to absolute position for precise alignment */}
          </div>
        </div>
      </div>

      {/* Hover actions (absolute, no layout shift; push content via right padding) */}
      <div className={`absolute right-4 top-1/2 -translate-y-1/2 z-10 flex gap-1 min-w-[9rem] justify-end transition-opacity duration-150 ${isHovered ? "opacity-100" : "opacity-0 pointer-events-none"}`}>
        <Button
          variant="ghost"
          size="sm"
          onClick={(e) => {
            e.stopPropagation()
            onArchive(email.id)
          }}
          className="hover:bg-gray-200 transition-colors p-1"
        >
          {threadIcons.archive === "box" ? <Box className="h-4 w-4" /> : <Archive className="h-4 w-4" />}
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={(e) => {
            e.stopPropagation()
            onDelete(email.id)
          }}
          className="hover:bg-red-100 hover:text-red-600 transition-colors p-1"
        >
          {threadIcons.trash === "trash" ? <Trash className="h-4 w-4" /> : <Trash2 className="h-4 w-4" />}
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={(e) => {
            e.stopPropagation()
            onToggleRead?.(email.id, email.threadId)
          }}
          className="hover:bg-gray-200 transition-colors p-1"
        >
          {!email.isRead ? <MailOpen className="h-4 w-4" /> : <Mail className="h-4 w-4" />}
        </Button>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation()
              }}
              className="hover:bg-gray-200 transition-colors p-1"
            >
              <Clock className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>Snooze</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={(e) => {
                e.stopPropagation()
                onSnooze?.(email.id, snoozeLaterTodayISO())
              }}
            >
              Later today
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={(e) => {
                e.stopPropagation()
                onSnooze?.(email.id, snoozeTomorrowISO())
              }}
            >
              Tomorrow
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={(e) => {
                e.stopPropagation()
                onSnooze?.(email.id, snoozeThisWeekendISO())
              }}
            >
              This weekend
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={(e) => {
                e.stopPropagation()
                onSnooze?.(email.id, snoozeNextWeekISO())
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
                onSnooze?.(email.id, iso)
              }}
            >
              Pick date & time…
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Time or Snoozed-until flag, aligned to the right; hidden on hover */}
      {!isHovered && !showInlineTime && (
        <span className="absolute right-4 top-1/2 -translate-y-1/2 text-xs  whitespace-nowrap font-normal flex items-center gap-1">
          {email.snoozeUntil ? (
            <>
              <Clock className="h-3.5 w-3.5" />
              {formatSnoozeUntil(email.snoozeUntil)}
            </>
          ) : (
            email.time
          )}
        </span>
      )}
    </div>
  )
}
