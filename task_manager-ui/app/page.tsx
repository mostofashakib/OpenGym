"use client"

import React, { useState, useEffect } from "react"
import {
  Kanban,
  List,
  CheckCircle2,
  AlertCircle,
  Clock,
  Filter,
  Search,
  ChevronDown,
  X,
  ExternalLink,
  ShieldCheck,
  RotateCcw,
  RefreshCw,
  FolderGit2,
  ArrowRight,
  GitBranch,
  AlertTriangle,
  Send,
  SlidersHorizontal,
  User,
  Tag,
} from "lucide-react"

interface Task {
  task_id: string
  title: string
  description: string
  status: "PENDING" | "IN_PROGRESS" | "BLOCKED" | "COMPLETED" | "CANCELLED"
  priority: "LOW" | "MEDIUM" | "HIGH" | "URGENT"
  project_id: string
  milestone_id?: string
  assignee_id?: string | null
  labels?: string[]
  depends_on?: string[]
  required_by?: string[]
}

interface Project {
  project_id: string
  name: string
  description?: string
}

export default function TaskManagerPage() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [projects, setProjects] = useState<Project[]>([])
  const [selectedProject, setSelectedProject] = useState<string>("P005") // Titanium Enterprise v3.0
  const [selectedMilestone, setSelectedMilestone] = useState<string>("M006") // v3.0 Cutover Gate
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState("")
  const [viewMode, setViewMode] = useState<"kanban" | "list">("kanban")

  // Detail Drawer
  const [activeTask, setActiveTask] = useState<Task | null>(null)
  const [loadingTaskDetail, setLoadingTaskDetail] = useState(false)

  // Handover Modal
  const [showHandoverModal, setShowHandoverModal] = useState(false)
  const [handoverSummary, setHandoverSummary] = useState(
    "Titanium v3.0 Cutover Gate Reconciled: DR replication drills verified, token revocation concurrency resolved, circular dependencies between cache recovery unblocked, and operational runbook approved."
  )
  const [selectedTaskIds, setSelectedTaskIds] = useState<string[]>([
    "TASK037",
    "TASK038",
    "TASK039",
    "TASK040",
    "TASK041",
    "TASK042",
    "TASK043",
    "TASK044",
    "TASK048",
    "TASK051",
    "TASK052",
  ])
  const [handoverStatus, setHandoverStatus] = useState<string | null>(null)
  const [submittingHandover, setSubmittingHandover] = useState(false)

  const fetchTasks = async () => {
    try {
      setLoading(true)
      let url = `/api/tasks?project_id=${selectedProject}`
      if (selectedMilestone) {
        url += `&milestone_id=${selectedMilestone}`
      }
      const res = await fetch(url)
      if (res.ok) {
        const data = await res.json()
        setTasks(data.tasks || [])
      }
    } catch (err) {
      console.error("Failed to load tasks", err)
    } finally {
      setLoading(false)
    }
  }

  const fetchProjects = async () => {
    try {
      const res = await fetch("/api/projects")
      if (res.ok) {
        const data = await res.json()
        setProjects(data.projects || [])
      }
    } catch (err) {
      console.error("Failed to load projects", err)
    }
  }

  const openTaskDetail = async (taskId: string) => {
    try {
      setLoadingTaskDetail(true)
      const res = await fetch(`/api/tasks/${taskId}`)
      if (res.ok) {
        const data = await res.json()
        setActiveTask(data)
      }
    } catch (err) {
      console.error("Failed to fetch task details", err)
    } finally {
      setLoadingTaskDetail(false)
    }
  }

  const updateTaskStatus = async (taskId: string, newStatus: string) => {
    try {
      const res = await fetch(`/api/tasks/${taskId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus }),
      })
      if (res.ok) {
        await fetchTasks()
        if (activeTask && activeTask.task_id === taskId) {
          await openTaskDetail(taskId)
        }
      }
    } catch (err) {
      console.error("Failed to update task", err)
    }
  }

  const handleSubmitHandover = async () => {
    try {
      setSubmittingHandover(true)
      const res = await fetch("/api/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          task_ids: selectedTaskIds,
          summary: handoverSummary,
        }),
      })
      if (res.ok) {
        setHandoverStatus("Report submitted successfully!")
        setShowHandoverModal(false)
        await fetchTasks()
      }
    } catch (err: any) {
      setHandoverStatus(`Error: ${err.message}`)
    } finally {
      setSubmittingHandover(false)
    }
  }

  useEffect(() => {
    fetchProjects()
  }, [])

  useEffect(() => {
    fetchTasks()
  }, [selectedProject, selectedMilestone])

  const filteredTasks = tasks.filter((t) => {
    if (!searchQuery.trim()) return true
    const q = searchQuery.toLowerCase()
    return (
      t.title.toLowerCase().includes(q) ||
      t.task_id.toLowerCase().includes(q) ||
      t.description.toLowerCase().includes(q)
    )
  })

  const blockedCount = tasks.filter((t) => t.status === "BLOCKED").length
  const completedCount = tasks.filter((t) => t.status === "COMPLETED").length
  const inProgressCount = tasks.filter((t) => t.status === "IN_PROGRESS").length
  const pendingCount = tasks.filter((t) => t.status === "PENDING").length

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#0d1117]">
      {/* 1. Left Sidebar */}
      <aside className="w-64 bg-[#161b22] border-r border-[#30363d] flex flex-col shrink-0 select-none">
        <div className="p-3.5 border-b border-[#30363d] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white text-sm shadow">
              T
            </div>
            <div>
              <span className="font-bold text-sm text-white tracking-tight">Titanium Tracker</span>
              <p className="text-[10px] text-slate-400">Release Gate Engineering</p>
            </div>
          </div>
          <button
            onClick={fetchTasks}
            title="Refresh"
            className="p-1 rounded hover:bg-[#30363d] text-slate-400 hover:text-white transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>

        {/* Project Selector */}
        <div className="p-2 border-b border-[#30363d]">
          <label className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block px-1 mb-1">
            Projects
          </label>
          <div className="space-y-0.5">
            {projects.map((p) => {
              const isSelected = selectedProject === p.project_id
              return (
                <button
                  key={p.project_id}
                  onClick={() => setSelectedProject(p.project_id)}
                  className={`w-full text-left px-2.5 py-1.5 rounded-md text-xs font-medium flex items-center gap-2 transition ${
                    isSelected
                      ? "bg-[#1f6feb]/20 text-[#58a6ff] border border-[#1f6feb]/40"
                      : "text-slate-300 hover:bg-[#21262d]"
                  }`}
                >
                  <FolderGit2 className="w-3.5 h-3.5 shrink-0 opacity-70" />
                  <span className="truncate">{p.name}</span>
                </button>
              )
            })}
          </div>
        </div>

        {/* Milestones Filter */}
        <div className="p-2 border-b border-[#30363d] space-y-1">
          <label className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block px-1">
            Milestones
          </label>
          <button
            onClick={() => setSelectedMilestone("M006")}
            className={`w-full text-left px-2.5 py-1.5 rounded-md text-xs font-medium flex items-center justify-between transition ${
              selectedMilestone === "M006"
                ? "bg-[#238636]/20 text-[#3fb950] border border-[#238636]/40"
                : "text-slate-300 hover:bg-[#21262d]"
            }`}
          >
            <span className="truncate">v3.0 Cutover Gate</span>
            <span className="text-[10px] px-1.5 rounded bg-black/40 text-slate-400">M006</span>
          </button>
          <button
            onClick={() => setSelectedMilestone("")}
            className={`w-full text-left px-2.5 py-1.5 rounded-md text-xs font-medium flex items-center justify-between transition ${
              selectedMilestone === ""
                ? "bg-[#1f6feb]/20 text-[#58a6ff] border border-[#1f6feb]/40"
                : "text-slate-300 hover:bg-[#21262d]"
            }`}
          >
            <span className="truncate">All Milestones</span>
            <span className="text-[10px] px-1.5 rounded bg-black/40 text-slate-400">All</span>
          </button>
        </div>

        {/* Views switcher */}
        <div className="flex-1 p-2 space-y-0.5">
          <label className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block px-1 mb-1">
            Views
          </label>
          <button
            onClick={() => setViewMode("kanban")}
            className={`w-full text-left px-2.5 py-1.5 rounded-md text-xs font-medium flex items-center gap-2 transition ${
              viewMode === "kanban"
                ? "bg-[#21262d] text-white"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Kanban className="w-3.5 h-3.5" />
            <span>Kanban Board</span>
          </button>
          <button
            onClick={() => setViewMode("list")}
            className={`w-full text-left px-2.5 py-1.5 rounded-md text-xs font-medium flex items-center gap-2 transition ${
              viewMode === "list"
                ? "bg-[#21262d] text-white"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <List className="w-3.5 h-3.5" />
            <span>List Table</span>
          </button>
        </div>

        {/* Footer User Card */}
        <div className="p-3 border-t border-[#30363d] bg-[#0d1117] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-full bg-indigo-600 flex items-center justify-center text-white text-xs font-bold">
              RL
            </div>
            <div>
              <p className="text-xs font-semibold text-white">Lead SRE Auditor</p>
              <p className="text-[10px] text-slate-400">Cutover Gate Officer</p>
            </div>
          </div>
          <span className="w-2 h-2 rounded-full bg-emerald-400" />
        </div>
      </aside>

      {/* 2. Main Content Workspace */}
      <main className="flex-1 flex flex-col min-w-0 bg-[#0d1117]">
        {/* Top Navigation Bar */}
        <header className="px-6 py-3 border-b border-[#30363d] bg-[#161b22] flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="font-bold text-sm text-white">
              {selectedMilestone === "M006" ? "Milestone: v3.0 Cutover Gate" : "Project Tasks"}
            </h1>
            {/* Quick Metrics Badges */}
            <div className="flex items-center gap-2 text-xs">
              <span className="px-2 py-0.5 rounded-full bg-rose-950/40 text-rose-300 border border-rose-800/40 font-semibold flex items-center gap-1">
                <AlertTriangle className="w-3 h-3" /> {blockedCount} Blocked
              </span>
              <span className="px-2 py-0.5 rounded-full bg-blue-950/40 text-blue-300 border border-blue-800/40 font-semibold">
                {inProgressCount} In Progress
              </span>
              <span className="px-2 py-0.5 rounded-full bg-emerald-950/40 text-emerald-300 border border-emerald-800/40 font-semibold flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" /> {completedCount} Done
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Search Input */}
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-slate-500" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Filter tasks by key or text..."
                className="bg-[#0d1117] border border-[#30363d] rounded-lg pl-8 pr-3 py-1.5 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-indigo-500 w-64"
              />
            </div>

            {/* Handover Action */}
            <button
              onClick={() => setShowHandoverModal(true)}
              className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition flex items-center gap-1.5 shadow-sm shadow-indigo-600/30"
            >
              <ShieldCheck className="w-4 h-4" />
              Submit Cutover Handover
            </button>
          </div>
        </header>

        {/* Handover Alert Notification */}
        {handoverStatus && (
          <div className="bg-emerald-950/40 border-b border-emerald-800/50 px-6 py-2 flex items-center justify-between text-xs text-emerald-300">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>{handoverStatus}</span>
            </div>
            <button onClick={() => setHandoverStatus(null)} className="text-slate-400 hover:text-white">
              Dismiss
            </button>
          </div>
        )}

        {/* 3. Task Views: Kanban vs List */}
        <div className="flex-1 overflow-auto p-6">
          {viewMode === "kanban" ? (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 h-full">
              {/* Column: BLOCKED */}
              <div className="flex flex-col bg-[#161b22]/50 border border-rose-900/30 rounded-xl p-3">
                <div className="flex items-center justify-between pb-2 mb-3 border-b border-[#30363d]">
                  <span className="text-xs font-bold text-rose-400 flex items-center gap-1.5">
                    <AlertTriangle className="w-3.5 h-3.5" /> BLOCKED ({blockedCount})
                  </span>
                </div>
                <div className="flex-1 overflow-y-auto space-y-2.5">
                  {filteredTasks
                    .filter((t) => t.status === "BLOCKED")
                    .map((t) => (
                      <TaskCard key={t.task_id} task={t} onSelect={() => openTaskDetail(t.task_id)} />
                    ))}
                </div>
              </div>

              {/* Column: PENDING */}
              <div className="flex flex-col bg-[#161b22]/50 border border-[#30363d] rounded-xl p-3">
                <div className="flex items-center justify-between pb-2 mb-3 border-b border-[#30363d]">
                  <span className="text-xs font-bold text-amber-400 flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5" /> PENDING ({pendingCount})
                  </span>
                </div>
                <div className="flex-1 overflow-y-auto space-y-2.5">
                  {filteredTasks
                    .filter((t) => t.status === "PENDING")
                    .map((t) => (
                      <TaskCard key={t.task_id} task={t} onSelect={() => openTaskDetail(t.task_id)} />
                    ))}
                </div>
              </div>

              {/* Column: IN_PROGRESS */}
              <div className="flex flex-col bg-[#161b22]/50 border border-[#30363d] rounded-xl p-3">
                <div className="flex items-center justify-between pb-2 mb-3 border-b border-[#30363d]">
                  <span className="text-xs font-bold text-blue-400 flex items-center gap-1.5">
                    <GitBranch className="w-3.5 h-3.5" /> IN PROGRESS ({inProgressCount})
                  </span>
                </div>
                <div className="flex-1 overflow-y-auto space-y-2.5">
                  {filteredTasks
                    .filter((t) => t.status === "IN_PROGRESS")
                    .map((t) => (
                      <TaskCard key={t.task_id} task={t} onSelect={() => openTaskDetail(t.task_id)} />
                    ))}
                </div>
              </div>

              {/* Column: COMPLETED */}
              <div className="flex flex-col bg-[#161b22]/50 border border-emerald-900/30 rounded-xl p-3">
                <div className="flex items-center justify-between pb-2 mb-3 border-b border-[#30363d]">
                  <span className="text-xs font-bold text-emerald-400 flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5" /> COMPLETED ({completedCount})
                  </span>
                </div>
                <div className="flex-1 overflow-y-auto space-y-2.5">
                  {filteredTasks
                    .filter((t) => t.status === "COMPLETED")
                    .map((t) => (
                      <TaskCard key={t.task_id} task={t} onSelect={() => openTaskDetail(t.task_id)} />
                    ))}
                </div>
              </div>
            </div>
          ) : (
            /* List View */
            <div className="bg-[#161b22] border border-[#30363d] rounded-xl overflow-hidden">
              <table className="w-full text-left text-xs">
                <thead className="bg-[#0d1117] text-slate-400 border-b border-[#30363d] uppercase tracking-wider text-[10px]">
                  <tr>
                    <th className="p-3">Key</th>
                    <th className="p-3">Title</th>
                    <th className="p-3">Status</th>
                    <th className="p-3">Priority</th>
                    <th className="p-3">Assignee</th>
                    <th className="p-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#30363d]/60">
                  {filteredTasks.map((t) => (
                    <tr
                      key={t.task_id}
                      onClick={() => openTaskDetail(t.task_id)}
                      className="hover:bg-[#21262d] cursor-pointer transition"
                    >
                      <td className="p-3 font-mono font-bold text-indigo-400">{t.task_id}</td>
                      <td className="p-3 font-medium text-white">{t.title}</td>
                      <td className="p-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            t.status === "COMPLETED"
                              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                              : t.status === "BLOCKED"
                              ? "bg-rose-500/10 text-rose-400 border border-rose-500/30"
                              : "bg-blue-500/10 text-blue-400 border border-blue-500/30"
                          }`}
                        >
                          {t.status}
                        </span>
                      </td>
                      <td className="p-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-semibold priority-${t.priority.toLowerCase()}`}>
                          {t.priority}
                        </span>
                      </td>
                      <td className="p-3 text-slate-400 font-mono">{t.assignee_id || "Unassigned"}</td>
                      <td className="p-3 text-right">
                        <button className="text-slate-400 hover:text-white text-xs">View</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>

      {/* 4. Task Detail Drawer */}
      {activeTask && (
        <aside className="w-96 bg-[#161b22] border-l border-[#30363d] flex flex-col shrink-0">
          <div className="p-3.5 border-b border-[#30363d] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="font-mono font-bold text-xs text-indigo-400">{activeTask.task_id}</span>
              <span className={`text-[10px] px-2 py-0.5 rounded priority-${activeTask.priority.toLowerCase()}`}>
                {activeTask.priority}
              </span>
            </div>
            <button
              onClick={() => setActiveTask(null)}
              className="p-1 rounded hover:bg-[#30363d] text-slate-400 hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
            <div>
              <h3 className="font-bold text-sm text-white leading-snug">{activeTask.title}</h3>
              <p className="text-slate-300 mt-2 leading-relaxed bg-[#0d1117] p-3 rounded-lg border border-[#30363d]">
                {activeTask.description}
              </p>
            </div>

            {/* Status Selector */}
            <div>
              <label className="block text-slate-400 text-[11px] font-medium mb-1">Update Status</label>
              <div className="grid grid-cols-2 gap-1.5">
                {(["PENDING", "IN_PROGRESS", "BLOCKED", "COMPLETED"] as const).map((st) => (
                  <button
                    key={st}
                    onClick={() => updateTaskStatus(activeTask.task_id, st)}
                    className={`py-1.5 px-2 rounded text-[11px] font-semibold border transition ${
                      activeTask.status === st
                        ? "bg-indigo-600 text-white border-indigo-500"
                        : "bg-[#0d1117] text-slate-400 border-[#30363d] hover:border-slate-500"
                    }`}
                  >
                    {st}
                  </button>
                ))}
              </div>
            </div>

            {/* Dependencies */}
            <div className="space-y-2 pt-2 border-t border-[#30363d]">
              <span className="text-slate-400 font-semibold text-[11px] uppercase tracking-wider block">
                Upstream Dependencies (depends_on)
              </span>
              {activeTask.depends_on && activeTask.depends_on.length > 0 ? (
                <div className="space-y-1">
                  {activeTask.depends_on.map((depId) => (
                    <div
                      key={depId}
                      onClick={() => openTaskDetail(depId)}
                      className="p-2 rounded bg-[#0d1117] border border-[#30363d] text-slate-300 flex items-center justify-between cursor-pointer hover:border-indigo-500 transition"
                    >
                      <span className="font-mono text-indigo-400">{depId}</span>
                      <ArrowRight className="w-3 h-3 text-slate-500" />
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-slate-500 italic text-[11px]">No upstream dependencies.</p>
              )}
            </div>

            {/* Dependents */}
            <div className="space-y-2 pt-2 border-t border-[#30363d]">
              <span className="text-slate-400 font-semibold text-[11px] uppercase tracking-wider block">
                Required By (required_by)
              </span>
              {activeTask.required_by && activeTask.required_by.length > 0 ? (
                <div className="space-y-1">
                  {activeTask.required_by.map((reqId) => (
                    <div
                      key={reqId}
                      onClick={() => openTaskDetail(reqId)}
                      className="p-2 rounded bg-[#0d1117] border border-[#30363d] text-slate-300 flex items-center justify-between cursor-pointer hover:border-indigo-500 transition"
                    >
                      <span className="font-mono text-indigo-400">{reqId}</span>
                      <ArrowRight className="w-3 h-3 text-slate-500" />
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-slate-500 italic text-[11px]">No downstream tasks waiting on this.</p>
              )}
            </div>
          </div>
        </aside>
      )}

      {/* 5. Cutover Handover Modal */}
      {showHandoverModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#161b22] border border-indigo-700 max-w-xl w-full rounded-xl p-5 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-[#30363d] pb-3">
              <div className="flex items-center gap-2 text-white">
                <ShieldCheck className="w-5 h-5 text-indigo-400" />
                <h3 className="font-bold text-sm">Submit Release Handover Report</h3>
              </div>
              <button
                onClick={() => setShowHandoverModal(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              Record the outcome of your cutover gate reconciliation. Specify the reconciled task IDs and your technical cutover rationale.
            </p>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Executive Cutover Rationale & Recommendation
              </label>
              <textarea
                value={handoverSummary}
                onChange={(e) => setHandoverSummary(e.target.value)}
                rows={4}
                className="w-full bg-[#0d1117] border border-[#30363d] rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 leading-relaxed font-sans"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Reconciled Task IDs (comma separated)
              </label>
              <input
                type="text"
                value={selectedTaskIds.join(", ")}
                onChange={(e) =>
                  setSelectedTaskIds(
                    e.target.value
                      .split(",")
                      .map((s) => s.trim())
                      .filter(Boolean)
                  )
                }
                className="w-full bg-[#0d1117] border border-[#30363d] rounded-lg p-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-[#30363d]">
              <button
                onClick={() => setShowHandoverModal(false)}
                className="px-3 py-1.5 rounded bg-slate-800 text-slate-300 text-xs hover:bg-slate-700"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmitHandover}
                disabled={submittingHandover}
                className="px-4 py-1.5 rounded bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/30 flex items-center gap-1.5"
              >
                <Send className="w-3.5 h-3.5" />
                <span>{submittingHandover ? "Submitting..." : "Submit Handover Report"}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function TaskCard({ task, onSelect }: { task: Task; onSelect: () => void }) {
  return (
    <div
      onClick={onSelect}
      className="linear-card p-3 rounded-lg cursor-pointer space-y-2 select-none"
    >
      <div className="flex items-center justify-between">
        <span className="font-mono text-[11px] font-bold text-indigo-400">{task.task_id}</span>
        <span className={`text-[9px] px-1.5 py-0.2 rounded font-semibold priority-${task.priority.toLowerCase()}`}>
          {task.priority}
        </span>
      </div>
      <p className="text-xs font-medium text-white line-clamp-2 leading-snug">{task.title}</p>
      <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1 border-t border-[#30363d]/60">
        <span className="font-mono">{task.assignee_id || "Unassigned"}</span>
        {task.labels && task.labels.length > 0 && (
          <span className="px-1.5 py-0.2 rounded bg-black/40 text-slate-400">
            {task.labels[0]}
          </span>
        )}
      </div>
    </div>
  )
}
