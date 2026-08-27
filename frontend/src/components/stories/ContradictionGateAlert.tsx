"use client";

import React, { useState } from "react";
import { AlertOctagon, ShieldCheck, CheckCircle2, RefreshCw, XCircle, ArrowRightLeft } from "lucide-react";

export interface ContradictionItem {
  id: string;
  story_id: string;
  claim_a_id: string;
  claim_b_id: string;
  claim_a_statement: string;
  claim_b_statement: string;
  claim_a_source: string;
  claim_b_source: string;
  is_load_bearing: boolean;
  status: string;
  severity: string;
  description: string;
  halted_prediction: boolean;
  detected_at?: string;
}

interface ContradictionGateAlertProps {
  storyId: string;
  contradictionStatus: string;
  predictionEligible: boolean;
  contradictions: ContradictionItem[];
  onResolutionSuccess?: () => void;
}

export const ContradictionGateAlert: React.FC<ContradictionGateAlertProps> = ({
  storyId,
  contradictionStatus,
  predictionEligible,
  contradictions,
  onResolutionSuccess,
}) => {
  const [resolvingId, setResolvingId] = useState<string | null>(null);
  const [resolveNotes, setResolveNotes] = useState<string>("");
  const [selectedContradiction, setSelectedContradiction] = useState<ContradictionItem | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const openLoadBearing = contradictions.filter(
    (c) => c.is_load_bearing && (c.status === "OPEN" || c.status === "UNRESOLVED")
  );

  const handleResolve = async (contradictionId: string) => {
    setSubmitting(true);
    try {
      const res = await fetch(
        `http://localhost:8000/api/v1/stories/${storyId}/contradictions/${contradictionId}/resolve`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            resolution_notes: resolveNotes || "Resolved by analyst verification against official registry.",
          }),
        }
      );
      if (res.ok) {
        setSelectedContradiction(null);
        setResolveNotes("");
        if (onResolutionSuccess) onResolutionSuccess();
      }
    } catch (err) {
      console.error("Resolution error:", err);
    } finally {
      setSubmitting(false);
    }
  };

  if (predictionEligible && openLoadBearing.length === 0) {
    return (
      <div className="bg-emerald-950/20 border border-emerald-500/30 rounded-xl p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold text-emerald-300">Contradiction Gate: PASS</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 font-semibold border border-emerald-500/30">
                PREDICTIONS PERMITTED
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Zero load-bearing factual contradictions detected across multilingual reporting sources.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-rose-950/30 border-2 border-rose-600/60 rounded-xl p-6 shadow-2xl backdrop-blur-md">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-rose-900/60">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-rose-600/20 text-rose-400 border border-rose-500/30">
            <AlertOctagon className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-rose-300 tracking-wide">
                CONTRADICTION GATE: PREDICTION BLOCKED
              </h3>
              <span className="px-2.5 py-0.5 rounded text-[11px] font-bold uppercase bg-rose-600 text-white tracking-wider">
                HARD HALT
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-1">
              Direct factual conflict detected on load-bearing claims. Narrative projection is halted until resolved.
            </p>
          </div>
        </div>
      </div>

      {/* Side-by-Side Claim Conflict Cards */}
      <div className="mt-4 space-y-4">
        {openLoadBearing.map((item) => (
          <div key={item.id} className="bg-slate-950/80 border border-rose-900/40 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold text-rose-400 flex items-center gap-1.5">
                <ArrowRightLeft className="w-4 h-4" />
                Factual Discrepancy #{item.id.slice(0, 8)}
              </span>
              <button
                onClick={() => setSelectedContradiction(item)}
                className="px-3 py-1 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium rounded transition-colors"
              >
                Resolve Conflict
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {/* Claim A */}
              <div className="p-3 rounded bg-slate-900/90 border border-slate-800">
                <div className="text-[10px] font-mono text-cyan-400 uppercase tracking-wider mb-1">
                  Source: {item.claim_a_source}
                </div>
                <div className="text-xs font-medium text-slate-200 leading-relaxed">
                  "{item.claim_a_statement}"
                </div>
              </div>

              {/* Claim B */}
              <div className="p-3 rounded bg-slate-900/90 border border-slate-800">
                <div className="text-[10px] font-mono text-rose-400 uppercase tracking-wider mb-1">
                  Source: {item.claim_b_source}
                </div>
                <div className="text-xs font-medium text-slate-200 leading-relaxed">
                  "{item.claim_b_statement}"
                </div>
              </div>
            </div>

            <div className="mt-2 text-[11px] text-slate-400 italic">
              Conflict note: {item.description}
            </div>
          </div>
        ))}
      </div>

      {/* Resolution Modal / Form */}
      {selectedContradiction && (
        <div className="mt-4 p-4 rounded-lg bg-slate-900 border border-indigo-500/40 animate-fadeIn">
          <h4 className="text-xs font-bold text-white mb-2">
            Analyst Conflict Resolution Note
          </h4>
          <textarea
            value={resolveNotes}
            onChange={(e) => setResolveNotes(e.target.value)}
            placeholder="Document official register verification, retractions, or authoritative primary source evidence..."
            className="w-full h-20 p-2.5 rounded bg-slate-950 border border-slate-700 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
          />
          <div className="flex justify-end gap-2 mt-2">
            <button
              onClick={() => setSelectedContradiction(null)}
              className="px-3 py-1 text-xs text-slate-400 hover:text-white"
            >
              Cancel
            </button>
            <button
              onClick={() => handleResolve(selectedContradiction.id)}
              disabled={submitting}
              className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded transition-colors disabled:opacity-50"
            >
              {submitting ? "Resolving..." : "Confirm & Unblock Prediction Gate"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
