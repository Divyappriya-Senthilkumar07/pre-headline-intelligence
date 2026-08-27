"use client";

import React, { useEffect, useState } from "react";
import { MediaUploader } from "@/components/ingest/MediaUploader";
import { RssIngestionCard } from "@/components/ingest/RssIngestionCard";
import { GdeltIngestionCard } from "@/components/ingest/GdeltIngestionCard";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

interface IngestionDashboardData {
  total_media_count: number;
  recent_media: any[];
  total_articles_count: number;
  total_sources_count: number;
  rss_status: string;
  gdelt_status: string;
  last_successful_ingestion: string | null;
  recent_articles: Array<{
    id: string;
    title: string;
    source_name: string;
    language: string;
    published_at: string;
    excerpt: string;
    url: string;
  }>;
}

export default function IngestPage() {
  const [data, setData] = useState<IngestionDashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/ingest/status`);
      if (res.ok) {
        const json = await res.json();
        setData(json);
      }
    } catch (e) {
      console.error("Failed to load ingestion status:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const timer = setInterval(fetchStatus, 8000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-black tracking-tight text-zinc-100 flex items-center gap-3">
              <span className="p-2 rounded-xl bg-zinc-900 border border-zinc-800 text-emerald-400 font-mono text-xl">
                ⚡
              </span>
              Ingestion & Media Pipeline
            </h1>
            <p className="text-sm text-zinc-400 mt-1 max-w-3xl">
              Phase 1 foundation: Ingest signals via Analyst Uploads (Images, PDFs, Text, Audio, Video),
              multilingual RSS feeds, and GDELT Global Knowledge Graph into normalized Article and Source records.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Badge variant="success" className="animate-pulse">
              Deduplication Active
            </Badge>
            <Badge variant="outline">Phase 1 Foundation</Badge>
          </div>
        </div>

        {/* Top Aggregate Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
          <Card className="p-4 bg-zinc-900/60 border-zinc-800">
            <div className="text-xs font-mono text-zinc-500 uppercase">Uploaded Media</div>
            <div className="text-2xl font-bold text-zinc-100 mt-1">
              {data?.total_media_count ?? 0}
            </div>
            <div className="text-[11px] text-zinc-400 mt-0.5">Images, PDFs, Plain Text</div>
          </Card>

          <Card className="p-4 bg-zinc-900/60 border-zinc-800">
            <div className="text-xs font-mono text-zinc-500 uppercase">Normalized Articles</div>
            <div className="text-2xl font-bold text-emerald-400 mt-1">
              {data?.total_articles_count ?? 0}
            </div>
            <div className="text-[11px] text-zinc-400 mt-0.5">Excerpts + attribution only</div>
          </Card>

          <Card className="p-4 bg-zinc-900/60 border-zinc-800">
            <div className="text-xs font-mono text-zinc-500 uppercase">Tracked Sources</div>
            <div className="text-2xl font-bold text-cyan-400 mt-1">
              {data?.total_sources_count ?? 0}
            </div>
            <div className="text-[11px] text-zinc-400 mt-0.5">RSS, GDELT & Analyst</div>
          </Card>

          <Card className="p-4 bg-zinc-900/60 border-zinc-800">
            <div className="text-xs font-mono text-zinc-500 uppercase">Supported Languages</div>
            <div className="text-2xl font-bold text-purple-400 mt-1">3</div>
            <div className="text-[11px] text-zinc-400 mt-0.5">English (EN), தமிழ் (TA), हिन्दी (HI)</div>
          </Card>
        </div>
      </div>

      {/* Main Two-Column Ingestion Control Center */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Media Upload & Extraction */}
        <div className="lg:col-span-6 space-y-6">
          <MediaUploader onUploadComplete={fetchStatus} />

          {/* Recently Uploaded Media List */}
          {data?.recent_media && data.recent_media.length > 0 && (
            <Card className="p-6">
              <h3 className="text-base font-bold text-zinc-200 mb-3">Recently Uploaded Media</h3>
              <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                {data.recent_media.map((m) => (
                  <div
                    key={m.id}
                    className="flex items-center justify-between p-2.5 rounded-lg bg-zinc-900/60 border border-zinc-800 text-xs"
                  >
                    <div className="truncate pr-2">
                      <div className="font-medium text-zinc-200 truncate">{m.original_filename}</div>
                      <div className="text-[11px] text-zinc-500 font-mono">
                        {m.media_type} • {(m.file_size_bytes / 1024).toFixed(1)} KB
                      </div>
                    </div>
                    <Badge
                      variant={
                        m.processing_status === "COMPLETED"
                          ? "success"
                          : m.processing_status === "FAILED"
                          ? "danger"
                          : "warning"
                      }
                      className="font-mono text-[10px]"
                    >
                      {m.processing_status}
                    </Badge>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>

        {/* Right Column: RSS + GDELT Ingestion & Stream */}
        <div className="lg:col-span-6 space-y-6">
          <RssIngestionCard onTriggerComplete={fetchStatus} />
          <GdeltIngestionCard onTriggerComplete={fetchStatus} />

          {/* Ingested Normalized Signal Stream */}
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold text-zinc-200">Normalized Signal Ingestion Stream</h3>
              <Badge variant="outline" className="font-mono text-[11px]">
                {data?.recent_articles?.length ?? 0} Latest Signals
              </Badge>
            </div>

            {loading ? (
              <div className="py-8 flex justify-center">
                <LoadingSpinner size="md" />
              </div>
            ) : !data?.recent_articles || data.recent_articles.length === 0 ? (
              <div className="py-8 text-center text-xs text-zinc-500 italic">
                No signals ingested yet. Upload media or trigger RSS/GDELT ingestion above.
              </div>
            ) : (
              <div className="space-y-3 max-h-96 overflow-y-auto pr-1">
                {data.recent_articles.map((art) => (
                  <div
                    key={art.id}
                    className="p-3 rounded-lg bg-zinc-950/80 border border-zinc-800/80 space-y-1.5"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <h4 className="text-xs font-semibold text-zinc-200 leading-snug line-clamp-1">
                        {art.title}
                      </h4>
                      <Badge variant="outline" className="font-mono text-[10px] uppercase shrink-0">
                        {art.language}
                      </Badge>
                    </div>

                    <p className="text-[11px] text-zinc-400 line-clamp-2 leading-relaxed">
                      {art.excerpt}
                    </p>

                    <div className="flex items-center justify-between text-[10px] text-zinc-500 font-mono pt-1">
                      <span>{art.source_name}</span>
                      <span>{new Date(art.published_at).toLocaleTimeString()}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
