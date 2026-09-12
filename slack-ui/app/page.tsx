"use client"

import React, { useState, useEffect, useRef } from "react"
import {
  Hash,
  Lock,
  MessageSquare,
  Search,
  Send,
  Smile,
  ChevronDown,
  X,
  CheckCircle2,
  Code2,
  Check,
  RefreshCw,
  Bell,
  User,
  Users,
  Info,
  ExternalLink,
  ShieldAlert,
  ThumbsUp,
  Sparkles,
} from "lucide-react"

interface Channel {
  channel_id: string
  name: string
  is_private: boolean
  topic?: string
  unread_count?: number
  member_count?: number
}

interface SlackMessage {
  id: string
  channel_id: string
  user_id: string
  author_handle?: string
  author_display_name?: string
  ts: string
  text: string
  is_thread_reply: boolean
  reply_count?: number
  thread_ts?: string
  reactions?: Array<{ emoji: string; count: number; users: string[] }>
}

export default function SlackWorkspacePage() {
  const [channels, setChannels] = useState<Channel[]>([])
  const [selectedChannel, setSelectedChannel] = useState<Channel | null>(null)
  const [messages, setMessages] = useState<SlackMessage[]>([])
  const [loadingMessages, setLoadingMessages] = useState(false)
  const [messageInput, setMessageInput] = useState("")
  const [activeThread, setActiveThread] = useState<SlackMessage | null>(null)
  const [threadReplies, setThreadReplies] = useState<SlackMessage[]>([])
  const [threadInput, setThreadInput] = useState("")
  const [loadingThread, setLoadingThread] = useState(false)

  // Cutover Decision Modal State
  const [showDecisionModal, setShowDecisionModal] = useState(false)
  const [decisionText, setDecisionText] = useState(
    `Migration Cutover Assessment:
- Confirmed migration time: Thursday 02:00 UTC (expected downtime: 90 minutes)
- Status: READY
- Current state & owners:
  * SSO / Auth: Alyssa (cert rotation verified, staged in identity-eng)
  * Historical Data: Marcus (backfill complete, verified in data-ops)
  * EU Workspace Access: Sophia (permissions sync verified)
  * Cutover Window: Daniel (coordinated with customer ops)
- Code reviews: All [review-needed] PRs in #debugging reviewed and cleared.
- No remaining blocking issues.`
  )
  const [decisionSent, setDecisionSent] = useState(false)
  const [feedbackMsg, setFeedbackMsg] = useState<string | null>(null)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const threadEndRef = useRef<HTMLDivElement>(null)

  // Fetch initial channels
  const fetchChannels = async () => {
    try {
      const res = await fetch("/api/slack/channels")
      if (res.ok) {
        const data = await res.json()
        const chList: Channel[] = data.channels || []
        setChannels(chList)
        // Default to #acme-migration (C019) or first channel
        const defaultCh = chList.find((c) => c.name === "acme-migration") || chList[0]
        if (defaultCh && !selectedChannel) {
          setSelectedChannel(defaultCh)
        }
      }
    } catch (err) {
      console.error("Failed to load channels", err)
    }
  }

  // Fetch messages for selected channel
  const fetchMessages = async (channelId: string) => {
    try {
      setLoadingMessages(true)
      const res = await fetch(`/api/slack/messages?channel_id=${channelId}`)
      if (res.ok) {
        const data = await res.json()
        setMessages(data.messages || [])
      }
    } catch (err) {
      console.error("Failed to load messages", err)
    } finally {
      setLoadingMessages(false)
    }
  }

  // Fetch thread replies
  const fetchThreadReplies = async (threadTs: string, channelId: string) => {
    try {
      setLoadingThread(true)
      const res = await fetch(`/api/slack/threads?thread_ts=${threadTs}&channel_id=${channelId}`)
      if (res.ok) {
        const data = await res.json()
        setThreadReplies(data.messages || [])
      }
    } catch (err) {
      console.error("Failed to load thread replies", err)
    } finally {
      setLoadingThread(false)
    }
  }

  useEffect(() => {
    fetchChannels()
  }, [])

  useEffect(() => {
    if (selectedChannel) {
      fetchMessages(selectedChannel.channel_id)
    }
  }, [selectedChannel])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  useEffect(() => {
    threadEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [threadReplies])

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!messageInput.trim() || !selectedChannel) return

    const textToSend = messageInput
    setMessageInput("")

    try {
      const res = await fetch("/api/slack/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ channel_id: selectedChannel.channel_id, text: textToSend }),
      })
      if (res.ok) {
        await fetchMessages(selectedChannel.channel_id)
      }
    } catch (err) {
      console.error("Failed to send message", err)
    }
  }

  const handleSendThreadReply = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!threadInput.trim() || !activeThread || !selectedChannel) return

    const textToSend = threadInput
    setThreadInput("")

    try {
      const res = await fetch("/api/slack/threads", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          channel_id: selectedChannel.channel_id,
          thread_ts: activeThread.thread_ts || activeThread.ts,
          text: textToSend,
        }),
      })
      if (res.ok) {
        await fetchThreadReplies(activeThread.thread_ts || activeThread.ts, selectedChannel.channel_id)
        await fetchMessages(selectedChannel.channel_id)
      }
    } catch (err) {
      console.error("Failed to reply in thread", err)
    }
  }

  const handleAddReaction = async (msg: SlackMessage, emoji: string) => {
    if (!selectedChannel) return
    try {
      await fetch("/api/slack/react", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          channel_id: selectedChannel.channel_id,
          ts: msg.ts,
          emoji,
        }),
      })
      await fetchMessages(selectedChannel.channel_id)
    } catch (err) {
      console.error("Failed to react", err)
    }
  }

  const handleOpenThread = (msg: SlackMessage) => {
    setActiveThread(msg)
    if (selectedChannel) {
      fetchThreadReplies(msg.thread_ts || msg.ts, selectedChannel.channel_id)
    }
  }

  const handleSendDecision = async () => {
    if (!decisionText.trim()) return
    // Daniel's root message in C019 is MSG145 with ts '1787176500.000000'
    try {
      const res = await fetch("/api/slack/threads", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          channel_id: "C019",
          thread_ts: "1787176500.000000",
          text: decisionText,
        }),
      })
      if (res.ok) {
        setDecisionSent(true)
        setFeedbackMsg("Migration readiness assessment posted into Daniel's thread!")
        if (selectedChannel?.channel_id === "C019") {
          await fetchMessages("C019")
        }
      }
    } catch (err: any) {
      setFeedbackMsg(`Error: ${err.message}`)
    }
  }

  const getAvatarColor = (name: string) => {
    const colors = [
      "bg-emerald-600",
      "bg-sky-600",
      "bg-amber-600",
      "bg-purple-600",
      "bg-rose-600",
      "bg-indigo-600",
      "bg-teal-600",
    ]
    let sum = 0
    for (let i = 0; i < name.length; i++) sum += name.charCodeAt(i)
    return colors[sum % colors.length]
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#1a1d21]">
      {/* 1. Left Slack Workspace Sidebar */}
      <aside className="w-64 bg-[#19171d] border-r border-[#383540] flex flex-col shrink-0 select-none">
        {/* Workspace Title Header */}
        <div className="p-3.5 border-b border-[#383540] flex items-center justify-between hover:bg-[#27242c] cursor-pointer transition">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-sky-600 flex items-center justify-center font-bold text-white text-sm shadow-md">
              A
            </div>
            <div>
              <div className="flex items-center gap-1">
                <span className="font-bold text-sm text-white tracking-tight">Acme Workspace</span>
                <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
              </div>
              <div className="flex items-center gap-1.5 text-[11px] text-emerald-400">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                <span>Engineering Prod</span>
              </div>
            </div>
          </div>
          <button
            onClick={fetchChannels}
            title="Refresh channels"
            className="p-1 rounded hover:bg-[#383540] text-slate-400 hover:text-white transition"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Channels List */}
        <div className="flex-1 overflow-y-auto py-2 px-2 space-y-0.5 text-xs">
          <div className="px-2 py-1 text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center justify-between">
            <span>Channels</span>
            <span className="text-[10px] text-slate-500">{channels.length}</span>
          </div>

          {channels.map((ch) => {
            const isSelected = selectedChannel?.channel_id === ch.channel_id
            return (
              <button
                key={ch.channel_id}
                onClick={() => setSelectedChannel(ch)}
                className={`w-full text-left px-2.5 py-1.5 rounded-md flex items-center justify-between transition ${
                  isSelected
                    ? "bg-[#1164A3] text-white font-semibold"
                    : "text-slate-300 hover:bg-[#27242c]"
                }`}
              >
                <div className="flex items-center gap-2 truncate">
                  {ch.is_private ? (
                    <Lock className="w-3.5 h-3.5 shrink-0 opacity-70" />
                  ) : (
                    <Hash className="w-3.5 h-3.5 shrink-0 opacity-70" />
                  )}
                  <span className="truncate">{ch.name}</span>
                </div>
                {ch.unread_count && ch.unread_count > 0 ? (
                  <span
                    className={`text-[10px] px-1.5 py-0.2 rounded-full font-bold shrink-0 ${
                      isSelected ? "bg-white text-[#1164A3]" : "bg-rose-500/80 text-white"
                    }`}
                  >
                    {ch.unread_count}
                  </span>
                ) : null}
              </button>
            )
          })}

          {/* Key Direct Messages section */}
          <div className="pt-3 px-2 py-1 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            Direct Messages
          </div>
          {[
            { name: "Daniel Cho", handle: "daniel", role: "Migration Lead" },
            { name: "Alyssa Vance", handle: "alyssa", role: "Identity Eng" },
            { name: "Sophia Lin", handle: "sophia", role: "EU Compliance" },
            { name: "Marcus Brody", handle: "marcus", role: "Data Ops" },
          ].map((dm) => (
            <div
              key={dm.handle}
              className="px-2.5 py-1.5 rounded-md flex items-center justify-between text-slate-300 hover:bg-[#27242c] cursor-pointer"
            >
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-400" />
                <span>{dm.name}</span>
              </div>
              <span className="text-[10px] text-slate-500 font-mono">@{dm.handle}</span>
            </div>
          ))}
        </div>

        {/* User Profile Card */}
        <div className="p-3 border-t border-[#383540] bg-[#141217] flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded bg-sky-600 flex items-center justify-center text-white font-bold text-xs">
              AG
            </div>
            <div>
              <p className="text-xs font-semibold text-white">agent</p>
              <p className="text-[10px] text-slate-400">Senior Staff Engineer</p>
            </div>
          </div>
          <span className="w-2 h-2 rounded-full bg-emerald-400" title="Active" />
        </div>
      </aside>

      {/* 2. Center Chat Main Panel */}
      <main className="flex-1 flex flex-col min-w-0 bg-[#1a1d21]">
        {/* Channel Header Bar */}
        <header className="px-4 py-2.5 border-b border-[#383540] bg-[#1a1d21] flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-sm text-white flex items-center gap-1">
                {selectedChannel?.is_private ? <Lock className="w-4 h-4" /> : <Hash className="w-4 h-4" />}
                {selectedChannel?.name || "channel"}
              </span>
              {selectedChannel?.name === "debugging" && (
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/20 border border-amber-500/40 text-amber-300 font-semibold">
                  Review Queue Active
                </span>
              )}
              {selectedChannel?.name === "acme-migration" && (
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-sky-500/20 border border-sky-500/40 text-sky-300 font-semibold">
                  Cutover Coordination
                </span>
              )}
            </div>
            <p className="text-xs text-slate-400 truncate max-w-xl">
              {selectedChannel?.topic || "No topic set"}
            </p>
          </div>

          {/* Action Triggers */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowDecisionModal(true)}
              className="px-3 py-1.5 rounded bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold transition flex items-center gap-1.5 shadow-sm shadow-sky-600/30"
            >
              <ShieldAlert className="w-3.5 h-3.5" />
              Post Cutover Decision
            </button>
            <button
              onClick={() => selectedChannel && fetchMessages(selectedChannel.channel_id)}
              className="p-1.5 rounded hover:bg-[#27242c] text-slate-400 hover:text-white transition"
              title="Refresh messages"
            >
              <RefreshCw className={`w-4 h-4 ${loadingMessages ? "animate-spin" : ""}`} />
            </button>
          </div>
        </header>

        {/* Feedback Alert */}
        {feedbackMsg && (
          <div className="bg-sky-950/60 border-b border-sky-800/60 px-4 py-2 flex items-center justify-between text-xs text-sky-300">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-sky-400" />
              <span>{feedbackMsg}</span>
            </div>
            <button onClick={() => setFeedbackMsg(null)} className="text-slate-400 hover:text-slate-200">
              Dismiss
            </button>
          </div>
        )}

        {/* Message Stream */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {loadingMessages && messages.length === 0 ? (
            <div className="flex items-center justify-center h-full text-slate-500 text-xs gap-2">
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Loading messages...</span>
            </div>
          ) : messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-slate-500 text-xs">
              <MessageSquare className="w-8 h-8 mb-2 opacity-40" />
              <span>This is the start of the #{selectedChannel?.name} channel.</span>
            </div>
          ) : (
            messages.map((msg) => {
              const displayName = msg.author_display_name || msg.author_handle || msg.user_id
              const handle = msg.author_handle || msg.user_id
              const isDanielPrompt = msg.id === "MSG145"
              const isReviewNeeded = msg.text.includes("[review-needed]")

              return (
                <div
                  key={msg.id}
                  className={`slack-message p-2.5 rounded-lg transition group ${
                    isDanielPrompt
                      ? "bg-sky-950/20 border border-sky-800/40"
                      : isReviewNeeded
                      ? "bg-amber-950/10 border border-amber-900/30"
                      : ""
                  }`}
                >
                  <div className="flex items-start gap-3">
                    {/* User Avatar */}
                    <div
                      className={`w-9 h-9 rounded-lg flex items-center justify-center text-white font-bold text-xs shrink-0 ${getAvatarColor(
                        displayName
                      )}`}
                    >
                      {displayName.substring(0, 2).toUpperCase()}
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-baseline gap-2">
                        <span className="font-bold text-xs text-white">{displayName}</span>
                        <span className="text-[10px] text-slate-400 font-mono">@{handle}</span>
                        <span className="text-[10px] text-slate-500">{msg.ts}</span>
                        {isDanielPrompt && (
                          <span className="text-[9px] px-1.5 py-0.2 rounded bg-sky-500/20 text-sky-300 font-semibold">
                            Cutover Request Prompt
                          </span>
                        )}
                        {isReviewNeeded && (
                          <span className="text-[9px] px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 font-semibold">
                            Review Needed
                          </span>
                        )}
                      </div>

                      {/* Message Text */}
                      <div className="text-xs text-slate-200 mt-1 leading-relaxed whitespace-pre-wrap font-sans">
                        {msg.text}
                      </div>

                      {/* Thread Replies Trigger */}
                      <div className="mt-2 flex items-center gap-2">
                        {(msg.reply_count && msg.reply_count > 0) || isDanielPrompt ? (
                          <button
                            onClick={() => handleOpenThread(msg)}
                            className="px-2 py-1 rounded bg-[#222529] hover:bg-[#2b2e33] border border-[#383540] text-[11px] font-medium text-sky-400 flex items-center gap-1.5 transition"
                          >
                            <MessageSquare className="w-3 h-3" />
                            <span>
                              {msg.reply_count && msg.reply_count > 0
                                ? `${msg.reply_count} replies`
                                : "View thread replies"}
                            </span>
                          </button>
                        ) : null}

                        {/* Quick Reaction Button */}
                        <button
                          onClick={() => handleAddReaction(msg, "thumbsup")}
                          className="opacity-0 group-hover:opacity-100 px-2 py-1 rounded bg-[#222529] hover:bg-[#2b2e33] border border-[#383540] text-[11px] text-slate-400 hover:text-white flex items-center gap-1 transition"
                        >
                          <Smile className="w-3 h-3" />
                          <span>+React</span>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )
            })
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Message Input Box */}
        <div className="p-3 border-t border-[#383540] bg-[#1a1d21]">
          <form onSubmit={handleSendMessage} className="rounded-lg border border-[#383540] bg-[#222529] overflow-hidden focus-within:border-sky-500">
            <textarea
              value={messageInput}
              onChange={(e) => setMessageInput(e.target.value)}
              placeholder={`Message #${selectedChannel?.name || "channel"}...`}
              rows={2}
              className="w-full bg-transparent p-2.5 text-xs text-white placeholder:text-slate-500 focus:outline-none resize-none"
            />
            <div className="px-2.5 py-1.5 bg-[#1e2226] border-t border-[#2e3238] flex items-center justify-between text-xs">
              <div className="flex items-center gap-1 text-slate-400 text-[11px]">
                <span className="font-mono">Markdown supported</span>
              </div>
              <button
                type="submit"
                disabled={!messageInput.trim()}
                className="px-3 py-1 rounded bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white text-xs font-semibold transition flex items-center gap-1"
              >
                <Send className="w-3 h-3" />
                <span>Send</span>
              </button>
            </div>
          </form>
        </div>
      </main>

      {/* 3. Right Thread Side Drawer */}
      {activeThread && (
        <aside className="w-96 bg-[#1e2228] border-l border-[#383540] flex flex-col shrink-0">
          <div className="p-3 border-b border-[#383540] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-sky-400" />
              <span className="font-bold text-xs text-white">Thread</span>
              <span className="text-[10px] text-slate-400 font-mono">#{selectedChannel?.name}</span>
            </div>
            <button
              onClick={() => setActiveThread(null)}
              className="p-1 rounded hover:bg-[#2b2f36] text-slate-400 hover:text-white transition"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Root Message Preview in Thread */}
          <div className="p-3.5 border-b border-[#383540] bg-[#171a1f] space-y-1">
            <div className="flex items-center gap-2">
              <span className="font-bold text-xs text-white">
                {activeThread.author_display_name || activeThread.author_handle}
              </span>
              <span className="text-[10px] text-slate-500">{activeThread.ts}</span>
            </div>
            <p className="text-xs text-slate-300 line-clamp-3 font-sans leading-relaxed">
              {activeThread.text}
            </p>
          </div>

          {/* Thread Replies List */}
          <div className="flex-1 overflow-y-auto p-3.5 space-y-3">
            {loadingThread ? (
              <div className="flex items-center justify-center py-6 text-slate-500 text-xs gap-2">
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Loading replies...</span>
              </div>
            ) : threadReplies.length === 0 ? (
              <div className="text-center py-6 text-slate-500 text-xs">
                No replies yet. Be the first to respond!
              </div>
            ) : (
              threadReplies.map((reply) => (
                <div key={reply.id} className="space-y-1 text-xs">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-white">
                      {reply.author_display_name || reply.author_handle || reply.user_id}
                    </span>
                    <span className="text-[10px] text-slate-500">{reply.ts}</span>
                  </div>
                  <div className="text-slate-200 bg-[#16181d] p-2.5 rounded border border-[#2b2f36] leading-relaxed whitespace-pre-wrap">
                    {reply.text}
                  </div>
                </div>
              ))
            )}
            <div ref={threadEndRef} />
          </div>

          {/* Quick Reply Helper for Code Review in Thread */}
          <div className="px-3 py-1.5 bg-[#171a1f] border-t border-[#2e3238] flex items-center gap-1.5 overflow-x-auto text-[10px]">
            <span className="text-slate-400">Quick:</span>
            <button
              onClick={() => setThreadInput("Looks good to me")}
              className="px-2 py-0.5 rounded bg-sky-900/30 text-sky-300 border border-sky-800/40 hover:bg-sky-900/50"
            >
              Looks good to me
            </button>
            <button
              onClick={() =>
                setThreadInput(
                  "Correctness issue: missing validation for token expiration edge cases on reconnect."
                )
              }
              className="px-2 py-0.5 rounded bg-rose-950/30 text-rose-300 border border-rose-900/40 hover:bg-rose-950/50"
            >
              Material Issue
            </button>
          </div>

          {/* Thread Input Box */}
          <form onSubmit={handleSendThreadReply} className="p-3 border-t border-[#383540] bg-[#1a1d21]">
            <div className="flex gap-2">
              <input
                type="text"
                value={threadInput}
                onChange={(e) => setThreadInput(e.target.value)}
                placeholder="Reply in thread..."
                className="flex-1 bg-[#222529] border border-[#383540] rounded px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-sky-500"
              />
              <button
                type="submit"
                disabled={!threadInput.trim()}
                className="px-3 py-1.5 rounded bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white text-xs font-semibold"
              >
                Reply
              </button>
            </div>
          </form>
        </aside>
      )}

      {/* 4. Cutover Decision Modal */}
      {showDecisionModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#1e2228] border border-sky-800 max-w-xl w-full rounded-xl p-5 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-[#383540] pb-3">
              <div className="flex items-center gap-2 text-white">
                <ShieldAlert className="w-5 h-5 text-sky-400" />
                <h3 className="font-bold text-sm">Post Final Cutover Decision</h3>
              </div>
              <button
                onClick={() => setShowDecisionModal(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              This response will be posted as an authoritative reply to Daniel Cho's request thread (
              <code className="text-sky-300">MSG145</code> in <code className="text-sky-300">#acme-migration</code>).
            </p>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Authoritative Handover Report
              </label>
              <textarea
                value={decisionText}
                onChange={(e) => setDecisionText(e.target.value)}
                rows={8}
                className="w-full bg-[#131519] border border-[#383540] rounded-lg p-3 text-xs font-mono text-slate-200 focus:outline-none focus:border-sky-500 leading-relaxed"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-[#383540]">
              <button
                onClick={() => setShowDecisionModal(false)}
                className="px-3 py-1.5 rounded bg-slate-800 text-slate-300 text-xs hover:bg-slate-700"
              >
                Cancel
              </button>
              <button
                onClick={handleSendDecision}
                className="px-4 py-1.5 rounded bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold shadow-md shadow-sky-600/30 flex items-center gap-1.5"
              >
                <Send className="w-3.5 h-3.5" />
                <span>Submit to Daniel's Thread</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
