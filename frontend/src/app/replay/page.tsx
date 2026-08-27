"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  PlayCircle,
  Clock,
  ShieldCheck,
  Languages,
  ChevronRight,
  TrendingUp,
  AlertTriangle,
  Play,
  RotateCcw,
  BookOpen,
} from "lucide-react";

interface ScenarioSummary {
  id: string;
  name: string;
  description: string;
  scenario_type: string;
  expected_outcome: string;
  target_milestone: string;
  target_milestone_time?: string | null;
  events_count: number;
}

export default function ReplayScenarioCatalogPage() {
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchScenarios = async () => {
      try {
        const res = await fetch("http://localhost:8000/api/v1/replay/scenarios");
        if (res.ok) {
          const data = await res.json();
          setScenarios(data);
        } else {
          setScenarios(getFallbackScenarios());
        }
      } catch (err) {
        console.warn("Using fallback scenarios:", err);
        setScenarios(getFallbackScenarios());
      } finally {
        setLoading(false);
      }
    };
    fetchScenarios();
  }, []);

  const getTypeBadge = (type: string) => {
    switch (type) {
      case "EARLY_DETECTION":
        return "bg-emerald-500/20 text-emerald-300 border-emerald-500/40";
      case "SYNDICATION_TRAP":
        return "bg-amber-500/20 text-amber-300 border-amber-500/40";
      case "MULTILINGUAL_CONVERGENCE":
        return "bg-purple-500/20 text-purple-300 border-purple-500/40";
      case "CONTRADICTION":
        return "bg-rose-500/20 text-rose-300 border-rose-500/40";
      case "FALSE_SIGNAL":
        return "bg-blue-500/20 text-blue-300 border-blue-500/40";
      case "MISSED_STORY":
        return "bg-slate-700/60 text-slate-300 border-slate-600";
      default:
        return "bg-slate-800 text-slate-300 border-slate-700";
    }
  };

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-md bg-cyan-500/10 text-cyan-400 text-xs font-mono mb-2 border border-cyan-500/20">
            <PlayCircle className="w-3.5 h-3.5" />
            HISTORICAL EVALUATION REPLAY ENGINE
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
            Historical Story Replay & Lead-Time Benchmarking
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1 max-w-2xl">
            Reconstruct what the system believed at each historical timestamp $T$ with <strong className="text-slate-300">zero look-ahead bias</strong>. Verify early detection and measure lead time against target milestones.
          </p>
        </div>

        <Link
          href="/evaluation"
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-500/20 transition-all shrink-0"
        >
          <TrendingUp className="w-4 h-4" /> View Full Evaluation Dashboard
        </Link>
      </div>

      {/* Scenario Grid */}
      {loading ? (
        <div className="p-12 text-center text-slate-400 bg-slate-900/40 rounded-2xl border border-slate-800">
          <div className="w-8 h-8 border-4 border-cyan-500/20 border-t-cyan-500 rounded-full animate-spin mx-auto mb-3" />
          <p className="text-xs font-mono">Loading Historical Replay Scenarios...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {scenarios.map((s, idx) => (
            <div
              key={s.id || idx}
              className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 hover:border-slate-700 transition-all shadow-xl flex flex-col justify-between space-y-4 backdrop-blur-sm relative overflow-hidden group"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between gap-2">
                  <span
                    className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full border ${getTypeBadge(
                      s.scenario_type
                    )}`}
                  >
                    {s.scenario_type.replace(/_/g, " ")}
                  </span>
                  <span className="text-[11px] font-mono text-slate-400">
                    {s.events_count} Chronological Events
                  </span>
                </div>

                <h3 className="text-base font-bold text-white tracking-tight group-hover:text-cyan-400 transition-colors">
                  {s.name}
                </h3>
                <p className="text-xs text-slate-400 leading-relaxed line-clamp-3">
                  {s.description}
                </p>
              </div>

              <div className="pt-4 border-t border-slate-800/80 flex items-center justify-between">
                <div className="text-[10px] font-mono text-slate-400">
                  <span>Target: </span>
                  <strong className="text-slate-200">{s.expected_outcome.replace(/_/g, " ")}</strong>
                </div>

                <Link
                  href={`/replay/${s.id}`}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-300 text-xs font-semibold border border-cyan-500/40 transition-colors"
                >
                  <Play className="w-3 h-3" /> Launch Replay
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function getFallbackScenarios(): ScenarioSummary[] {
  return [
    {
      id: "scenario-1-early-detection",
      name: "Scenario 1: Successful Early Detection (Industrial Audit)",
      description: "Story begins with local Tamil coverage, expands to regulatory document, then Hindi desk, generating early alert 2.5 hours before national mainstream headline.",
      scenario_type: "EARLY_DETECTION",
      expected_outcome: "MAINSTREAM_HEADLINE",
      target_milestone: "MAINSTREAM",
      events_count: 6,
    },
    {
      id: "scenario-2-syndication-trap",
      name: "Scenario 2: Syndication Trap (Wire Duplication)",
      description: "One single original publisher article is rapidly republished by 4 wire portals. The system must recognize that independent source count is 1, not 5, suppressing false early alerts.",
      scenario_type: "SYNDICATION_TRAP",
      expected_outcome: "REGIONAL_ONLY",
      target_milestone: "MAINSTREAM",
      events_count: 4,
    },
    {
      id: "scenario-3-multilingual-convergence",
      name: "Scenario 3: Multilingual Convergence (Independent Indic Desks)",
      description: "Same core event reported independently in Tamil, Hindi, and English regional desks without shared wire copy, maximizing cross-lingual corroboration.",
      scenario_type: "MULTILINGUAL_CONVERGENCE",
      expected_outcome: "NATIONAL_PICKUP",
      target_milestone: "NATIONAL",
      events_count: 3,
    },
    {
      id: "scenario-4-contradiction",
      name: "Scenario 4: Contradiction Gate Defense (Conflicting Factual Claims)",
      description: "Two credible sources report diametrically opposing factual claims on permit status. The Hard Contradiction Gate must halt prediction and block alerting.",
      scenario_type: "CONTRADICTION",
      expected_outcome: "CONFLICT_HALTED",
      target_milestone: "MAINSTREAM",
      events_count: 2,
    },
    {
      id: "scenario-5-false-signal",
      name: "Scenario 5: False Signal (Non-Progressing Speculation)",
      description: "A single unverified blog post makes speculative claims that are never corroborated or picked up by independent desks.",
      scenario_type: "FALSE_SIGNAL",
      expected_outcome: "DISAPPEARED",
      target_milestone: "MAINSTREAM",
      events_count: 1,
    },
    {
      id: "scenario-6-missed-story",
      name: "Scenario 6: Missed Story (Sudden Breaking Flash)",
      description: "Mainstream breaking event occurs with no prior multi-source regional reporting, demonstrating the system's honest classification of missed stories and root cause attribution.",
      scenario_type: "MISSED_STORY",
      expected_outcome: "MAINSTREAM_HEADLINE",
      target_milestone: "MAINSTREAM",
      events_count: 2,
    },
  ];
}
