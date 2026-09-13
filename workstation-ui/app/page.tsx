"use client"

import React, { useState, useEffect, useRef } from "react"
import {
  Mail,
  Calendar as CalendarIcon,
  Folder,
  Table,
  FileText,
  File,
  Terminal as TerminalIcon,
  Users,
  LifeBuoy,
  BookOpen,
  CreditCard,
  Globe,
  X,
  Minus,
  Maximize2,
  Clock,
  Shield,
  Send,
  Plus,
  RefreshCw,
  Search,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  Save,
  Check,
} from "lucide-react"

interface WindowState {
  id: string
  title: string
  icon: any
  isOpen: boolean
  isMinimized: boolean
  zIndex: number
}

export default function WorkstationDesktop() {
  // Desktop state
  const [activeWindowId, setActiveWindowId] = useState<string | null>("crm")
  const [windows, setWindows] = useState<Record<string, WindowState>>({
    mail: { id: "mail", title: "Mail", icon: Mail, isOpen: false, isMinimized: false, zIndex: 1 },
    calendar: { id: "calendar", title: "Calendar", icon: CalendarIcon, isOpen: false, isMinimized: false, zIndex: 1 },
    drive: { id: "drive", title: "Drive (Files)", icon: Folder, isOpen: false, isMinimized: false, zIndex: 1 },
    sheets: { id: "sheets", title: "Sheets (Spreadsheets)", icon: Table, isOpen: false, isMinimized: false, zIndex: 1 },
    docs: { id: "docs", title: "Docs", icon: FileText, isOpen: false, isMinimized: false, zIndex: 1 },
    pdf: { id: "pdf", title: "PDF Viewer", icon: File, isOpen: false, isMinimized: false, zIndex: 1 },
    terminal: { id: "terminal", title: "Terminal", icon: TerminalIcon, isOpen: false, isMinimized: false, zIndex: 1 },
    crm: { id: "crm", title: "CRM (Customer 360)", icon: Users, isOpen: true, isMinimized: false, zIndex: 2 },
    tickets: { id: "tickets", title: "Ticketing (Support Desk)", icon: LifeBuoy, isOpen: true, isMinimized: false, zIndex: 3 },
    kb: { id: "kb", title: "Knowledge Base", icon: BookOpen, isOpen: false, isMinimized: false, zIndex: 1 },
    billing: { id: "billing", title: "Billing & Invoices", icon: CreditCard, isOpen: false, isMinimized: false, zIndex: 1 },
    browser: { id: "browser", title: "Intranet Web Browser", icon: Globe, isOpen: false, isMinimized: false, zIndex: 1 },
  })
  const [highestZ, setHighestZ] = useState(3)

  // Simulation & Task State
  const [virtualTime, setVirtualTime] = useState("10:45 AM")
  const [stateHash, setStateHash] = useState("...")
  const [isSubmittingTask, setIsSubmittingTask] = useState(false)
  const [taskSummary, setTaskSummary] = useState("")
  const [taskAffectedIds, setTaskAffectedIds] = useState("")
  const [taskSuccessMsg, setTaskSuccessMsg] = useState<string | null>(null)

  // --- App-specific States ---
  // Mail
  const [emails, setEmails] = useState<any[]>([])
  const [selectedEmail, setSelectedEmail] = useState<any | null>(null)
  const [mailFolder, setMailFolder] = useState("inbox")
  const [showCompose, setShowCompose] = useState(false)
  const [composeTo, setComposeTo] = useState("")
  const [composeSubject, setComposeSubject] = useState("")
  const [composeBody, setComposeBody] = useState("")

  // Calendar
  const [events, setEvents] = useState<any[]>([])

  // Files & Drive
  const [files, setFiles] = useState<any[]>([])
  const [fileContent, setFileContent] = useState<string>("")
  const [selectedFile, setSelectedFile] = useState<string | null>(null)

  // Sheets
  const [sheetData, setSheetData] = useState<any | null>(null)
  const [editingCell, setEditingCell] = useState<{ cell: string; val: string } | null>(null)

  // Docs
  const [docContent, setDocContent] = useState("")
  const [docAppendText, setDocAppendText] = useState("")

  // Terminal
  const [terminalHistory, setTerminalHistory] = useState<Array<{ cmd: string; output: string }>>([
    { cmd: "whoami", output: "alex.mercer@apexglobal.io (Employee #042)" },
    { cmd: "uname -a", output: "OmniDesk OS 5.15.0-x86_64 Enterprise Workstation" },
  ])
  const [terminalInput, setTerminalInput] = useState("")

  // CRM
  const [crmQuery, setCrmQuery] = useState("CUST-001")
  const [crmCustomer, setCrmCustomer] = useState<any | null>(null)
  const [crmStatusUpdate, setCrmStatusUpdate] = useState("active")
  const [crmTierUpdate, setCrmTierUpdate] = useState("enterprise")

  // Tickets
  const [tickets, setTickets] = useState<any[]>([])
  const [selectedTicket, setSelectedTicket] = useState<any | null>(null)
  const [ticketStatusFilter, setTicketStatusFilter] = useState("all")
  const [ticketComment, setTicketComment] = useState("")

  // Knowledge Base
  const [kbQuery, setKbQuery] = useState("")
  const [kbArticles, setKbArticles] = useState<any[]>([])
  const [selectedArticle, setSelectedArticle] = useState<any | null>(null)

  // Billing
  const [invoiceQuery, setInvoiceQuery] = useState("INV-2026-0001")
  const [invoiceData, setInvoiceData] = useState<any | null>(null)
  const [refundAmount, setRefundAmount] = useState("")
  const [refundReason, setRefundReason] = useState("")

  // Fetch initial system state
  useEffect(() => {
    fetchSimulationState()
    loadEmails()
    loadTickets()
    loadCrmCustomer("CUST-001")
    loadFiles()
    loadEvents()
    loadSheet()
    loadKb()
    loadInvoice("INV-2026-0001")
  }, [])

  const fetchSimulationState = async () => {
    try {
      const res = await fetch("/api/workstation/simulation")
      const data = await res.json()
      if (data.ok) {
        setStateHash(data.state_hash.substring(0, 10))
      }
    } catch {}
  }

  const stepSimulation = async (minutes: number) => {
    try {
      const res = await fetch("/api/workstation/simulation", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "step", seconds: minutes * 60 }),
      })
      const data = await res.json()
      if (data.ok) {
        fetchSimulationState()
        loadEmails()
        loadTickets()
      }
    } catch {}
  }

  const submitTaskHandover = async () => {
    try {
      const res = await fetch("/api/workstation/simulation", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "submit", summary: taskSummary, affected_ids: taskAffectedIds }),
      })
      const data = await res.json()
      if (data.ok) {
        setTaskSuccessMsg("Task completion logged to tamper-evident audit trail.")
        setTimeout(() => {
          setIsSubmittingTask(false)
          setTaskSuccessMsg(null)
        }, 2000)
      }
    } catch {}
  }

  // Window actions
  const openWindow = (id: string) => {
    const nextZ = highestZ + 1
    setHighestZ(nextZ)
    setWindows((prev) => ({
      ...prev,
      [id]: { ...prev[id], isOpen: true, isMinimized: false, zIndex: nextZ },
    }))
    setActiveWindowId(id)
  }

  const closeWindow = (id: string) => {
    setWindows((prev) => ({
      ...prev,
      [id]: { ...prev[id], isOpen: false },
    }))
    if (activeWindowId === id) {
      setActiveWindowId(null)
    }
  }

  const minimizeWindow = (id: string) => {
    setWindows((prev) => ({
      ...prev,
      [id]: { ...prev[id], isMinimized: true },
    }))
  }

  const focusWindow = (id: string) => {
    const nextZ = highestZ + 1
    setHighestZ(nextZ)
    setWindows((prev) => ({
      ...prev,
      [id]: { ...prev[id], isMinimized: false, zIndex: nextZ },
    }))
    setActiveWindowId(id)
  }

  // Loaders
  const loadEmails = async (folder = mailFolder) => {
    try {
      const res = await fetch(`/api/workstation/email?folder=${folder}`)
      const data = await res.json()
      if (data.ok && Array.isArray(data.emails)) {
        setEmails(data.emails)
        if (data.emails.length > 0) setSelectedEmail(data.emails[0])
      }
    } catch {}
  }

  const handleSendEmail = async () => {
    if (!composeTo || !composeSubject) return
    try {
      await fetch("/api/workstation/email", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ to: composeTo, subject: composeSubject, body: composeBody }),
      })
      setShowCompose(false)
      setComposeTo("")
      setComposeSubject("")
      setComposeBody("")
      loadEmails()
    } catch {}
  }

  const loadTickets = async (status = ticketStatusFilter) => {
    try {
      const res = await fetch(`/api/workstation/tickets?status=${status}`)
      const data = await res.json()
      if (data.ok && Array.isArray(data.tickets)) {
        setTickets(data.tickets)
        if (data.tickets.length > 0) setSelectedTicket(data.tickets[0])
      }
    } catch {}
  }

  const handleUpdateTicket = async (ticketId: string, status?: string) => {
    try {
      await fetch("/api/workstation/tickets", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticket_id: ticketId, status, comment: ticketComment }),
      })
      setTicketComment("")
      loadTickets()
    } catch {}
  }

  const loadCrmCustomer = async (id: string) => {
    try {
      const res = await fetch(`/api/workstation/crm?id=${id}`)
      const data = await res.json()
      if (data.ok && data.customer) {
        setCrmCustomer(data.customer)
        setCrmStatusUpdate(data.customer.status || "active")
        setCrmTierUpdate(data.customer.account_tier || "enterprise")
      }
    } catch {}
  }

  const handleUpdateCrm = async () => {
    if (!crmCustomer) return
    try {
      await fetch("/api/workstation/crm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          customer_id: crmCustomer.customer_id || crmCustomer.id,
          status: crmStatusUpdate,
          account_tier: crmTierUpdate,
        }),
      })
      loadCrmCustomer(crmCustomer.customer_id || crmCustomer.id)
    } catch {}
  }

  const loadFiles = async (dir = "/") => {
    try {
      const res = await fetch(`/api/workstation/files?dir=${dir}`)
      const data = await res.json()
      if (data.ok && Array.isArray(data.files)) {
        setFiles(data.files)
      }
    } catch {}
  }

  const handleReadFile = async (path: string) => {
    setSelectedFile(path)
    try {
      const res = await fetch(`/api/workstation/files?path=${encodeURIComponent(path)}`)
      const data = await res.json()
      if (data.ok) {
        setFileContent(data.content?.content || JSON.stringify(data.content, null, 2))
      }
    } catch {}
  }

  const loadEvents = async () => {
    try {
      const res = await fetch("/api/workstation/calendar")
      const data = await res.json()
      if (data.ok && Array.isArray(data.events)) setEvents(data.events)
    } catch {}
  }

  const loadSheet = async () => {
    try {
      const res = await fetch("/api/workstation/sheets")
      const data = await res.json()
      if (data.ok) setSheetData(data.spreadsheet)
    } catch {}
  }

  const handleUpdateCell = async () => {
    if (!editingCell) return
    try {
      await fetch("/api/workstation/sheets", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path: "financial_tracker.csv", cell: editingCell.cell, value: editingCell.val }),
      })
      setEditingCell(null)
      loadSheet()
    } catch {}
  }

  const loadKb = async (query = "") => {
    try {
      const res = await fetch(`/api/workstation/kb?q=${query}`)
      const data = await res.json()
      if (data.ok && Array.isArray(data.articles)) {
        setKbArticles(data.articles)
        if (data.articles.length > 0) setSelectedArticle(data.articles[0])
      }
    } catch {}
  }

  const loadInvoice = async (id: string) => {
    try {
      const res = await fetch(`/api/workstation/billing?id=${id}`)
      const data = await res.json()
      if (data.ok) setInvoiceData(data.invoice)
    } catch {}
  }

  const handleIssueRefund = async () => {
    if (!invoiceData || !refundAmount) return
    try {
      await fetch("/api/workstation/billing", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          invoice_number: invoiceData.invoice_number || invoiceData.id,
          amount: refundAmount,
          reason: refundReason,
        }),
      })
      setRefundAmount("")
      setRefundReason("")
      loadInvoice(invoiceData.invoice_number || invoiceData.id)
    } catch {}
  }

  const handleTerminalSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!terminalInput.trim()) return
    const cmd = terminalInput
    setTerminalInput("")
    try {
      const res = await fetch("/api/workstation/terminal", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command: cmd }),
      })
      const data = await res.json()
      setTerminalHistory((prev) => [
        ...prev,
        { cmd, output: data.output?.stdout || data.output || "Command completed." },
      ])
    } catch (err: any) {
      setTerminalHistory((prev) => [...prev, { cmd, output: `Error: ${err.message}` }])
    }
  }

  return (
    <div className="h-screen w-screen flex flex-col bg-slate-950 text-slate-100 font-sans select-none overflow-hidden relative">
      {/* 1. Top OS Menu Bar */}
      <header className="h-8 bg-slate-900/90 backdrop-blur border-b border-slate-800 flex items-center justify-between px-3 text-xs z-50">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-1.5 font-bold text-sky-400">
            <span className="w-2.5 h-2.5 rounded-full bg-sky-500 inline-block animate-pulse"></span>
            <span>OmniDesk OS</span>
          </div>
          <span className="text-slate-500">|</span>
          <span className="text-slate-300 font-medium">Alex Mercer (Employee Workstation)</span>
        </div>

        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1 bg-slate-800/80 px-2 py-0.5 rounded border border-slate-700/60 font-mono text-[11px] text-slate-300">
            <Shield className="w-3 h-3 text-emerald-400" />
            <span>SHA: {stateHash}</span>
          </div>

          <div className="flex items-center space-x-1 bg-slate-800/80 px-2 py-0.5 rounded border border-slate-700/60 font-mono text-[11px] text-slate-300">
            <Clock className="w-3 h-3 text-sky-400" />
            <span>{virtualTime}</span>
          </div>

          <div className="flex items-center space-x-1">
            <button
              onClick={() => stepSimulation(15)}
              className="px-2 py-0.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 text-[11px] transition"
              title="Advance virtual clock by 15 minutes"
            >
              +15m
            </button>
            <button
              onClick={() => stepSimulation(60)}
              className="px-2 py-0.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 text-[11px] transition"
              title="Advance virtual clock by 1 hour"
            >
              +1h
            </button>
          </div>

          <button
            onClick={() => setIsSubmittingTask(true)}
            className="px-2.5 py-0.5 bg-sky-600 hover:bg-sky-500 text-white rounded font-medium text-[11px] shadow flex items-center space-x-1 transition"
          >
            <CheckCircle2 className="w-3 h-3" />
            <span>Submit Task</span>
          </button>
        </div>
      </header>

      {/* 2. Desktop Workspace with Icons */}
      <main className="flex-1 relative overflow-hidden bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950/30 p-4">
        {/* Desktop Shortcuts Grid */}
        <div className="grid grid-flow-col grid-rows-6 gap-4 w-fit z-0">
          {Object.values(windows).map((win) => {
            const Icon = win.icon
            return (
              <button
                key={win.id}
                onClick={() => openWindow(win.id)}
                className="w-20 h-20 rounded-xl hover:bg-white/5 flex flex-col items-center justify-center p-2 text-center group transition cursor-pointer"
              >
                <div className="w-10 h-10 rounded-xl bg-slate-800/80 border border-slate-700/60 flex items-center justify-center text-sky-400 group-hover:scale-105 group-hover:border-sky-500/50 shadow-lg transition">
                  <Icon className="w-5 h-5" />
                </div>
                <span className="text-[11px] mt-1 text-slate-300 font-medium truncate w-full group-hover:text-white drop-shadow">
                  {win.title.split(" ")[0]}
                </span>
              </button>
            )
          })}
        </div>

        {/* 3. Open Windows */}
        {Object.values(windows).map((win) => {
          if (!win.isOpen || win.isMinimized) return null
          const Icon = win.icon
          const isActive = activeWindowId === win.id

          return (
            <div
              key={win.id}
              onClick={() => focusWindow(win.id)}
              style={{ zIndex: win.zIndex }}
              className={`absolute top-10 left-24 w-[850px] h-[540px] bg-slate-900/95 border rounded-xl shadow-2xl flex flex-col overflow-hidden backdrop-blur-md transition-shadow ${
                isActive ? "border-sky-500/60 shadow-sky-950/40" : "border-slate-800"
              }`}
            >
              {/* Window Titlebar */}
              <div className="h-9 bg-slate-800/90 border-b border-slate-800 flex items-center justify-between px-3 cursor-move">
                <div className="flex items-center space-x-2">
                  <Icon className="w-4 h-4 text-sky-400" />
                  <span className="text-xs font-semibold text-slate-200">{win.title}</span>
                </div>
                <div className="flex items-center space-x-1.5">
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      minimizeWindow(win.id)
                    }}
                    className="w-3 h-3 rounded-full bg-amber-500/80 hover:bg-amber-500 flex items-center justify-center text-black"
                  >
                    <Minus className="w-2 h-2 opacity-0 hover:opacity-100" />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      closeWindow(win.id)
                    }}
                    className="w-3 h-3 rounded-full bg-rose-500/80 hover:bg-rose-500 flex items-center justify-center text-black"
                  >
                    <X className="w-2 h-2 opacity-0 hover:opacity-100" />
                  </button>
                </div>
              </div>

              {/* Window Body */}
              <div className="flex-1 overflow-hidden flex flex-col bg-slate-950/60 text-xs">
                {/* --- 1. CRM Window --- */}
                {win.id === "crm" && (
                  <div className="flex-1 flex flex-col p-4 space-y-4 overflow-y-auto">
                    <div className="flex items-center space-x-2">
                      <input
                        type="text"
                        value={crmQuery}
                        onChange={(e) => setCrmQuery(e.target.value)}
                        placeholder="Search Customer ID or Name (e.g. CUST-001, Acme Corp)..."
                        className="flex-1 bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-xs text-white focus:outline-none focus:border-sky-500"
                      />
                      <button
                        onClick={() => loadCrmCustomer(crmQuery)}
                        className="px-3 py-1.5 bg-sky-600 hover:bg-sky-500 text-white rounded font-medium transition"
                      >
                        Lookup
                      </button>
                    </div>

                    {crmCustomer && (
                      <div className="grid grid-cols-2 gap-4">
                        <div className="bg-slate-900 border border-slate-800 rounded-lg p-3 space-y-2">
                          <h3 className="font-semibold text-slate-200 text-sm">{crmCustomer.name || crmCustomer.company_name}</h3>
                          <div className="text-slate-400 space-y-1">
                            <p><span className="text-slate-500">ID:</span> {crmCustomer.customer_id || crmCustomer.id}</p>
                            <p><span className="text-slate-500">Primary Contact:</span> {crmCustomer.contact_email || crmCustomer.email || "billing@customer.com"}</p>
                            <p><span className="text-slate-500">Phone:</span> {crmCustomer.phone || "+1 (555) 019-2834"}</p>
                            <p><span className="text-slate-500">Address:</span> {crmCustomer.address || "100 Innovation Way, Suite 400"}</p>
                          </div>
                        </div>

                        <div className="bg-slate-900 border border-slate-800 rounded-lg p-3 space-y-3">
                          <h4 className="font-semibold text-slate-300">Account Status & Controls</h4>
                          <div>
                            <label className="text-slate-400 block mb-1">Status:</label>
                            <select
                              value={crmStatusUpdate}
                              onChange={(e) => setCrmStatusUpdate(e.target.value)}
                              className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs text-white"
                            >
                              <option value="active">Active</option>
                              <option value="pending_review">Pending Review</option>
                              <option value="suspended">Suspended</option>
                            </select>
                          </div>
                          <div>
                            <label className="text-slate-400 block mb-1">Service Tier:</label>
                            <select
                              value={crmTierUpdate}
                              onChange={(e) => setCrmTierUpdate(e.target.value)}
                              className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs text-white"
                            >
                              <option value="standard">Standard</option>
                              <option value="professional">Professional</option>
                              <option value="enterprise">Enterprise</option>
                            </select>
                          </div>
                          <button
                            onClick={handleUpdateCrm}
                            className="w-full py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-medium rounded transition"
                          >
                            Save Account Updates
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* --- 2. Tickets Window --- */}
                {win.id === "tickets" && (
                  <div className="flex-1 flex overflow-hidden">
                    <div className="w-1/3 border-r border-slate-800 flex flex-col">
                      <div className="p-2 border-b border-slate-800 flex space-x-1">
                        {["all", "open", "in_progress", "resolved"].map((s) => (
                          <button
                            key={s}
                            onClick={() => {
                              setTicketStatusFilter(s)
                              loadTickets(s)
                            }}
                            className={`px-2 py-1 rounded text-[10px] font-medium capitalize ${
                              ticketStatusFilter === s ? "bg-sky-600 text-white" : "bg-slate-800 text-slate-400 hover:text-white"
                            }`}
                          >
                            {s.replace("_", " ")}
                          </button>
                        ))}
                      </div>
                      <div className="flex-1 overflow-y-auto divide-y divide-slate-800/60">
                        {tickets.map((t) => (
                          <div
                            key={t.ticket_id || t.id}
                            onClick={() => setSelectedTicket(t)}
                            className={`p-3 cursor-pointer transition ${
                              selectedTicket?.ticket_id === t.ticket_id ? "bg-sky-950/40 border-l-2 border-sky-500" : "hover:bg-slate-900/50"
                            }`}
                          >
                            <div className="flex items-center justify-between">
                              <span className="font-mono text-[10px] text-slate-500">{t.ticket_id || t.id}</span>
                              <span className="px-1.5 py-0.5 rounded text-[9px] bg-slate-800 text-slate-300 uppercase">{t.status}</span>
                            </div>
                            <h4 className="font-medium text-slate-200 mt-1 truncate">{t.subject || t.title}</h4>
                            <p className="text-slate-400 text-[11px] truncate">{t.customer_name || t.customer_id}</p>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="flex-1 flex flex-col p-4 overflow-y-auto">
                      {selectedTicket ? (
                        <div className="space-y-4">
                          <div>
                            <div className="flex items-center space-x-2">
                              <span className="font-mono text-xs text-sky-400">{selectedTicket.ticket_id || selectedTicket.id}</span>
                              <span className="text-slate-400">• Priority: {selectedTicket.priority || "High"}</span>
                            </div>
                            <h2 className="text-base font-semibold text-slate-100 mt-1">{selectedTicket.subject || selectedTicket.title}</h2>
                          </div>

                          <div className="bg-slate-900 border border-slate-800 rounded-lg p-3 text-slate-300 whitespace-pre-wrap">
                            {selectedTicket.description || selectedTicket.body || "Customer reported outage during morning payroll reconciliation."}
                          </div>

                          <div className="space-y-2">
                            <label className="text-slate-400 font-medium">Add Internal Note / Response:</label>
                            <textarea
                              rows={3}
                              value={ticketComment}
                              onChange={(e) => setTicketComment(e.target.value)}
                              placeholder="Type response or ticket update..."
                              className="w-full bg-slate-800 border border-slate-700 rounded p-2 text-xs text-white focus:outline-none focus:border-sky-500"
                            />
                            <div className="flex space-x-2">
                              <button
                                onClick={() => handleUpdateTicket(selectedTicket.ticket_id || selectedTicket.id, "in_progress")}
                                className="px-3 py-1.5 bg-amber-600 hover:bg-amber-500 text-white rounded font-medium transition"
                              >
                                Mark In Progress
                              </button>
                              <button
                                onClick={() => handleUpdateTicket(selectedTicket.ticket_id || selectedTicket.id, "resolved")}
                                className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded font-medium transition"
                              >
                                Resolve Ticket
                              </button>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="flex items-center justify-center h-full text-slate-500">Select a ticket from the queue</div>
                      )}
                    </div>
                  </div>
                )}

                {/* --- 3. Mail Window --- */}
                {win.id === "mail" && (
                  <div className="flex-1 flex overflow-hidden">
                    <div className="w-1/4 border-r border-slate-800 p-2 space-y-1">
                      <button
                        onClick={() => setShowCompose(true)}
                        className="w-full py-1.5 bg-sky-600 hover:bg-sky-500 text-white font-medium rounded mb-2 flex items-center justify-center space-x-1"
                      >
                        <Plus className="w-3.5 h-3.5" />
                        <span>Compose</span>
                      </button>
                      {["inbox", "sent", "archive"].map((f) => (
                        <button
                          key={f}
                          onClick={() => {
                            setMailFolder(f)
                            loadEmails(f)
                          }}
                          className={`w-full text-left px-3 py-1.5 rounded capitalize font-medium ${
                            mailFolder === f ? "bg-slate-800 text-white" : "text-slate-400 hover:bg-slate-900"
                          }`}
                        >
                          {f}
                        </button>
                      ))}
                    </div>

                    <div className="w-1/3 border-r border-slate-800 overflow-y-auto divide-y divide-slate-800/60">
                      {emails.map((e) => (
                        <div
                          key={e.thread_id || e.id}
                          onClick={() => setSelectedEmail(e)}
                          className={`p-3 cursor-pointer transition ${
                            selectedEmail?.thread_id === e.thread_id ? "bg-sky-950/40" : "hover:bg-slate-900/50"
                          }`}
                        >
                          <div className="font-medium text-slate-200 truncate">{e.sender || e.from}</div>
                          <div className="text-slate-300 text-[11px] truncate font-semibold">{e.subject}</div>
                          <div className="text-slate-500 text-[10px] truncate">{e.snippet || e.body}</div>
                        </div>
                      ))}
                    </div>

                    <div className="flex-1 p-4 overflow-y-auto">
                      {selectedEmail ? (
                        <div className="space-y-3">
                          <h3 className="text-base font-semibold text-slate-100">{selectedEmail.subject}</h3>
                          <div className="text-slate-400 text-xs border-b border-slate-800 pb-2">
                            <span>From: {selectedEmail.sender || selectedEmail.from}</span>
                            <span className="mx-2">•</span>
                            <span>To: {selectedEmail.recipient || "alex.mercer@apexglobal.io"}</span>
                          </div>
                          <div className="text-slate-200 whitespace-pre-wrap leading-relaxed">
                            {selectedEmail.body || selectedEmail.snippet}
                          </div>
                        </div>
                      ) : (
                        <div className="flex items-center justify-center h-full text-slate-500">No message selected</div>
                      )}
                    </div>
                  </div>
                )}

                {/* --- 4. Billing Window --- */}
                {win.id === "billing" && (
                  <div className="flex-1 p-4 space-y-4 overflow-y-auto">
                    <div className="flex items-center space-x-2">
                      <input
                        type="text"
                        value={invoiceQuery}
                        onChange={(e) => setInvoiceQuery(e.target.value)}
                        placeholder="Lookup Invoice Number (e.g. INV-2026-0001)..."
                        className="flex-1 bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-xs text-white focus:outline-none"
                      />
                      <button
                        onClick={() => loadInvoice(invoiceQuery)}
                        className="px-3 py-1.5 bg-sky-600 hover:bg-sky-500 text-white rounded font-medium"
                      >
                        Search Invoice
                      </button>
                    </div>

                    {invoiceData && (
                      <div className="grid grid-cols-2 gap-4">
                        <div className="bg-slate-900 border border-slate-800 rounded-lg p-3 space-y-2">
                          <h4 className="font-semibold text-slate-200">Invoice Details</h4>
                          <div className="text-slate-400 space-y-1">
                            <p><span className="text-slate-500">Number:</span> {invoiceData.invoice_number || invoiceData.id}</p>
                            <p><span className="text-slate-500">Customer:</span> {invoiceData.customer_name || invoiceData.customer_id}</p>
                            <p><span className="text-slate-500">Amount:</span> ${(invoiceData.amount_cents / 100 || invoiceData.amount || 2400).toFixed(2)}</p>
                            <p><span className="text-slate-500">Status:</span> <span className="text-emerald-400 uppercase font-semibold">{invoiceData.status || "Paid"}</span></p>
                          </div>
                        </div>

                        <div className="bg-slate-900 border border-slate-800 rounded-lg p-3 space-y-3">
                          <h4 className="font-semibold text-slate-200">Process Customer Refund</h4>
                          <div>
                            <label className="text-slate-400 block mb-1">Refund Amount ($):</label>
                            <input
                              type="number"
                              value={refundAmount}
                              onChange={(e) => setRefundAmount(e.target.value)}
                              placeholder="e.g. 2400.00"
                              className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1 text-white"
                            />
                          </div>
                          <div>
                            <label className="text-slate-400 block mb-1">Reason / Justification:</label>
                            <input
                              type="text"
                              value={refundReason}
                              onChange={(e) => setRefundReason(e.target.value)}
                              placeholder="SLA service interruption credit"
                              className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1 text-white"
                            />
                          </div>
                          <button
                            onClick={handleIssueRefund}
                            className="w-full py-1.5 bg-rose-600 hover:bg-rose-500 text-white font-medium rounded transition"
                          >
                            Issue Authorized Refund
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* --- 5. Terminal Window --- */}
                {win.id === "terminal" && (
                  <div className="flex-1 bg-black p-3 font-mono text-emerald-400 flex flex-col">
                    <div className="flex-1 overflow-y-auto space-y-2">
                      {terminalHistory.map((item, i) => (
                        <div key={i}>
                          <div className="text-slate-400">$ {item.cmd}</div>
                          <div className="text-slate-200 whitespace-pre-wrap">{item.output}</div>
                        </div>
                      ))}
                    </div>
                    <form onSubmit={handleTerminalSubmit} className="mt-2 flex items-center space-x-2 border-t border-slate-800 pt-2">
                      <span className="text-emerald-500 font-bold">$</span>
                      <input
                        type="text"
                        value={terminalInput}
                        onChange={(e) => setTerminalInput(e.target.value)}
                        placeholder="Type shell command..."
                        className="flex-1 bg-transparent text-emerald-300 focus:outline-none text-xs"
                      />
                    </form>
                  </div>
                )}

                {/* --- 6. Sheets Window --- */}
                {win.id === "sheets" && (
                  <div className="flex-1 p-3 flex flex-col space-y-2 overflow-hidden">
                    <div className="text-slate-400 font-medium">Viewing: financial_tracker.csv</div>
                    <div className="flex-1 overflow-auto border border-slate-800 rounded bg-slate-900">
                      <table className="w-full text-left border-collapse">
                        <thead>
                          <tr className="bg-slate-800/80 border-b border-slate-700 text-slate-300">
                            <th className="p-2 border-r border-slate-700">Account ID</th>
                            <th className="p-2 border-r border-slate-700">Client Name</th>
                            <th className="p-2 border-r border-slate-700">Contract Value</th>
                            <th className="p-2 border-r border-slate-700">SLA Tier</th>
                            <th className="p-2">Refund Cap</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800 text-slate-300 font-mono">
                          <tr>
                            <td className="p-2 border-r border-slate-800">CUST-001</td>
                            <td className="p-2 border-r border-slate-800">Acme Corporation</td>
                            <td className="p-2 border-r border-slate-800">$120,000</td>
                            <td className="p-2 border-r border-slate-800">Platinum</td>
                            <td className="p-2">$3,000</td>
                          </tr>
                          <tr>
                            <td className="p-2 border-r border-slate-800">CUST-002</td>
                            <td className="p-2 border-r border-slate-800">Starlight Analytics</td>
                            <td className="p-2 border-r border-slate-800">$85,000</td>
                            <td className="p-2 border-r border-slate-800">Gold</td>
                            <td className="p-2">$1,500</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* --- Other Windows Placeholder --- */}
                {!["crm", "tickets", "mail", "billing", "terminal", "sheets"].includes(win.id) && (
                  <div className="flex-1 flex flex-col items-center justify-center text-slate-400 space-y-2">
                    <Icon className="w-8 h-8 text-sky-400/50" />
                    <p className="font-medium text-slate-300">{win.title} Active</p>
                    <p className="text-slate-500 text-xs">Workstation application connected to simulated organization state.</p>
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </main>

      {/* 4. Bottom OS Dock */}
      <footer className="h-14 bg-slate-900/80 backdrop-blur-md border-t border-slate-800/80 flex items-center justify-center px-4 z-40">
        <div className="flex items-center space-x-2 bg-slate-800/60 p-1.5 rounded-2xl border border-slate-700/50 shadow-xl">
          {Object.values(windows).map((win) => {
            const Icon = win.icon
            const isOpen = win.isOpen

            return (
              <button
                key={win.id}
                onClick={() => {
                  if (!isOpen) openWindow(win.id)
                  else if (win.isMinimized) focusWindow(win.id)
                  else if (activeWindowId === win.id) minimizeWindow(win.id)
                  else focusWindow(win.id)
                }}
                className={`w-10 h-10 rounded-xl flex flex-col items-center justify-center transition-all duration-150 hover:scale-110 relative group ${
                  activeWindowId === win.id && isOpen && !win.isMinimized
                    ? "bg-sky-600 text-white shadow-lg shadow-sky-600/30"
                    : "bg-slate-700/60 text-slate-300 hover:bg-slate-700 hover:text-white"
                }`}
              >
                <Icon className="w-5 h-5" />
                {isOpen && (
                  <span className="w-1 h-1 rounded-full bg-sky-400 absolute bottom-1"></span>
                )}
                {/* Tooltip */}
                <span className="absolute -top-8 px-2 py-0.5 bg-slate-800 border border-slate-700 rounded text-[10px] text-white opacity-0 group-hover:opacity-100 transition pointer-events-none whitespace-nowrap shadow-lg">
                  {win.title}
                </span>
              </button>
            )
          })}
        </div>
      </footer>

      {/* 5. Submit Task Modal */}
      {isSubmittingTask && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-5 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 font-semibold text-slate-100">
                <CheckCircle2 className="w-5 h-5 text-sky-400" />
                <span>Submit Workstation Task Handover</span>
              </div>
              <button onClick={() => setIsSubmittingTask(false)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            {taskSuccessMsg ? (
              <div className="bg-emerald-950/40 border border-emerald-800 text-emerald-300 p-3 rounded text-xs flex items-center space-x-2">
                <Check className="w-4 h-4 text-emerald-400" />
                <span>{taskSuccessMsg}</span>
              </div>
            ) : (
              <div className="space-y-3 text-xs">
                <p className="text-slate-400">
                  Submitting formal completion for this episode logs the summary and affected entity IDs to the tamper-evident workstation audit log.
                </p>
                <div>
                  <label className="text-slate-300 font-medium block mb-1">Execution Summary:</label>
                  <textarea
                    rows={3}
                    value={taskSummary}
                    onChange={(e) => setTaskSummary(e.target.value)}
                    placeholder="Describe completed actions (e.g. Updated Acme Corp tier, resolved ticket tkt-001, issued authorized refund)..."
                    className="w-full bg-slate-800 border border-slate-700 rounded p-2 text-white focus:outline-none focus:border-sky-500"
                  />
                </div>
                <div>
                  <label className="text-slate-300 font-medium block mb-1">Affected Entity IDs (comma-separated):</label>
                  <input
                    type="text"
                    value={taskAffectedIds}
                    onChange={(e) => setTaskAffectedIds(e.target.value)}
                    placeholder="e.g. CUST-001, tkt-0001, INV-2026-0001"
                    className="w-full bg-slate-800 border border-slate-700 rounded p-2 text-white focus:outline-none focus:border-sky-500"
                  />
                </div>

                <div className="flex justify-end space-x-2 pt-2">
                  <button
                    onClick={() => setIsSubmittingTask(false)}
                    className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded font-medium"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={submitTaskHandover}
                    className="px-4 py-1.5 bg-sky-600 hover:bg-sky-500 text-white rounded font-medium"
                  >
                    Submit Handover
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
