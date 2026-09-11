"use client"

import React from "react"
import { EmailListItem } from "./email-list-item"
import { useRandomization } from "@/lib/randomization-context"
import { EmailCardItem } from "./email-card-item"

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
}

interface EmailListProps {
  emails: Email[]
  selectedEmails: string[]
  onEmailSelect: (emailId: string) => void
  onEmailStar: (emailId: string) => void
  onEmailToggleImportant?: (emailId: string) => void
  onEmailArchive: (emailId: string) => void
  onEmailDelete: (emailId: string) => void
  onThreadClick?: (threadId: string) => void
  showInboxLabelChip?: boolean
  inTrashView?: boolean
  onEmailToggleRead?: (emailId: string, threadId?: string) => void
  labelMetaById?: Record<string, { id: string; name: string; type: "SYSTEM" | "USER"; color?: string }>
  onEmailSnooze?: (emailId: string, untilISO: string) => void
}

export function EmailList({
  emails,
  selectedEmails,
  onEmailSelect,
  onEmailStar,
  onEmailToggleImportant,
  onEmailArchive,
  onEmailDelete,
  onThreadClick,
  showInboxLabelChip,
  inTrashView,
  onEmailToggleRead,
  labelMetaById,
  onEmailSnooze,
}: EmailListProps) {
  const rnd = useRandomization()
  const view: "list" | "grid" = (rnd?.emailListView === "grid" ? "grid" : "list")

  

  return (
    <div className="h-full flex flex-col">
      {/* Email List */}
      {view === "list" ? (
        <div className="flex-1 overflow-auto">
          {emails.length === 0 ? (
            <div className="flex items-center justify-center h-64 ">
              <div className="text-center">
                <div className="text-lg mb-2">No emails found</div>
                <div className="text-sm">Your inbox is empty</div>
              </div>
            </div>
          ) : (
            emails.map((email) => (
              <EmailListItem
                key={email.id}
                email={email}
                isSelected={selectedEmails.includes(email.id)}
                onSelect={onEmailSelect}
                onStar={onEmailStar}
                onToggleImportant={onEmailToggleImportant}
                onArchive={onEmailArchive}
                onDelete={onEmailDelete}
                onThreadClick={onThreadClick}
                showInboxLabelChip={showInboxLabelChip}
                inTrashView={inTrashView}
                onToggleRead={onEmailToggleRead}
                labelMetaById={labelMetaById}
                onSnooze={onEmailSnooze}
              />
            ))
          )}
        </div>
      ) : (
        <div className="flex-1 overflow-auto p-4">
          {emails.length === 0 ? (
            <div className="flex items-center justify-center h-64 ">
              <div className="text-center">
                <div className="text-lg mb-2">No emails found</div>
                <div className="text-sm">Your inbox is empty</div>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {emails.map((email) => (
                <EmailCardItem
                  key={email.id}
                  email={email}
                  selected={selectedEmails.includes(email.id)}
                  onEmailSelect={onEmailSelect}
                  onEmailStar={onEmailStar}
                  onEmailToggleImportant={onEmailToggleImportant}
                  onThreadClick={onThreadClick}
                  showInboxLabelChip={showInboxLabelChip}
                  labelMetaById={labelMetaById}
                  onEmailArchive={onEmailArchive}
                  onEmailDelete={onEmailDelete}
                  onEmailToggleRead={onEmailToggleRead}
                  onEmailSnooze={onEmailSnooze}
                  inTrashView={inTrashView}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
