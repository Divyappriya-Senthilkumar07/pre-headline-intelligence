"use client";

import React, { useState } from "react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export function GdeltIngestionCard({ onTriggerComplete }: { onTriggerComplete?: () => void }) {
  const [topic, setTopic] = useState("");
  const [loading, setLoading] = useState(false);
  const [lastResult, setLastResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleTrigger = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/ingest/gdelt`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query_topic: topic.trim() || undefined }),
      });

      if (!res.ok) {
        throw new Error(`GDELT Ingestion returned status ${res.status}`);
      }

      const data = await res.json();
      setLastResult(data);
      if (onTriggerComplete) onTriggerComplete();
    } catch (err: any) {
      setError(err.message || "Failed to trigger GDELT ingestion");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-xl font-bold tracking-wide text-zinc-100 flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-purple-500 animate-pulse" />
            GDELT GKG Stream Ingestion
          </h2>
          <p className="text-xs text-zinc-400 mt-1">
            Global Knowledge Graph event themes & normalized entity extraction.
          </p>
        </div>
        <Badge variant="outline">GKG Stream Live</Badge>
      </div>

      <div className="mb-4">
        <label className="block text-xs font-medium text-zinc-400 mb-1">
          Theme / Topic Filter (Optional)
        </label>
        <input
          type="text"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="e.g. environment OR inspection OR compliance"
          className="w-full bg-zinc-900 border border-zinc-700/80 rounded-lg px-3 py-2 text-xs text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-zinc-500"
        />
      </div>

      <Button
        variant="secondary"
        onClick={handleTrigger}
        disabled={loading}
        className="w-full"
      >
        {loading ? (
          <span className="flex items-center gap-2 justify-center">
            <LoadingSpinner size="sm" /> Fetching & Normalizing GKG Records...
          </span>
        ) : (
          "Trigger GDELT GKG Stream Ingestion"
        )}
      </Button>

      {/* Ingestion Results */}
      {lastResult && (
        <div className="mt-4 p-3 rounded-lg bg-purple-950/20 border border-purple-800/40 text-xs text-purple-300">
          <div className="font-bold mb-1">GDELT GKG Ingestion Completed:</div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-zinc-300 font-mono text-[11px] mt-1">
            <span>Records: {lastResult.total_records}</span>
            <span>Articles: {lastResult.new_articles}</span>
            <span>Entities: {lastResult.new_entities}</span>
            <span>Duplicates: {lastResult.duplicates_skipped}</span>
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
