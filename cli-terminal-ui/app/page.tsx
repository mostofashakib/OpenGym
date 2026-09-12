"use client"

import React, { useState, useEffect, useRef } from "react"
import {
  Terminal as TerminalIcon,
  Server,
  Cpu,
  HardDrive,
  Activity,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Play,
  RotateCcw,
  Send,
  FileText,
  Folder,
  Shield,
  Clock,
  Sparkles,
  ChevronRight,
  RefreshCw,
  Eye,
  Trash2,
} from "lucide-react"

interface CommandHistoryItem {
  id: string
  command: string
  stdout: string
  stderr: string
  exit_code: number
  timestamp: string
}

export default function TerminalConsolePage() {
  const [commandInput, setCommandInput] = useState("")
  const [history, setHistory] = useState<CommandHistoryItem[]>([])
  const [loadingCommand, setLoadingCommand] = useState(false)
  const [systemState, setSystemState] = useState<any>(null)
  const [activeTab, setActiveTab] = useState<"monitor" | "files" | "submit">("monitor")
  const [selectedFile, setSelectedFile] = useState<string | null>(null)
  const [fileContent, setFileContent] = useState<string>("")
  const [loadingFile, setLoadingFile] = useState(false)
  const [summaryText, setSummaryText] = useState("")
  const [actionsInput, setActionsInput] = useState("")
  const [submitResult, setSubmitResult] = useState<any>(null)
  const [submitting, setSubmitting] = useState(false)

  const terminalEndRef = useRef<HTMLDivElement>(null)
  const commandInputRef = useRef<HTMLInputElement>(null)

  // Fetch initial system state
  const fetchSystem = async () => {
    try {
      const res = await fetch("/api/terminal/system")
      if (res.ok) {
        const data = await res.json()
        setSystemState(data)
      }
    } catch (err) {
      console.error("Failed to fetch system state", err)
    }
  }

  useEffect(() => {
    fetchSystem()
    // Initial greeting in terminal
    setHistory([
      {
        id: "init-1",
        command: "uname -a && uptime",
        stdout: "Linux app-node-04.prod.corp 6.8.0-40-generic #40-Ubuntu SMP PREEMPT_DYNAMIC x86_64\n 02:30:15 up 14 days, 3 hours, 2 users, load average: 4.82, 3.12, 1.95",
        stderr: "",
        exit_code: 0,
        timestamp: "02:30:15",
      },
      {
        id: "init-2",
        command: "systemctl status payment-processor.service",
        stdout: "● payment-processor.service - Production Payment Processing Engine\n   Loaded: loaded (/etc/systemd/system/payment-processor.service; enabled)\n   Active: failed (Result: exit-code) since Sat 2026-09-12 02:14:19 UTC\n\nSep 12 02:14:19 app-node-04 payment-processor[3102]: [ERROR] Database connection failed",
        stderr: "",
        exit_code: 3,
        timestamp: "02:30:16",
      },
    ])
  }, [])

  useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [history])

  const runCommand = async (cmdToRun: string) => {
    if (!cmdToRun.trim() || loadingCommand) return
    setLoadingCommand(true)

    const now = new Date()
    const timeStr = now.toTimeString().split(" ")[0]

    try {
      const res = await fetch("/api/terminal/command", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command: cmdToRun, cwd: "/home/admin" }),
      })

      const data = await res.json()
      setHistory((prev) => [
        ...prev,
        {
          id: Math.random().toString(36).substring(2, 9),
          command: cmdToRun,
          stdout: data.stdout || "",
          stderr: data.stderr || (data.error ? `Error: ${data.error}` : ""),
          exit_code: data.exit_code !== undefined ? data.exit_code : data.error ? 1 : 0,
          timestamp: timeStr,
        },
      ])

      // Refresh telemetry after executing command
      await fetchSystem()
    } catch (err: any) {
      setHistory((prev) => [
        ...prev,
        {
          id: Math.random().toString(36).substring(2, 9),
          command: cmdToRun,
          stdout: "",
          stderr: `Network Error: ${err.message}`,
          exit_code: 1,
          timestamp: timeStr,
        },
      ])
    } finally {
      setLoadingCommand(false)
      setCommandInput("")
      commandInputRef.current?.focus()
    }
  }

  const handleCommandSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    runCommand(commandInput)
  }

  const handleViewFile = async (filePath: string) => {
    setSelectedFile(filePath)
    setLoadingFile(true)
    try {
      const res = await fetch(`/api/terminal/files?path=${encodeURIComponent(filePath)}`)
      if (res.ok) {
        const data = await res.json()
        setFileContent(data.content || data.stdout || "Empty file.")
      }
    } catch (err) {
      setFileContent("Failed to load file content.")
    } finally {
      setLoadingFile(false)
    }
  }

  const handleSubmitRemediation = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!summaryText.trim()) return
    setSubmitting(true)

    try {
      const actions = actionsInput
        .split("\n")
        .map((a) => a.trim())
        .filter(Boolean)

      const res = await fetch("/api/terminal/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ summary: summaryText, actions_taken: actions }),
      })
      const data = await res.json()
      setSubmitResult(data)
      await fetchSystem()
    } catch (err: any) {
      setSubmitResult({ error: err.message })
    } finally {
      setSubmitting(false)
    }
  }

  const diskUsedPercent = systemState?.system?.disk?.used_percent || 96.7
  const memoryTotal = systemState?.system?.memory?.total_mb || 8192
  const memoryUsed = systemState?.system?.memory?.used_mb || 4200
  const memoryPercent = Math.round((memoryUsed / memoryTotal) * 100)
  const isHighDisk = diskUsedPercent > 80
  const paymentSvc = systemState?.services?.find((s: any) => s.name === "payment-processor")
  const isServiceHealthy = paymentSvc?.status === "active"

  return (
    <div className="flex flex-col min-h-screen">
      {/* Top Navbar */}
      <header className="border-b border-slate-800 bg-[#0d1322]/90 backdrop-blur sticky top-0 z-30 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
            <TerminalIcon className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-sm tracking-wide text-white">OpenGym Terminal</span>
              <span className="text-xs px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 font-mono">
                app-node-04.prod.corp
              </span>
              <span
                className={`flex items-center gap-1.5 text-xs px-2 py-0.5 rounded-full font-medium ${
                  isServiceHealthy
                    ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                    : "bg-rose-500/10 text-rose-400 border border-rose-500/30 animate-pulse"
                }`}
              >
                <span className={`w-1.5 h-1.5 rounded-full ${isServiceHealthy ? "bg-emerald-400" : "bg-rose-500"}`} />
                {isServiceHealthy ? "OPERATIONAL" : "SEV-1 INCIDENT"}
              </span>
            </div>
            <p className="text-[11px] text-slate-400">Cluster: us-east-prod-01 • Environment: Linux POSIX Simulator</p>
          </div>
        </div>

        {/* Quick controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={fetchSystem}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh Telemetry
          </button>
          <button
            onClick={() => setActiveTab("submit")}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-medium transition shadow-sm shadow-cyan-600/30"
          >
            <Shield className="w-3.5 h-3.5" />
            Submit Triage Report
          </button>
        </div>
      </header>

      {/* Telemetry Bar */}
      <section className="bg-[#090d16] border-b border-slate-800/80 px-4 py-3">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 max-w-7xl mx-auto">
          {/* CPU Metric */}
          <div className="glass-panel p-3 rounded-lg flex items-center gap-3">
            <div className="w-9 h-9 rounded-md bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400 shrink-0">
              <Cpu className="w-4 h-4" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-400 font-medium">CPU Load</span>
                <span className="font-mono text-amber-400 font-semibold">94.8%</span>
              </div>
              <div className="w-full bg-slate-800 h-1.5 rounded-full mt-1.5 overflow-hidden">
                <div className="bg-amber-500 h-full rounded-full" style={{ width: "94.8%" }} />
              </div>
              <p className="text-[10px] text-slate-400 mt-1 truncate">PID 4921 worker-leak.py runaway</p>
            </div>
          </div>

          {/* Memory Metric */}
          <div className="glass-panel p-3 rounded-lg flex items-center gap-3">
            <div className="w-9 h-9 rounded-md bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400 shrink-0">
              <Activity className="w-4 h-4" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-400 font-medium">Memory Usage</span>
                <span className="font-mono text-blue-400 font-semibold">{memoryPercent}%</span>
              </div>
              <div className="w-full bg-slate-800 h-1.5 rounded-full mt-1.5 overflow-hidden">
                <div className="bg-blue-500 h-full rounded-full" style={{ width: `${memoryPercent}%` }} />
              </div>
              <p className="text-[10px] text-slate-400 mt-1">
                {memoryUsed} MB / {memoryTotal} MB
              </p>
            </div>
          </div>

          {/* Disk Pressure Metric */}
          <div className="glass-panel p-3 rounded-lg flex items-center gap-3">
            <div
              className={`w-9 h-9 rounded-md flex items-center justify-center shrink-0 ${
                isHighDisk
                  ? "bg-rose-500/10 border border-rose-500/30 text-rose-400"
                  : "bg-emerald-500/10 border border-emerald-500/30 text-emerald-400"
              }`}
            >
              <HardDrive className="w-4 h-4" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-400 font-medium">Root Disk</span>
                <span className={`font-mono font-semibold ${isHighDisk ? "text-rose-400" : "text-emerald-400"}`}>
                  {diskUsedPercent.toFixed(1)}%
                </span>
              </div>
              <div className="w-full bg-slate-800 h-1.5 rounded-full mt-1.5 overflow-hidden">
                <div
                  className={`h-full rounded-full ${isHighDisk ? "bg-rose-500" : "bg-emerald-500"}`}
                  style={{ width: `${Math.min(diskUsedPercent, 100)}%` }}
                />
              </div>
              <p className="text-[10px] text-slate-400 mt-1">
                {isHighDisk ? "CRITICAL: Log explosion in /var/log" : "Space optimal"}
              </p>
            </div>
          </div>

          {/* Primary Service Status */}
          <div className="glass-panel p-3 rounded-lg flex items-center gap-3">
            <div
              className={`w-9 h-9 rounded-md flex items-center justify-center shrink-0 ${
                isServiceHealthy
                  ? "bg-emerald-500/10 border border-emerald-500/30 text-emerald-400"
                  : "bg-rose-500/10 border border-rose-500/30 text-rose-400"
              }`}
            >
              <Server className="w-4 h-4" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-400 font-medium">Payment Service</span>
                <span className={`font-mono font-semibold ${isServiceHealthy ? "text-emerald-400" : "text-rose-400"}`}>
                  {isServiceHealthy ? "ACTIVE" : "FAILED"}
                </span>
              </div>
              <p className="text-[11px] font-medium text-slate-200 mt-1 truncate">payment-processor.service</p>
              <p className="text-[10px] text-slate-400 mt-0.5">
                {isServiceHealthy ? "Port 8080 listening" : "Database config & TLS key error"}
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Main Console Workspace */}
      <main className="flex-1 p-4 max-w-7xl mx-auto w-full grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Terminal Screen (Col 7) */}
        <section className="lg:col-span-7 flex flex-col h-[700px] glass-panel rounded-xl overflow-hidden border border-slate-800 shadow-2xl terminal-glow">
          {/* Terminal Titlebar */}
          <div className="bg-[#0f172a] border-b border-slate-800 px-4 py-2.5 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-rose-500/80" />
              <div className="w-3 h-3 rounded-full bg-amber-500/80" />
              <div className="w-3 h-3 rounded-full bg-emerald-500/80" />
              <span className="ml-2 text-xs font-mono text-slate-400">devops@app-node-04: ~ (zsh)</span>
            </div>
            <div className="flex items-center gap-2 text-[11px] text-slate-400 font-mono">
              <span>UTF-8</span>
              <span>•</span>
              <span>PID: 1044</span>
            </div>
          </div>

          {/* Terminal Output Area */}
          <div className="flex-1 overflow-y-auto p-4 font-mono text-xs space-y-4 bg-[#080d19]/95 text-slate-200">
            <div className="text-slate-500 text-[11px] pb-2 border-b border-slate-800/60">
              Authorized Cloud Diagnostics Console • All commands logged to audit journal
            </div>

            {history.map((item) => (
              <div key={item.id} className="space-y-1.5">
                <div className="flex items-center gap-2 text-slate-400">
                  <span className="text-emerald-400 font-semibold">devops@app-node-04</span>
                  <span className="text-slate-600">:</span>
                  <span className="text-cyan-400">~</span>
                  <span className="text-slate-500">$</span>
                  <span className="text-slate-100 font-medium">{item.command}</span>
                  <span className="ml-auto text-[10px] text-slate-600">{item.timestamp}</span>
                </div>

                {item.stdout && (
                  <pre className="p-2.5 rounded bg-black/40 border border-slate-800/80 text-emerald-300 font-mono text-[11px] whitespace-pre-wrap overflow-x-auto leading-relaxed">
                    {item.stdout}
                  </pre>
                )}

                {item.stderr && (
                  <pre className="p-2.5 rounded bg-rose-950/20 border border-rose-900/40 text-rose-300 font-mono text-[11px] whitespace-pre-wrap overflow-x-auto">
                    {item.stderr}
                  </pre>
                )}
              </div>
            ))}

            {loadingCommand && (
              <div className="flex items-center gap-2 text-cyan-400 text-xs py-1">
                <span className="animate-spin">⠋</span>
                <span>Executing on simulated host...</span>
              </div>
            )}

            <div ref={terminalEndRef} />
          </div>

          {/* Quick Helper Chips */}
          <div className="px-3 py-2 bg-[#0b1220] border-t border-slate-800/80 flex items-center gap-1.5 overflow-x-auto text-[11px]">
            <span className="text-slate-500 text-[10px] font-mono mr-1">Quick:</span>
            {[
              "ps aux | grep worker",
              "df -h",
              "systemctl status payment-processor",
              "tail -n 25 /var/log/syslog",
              "kill -9 4921",
              "truncate -s 0 /var/log/app/debug_trace.log",
            ].map((chipCmd) => (
              <button
                key={chipCmd}
                onClick={() => runCommand(chipCmd)}
                className="whitespace-nowrap px-2 py-0.5 rounded bg-slate-800/70 hover:bg-slate-700 text-slate-300 font-mono border border-slate-700/60 transition text-[10px]"
              >
                {chipCmd}
              </button>
            ))}
          </div>

          {/* Interactive Command Input Form */}
          <form onSubmit={handleCommandSubmit} className="bg-[#0a0f1d] border-t border-slate-800 p-2.5 flex items-center gap-2">
            <span className="text-emerald-400 font-mono text-xs font-bold pl-2">devops@app-node-04:~$</span>
            <input
              ref={commandInputRef}
              type="text"
              value={commandInput}
              onChange={(e) => setCommandInput(e.target.value)}
              placeholder="Type Linux shell command (e.g. ps aux, systemctl status payment-processor)..."
              disabled={loadingCommand}
              className="flex-1 bg-transparent text-slate-100 font-mono text-xs focus:outline-none placeholder:text-slate-600"
            />
            <button
              type="submit"
              disabled={loadingCommand || !commandInput.trim()}
              className="px-3 py-1 rounded bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white text-xs font-medium transition flex items-center gap-1"
            >
              <Send className="w-3 h-3" />
              <span>Run</span>
            </button>
          </form>
        </section>

        {/* Right Tabbed Panel (Col 5) */}
        <section className="lg:col-span-5 flex flex-col h-[700px] glass-panel rounded-xl overflow-hidden border border-slate-800">
          {/* Navigation Tabs */}
          <div className="bg-[#0f172a] border-b border-slate-800 px-3 flex items-center gap-2">
            <button
              onClick={() => setActiveTab("monitor")}
              className={`px-3 py-2.5 text-xs font-medium border-b-2 transition flex items-center gap-1.5 ${
                activeTab === "monitor"
                  ? "border-cyan-400 text-cyan-400"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              <Activity className="w-3.5 h-3.5" />
              Services & Procs
            </button>
            <button
              onClick={() => setActiveTab("files")}
              className={`px-3 py-2.5 text-xs font-medium border-b-2 transition flex items-center gap-1.5 ${
                activeTab === "files"
                  ? "border-cyan-400 text-cyan-400"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              <Folder className="w-3.5 h-3.5" />
              File Inspector
            </button>
            <button
              onClick={() => setActiveTab("submit")}
              className={`px-3 py-2.5 text-xs font-medium border-b-2 transition flex items-center gap-1.5 ${
                activeTab === "submit"
                  ? "border-cyan-400 text-cyan-400"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              <Shield className="w-3.5 h-3.5" />
              Triage Report
            </button>
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
            {activeTab === "monitor" && (
              <div className="space-y-4">
                {/* Services Card */}
                <div>
                  <h3 className="text-slate-300 font-semibold text-xs tracking-wider uppercase mb-2 flex items-center gap-1.5">
                    <Server className="w-3.5 h-3.5 text-cyan-400" />
                    Systemd Services
                  </h3>
                  <div className="space-y-2">
                    {systemState?.services?.map((svc: any) => (
                      <div
                        key={svc.name}
                        className="p-2.5 rounded-lg bg-[#0b1220] border border-slate-800 flex items-center justify-between"
                      >
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-slate-200 font-semibold">{svc.name}</span>
                            <span
                              className={`text-[10px] px-1.5 py-0.2 rounded font-medium ${
                                svc.status === "active"
                                  ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                                  : "bg-rose-500/10 text-rose-400 border border-rose-500/30 font-bold"
                              }`}
                            >
                              {svc.status.toUpperCase()}
                            </span>
                          </div>
                          <p className="text-[11px] text-slate-400 mt-0.5">{svc.description}</p>
                        </div>
                        {svc.name === "payment-processor" && (
                          <button
                            onClick={() => runCommand("systemctl restart payment-processor")}
                            className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs border border-slate-700 transition flex items-center gap-1"
                          >
                            <RotateCcw className="w-3 h-3" />
                            Restart
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Processes Table */}
                <div>
                  <h3 className="text-slate-300 font-semibold text-xs tracking-wider uppercase mb-2 flex items-center gap-1.5">
                    <Activity className="w-3.5 h-3.5 text-amber-400" />
                    Top Active Processes
                  </h3>
                  <div className="rounded-lg border border-slate-800 overflow-hidden bg-[#0b1220]">
                    <table className="w-full text-left text-[11px]">
                      <thead className="bg-[#0f172a] text-slate-400 border-b border-slate-800">
                        <tr>
                          <th className="p-2">PID</th>
                          <th className="p-2">User</th>
                          <th className="p-2">CPU%</th>
                          <th className="p-2">Command</th>
                          <th className="p-2 text-right">Action</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60 font-mono">
                        {systemState?.processes?.map((proc: any) => (
                          <tr key={proc.pid} className={proc.pid === 4921 ? "bg-rose-950/20" : ""}>
                            <td className="p-2 text-slate-300 font-semibold">{proc.pid}</td>
                            <td className="p-2 text-slate-400">{proc.user}</td>
                            <td
                              className={`p-2 font-bold ${
                                proc.cpu_percent > 50 ? "text-rose-400" : "text-slate-300"
                              }`}
                            >
                              {proc.cpu_percent}%
                            </td>
                            <td className="p-2 text-slate-300 max-w-[140px] truncate" title={proc.command}>
                              {proc.command}
                            </td>
                            <td className="p-2 text-right">
                              {proc.pid === 4921 && (
                                <button
                                  onClick={() => runCommand("kill -9 4921")}
                                  className="px-2 py-0.5 rounded bg-rose-600 hover:bg-rose-500 text-white text-[10px] font-sans font-medium transition"
                                >
                                  Kill
                                </button>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {activeTab === "files" && (
              <div className="space-y-3">
                <h3 className="text-slate-300 font-semibold text-xs tracking-wider uppercase mb-1 flex items-center gap-1.5">
                  <Folder className="w-3.5 h-3.5 text-cyan-400" />
                  Key Server Files
                </h3>
                <div className="grid grid-cols-1 gap-1.5">
                  {[
                    { path: "/etc/payment-processor/config.yaml", label: "Service DB & SSL Config" },
                    { path: "/etc/ssl/certs/payment-api.key", label: "TLS Private Key (Perms)" },
                    { path: "/var/log/app/debug_trace.log", label: "Runaway Disk Log (18.8MB)" },
                    { path: "/var/log/syslog", label: "System Journal & Log" },
                    { path: "/etc/hosts", label: "Cluster DNS & Hosts" },
                  ].map((f) => (
                    <button
                      key={f.path}
                      onClick={() => handleViewFile(f.path)}
                      className={`text-left p-2 rounded border flex items-center justify-between transition ${
                        selectedFile === f.path
                          ? "bg-cyan-950/30 border-cyan-500/50 text-cyan-200"
                          : "bg-[#0b1220] border-slate-800 text-slate-300 hover:border-slate-700"
                      }`}
                    >
                      <div>
                        <span className="font-mono text-xs font-medium">{f.path}</span>
                        <p className="text-[10px] text-slate-400">{f.label}</p>
                      </div>
                      <Eye className="w-3.5 h-3.5 text-slate-400" />
                    </button>
                  ))}
                </div>

                {selectedFile && (
                  <div className="mt-4 border border-slate-800 rounded-lg overflow-hidden">
                    <div className="bg-[#0f172a] px-3 py-1.5 border-b border-slate-800 flex items-center justify-between text-slate-400 font-mono text-[11px]">
                      <span>{selectedFile}</span>
                      {selectedFile === "/var/log/app/debug_trace.log" && (
                        <button
                          onClick={() => runCommand("truncate -s 0 /var/log/app/debug_trace.log")}
                          className="text-rose-400 hover:text-rose-300 text-[10px] flex items-center gap-1 font-sans"
                        >
                          <Trash2 className="w-3 h-3" /> Truncate
                        </button>
                      )}
                    </div>
                    <pre className="p-3 bg-black/60 font-mono text-[11px] text-slate-300 max-h-[300px] overflow-y-auto whitespace-pre-wrap">
                      {loadingFile ? "Loading..." : fileContent}
                    </pre>
                  </div>
                )}
              </div>
            )}

            {activeTab === "submit" && (
              <div className="space-y-4">
                <div className="p-3 rounded-lg bg-cyan-950/20 border border-cyan-500/30 text-slate-300">
                  <h4 className="font-semibold text-xs text-cyan-300 flex items-center gap-1.5">
                    <Shield className="w-4 h-4" /> Incident Remediation Checklist
                  </h4>
                  <ul className="mt-2 space-y-1 text-[11px] text-slate-400 list-disc list-inside">
                    <li>Terminate rogue runaway process (PID 4921)</li>
                    <li>Reclaim disk pressure (truncate debug_trace.log)</li>
                    <li>Fix database connection in /etc/payment-processor/config.yaml</li>
                    <li>Secure private key permissions (chmod 600)</li>
                    <li>Restart payment-processor service to active</li>
                  </ul>
                </div>

                <form onSubmit={handleSubmitRemediation} className="space-y-3">
                  <div>
                    <label className="block text-slate-300 text-xs font-medium mb-1">
                      Incident Summary & Root Cause
                    </label>
                    <textarea
                      value={summaryText}
                      onChange={(e) => setSummaryText(e.target.value)}
                      rows={3}
                      placeholder="Identified leaking worker process 4921, reclaimed disk space, resolved database connection string to db-primary.internal, secured private key permissions, and restored payment-processor service."
                      className="w-full rounded-lg bg-[#0b1220] border border-slate-800 p-2.5 text-xs text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-cyan-500"
                    />
                  </div>

                  <div>
                    <label className="block text-slate-300 text-xs font-medium mb-1">
                      Actions Taken (one per line)
                    </label>
                    <textarea
                      value={actionsInput}
                      onChange={(e) => setActionsInput(e.target.value)}
                      rows={4}
                      placeholder="kill -9 4921&#10;truncate -s 0 /var/log/app/debug_trace.log&#10;updated config.yaml to db-primary.internal&#10;chmod 600 /etc/ssl/certs/payment-api.key&#10;systemctl restart payment-processor"
                      className="w-full rounded-lg bg-[#0b1220] border border-slate-800 p-2.5 text-xs font-mono text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-cyan-500"
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={submitting || !summaryText.trim()}
                    className="w-full py-2.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white text-xs font-semibold transition shadow-md shadow-cyan-600/30 flex items-center justify-center gap-1.5"
                  >
                    {submitting ? "Submitting..." : "Submit Incident Remediation"}
                  </button>
                </form>

                {submitResult && (
                  <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-xs">
                    <span className="font-semibold text-emerald-400">Submission Recorded:</span>
                    <pre className="mt-1 font-mono text-[10px] text-slate-300 whitespace-pre-wrap">
                      {JSON.stringify(submitResult, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  )
}
