"use client"

import React, { useState, useEffect } from "react"
import {
  Layers,
  Search,
  Filter,
  RefreshCw,
  Plus,
  ArrowRight,
  Shield,
  CheckCircle2,
  AlertCircle,
  Clock,
  ChevronRight,
  User,
  Database,
  ExternalLink,
  Edit2,
  Check,
  X,
  FileText,
  Activity,
  Save,
} from "lucide-react"

export default function ProceduralSaaSConsole() {
  const [schemaData, setSchemaData] = useState<any | null>(null)
  const [domains, setDomains] = useState<string[]>([])
  const [splits, setSplits] = useState<string[]>([])
  const [selectedDomain, setSelectedDomain] = useState("logistics")
  const [selectedSplit, setSelectedSplit] = useState("iid")
  const [actorRole, setActorRole] = useState("admin")
  const [stateHash, setStateHash] = useState("...")

  // Entity Browsing State
  const [selectedEntityName, setSelectedEntityName] = useState<string>("Shipment")
  const [entitiesList, setEntitiesList] = useState<any[]>([])
  const [totalCount, setTotalCount] = useState(0)
  const [searchQuery, setSearchQuery] = useState("")
  const [currentPage, setCurrentPage] = useState(1)
  const [loading, setLoading] = useState(false)

  // Selected Entity Detail & Workflow
  const [selectedEntity, setSelectedEntity] = useState<any | null>(null)
  const [isEditing, setIsEditing] = useState(false)
  const [editFields, setEditFields] = useState<Record<string, any>>({})
  const [transitionMsg, setTransitionMsg] = useState<string | null>(null)

  // Audit Log Drawer
  const [showAuditModal, setShowAuditModal] = useState(false)
  const [auditLogs, setAuditLogs] = useState<any[]>([])

  // Task Submission Modal
  const [isSubmittingTask, setIsSubmittingTask] = useState(false)
  const [taskSummary, setTaskSummary] = useState("")
  const [taskAffectedIds, setTaskAffectedIds] = useState("")
  const [taskSuccessMsg, setTaskSuccessMsg] = useState<string | null>(null)

  // Load schema on mount
  useEffect(() => {
    loadSchema()
  }, [])

  // When selected entity or query changes, reload entities
  useEffect(() => {
    if (selectedEntityName) {
      loadEntities(selectedEntityName, searchQuery, currentPage)
    }
  }, [selectedEntityName, currentPage])

  const loadSchema = async () => {
    try {
      const res = await fetch("/api/software/schema")
      const data = await res.json()
      if (data.ok && data.schema) {
        setSchemaData(data.schema)
        setDomains(data.domains || [])
        setSplits(data.splits || [])
        setSelectedDomain(data.domain || "logistics")
        setSelectedSplit(data.split || "iid")

        const firstEntity = data.schema.entities?.[0]?.name || "Shipment"
        setSelectedEntityName(firstEntity)
        fetchStateHash()
      }
    } catch {}
  }

  const fetchStateHash = async () => {
    try {
      const res = await fetch("/api/software/audit")
      const data = await res.json()
      if (data.ok) {
        setStateHash(data.state_hash?.substring(0, 10) || "ready")
        setAuditLogs(data.audit_log || [])
      }
    } catch {}
  }

  const handleDomainReset = async (newDomain: string, newSplit = selectedSplit) => {
    setLoading(true)
    try {
      await fetch("/api/software/session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "reset", domain: newDomain, split: newSplit, seed: 42 }),
      })
      setSelectedDomain(newDomain)
      setSelectedSplit(newSplit)
      setSelectedEntity(null)
      await loadSchema()
    } finally {
      setLoading(false)
    }
  }

  const loadEntities = async (entity: string, query = "", page = 1) => {
    setLoading(true)
    try {
      const res = await fetch(`/api/software/entities?entity=${entity}&q=${encodeURIComponent(query)}&page=${page}&pageSize=20`)
      const data = await res.json()
      const result = data.result || data
      const items = result.items || result.entities || (Array.isArray(result) ? result : [])
      setEntitiesList(items)
      setTotalCount(result.total || items.length)
      if (items.length > 0 && (!selectedEntity || selectedEntityName !== entity)) {
        setSelectedEntity(items[0])
        setEditFields(items[0])
      }
    } finally {
      setLoading(false)
    }
  }

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setCurrentPage(1)
    loadEntities(selectedEntityName, searchQuery, 1)
  }

  const handleSelectEntityRow = (item: any) => {
    setSelectedEntity(item)
    setEditFields(item)
    setIsEditing(false)
    setTransitionMsg(null)
  }

  const handleFieldChange = (key: string, val: any) => {
    setEditFields((prev) => ({ ...prev, [key]: val }))
  }

  const handleSaveEntity = async () => {
    if (!selectedEntity) return
    const id = selectedEntity.id || selectedEntity[currentEntitySpec?.primary_key || "id"]
    try {
      await fetch("/api/software/entities", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "update", entity_name: selectedEntityName, entity_id: id, fields: editFields }),
      })
      setIsEditing(false)
      loadEntities(selectedEntityName, searchQuery, currentPage)
      fetchStateHash()
    } catch {}
  }

  const handleTriggerTransition = async (action: string) => {
    if (!selectedEntity) return
    const id = selectedEntity.id || selectedEntity[currentEntitySpec?.primary_key || "id"]
    try {
      const res = await fetch("/api/software/transition", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ entity_name: selectedEntityName, entity_id: id, action }),
      })
      const data = await res.json()
      if (data.error) {
        setTransitionMsg(`Error: ${data.error}`)
      } else {
        setTransitionMsg(`Transition '${action}' applied successfully!`)
        loadEntities(selectedEntityName, searchQuery, currentPage)
        // Refresh selected entity
        const updated = await fetch(`/api/software/entities?entity=${selectedEntityName}&id=${id}`).then((r) => r.json())
        if (updated.entity) {
          setSelectedEntity(updated.entity)
          setEditFields(updated.entity)
        }
        fetchStateHash()
      }
    } catch (e: any) {
      setTransitionMsg(`Error: ${e.message}`)
    }
  }

  const submitTaskHandover = async () => {
    try {
      const res = await fetch("/api/software/session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "submit", summary: taskSummary, affected_ids: taskAffectedIds }),
      })
      const data = await res.json()
      if (data.ok) {
        setTaskSuccessMsg("Task submitted to audit trail.")
        setTimeout(() => {
          setIsSubmittingTask(false)
          setTaskSuccessMsg(null)
        }, 2000)
      }
    } catch {}
  }

  const currentEntitySpec = schemaData?.entities?.find((e: any) => e.name === selectedEntityName)
  const currentWorkflow = schemaData?.workflows?.find((w: any) => w.entity_name === selectedEntityName)
  const currentState = selectedEntity?.status || selectedEntity?.state || selectedEntity?.lifecycle_state || ""

  // Available transitions for current entity & state
  const allowedTransitions = currentWorkflow?.transitions?.filter(
    (t: any) => t.from_state === currentState && (actorRole === "admin" || !t.required_roles || t.required_roles.includes(actorRole))
  ) || []

  return (
    <div className="h-screen w-screen flex flex-col bg-[#090d16] text-slate-100 font-sans select-none overflow-hidden">
      {/* 1. Global Navigation Bar */}
      <header className="h-12 bg-slate-900/90 border-b border-slate-800 flex items-center justify-between px-4 z-20 backdrop-blur">
        <div className="flex items-center space-x-3">
          <div className="w-7 h-7 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white shadow">
            <Layers className="w-4 h-4" />
          </div>
          <div>
            <h1 className="font-semibold text-sm text-slate-100 flex items-center space-x-2">
              <span>{schemaData?.name || "Procedural SaaS Console"}</span>
              <span className="text-[10px] px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800 font-mono uppercase">
                {selectedDomain}
              </span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">
                {selectedSplit}
              </span>
            </h1>
          </div>
        </div>

        {/* Controls: Domain Switcher, Role, State Hash, Task Submit */}
        <div className="flex items-center space-x-3 text-xs">
          {/* Domain selector */}
          <div className="flex items-center space-x-1.5 bg-slate-800/80 px-2.5 py-1 rounded border border-slate-700">
            <Database className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={selectedDomain}
              onChange={(e) => handleDomainReset(e.target.value)}
              className="bg-transparent text-slate-200 focus:outline-none cursor-pointer"
            >
              {domains.map((d) => (
                <option key={d} value={d} className="bg-slate-900 text-white">
                  Domain: {d}
                </option>
              ))}
            </select>
          </div>

          {/* Role selector */}
          <div className="flex items-center space-x-1.5 bg-slate-800/80 px-2.5 py-1 rounded border border-slate-700">
            <User className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={actorRole}
              onChange={(e) => setActorRole(e.target.value)}
              className="bg-transparent text-slate-200 focus:outline-none cursor-pointer"
            >
              <option value="admin" className="bg-slate-900">Role: Admin</option>
              <option value="manager" className="bg-slate-900">Role: Manager</option>
              <option value="operator" className="bg-slate-900">Role: Operator</option>
              <option value="auditor" className="bg-slate-900">Role: Auditor</option>
            </select>
          </div>

          {/* State hash badge */}
          <div className="flex items-center space-x-1 bg-slate-800/80 px-2.5 py-1 rounded border border-slate-700 font-mono text-slate-300">
            <Shield className="w-3.5 h-3.5 text-emerald-400" />
            <span>SHA: {stateHash}</span>
          </div>

          <button
            onClick={() => setShowAuditModal(true)}
            className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 font-medium transition flex items-center space-x-1"
          >
            <Activity className="w-3.5 h-3.5 text-sky-400" />
            <span>Audit Trail</span>
          </button>

          <button
            onClick={() => setIsSubmittingTask(true)}
            className="px-3 py-1 bg-indigo-600 hover:bg-indigo-500 text-white rounded font-medium shadow flex items-center space-x-1 transition"
          >
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Submit Task</span>
          </button>
        </div>
      </header>

      {/* 2. Main Workspace */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar: Entities Navigation */}
        <aside className="w-56 bg-slate-900/60 border-r border-slate-800 flex flex-col">
          <div className="p-3 border-b border-slate-800 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            Application Entities
          </div>
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {schemaData?.entities?.map((ent: any) => {
              const isSelected = selectedEntityName === ent.name
              return (
                <button
                  key={ent.name}
                  onClick={() => {
                    setSelectedEntityName(ent.name)
                    setCurrentPage(1)
                    setSearchQuery("")
                  }}
                  className={`w-full text-left px-3 py-2 rounded-lg text-xs font-medium flex items-center justify-between transition ${
                    isSelected
                      ? "bg-indigo-600 text-white shadow"
                      : "text-slate-300 hover:bg-slate-800/60 hover:text-white"
                  }`}
                >
                  <div className="truncate">{ent.plural_name || ent.name}</div>
                  <ChevronRight className={`w-3.5 h-3.5 ${isSelected ? "text-white" : "text-slate-500"}`} />
                </button>
              )
            })}
          </div>
          <div className="p-3 border-t border-slate-800 text-[11px] text-slate-500">
            Layout: <span className="font-mono text-slate-400">{schemaData?.layout?.layout_family || "sidebar_table"}</span>
          </div>
        </aside>

        {/* Center: Search, Filter, Data Grid */}
        <section className="flex-1 flex flex-col overflow-hidden bg-slate-950/40">
          {/* Top Filter & Action Bar */}
          <div className="h-12 border-b border-slate-800 flex items-center justify-between px-4 bg-slate-900/30">
            <form onSubmit={handleSearchSubmit} className="flex items-center space-x-2 flex-1 max-w-md">
              <div className="relative flex-1">
                <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-2.5" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder={`Search ${currentEntitySpec?.plural_name || "records"}...`}
                  className="w-full bg-slate-900 border border-slate-700/80 rounded-md pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>
              <button
                type="submit"
                className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded text-xs font-medium border border-slate-700 transition"
              >
                Search
              </button>
            </form>

            <div className="text-xs text-slate-400">
              Showing {entitiesList.length} of {totalCount} records
            </div>
          </div>

          {/* Dynamic Table */}
          <div className="flex-1 overflow-auto">
            {loading ? (
              <div className="flex items-center justify-center h-full text-slate-500 text-xs">
                <RefreshCw className="w-4 h-4 animate-spin mr-2" /> Loading records...
              </div>
            ) : entitiesList.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-slate-500 text-xs space-y-1">
                <FileText className="w-6 h-6 text-slate-600" />
                <span>No records found for {selectedEntityName}.</span>
              </div>
            ) : (
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-900/80 border-b border-slate-800 text-slate-400 font-medium sticky top-0 backdrop-blur z-10">
                    {currentEntitySpec?.fields?.slice(0, 6).map((f: any) => (
                      <th key={f.name} className="py-2.5 px-3 uppercase text-[10px] tracking-wider">
                        {f.name.replace(/_/g, " ")}
                      </th>
                    ))}
                    <th className="py-2.5 px-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                  {entitiesList.map((row: any, idx: number) => {
                    const id = row.id || row[currentEntitySpec?.primary_key || "id"] || idx
                    const isSelected = selectedEntity && (selectedEntity.id === row.id || selectedEntity === row)

                    return (
                      <tr
                        key={id}
                        onClick={() => handleSelectEntityRow(row)}
                        className={`cursor-pointer transition ${
                          isSelected ? "bg-indigo-950/40 border-l-2 border-indigo-500" : "hover:bg-slate-900/50"
                        }`}
                      >
                        {currentEntitySpec?.fields?.slice(0, 6).map((f: any) => {
                          const val = row[f.name]
                          const isStatus = f.name === "status" || f.name === "state"
                          return (
                            <td key={f.name} className="py-2.5 px-3 truncate max-w-[180px]">
                              {isStatus ? (
                                <span className="px-2 py-0.5 rounded-full text-[10px] uppercase font-semibold bg-indigo-950 text-indigo-300 border border-indigo-800">
                                  {String(val || "N/A")}
                                </span>
                              ) : typeof val === "object" ? (
                                JSON.stringify(val)
                              ) : (
                                String(val ?? "—")
                              )}
                            </td>
                          )
                        })}
                        <td className="py-2.5 px-3 text-right">
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              handleSelectEntityRow(row)
                              setIsEditing(true)
                            }}
                            className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-[10px] font-sans"
                          >
                            Inspect
                          </button>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            )}
          </div>
        </section>

        {/* Right Drawer: Entity Detail, Field Editor, and Workflow Action Bar */}
        {selectedEntity && (
          <aside className="w-96 bg-slate-900/80 border-l border-slate-800 flex flex-col overflow-hidden">
            {/* Header */}
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <div>
                <span className="text-[10px] text-slate-500 uppercase font-mono">{selectedEntityName} ID</span>
                <h3 className="font-semibold text-slate-100 text-sm truncate max-w-[200px]">
                  {selectedEntity.id || selectedEntity.name || "Entity Record"}
                </h3>
              </div>
              <div className="flex space-x-1">
                {isEditing ? (
                  <button
                    onClick={handleSaveEntity}
                    className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-medium flex items-center space-x-1"
                  >
                    <Save className="w-3 h-3" />
                    <span>Save</span>
                  </button>
                ) : (
                  <button
                    onClick={() => setIsEditing(true)}
                    className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs font-medium flex items-center space-x-1 border border-slate-700"
                  >
                    <Edit2 className="w-3 h-3" />
                    <span>Edit</span>
                  </button>
                )}
              </div>
            </div>

            {/* Workflow Transition Action Bar */}
            {currentWorkflow && (
              <div className="p-3 bg-indigo-950/30 border-b border-indigo-900/40 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-400">Current State:</span>
                  <span className="px-2 py-0.5 rounded text-[10px] uppercase font-semibold bg-indigo-900 text-indigo-200">
                    {currentState || "initial"}
                  </span>
                </div>

                {allowedTransitions.length > 0 ? (
                  <div className="space-y-1.5 pt-1">
                    <span className="text-[10px] text-slate-400 font-medium block">Allowed Workflow Transitions:</span>
                    <div className="flex flex-wrap gap-1.5">
                      {allowedTransitions.map((t: any) => (
                        <button
                          key={t.name}
                          onClick={() => handleTriggerTransition(t.name)}
                          className="px-2.5 py-1 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-[11px] font-medium flex items-center space-x-1 shadow transition"
                        >
                          <span>{t.name.replace(/_/g, " ")}</span>
                          <ArrowRight className="w-3 h-3 text-indigo-200" />
                        </button>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="text-[11px] text-slate-500 italic">No transitions available from state '{currentState}' for role '{actorRole}'.</div>
                )}

                {transitionMsg && (
                  <div className="text-[11px] p-2 rounded bg-slate-900 border border-indigo-800 text-indigo-300">
                    {transitionMsg}
                  </div>
                )}
              </div>
            )}

            {/* Fields List / Editor */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3 text-xs">
              <div className="font-semibold text-slate-300 text-xs uppercase tracking-wider mb-2">Entity Fields</div>
              {currentEntitySpec?.fields?.map((f: any) => {
                const val = isEditing ? editFields[f.name] : selectedEntity[f.name]
                return (
                  <div key={f.name} className="space-y-1">
                    <label className="text-slate-400 font-medium block capitalize">
                      {f.name.replace(/_/g, " ")} {f.required && <span className="text-rose-400">*</span>}
                    </label>
                    {isEditing ? (
                      f.type === "enum" ? (
                        <select
                          value={val || ""}
                          onChange={(e) => handleFieldChange(f.name, e.target.value)}
                          className="w-full bg-slate-800 border border-slate-700 rounded p-1.5 text-xs text-white"
                        >
                          {f.enum_values?.map((ev: string) => (
                            <option key={ev} value={ev}>
                              {ev}
                            </option>
                          ))}
                        </select>
                      ) : (
                        <input
                          type={f.type === "integer" || f.type === "float" ? "number" : "text"}
                          value={val ?? ""}
                          onChange={(e) => handleFieldChange(f.name, e.target.value)}
                          className="w-full bg-slate-800 border border-slate-700 rounded p-1.5 text-xs text-white"
                        />
                      )
                    ) : (
                      <div className="bg-slate-900/60 border border-slate-800/80 rounded p-2 text-slate-200 font-mono text-[11px] break-all">
                        {String(val ?? "—")}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </aside>
        )}
      </div>

      {/* 3. Audit Log Modal */}
      {showAuditModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-2xl w-full p-5 space-y-4 shadow-2xl flex flex-col max-h-[80vh]">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-2 font-semibold text-slate-100">
                <Activity className="w-5 h-5 text-indigo-400" />
                <span>Procedural Application Audit Trail</span>
              </div>
              <button onClick={() => setShowAuditModal(false)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-2 text-xs font-mono">
              {auditLogs.length === 0 ? (
                <div className="text-slate-500 p-4 text-center">No audit records logged yet.</div>
              ) : (
                auditLogs.map((log: any, i: number) => (
                  <div key={i} className="p-2.5 rounded bg-slate-950/60 border border-slate-800 space-y-1">
                    <div className="flex items-center justify-between text-slate-400 text-[10px]">
                      <span className="text-indigo-400 font-semibold">{log.action}</span>
                      <span>{log.timestamp || log.timestamp_iso || "2026-10-15"}</span>
                    </div>
                    <div className="text-slate-300 text-[11px]">
                      {log.entity_name} [{log.entity_id}] by {log.actor || "operator"} ({log.role || "admin"})
                    </div>
                    {log.details && (
                      <div className="text-slate-500 text-[10px] truncate">{JSON.stringify(log.details)}</div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* 4. Submit Task Modal */}
      {isSubmittingTask && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-5 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 font-semibold text-slate-100">
                <CheckCircle2 className="w-5 h-5 text-indigo-400" />
                <span>Submit Software Task Handover</span>
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
                  Submitting formal completion logs your structured report and affected IDs to the application audit log.
                </p>
                <div>
                  <label className="text-slate-300 font-medium block mb-1">Execution Summary:</label>
                  <textarea
                    rows={3}
                    value={taskSummary}
                    onChange={(e) => setTaskSummary(e.target.value)}
                    placeholder="Describe completed actions (e.g. Dispatched pending shipments, cleared transit exceptions, updated depot assignments)..."
                    className="w-full bg-slate-800 border border-slate-700 rounded p-2 text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="text-slate-300 font-medium block mb-1">Affected Entity IDs (comma-separated):</label>
                  <input
                    type="text"
                    value={taskAffectedIds}
                    onChange={(e) => setTaskAffectedIds(e.target.value)}
                    placeholder="e.g. SHP-1001, EXC-2001, DEPOT-01"
                    className="w-full bg-slate-800 border border-slate-700 rounded p-2 text-white focus:outline-none focus:border-indigo-500"
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
                    className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded font-medium"
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
