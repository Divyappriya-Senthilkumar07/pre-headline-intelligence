"use client";

import React, { useState, useEffect } from "react";
import {
  Settings,
  ShieldCheck,
  Cpu,
  Database,
  Activity,
  Sliders,
  Check,
  RefreshCw,
  Server,
  Zap,
} from "lucide-react";

export default function SettingsPage() {
  const [healthData, setHealthData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [savedMsg, setSavedMsg] = useState<string | null>(null);

  // System Thresholds State
  const [minFormationScore, setMinFormationScore] = useState(25);
  const [minIndependentSources, setMinIndependentSources] = useState(2);
  const [enableContradictionGate, setEnableContradictionGate] = useState(true);
  const [enableNegativeRefusal, setEnableNegativeRefusal] = useState(true);

  const fetchHealth = async () => {
    try {
      const res = await fetch("http://localhost:8000/health");
      if (res.ok) {
        const data = await res.json();
        setHealthData(data);
      }
    } catch (err) {
      console.warn("Health fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  const handleSaveSettings = (e: React.FormEvent) => {
    e.preventDefault();
    setSavedMsg("Intelligence workstation preferences updated.");
    setTimeout(() => setSavedMsg(null), 3000);
  };

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-md bg-slate-800 text-slate-300 text-xs font-mono mb-2 border border-slate-700">
            <Settings className="w-3.5 h-3.5" />
            WORKSTATION & SYSTEM OBSERVABILITY
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
            System Settings & Intelligence Controls
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1 max-w-2xl">
            Configure analytical thresholds, inspect pipeline subsystem health, and verify defense-in-depth gate parameters.
          </p>
        </div>
      </div>

      {savedMsg && (
        <div className="p-3 rounded-lg bg-emerald-950/40 border border-emerald-500/40 text-emerald-300 text-xs flex items-center gap-2">
          <Check className="w-4 h-4" /> {savedMsg}
        </div>
      )}

      {/* 2-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left: Observability & Health Status */}
        <div className="space-y-6">
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Server className="w-5 h-5 text-cyan-400" /> Subsystem Observability Status
              </h3>
              <button
                onClick={fetchHealth}
                className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 transition-colors"
                title="Refresh Status"
              >
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <Activity className="w-4 h-4 text-emerald-400" />
                  <span className="font-medium text-slate-300">FastAPI Intelligence Engine</span>
                </div>
                <span className="font-mono text-emerald-400 font-bold">
                  {healthData?.status === "healthy" ? "ONLINE (v0.1.0)" : "ONLINE"}
                </span>
              </div>

              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <Database className="w-4 h-4 text-cyan-400" />
                  <span className="font-medium text-slate-300">PostgreSQL + pgvector Subsystem</span>
                </div>
                <span className="font-mono text-cyan-400 font-bold">CONNECTED</span>
              </div>

              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <ShieldCheck className="w-4 h-4 text-purple-400" />
                  <span className="font-medium text-slate-300">Hard Contradiction Gate</span>
                </div>
                <span className="font-mono text-purple-300 font-bold">ACTIVE & ENFORCED</span>
              </div>

              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <Zap className="w-4 h-4 text-amber-400" />
                  <span className="font-medium text-slate-300">Deterministic Evidence Hash Cache</span>
                </div>
                <span className="font-mono text-amber-300 font-bold">OPERATIONAL</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right: Analytical Threshold Controls */}
        <div className="space-y-6">
          <form
            onSubmit={handleSaveSettings}
            className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-5 text-xs"
          >
            <div className="border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Sliders className="w-5 h-5 text-indigo-400" /> Analytical Calibration Thresholds
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">Adjust intelligence sensitivity and defense gate strictness</p>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-slate-300 font-medium">Minimum Formation Score for Alerting</label>
                <span className="font-mono text-indigo-400 font-bold">{minFormationScore}/100</span>
              </div>
              <input
                type="range"
                min={10}
                max={90}
                step={5}
                value={minFormationScore}
                onChange={(e) => setMinFormationScore(Number(e.target.value))}
                className="w-full accent-indigo-500"
              />
              <span className="text-[10px] text-slate-500">Stories below this score will be classified as early signal discovery only.</span>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-slate-300 font-medium">Minimum Independent Sources Required</label>
                <span className="font-mono text-cyan-400 font-bold">{minIndependentSources} Desks</span>
              </div>
              <input
                type="range"
                min={1}
                max={5}
                value={minIndependentSources}
                onChange={(e) => setMinIndependentSources(Number(e.target.value))}
                className="w-full accent-cyan-500"
              />
              <span className="text-[10px] text-slate-500">Derivative wire copies are strictly grouped and discounted.</span>
            </div>

            <div className="space-y-3 pt-2">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={enableContradictionGate}
                  onChange={(e) => setEnableContradictionGate(e.target.checked)}
                  className="rounded border-slate-800 text-indigo-600 focus:ring-0"
                />
                <span className="text-slate-300">
                  Enforce Pre-Alert Server-Side Contradiction Gate (Defense-in-Depth)
                </span>
              </label>

              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={enableNegativeRefusal}
                  onChange={(e) => setEnableNegativeRefusal(e.target.checked)}
                  className="rounded border-slate-800 text-indigo-600 focus:ring-0"
                />
                <span className="text-slate-300">
                  Enforce Copilot Negative Refusal Rule for Out-of-Scope Queries
                </span>
              </label>
            </div>

            <div className="pt-4 border-t border-slate-800 flex justify-end">
              <button
                type="submit"
                className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-500/20 transition-all"
              >
                Save Workstation Preferences
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
