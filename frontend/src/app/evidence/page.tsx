"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  FileCheck2,
  ShieldCheck,
  Globe2,
  ExternalLink,
  ChevronRight,
  Search,
  Layers,
  CheckCircle2,
} from "lucide-react";

interface StoryEvidenceSummary {
  id: string;
  title: string;
  formation_score: number;
  independent_sources_count: number;
  languages: string[];
  evidence_strength_score: number;
  status: string;
  created_at: string;
}

export default function EvidenceLibraryPage() {
  const [stories, setStories] = useState<StoryEvidenceSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    const fetchStories = async () => {
      try {
        const res = await fetch("http://localhost:8000/api/v1/stories");
        if (res.ok) {
          const data = await res.json();
          setStories(data);
        }
      } catch (err) {
        console.warn("Evidence fetch error:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchStories();
  }, []);

  const filtered = stories.filter(
    (s) =>
      s.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.languages.some((l) => l.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-md bg-indigo-500/10 text-indigo-400 text-xs font-mono mb-2 border border-indigo-500/20">
            <FileCheck2 className="w-3.5 h-3.5" />
            AGENT 8 AUDITABLE PROVENANCE REPOSITORY
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
            Evidence Chains & Provenance Library
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1 max-w-2xl">
            Audit-ready evidence graphs with short quotes, source attribution, and cross-lingual corroboration links.
          </p>
        </div>

        {/* Search */}
        <div className="relative w-full sm:w-64">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Filter evidence chains..."
            className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />
        </div>
      </div>

      {loading ? (
        <div className="p-12 text-center text-slate-400 bg-slate-900/40 rounded-2xl border border-slate-800">
          <div className="w-8 h-8 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin mx-auto mb-3" />
          <p className="text-xs font-mono">Loading Provenance Chains...</p>
        </div>
      ) : filtered.length === 0 ? (
        <div className="p-12 text-center text-slate-400 bg-slate-900/40 rounded-2xl border border-slate-800">
          <FileCheck2 className="w-8 h-8 text-slate-600 mx-auto mb-3" />
          <p className="text-sm font-medium text-slate-300">No evidence chains match your filter.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {filtered.map((s) => (
            <div
              key={s.id}
              className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 hover:border-slate-700 transition-all shadow-xl space-y-4"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/40">
                      ID: {s.id.slice(0, 8)}
                    </span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 uppercase">
                      {s.languages.join(", ")}
                    </span>
                  </div>
                  <h3 className="text-base font-bold text-white tracking-tight">{s.title}</h3>
                </div>

                <div className="text-right shrink-0">
                  <span className="text-xs font-mono text-slate-400 block">Formation</span>
                  <span className="text-lg font-bold font-mono text-indigo-400">
                    {Math.round(s.formation_score)}/100
                  </span>
                </div>
              </div>

              <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
                <span className="text-slate-400 flex items-center gap-1 font-mono">
                  <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
                  {s.independent_sources_count} Independent Sources
                </span>

                <Link
                  href={`/stories/${s.id}`}
                  className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition-colors"
                >
                  Inspect Full Provenance Graph <ChevronRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
