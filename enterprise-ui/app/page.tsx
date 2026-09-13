'use client';

import React, { useState, useEffect } from 'react';
import {
  Building2,
  Users,
  LifeBuoy,
  CheckCircle2,
  AlertTriangle,
  Receipt,
  Mail,
  Shield,
  Clock,
  Send,
  Search,
  Filter,
  RefreshCw,
  PlusCircle,
  FileText,
  DollarSign,
  ArrowRight,
  UserCheck,
  Briefcase,
  AlertCircle
} from 'lucide-react';

export default function EnterpriseDashboard() {
  const [activeTab, setActiveTab] = useState<'customers' | 'support' | 'approvals' | 'billing' | 'comms' | 'org' | 'audit'>('customers');
  const [loading, setLoading] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  // Simulation Clock & Hash
  const [virtualTime, setVirtualTime] = useState<string>('2026-10-15T09:00:00Z');
  const [stateHash, setStateHash] = useState<string>('');

  // Data States
  const [customers, setCustomers] = useState<any[]>([]);
  const [selectedCustomerId, setSelectedCustomerId] = useState<string | null>(null);
  const [customerProfile, setCustomerProfile] = useState<any | null>(null);
  const [customerSearch, setCustomerSearch] = useState<string>('');

  const [tickets, setTickets] = useState<any[]>([]);
  const [selectedTicketId, setSelectedTicketId] = useState<string | null>(null);
  const [ticketDetails, setTicketDetails] = useState<any | null>(null);
  const [newComment, setNewComment] = useState<string>('');
  const [isInternalComment, setIsInternalComment] = useState<boolean>(false);

  const [approvals, setApprovals] = useState<any[]>([]);
  const [approvalDecisionNotes, setApprovalDecisionNotes] = useState<string>('');

  const [invoices, setInvoices] = useState<any[]>([]);
  const [refundAmount, setRefundAmount] = useState<string>('');
  const [refundReason, setRefundReason] = useState<string>('');
  const [selectedInvoiceId, setSelectedInvoiceId] = useState<string>('');

  const [employees, setEmployees] = useState<any[]>([]);
  const [orgSearch, setOrgSearch] = useState<string>('');

  const [auditEvents, setAuditEvents] = useState<any[]>([]);
  const [messages, setMessages] = useState<any[]>([]);

  // Load Initial Data
  useEffect(() => {
    refreshAll();
  }, []);

  const refreshAll = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchCustomers(),
        fetchTickets(),
        fetchApprovals(),
        fetchAuditHash(),
        fetchEmployees(),
      ]);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const fetchCustomers = async (q = '') => {
    try {
      const res = await fetch(`/api/enterprise/customers?q=${encodeURIComponent(q)}`);
      const data = await res.json();
      if (data.customers) {
        setCustomers(data.customers);
        if (data.customers.length > 0 && !selectedCustomerId) {
          loadCustomerProfile(data.customers[0].id);
        }
      }
    } catch (err) {
      console.error(err);
    }
  };

  const loadCustomerProfile = async (id: string) => {
    setSelectedCustomerId(id);
    try {
      const res = await fetch(`/api/enterprise/customers?id=${id}`);
      const data = await res.json();
      if (data.profile) {
        setCustomerProfile(data.profile);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const fetchTickets = async (status = '') => {
    try {
      const res = await fetch(`/api/enterprise/support?status=${encodeURIComponent(status)}`);
      const data = await res.json();
      if (data.tickets) {
        setTickets(data.tickets);
        if (data.tickets.length > 0 && !selectedTicketId) {
          loadTicketDetails(data.tickets[0].id);
        }
      }
    } catch (err) {
      console.error(err);
    }
  };

  const loadTicketDetails = async (id: string) => {
    setSelectedTicketId(id);
    try {
      const res = await fetch(`/api/enterprise/support?id=${id}`);
      const data = await res.json();
      if (data.ticket) {
        setTicketDetails(data.ticket);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleAddComment = async () => {
    if (!selectedTicketId || !newComment) return;
    setLoading(true);
    try {
      const res = await fetch('/api/enterprise/support', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'add_comment',
          ticketId: selectedTicketId,
          content: newComment,
          isInternal: isInternalComment,
        }),
      });
      const data = await res.json();
      if (data.result?.policy_violation) {
        setStatusMessage(`DLP Policy Alert: ${data.result.policy_violation}`);
      } else if (data.ok) {
        setNewComment('');
        setStatusMessage('Comment recorded in audit trail.');
        await loadTicketDetails(selectedTicketId);
        await fetchAuditHash();
      }
    } catch (err: any) {
      setStatusMessage(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const fetchApprovals = async () => {
    try {
      const res = await fetch('/api/enterprise/approvals');
      const data = await res.json();
      if (data.approvals) {
        setApprovals(data.approvals);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleApprovalDecision = async (requestId: string, decision: string) => {
    setLoading(true);
    try {
      const res = await fetch('/api/enterprise/approvals', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'decide',
          requestId,
          decision,
          notes: approvalDecisionNotes || `Manager decision: ${decision}`,
        }),
      });
      const data = await res.json();
      if (data.ok) {
        setStatusMessage(`Approval request ${requestId} marked as ${decision}.`);
        setApprovalDecisionNotes('');
        await fetchApprovals();
        await fetchAuditHash();
      }
    } catch (err: any) {
      setStatusMessage(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleProcessRefund = async () => {
    if (!selectedInvoiceId || !selectedCustomerId || !refundAmount) {
      setStatusMessage('Please select an invoice and enter amount');
      return;
    }
    setLoading(true);
    try {
      const res = await fetch('/api/enterprise/billing', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          invoiceId: selectedInvoiceId,
          customerId: selectedCustomerId,
          amountUsd: parseFloat(refundAmount),
          reason: refundReason || 'Customer satisfaction concession',
        }),
      });
      const data = await res.json();
      if (data.refund?.policy_violation) {
        setStatusMessage(`Governance Policy Veto: ${data.refund.policy_violation}`);
      } else if (data.ok) {
        setStatusMessage(`Refund processed successfully: ID ${data.refund?.refund?.refund_id || 'OK'}`);
        setRefundAmount('');
        setRefundReason('');
        await loadCustomerProfile(selectedCustomerId);
        await fetchAuditHash();
      }
    } catch (err: any) {
      setStatusMessage(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const fetchAuditHash = async () => {
    try {
      const [hRes, aRes] = await Promise.all([
        fetch('/api/enterprise/audit?hash=true'),
        fetch('/api/enterprise/audit'),
      ]);
      const hData = await hRes.json();
      const aData = await aRes.json();
      if (hData.state_hash) setStateHash(hData.state_hash);
      if (aData.audit_events) setAuditEvents(aData.audit_events.slice(-25).reverse());
    } catch (err) {
      console.error(err);
    }
  };

  const fetchEmployees = async (q = '') => {
    try {
      const res = await fetch(`/api/enterprise/org?q=${encodeURIComponent(q)}`);
      const data = await res.json();
      if (data.employees) {
        setEmployees(data.employees);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleStepSim = async (minutes = 15) => {
    setLoading(true);
    try {
      const res = await fetch('/api/enterprise/simulation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'step', minutes }),
      });
      const data = await res.json();
      if (data.step) {
        setVirtualTime(data.step.current_virtual_time);
        setStatusMessage(`Advanced clock by ${minutes}m.`);
        await refreshAll();
      }
    } catch (err: any) {
      setStatusMessage(`Step error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitTask = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/enterprise/simulation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'submit',
          summary: 'Enterprise SLA & support resolution completed with verified audit trail.',
          affectedIds: selectedCustomerId || 'cust-0001',
        }),
      });
      const data = await res.json();
      if (data.ok) {
        setStatusMessage('Workflow Episode Submitted with Complete Audit Trail!');
        await fetchAuditHash();
      }
    } catch (err: any) {
      setStatusMessage(`Submission error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#090d16] text-slate-100 font-sans">
      {/* Sidebar */}
      <aside className="w-64 bg-[#0d1322] border-r border-slate-800 flex flex-col justify-between select-none">
        <div>
          <div className="p-4 border-b border-slate-800 flex items-center space-x-3">
            <div className="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
              <Building2 className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-sm tracking-wide text-white">APEX ENTERPRISE</h1>
              <p className="text-xs text-blue-400 font-medium">Cloud Operations Twin</p>
            </div>
          </div>

          <nav className="p-3 space-y-1">
            <button
              onClick={() => setActiveTab('customers')}
              className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-xs font-semibold transition ${
                activeTab === 'customers' ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30' : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
              }`}
            >
              <Users className="w-4 h-4" />
              <span>Customer 360</span>
            </button>

            <button
              onClick={() => setActiveTab('support')}
              className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-xs font-semibold transition ${
                activeTab === 'support' ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30' : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
              }`}
            >
              <LifeBuoy className="w-4 h-4" />
              <span>Support Desk</span>
            </button>

            <button
              onClick={() => setActiveTab('approvals')}
              className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-xs font-semibold transition ${
                activeTab === 'approvals' ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30' : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
              }`}
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>Approvals & Governance</span>
            </button>

            <button
              onClick={() => setActiveTab('billing')}
              className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-xs font-semibold transition ${
                activeTab === 'billing' ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30' : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
              }`}
            >
              <Receipt className="w-4 h-4" />
              <span>Billing & Refunds</span>
            </button>

            <button
              onClick={() => setActiveTab('org')}
              className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-xs font-semibold transition ${
                activeTab === 'org' ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30' : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
              }`}
            >
              <Briefcase className="w-4 h-4" />
              <span>Org Directory</span>
            </button>

            <button
              onClick={() => setActiveTab('audit')}
              className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-xs font-semibold transition ${
                activeTab === 'audit' ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30' : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
              }`}
            >
              <Shield className="w-4 h-4" />
              <span>Audit & Compliance</span>
            </button>
          </nav>
        </div>

        <div className="p-4 border-t border-slate-800 bg-[#0a0e19]">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
            <span className="flex items-center gap-1.5"><Clock className="w-3.5 h-3.5 text-blue-400" /> Virtual Time:</span>
          </div>
          <p className="text-xs font-mono font-medium text-slate-200 mb-3">{virtualTime}</p>
          <div className="flex items-center justify-between gap-2">
            <button
              onClick={() => handleStepSim(15)}
              className="flex-1 py-1.5 bg-slate-800 hover:bg-slate-700 text-xs font-medium rounded text-slate-300 transition"
            >
              +15m
            </button>
            <button
              onClick={() => handleStepSim(60)}
              className="flex-1 py-1.5 bg-slate-800 hover:bg-slate-700 text-xs font-medium rounded text-slate-300 transition"
            >
              +1h
            </button>
            <button
              onClick={handleSubmitTask}
              className="flex-1 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-xs font-medium rounded text-white transition"
            >
              Submit
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Top Header */}
        <header className="h-14 bg-[#0d1322]/80 backdrop-blur border-b border-slate-800 flex items-center justify-between px-6">
          <div className="flex items-center space-x-4">
            <span className="text-xs px-2.5 py-1 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 font-mono">
              Actor: emp-003 (role-mgr-supp)
            </span>
            <span className="text-xs px-2.5 py-1 rounded bg-slate-800/80 text-slate-400 border border-slate-700 font-mono">
              Hash: {stateHash ? stateHash.slice(0, 16) : 'Calculating...'}...
            </span>
          </div>

          <div className="flex items-center space-x-3">
            {statusMessage && (
              <span className="text-xs px-3 py-1 rounded bg-amber-500/10 text-amber-300 border border-amber-500/30">
                {statusMessage}
              </span>
            )}
            <button
              onClick={refreshAll}
              disabled={loading}
              className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition"
              title="Refresh"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-blue-400' : ''}`} />
            </button>
          </div>
        </header>

        {/* Tab Body */}
        <div className="flex-1 overflow-y-auto p-6 bg-[#090d16]">
          {/* 1. CUSTOMER 360 */}
          {activeTab === 'customers' && (
            <div className="grid grid-cols-12 gap-6 h-full">
              <div className="col-span-4 bg-[#0e1424] border border-slate-800 rounded-xl p-4 flex flex-col">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-sm font-bold text-white flex items-center gap-2">
                    <Users className="w-4 h-4 text-blue-400" /> Accounts & Customers
                  </h2>
                  <span className="text-xs text-slate-500">{customers.length} total</span>
                </div>
                <div className="relative mb-3">
                  <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
                  <input
                    type="text"
                    placeholder="Search accounts..."
                    value={customerSearch}
                    onChange={(e) => {
                      setCustomerSearch(e.target.value);
                      fetchCustomers(e.target.value);
                    }}
                    className="w-full bg-[#141b2e] border border-slate-700 rounded-lg pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div className="flex-1 overflow-y-auto space-y-2 pr-1">
                  {customers.map((c) => (
                    <div
                      key={c.id}
                      onClick={() => loadCustomerProfile(c.id)}
                      className={`p-3 rounded-lg border cursor-pointer transition ${
                        selectedCustomerId === c.id
                          ? 'bg-blue-600/10 border-blue-500/50'
                          : 'bg-[#12192c] border-slate-800/80 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-semibold text-white">{c.company_name}</span>
                        <span
                          className={`text-[10px] px-1.5 py-0.5 rounded uppercase font-bold ${
                            c.tier === 'enterprise'
                              ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                              : c.tier === 'mid_market'
                              ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                              : 'bg-slate-700 text-slate-300'
                          }`}
                        >
                          {c.tier}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-[11px] text-slate-400">
                        <span>ID: {c.id}</span>
                        <span className="font-mono text-emerald-400">${c.arr_usd.toLocaleString()} ARR</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Customer 360 Detail */}
              <div className="col-span-8 bg-[#0e1424] border border-slate-800 rounded-xl p-6 overflow-y-auto">
                {customerProfile?.customer ? (
                  <div className="space-y-6">
                    <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                      <div>
                        <h3 className="text-lg font-bold text-white">{customerProfile.customer.company_name}</h3>
                        <p className="text-xs text-slate-400">Account ID: {customerProfile.customer.id} • Owner: {customerProfile.customer.account_owner_id}</p>
                      </div>
                      <div className="text-right">
                        <span className="text-sm font-mono font-bold text-emerald-400">${customerProfile.customer.arr_usd.toLocaleString()} ARR</span>
                        <p className="text-xs text-slate-400 uppercase tracking-wider">{customerProfile.customer.tier} Tier</p>
                      </div>
                    </div>

                    {/* Contacts & Contracts */}
                    <div className="grid grid-cols-2 gap-4">
                      <div className="bg-[#12192c] p-4 rounded-lg border border-slate-800">
                        <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">Key Contacts</h4>
                        <div className="space-y-2">
                          {customerProfile.contacts?.map((ct: any) => (
                            <div key={ct.id} className="text-xs border-b border-slate-800/60 pb-1.5 last:border-0">
                              <p className="font-medium text-white">{ct.first_name} {ct.last_name}</p>
                              <p className="text-slate-400">{ct.email} • {ct.title}</p>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div className="bg-[#12192c] p-4 rounded-lg border border-slate-800">
                        <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">Active Contracts & SLAs</h4>
                        <div className="space-y-2">
                          {customerProfile.contracts?.map((ctr: any) => (
                            <div key={ctr.id} className="text-xs border-b border-slate-800/60 pb-1.5 last:border-0">
                              <div className="flex justify-between">
                                <span className="font-medium text-white">{ctr.plan_name}</span>
                                <span className="text-blue-400 font-mono">${ctr.annual_value_usd.toLocaleString()}</span>
                              </div>
                              <p className="text-slate-400">SLA: {ctr.sla_tier} • Concession Cap: ${ctr.max_concession_cap_usd || '5,000'}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Invoices */}
                    <div>
                      <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">Recent Invoices</h4>
                      <div className="bg-[#12192c] rounded-lg border border-slate-800 overflow-hidden">
                        <table className="w-full text-left text-xs">
                          <thead className="bg-[#161e33] text-slate-400 border-b border-slate-800">
                            <tr>
                              <th className="p-3">Invoice #</th>
                              <th className="p-3">Due Date</th>
                              <th className="p-3">Status</th>
                              <th className="p-3 text-right">Amount</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-800 text-slate-300">
                            {customerProfile.invoices?.map((inv: any) => (
                              <tr key={inv.id} className="hover:bg-slate-800/30">
                                <td className="p-3 font-mono text-blue-400">{inv.id}</td>
                                <td className="p-3">{inv.due_date}</td>
                                <td className="p-3">
                                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                                    inv.status === 'paid' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-amber-500/20 text-amber-300'
                                  }`}>
                                    {inv.status}
                                  </span>
                                </td>
                                <td className="p-3 text-right font-mono font-medium">${inv.amount_usd.toLocaleString()}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="h-full flex items-center justify-center text-slate-500 text-sm">
                    Select a customer to inspect Customer 360 profile
                  </div>
                )}
              </div>
            </div>
          )}

          {/* 2. SUPPORT DESK */}
          {activeTab === 'support' && (
            <div className="grid grid-cols-12 gap-6 h-full">
              <div className="col-span-5 bg-[#0e1424] border border-slate-800 rounded-xl p-4 flex flex-col">
                <div className="flex items-center justify-between mb-3">
                  <h2 className="text-sm font-bold text-white flex items-center gap-2">
                    <LifeBuoy className="w-4 h-4 text-blue-400" /> Support Queue
                  </h2>
                  <div className="flex space-x-1">
                    {['', 'open', 'in_progress', 'resolved'].map((st) => (
                      <button
                        key={st}
                        onClick={() => fetchTickets(st)}
                        className="text-[10px] px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 uppercase"
                      >
                        {st || 'All'}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="flex-1 overflow-y-auto space-y-2 pr-1">
                  {tickets.map((t) => (
                    <div
                      key={t.id}
                      onClick={() => loadTicketDetails(t.id)}
                      className={`p-3 rounded-lg border cursor-pointer transition ${
                        selectedTicketId === t.id
                          ? 'bg-blue-600/10 border-blue-500/50'
                          : 'bg-[#12192c] border-slate-800/80 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-semibold text-white truncate max-w-[200px]">{t.title}</span>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded uppercase font-bold ${
                          t.priority === 'urgent' ? 'bg-red-500/20 text-red-300' : 'bg-slate-700 text-slate-300'
                        }`}>
                          {t.priority}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-[11px] text-slate-400">
                        <span>{t.customer_name || t.customer_id}</span>
                        <span className="text-blue-400 uppercase text-[10px]">{t.status}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Ticket Details & Timeline */}
              <div className="col-span-7 bg-[#0e1424] border border-slate-800 rounded-xl p-6 flex flex-col justify-between">
                {ticketDetails?.ticket ? (
                  <div className="flex flex-col h-full justify-between">
                    <div>
                      <div className="flex items-start justify-between border-b border-slate-800 pb-3 mb-4">
                        <div>
                          <h3 className="text-base font-bold text-white">{ticketDetails.ticket.title}</h3>
                          <p className="text-xs text-slate-400">Ticket {ticketDetails.ticket.id} • Customer: {ticketDetails.ticket.customer_id}</p>
                        </div>
                        <span className="text-xs font-bold uppercase px-2.5 py-1 rounded bg-blue-500/20 text-blue-300 border border-blue-500/30">
                          {ticketDetails.ticket.status}
                        </span>
                      </div>

                      <div className="bg-[#12192c] p-3 rounded-lg border border-slate-800 text-xs text-slate-300 mb-4">
                        {ticketDetails.ticket.description}
                      </div>

                      {/* Comments stream */}
                      <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">Discussion & Activity</h4>
                      <div className="space-y-2 max-h-56 overflow-y-auto pr-1 mb-4">
                        {ticketDetails.comments?.map((c: any) => (
                          <div
                            key={c.id}
                            className={`p-2.5 rounded-lg text-xs border ${
                              c.is_internal
                                ? 'bg-amber-500/10 border-amber-500/30 text-amber-200'
                                : 'bg-[#141b2e] border-slate-800 text-slate-300'
                            }`}
                          >
                            <div className="flex justify-between text-[10px] text-slate-400 mb-1">
                              <span>{c.author_id} {c.is_internal && '(Internal Note)'}</span>
                              <span>{c.created_iso}</span>
                            </div>
                            <p>{c.content}</p>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Add Comment with DLP Scanner */}
                    <div className="bg-[#12192c] p-3 rounded-lg border border-slate-800">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-bold text-slate-300">Add Response (DLP Protected)</span>
                        <label className="flex items-center space-x-2 text-xs text-slate-400 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={isInternalComment}
                            onChange={(e) => setIsInternalComment(e.target.checked)}
                            className="rounded bg-slate-800 border-slate-700 text-blue-600 focus:ring-0"
                          />
                          <span>Internal Note</span>
                        </label>
                      </div>
                      <textarea
                        rows={2}
                        value={newComment}
                        onChange={(e) => setNewComment(e.target.value)}
                        placeholder="Draft resolution or reply..."
                        className="w-full bg-[#161e33] border border-slate-700 rounded-lg p-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 mb-2"
                      />
                      <button
                        onClick={handleAddComment}
                        disabled={loading || !newComment}
                        className="w-full py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-bold transition flex items-center justify-center gap-1.5"
                      >
                        <Send className="w-3.5 h-3.5" /> Submit Response
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="h-full flex items-center justify-center text-slate-500 text-sm">
                    Select a ticket to inspect
                  </div>
                )}
              </div>
            </div>
          )}

          {/* 3. APPROVALS & GOVERNANCE */}
          {activeTab === 'approvals' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-bold text-white flex items-center gap-2">
                    <CheckCircle2 className="w-5 h-5 text-emerald-400" /> Executive Approvals & Governance
                  </h2>
                  <p className="text-xs text-slate-400">Segregation of Duties and Dual-Control Financial Authorization Desk</p>
                </div>
              </div>

              <div className="bg-[#0e1424] border border-slate-800 rounded-xl overflow-hidden">
                <table className="w-full text-left text-xs">
                  <thead className="bg-[#141b2e] text-slate-400 border-b border-slate-800">
                    <tr>
                      <th className="p-3">Request ID</th>
                      <th className="p-3">Type</th>
                      <th className="p-3">Requester</th>
                      <th className="p-3">Approver</th>
                      <th className="p-3">Amount</th>
                      <th className="p-3">Reason</th>
                      <th className="p-3">Status</th>
                      <th className="p-3 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800 text-slate-300">
                    {approvals.map((app) => (
                      <tr key={app.id} className="hover:bg-slate-800/30">
                        <td className="p-3 font-mono text-blue-400">{app.id}</td>
                        <td className="p-3 uppercase font-medium">{app.request_type}</td>
                        <td className="p-3">{app.requester_name || app.requester_id}</td>
                        <td className="p-3">{app.approver_name || app.approver_id}</td>
                        <td className="p-3 font-mono font-semibold text-emerald-400">${app.amount_usd.toLocaleString()}</td>
                        <td className="p-3 max-w-xs truncate">{app.reason}</td>
                        <td className="p-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                            app.status === 'approved'
                              ? 'bg-emerald-500/20 text-emerald-300'
                              : app.status === 'rejected'
                              ? 'bg-red-500/20 text-red-300'
                              : 'bg-amber-500/20 text-amber-300'
                          }`}>
                            {app.status}
                          </span>
                        </td>
                        <td className="p-3 text-right">
                          {app.status === 'pending' && (
                            <div className="flex items-center justify-end space-x-2">
                              <button
                                onClick={() => handleApprovalDecision(app.id, 'approved')}
                                className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-[10px] font-bold"
                              >
                                Approve
                              </button>
                              <button
                                onClick={() => handleApprovalDecision(app.id, 'rejected')}
                                className="px-2.5 py-1 bg-red-600 hover:bg-red-500 text-white rounded text-[10px] font-bold"
                              >
                                Reject
                              </button>
                            </div>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 4. BILLING & REFUNDS */}
          {activeTab === 'billing' && (
            <div className="grid grid-cols-12 gap-6">
              <div className="col-span-6 bg-[#0e1424] border border-slate-800 rounded-xl p-6">
                <h3 className="text-base font-bold text-white mb-2 flex items-center gap-2">
                  <Receipt className="w-4 h-4 text-blue-400" /> Process SLA Concession or Refund
                </h3>
                <p className="text-xs text-slate-400 mb-6">Subject to Financial Authorization matrix and contract SLA caps.</p>

                <div className="space-y-4 text-xs">
                  <div>
                    <label className="block text-slate-300 font-medium mb-1">Customer Account</label>
                    <select
                      value={selectedCustomerId || ''}
                      onChange={(e) => {
                        setSelectedCustomerId(e.target.value);
                        loadCustomerProfile(e.target.value);
                      }}
                      className="w-full bg-[#141b2e] border border-slate-700 rounded-lg p-2.5 text-white"
                    >
                      {customers.map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.company_name} ({c.id})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-slate-300 font-medium mb-1">Select Invoice</label>
                    <select
                      value={selectedInvoiceId}
                      onChange={(e) => setSelectedInvoiceId(e.target.value)}
                      className="w-full bg-[#141b2e] border border-slate-700 rounded-lg p-2.5 text-white"
                    >
                      <option value="">-- Choose Invoice --</option>
                      {customerProfile?.invoices?.map((inv: any) => (
                        <option key={inv.id} value={inv.id}>
                          {inv.id} - ${inv.amount_usd.toLocaleString()} ({inv.status})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-slate-300 font-medium mb-1">Refund Amount (USD)</label>
                    <input
                      type="number"
                      placeholder="e.g. 500"
                      value={refundAmount}
                      onChange={(e) => setRefundAmount(e.target.value)}
                      className="w-full bg-[#141b2e] border border-slate-700 rounded-lg p-2.5 text-white"
                    />
                  </div>

                  <div>
                    <label className="block text-slate-300 font-medium mb-1">Business Justification</label>
                    <textarea
                      rows={3}
                      placeholder="Enter justification..."
                      value={refundReason}
                      onChange={(e) => setRefundReason(e.target.value)}
                      className="w-full bg-[#141b2e] border border-slate-700 rounded-lg p-2.5 text-white"
                    />
                  </div>

                  <button
                    onClick={handleProcessRefund}
                    disabled={loading || !selectedInvoiceId || !refundAmount}
                    className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-bold text-xs transition"
                  >
                    Execute Financial Transaction
                  </button>
                </div>
              </div>

              <div className="col-span-6 bg-[#0e1424] border border-slate-800 rounded-xl p-6">
                <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
                  <Shield className="w-4 h-4 text-emerald-400" /> Financial Governance Rules
                </h3>
                <div className="space-y-3 text-xs text-slate-300">
                  <div className="p-3 bg-[#141b2e] rounded-lg border border-slate-800">
                    <p className="font-semibold text-white mb-1">Dual-Approval Thresholds</p>
                    <p className="text-slate-400">Amounts exceeding employee role limit ($1,000 for Support Rep, $5,000 for Support Manager) strictly require manager counter-signature.</p>
                  </div>
                  <div className="p-3 bg-[#141b2e] rounded-lg border border-slate-800">
                    <p className="font-semibold text-white mb-1">SLA Contract Cap Enforcement</p>
                    <p className="text-slate-400">Total refunds within billing period cannot exceed max concession ceiling stipulated in Master Services Agreement.</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 5. ORG DIRECTORY */}
          {activeTab === 'org' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  <Briefcase className="w-5 h-5 text-blue-400" /> Enterprise Organization Directory
                </h2>
                <input
                  type="text"
                  placeholder="Search staff..."
                  value={orgSearch}
                  onChange={(e) => {
                    setOrgSearch(e.target.value);
                    fetchEmployees(e.target.value);
                  }}
                  className="bg-[#141b2e] border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white placeholder-slate-500"
                />
              </div>

              <div className="bg-[#0e1424] border border-slate-800 rounded-xl overflow-hidden">
                <table className="w-full text-left text-xs">
                  <thead className="bg-[#141b2e] text-slate-400 border-b border-slate-800">
                    <tr>
                      <th className="p-3">ID</th>
                      <th className="p-3">Name</th>
                      <th className="p-3">Email</th>
                      <th className="p-3">Title</th>
                      <th className="p-3">Department</th>
                      <th className="p-3">Team</th>
                      <th className="p-3 text-right">Approval Limit</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800 text-slate-300">
                    {employees.map((e) => (
                      <tr key={e.id} className="hover:bg-slate-800/30">
                        <td className="p-3 font-mono text-blue-400">{e.id}</td>
                        <td className="p-3 font-semibold text-white">{e.first_name} {e.last_name}</td>
                        <td className="p-3 text-slate-400">{e.email}</td>
                        <td className="p-3">{e.title}</td>
                        <td className="p-3">{e.department}</td>
                        <td className="p-3">{e.team}</td>
                        <td className="p-3 text-right font-mono text-emerald-400">
                          ${e.approval_limit_usd.toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 6. AUDIT & COMPLIANCE */}
          {activeTab === 'audit' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-bold text-white flex items-center gap-2">
                    <Shield className="w-5 h-5 text-blue-400" /> Immutable Enterprise Audit Trail
                  </h2>
                  <p className="text-xs text-slate-400">Cryptographically verifiable event log recording all actions across 11 integrated systems</p>
                </div>
                <div className="text-right">
                  <span className="text-xs text-slate-400">SHA-256 State Digest:</span>
                  <p className="text-xs font-mono text-blue-400">{stateHash || 'Calculating...'}</p>
                </div>
              </div>

              <div className="bg-[#0e1424] border border-slate-800 rounded-xl overflow-hidden">
                <table className="w-full text-left text-xs">
                  <thead className="bg-[#141b2e] text-slate-400 border-b border-slate-800">
                    <tr>
                      <th className="p-3">Timestamp</th>
                      <th className="p-3">Actor</th>
                      <th className="p-3">Role</th>
                      <th className="p-3">Action</th>
                      <th className="p-3">Resource</th>
                      <th className="p-3">Authorized</th>
                      <th className="p-3">Details</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800 text-slate-300">
                    {auditEvents.map((evt) => (
                      <tr key={evt.id} className="hover:bg-slate-800/30">
                        <td className="p-3 font-mono text-slate-400">{evt.timestamp_iso}</td>
                        <td className="p-3 font-mono text-blue-400">{evt.actor_id}</td>
                        <td className="p-3">{evt.actor_role}</td>
                        <td className="p-3 font-semibold text-white">{evt.action}</td>
                        <td className="p-3">{evt.resource_type}:{evt.resource_id}</td>
                        <td className="p-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            evt.authorized ? 'bg-emerald-500/20 text-emerald-300' : 'bg-red-500/20 text-red-300'
                          }`}>
                            {evt.authorized ? 'YES' : 'VIOLATION'}
                          </span>
                        </td>
                        <td className="p-3 font-mono text-[11px] text-slate-400 max-w-xs truncate">
                          {evt.details_json}
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
  );
}
