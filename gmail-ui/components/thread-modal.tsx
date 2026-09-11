"use client"

import { Button } from "@/components/ui/button"
import { EmailThreadView } from "@/components/email-thread-view"
import { ComposeModal } from "@/components/compose-modal"

type ComposeMode = "compose" | "reply" | "replyAll" | "forward"

interface ThreadModalProps {
  isOpen: boolean
  onClose: () => void
  thread: any | null
  onBack: () => void
  onReply: (messageId: string) => void
  onReplyAll: (messageId: string) => void
  onForward: (messageId: string) => void
  onStar: (threadId: string) => void
  onArchive: (threadId: string) => Promise<void> | void
  onDelete: (threadId: string) => Promise<void> | void
  onMessageStarToggle?: (messageId: string, nextIsStarred: boolean) => void
  onMessageToggleRead?: (messageId: string, nextIsRead: boolean) => void
  // Compose controls
  showCompose: boolean
  onComposeClose: () => void
  onComposeSend: (emailData: { to: string; cc?: string; bcc?: string; subject: string; body: string; htmlBody?: string }) => Promise<void> | void
  threadComposeMode: ComposeMode
  threadComposeInitials: { to?: string; cc?: string; bcc?: string; subject?: string; body?: string }
  threadComposeCloseSignal: number
}

export function ThreadModal({
  isOpen,
  onClose,
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
  showCompose,
  onComposeClose,
  onComposeSend,
  threadComposeMode,
  threadComposeInitials,
  threadComposeCloseSignal,
}: ThreadModalProps) {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 bg-black/30 flex items-center justify-center" onClick={onClose}>
      <div className="bg-white w-full max-w-5xl max-h-[90vh] rounded-lg shadow-lg overflow-hidden flex flex-col" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between px-4 py-2 border-b border-gray-200">
          <div className="text-sm font-medium">Conversation</div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            Close
          </Button>
        </div>
        <div className="flex-1 overflow-auto">
          {thread && (
            <>
              <EmailThreadView
                thread={thread}
                onBack={onBack}
                onReply={onReply}
                onReplyAll={onReplyAll}
                onForward={onForward}
                onStar={onStar}
                onArchive={onArchive}
                onDelete={onDelete}
                onMessageStarToggle={onMessageStarToggle}
                onMessageToggleRead={onMessageToggleRead}
              />
              <ComposeModal
                isOpen={showCompose}
                onClose={onComposeClose}
                onSend={onComposeSend}
                mode={threadComposeMode}
                variant={"inline"}
                externalCloseSignal={threadComposeCloseSignal}
                initialTo={threadComposeInitials.to}
                initialCc={threadComposeInitials.cc}
                initialBcc={threadComposeInitials.bcc}
                initialSubject={threadComposeInitials.subject}
                initialBody={threadComposeInitials.body}
                parentThreadId={thread?.id}
              />
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default ThreadModal


