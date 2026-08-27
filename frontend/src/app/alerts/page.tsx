"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  BellRing,
  ShieldAlert,
  ShieldCheck,
  Languages,
  ChevronRight,
  TrendingUp,
  AlertTriangle,
  ThumbsUp,
  ThumbsDown,
  Filter,
  CheckCircle2,
} from "lucide-react";

interface AlertItem {
  id: string;
  story_id: string;
  alert_type: string;
  headline_in_progress: string;
  why_it_matters: string;
  urgency: number;
  probability: number;
  impact: number;
  impact_level: string;
  ranking_score: number;
  ranking_explanation: string;
  formation_score: number;
  independent_source_count: number;
  language_count: number;
  languages: string[];
  evidence_available: boolean;
  contradiction_status: string;
  prediction_status: string;
  status: string;
  created_at: string;
}

const STATUS_TABS = ["ALL", "ACTIVE", "INVESTIGATING", "ACKNOWLEDGED", "DISMISSED", "BLOCKED", "RESOLVED"];

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("ALL");
  const [feedbackSuccess, setFeedbackSuccess] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const fetchAlerts = async (statusFilter?: string) => {
    try {
      const url =
        statusFilter && statusFilter !== "ALL"
          ? `http://localhost:8000/api/v1/alerts?status=${statusFilter}`
          : "http://localhost:8000/api/v1/alerts";
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setAlerts(data);
      }
    } catch (err) {
      console.warn("Alerts fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts(activeTab);
  }, [activeTab]);

  const handleStatusChange = async (alertId: string, targetStatus: string) => {
    setErrorMessage(null);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/alerts/${alertId}/status`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: targetStatus }),
      });

      if (!res.ok) {
        const errData = await res.json();
        setErrorMessage(errData.detail || "Failed to update alert status.");
        return;
      }

      const updated = await res.json();
      setAlerts((prev) => prev.map((a) => (a.id === alertId ? updated : a)));
    } catch (err: any) {
      setErrorMessage(err.message);
    }
  };

  const handleFeedback = async (alertId: string, rating: "THUMBS_UP" | "THUMBS_DOWN") => {
    try {
      await fetch(`http://localhost:8000/api/v1/alerts/${alertId}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rating, notes: "Verified in Alerts console" }),
      });
      setFeedbackSuccess(alertId);
      setTimeout(() => setFeedbackSuccess(null), 3000);
    } catch (err) {
      console.error("Feedback error:", err);
    }
  };

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-md bg-amber-500/10 text-amber-400 text-xs font-mono mb-2 border border-amber-500/20">
            <BellRing className="w-3.5 h-3.5" />
            AGENT 9 ALERT ORCHESTRATION & LIFECYCLE
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
            Early Intelligence Alerts
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1 max-w-2xl">
            Ranked by Urgency × Probability × Impact. Contradiction-blocked alerts are strictly gated from activation until factual discrepancies are resolved.
          </p>
        </div>
      </div>

      {errorMessage && (
        <div className="p-3 rounded-lg bg-rose-950/40 border border-rose-500/40 text-rose-300 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" /> {errorMessage}
        </div>
      )}

      {/* Status Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 border-b border-slate-800/80 no-scrollbar">
        {STATUS_TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all font-mono ${
              activeTab === tab
                ? "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                : "bg-slate-900 text-slate-400 border border-slate-800 hover:text-slate-200"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Alerts Table / List */}
      {loading ? (
        <div className="p-12 text-center text-slate-400 bg-slate-900/40 rounded-2xl border border-slate-800">
          <div className="w-8 h-8 border-4 border-amber-500/20 border-t-amber-500 rounded-full animate-spin mx-auto mb-3" />
          <p className="text-xs font-mono">Loading Intelligence Alerts...</p>
        </div>
      ) : alerts.length === 0 ? (
        <div className="p-12 text-center text-slate-400 bg-slate-900/40 rounded-2xl border border-slate-800">
          <BellRing className="w-8 h-8 text-slate-600 mx-auto mb-3" />
          <p className="text-sm font-medium text-slate-300">No alerts found under &apos;{activeTab}&apos; filter.</p>
          <p className="text-xs text-slate-500 mt-1">Grounded alerts will appear as multi-source signals form.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {alerts.map((a, idx) => {
            const isBlocked = a.status === "BLOCKED" || a.contradiction_status === "PREDICTION_BLOCKED";

            return (
              <div
                key={a.id || idx}
                className={`p-6 rounded-2xl border transition-all relative overflow-hidden backdrop-blur-sm ${
                  isBlocked
                    ? "bg-rose-950/20 border-rose-500/40"
                    : "bg-slate-900/90 border-slate-800 hover:border-slate-700"
                }`}
              >
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
                  {/* Left Detail */}
                  <div className="space-y-2 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                        #{idx + 1} RANK {a.ranking_score.toFixed(3)}
                      </span>

                      <span
                        className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${
                          isBlocked
                            ? "bg-rose-500/20 text-rose-300 border-rose-500/40"
                            : "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                        }`}
                      >
                        {a.status}
                      </span>

                      <span className="text-xs font-mono text-slate-400 px-2 py-0.5 rounded bg-slate-950 border border-slate-800">
                        {a.independent_source_count} Independent Sources
                      </span>

                      <span className="text-xs font-mono text-purple-300 px-2 py-0.5 rounded bg-purple-500/10 border border-purple-500/30 uppercase">
                        {a.languages.join(", ")}
                      </span>
                    </div>

                    <h3 className="text-lg font-bold text-white tracking-tight">
                      {a.headline_in_progress}
                    </h3>
                    <p className="text-xs text-slate-300 leading-relaxed">{a.why_it_matters}</p>

                    {/* Metrics */}
                    <div className="grid grid-cols-3 gap-2 pt-2 max-w-sm text-xs font-mono">
                      <div className="p-2 rounded bg-slate-950 border border-slate-800">
                        <span className="text-[10px] text-slate-500 block uppercase">Urgency</span>
                        <span className="text-cyan-400 font-bold">{Math.round(a.urgency * 100)}%</span>
                      </div>
                      <div className="p-2 rounded bg-slate-950 border border-slate-800">
                        <span className="text-[10px] text-slate-500 block uppercase">Probability</span>
                        <span className="text-blue-400 font-bold">{Math.round(a.probability * 100)}%</span>
                      </div>
                      <div className="p-2 rounded bg-slate-950 border border-slate-800">
                        <span className="text-[10px] text-slate-500 block uppercase">Impact</span>
                        <span className="text-amber-400 font-bold">{a.impact_level}</span>
                      </div>
                    </div>
                  </div>

                  {/* Right Actions & Status Transitions */}
                  <div className="flex flex-col items-end justify-between gap-4 shrink-0">
                    <Link
                      href={`/stories/${a.story_id}`}
                      className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-100 text-xs font-semibold border border-slate-700 transition-all group"
                    >
                      Investigate Story
                      <ChevronRight className="w-4 h-4 text-slate-400 group-hover:translate-x-1 transition-transform" />
                    </Link>

                    {/* Status Dropdown */}
                    <div className="flex items-center gap-2 text-xs">
                      <span className="text-slate-400 font-medium">Set Status:</span>
                      <select
                        value={a.status}
                        onChange={(e) => handleStatusChange(a.id, e.target.value)}
                        className="bg-slate-950 border border-slate-800 text-slate-200 text-xs rounded-lg p-1.5 focus:outline-none focus:border-amber-500"
                      >
                        <option value="ACTIVE">ACTIVE</option>
                        <option value="INVESTIGATING">INVESTIGATING</option>
                        <option value="ACKNOWLEDGED">ACKNOWLEDGED</option>
                        <option value="DISMISSED">DISMISSED</option>
                        <option value="BLOCKED">BLOCKED</option>
                        <option value="RESOLVED">RESOLVED</option>
                      </select>
                    </div>

                    {/* Feedback Rating */}
                    <div className="flex items-center gap-2 text-xs text-slate-400">
                      <span>Rating:</span>
                      <button
                        onClick={() => handleFeedback(a.id, "THUMBS_UP")}
                        className="p-1 hover:text-emerald-400 transition-colors"
                        title="Useful Alert"
                      >
                        <ThumbsUp className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleFeedback(a.id, "THUMBS_DOWN")}
                        className="p-1 hover:text-rose-400 transition-colors"
                        title="Not Useful"
                      >
                        <ThumbsDown className="w-4 h-4" />
                      </button>
                      {feedbackSuccess === a.id && (
                        <span className="text-[10px] text-emerald-400 font-mono">Feedback Saved!</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
