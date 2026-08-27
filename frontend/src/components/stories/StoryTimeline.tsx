"use client";

import React, { useState, useEffect } from "react";
import { Clock, Radio, FileText, Image as ImageIcon, FileAudio, ExternalLink, ChevronDown, ChevronUp } from "lucide-react";

export interface TimelineEvent {
  id: string;
  timestamp: string;
  event_type: string;
  title: string;
  source_name: string;
  language: string;
  claim_statement?: string | null;
  evidence_excerpt?: string | null;
  media_metadata?: {
    media_id: string;
    media_type: string;
    filename: string;
    extraction_method: string;
    extracted_content: string;
  } | null;
}

interface StoryTimelineProps {
  storyId: string;
}

export const StoryTimeline: React.FC<StoryTimelineProps> = ({ storyId }) => {
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    const fetchTimeline = async () => {
      try {
        const res = await fetch(`http://localhost:8000/api/v1/stories/${storyId}/timeline`);
        if (res.ok) {
          const data = await res.json();
          setEvents(data);
        }
      } catch (err) {
        console.warn("Timeline fetch error:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchTimeline();
  }, [storyId]);

  if (loading) {
    return (
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 text-center text-slate-400">
        <div className="w-6 h-6 border-2 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin mx-auto mb-2" />
        <p className="text-xs font-mono">Loading Story Timeline...</p>
      </div>
    );
  }

  if (events.length === 0) {
    return (
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 text-center text-slate-400">
        <Clock className="w-5 h-5 mx-auto mb-2 text-slate-500" />
        <p className="text-xs">No chronological events recorded yet for this candidate story.</p>
      </div>
    );
  }

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6 shadow-xl relative">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-6">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-lg bg-cyan-500/10 text-cyan-400">
            <Clock className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
              Story Chronology & Event Timeline
              <span className="text-xs px-2 py-0.5 rounded-full font-mono bg-slate-800 text-slate-400 border border-slate-700">
                {events.length} EVENTS
              </span>
            </h3>
            <p className="text-xs text-slate-400">Natural temporal sequence of reporting signals and primary disclosures</p>
          </div>
        </div>
      </div>

      <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-3 before:bottom-3 before:w-0.5 before:bg-slate-800">
        {events.map((evt, idx) => {
          const isExpanded = expandedId === evt.id;
          const dateObj = new Date(evt.timestamp);
          const timeStr = isNaN(dateObj.getTime())
            ? evt.timestamp
            : dateObj.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) +
              " (" +
              dateObj.toLocaleDateString() +
              ")";

          return (
            <div key={evt.id || idx} className="relative group">
              {/* Timeline marker node */}
              <div className="absolute -left-[27px] top-1.5 w-3.5 h-3.5 rounded-full bg-slate-950 border-2 border-cyan-500 ring-4 ring-slate-900" />

              <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-800 hover:border-slate-700 transition-all">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2 flex-wrap mb-1">
                      <span className="text-[11px] font-mono font-bold text-cyan-400">{timeStr}</span>
                      <span className="text-[10px] font-mono px-2 py-0.2 rounded bg-slate-900 text-slate-300 border border-slate-700">
                        {evt.source_name}
                      </span>
                      <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-purple-500/10 text-purple-400 border border-purple-500/30 uppercase">
                        {evt.language}
                      </span>
                      <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 border border-slate-700">
                        {evt.event_type}
                      </span>
                    </div>

                    <h4 className="text-sm font-semibold text-slate-100">{evt.title}</h4>

                    {evt.claim_statement && (
                      <p className="text-xs text-slate-300 mt-1.5 bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80">
                        <strong className="text-slate-400 font-medium font-mono text-[10px] uppercase block mb-0.5">
                          Extracted Claim:
                        </strong>
                        {evt.claim_statement}
                      </p>
                    )}
                  </div>

                  <button
                    onClick={() => setExpandedId(isExpanded ? null : evt.id)}
                    className="p-1 text-slate-400 hover:text-slate-200 transition-colors"
                  >
                    {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </button>
                </div>

                {/* Media Metadata & Extraction preview if present */}
                {isExpanded && (
                  <div className="mt-3 pt-3 border-t border-slate-800/80 space-y-2 text-xs">
                    {evt.evidence_excerpt && (
                      <div>
                        <span className="text-[10px] font-mono uppercase text-slate-500">Full Short Excerpt:</span>
                        <p className="text-slate-300 italic bg-slate-900 p-2 rounded border border-slate-800 mt-0.5">
                          {evt.evidence_excerpt}
                        </p>
                      </div>
                    )}

                    {evt.media_metadata && (
                      <div className="p-2.5 rounded bg-slate-950 border border-slate-800 space-y-1">
                        <span className="text-[10px] font-mono text-cyan-400 uppercase flex items-center gap-1">
                          <FileText className="w-3 h-3" /> Media Provenance Record:
                        </span>
                        <p className="text-[11px] text-slate-300">
                          Filename: <strong>{evt.media_metadata.filename}</strong> ({evt.media_metadata.media_type})
                        </p>
                        <p className="text-[10px] text-slate-400">
                          Extraction method: {evt.media_metadata.extraction_method}
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
