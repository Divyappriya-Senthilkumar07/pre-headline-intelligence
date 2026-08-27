"use client";

import React from "react";
import { TrendingUp, AlertTriangle, ShieldCheck, Clock, CheckCircle2, ChevronRight } from "lucide-react";

export interface PredictionData {
  id?: string;
  formation_probability: number;
  impact_score: number;
  impact_level: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL" | string;
  current_stage: string;
  predicted_next_stage: string;
  trajectory_confidence: number;
  trajectory_reasoning: string;
  prediction_status: "ELIGIBLE" | "BLOCKED" | string;
  blocked_reason?: string | null;
  historical_support_level?: string;
  explanation: string;
}

interface PredictionCardProps {
  prediction: PredictionData | null;
  contradictionStatus: string;
}

const STAGES = ["EARLY", "REGIONAL", "NATIONAL", "MAINSTREAM"];

export const PredictionCard: React.FC<PredictionCardProps> = ({ prediction, contradictionStatus }) => {
  if (!prediction) {
    return (
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 text-center text-slate-400">
        <p>No trajectory projection generated yet. Run Phase 4 pipeline to compute.</p>
      </div>
    );
  }

  const isBlocked = prediction.prediction_status === "BLOCKED" || contradictionStatus === "PREDICTION_BLOCKED";
  const probPct = Math.round(prediction.formation_probability * 100);
  const impactPct = Math.round(prediction.impact_score * 100);

  const getImpactBadgeColor = (level: string) => {
    switch (level.toUpperCase()) {
      case "CRITICAL":
        return "bg-rose-500/20 text-rose-300 border-rose-500/40";
      case "HIGH":
        return "bg-amber-500/20 text-amber-300 border-amber-500/40";
      case "MEDIUM":
        return "bg-blue-500/20 text-blue-300 border-blue-500/40";
      default:
        return "bg-slate-500/20 text-slate-300 border-slate-500/40";
    }
  };

  const currentStageIndex = STAGES.indexOf(prediction.current_stage.toUpperCase());
  const nextStageIndex = STAGES.indexOf(prediction.predicted_next_stage.toUpperCase());

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6 shadow-xl relative overflow-hidden">
      {/* Top Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-6">
        <div className="flex items-center space-x-3">
          <div className={`p-2.5 rounded-lg ${isBlocked ? "bg-rose-500/10 text-rose-400" : "bg-emerald-500/10 text-emerald-400"}`}>
            {isBlocked ? <AlertTriangle className="w-5 h-5" /> : <TrendingUp className="w-5 h-5" />}
          </div>
          <div>
            <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
              Agent 7: Trajectory & Impact Prediction
              <span className="text-xs px-2 py-0.5 rounded-full font-mono bg-slate-800 text-slate-400 border border-slate-700">
                PROBABILITY ≠ IMPACT
              </span>
            </h3>
            <p className="text-xs text-slate-400">Separate projection of progression likelihood versus systemic significance</p>
          </div>
        </div>

        {isBlocked ? (
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-rose-500/20 text-rose-300 border border-rose-500/40 animate-pulse">
            PREDICTION BLOCKED
          </span>
        ) : (
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
            PROJECTION ACTIVE
          </span>
        )}
      </div>

      {/* Contradiction Gate Blocking Banner */}
      {isBlocked && (
        <div className="mb-6 p-4 rounded-lg bg-rose-950/40 border border-rose-500/50 text-rose-200">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
            <div>
              <h4 className="text-sm font-semibold text-rose-300">Hard Contradiction Gate Active</h4>
              <p className="text-xs text-rose-200/80 mt-1">
                {prediction.blocked_reason || "Load-bearing contradiction detected across source reports."} All forward trajectory and impact projections are halted until the underlying factual discrepancy is resolved by an intelligence analyst.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* 2-Column Metrics: Probability vs Impact */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        {/* Probability Card */}
        <div className={`p-4 rounded-xl border ${isBlocked ? "bg-slate-900/50 border-slate-800 opacity-60" : "bg-slate-800/40 border-slate-700/60"}`}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Formation Probability</span>
            <span className="text-xl font-bold font-mono text-cyan-400">{isBlocked ? "0%" : `${probPct}%`}</span>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden mb-2">
            <div
              className={`h-full transition-all duration-500 rounded-full ${isBlocked ? "bg-slate-600" : "bg-gradient-to-r from-cyan-500 to-blue-500"}`}
              style={{ width: `${isBlocked ? 0 : probPct}%` }}
            />
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Likelihood of narrative progressing from regional weak signals to broader coverage.
          </p>
        </div>

        {/* Impact Card */}
        <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/60">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Estimated Impact</span>
            <div className="flex items-center gap-2">
              <span className={`px-2 py-0.5 rounded text-xs font-semibold border ${getImpactBadgeColor(prediction.impact_level)}`}>
                {prediction.impact_level}
              </span>
              <span className="text-xl font-bold font-mono text-amber-400">{impactPct}%</span>
            </div>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden mb-2">
            <div
              className="h-full bg-gradient-to-r from-amber-500 to-rose-500 transition-all duration-500 rounded-full"
              style={{ width: `${impactPct}%` }}
            />
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Magnitude of regulatory, financial, or operational consequence if development materializes.
          </p>
        </div>
      </div>

      {/* Trajectory Stepper */}
      <div className="p-4 rounded-xl bg-slate-800/20 border border-slate-800 mb-6">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
            <Clock className="w-4 h-4 text-slate-400" />
            Signal Trajectory Stage Progression
          </span>
          <span className="text-xs font-mono text-slate-400">Confidence: {Math.round(prediction.trajectory_confidence * 100)}%</span>
        </div>

        <div className="grid grid-cols-4 gap-2">
          {STAGES.map((stage, idx) => {
            const isPast = idx < currentStageIndex;
            const isCurrent = idx === currentStageIndex;
            const isNext = idx === nextStageIndex;

            let badgeStyle = "bg-slate-900 border-slate-800 text-slate-500";
            if (isCurrent) {
              badgeStyle = "bg-cyan-500/20 border-cyan-500/60 text-cyan-300 ring-1 ring-cyan-500/40";
            } else if (isNext && !isBlocked) {
              badgeStyle = "bg-amber-500/10 border-amber-500/40 text-amber-300 border-dashed animate-pulse";
            } else if (isPast) {
              badgeStyle = "bg-slate-800 border-slate-700 text-slate-300";
            }

            return (
              <div
                key={stage}
                className={`p-2.5 rounded-lg border text-center transition-all ${badgeStyle}`}
              >
                <div className="text-[10px] font-mono uppercase tracking-wider mb-1">
                  {isCurrent ? "Current" : (isNext && !isBlocked ? "Predicted" : `Stage ${idx + 1}`)}
                </div>
                <div className="text-xs font-bold font-sans truncate">{stage}</div>
              </div>
            );
          })}
        </div>

        <p className="text-xs text-slate-400 mt-3 pt-3 border-t border-slate-800/80">
          <span className="text-slate-300 font-medium">Trajectory Rationale:</span> {prediction.trajectory_reasoning}
        </p>
      </div>

      {/* Historical Support Footer */}
      <div className="flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-800">
        <span>Historical Support: <strong className="text-slate-300">{prediction.historical_support_level || "LIMITED_HISTORICAL_DATA"}</strong></span>
        <span className="text-slate-500">Uncalibrated lead-time fabrication prohibited</span>
      </div>
    </div>
  );
};
