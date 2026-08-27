"use client";

import React, { useState } from "react";
import { Link2, ShieldCheck, FileText, CheckCircle2, ChevronRight, AlertCircle, ExternalLink, Eye } from "lucide-react";

export interface EvidenceChainItem {
  item_id: string;
  step_order: number;
  source_name: string;
  domain: string;
  claim_statement: string;
  evidence_type: string;
  evidence_excerpt: string;
  corroborating_sources: string[];
  confidence_contribution: number;
}

export interface EvidenceChainData {
  id?: string;
  chain_status: "COMPLETE" | "PARTIAL" | "INSUFFICIENT_EVIDENCE" | string;
  confidence_score: number;
  items: EvidenceChainItem[];
  has_sufficient_evidence: boolean;
}

interface EvidenceChainViewerProps {
  evidenceChain: EvidenceChainData | null;
  storyTitle: string;
}

export const EvidenceChainViewer: React.FC<EvidenceChainViewerProps> = ({ evidenceChain, storyTitle }) => {
  const [selectedItem, setSelectedItem] = useState<EvidenceChainItem | null>(null);

  if (!evidenceChain || !evidenceChain.items || evidenceChain.items.length === 0) {
    return (
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6">
        <div className="flex items-center gap-3 text-amber-400 mb-2">
          <AlertCircle className="w-5 h-5" />
          <h3 className="text-base font-semibold text-slate-100">Agent 8: Evidence & Investigation</h3>
        </div>
        <div className="p-4 rounded-lg bg-amber-950/20 border border-amber-500/30 text-amber-200/80 text-xs">
          <strong className="text-amber-300">INSUFFICIENT EVIDENCE:</strong> No structured evidence chain has been assembled for this candidate story. Under product integrity rules, alerts without evidence are strictly withheld.
        </div>
      </div>
    );
  }

  const isInsufficient = evidenceChain.chain_status === "INSUFFICIENT_EVIDENCE";

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6 shadow-xl relative">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-6">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-lg bg-indigo-500/10 text-indigo-400">
            <Link2 className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
              Agent 8: Structured Evidence Chain
              <span className="text-xs px-2 py-0.5 rounded-full font-mono bg-indigo-500/20 text-indigo-300 border border-indigo-500/40">
                AUDITABLE PROVENANCE
              </span>
            </h3>
            <p className="text-xs text-slate-400">
              Deterministic evidence graph (Source → Claim → Short Excerpt → Corroboration → Confidence)
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-slate-400">
            Chain Confidence: <strong className="text-indigo-300">{Math.round(evidenceChain.confidence_score * 100)}%</strong>
          </span>
          <span
            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${
              isInsufficient
                ? "bg-amber-500/20 text-amber-300 border-amber-500/40"
                : "bg-indigo-500/20 text-indigo-300 border-indigo-500/40"
            }`}
          >
            {evidenceChain.chain_status}
          </span>
        </div>
      </div>

      {/* Provenance Steps List */}
      <div className="space-y-3">
        {evidenceChain.items.map((item, index) => {
          const isSelected = selectedItem?.item_id === item.item_id;

          return (
            <div
              key={item.item_id || index}
              onClick={() => setSelectedItem(item)}
              className={`p-4 rounded-xl border transition-all cursor-pointer ${
                isSelected
                  ? "bg-indigo-950/30 border-indigo-500/80 shadow-lg ring-1 ring-indigo-500/40"
                  : "bg-slate-800/30 border-slate-800 hover:border-slate-700 hover:bg-slate-800/60"
              }`}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-slate-800 border border-slate-700 text-slate-300 text-xs font-mono flex items-center justify-center shrink-0 mt-0.5">
                    {item.step_order || index + 1}
                  </div>
                  <div>
                    <div className="flex items-center gap-2 flex-wrap mb-1">
                      <span className="text-xs font-semibold text-slate-200">{item.source_name}</span>
                      <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 border border-slate-700">
                        {item.domain}
                      </span>
                      <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/30">
                        {item.evidence_type}
                      </span>
                    </div>

                    <p className="text-xs text-slate-300 font-medium line-clamp-2">{item.claim_statement}</p>

                    <p className="text-[11px] text-slate-400 italic mt-1 line-clamp-1 bg-slate-900/60 px-2 py-1 rounded border border-slate-800">
                      {item.evidence_excerpt}
                    </p>
                  </div>
                </div>

                <div className="flex flex-col items-end shrink-0">
                  <span className="text-xs font-mono font-bold text-emerald-400">
                    +{Math.round(item.confidence_contribution * 100)}%
                  </span>
                  <span className="text-[10px] text-slate-500 mt-1">
                    {item.corroborating_sources.length} corroborating
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Detail Drawer / Modal for Selected Evidence Step */}
      {selectedItem && (
        <div className="mt-4 p-4 rounded-xl bg-slate-950 border border-indigo-500/40 text-slate-200 animate-in fade-in duration-200">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-indigo-300 flex items-center gap-2">
              <Eye className="w-3.5 h-3.5" />
              Evidence Step #{selectedItem.step_order} Deep Audit
            </h4>
            <button
              onClick={() => setSelectedItem(null)}
              className="text-xs text-slate-400 hover:text-slate-200 underline"
            >
              Close
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div>
              <span className="text-slate-400 font-medium">Claim Statement:</span>
              <p className="mt-1 text-slate-200 font-medium">{selectedItem.claim_statement}</p>
            </div>
            <div>
              <span className="text-slate-400 font-medium">Attributed Short Excerpt:</span>
              <p className="mt-1 text-slate-300 italic bg-slate-900 p-2 rounded border border-slate-800">
                {selectedItem.evidence_excerpt}
              </p>
            </div>
          </div>

          <div className="mt-3 pt-3 border-t border-slate-900 flex items-center justify-between text-[11px] text-slate-400">
            <span>Source: <strong className="text-slate-300">{selectedItem.source_name}</strong> ({selectedItem.domain})</span>
            <span className="text-slate-500">Short excerpt format strictly enforces copyright compliance</span>
          </div>
        </div>
      )}
    </div>
  );
};
