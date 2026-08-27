"use client";

import React, { useState, useEffect } from "react";
import { StoryClusterCard } from "@/components/stories/StoryClusterCard";
import { GraphViewer, GraphNode, GraphEdgeItem } from "@/components/stories/GraphViewer";
import {
  Layers,
  Sparkles,
  RefreshCw,
  Play,
  CheckCircle2,
  AlertCircle,
  Network,
  Globe2,
  Database,
} from "lucide-react";

interface StoryItem {
  id: string;
  title: string;
  summary?: string;
  status: string;
  article_count: number;
  languages: string[];
  primary_entities: string[];
  created_at: string;
}

export default function StoriesPage() {
  const [stories, setStories] = useState<StoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [runningPipeline, setRunningPipeline] = useState(false);
  const [pipelineResult, setPipelineResult] = useState<any | null>(null);
  const [graphNodes, setGraphNodes] = useState<GraphNode[]>([]);
  const [graphEdges, setGraphEdges] = useState<GraphEdgeItem[]>([]);

  const fetchStoriesAndGraph = async () => {
    setLoading(true);
    try {
      // 1. Fetch Candidate Stories
      const storiesRes = await fetch("http://localhost:8000/api/v1/stories");
      if (storiesRes.ok) {
        const data = await storiesRes.json();
        setStories(data);
      }

      // 2. Fetch Graph Entities
      const entitiesRes = await fetch("http://localhost:8000/api/v1/entities");
      if (entitiesRes.ok) {
        const ents = await entitiesRes.json();
        const nodes: GraphNode[] = ents.map((e: any) => ({
          id: e.id,
          label: e.canonical_name || e.name,
          type: "ENTITY" as const,
          details: `Type: ${e.entity_type}`,
        }));

        // Fetch events for graph
        const eventsRes = await fetch("http://localhost:8000/api/v1/events");
        if (eventsRes.ok) {
          const events = await eventsRes.json();
          events.forEach((ev: any) => {
            nodes.push({
              id: ev.id,
              label: ev.title,
              type: "EVENT" as const,
              details: `Type: ${ev.event_type}`,
            });
          });
        }

        setGraphNodes(nodes);
      }
    } catch (err) {
      console.error("Error fetching stories and graph:", err);
      // Populate rich demo data if backend is offline
      setStories([
        {
          id: "story-seed-001",
          title: "Tamil Nadu State Pollution Control Board Inspection at Company X Plant",
          summary: "Candidate story cluster formed by 3 signals across English, Tamil, and Hindi regional reporting.",
          status: "EMERGING",
          article_count: 3,
          languages: ["en", "ta", "hi"],
          primary_entities: ["Company X", "TNSPCB"],
          created_at: new Date().toISOString(),
        },
      ]);
      setGraphNodes([
        { id: "ent-1", label: "Company X", type: "ENTITY", details: "Pvt Ltd Industrial Unit" },
        { id: "ent-2", label: "Tamil Nadu Pollution Control Board", type: "ENTITY", details: "State Environmental Regulator" },
        { id: "ev-1", label: "Scheduled Industrial Compliance Audit", type: "EVENT", details: "Event: inspection" },
      ]);
      setGraphEdges([
        { source: "ent-1", target: "ent-2", relation: "regulated_by", weight: 0.95 },
        { source: "ent-1", target: "ev-1", relation: "involved_in", weight: 0.90 },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStoriesAndGraph();
  }, []);

  const handleRunPhase2Pipeline = async () => {
    setRunningPipeline(true);
    setPipelineResult(null);
    try {
      const res = await fetch("http://localhost:8000/api/v1/pipeline/run-phase2", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          watchlist_keywords: ["Company X", "Pollution Control Board", "State Regulator"],
          target_languages: ["en", "ta", "hi"],
          min_cluster_size: 2,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setPipelineResult(data);
        await fetchStoriesAndGraph();
      }
    } catch (err) {
      console.error("Error triggering Phase 2 pipeline:", err);
    } finally {
      setRunningPipeline(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Top Banner & Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <div className="p-1.5 rounded-md bg-cyan-950 border border-cyan-500/30 text-cyan-400">
              <Layers className="w-4 h-4" />
            </div>
            <span className="text-xs font-mono tracking-wider text-cyan-400 uppercase font-semibold">
              Phase 2 Intelligence Pipeline
            </span>
          </div>
          <h1 className="text-2xl font-bold text-slate-100 tracking-tight">
            Candidate Story Clusters & Media Event Graph
          </h1>
          <p className="text-sm text-slate-400 mt-1 max-w-2xl">
            Agent 2 Context extraction, PostgreSQL multi-hop graph expansion, 384D multilingual embeddings, and HDBSCAN semantic story formation.
          </p>
        </div>

        {/* Pipeline Trigger & Refresh Actions */}
        <div className="flex items-center gap-3">
          <button
            onClick={fetchStoriesAndGraph}
            disabled={loading}
            className="px-3.5 py-2 rounded-lg border border-slate-700 bg-slate-900 hover:bg-slate-800 text-slate-300 text-xs font-medium flex items-center gap-2 transition-all"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-cyan-400" : ""}`} />
            Refresh
          </button>

          <button
            onClick={handleRunPhase2Pipeline}
            disabled={runningPipeline}
            className="px-4 py-2 rounded-lg bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white text-xs font-semibold shadow-lg shadow-cyan-900/30 flex items-center gap-2 transition-all disabled:opacity-50"
          >
            {runningPipeline ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin text-white" />
                Executing Pipeline...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-current text-white" />
                Run Phase 2 Pipeline
              </>
            )}
          </button>
        </div>
      </div>

      {/* Pipeline Execution Result Alert */}
      {pipelineResult && (
        <div className="rounded-xl border border-cyan-500/40 bg-cyan-950/20 p-4 flex items-start justify-between gap-3 text-xs">
          <div className="flex items-start gap-3">
            <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5" />
            <div>
              <div className="font-semibold text-slate-200 mb-1">
                Phase 2 Intelligence Pipeline Execution Completed
              </div>
              <div className="text-slate-400 space-y-0.5 font-mono text-[11px]">
                <div>• Total Articles Processed: {pipelineResult.total_articles_processed}</div>
                <div>• Entities Discovered / Upserted: {pipelineResult.entities_extracted_count}</div>
                <div>• Events Extracted: {pipelineResult.events_extracted_count}</div>
                <div>• Graph Expansion Candidates: {pipelineResult.expanded_articles_count}</div>
                <div>• Candidate Story Clusters Formed: {pipelineResult.candidate_stories_formed}</div>
              </div>
            </div>
          </div>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950/80 border border-emerald-500/40 text-emerald-300">
            SUCCESS
          </span>
        </div>
      )}

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
          <div className="text-xs text-slate-400 mb-1 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            Candidate Story Clusters
          </div>
          <div className="text-2xl font-bold text-slate-100">{stories.length}</div>
          <div className="text-[11px] text-emerald-400 mt-1">HDBSCAN Semantic Formations</div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
          <div className="text-xs text-slate-400 mb-1 flex items-center gap-1.5">
            <Globe2 className="w-3.5 h-3.5 text-amber-400" />
            Multilingual Support
          </div>
          <div className="text-lg font-bold text-slate-100">EN · தமிழ் · हिन्दी</div>
          <div className="text-[11px] text-slate-400 mt-1">Dense 384D Cross-Lingual Vectors</div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
          <div className="text-xs text-slate-400 mb-1 flex items-center gap-1.5">
            <Network className="w-3.5 h-3.5 text-indigo-400" />
            Media Event Graph
          </div>
          <div className="text-2xl font-bold text-slate-100">{graphNodes.length} Nodes</div>
          <div className="text-[11px] text-indigo-300 mt-1">PostgreSQL Adjacency List</div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
          <div className="text-xs text-slate-400 mb-1 flex items-center gap-1.5">
            <Database className="w-3.5 h-3.5 text-emerald-400" />
            Noise / Outlier Tolerance
          </div>
          <div className="text-2xl font-bold text-emerald-400">HDBSCAN -1</div>
          <div className="text-[11px] text-slate-400 mt-1">Unclustered Noise Rejection</div>
        </div>
      </div>

      {/* Candidate Stories Feed */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-slate-200 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-cyan-400" />
            Emerging Candidate Story Clusters
          </h2>
          <span className="text-xs text-slate-400">
            Showing {stories.length} candidate clusters
          </span>
        </div>

        {loading ? (
          <div className="text-center py-12 text-slate-500 space-y-3">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto text-cyan-500" />
            <p className="text-xs">Loading Candidate Story Clusters...</p>
          </div>
        ) : stories.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-800 p-12 text-center text-slate-400 space-y-3">
            <Layers className="w-8 h-8 mx-auto text-slate-600" />
            <p className="text-sm font-medium text-slate-300">No Candidate Stories Formed Yet</p>
            <p className="text-xs max-w-md mx-auto text-slate-500">
              Click &quot;Run Phase 2 Pipeline&quot; above to cluster ingested RSS feeds, GDELT streams, and uploaded media files into semantic story candidates.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {stories.map((story) => (
              <StoryClusterCard
                key={story.id}
                id={story.id}
                title={story.title}
                summary={story.summary}
                status={story.status}
                articleCount={story.article_count}
                languages={story.languages}
                primaryEntities={story.primary_entities}
                createdAt={story.created_at}
              />
            ))}
          </div>
        )}
      </div>

      {/* Interactive Media Event Graph Viewer */}
      <div className="pt-6 border-t border-slate-800">
        <GraphViewer
          nodes={graphNodes}
          edges={graphEdges}
          title="Media Event Graph — Multilingual Entity & Event Relationships"
        />
      </div>
    </div>
  );
}
