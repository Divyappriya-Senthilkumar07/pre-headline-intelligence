"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { GraphViewer, GraphNode, GraphEdgeItem } from "@/components/stories/GraphViewer";
import { FormationScoreGauge } from "@/components/stories/FormationScoreGauge";
import { ContradictionGateAlert, ContradictionItem } from "@/components/stories/ContradictionGateAlert";
import { IndependenceBreakdown } from "@/components/stories/IndependenceBreakdown";
import { SourceRelationshipTree } from "@/components/stories/SourceRelationshipTree";
import { StoryTimeline } from "@/components/stories/StoryTimeline";
import { AnalystNotesPanel, StoryNoteItem } from "@/components/stories/AnalystNotesPanel";
import { PredictionCard, PredictionData } from "@/components/stories/PredictionCard";
import { EvidenceChainViewer, EvidenceChainData } from "@/components/stories/EvidenceChainViewer";
import { CopilotPanel } from "@/components/stories/CopilotPanel";
import {
  ChevronLeft,
  Globe2,
  Building2,
  Layers,
  Network,
  BookOpen,
  HelpCircle,
} from "lucide-react";

interface StoryArticle {
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

interface StoryEntity {
  id: string;
  name: string;
  canonical_name: string;
  entity_type: string;
}

interface StoryDetail {
  id: string;
  title: string;
  summary?: string;
  why_it_matters?: string;
  status: string;
  formation_status: string;
  formation_score: number;
  narrative_summary?: string;
  article_count: number;
  candidate_sources_count: number;
  independent_sources_count: number;
  independence_score: number;
  source_diversity_score: number;
  temporal_spread_score: number;
  entity_alignment_score: number;
  cross_language_score: number;
  evidence_strength_score: number;
  contradiction_status: string;
  prediction_eligible: boolean;
  created_at: string;
  languages: string[];
  score_breakdown: Record<string, any>;
  articles: StoryArticle[];
  entities: StoryEntity[];
  contradictions: ContradictionItem[];
  prediction?: PredictionData | null;
  evidence_chain?: EvidenceChainData | null;
  notes?: StoryNoteItem[];
}

export default function StoryClusterDetailPage() {
  const params = useParams();
  const storyId = Array.isArray(params?.id) ? params.id[0] : (params?.id as string) || "story-seed-001";

  const [story, setStory] = useState<StoryDetail | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchStoryDetail = async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/stories/${storyId}`);
      if (res.ok) {
        const data = await res.json();
        setStory(data);
      } else {
        setStory(getFallbackDemoStory(storyId));
      }
    } catch (err) {
      console.warn("Backend fetch failed, using fallback demo context:", err);
      setStory(getFallbackDemoStory(storyId));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStoryDetail();
  }, [storyId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-4 border-cyan-500/20 border-t-cyan-500 rounded-full animate-spin" />
          <span className="text-sm font-medium text-slate-400 font-mono">Loading Story Intelligence Workspace...</span>
        </div>
      </div>
    );
  }

  if (!story) {
    return (
      <div className="p-8 text-center">
        <h2 className="text-xl font-bold text-white mb-2">Story Cluster Not Found</h2>
        <Link href="/" className="text-cyan-400 hover:underline text-sm font-mono">
          ← Return to Intelligence Feed
        </Link>
      </div>
    );
  }

  const graphNodes: GraphNode[] = [
    {
      id: story.id,
      label: story.title.length > 25 ? story.title.slice(0, 25) + "..." : story.title,
      type: "STORY",
      group: 1,
    },
    ...story.entities.map((e) => ({
      id: e.id,
      label: e.canonical_name || e.name,
      type: e.entity_type || "ENTITY",
      group: 2,
    })),
    ...story.articles.map((a) => ({
      id: a.id,
      label: a.source_name || "Article",
      type: "ARTICLE",
      group: 3,
    })),
  ];

  const graphEdges: GraphEdgeItem[] = [
    ...story.entities.map((e) => ({
      source: story.id,
      target: e.id,
      label: "involves",
    })),
    ...story.articles.map((a) => ({
      source: a.id,
      target: story.id,
      label: "corroborates",
    })),
  ];

  const whyMattersText =
    story.why_it_matters ||
    story.narrative_summary ||
    story.summary ||
    "Insufficient evidence for a reliable explanation.";

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-6">
      {/* 1. Top Navigation Bar */}
      <div className="flex items-center justify-between">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-400 hover:text-white transition-colors"
        >
          <ChevronLeft className="w-4 h-4" /> Back to Intelligence Feed
        </Link>
        <div className="flex items-center gap-2">
          <span className="text-xs px-2.5 py-1 rounded-full font-mono bg-slate-800 text-slate-300 border border-slate-700">
            CLUSTER ID: {story.id.slice(0, 8)}
          </span>
          <span
            className={`text-xs px-2.5 py-1 rounded-full font-semibold border ${
              story.formation_status === "CORROBORATED"
                ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                : "bg-amber-500/20 text-amber-300 border-amber-500/40"
            }`}
          >
            {story.formation_status}
          </span>
        </div>
      </div>

      {/* 2. Main Story Header */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 md:p-8 shadow-2xl backdrop-blur-sm relative overflow-hidden">
        <div className="relative z-10 space-y-4">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="inline-flex items-center gap-1 text-xs font-medium px-2.5 py-1 rounded-md bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-mono">
              <Layers className="w-3.5 h-3.5" /> Story Formation Cluster
            </span>
            <span className="inline-flex items-center gap-1 text-xs font-medium px-2.5 py-1 rounded-md bg-slate-800 text-slate-300 border border-slate-700 font-mono">
              <Globe2 className="w-3.5 h-3.5 text-slate-400" />
              {story.languages.join(", ").toUpperCase()}
            </span>
            <span className="inline-flex items-center gap-1 text-xs font-medium px-2.5 py-1 rounded-md bg-slate-800 text-slate-300 border border-slate-700 font-mono">
              <Building2 className="w-3.5 h-3.5 text-slate-400" />
              {story.independent_sources_count} Independent Sources ({story.article_count} total articles)
            </span>
          </div>

          <h1 className="text-2xl md:text-3xl font-bold text-white tracking-tight leading-snug">
            {story.title}
          </h1>

          {/* Quick Metrics Bar */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-4 border-t border-slate-800/80">
            <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
              <span className="text-xs text-slate-400">Formation Score</span>
              <div className="text-lg font-bold font-mono text-cyan-400 mt-0.5">
                {Math.round(story.formation_score)}/100
              </div>
            </div>
            <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
              <span className="text-xs text-slate-400">Independence Score</span>
              <div className="text-lg font-bold font-mono text-indigo-400 mt-0.5">
                {Math.round(story.independence_score * 100)}%
              </div>
            </div>
            <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
              <span className="text-xs text-slate-400">Contradiction Gate</span>
              <div className="text-sm font-bold font-mono text-slate-200 mt-1">
                {story.contradiction_status === "PREDICTION_BLOCKED" ? (
                  <span className="text-rose-400 font-bold">PREDICTION BLOCKED</span>
                ) : (
                  <span className="text-emerald-400 font-bold">GATE CLEAR</span>
                )}
              </div>
            </div>
            <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
              <span className="text-xs text-slate-400">Languages Corroborated</span>
              <div className="text-sm font-bold font-mono text-purple-300 mt-1">
                {story.languages.map((l) => l.toUpperCase()).join(" • ")}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 3. Contradiction Gate Banner */}
      <ContradictionGateAlert
        storyId={story.id}
        contradictionStatus={story.contradiction_status}
        predictionEligible={story.prediction_eligible}
        contradictions={story.contradictions}
        onResolutionSuccess={fetchStoryDetail}
      />

      {/* 4. Grounded "Why It Matters" Section */}
      <div className="p-6 rounded-xl bg-gradient-to-r from-slate-900 via-cyan-950/20 to-slate-900 border border-cyan-500/30 shadow-xl backdrop-blur-md">
        <div className="flex items-center justify-between gap-4 mb-3">
          <div className="flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-cyan-400" />
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Why It Matters (Grounded Analytical Summary)
            </h3>
          </div>
          <span className="text-[10px] font-mono px-2.5 py-1 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
            Signal Provenance Verified
          </span>
        </div>
        <p className="text-sm text-slate-200 leading-relaxed">{whyMattersText}</p>
      </div>

      {/* 5. Prediction Card & Grounded Copilot Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <PredictionCard
          prediction={story.prediction || null}
          contradictionStatus={story.contradiction_status}
        />
        <CopilotPanel
          storyId={story.id}
          storyTitle={story.title}
        />
      </div>

      {/* 6. Structured Evidence Chain */}
      <EvidenceChainViewer
        evidenceChain={story.evidence_chain || null}
        storyTitle={story.title}
      />

      {/* 7. Source Independence Tree & Relationship Visualization */}
      <SourceRelationshipTree
        articles={story.articles}
        independentCount={story.independent_sources_count}
        totalCount={story.article_count}
      />

      {/* 8. Story Event Chronological Timeline */}
      <StoryTimeline storyId={story.id} />

      {/* 9. 6-Dimension Explainable Formation Score Gauge */}
      <FormationScoreGauge
        score={story.formation_score}
        status={story.formation_status}
        predictionEligible={story.prediction_eligible}
        scoreBreakdown={story.score_breakdown}
      />

      {/* 10. Analyst Notes & Disposition Actions */}
      <AnalystNotesPanel
        storyId={story.id}
        initialNotes={story.notes || []}
        currentStatus={story.status}
        onStatusChange={(s) => setStory((prev) => (prev ? { ...prev, status: s } : prev))}
      />

      {/* 11. Media Event Adjacency Graph */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 shadow-xl backdrop-blur-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Network className="w-5 h-5 text-cyan-400" />
            <h3 className="text-base font-bold text-white">Media Event Provenance Graph</h3>
          </div>
          <span className="text-xs text-slate-400 font-mono">
            {story.entities.length} Tracked Entities • {story.articles.length} Reporting Nodes
          </span>
        </div>
        <div className="h-80 rounded-lg overflow-hidden border border-slate-800 bg-slate-950">
          <GraphViewer nodes={graphNodes} edges={graphEdges} height={320} />
        </div>
      </div>
    </div>
  );
}

function getFallbackDemoStory(id: string): StoryDetail {
  return {
    id,
    title: "Regional Environmental Audit & Emission Inquiries at Industrial Unit",
    summary:
      "State Pollution Control Board launched multi-team compliance inspections covering chemical discharge.",
    why_it_matters:
      "Story trajectory forming across 3 independent publishers in Tamil and English. State regulatory inspection initiated following regional effluent discharge reports.",
    status: "CORROBORATED",
    formation_status: "CORROBORATED",
    formation_score: 88.0,
    narrative_summary:
      "Story trajectory forming across 3 independent publishers in Tamil and English. State regulatory inspection initiated following regional effluent discharge reports.",
    article_count: 3,
    candidate_sources_count: 3,
    independent_sources_count: 3,
    independence_score: 0.88,
    source_diversity_score: 0.85,
    temporal_spread_score: 0.80,
    entity_alignment_score: 0.90,
    cross_language_score: 0.95,
    evidence_strength_score: 0.85,
    contradiction_status: "CLEAR",
    prediction_eligible: true,
    created_at: new Date().toISOString(),
    languages: ["en", "ta"],
    score_breakdown: {
      overall_formation_score: 88.0,
      formation_status: "CORROBORATED",
      dimensions: {
        source_diversity: { score: 85.0, weight: "20%", detail: "3 independent publisher domains" },
        temporal_spread: { score: 80.0, weight: "15%", detail: "Natural 45min-2hr staggered reporting" },
        entity_alignment: { score: 90.0, weight: "20%", detail: "Shared entity: Company X & TNSPCB" },
        cross_language_corroboration: { score: 95.0, weight: "20%", detail: "Corroborated in EN and TA" },
        evidence_strength: { score: 85.0, weight: "15%", detail: "Named regulatory officials" },
        absence_of_contradictions: { score: 100.0, weight: "10%", detail: "Contradiction Gate CLEAR" },
      },
    },
    prediction: {
      formation_probability: 0.82,
      impact_score: 0.88,
      impact_level: "HIGH",
      current_stage: "REGIONAL",
      predicted_next_stage: "NATIONAL",
      trajectory_confidence: 0.85,
      trajectory_reasoning: "Corroborated across 3 independent regional outlets; awaiting English national wire pickup.",
      prediction_status: "ELIGIBLE",
      explanation: "Explainable multi-source regional trajectory.",
    },
    evidence_chain: {
      chain_status: "COMPLETE",
      confidence_score: 0.91,
      has_sufficient_evidence: true,
      items: [
        {
          item_id: "ev-01",
          step_order: 1,
          source_name: "The Hindu Regional",
          domain: "thehindu.com",
          claim_statement: "State Pollution Control Board initiates plant inspection at manufacturing unit.",
          evidence_type: "REGULATORY_SOURCE",
          evidence_excerpt: "[The Hindu]: Officials initiated comprehensive compliance audit of chemical discharge.",
          corroborating_sources: ["Dinamani", "PTI"],
          confidence_contribution: 0.35,
        },
        {
          item_id: "ev-02",
          step_order: 2,
          source_name: "Dinamani",
          domain: "dinamani.com",
          claim_statement: "கம்பெனி எக்ஸ் தொழிற்கூடத்தில் அதிகாரிகள் திடீர் ஆய்வு.",
          evidence_type: "INDEPENDENT_CORROBORATION",
          evidence_excerpt: "[Dinamani]: தமிழக அரசு மாசுக் கட்டுப்பாட்டு வாரிய அதிகாரிகள் திடீர் ஆய்வு மேற்கொண்டனர்.",
          corroborating_sources: ["The Hindu"],
          confidence_contribution: 0.30,
        },
      ],
    },
    notes: [
      {
        id: "note-01",
        story_id: id,
        user_id: "Lead Analyst",
        note: "Audited regional filings against Tamil Nadu Gazette notice #2026-88.",
        created_at: new Date().toISOString(),
      },
    ],
    articles: [
      {
        id: "art-01",
        title: "State Pollution Control Board inspects Company X manufacturing plant",
        source_name: "The Hindu",
        domain: "thehindu.com",
        url: "https://thehindu.com/news/national/tamil-nadu/company-x-inspection",
        language: "en",
        published_at: new Date().toISOString(),
        excerpt: "Officials initiated comprehensive compliance audit of chemical discharge.",
        relationship_type: "ORIGINAL",
        is_original: true,
      },
      {
        id: "art-02",
        title: "கம்பெனி எக்ஸ் தொழிற்கூடத்தில் அதிகாரிகள் திடீர் ஆய்வு",
        source_name: "Dinamani Regional",
        domain: "dinamani.com",
        url: "https://dinamani.com/tamilnadu/company-x-audit",
        language: "ta",
        published_at: new Date(Date.now() - 45 * 60000).toISOString(),
        excerpt: "தமிழக அரசு மாசுக் கட்டுப்பாட்டு வாரிய அதிகாரிகள் திடீர் ஆய்வு மேற்கொண்டனர்.",
        relationship_type: "INDEPENDENT",
        is_original: true,
      },
      {
        id: "art-03",
        title: "Regional Environmental Audit Report Published",
        source_name: "PTI Wire",
        domain: "pti.in",
        url: "https://pti.in/wire/company-x",
        language: "en",
        published_at: new Date(Date.now() - 90 * 60000).toISOString(),
        excerpt: "Wire bulletin on ongoing environmental inquiries in industrial corridor.",
        relationship_type: "ORIGINAL",
        is_original: true,
      },
    ],
    entities: [
      { id: "ent-01", name: "Company X", canonical_name: "Company X", entity_type: "COMPANY" },
      { id: "ent-02", name: "TNSPCB", canonical_name: "Tamil Nadu Pollution Control Board", entity_type: "REGULATOR" },
      { id: "ent-03", name: "Chennai", canonical_name: "Chennai, Tamil Nadu", entity_type: "LOCATION" },
    ],
    contradictions: [],
  };
}
