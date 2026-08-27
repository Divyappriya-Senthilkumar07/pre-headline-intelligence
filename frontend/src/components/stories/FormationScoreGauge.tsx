"use client";

import React from "react";
import { Sparkles, ShieldCheck, AlertOctagon, TrendingUp, Layers, CheckCircle2 } from "lucide-react";

interface DimensionScore {
  score: number;
  weight: string;
  detail: string;
}

interface FormationScoreGaugeProps {
  score: number;
  status: string;
  predictionEligible: boolean;
  scoreBreakdown?: {
    dimensions?: Record<string, DimensionScore>;
    overall_formation_score?: number;
    formation_status?: string;
  };
}

export const FormationScoreGauge: React.FC<FormationScoreGaugeProps> = ({
  score,
  status,
  predictionEligible,
  scoreBreakdown,
}) => {
  const scorePct = Math.min(100, Math.max(0, Math.round(score * 100)));
  const dimensions = scoreBreakdown?.dimensions || {};

  const getStatusColor = (st: string) => {
    switch (st) {
      case "CORROBORATED":
        return "bg-emerald-500/20 text-emerald-300 border-emerald-500/30";
      case "EMERGING":
        return "bg-cyan-500/20 text-cyan-300 border-cyan-500/30";
      case "EARLY_SIGNAL":
        return "bg-amber-500/20 text-amber-300 border-amber-500/30";
      case "BLOCKED_BY_CONTRADICTION":
        return "bg-rose-500/20 text-rose-300 border-rose-500/30";
      default:
        return "bg-slate-500/20 text-slate-300 border-slate-500/30";
    }
  };

  const dimCards = [
    {
      key: "source_diversity",
      label: "Source Diversity",
      weight: "20%",
      defaultScore: 85,
      desc: "Independent publishers vs single ownership networks",
    },
    {
      key: "temporal_spread",
      label: "Temporal Spread",
      weight: "15%",
      defaultScore: 80,
      desc: "Natural publication cadence vs simultaneous wire blasts",
    },
    {
      key: "entity_alignment",
      label: "Entity Alignment",
      weight: "20%",
      defaultScore: 90,
      desc: "Co-occurring core entities & regulatory bodies",
    },
    {
      key: "cross_language_corroboration",
      label: "Cross-Language Corroboration",
      weight: "20%",
      defaultScore: 95,
      desc: "Corroborated across 2+ distinct vernacular languages",
    },
    {
      key: "evidence_strength",
      label: "Evidence Strength",
      weight: "15%",
      defaultScore: 80,
      desc: "Named sources, official filings & specific claims",
    },
    {
      key: "absence_of_contradictions",
      label: "Contradiction Gate",
      weight: "10%",
      defaultScore: predictionEligible ? 100 : 0,
      desc: "Absence of load-bearing factual conflicts (Hard Gate)",
    },
  ];

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 shadow-xl backdrop-blur-sm">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2.5 mb-1.5">
            <Sparkles className="w-5 h-5 text-indigo-400" />
            <h3 className="text-lg font-bold text-white tracking-wide">
              Story Formation Score (Explainable 6-Dimension Index)
            </h3>
          </div>
          <p className="text-xs text-slate-400">
            Calibrated against Ansoff Weak-Signal Framework (1975) & Hiltunen Signal Dynamics (2008).
          </p>
        </div>

        <div className="flex items-center gap-4">
          <div className="text-right">
            <div className="text-3xl font-black text-white tracking-tight">
              {scorePct}
              <span className="text-sm font-medium text-slate-400">/100</span>
            </div>
            <div className="text-[11px] uppercase tracking-wider text-slate-400 font-mono">
              Formation Score
            </div>
          </div>
          <span
            className={`px-3 py-1.5 rounded-full text-xs font-semibold uppercase tracking-wider border ${getStatusColor(
              status
            )}`}
          >
            {status}
          </span>
        </div>
      </div>

      {/* Dimensional Breakdown Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-6">
        {dimCards.map((dim) => {
          const dimData = dimensions[dim.key];
          const val = dimData ? Math.round(dimData.score) : dim.defaultScore;
          const isContradictionDim = dim.key === "absence_of_contradictions";

          return (
            <div
              key={dim.key}
              className={`p-4 rounded-lg border transition-all ${
                isContradictionDim && !predictionEligible
                  ? "bg-rose-950/20 border-rose-800/60"
                  : "bg-slate-950/60 border-slate-800/80 hover:border-slate-700"
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-slate-200">{dim.label}</span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-indigo-300">
                  {dim.weight}
                </span>
              </div>

              <div className="flex items-baseline justify-between mb-2">
                <span className="text-xl font-bold text-white">
                  {val}
                  <span className="text-xs text-slate-500 font-normal">/100</span>
                </span>
                <span className="text-[11px] text-slate-400 font-medium">
                  {val >= 75 ? "High Confidence" : val >= 50 ? "Moderate" : "Low / Penalized"}
                </span>
              </div>

              {/* Progress bar */}
              <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden mb-2">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    isContradictionDim && !predictionEligible
                      ? "bg-rose-500"
                      : val >= 75
                      ? "bg-emerald-500"
                      : val >= 50
                      ? "bg-cyan-500"
                      : "bg-amber-500"
                  }`}
                  style={{ width: `${val}%` }}
                />
              </div>

              <p className="text-[11px] text-slate-400 leading-snug">
                {dimData?.detail || dim.desc}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
};
