"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Radio,
  Clock,
  ShieldCheck,
  Languages,
  ChevronRight,
  TrendingUp,
  AlertTriangle,
  Play,
  CheckCircle2,
  ExternalLink,
  Sparkles,
  Link2,
  ThumbsUp,
  ThumbsDown,
  Search,
  SlidersHorizontal,
  ArrowUpDown,
  RotateCcw,
} from "lucide-react";

interface AlertFeedItem {
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

export default function IntelligenceFeedPage() {
  const [alerts, setAlerts] = useState<AlertFeedItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [pipelineRunning, setPipelineRunning] = useState(false);
  const [pipelinePhase, setPipelinePhase] = useState<string>("");
  const [feedbackSuccess, setFeedbackSuccess] = useState<string | null>(null);
  const [ingestStatus, setIngestStatus] = useState<{
    is_live_signal?: boolean;
    last_successful_ingestion?: string | null;
    current_status?: string;
    total_articles_count?: number;
  } | null>(null);

  // Search & Filter States
  const [searchQuery, setSearchQuery] = useState("");
  const [minFormationScore, setMinFormationScore] = useState<number>(0);
  const [selectedLanguage, setSelectedLanguage] = useState<string>("ALL");
  const [selectedContradictionStatus, setSelectedContradictionStatus] = useState<string>("ALL");
  const [sortBy, setSortBy] = useState<string>("ranking_score");
  const [showFilters, setShowFilters] = useState(false);

  const fetchIngestStatus = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/ingest/status");
      if (res.ok) {
        const data = await res.json();
        setIngestStatus(data);
      }
    } catch (e) {
      console.debug("Status fetch note:", e);
    }
  };

  const fetchEmergingFeed = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (searchQuery.trim()) params.append("search", searchQuery.trim());
      if (minFormationScore > 0) params.append("min_formation_score", String(minFormationScore));
      if (selectedLanguage !== "ALL") params.append("language", selectedLanguage);
      if (selectedContradictionStatus !== "ALL") params.append("contradiction_status", selectedContradictionStatus);
      if (sortBy) params.append("sort_by", sortBy);

      const url = `http://localhost:8000/api/v1/stories/emerging?${params.toString()}`;
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setAlerts(data);
      } else {
        setAlerts([]);
      }
    } catch (err) {
      console.warn("Feed fetch note:", err);
      setAlerts([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIngestStatus();
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchEmergingFeed();
    }, 250);
    return () => clearTimeout(timer);
  }, [searchQuery, minFormationScore, selectedLanguage, selectedContradictionStatus, sortBy]);

  const runFullIntelligencePipeline = async () => {
    setPipelineRunning(true);
    setPipelinePhase("Ingesting Live GDELT & RSS News...");
    try {
      // 1. Call full pipeline execute endpoint
      const res = await fetch("http://localhost:8000/api/v1/pipeline/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      if (!res.ok) {
        // Fallback: run individual phases
        setPipelinePhase("Running Intelligence Pipeline...");
        await fetch("http://localhost:8000/api/v1/pipeline/run-phase2", { method: "POST" });
        await fetch("http://localhost:8000/api/v1/pipeline/run-phase3", { method: "POST" });
        await fetch("http://localhost:8000/api/v1/pipeline/run-phase4", { method: "POST" });
      }
      await fetchEmergingFeed();
      await fetchIngestStatus();
    } catch (err) {
      console.error("Pipeline run error:", err);
    } finally {
      setPipelineRunning(false);
      setPipelinePhase("");
    }
  };

  const submitFeedback = async (alertId: string, rating: "THUMBS_UP" | "THUMBS_DOWN") => {
    try {
      await fetch(`http://localhost:8000/api/v1/alerts/${alertId}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rating, notes: "Verified in analyst feed" }),
      });
      setFeedbackSuccess(alertId);
      setTimeout(() => setFeedbackSuccess(null), 3000);
    } catch (err) {
      console.error("Feedback error:", err);
    }
  };

  const resetFilters = () => {
    setSearchQuery("");
    setMinFormationScore(0);
    setSelectedLanguage("ALL");
    setSelectedContradictionStatus("ALL");
    setSortBy("ranking_score");
  };

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-6">
      {/* Top Hero Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 pb-6 border-b border-slate-800">
        <div className="space-y-2">
          {ingestStatus?.is_live_signal ? (
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-md bg-emerald-500/10 text-emerald-400 text-xs font-mono border border-emerald-500/30">
              <Radio className="w-3.5 h-3.5 animate-pulse text-emerald-400" />
              LIVE MEDIA SIGNAL &bull; Last Ingested:{" "}
              {ingestStatus.last_successful_ingestion
                ? new Date(ingestStatus.last_successful_ingestion).toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                    second: "2-digit",
                  })
                : "Active"}
            </div>
          ) : (
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-md bg-cyan-500/10 text-cyan-400 text-xs font-mono border border-cyan-500/20">
              <Radio className="w-3.5 h-3.5 animate-pulse" />
              RANKED INTELLIGENCE STREAM (AGENT 9 ORCHESTRATION)
            </div>
          )}
          <h1 className="text-3xl font-bold tracking-tight text-white">
            Pre-Headline Intelligence Feed
          </h1>
          <p className="text-sm text-slate-400 max-w-2xl">
            Ranked by <strong className="text-slate-300">Urgency &times; Probability &times; Impact</strong>. We don&apos;t just detect a story is emerging &mdash; we prove it, before it&apos;s obvious, in the language it&apos;s actually forming in.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={runFullIntelligencePipeline}
            disabled={pipelineRunning}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-xs font-semibold shadow-lg shadow-cyan-500/20 transition-all disabled:opacity-50"
          >
            <Play className={`w-3.5 h-3.5 ${pipelineRunning ? "animate-spin" : ""}`} />
            {pipelineRunning ? (pipelinePhase || "Processing Pipeline...") : "Execute Intelligence Pipeline"}
          </button>
        </div>
      </div>

      {/* Search & Analyst Filters Bar */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row items-center gap-3">
          <div className="relative flex-1 w-full">
            <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by story headline, tracked entities, claims, or keywords..."
              className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition-colors"
            />
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`inline-flex items-center gap-1.5 px-3.5 py-2.5 rounded-xl border text-xs font-semibold transition-colors ${
                showFilters || minFormationScore > 0 || selectedLanguage !== "ALL" || selectedContradictionStatus !== "ALL"
                  ? "bg-cyan-500/20 text-cyan-300 border-cyan-500/50"
                  : "bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200"
              }`}
            >
              <SlidersHorizontal className="w-3.5 h-3.5" />
              Filters {(minFormationScore > 0 || selectedLanguage !== "ALL" || selectedContradictionStatus !== "ALL") && "•"}
            </button>

            {/* Sort Dropdown */}
            <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs">
              <ArrowUpDown className="w-3.5 h-3.5 text-slate-500" />
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="bg-transparent text-slate-300 focus:outline-none text-xs font-mono"
              >
                <option value="ranking_score">Sort: Ranking Score</option>
                <option value="formation_score">Sort: Formation Score</option>
                <option value="probability">Sort: Probability</option>
                <option value="impact">Sort: Impact</option>
                <option value="urgency">Sort: Urgency</option>
                <option value="independent_sources">Sort: Independent Sources</option>
                <option value="latest_update">Sort: Latest Update</option>
              </select>
            </div>
          </div>
        </div>

        {/* Expandable Filter Drawer */}
        {showFilters && (
          <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs animate-fade-in">
            <div>
              <div className="flex items-center justify-between mb-1.5 font-medium text-slate-300">
                <span>Min Formation Score:</span>
                <span className="font-mono text-cyan-400 font-bold">{minFormationScore}/100</span>
              </div>
              <input
                type="range"
                min={0}
                max={90}
                step={10}
                value={minFormationScore}
                onChange={(e) => setMinFormationScore(Number(e.target.value))}
                className="w-full accent-cyan-500"
              />
            </div>

            <div>
              <label className="block text-slate-300 font-medium mb-1.5">Language</label>
              <select
                value={selectedLanguage}
                onChange={(e) => setSelectedLanguage(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
              >
                <option value="ALL">All Languages (Tamil, Hindi, English)</option>
                <option value="ta">Tamil (தமிழ்)</option>
                <option value="hi">Hindi (हिन्दी)</option>
                <option value="en">English</option>
              </select>
            </div>

            <div>
              <label className="block text-slate-300 font-medium mb-1.5">Contradiction Status</label>
              <select
                value={selectedContradictionStatus}
                onChange={(e) => setSelectedContradictionStatus(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
              >
                <option value="ALL">All Contradiction States</option>
                <option value="CLEAR">Gate Clear Only</option>
                <option value="PREDICTION_BLOCKED">Prediction Blocked Only</option>
                <option value="RESOLVED">Resolved Only</option>
              </select>
            </div>

            <div className="sm:col-span-3 flex justify-end pt-2 border-t border-slate-800/80">
              <button
                onClick={resetFilters}
                className="inline-flex items-center gap-1 text-[11px] text-slate-400 hover:text-slate-200 transition-colors"
              >
                <RotateCcw className="w-3 h-3" /> Reset all filters
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Main Ranked Feed List */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-400">
            Ranked Active Intelligence Alerts ({alerts.length})
          </h2>
          <span className="text-xs text-slate-500 font-mono">Defense-in-depth gate guarded</span>
        </div>

        {loading ? (
          <div className="p-12 text-center text-slate-400 bg-slate-900/40 rounded-2xl border border-slate-800">
            <div className="w-8 h-8 border-4 border-cyan-500/20 border-t-cyan-500 rounded-full animate-spin mx-auto mb-3" />
            <p className="text-xs font-mono">Loading Ranked Intelligence Feed...</p>
          </div>
        ) : alerts.length === 0 ? (
          <div className="p-12 text-center text-slate-400 bg-slate-900/40 rounded-2xl border border-slate-800">
            <Radio className="w-8 h-8 text-slate-600 mx-auto mb-3" />
            <p className="text-sm font-medium text-slate-300">No emerging stories meet your current filters.</p>
            <p className="text-xs text-slate-500 mt-1">Adjust your filters or run the intelligence pipeline.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {alerts.map((item, index) => {
              const isBlocked = item.status === "BLOCKED" || item.contradiction_status === "PREDICTION_BLOCKED";
              const probPct = Math.round(item.probability * 100);
              const impactPct = Math.round(item.impact * 100);
              const urgencyPct = Math.round(item.urgency * 100);

              const dateObj = new Date(item.created_at);
              const timeFormatted = isNaN(dateObj.getTime())
                ? "Active Lead"
                : dateObj.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

              return (
                <div
                  key={item.id || index}
                  className={`p-6 rounded-2xl border transition-all relative overflow-hidden backdrop-blur-sm ${
                    isBlocked
                      ? "bg-rose-950/20 border-rose-500/40 opacity-95"
                      : index === 0
                      ? "bg-gradient-to-r from-slate-900 via-cyan-950/20 to-slate-900 border-cyan-500/50 shadow-xl shadow-cyan-500/5 ring-1 ring-cyan-500/30"
                      : "bg-slate-900/80 border-slate-800 hover:border-slate-700"
                  }`}
                >
                  <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
                    {/* Left Details */}
                    <div className="space-y-3 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        {/* Rank Badge */}
                        <span className="text-xs font-mono font-bold px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                          #{index + 1} RANK {item.ranking_score.toFixed(3)}
                        </span>

                        {/* Status Badge */}
                        {isBlocked ? (
                          <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/40 flex items-center gap-1">
                            <AlertTriangle className="w-3 h-3" /> PREDICTION BLOCKED
                          </span>
                        ) : (
                          <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 flex items-center gap-1">
                            <CheckCircle2 className="w-3 h-3" /> FORMING INTELLIGENCE
                          </span>
                        )}

                        {/* VISUAL SEPARATION: Articles != Independent Sources */}
                        <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-950 text-slate-300 border border-slate-800 flex items-center gap-1">
                          <ShieldCheck className="w-3 h-3 text-cyan-400" />
                          <strong className="text-cyan-300">{item.independent_source_count} Independent Sources</strong>
                        </span>

                        <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700 flex items-center gap-1">
                          <Languages className="w-3 h-3 text-purple-400" />
                          {item.languages.map((l) => l.toUpperCase()).join(", ")}
                        </span>

                        <span className="text-[11px] font-mono text-slate-500 flex items-center gap-1">
                          <Clock className="w-3 h-3" /> {timeFormatted}
                        </span>
                      </div>

                      {/* Headline in progress */}
                      <div>
                        <h3 className="text-lg md:text-xl font-bold text-white tracking-tight">
                          {item.headline_in_progress}
                        </h3>
                        <p className="text-xs md:text-sm text-slate-300 mt-1 leading-relaxed">
                          {item.why_it_matters || "Insufficient evidence for a reliable explanation."}
                        </p>
                      </div>

                      {/* Decoupled Metrics: Urgency, Probability, Impact */}
                      <div className="grid grid-cols-3 gap-3 pt-2 max-w-lg">
                        <div className="p-2 rounded-lg bg-slate-950/60 border border-slate-800">
                          <span className="text-[10px] font-mono text-slate-400 uppercase">Urgency</span>
                          <div className="text-sm font-bold font-mono text-cyan-400">{urgencyPct}%</div>
                        </div>
                        <div className="p-2 rounded-lg bg-slate-950/60 border border-slate-800">
                          <span className="text-[10px] font-mono text-slate-400 uppercase">Probability</span>
                          <div className="text-sm font-bold font-mono text-blue-400">{isBlocked ? "0%" : `${probPct}%`}</div>
                        </div>
                        <div className="p-2 rounded-lg bg-slate-950/60 border border-slate-800">
                          <span className="text-[10px] font-mono text-slate-400 uppercase">Impact</span>
                          <div className="text-sm font-bold font-mono text-amber-400">{item.impact_level} ({impactPct}%)</div>
                        </div>
                      </div>
                    </div>

                    {/* Right Actions & Investigation Link */}
                    <div className="flex flex-col items-end justify-between gap-4 shrink-0">
                      <Link
                        href={`/stories/${item.story_id}`}
                        className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-100 text-xs font-semibold border border-slate-700 shadow-md transition-all group"
                      >
                        Inspect Evidence Chain & Copilot
                        <ChevronRight className="w-4 h-4 text-slate-400 group-hover:translate-x-1 transition-transform" />
                      </Link>

                      {/* Feedback buttons */}
                      <div className="flex items-center gap-2 text-xs text-slate-400">
                        <span>Feedback:</span>
                        <button
                          onClick={() => submitFeedback(item.id, "THUMBS_UP")}
                          className="p-1.5 rounded-md hover:bg-slate-800 hover:text-emerald-400 transition-colors"
                          title="Useful Alert"
                        >
                          <ThumbsUp className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => submitFeedback(item.id, "THUMBS_DOWN")}
                          className="p-1.5 rounded-md hover:bg-slate-800 hover:text-rose-400 transition-colors"
                          title="Not Useful"
                        >
                          <ThumbsDown className="w-4 h-4" />
                        </button>
                        {feedbackSuccess === item.id && (
                          <span className="text-[10px] text-emerald-400 font-mono animate-fade-in">Saved!</span>
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
    </div>
  );
}

function getFallbackFeed(): AlertFeedItem[] {
  return [
    {
      id: "alert-demo-01",
      story_id: "story-seed-001",
      alert_type: "EMERGING_STORY",
      headline_in_progress: "Emerging: State Pollution Control Board Compliance Probe at Company X",
      why_it_matters:
        "Multi-source regional corroboration in Tamil and English indicates unannounced regulatory review at manufacturing plant.",
      urgency: 0.85,
      probability: 0.82,
      impact: 0.88,
      impact_level: "HIGH",
      ranking_score: 0.613,
      ranking_explanation: "Ranked #1 (Urgency: 85%, Prob: 82%, Impact: 88%).",
      formation_score: 88.0,
      independent_source_count: 3,
      language_count: 2,
      languages: ["ta", "en"],
      evidence_available: true,
      contradiction_status: "CLEAR",
      prediction_status: "ELIGIBLE",
      status: "ACTIVE",
      created_at: new Date().toISOString(),
    },
    {
      id: "alert-demo-02",
      story_id: "story-seed-002",
      alert_type: "REGULATORY_DISPUTE",
      headline_in_progress: "Halted: Company X Plant Expansion Permit Approval Status",
      why_it_matters:
        "Conflicting statements between official registry and company PR regarding license grant.",
      urgency: 0.70,
      probability: 0.0,
      impact: 0.85,
      impact_level: "HIGH",
      ranking_score: 0.0,
      ranking_explanation: "ALERT BLOCKED: Load-bearing contradiction detected. Investigation required.",
      formation_score: 75.0,
      independent_source_count: 2,
      language_count: 1,
      languages: ["en"],
      evidence_available: true,
      contradiction_status: "PREDICTION_BLOCKED",
      prediction_status: "BLOCKED",
      status: "BLOCKED",
      created_at: new Date().toISOString(),
    },
  ];
}
