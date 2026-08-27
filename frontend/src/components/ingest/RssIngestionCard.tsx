"use client";

import React, { useState } from "react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export function RssIngestionCard({ onTriggerComplete }: { onTriggerComplete?: () => void }) {
  const [loading, setLoading] = useState(false);
  const [lastResult, setLastResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const feeds = [
    { name: "The Hindu - National", lang: "EN", domain: "thehindu.com", region: "India" },
    { name: "Dinamalar - Tamil Regional", lang: "TA", domain: "dinamalar.com", region: "Tamil Nadu" },
    { name: "Dainik Bhaskar - Hindi National", lang: "HI", domain: "bhaskar.com", region: "National" },
  ];

  const handleTrigger = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/ingest/rss`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });

      if (!res.ok) {
        throw new Error(`RSS Ingestion returned status ${res.status}`);
      }

      const data = await res.json();
      setLastResult(data);
      if (onTriggerComplete) onTriggerComplete();
    } catch (err: any) {
      setError(err.message || "Failed to trigger RSS ingestion");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-xl font-bold tracking-wide text-zinc-100 flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-500 animate-pulse" />
            Automated RSS Ingestion
          </h2>
          <p className="text-xs text-zinc-400 mt-1">
            Agent 1 (Discovery) multilingual wire feed polling & URL deduplication.
          </p>
        </div>
        <Badge variant="info">Active Feeds: {feeds.length}</Badge>
      </div>

      {/* Configured Feeds List */}
      <div className="space-y-2 mb-5">
        {feeds.map((f, i) => (
          <div
            key={i}
            className="flex items-center justify-between p-2.5 rounded-lg bg-zinc-900/60 border border-zinc-800 text-xs"
          >
            <div className="flex items-center gap-2.5">
              <Badge variant="outline" className="font-mono text-[10px]">
                {f.lang}
              </Badge>
              <span className="font-medium text-zinc-200">{f.name}</span>
            </div>
            <span className="text-zinc-500 font-mono text-[11px]">{f.domain}</span>
          </div>
        ))}
      </div>

      {/* Trigger Button */}
      <div className="flex items-center justify-between pt-2">
        <Button
          variant="secondary"
          onClick={handleTrigger}
          disabled={loading}
          className="w-full"
        >
          {loading ? (
            <span className="flex items-center gap-2 justify-center">
              <LoadingSpinner size="sm" /> Polling & Deduplicating Feeds...
            </span>
          ) : (
            "Trigger Automated RSS Ingestion"
          )}
        </Button>
      </div>

      {/* Ingestion Results */}
      {lastResult && (
        <div className="mt-4 p-3 rounded-lg bg-emerald-950/20 border border-emerald-800/40 text-xs text-emerald-300">
          <div className="font-bold mb-1">RSS Ingestion Completed:</div>
          <div className="flex gap-4 text-zinc-300 font-mono text-[11px]">
            <span>Feeds Processed: {lastResult.feeds_processed}</span>
            <span>New Articles: {lastResult.new_articles_total}</span>
            <span>Duplicates Filtered: {lastResult.duplicates_skipped_total}</span>
          </div>
        </div>
      )}

      {error && (
        <div className="mt-4 p-3 rounded-lg bg-rose-950/40 border border-rose-800/60 text-xs text-rose-300">
          {error}
        </div>
      )}
    </Card>
  );
}
