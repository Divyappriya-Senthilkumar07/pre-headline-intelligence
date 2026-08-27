"use client";

import React from "react";
import { ShieldCheck, Network, Copy, CheckCircle2, Clock, Globe, Split } from "lucide-react";

interface StoryArticleItem {
  id: string;
  title: string;
  source_name: string;
  domain: string;
  url: string;
  language: string;
  published_at: string;
  excerpt: string;
  relationship_type?: string;
  is_original?: boolean;
  syndication_origin?: string | null;
}

interface IndependenceBreakdownProps {
  totalArticlesCount: number;
  candidateSourcesCount: number;
  independentSourcesCount: number;
  independenceScore: number;
  sourceDiversityScore: number;
  temporalSpreadScore: number;
  entityAlignmentScore: number;
  articles: StoryArticleItem[];
}

export const IndependenceBreakdown: React.FC<IndependenceBreakdownProps> = ({
  totalArticlesCount,
  candidateSourcesCount,
  independentSourcesCount,
  independenceScore,
  sourceDiversityScore,
  temporalSpreadScore,
  entityAlignmentScore,
  articles,
}) => {
  const indepPct = Math.round(independenceScore * 100);
  const divPct = Math.round(sourceDiversityScore * 100);
  const tempPct = Math.round(temporalSpreadScore * 100);
  const entPct = Math.round(entityAlignmentScore * 100);

  const getRelationshipBadge = (type: string = "INDEPENDENT") => {
    switch (type) {
      case "ORIGINAL":
      case "INDEPENDENT":
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
            Original Source
          </span>
        );
      case "SYNDICATED":
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
            Wire Syndication
          </span>
        );
      case "COPIED":
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30">
            Derivative / Copy
          </span>
        );
      case "RELATED":
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-purple-500/20 text-purple-300 border border-purple-500/30">
            Publisher Network
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-700 text-slate-300">
            {type}
          </span>
        );
    }
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 shadow-xl backdrop-blur-sm">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Split className="w-5 h-5 text-indigo-400" />
            <h3 className="text-base font-bold text-white tracking-wide">
              Source Independence & Syndication Intelligence
            </h3>
          </div>
          <p className="text-xs text-slate-400">
            Article count is NOT independent source count. Derivative wire republishing is discounted.
          </p>
        </div>

        {/* Counts Comparison Badge */}
        <div className="flex items-center gap-3 bg-slate-950 p-3 rounded-lg border border-slate-800">
          <div className="text-center px-3 border-r border-slate-800">
            <div className="text-xs text-slate-400 font-medium">Ingested Articles</div>
            <div className="text-xl font-black text-white">{totalArticlesCount}</div>
          </div>
          <div className="text-center px-3">
            <div className="text-xs text-emerald-400 font-medium">Independent Sources</div>
            <div className="text-xl font-black text-emerald-300">{independentSourcesCount}</div>
          </div>
        </div>
      </div>

      {/* 3 Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-4">
        <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
          <div className="text-[11px] text-slate-400 mb-1">Source Diversity</div>
          <div className="text-lg font-bold text-white mb-1">{divPct}%</div>
          <div className="w-full h-1 bg-slate-800 rounded-full overflow-hidden">
            <div className="h-full bg-indigo-500 rounded-full" style={{ width: `${divPct}%` }} />
          </div>
        </div>

        <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
          <div className="text-[11px] text-slate-400 mb-1">Temporal Spread</div>
          <div className="text-lg font-bold text-white mb-1">{tempPct}%</div>
          <div className="w-full h-1 bg-slate-800 rounded-full overflow-hidden">
            <div className="h-full bg-cyan-500 rounded-full" style={{ width: `${tempPct}%` }} />
          </div>
        </div>

        <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
          <div className="text-[11px] text-slate-400 mb-1">Entity Alignment</div>
          <div className="text-lg font-bold text-white mb-1">{entPct}%</div>
          <div className="w-full h-1 bg-slate-800 rounded-full overflow-hidden">
            <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${entPct}%` }} />
          </div>
        </div>
      </div>

      {/* Articles & Syndication Classification List */}
      <div className="mt-5 space-y-2.5">
        <div className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
          Origin & Syndication Chains
        </div>
        {articles.map((art) => (
          <div
            key={art.id}
            className="flex flex-col sm:flex-row sm:items-center justify-between p-3 rounded-lg bg-slate-950/50 border border-slate-800/80 hover:border-slate-700 transition-colors gap-2"
          >
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-white truncate max-w-md">
                  {art.title}
                </span>
                <span className="text-[10px] font-mono uppercase px-1.5 py-0.2 bg-slate-800 text-slate-300 rounded">
                  {art.language}
                </span>
              </div>
              <div className="flex items-center gap-2 mt-1 text-[11px] text-slate-400">
                <span>{art.source_name}</span>
                <span>•</span>
                <span>{art.domain}</span>
                {art.syndication_origin && (
                  <>
                    <span>•</span>
                    <span className="text-cyan-400 flex items-center gap-1">
                      <Copy className="w-3 h-3" /> Origin: {art.syndication_origin}
                    </span>
                  </>
                )}
              </div>
            </div>

            <div className="shrink-0">{getRelationshipBadge(art.relationship_type)}</div>
          </div>
        ))}
      </div>
    </div>
  );
};
