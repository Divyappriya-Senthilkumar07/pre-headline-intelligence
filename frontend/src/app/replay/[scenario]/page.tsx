"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  PlayCircle,
  PauseCircle,
  RotateCcw,
  StepForward,
  ChevronLeft,
  Clock,
  Radio,
  ShieldCheck,
  Languages,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  Lock,
  Sparkles,
  Layers,
  ArrowRight,
} from "lucide-react";

interface ReplayTimelineStep {
  step: number;
  timestamp: string;
  source_name: string;
  title: string;
  language: string;
  formation_score: number;
  independent_sources: number;
  total_articles: number;
  contradiction_status: string;
  is_prediction_blocked: boolean;
  probability: number;
  impact: number;
  urgency: number;
  ranking_score: number;
  alert_fired: boolean;
  is_valid_early_alert: boolean;
  story_state: string;
}

interface ReplayRunData {
  scenario_id: string;
  scenario_name: string;
  scenario_type: string;
  description: string;
  expected_outcome: string;
  target_milestone: string;
  target_milestone_time?: string | null;
  first_valid_alert_time?: string | null;
  first_valid_alert_snapshot?: {
    step: number;
    timestamp: string;
    formation_score: number;
    probability: number;
    impact: number;
    independent_sources: number;
    ranking_score: number;
  } | null;
  lead_time_hours?: number | null;
  lead_time_minutes?: number | null;
  lead_time_status: string;
  total_steps: number;
  completed_steps: number;
  timeline: ReplayTimelineStep[];
}

