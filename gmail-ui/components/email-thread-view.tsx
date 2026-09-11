"use client"

import { useState } from "react"
import { nowDate } from "@/lib/clock"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import {
  ArrowLeft,
  Star,
  Archive,
  Trash2,
  Trash,
  Box,
  Sparkles,
  MoreHorizontal,
  Reply,
  ReplyAll,
  Forward,
  ChevronDown,
  ChevronUp,
  Paperclip,
  PrinterIcon as Print,
} from "lucide-react"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { useRandomization } from "@/lib/randomization-context"

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

interface EmailThreadViewProps {
  thread: EmailThread
  onBack: () => void
  onReply: (messageId: string) => void
  onReplyAll: (messageId: string) => void
  onForward: (messageId: string) => void
  onStar: (threadId: string) => void
  onArchive: (threadId: string) => void
  onDelete: (threadId: string) => void
  onMessageStarToggle?: (messageId: string, nextIsStarred: boolean) => void
  onMessageToggleRead?: (messageId: string, nextIsRead: boolean) => void
  hideMessageIds?: string[]
}

export function EmailThreadView({
  thread,
  onBack,
  onReply,
  onReplyAll,
  onForward,
  onStar,
  onArchive,
  onDelete,
  onMessageStarToggle,
  onMessageToggleRead,
  hideMessageIds,
}: EmailThreadViewProps) {
  const rnd = useRandomization()
  const threadIcons = (rnd?.threadIcons || {}) as { star?: string; archive?: string; trash?: string }
  const [expandedMessages, setExpandedMessages] = useState<Set<string>>(
    new Set([thread.messages[thread.messages.length - 1]?.id]),
  )
  const [expandedDetails, setExpandedDetails] = useState<Set<string>>(new Set())

  const toggleMessageExpansion = (messageId: string) => {
    setExpandedMessages((prev) => {
      const newSet = new Set(prev)
      if (newSet.has(messageId)) {
        newSet.delete(messageId)
      } else {
        newSet.add(messageId)
      }
      return newSet
    })
  }

  const toggleDetails = (messageId: string) => {
    setExpandedDetails((prev) => {
      const next = new Set(prev)
      if (next.has(messageId)) next.delete(messageId)
      else next.add(messageId)
      return next
    })
  }

  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2)
  }

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = nowDate()
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60)

    if (diffInHours < 24) {
      return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    } else if (diffInHours < 24 * 7) {
      return date.toLocaleDateString([], { weekday: "short", hour: "2-digit", minute: "2-digit" })
    } else {
      return date.toLocaleDateString([], { month: "short", day: "numeric", year: "numeric" })
    }
  }

  // Basic client-side sanitizer to allow simple formatting while stripping dangerous markup
  const sanitizeHtml = (input: string): string => {
    try {
      const parser = new DOMParser()
      const doc = parser.parseFromString(input, "text/html")
      const allowed = new Set(["B", "STRONG", "I", "EM", "U", "SPAN", "A", "P", "BR", "UL", "OL", "LI", "DIV", "PRE"]) as Set<string>
      const walk = (node: Node) => {
        const children = Array.from(node.childNodes)
        for (const child of children) {
          if (child.nodeType === 1) {
            const el = child as HTMLElement
            if (!allowed.has(el.tagName)) {
              const parent = el.parentNode
              if (parent) {
                while (el.firstChild) parent.insertBefore(el.firstChild, el)
                parent.removeChild(el)
              }
              continue
            }
            // Strip all attributes, then add back safe ones
            const attrs = Array.from(el.attributes)
            for (const a of attrs) el.removeAttribute(a.name)
            if (el.tagName === "A") {
              const rawHref = (child as HTMLAnchorElement).getAttribute("href") || ""
              if (rawHref && /^(https?:)?\/\//i.test(rawHref)) {
                el.setAttribute("href", rawHref)
                el.setAttribute("target", "_blank")
                el.setAttribute("rel", "noopener noreferrer")
              }
            }
            if (el.tagName === "SPAN") {
              // Preserve text color only
              const style = (child as HTMLElement).getAttribute("style") || ""
              const match = style.match(/color\s*:\s*([^;]+)/i)
              if (match) {
                el.style.color = match[1]
              }
            }
            walk(child)
          } else if (child.nodeType === 3) {
            // text node ok
          } else {
            child.parentNode?.removeChild(child)
          }
        }
      }
      walk(doc.body)
      return doc.body.innerHTML
    } catch {
      return input
    }
  }

  return (
    <div className="flex-1 flex flex-col ">
      {/* Thread Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={onBack}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div className="flex-1">
            <h1 className="text-lg font-normal  truncate injectable">{thread.subject}</h1>
            <div className="text-sm ">
              {thread.messageCount} message{thread.messageCount !== 1 ? "s" : ""} • <span className="injectable">{thread.participants.join(", ")}</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={() => onStar(thread.id)}>
            {threadIcons.star === "sparkles" ? (
              <Sparkles className={`h-4 w-4 ${thread.isStarred ? "text-yellow-500" : "text-gray-400"}`} />
            ) : (
              <Star className={`h-4 w-4 ${thread.isStarred ? "text-yellow-500 fill-current" : "text-gray-400"}`} />
            )}
          </Button>
          <Button variant="ghost" size="sm" onClick={() => onArchive(thread.id)}>
            {threadIcons.archive === "box" ? (
              <Box className="h-4 w-4" />
            ) : (
              <Archive className="h-4 w-4" />
            )}
          </Button>
          <Button variant="ghost" size="sm" onClick={() => onDelete(thread.id)}>
            {threadIcons.trash === "trash" ? (
              <Trash className="h-4 w-4" />
            ) : (
              <Trash2 className="h-4 w-4" />
            )}
          </Button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                onClick={(e) => {
                  e.stopPropagation()
                  const lastMsg = thread.messages[thread.messages.length - 1]
                  if (lastMsg) onMessageToggleRead?.(lastMsg.id, false)
                }}
              >
                Mark as unread
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Thread Messages */}
      <div className="flex-1 overflow-auto">
        <div className="max-w-4xl mx-auto p-4 space-y-4">
          {thread.messages
            .filter((m) => !(hideMessageIds || []).includes(m.id))
            .map((message, index, arr) => {
            const isExpanded = expandedMessages.has(message.id)
            const isLast = index === arr.length - 1

            return (
              <div
                key={message.id}
                className={`border rounded-lg transition-all ${
                  isExpanded ? "border-gray-200 shadow-sm" : "border-gray-100 hover:border-gray-200"
                }`}
              >
                {/* Message Header */}
                <div
                  className="flex items-center justify-between p-4 cursor-pointer"
                  onClick={() => !isLast && toggleMessageExpansion(message.id)}
                >
                  <div className="flex items-center gap-3">
                    <Avatar className="h-8 w-8">
                      <AvatarFallback className="text-xs">{getInitials(message.sender)}</AvatarFallback>
                    </Avatar>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className={`text-sm ${!message.isRead ? "font-medium" : ""} injectable`}>{message.sender}</span>
                        {!message.isRead && <div className="w-2 h-2 bg-blue-500 rounded-full"></div>}
                        {message.hasAttachment && <Paperclip className="h-3 w-3 text-gray-400" />}
                      </div>
                      <div className="text-xs ">
                        <button
                          className="hover:underline focus:underline outline-none"
                          onClick={(e) => {
                            e.stopPropagation()
                            toggleDetails(message.id)
                          }}
                        >
                          to <span className="injectable">{message.recipient}</span>
                          {expandedDetails.has(message.id) ? (
                            <ChevronUp className="inline-block ml-1 h-3 w-3 align-[-2px]" />
                          ) : (
                            <ChevronDown className="inline-block ml-1 h-3 w-3 align-[-2px]" />
                          )}
                        </button>
                        {" "}• {formatTimestamp(message.timestamp)}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      className={`${message.isStarred ? "text-yellow-500" : "text-gray-400"}`}
                      onClick={(e) => {
                        e.stopPropagation()
                        const next = !message.isStarred
                        onMessageStarToggle?.(message.id, next)
                      }}
                    >
                      {threadIcons.star === "sparkles" ? (
                        <Sparkles className="h-3 w-3" />
                      ) : (
                        <Star className="h-3 w-3" fill={message.isStarred ? "currentColor" : "none"} />
                      )}
                    </Button>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm" onClick={(e) => e.stopPropagation()}>
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem
                          onClick={(e) => {
                            e.stopPropagation()
                            onMessageToggleRead?.(message.id, false)
                          }}
                        >
                          Mark as unread
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                    {!isLast && (
                      <Button variant="ghost" size="sm">
                        {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                      </Button>
                    )}
                  </div>
                </div>

                {/* Message Body */}
                {(isExpanded || isLast) && (
                  <div className="px-4 pb-4">
                    {expandedDetails.has(message.id) && (
                      <div className="mb-3 p-3  border border-gray-100 rounded text-xs text-gray-700 space-y-1">
                        <div>
                          <span className="font-medium">From:</span>{" "}
                          <span className="injectable">{message.sender}</span>
                          {message.senderEmail ? <span className="injectable">{` <${message.senderEmail}>`}</span> : ""}
                        </div>
                        <div>
                          <span className="font-medium">To:</span>{" "}
                          <span className="injectable">{Array.isArray(message.to) && message.to.length
                            ? message.to.join(", ")
                            : message.recipient}</span>
                        </div>
                        {Array.isArray(message.cc) && message.cc.length > 0 && (
                          <div>
                            <span className="font-medium">Cc:</span>{" "}
                            <span className="injectable">{message.cc.join(", ")}</span>
                          </div>
                        )}
                        {Array.isArray(message.bcc) && message.bcc.length > 0 && (
                          <div>
                            <span className="font-medium">Bcc:</span>{" "}
                            <span className="injectable">{message.bcc.join(", ")}</span>
                          </div>
                        )}
                      </div>
                    )}
                    <div className="prose prose-sm max-w-none">
                      {typeof message.bodyHtml === "string" && message.bodyHtml.trim().length > 0 ? (
                        <div
                          className="text-sm  leading-relaxed whitespace-pre-wrap injectable"
                          dangerouslySetInnerHTML={{ __html: sanitizeHtml(message.bodyHtml) }}
                        />
                      ) : (
                        <div className="whitespace-pre-wrap text-sm  leading-relaxed injectable">{message.body}</div>
                      )}
                    </div>

                    {/* Attachments */}
                    {message.attachments && message.attachments.length > 0 && (
                      <div className="mt-4 pt-4 border-t border-gray-100">
                        <div className="text-sm  mb-2">
                          {message.attachments.length} attachment{message.attachments.length !== 1 ? "s" : ""}
                        </div>
                        <div className="space-y-2">
                          {message.attachments.map((attachment, idx) => (
                            <div key={idx} className="flex items-center gap-2 p-2  rounded">
                              <Paperclip className="h-4 w-4 " />
                              <span className="text-sm flex-1 injectable">{attachment.name}</span>
                              <span className="text-xs ">{attachment.size}</span>
                              <Button variant="ghost" size="sm" className=" text-xs">
                                Download
                              </Button>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Message Actions */}
                    <div className="flex items-center gap-2 mt-4 pt-4 border-t border-gray-100">
                      <Button variant="ghost" size="sm" onClick={() => onReply(message.id)}>
                        <Reply className="h-4 w-4 mr-2" />
                        Reply
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => onReplyAll(message.id)}>
                        <ReplyAll className="h-4 w-4 mr-2" />
                        Reply all
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => onForward(message.id)}>
                        <Forward className="h-4 w-4 mr-2" />
                        Forward
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
