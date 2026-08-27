"use client";

import React from "react";
import Link from "next/link";
import { Network, FileText, Globe2, ChevronRight, Sparkles, Building2 } from "lucide-react";

export interface StoryClusterCardProps {
  id: string;
  title: string;
  summary?: string;
  status: string;
  articleCount: number;
  languages: string[];
  primaryEntities: string[];
  createdAt: string;
}

export const StoryClusterCard: React.FC<StoryClusterCardProps> = ({
  id,
  title,
  summary,
  status,
  articleCount,
  languages,
  primaryEntities,
  createdAt,
}) => {
  const getLangBadge = (lang: string) => {
    switch (lang.toLowerCase()) {
      case "ta":
        return { label: "Tamil (தமிழ்)", bg: "bg-amber-950/70 border-amber-600/40 text-amber-300" };
      case "hi":
        return { label: "Hindi (हिन्दी)", bg: "bg-orange-950/70 border-orange-600/40 text-orange-300" };
      case "en":
      default:
        return { label: "English", bg: "bg-cyan-950/70 border-cyan-600/40 text-cyan-300" };
    }
  };

  return (
    <div className="group relative rounded-xl border border-slate-800/80 bg-slate-900/50 p-5 hover:border-cyan-500/40 hover:bg-slate-900/80 transition-all duration-200 shadow-lg">
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-950/80 border border-emerald-500/40 text-emerald-300">
            <Sparkles className="w-3 h-3 animate-pulse text-emerald-400" />
            {status}
          </span>
          <span className="text-xs text-slate-400">
            {new Date(createdAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
          </span>
        </div>

        {/* Multilingual Signals Represented */}
        <div className="flex flex-wrap items-center gap-1.5">
          {languages.map((lang) => {
            const badge = getLangBadge(lang);
            return (
              <span
                key={lang}
                className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono border ${badge.bg}`}
              >
                <Globe2 className="w-3 h-3 opacity-70" />
                {badge.label}
              </span>
            );
          })}
        </div>
      </div>

      {/* Story Working Headline */}
      <h3 className="text-lg font-semibold text-slate-100 group-hover:text-cyan-300 transition-colors mb-2 line-clamp-2">
        {title}
      </h3>

      {/* Story Summary Excerpt */}
      {summary && (
        <p className="text-xs text-slate-400 mb-4 line-clamp-2 leading-relaxed">
          {summary}
        </p>
      )}

      {/* Primary Tracked Entities */}
      {primaryEntities && primaryEntities.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 mb-4 pt-2 border-t border-slate-800/60">
          <span className="text-[11px] text-slate-500 flex items-center gap-1">
            <Building2 className="w-3 h-3" /> Entities:
          </span>
          {primaryEntities.map((ent, idx) => (
            <span
              key={idx}
              className="text-xs px-2 py-0.5 rounded bg-slate-800/80 border border-slate-700 text-slate-300 font-medium"
            >
              {ent}
            </span>
          ))}
        </div>
      )}

      {/* Footer Link & Counts */}
      <div className="flex items-center justify-between pt-3 border-t border-slate-800/60">
        <div className="flex items-center gap-3 text-xs text-slate-400">
          <span className="flex items-center gap-1 text-slate-300">
            <FileText className="w-3.5 h-3.5 text-cyan-400" />
            <strong className="text-slate-100">{articleCount}</strong> signals clustered
          </span>
          <span className="flex items-center gap-1 text-slate-400">
            <Network className="w-3.5 h-3.5 text-indigo-400" />
            HDBSCAN Graph
          </span>
        </div>

        <Link
          href={`/stories/${id}`}
          className="inline-flex items-center gap-1 text-xs font-semibold text-cyan-400 group-hover:text-cyan-300 group-hover:translate-x-0.5 transition-all"
        >
          Inspect Cluster
          <ChevronRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
};