export default function HistoricalReplayPlayerPage() {
  const params = useParams();
  const scenarioId = Array.isArray(params?.scenario)
    ? params.scenario[0]
    : (params?.scenario as string) || "scenario-1-early-detection";

  const [replayData, setReplayData] = useState<ReplayRunData | null>(null);
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1);
  const [loading, setLoading] = useState(true);

  // Fetch full replay data
  const fetchReplay = async (step?: number) => {
    try {
      const url = step
        ? `http://localhost:8000/api/v1/replay/scenarios/${scenarioId}/run?step=${step}`
        : `http://localhost:8000/api/v1/replay/scenarios/${scenarioId}/run`;
      const res = await fetch(url, { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        setReplayData(data);
      }
    } catch (err) {
      console.warn("Replay fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReplay(currentStep);
  }, [scenarioId, currentStep]);

  // Autoplay ticker
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    if (isPlaying && replayData && currentStep < replayData.total_steps) {
      const delayMs = Math.max(1000 / playbackSpeed, 400);
      interval = setInterval(() => {
        setCurrentStep((prev) => {
          if (prev >= replayData.total_steps) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, delayMs);
    } else if (replayData && currentStep >= replayData.total_steps) {
      setIsPlaying(false);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isPlaying, playbackSpeed, currentStep, replayData]);

  const handleReset = () => {
    setIsPlaying(false);
    setCurrentStep(1);
  };

  const handleStepForward = () => {
    if (replayData && currentStep < replayData.total_steps) {
      setCurrentStep((prev) => prev + 1);
    }
  };

  if (loading || !replayData) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-4 border-cyan-500/20 border-t-cyan-500 rounded-full animate-spin" />
          <span className="text-sm font-medium text-slate-400 font-mono">Initializing Historical Replay Engine...</span>
        </div>
      </div>
    );
  }

  const activeSnapshot = replayData.timeline[currentStep - 1] || replayData.timeline[0];
  const activeTimeStr = new Date(activeSnapshot.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-8">
      {/* Top Breadcrumb & No-Leakage Badge */}
      <div className="flex items-center justify-between">
        <Link
          href="/replay"
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors"
        >
          <ChevronLeft className="w-4 h-4" /> Back to Replay Catalog
        </Link>
        <div className="flex items-center gap-2">
          <span className="text-xs px-2.5 py-1 rounded-full font-mono bg-emerald-950/40 text-emerald-300 border border-emerald-500/40 flex items-center gap-1">
            <Lock className="w-3 h-3" /> NO FUTURE LEAKAGE GUARANTEE
          </span>
          <span className="text-xs px-2.5 py-1 rounded-full font-mono bg-slate-800 text-slate-400 border border-slate-700 uppercase">
            {replayData.scenario_type}
          </span>
        </div>
      </div>

      {/* Header Banner */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 md:p-8 shadow-2xl backdrop-blur-sm space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2 max-w-3xl">
            <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-md bg-cyan-500/10 text-cyan-400 text-xs font-mono border border-cyan-500/20">
              <PlayCircle className="w-3.5 h-3.5" />
              CHRONOLOGICAL BELIEF STATE RECONSTRUCTION
            </div>
            <h1 className="text-2xl md:text-3xl font-bold text-white tracking-tight">
              {replayData.scenario_name}
            </h1>
            <p className="text-xs md:text-sm text-slate-300 leading-relaxed">
              {replayData.description}
            </p>
          </div>

          {/* Lead-Time Benchmark Card */}
          <div className="p-4 rounded-xl bg-slate-950 border border-cyan-500/30 text-right shrink-0 shadow-lg min-w-[200px]">
            <span className="text-[10px] text-slate-400 uppercase font-mono block">MEASURED LEAD TIME</span>
            <div className="text-2xl font-bold font-mono text-cyan-400 mt-0.5">
              {replayData.lead_time_hours !== null && replayData.lead_time_hours !== undefined
                ? `${replayData.lead_time_hours} HOURS`
                : replayData.lead_time_status.replace(/_/g, " ")}
            </div>
            <span className="text-[11px] text-slate-400 block font-mono mt-0.5">
              {replayData.first_valid_alert_time
                ? `${new Date(replayData.first_valid_alert_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} → ${
                    replayData.target_milestone_time
                      ? new Date(replayData.target_milestone_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
                      : "Ongoing"
                  }`
                : "No valid alert before milestone"}
            </span>
          </div>
        </div>

        {/* Player Controls Bar */}
        <div className="pt-4 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-4">
          {/* Play/Pause/Step/Reset */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold shadow-lg shadow-cyan-500/20 transition-all"
            >
              {isPlaying ? <PauseCircle className="w-4 h-4" /> : <PlayCircle className="w-4 h-4" />}
              {isPlaying ? "Pause" : "Play Timeline"}
            </button>
            <button
              onClick={handleStepForward}
              disabled={currentStep >= replayData.total_steps}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 disabled:opacity-40 transition-colors"
            >
              <StepForward className="w-4 h-4" /> Step
            </button>
            <button
              onClick={handleReset}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-colors"
            >
              <RotateCcw className="w-4 h-4" /> Reset
            </button>
          </div>

          {/* Clock & Step Indicator */}
          <div className="flex items-center gap-4 text-xs font-mono">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800">
              <Clock className="w-3.5 h-3.5 text-cyan-400" />
              <span className="text-slate-400">Replay Clock: </span>
              <strong className="text-white text-sm">{activeTimeStr}</strong>
            </div>

            <div className="px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-300">
              Step <strong className="text-cyan-400">{currentStep}</strong> of {replayData.total_steps}
            </div>

            {/* Speed Selector */}
            <div className="flex items-center gap-1 bg-slate-950 border border-slate-800 rounded-lg p-1">
              {[1, 2, 5].map((speed) => (
                <button
                  key={speed}
                  onClick={() => setPlaybackSpeed(speed)}
                  className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                    playbackSpeed === speed
                      ? "bg-cyan-500 text-slate-950"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {speed}x
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Belief State Cards (What the system knew at Time T) */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 shadow-xl">
          <span className="text-[10px] font-mono text-slate-400 uppercase">Formation Score</span>
          <div className="text-xl font-bold font-mono text-cyan-400 mt-1">
            {Math.round(activeSnapshot.formation_score)}/100
          </div>
          <span className="text-[10px] text-slate-500 mt-0.5 block">{activeSnapshot.story_state}</span>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 shadow-xl">
          <span className="text-[10px] font-mono text-slate-400 uppercase">Independent Desks</span>
          <div className="text-xl font-bold font-mono text-indigo-400 mt-1">
            {activeSnapshot.independent_sources} Desks
          </div>
          <span className="text-[10px] text-slate-500 mt-0.5 block">{activeSnapshot.total_articles} total articles</span>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 shadow-xl">
          <span className="text-[10px] font-mono text-slate-400 uppercase">Probability / Impact</span>
          <div className="text-xl font-bold font-mono text-blue-400 mt-1">
            {Math.round(activeSnapshot.probability * 100)}% / {Math.round(activeSnapshot.impact * 100)}%
          </div>
          <span className="text-[10px] text-slate-500 mt-0.5 block">Stage: {activeSnapshot.story_state.slice(0, 18)}</span>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 shadow-xl">
          <span className="text-[10px] font-mono text-slate-400 uppercase">Alert & Gate State</span>
          <div className="text-sm font-bold font-mono mt-1">
            {activeSnapshot.is_prediction_blocked ? (
              <span className="text-rose-400 font-bold">PREDICTION BLOCKED</span>
            ) : activeSnapshot.is_valid_early_alert ? (
              <span className="text-emerald-400 font-bold">🚨 EARLY ALERT FIRED</span>
            ) : (
              <span className="text-amber-400 font-bold">MONITORING</span>
            )}
          </div>
          <span className="text-[10px] text-slate-500 mt-0.5 block">
            Rank Score: {activeSnapshot.ranking_score.toFixed(3)}
          </span>
        </div>
      </div>

      {/* Chronological Event Stream */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-400">
            Chronological Information Sequence (Step 1 to {currentStep})
          </h2>
          <span className="text-xs text-slate-500 font-mono">
            {replayData.total_steps - currentStep} future events masked
          </span>
        </div>

        <div className="space-y-3">
          {replayData.timeline.slice(0, currentStep).map((evt, idx) => {
            const isLatest = idx === currentStep - 1;
            const evtTime = new Date(evt.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

            return (
              <div
                key={evt.step}
                className={`p-5 rounded-2xl border transition-all relative overflow-hidden backdrop-blur-sm ${
                  isLatest
                    ? "bg-slate-900 border-cyan-500/50 shadow-xl shadow-cyan-500/5 ring-1 ring-cyan-500/30"
                    : "bg-slate-900/50 border-slate-800/80 opacity-70"
                }`}
              >
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="space-y-1.5 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-xs font-mono font-bold px-2.5 py-0.5 rounded bg-slate-950 text-cyan-400 border border-slate-800">
                        {evtTime}
                      </span>
                      <span className="text-xs font-semibold text-slate-200">
                        {evt.source_name}
                      </span>
                      <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-purple-500/10 text-purple-300 border border-purple-500/30 uppercase">
                        {evt.language}
                      </span>
                      {evt.is_valid_early_alert && (
                        <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 animate-pulse">
                          🚨 FIRST VALID ALERT
                        </span>
                      )}
                    </div>

                    <h3 className="text-sm font-bold text-white tracking-tight">{evt.title}</h3>
                  </div>

                  <div className="flex items-center gap-4 text-xs font-mono shrink-0">
                    <div className="text-right">
                      <span className="text-[10px] text-slate-500 block">FORMATION</span>
                      <span className="text-cyan-400 font-bold">{Math.round(evt.formation_score)}/100</span>
                    </div>
                    <div className="text-right">
                      <span className="text-[10px] text-slate-500 block">INDEP SOURCES</span>
                      <span className="text-indigo-300 font-bold">{evt.independent_sources}</span>
                    </div>
                    <div className="text-right">
                      <span className="text-[10px] text-slate-500 block">PROBABILITY</span>
                      <span className="text-blue-400 font-bold">{Math.round(evt.probability * 100)}%</span>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
