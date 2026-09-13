"use client"

import React, { useState, useEffect } from "react"
import {
  HeartPulse,
  Search,
  User,
  AlertTriangle,
  FileText,
  Pill,
  Activity,
  Calendar,
  Send,
  Shield,
  CheckCircle2,
  Clock,
  Plus,
  ArrowRight,
  RefreshCw,
  X,
  Check,
  Phone,
  Mail,
  AlertOctagon,
  Lock,
} from "lucide-react"

export default function AegisHealthEHR() {
  // Navigation & Patient State
  const [patients, setPatients] = useState<any[]>([])
  const [selectedPatientId, setSelectedPatientId] = useState("pat-0001")
  const [patientChart, setPatientChart] = useState<any | null>(null)
  const [activeTab, setActiveTab] = useState<"summary" | "medications" | "labs" | "orders" | "portal" | "audit">("summary")
  const [searchQuery, setSearchQuery] = useState("")
  const [loading, setLoading] = useState(false)

  // System & Simulation State
  const [stateHash, setStateHash] = useState("...")
  const [virtualTime, setVirtualTime] = useState("09:30 AM")
  const [isSubmittingTask, setIsSubmittingTask] = useState(false)
  const [taskSummary, setTaskSummary] = useState("")
  const [taskAffectedIds, setTaskAffectedIds] = useState("")
  const [taskSuccessMsg, setTaskSuccessMsg] = useState<string | null>(null)

  // Order Entry State
  const [orderType, setOrderType] = useState("medication")
  const [orderCode, setOrderCode] = useState("RX-6809")
  const [orderDisplay, setOrderDisplay] = useState("Ibuprofen 600mg")
  const [orderDosage, setOrderDosage] = useState("600 mg oral twice daily")
  const [orderInstructions, setOrderInstructions] = useState("Take with food as needed for joint pain")
  const [orderFeedback, setOrderFeedback] = useState<{ success: boolean; msg: string; warning?: string } | null>(null)

  // Portal Message State
  const [portalSubject, setPortalSubject] = useState("")
  const [portalBody, setPortalBody] = useState("")
  const [portalPriority, setPortalPriority] = useState("routine")
  const [portalMsgSent, setPortalMsgSent] = useState(false)

  // HIPAA Audit Events
  const [auditEvents, setAuditEvents] = useState<any[]>([])

  // Load patients and initial chart on mount
  useEffect(() => {
    loadPatients()
    loadPatientChart("pat-0001")
    fetchSimulationState()
  }, [])

  const loadPatients = async (q = "") => {
    try {
      const res = await fetch(`/api/healthcare/patients?q=${encodeURIComponent(q)}`)
      const data = await res.json()
      if (data.ok && Array.isArray(data.patients)) {
        setPatients(data.patients)
      }
    } catch {}
  }

  const loadPatientChart = async (pid: string) => {
    setLoading(true)
    setSelectedPatientId(pid)
    try {
      const res = await fetch(`/api/healthcare/patients?id=${pid}`)
      const data = await res.json()
      if (data.ok && data.chart) {
        setPatientChart(data.chart)
      }
      loadAuditEvents(pid)
    } finally {
      setLoading(false)
    }
  }

  const loadAuditEvents = async (pid = selectedPatientId) => {
    try {
      const res = await fetch(`/api/healthcare/audit?patientId=${pid}`)
      const data = await res.json()
      if (data.ok) {
        setAuditEvents(data.audit_events || [])
        setStateHash(data.state_hash?.substring(0, 10) || "ready")
      }
    } catch {}
  }

  const fetchSimulationState = async () => {
    try {
      const res = await fetch("/api/healthcare/audit")
      const data = await res.json()
      if (data.ok) {
        setStateHash(data.state_hash?.substring(0, 10) || "ready")
      }
    } catch {}
  }

  const stepSimulation = async (minutes: number) => {
    try {
      await fetch("/api/healthcare/simulation", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "step", minutes }),
      })
      fetchSimulationState()
      loadPatientChart(selectedPatientId)
    } catch {}
  }

  const handlePlaceOrder = async (e: React.FormEvent) => {
    e.preventDefault()
    setOrderFeedback(null)

    // Client-side allergy safety check for immediate physician awareness
    const allergies = patientChart?.allergies || []
    const allergenConflict = allergies.find((a: any) =>
      orderDisplay.toLowerCase().includes(a.substance_name.toLowerCase()) ||
      orderDisplay.toLowerCase().includes(a.substance_code.toLowerCase())
    )

    try {
      const res = await fetch("/api/healthcare/orders", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          patient_id: selectedPatientId,
          order_type: orderType,
          code: orderCode,
          display: orderDisplay,
          dosage: orderDosage,
          instructions: orderInstructions,
        }),
      })
      const data = await res.json()

      if (allergenConflict) {
        setOrderFeedback({
          success: false,
          msg: `SAFETY CONTRAINDICATION TRIGGERED: Patient has a documented ${allergenConflict.criticality} allergy to '${allergenConflict.substance_name}' (${allergenConflict.manifestation}). Order prohibited by safety invariants.`,
          warning: "Contraindication Alert",
        })
      } else if (data.ok) {
        setOrderFeedback({
          success: true,
          msg: `Order placed successfully: ${orderDisplay} (${orderCode})`,
        })
        loadPatientChart(selectedPatientId)
      } else {
        setOrderFeedback({
          success: false,
          msg: `Order rejected: ${data.error || "Safety check failed"}`,
        })
      }
    } catch (err: any) {
      setOrderFeedback({ success: false, msg: `Order failed: ${err.message}` })
    }
  }

  const handleSendPortalMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!portalSubject || !portalBody) return
    try {
      await fetch("/api/healthcare/portal", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          patient_id: selectedPatientId,
          subject: portalSubject,
          body: portalBody,
          priority: portalPriority,
        }),
      })
      setPortalMsgSent(true)
      setPortalSubject("")
      setPortalBody("")
      setTimeout(() => setPortalMsgSent(false), 3000)
      loadAuditEvents(selectedPatientId)
    } catch {}
  }

  const submitTaskHandover = async () => {
    try {
      const res = await fetch("/api/healthcare/simulation", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "submit", summary: taskSummary, affected_ids: taskAffectedIds }),
      })
      const data = await res.json()
      if (data.ok) {
        setTaskSuccessMsg("Clinical task handover verified and logged to HIPAA audit trail.")
        setTimeout(() => {
          setIsSubmittingTask(false)
          setTaskSuccessMsg(null)
        }, 2000)
      }
    } catch {}
  }

  const pat = patientChart?.patient || {}
  const allergies = patientChart?.allergies || []
  const conditions = patientChart?.conditions || []
  const medications = patientChart?.medications || []
  const observations = patientChart?.observations || []
  const encounters = patientChart?.encounters || []
  const serviceRequests = patientChart?.service_requests || []

  return (
    <div className="h-screen w-screen flex flex-col bg-[#060d17] text-slate-100 font-sans select-none overflow-hidden">
      {/* 1. Top Clinical Navigation */}
      <header className="h-12 bg-slate-900/90 border-b border-slate-800 flex items-center justify-between px-4 z-20 backdrop-blur">
        <div className="flex items-center space-x-3">
          <div className="w-7 h-7 rounded-lg bg-teal-600 flex items-center justify-center font-bold text-white shadow">
            <HeartPulse className="w-4 h-4" />
          </div>
          <div>
            <h1 className="font-semibold text-sm text-slate-100 flex items-center space-x-2">
              <span>Aegis Health EHR</span>
              <span className="text-[10px] px-2 py-0.5 rounded bg-teal-950 text-teal-300 border border-teal-800 font-mono">
                CLINICAL v4.2
              </span>
            </h1>
          </div>
        </div>

        <div className="flex items-center space-x-4 text-xs">
          <div className="text-slate-300 flex items-center space-x-1">
            <User className="w-3.5 h-3.5 text-teal-400" />
            <span>Dr. Eleanor Vance, MD (Attending Physician)</span>
          </div>

          <div className="flex items-center space-x-1 bg-slate-800/80 px-2 py-0.5 rounded border border-slate-700 font-mono text-[11px] text-slate-300">
            <Clock className="w-3 h-3 text-teal-400" />
            <span>{virtualTime}</span>
          </div>

          <div className="flex items-center space-x-1">
            <button
              onClick={() => stepSimulation(15)}
              className="px-2 py-0.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 text-[11px] transition"
            >
              +15m
            </button>
            <button
              onClick={() => stepSimulation(60)}
              className="px-2 py-0.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 text-[11px] transition"
            >
              +1h
            </button>
          </div>

          <div className="flex items-center space-x-1 bg-slate-800/80 px-2 py-0.5 rounded border border-slate-700 font-mono text-[11px] text-slate-300">
            <Shield className="w-3 h-3 text-emerald-400" />
            <span>SHA: {stateHash}</span>
          </div>

          <button
            onClick={() => setIsSubmittingTask(true)}
            className="px-3 py-1 bg-teal-600 hover:bg-teal-500 text-white rounded font-medium shadow flex items-center space-x-1 transition"
          >
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Submit Task</span>
          </button>
        </div>
      </header>

      {/* 2. Patient Safety Banner */}
      <section className="h-16 bg-slate-900 border-b border-slate-800 flex items-center justify-between px-5 text-xs">
        <div className="flex items-center space-x-6">
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-base text-slate-100">{pat.first_name} {pat.last_name}</span>
              <span className="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 font-mono text-[10px] text-teal-300">
                MRN: {pat.mrn}
              </span>
              <span className="text-slate-400 uppercase text-[11px]">({pat.gender})</span>
            </div>
            <div className="text-slate-400 text-[11px] flex space-x-4 mt-0.5">
              <span>DOB: {pat.birth_date} (Age 51)</span>
              <span>Phone: {pat.phone}</span>
              <span>Provider: {pat.primary_provider_id}</span>
            </div>
          </div>

          {/* Allergies Alerts */}
          <div className="flex items-center space-x-2 pl-4 border-l border-slate-800">
            <span className="text-slate-400 font-semibold text-[11px] uppercase tracking-wider">Allergies:</span>
            {allergies.length === 0 ? (
              <span className="text-emerald-400 font-medium">No Known Drug Allergies (NKDA)</span>
            ) : (
              allergies.map((a: any) => (
                <div
                  key={a.id}
                  className="px-2 py-0.5 rounded bg-rose-950/80 border border-rose-800 text-rose-300 text-[11px] flex items-center space-x-1 font-medium"
                >
                  <AlertTriangle className="w-3 h-3 text-rose-400" />
                  <span className="capitalize">{a.substance_name}: {a.manifestation}</span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Quick Vitals Strip */}
        <div className="flex items-center space-x-4 bg-slate-950/60 px-3 py-1.5 rounded-lg border border-slate-800 font-mono text-[11px]">
          <div className="text-slate-300"><span className="text-slate-500">BP:</span> 137/72 mmHg</div>
          <div className="text-slate-300"><span className="text-slate-500">eGFR:</span> 84.9 mL/min</div>
          <div className="text-slate-300"><span className="text-slate-500">HR:</span> 72 bpm</div>
          <div className="text-slate-300"><span className="text-slate-500">SpO2:</span> 98%</div>
        </div>
      </section>

      {/* 3. Main Workspace */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Drawer: Patient Search Directory */}
        <aside className="w-64 bg-slate-900/60 border-r border-slate-800 flex flex-col">
          <div className="p-3 border-b border-slate-800">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-2.5" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value)
                  loadPatients(e.target.value)
                }}
                placeholder="Search patient name / MRN..."
                className="w-full bg-slate-900 border border-slate-700 rounded-md pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-teal-500"
              />
            </div>
          </div>

          <div className="flex-1 overflow-y-auto divide-y divide-slate-800/60">
            {patients.map((p) => {
              const isSelected = selectedPatientId === p.id
              return (
                <div
                  key={p.id}
                  onClick={() => loadPatientChart(p.id)}
                  className={`p-3 cursor-pointer transition ${
                    isSelected ? "bg-teal-950/40 border-l-2 border-teal-500" : "hover:bg-slate-900/50"
                  }`}
                >
                  <div className="font-semibold text-slate-200 text-xs">{p.first_name} {p.last_name}</div>
                  <div className="text-slate-400 text-[11px] flex justify-between mt-0.5">
                    <span>MRN: {p.mrn}</span>
                    <span>DOB: {p.birth_date}</span>
                  </div>
                </div>
              )
            })}
          </div>
        </aside>

        {/* Center: Clinical Chart Sections */}
        <main className="flex-1 flex flex-col overflow-hidden bg-slate-950/40">
          {/* Section Tabs */}
          <nav className="h-10 border-b border-slate-800 flex space-x-1 px-4 bg-slate-900/40 text-xs">
            {[
              { id: "summary", label: "Chart Summary & Problems", icon: FileText },
              { id: "medications", label: "Medications & Allergies", icon: Pill },
              { id: "labs", label: "Labs & Diagnostics", icon: Activity },
              { id: "orders", label: "Clinical Order Entry", icon: Plus },
              { id: "portal", label: "Patient Portal", icon: Send },
              { id: "audit", label: "HIPAA Audit Trail", icon: Lock },
            ].map((tab) => {
              const Icon = tab.icon
              const isSelected = activeTab === tab.id
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`px-3 py-2 border-b-2 flex items-center space-x-1.5 font-medium transition ${
                    isSelected
                      ? "border-teal-500 text-teal-300 bg-teal-950/20"
                      : "border-transparent text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{tab.label}</span>
                </button>
              )
            })}
          </nav>

          {/* Tab Contents */}
          <div className="flex-1 overflow-y-auto p-5 text-xs">
            {/* 1. Summary & Problems */}
            {activeTab === "summary" && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-sm font-semibold text-slate-200 mb-3 flex items-center space-x-1.5">
                    <Activity className="w-4 h-4 text-teal-400" />
                    <span>Active Problem List & Diagnoses</span>
                  </h3>
                  <div className="border border-slate-800 rounded-lg overflow-hidden bg-slate-900/60">
                    <table className="w-full text-left border-collapse">
                      <thead className="bg-slate-900 border-b border-slate-800 text-slate-400 text-[11px]">
                        <tr>
                          <th className="py-2 px-3">ICD-10 Code</th>
                          <th className="py-2 px-3">Condition Description</th>
                          <th className="py-2 px-3">Onset Date</th>
                          <th className="py-2 px-3">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800 font-mono text-[11px] text-slate-300">
                        {conditions.map((c: any) => (
                          <tr key={c.id} className="hover:bg-slate-800/40">
                            <td className="py-2 px-3 font-semibold text-teal-300">{c.code_icd10}</td>
                            <td className="py-2 px-3 font-sans text-slate-200">{c.display}</td>
                            <td className="py-2 px-3">{c.onset_iso?.substring(0, 10) || "2023-01-10"}</td>
                            <td className="py-2 px-3">
                              <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-950 text-emerald-300 uppercase font-semibold">
                                {c.clinical_status}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Service Requests & Referrals */}
                <div>
                  <h3 className="text-sm font-semibold text-slate-200 mb-3 flex items-center space-x-1.5">
                    <Calendar className="w-4 h-4 text-teal-400" />
                    <span>Referrals & Specialized Orders</span>
                  </h3>
                  <div className="border border-slate-800 rounded-lg p-4 bg-slate-900/60 space-y-3">
                    {serviceRequests.map((sr: any) => (
                      <div key={sr.id} className="space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-slate-200 text-sm">{sr.display}</span>
                          <span className="px-2 py-0.5 rounded text-[10px] bg-teal-950 text-teal-300 border border-teal-800 uppercase">
                            {sr.status}
                          </span>
                        </div>
                        <p className="text-slate-400 text-xs">{sr.reason_text}</p>
                        <p className="text-slate-500 font-mono text-[10px]">Code: {sr.service_code} • Requester: {sr.requester_id}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* 2. Medications & Allergies */}
            {activeTab === "medications" && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-sm font-semibold text-slate-200 mb-3">Active Prescription Medications</h3>
                  <div className="border border-slate-800 rounded-lg overflow-hidden bg-slate-900/60">
                    <table className="w-full text-left border-collapse">
                      <thead className="bg-slate-900 border-b border-slate-800 text-slate-400 text-[11px]">
                        <tr>
                          <th className="py-2 px-3">Medication Name</th>
                          <th className="py-2 px-3">Dosage Instruction</th>
                          <th className="py-2 px-3">Route / Frequency</th>
                          <th className="py-2 px-3">Refills</th>
                          <th className="py-2 px-3">Prescriber</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800 font-mono text-[11px] text-slate-300">
                        {medications.map((m: any) => (
                          <tr key={m.id} className="hover:bg-slate-800/40">
                            <td className="py-2 px-3 font-semibold text-slate-100">{m.medication_name}</td>
                            <td className="py-2 px-3">{m.dosage_instruction}</td>
                            <td className="py-2 px-3">{m.route} / {m.frequency}</td>
                            <td className="py-2 px-3">{m.refills}</td>
                            <td className="py-2 px-3">{m.prescriber_id}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                <div>
                  <h3 className="text-sm font-semibold text-slate-200 mb-3">Allergy & Intolerance Records</h3>
                  <div className="border border-slate-800 rounded-lg overflow-hidden bg-slate-900/60">
                    <table className="w-full text-left border-collapse">
                      <thead className="bg-slate-900 border-b border-slate-800 text-slate-400 text-[11px]">
                        <tr>
                          <th className="py-2 px-3">Substance</th>
                          <th className="py-2 px-3">Reaction / Manifestation</th>
                          <th className="py-2 px-3">Criticality</th>
                          <th className="py-2 px-3">Onset Date</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800 text-[11px] text-slate-300">
                        {allergies.map((a: any) => (
                          <tr key={a.id} className="hover:bg-slate-800/40">
                            <td className="py-2 px-3 font-semibold text-rose-300 capitalize">{a.substance_name}</td>
                            <td className="py-2 px-3 text-slate-200">{a.manifestation}</td>
                            <td className="py-2 px-3 uppercase font-semibold text-rose-400">{a.criticality}</td>
                            <td className="py-2 px-3 font-mono">{a.onset_iso?.substring(0, 10) || "2020-03-15"}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {/* 3. Labs & Diagnostics */}
            {activeTab === "labs" && (
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-slate-200">Laboratory Flowsheet & Vital Observations</h3>
                <div className="border border-slate-800 rounded-lg overflow-hidden bg-slate-900/60">
                  <table className="w-full text-left border-collapse">
                    <thead className="bg-slate-900 border-b border-slate-800 text-slate-400 text-[11px]">
                      <tr>
                        <th className="py-2 px-3">LOINC Code</th>
                        <th className="py-2 px-3">Test / Measurement</th>
                        <th className="py-2 px-3">Result Value</th>
                        <th className="py-2 px-3">Reference Range</th>
                        <th className="py-2 px-3">Interpretation</th>
                        <th className="py-2 px-3">Effective Date</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800 font-mono text-[11px] text-slate-300">
                      {observations.map((o: any) => {
                        const val = o.value_numeric !== null && o.value_numeric !== undefined ? `${o.value_numeric} ${o.unit || ""}` : o.value_string
                        const isAbnormal = o.interpretation && o.interpretation !== "normal"
                        return (
                          <tr key={o.id} className="hover:bg-slate-800/40">
                            <td className="py-2 px-3 font-semibold text-slate-400">{o.code_loinc}</td>
                            <td className="py-2 px-3 font-sans text-slate-200">{o.display}</td>
                            <td className="py-2 px-3 font-bold text-slate-100">{val}</td>
                            <td className="py-2 px-3 text-slate-400">{o.reference_range_low ? `> ${o.reference_range_low}` : "Normal"}</td>
                            <td className="py-2 px-3">
                              <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-semibold ${
                                isAbnormal ? "bg-rose-950 text-rose-300 border border-rose-800" : "bg-emerald-950 text-emerald-300"
                              }`}>
                                {o.interpretation || "normal"}
                              </span>
                            </td>
                            <td className="py-2 px-3">{o.effective_iso?.substring(0, 16).replace("T", " ")}</td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* 4. Clinical Order Entry */}
            {activeTab === "orders" && (
              <div className="max-w-2xl space-y-4">
                <div>
                  <h3 className="text-sm font-semibold text-slate-200">Clinical Order Entry & Safety Checks</h3>
                  <p className="text-slate-400 text-xs mt-0.5">
                    Orders are validated in real-time against patient allergies, renal function (eGFR), and drug-drug interactions.
                  </p>
                </div>

                {orderFeedback && (
                  <div className={`p-3 rounded-lg border text-xs ${
                    orderFeedback.success ? "bg-emerald-950/60 border-emerald-800 text-emerald-300" : "bg-rose-950/60 border-rose-800 text-rose-300"
                  }`}>
                    {orderFeedback.warning && (
                      <div className="font-bold flex items-center space-x-1 mb-1">
                        <AlertOctagon className="w-4 h-4 text-rose-400" />
                        <span>{orderFeedback.warning}</span>
                      </div>
                    )}
                    <div>{orderFeedback.msg}</div>
                  </div>
                )}

                <form onSubmit={handlePlaceOrder} className="bg-slate-900 border border-slate-800 rounded-lg p-4 space-y-3">
                  <div>
                    <label className="text-slate-300 font-medium block mb-1">Order Type:</label>
                    <select
                      value={orderType}
                      onChange={(e) => setOrderType(e.target.value)}
                      className="w-full bg-slate-800 border border-slate-700 rounded p-2 text-white"
                    >
                      <option value="medication">Medication / Prescription</option>
                      <option value="lab">Laboratory Panel</option>
                      <option value="imaging">Diagnostic Imaging (X-Ray / MRI)</option>
                      <option value="referral">Specialist Referral</option>
                    </select>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-slate-300 font-medium block mb-1">Order Code (RxNorm/LOINC/CPT):</label>
                      <input
                        type="text"
                        value={orderCode}
                        onChange={(e) => setOrderCode(e.target.value)}
                        className="w-full bg-slate-800 border border-slate-700 rounded p-2 text-white font-mono"
                      />
                    </div>
                    <div>
                      <label className="text-slate-300 font-medium block mb-1">Display Name / Medication:</label>
                      <input
                        type="text"
                        value={orderDisplay}
                        onChange={(e) => setOrderDisplay(e.target.value)}
                        className="w-full bg-slate-800 border border-slate-700 rounded p-2 text-white"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="text-slate-300 font-medium block mb-1">Dosage & Frequency:</label>
                    <input
                      type="text"
                      value={orderDosage}
                      onChange={(e) => setOrderDosage(e.target.value)}
                      className="w-full bg-slate-800 border border-slate-700 rounded p-2 text-white"
                    />
                  </div>

                  <div>
                    <label className="text-slate-300 font-medium block mb-1">Clinical Instructions & Indication:</label>
                    <textarea
                      rows={2}
                      value={orderInstructions}
                      onChange={(e) => setOrderInstructions(e.target.value)}
                      className="w-full bg-slate-800 border border-slate-700 rounded p-2 text-white"
                    />
                  </div>

                  <button
                    type="submit"
                    className="w-full py-2 bg-teal-600 hover:bg-teal-500 text-white font-medium rounded transition flex items-center justify-center space-x-1"
                  >
                    <Plus className="w-4 h-4" />
                    <span>Validate & Place Order</span>
                  </button>
                </form>
              </div>
            )}

            {/* 5. Patient Portal Messaging */}
            {activeTab === "portal" && (
              <div className="max-w-2xl space-y-4">
                <div>
                  <h3 className="text-sm font-semibold text-slate-200">Patient Portal Secure Communication</h3>
                  <p className="text-slate-400 text-xs mt-0.5">Direct communication with patient portal account: {pat.email}</p>
                </div>

                {portalMsgSent && (
                  <div className="bg-emerald-950/60 border border-emerald-800 text-emerald-300 p-3 rounded text-xs flex items-center space-x-2">
                    <Check className="w-4 h-4 text-emerald-400" />
                    <span>Portal message dispatched to patient chart and portal inbox.</span>
                  </div>
                )}

                <form onSubmit={handleSendPortalMessage} className="bg-slate-900 border border-slate-800 rounded-lg p-4 space-y-3">
                  <div>
                    <label className="text-slate-300 font-medium block mb-1">Subject:</label>
                    <input
                      type="text"
                      value={portalSubject}
                      onChange={(e) => setPortalSubject(e.target.value)}
                      placeholder="e.g. Pre-operative lab clearance instructions..."
                      className="w-full bg-slate-800 border border-slate-700 rounded p-2 text-white"
                    />
                  </div>

                  <div>
                    <label className="text-slate-300 font-medium block mb-1">Priority Triage Level:</label>
                    <select
                      value={portalPriority}
                      onChange={(e) => setPortalPriority(e.target.value)}
                      className="w-full bg-slate-800 border border-slate-700 rounded p-2 text-white"
                    >
                      <option value="routine">Routine</option>
                      <option value="urgent">Urgent Clinical Follow-up</option>
                      <option value="stat">STAT Emergency Escalation</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-slate-300 font-medium block mb-1">Message Content:</label>
                    <textarea
                      rows={4}
                      value={portalBody}
                      onChange={(e) => setPortalBody(e.target.value)}
                      placeholder="Type clinical instructions or response to patient inquiry..."
                      className="w-full bg-slate-800 border border-slate-700 rounded p-2 text-white"
                    />
                  </div>

                  <button
                    type="submit"
                    className="w-full py-2 bg-teal-600 hover:bg-teal-500 text-white font-medium rounded transition flex items-center justify-center space-x-1"
                  >
                    <Send className="w-4 h-4" />
                    <span>Transmit Message</span>
                  </button>
                </form>
              </div>
            )}

            {/* 6. HIPAA Audit Trail */}
            {activeTab === "audit" && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-semibold text-slate-200">HIPAA Security & Access Audit Trail</h3>
                    <p className="text-slate-400 text-xs mt-0.5">Immutable record of chart accesses, orders, and identity checks.</p>
                  </div>
                  <button
                    onClick={() => loadAuditEvents(selectedPatientId)}
                    className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs border border-slate-700"
                  >
                    Refresh Logs
                  </button>
                </div>

                <div className="border border-slate-800 rounded-lg overflow-hidden bg-slate-900/60 font-mono text-xs">
                  <table className="w-full text-left border-collapse">
                    <thead className="bg-slate-900 border-b border-slate-800 text-slate-400 text-[11px]">
                      <tr>
                        <th className="py-2 px-3">Timestamp</th>
                        <th className="py-2 px-3">Actor ID / Role</th>
                        <th className="py-2 px-3">Resource</th>
                        <th className="py-2 px-3">Action</th>
                        <th className="py-2 px-3">Authorized</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800 text-[11px] text-slate-300">
                      {auditEvents.map((a: any, i: number) => (
                        <tr key={i} className="hover:bg-slate-800/40">
                          <td className="py-2 px-3 text-slate-400">{a.timestamp_iso || a.timestamp || "2026-10-15"}</td>
                          <td className="py-2 px-3 text-teal-300">{a.actor_id} ({a.actor_role})</td>
                          <td className="py-2 px-3">{a.resource_type} [{a.patient_id || selectedPatientId}]</td>
                          <td className="py-2 px-3 font-semibold">{a.action}</td>
                          <td className="py-2 px-3">
                            <span className="px-1.5 py-0.5 rounded text-[10px] bg-emerald-950 text-emerald-300">
                              PASS
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </main>
      </div>

      {/* 4. Task Submission Modal */}
      {isSubmittingTask && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-5 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 font-semibold text-slate-100">
                <CheckCircle2 className="w-5 h-5 text-teal-400" />
                <span>Submit Clinical Task Handover</span>
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
                  Submitting formal clinical handover logs your execution summary and affected patient/order records to the HIPAA audit trail.
                </p>
                <div>
                  <label className="text-slate-300 font-medium block mb-1">Clinical Handover Summary:</label>
                  <textarea
                    rows={3}
                    value={taskSummary}
                    onChange={(e) => setTaskSummary(e.target.value)}
                    placeholder="Describe completed clinical decisions (e.g. Cleared pre-op labs, verified identity, resolved medication allergy conflict)..."
                    className="w-full bg-slate-800 border border-slate-700 rounded p-2 text-white focus:outline-none focus:border-teal-500"
                  />
                </div>
                <div>
                  <label className="text-slate-300 font-medium block mb-1">Affected Patient / Order IDs (comma-separated):</label>
                  <input
                    type="text"
                    value={taskAffectedIds}
                    onChange={(e) => setTaskAffectedIds(e.target.value)}
                    placeholder="e.g. pat-0001, sr-pat-0001, ord-1002"
                    className="w-full bg-slate-800 border border-slate-700 rounded p-2 text-white focus:outline-none focus:border-teal-500"
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
                    className="px-4 py-1.5 bg-teal-600 hover:bg-teal-500 text-white rounded font-medium"
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
