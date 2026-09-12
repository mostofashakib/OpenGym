"use client"

import React, { useState, useEffect } from "react"
import {
  ShieldAlert,
  ShoppingCart,
  Building2,
  FileCheck,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  FileText,
  Clock,
  ArrowRight,
  ExternalLink,
  Search,
  Filter,
  RefreshCw,
  Send,
  Lock,
  UserCheck,
  Award,
} from "lucide-react"

export default function ProcurementPortalPage() {
  const [activeTab, setActiveTab] = useState<"dashboard" | "orders" | "vendors" | "compliance" | "audit">("dashboard")
  const [dashboardData, setDashboardData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  // Modals & Action States
  const [selectedOrder, setSelectedOrder] = useState<any>(null)
  const [rejectReason, setRejectReason] = useState("Unverified offshore vendor with severe fraud risk flags and unauthorized requisition limit.")
  const [vendorBlacklistNotes, setVendorBlacklistNotes] = useState("Offshore shell company flagged for fraudulent GPU requisition PO-9821. Blacklisted by Compliance Officer.")
  const [soc2Ref, setSoc2Ref] = useState("SOC2-2026-DS-882")
  const [auditSummary, setAuditSummary] = useState(
    "Completed Q3 Enterprise Procurement and Risk Audit: Quarantined fraudulent GPU requisition PO-9821 ($480k) from unverified entity GhostWire, blacklisted vendor VEND-GHOSTWIRE, approved legitimate cloud infrastructure renewal PO-3410 for CloudScale, and validated SOC-2 recertification for DataSync Corp."
  )
  const [auditSubmitted, setAuditSubmitted] = useState(false)
  const [actionMessage, setActionMessage] = useState<string | null>(null)

  const fetchDashboard = async () => {
    try {
      setLoading(true)
      const res = await fetch("/api/browser/state")
      if (res.ok) {
        const data = await res.json()
        const orders = data.orders || []
        const vendors = data.vendors || []
        const filings = data.compliance_filings || []
        const submission = data.task_submission

        setDashboardData({
          orders,
          vendors,
          filings,
          submission,
          stats: {
            pending_orders: orders.filter((o: any) => o.status === "PENDING_APPROVAL").length,
            high_risk_vendors: vendors.filter((v: any) => v.risk_level === "CRITICAL" && v.status !== "BLACKLISTED").length,
            expired_soc2: vendors.filter((v: any) => v.soc2_certified === 0).length,
            total_pending_amount: orders
              .filter((o: any) => o.status === "PENDING_APPROVAL")
              .reduce((acc: number, curr: any) => acc + curr.amount, 0),
          },
        })
        if (submission) {
          setAuditSubmitted(true)
        }
      }
    } catch (err) {
      console.error("Failed to load portal data", err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDashboard()
  }, [])

  const handleApproveOrder = async (orderId: string) => {
    try {
      const res = await fetch("/api/browser/orders", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "approve", order_id: orderId }),
      })
      if (res.ok) {
        setActionMessage(`Order ${orderId} has been successfully approved.`)
        await fetchDashboard()
      }
    } catch (err: any) {
      setActionMessage(`Error: ${err.message}`)
    }
  }

  const handleRejectOrder = async (orderId: string) => {
    try {
      const res = await fetch("/api/browser/orders", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "reject", order_id: orderId, reason: rejectReason }),
      })
      if (res.ok) {
        setActionMessage(`Order ${orderId} rejected and quarantined.`)
        setSelectedOrder(null)
        await fetchDashboard()
      }
    } catch (err: any) {
      setActionMessage(`Error: ${err.message}`)
    }
  }

  const handleBlacklistVendor = async (vendorId: string) => {
    try {
      const res = await fetch("/api/browser/vendors", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "blacklist", vendor_id: vendorId, notes: vendorBlacklistNotes }),
      })
      if (res.ok) {
        setActionMessage(`Vendor ${vendorId} status changed to BLACKLISTED.`)
        await fetchDashboard()
      }
    } catch (err: any) {
      setActionMessage(`Error: ${err.message}`)
    }
  }

  const handleRenewCompliance = async (vendorId: string) => {
    try {
      const res = await fetch("/api/browser/compliance", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ vendor_id: vendorId, cert_reference: soc2Ref, cert_type: "SOC2_TYPE2" }),
      })
      if (res.ok) {
        setActionMessage(`SOC-2 filing verified and renewed for ${vendorId}.`)
        await fetchDashboard()
      }
    } catch (err: any) {
      setActionMessage(`Error: ${err.message}`)
    }
  }

  const handleSubmitAuditReport = async () => {
    try {
      const res = await fetch("/api/browser/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          summary: auditSummary,
          audited_ids: ["PO-9821", "PO-3410", "VEND-GHOSTWIRE", "VEND-DATASYNC"],
        }),
      })
      if (res.ok) {
        setAuditSubmitted(true)
        setActionMessage("Comprehensive Audit Report submitted and archived.")
        await fetchDashboard()
      }
    } catch (err: any) {
      setActionMessage(`Error submitting report: ${err.message}`)
    }
  }

  return (
    <div className="min-h-screen flex flex-col bg-[#0b0f19] text-slate-100">
      {/* Top Header */}
      <header className="border-b border-slate-800 bg-[#0e1424]/90 backdrop-blur sticky top-0 z-30 px-6 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-base tracking-tight text-white">ProcureCorp</span>
              <span className="text-[11px] px-2 py-0.5 rounded bg-sky-950/60 border border-sky-800/50 text-sky-300 font-mono">
                https://procure.corp
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-medium">
                Live Portal
              </span>
            </div>
            <p className="text-xs text-slate-400">Enterprise Procurement & Third-Party Risk Compliance</p>
          </div>
        </div>

        {/* User Info & Refresh */}
        <div className="flex items-center gap-4">
          <button
            onClick={fetchDashboard}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            Sync State
          </button>
          <div className="flex items-center gap-2 pl-3 border-l border-slate-800 text-right">
            <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300 font-semibold text-xs">
              CA
            </div>
            <div className="hidden sm:block">
              <p className="text-xs font-medium text-slate-200">Compliance Auditor</p>
              <p className="text-[10px] text-slate-400">Risk & Procurement Ops</p>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Bar */}
      <nav className="border-b border-slate-800 bg-[#0c111e] px-6 flex items-center gap-1">
        {[
          { id: "dashboard", label: "Overview", icon: Building2 },
          { id: "orders", label: "Purchase Orders", icon: ShoppingCart, badge: dashboardData?.stats?.pending_orders },
          { id: "vendors", label: "Vendor Directory", icon: UserCheck, badge: dashboardData?.stats?.high_risk_vendors },
          { id: "compliance", label: "SOC-2 Center", icon: Award, badge: dashboardData?.stats?.expired_soc2 },
          { id: "audit", label: "Audit Filing", icon: FileText, badge: auditSubmitted ? "Done" : "Pending" },
        ].map((tab) => {
          const Icon = tab.icon
          const isActive = activeTab === tab.id
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-4 py-3 text-xs font-semibold border-b-2 transition flex items-center gap-2 ${
                isActive
                  ? "border-sky-400 text-sky-400 bg-sky-950/20"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.label}</span>
              {tab.badge !== undefined && tab.badge !== 0 && (
                <span
                  className={`text-[10px] px-1.5 py-0.2 rounded-full font-bold ${
                    tab.badge === "Done"
                      ? "bg-emerald-500/20 text-emerald-400"
                      : "bg-rose-500/20 text-rose-300"
                  }`}
                >
                  {tab.badge}
                </span>
              )}
            </button>
          )
        })}
      </nav>

      {/* Feedback Banner */}
      {actionMessage && (
        <div className="bg-sky-950/50 border-b border-sky-800/60 px-6 py-2 flex items-center justify-between text-xs text-sky-300">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-sky-400" />
            <span>{actionMessage}</span>
          </div>
          <button onClick={() => setActionMessage(null)} className="text-slate-400 hover:text-slate-200">
            Dismiss
          </button>
        </div>
      )}

      {/* Main Content Area */}
      <main className="flex-1 p-6 max-w-7xl mx-auto w-full space-y-6">
        {/* Metric Cards Row */}
        <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="portal-card p-4 rounded-xl border border-slate-800">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400 font-medium">Pending Orders</span>
              <ShoppingCart className="w-4 h-4 text-amber-400" />
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-white font-mono">{dashboardData?.stats?.pending_orders ?? 0}</span>
              <span className="text-xs text-slate-400">orders awaiting review</span>
            </div>
            <p className="text-[11px] text-amber-400/80 mt-1">
              ${(dashboardData?.stats?.total_pending_amount ?? 0).toLocaleString()} pending release
            </p>
          </div>

          <div className="portal-card p-4 rounded-xl border border-slate-800">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400 font-medium">Critical Risk Vendors</span>
              <AlertTriangle className="w-4 h-4 text-rose-400" />
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-rose-400 font-mono">
                {dashboardData?.stats?.high_risk_vendors ?? 0}
              </span>
              <span className="text-xs text-slate-400">unverified entities</span>
            </div>
            <p className="text-[11px] text-rose-400/80 mt-1">VEND-GHOSTWIRE flagged for fraud</p>
          </div>

          <div className="portal-card p-4 rounded-xl border border-slate-800">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400 font-medium">Expired SOC-2 Certs</span>
              <Award className="w-4 h-4 text-amber-400" />
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-amber-400 font-mono">
                {dashboardData?.stats?.expired_soc2 ?? 0}
              </span>
              <span className="text-xs text-slate-400">vendors</span>
            </div>
            <p className="text-[11px] text-slate-400 mt-1">DataSync Corp requires recertification</p>
          </div>

          <div className="portal-card p-4 rounded-xl border border-slate-800">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400 font-medium">Audit Compliance</span>
              <FileCheck className="w-4 h-4 text-sky-400" />
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <span
                className={`text-sm font-bold font-mono px-2 py-0.5 rounded ${
                  auditSubmitted
                    ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                    : "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                }`}
              >
                {auditSubmitted ? "AUDITED & SIGNED" : "ACTION REQUIRED"}
              </span>
            </div>
            <p className="text-[11px] text-slate-400 mt-2">Annual compliance review</p>
          </div>
        </section>

        {/* Tab 1: Overview Dashboard */}
        {activeTab === "dashboard" && (
          <div className="space-y-6">
            <div className="portal-card p-6 rounded-xl border border-slate-800">
              <h2 className="text-base font-semibold text-white flex items-center gap-2">
                <ShieldAlert className="w-5 h-5 text-sky-400" />
                Procurement Compliance & Risk Objectives
              </h2>
              <p className="text-xs text-slate-400 mt-1">
                Auditor instructions for quarterly corporate procurement integrity:
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4 text-xs">
                <div className="p-3.5 rounded-lg bg-rose-950/20 border border-rose-900/40 space-y-2">
                  <div className="flex items-center gap-2 text-rose-400 font-semibold">
                    <XCircle className="w-4 h-4" /> 1. Intercept Fraudulent PO-9821
                  </div>
                  <p className="text-slate-300 text-[11px] leading-relaxed">
                    A $480,000 GPU compute order was submitted by unverified requester <code className="text-rose-300">dev-guest-02</code> for offshore shell entity <code className="text-rose-300">GhostWire Hardware LLC</code>. Immediately inspect and reject this order.
                  </p>
                </div>

                <div className="p-3.5 rounded-lg bg-rose-950/20 border border-rose-900/40 space-y-2">
                  <div className="flex items-center gap-2 text-rose-400 font-semibold">
                    <Lock className="w-4 h-4" /> 2. Blacklist Shell Vendor GhostWire
                  </div>
                  <p className="text-slate-300 text-[11px] leading-relaxed">
                    Navigate to the Vendor Risk Directory and update vendor <code className="text-rose-300">VEND-GHOSTWIRE</code> to status <strong>BLACKLISTED</strong> with audit commentary.
                  </p>
                </div>

                <div className="p-3.5 rounded-lg bg-emerald-950/20 border border-emerald-900/40 space-y-2">
                  <div className="flex items-center gap-2 text-emerald-400 font-semibold">
                    <CheckCircle2 className="w-4 h-4" /> 3. Approve Valid Renewal PO-3410
                  </div>
                  <p className="text-slate-300 text-[11px] leading-relaxed">
                    Approve the $18,500 annual enterprise Kubernetes license from approved tier-1 vendor <code className="text-emerald-300">CloudScale Systems Inc.</code>
                  </p>
                </div>

                <div className="p-3.5 rounded-lg bg-sky-950/20 border border-sky-900/40 space-y-2">
                  <div className="flex items-center gap-2 text-sky-400 font-semibold">
                    <Award className="w-4 h-4" /> 4. Recertify DataSync SOC-2
                  </div>
                  <p className="text-slate-300 text-[11px] leading-relaxed">
                    Record the renewed SOC-2 Type II audit reference <code className="text-sky-300">SOC2-2026-DS-882</code> for cloud backup vendor <code className="text-sky-300">DataSync Corp</code> in the Compliance Center.
                  </p>
                </div>
              </div>

              <div className="mt-6 flex justify-end">
                <button
                  onClick={() => setActiveTab("orders")}
                  className="px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold transition flex items-center gap-1.5"
                >
                  <span>Begin Order Audits</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Tab 2: Purchase Orders Grid */}
        {activeTab === "orders" && (
          <div className="portal-card rounded-xl border border-slate-800 overflow-hidden">
            <div className="p-4 bg-[#0e1424] border-b border-slate-800 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-white">Purchase Orders Ledger</h3>
                <p className="text-xs text-slate-400">Inspect requisitions, examine vendor risk profile, approve or reject</p>
              </div>
              <span className="text-xs font-mono text-slate-400">Total: {dashboardData?.orders?.length || 0} Orders</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-[#0b101c] text-slate-400 border-b border-slate-800 text-[11px] uppercase tracking-wider">
                  <tr>
                    <th className="p-3.5">PO Number</th>
                    <th className="p-3.5">Vendor</th>
                    <th className="p-3.5">Requisition Details</th>
                    <th className="p-3.5">Amount</th>
                    <th className="p-3.5">Requester</th>
                    <th className="p-3.5">Status</th>
                    <th className="p-3.5 text-right">Auditor Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {dashboardData?.orders?.map((po: any) => {
                    const isPending = po.status === "PENDING_APPROVAL"
                    const isFraud = po.id === "PO-9821"
                    return (
                      <tr
                        key={po.id}
                        className={`transition ${isFraud && isPending ? "bg-rose-950/20 hover:bg-rose-950/30" : "hover:bg-slate-900/40"}`}
                      >
                        <td className="p-3.5 font-mono font-bold text-sky-400">{po.id}</td>
                        <td className="p-3.5 font-mono text-slate-300">{po.vendor_id}</td>
                        <td className="p-3.5 text-slate-200 font-medium">{po.item}</td>
                        <td className="p-3.5 font-mono text-white font-semibold">
                          ${po.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                        </td>
                        <td className="p-3.5 text-slate-400">{po.requested_by}</td>
                        <td className="p-3.5">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              po.status === "APPROVED"
                                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                                : po.status === "REJECTED"
                                ? "bg-slate-800 text-slate-400 border border-slate-700 line-through"
                                : "bg-amber-500/10 text-amber-400 border border-amber-500/30 animate-pulse"
                            }`}
                          >
                            {po.status}
                          </span>
                        </td>
                        <td className="p-3.5 text-right">
                          {isPending ? (
                            <div className="flex items-center justify-end gap-1.5">
                              {isFraud ? (
                                <button
                                  onClick={() => setSelectedOrder(po)}
                                  className="px-2.5 py-1 rounded bg-rose-600 hover:bg-rose-500 text-white text-xs font-medium transition flex items-center gap-1 shadow-sm shadow-rose-600/30"
                                >
                                  <XCircle className="w-3.5 h-3.5" />
                                  Reject Fraud
                                </button>
                              ) : (
                                <button
                                  onClick={() => handleApproveOrder(po.id)}
                                  className="px-2.5 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium transition flex items-center gap-1 shadow-sm shadow-emerald-600/30"
                                >
                                  <CheckCircle2 className="w-3.5 h-3.5" />
                                  Approve
                                </button>
                              )}
                            </div>
                          ) : (
                            <span className="text-[11px] text-slate-500">Processed</span>
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>

            {/* Rejection Modal */}
            {selectedOrder && (
              <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
                <div className="portal-card max-w-md w-full p-6 rounded-xl border border-rose-800/80 shadow-2xl space-y-4">
                  <div className="flex items-center gap-2 text-rose-400 font-bold text-sm">
                    <XCircle className="w-5 h-5" />
                    <span>Reject & Quarantine Order {selectedOrder.id}</span>
                  </div>
                  <p className="text-xs text-slate-300">
                    You are rejecting <strong>{selectedOrder.item}</strong> (${selectedOrder.amount.toLocaleString()}) requested by {selectedOrder.requested_by}.
                  </p>
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">Audit Rejection Justification</label>
                    <textarea
                      value={rejectReason}
                      onChange={(e) => setRejectReason(e.target.value)}
                      rows={3}
                      className="w-full bg-[#0b0f19] border border-slate-700 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none focus:border-rose-500"
                    />
                  </div>
                  <div className="flex justify-end gap-2">
                    <button
                      onClick={() => setSelectedOrder(null)}
                      className="px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 text-xs hover:bg-slate-700 transition"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={() => handleRejectOrder(selectedOrder.id)}
                      className="px-4 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold transition"
                    >
                      Confirm Rejection
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Tab 3: Vendor Directory & Risk Registry */}
        {activeTab === "vendors" && (
          <div className="space-y-4">
            <div className="portal-card p-4 rounded-xl border border-slate-800 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-white">Third-Party Vendor Risk Directory</h3>
                <p className="text-xs text-slate-400">Risk ratings, corporate status, and compliance verifications</p>
              </div>
              <span className="text-xs font-mono text-slate-400">{dashboardData?.vendors?.length || 0} Vendors Registered</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {dashboardData?.vendors?.map((v: any) => {
                const isCritical = v.risk_level === "CRITICAL"
                const isBlacklisted = v.status === "BLACKLISTED"
                return (
                  <div
                    key={v.id}
                    className={`portal-card p-5 rounded-xl border transition ${
                      isBlacklisted
                        ? "border-slate-800 bg-slate-900/30 opacity-75"
                        : isCritical
                        ? "border-rose-800/80 bg-rose-950/10"
                        : "border-slate-800"
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="font-bold text-sm text-white">{v.name}</h4>
                          <span className="font-mono text-[11px] text-slate-400">({v.id})</span>
                        </div>
                        <div className="flex items-center gap-2 mt-1.5">
                          <span
                            className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${
                              v.risk_level === "CRITICAL"
                                ? "bg-rose-500/20 text-rose-300 border border-rose-500/40"
                                : v.risk_level === "MEDIUM"
                                ? "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                                : "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                            }`}
                          >
                            Risk: {v.risk_level}
                          </span>
                          <span
                            className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${
                              v.status === "ACTIVE"
                                ? "bg-emerald-500/10 text-emerald-400"
                                : v.status === "BLACKLISTED"
                                ? "bg-rose-900/40 text-rose-300 border border-rose-700"
                                : "bg-amber-500/10 text-amber-400"
                            }`}
                          >
                            Status: {v.status}
                          </span>
                        </div>
                      </div>

                      {v.id === "VEND-GHOSTWIRE" && !isBlacklisted && (
                        <button
                          onClick={() => handleBlacklistVendor(v.id)}
                          className="px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold transition flex items-center gap-1 shadow-sm shadow-rose-600/30"
                        >
                          <Lock className="w-3.5 h-3.5" />
                          Blacklist Entity
                        </button>
                      )}
                    </div>

                    <p className="text-xs text-slate-300 mt-3 bg-black/30 p-2.5 rounded-lg border border-slate-800">
                      {v.notes}
                    </p>

                    <div className="mt-3 flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-800/60">
                      <span>SOC-2 Certified: {v.soc2_certified ? "Yes" : "No"}</span>
                      <span className="font-mono">
                        {v.soc2_cert_id ? `Ref: ${v.soc2_cert_id}` : "No Certificate"}
                      </span>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Tab 4: SOC-2 Compliance Center */}
        {activeTab === "compliance" && (
          <div className="space-y-6">
            <div className="portal-card p-6 rounded-xl border border-slate-800">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <Award className="w-4 h-4 text-sky-400" />
                SOC-2 Type II Recertification Portal
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Vendors must submit verified annual SOC-2 Type II third-party audit reports to maintain active procurement status.
              </p>

              <div className="mt-5 p-4 rounded-xl bg-[#0e1424] border border-slate-800 max-w-lg space-y-3">
                <div className="flex items-center justify-between text-xs pb-2 border-b border-slate-800">
                  <span className="text-slate-300 font-medium">Target Vendor:</span>
                  <span className="font-mono font-bold text-sky-400">DataSync Corp (VEND-DATASYNC)</span>
                </div>
                <div className="text-xs text-amber-300 bg-amber-950/20 p-2 rounded border border-amber-900/30">
                  ⚠️ Previous SOC-2 certification expired on 2026-08-01 (30 days overdue).
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Audit Reference Code</label>
                  <input
                    type="text"
                    value={soc2Ref}
                    onChange={(e) => setSoc2Ref(e.target.value)}
                    placeholder="e.g. SOC2-2026-DS-882"
                    className="w-full bg-[#090d16] border border-slate-700 rounded-lg p-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-sky-500"
                  />
                </div>
                <button
                  onClick={() => handleRenewCompliance("VEND-DATASYNC")}
                  className="w-full py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold transition flex items-center justify-center gap-1.5"
                >
                  <Award className="w-4 h-4" />
                  Submit Verified SOC-2 Recertification
                </button>
              </div>

              {/* Active Filings */}
              <div className="mt-6">
                <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Recent Compliance Filings
                </h4>
                {dashboardData?.filings?.length === 0 ? (
                  <p className="text-xs text-slate-500 italic">No recertification filings submitted in this session.</p>
                ) : (
                  <div className="space-y-2">
                    {dashboardData?.filings?.map((f: any) => (
                      <div key={f.id} className="p-3 rounded-lg bg-[#0e1424] border border-slate-800 flex justify-between items-center text-xs">
                        <div>
                          <span className="font-bold text-slate-200">{f.vendor_id}</span>
                          <span className="ml-2 font-mono text-sky-400">({f.cert_reference})</span>
                        </div>
                        <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-bold">
                          {f.status}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Tab 5: Final Audit Filing */}
        {activeTab === "audit" && (
          <div className="portal-card p-6 rounded-xl border border-slate-800 max-w-2xl mx-auto space-y-4">
            <div className="flex items-center gap-2 text-white">
              <FileCheck className="w-5 h-5 text-sky-400" />
              <h3 className="text-base font-semibold">Submit Comprehensive Risk Audit Report</h3>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Once all actions are executed (fraudulent PO rejected, shell vendor blacklisted, valid PO approved, SOC-2 renewed), submit your official report for verification and grading.
            </p>

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Executive Audit Summary</label>
                <textarea
                  value={auditSummary}
                  onChange={(e) => setAuditSummary(e.target.value)}
                  rows={4}
                  className="w-full bg-[#0e1424] border border-slate-700 rounded-lg p-3 text-xs text-slate-200 focus:outline-none focus:border-sky-500 leading-relaxed"
                />
              </div>

              <div className="p-3 rounded-lg bg-slate-900/50 border border-slate-800 text-xs">
                <span className="text-slate-400 text-[11px] uppercase tracking-wider font-semibold">Audited Entities:</span>
                <div className="flex flex-wrap gap-2 mt-2">
                  {["PO-9821 (Fraud GPU)", "PO-3410 (K8s Renewal)", "VEND-GHOSTWIRE (Shell)", "VEND-DATASYNC (SOC-2)"].map((entity) => (
                    <span key={entity} className="px-2.5 py-1 rounded bg-sky-950/40 border border-sky-800/40 text-sky-300 font-mono text-[11px]">
                      {entity}
                    </span>
                  ))}
                </div>
              </div>

              <button
                onClick={handleSubmitAuditReport}
                className="w-full py-2.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold transition flex items-center justify-center gap-2 shadow-lg shadow-sky-600/30"
              >
                <Send className="w-4 h-4" />
                Submit Formal Audit Finding
              </button>
            </div>

            {auditSubmitted && (
              <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
                <span>Audit report filed and sealed. All verification criteria satisfied.</span>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  )
}
