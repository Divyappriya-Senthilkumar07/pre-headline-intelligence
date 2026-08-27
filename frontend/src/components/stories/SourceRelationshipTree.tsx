"use client";

import React from "react";
import { ShieldCheck, Copy, Share2, GitFork, CheckCircle, ExternalLink, HelpCircle } from "lucide-react";

export interface SourceArticleNode {
  id: string;
  title: string;
  source_name: string;
  domain: string;
  url: string;
  language: string;
  relationship_type?: string;
  is_original?: boolean;
  syndication_origin?: string | null;
}

interface SourceRelationshipTreeProps {
  articles: SourceArticleNode[];
  independentCount: number;
  totalCount: number;
}

export const SourceRelationshipTree: React.FC<SourceRelationshipTreeProps> = ({
  articles,
  independentCount,
  totalCount,
}) => {
  const getClassificationBadge = (type?: string, isOriginal?: boolean) => {
    const t = (type || (isOriginal ? "INDEPENDENT" : "SYNDICATED")).toUpperCase();

    switch (t) {
      case "ORIGINAL":
      case "INDEPENDENT":
        return {
          label: "INDEPENDENT REPORTING",
          color: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40",
          icon: ShieldCheck,
        };
      case "SYNDICATED":
        return {
          label: "WIRE SYNDICATION",
          color: "bg-amber-500/20 text-amber-300 border-amber-500/40",
          icon: Share2,
        };
      case "COPIED":
        return {
          label: "DIRECT DERIVATIVE / COPIED",
          color: "bg-rose-500/20 text-rose-300 border-rose-500/40",
          icon: Copy,
        };
      case "RELATED":
        return {
          label: "RELATED CONTEXT",
          color: "bg-blue-500/20 text-blue-300 border-blue-500/40",
          icon: GitFork,
        };
      default:
        return {
          label: "UNKNOWN ORIGIN",
          color: "bg-slate-700/50 text-slate-300 border-slate-600",
          icon: HelpCircle,
        };
    }
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6 shadow-xl space-y-6">
      {/* Header with Visual Separation Metric */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-lg bg-cyan-500/10 text-cyan-400">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
              Agent 5: Source Independence & Syndication Tree
              <span className="text-xs px-2 py-0.5 rounded-full font-mono bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
                DISCOUNTING DERIVATIVES
              </span>
            </h3>
            <p className="text-xs text-slate-400">Distinguishing genuine independent primary reporting from wire republication</p>
          </div>
        </div>

        {/* Visual Callout: Articles != Independent Sources */}
        <div className="flex items-center gap-3 bg-slate-950 p-2.5 rounded-xl border border-slate-800">
          <div className="text-center px-3 border-r border-slate-800">
            <span className="text-[10px] font-mono uppercase text-slate-500 block">Total Articles</span>
            <span className="text-base font-bold font-mono text-slate-200">{totalCount}</span>
          </div>
          <div className="text-center px-3">
            <span className="text-[10px] font-mono uppercase text-cyan-400 block">Independent Desks</span>
            <span className="text-base font-bold font-mono text-cyan-400">{independentCount}</span>
          </div>
        </div>
      </div>

      {/* Sources List */}
      <div className="space-y-3">
        {articles.map((art, idx) => {
          const badge = getClassificationBadge(art.relationship_type, art.is_original);
          const Icon = badge.icon;

          return (
            <div
              key={art.id || idx}
              className="p-4 rounded-xl bg-slate-800/30 border border-slate-800 hover:border-slate-700 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-xs font-bold text-slate-100">{art.source_name}</span>
                  <span className="text-[10px] font-mono text-slate-400 px-1.5 py-0.2 rounded bg-slate-900 border border-slate-800">
                    {art.domain}
                  </span>
                  <span className="text-[10px] font-mono uppercase px-1.5 py-0.2 rounded bg-purple-500/10 text-purple-400 border border-purple-500/30">
                    {art.language}
                  </span>
                </div>
                <p className="text-xs text-slate-300 line-clamp-1">{art.title}</p>
              </div>

              <div className="flex items-center gap-3 shrink-0">
                <span
                  className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold border ${badge.color}`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  {badge.label}
                </span>

                {art.url && art.url.startsWith("http") && (
                  <a
                    href={art.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-1.5 text-slate-400 hover:text-cyan-400 transition-colors"
                    title="External link"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
