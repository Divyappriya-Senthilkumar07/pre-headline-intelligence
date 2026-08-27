"use client";

import React, { useState } from "react";
import { Network, Building2, Calendar, FileText, ArrowRight, ShieldCheck, Sparkles } from "lucide-react";

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  details?: string;
  group?: number;
}

export interface GraphEdgeItem {
  source: string;
  target: string;
  relation?: string;
  relationship?: string;
  weight?: number;
}

export interface GraphViewerProps {
  nodes: GraphNode[];
  edges: GraphEdgeItem[];
  title?: string;
  height?: number;
}

export const GraphViewer: React.FC<GraphViewerProps> = ({
  nodes,
  edges,
  title = "Media Event Graph (PostgreSQL Adjacency List)",
}) => {
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(nodes[0] || null);

  const getNodeColor = (type: string) => {
    switch (type) {
      case "ENTITY":
        return {
          bg: "bg-indigo-950/80 border-indigo-500/50 text-indigo-200",
          badge: "bg-indigo-900/60 text-indigo-300 border-indigo-700/50",
          icon: Building2,
        };
      case "EVENT":
        return {
          bg: "bg-amber-950/80 border-amber-500/50 text-amber-200",
          badge: "bg-amber-900/60 text-amber-300 border-amber-700/50",
          icon: Calendar,
        };
      case "ARTICLE":
        return {
          bg: "bg-cyan-950/80 border-cyan-500/50 text-cyan-200",
          badge: "bg-cyan-900/60 text-cyan-300 border-cyan-700/50",
          icon: FileText,
        };
      case "SOURCE":
      default:
        return {
          bg: "bg-emerald-950/80 border-emerald-500/50 text-emerald-200",
          badge: "bg-emerald-900/60 text-emerald-300 border-emerald-700/50",
          icon: ShieldCheck,
        };
    }
  };

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-xl">
      <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-lg bg-indigo-950 border border-indigo-500/30 text-indigo-400">
            <Network className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-slate-100">{title}</h4>
            <p className="text-xs text-slate-400">
              {nodes.length} Nodes · {edges.length} Bounded Multi-Hop Edges
            </p>
          </div>
        </div>

        {/* Legend */}
        <div className="hidden sm:flex items-center gap-2 text-[11px]">
          <span className="px-2 py-0.5 rounded bg-indigo-950/70 border border-indigo-500/40 text-indigo-300">
            Entity
          </span>
          <span className="px-2 py-0.5 rounded bg-amber-950/70 border border-amber-500/40 text-amber-300">
            Event
          </span>
          <span className="px-2 py-0.5 rounded bg-cyan-950/70 border border-cyan-500/40 text-cyan-300">
            Article
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Nodes Grid */}
        <div className="lg:col-span-2 space-y-2.5">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
            Discovered Graph Nodes & Entities
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 max-h-72 overflow-y-auto pr-1">
            {nodes.map((node) => {
              const style = getNodeColor(node.type);
              const Icon = style.icon;
              const isSelected = selectedNode?.id === node.id;

              return (
                <button
                  key={node.id}
                  onClick={() => setSelectedNode(node)}
                  className={`flex items-start gap-3 p-3 rounded-lg border text-left transition-all ${
                    isSelected
                      ? `${style.bg} ring-2 ring-cyan-400/50 shadow-md`
                      : "bg-slate-900/40 border-slate-800/80 hover:bg-slate-850 hover:border-slate-700 text-slate-300"
                  }`}
                >
                  <div className={`p-1.5 rounded-md border ${style.badge}`}>
                    <Icon className="w-3.5 h-3.5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-1 mb-0.5">
                      <span className="text-xs font-semibold truncate text-slate-100">{node.label}</span>
                      <span className="text-[10px] font-mono uppercase text-slate-400">
                        {node.type}
                      </span>
                    </div>
                    {node.details && (
                      <p className="text-[11px] text-slate-400 truncate">{node.details}</p>
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Selected Node Connections & Edges */}
        <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-800/80">
              <span className="text-xs font-semibold text-slate-300">Active Node Relationships</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                Depth 2 Expansion
              </span>
            </div>

            {selectedNode ? (
              <div className="space-y-3">
                <div className="p-2.5 rounded bg-slate-900/80 border border-slate-800">
                  <div className="text-[11px] text-slate-400">Selected Subject:</div>
                  <div className="text-sm font-semibold text-cyan-300">{selectedNode.label}</div>
                  <div className="text-[10px] font-mono text-slate-400 uppercase mt-0.5">
                    Type: {selectedNode.type}
                  </div>
                </div>

                <div className="text-xs font-medium text-slate-400">Connected Graph Edges:</div>
                <div className="space-y-1.5 max-h-40 overflow-y-auto pr-1">
                  {edges
                    .filter(
                      (e) =>
                        e.source === selectedNode.id ||
                        e.target === selectedNode.id ||
                        nodes.some((n) => n.id === e.source && n.label === selectedNode.label)
                    )
                    .map((edge, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between text-xs p-2 rounded bg-slate-900/60 border border-slate-800/80 text-slate-300"
                      >
                        <span className="font-mono text-[11px] text-amber-300 truncate">
                          {edge.relation}
                        </span>
                        <div className="flex items-center gap-1 text-[11px] text-slate-400">
                          <span>w: {(edge.weight ?? 1.0).toFixed(2)}</span>
                          <ArrowRight className="w-3 h-3 text-slate-500" />
                        </div>
                      </div>
                    ))}

                  {edges.filter(
                    (e) =>
                      e.source === selectedNode.id ||
                      e.target === selectedNode.id ||
                      nodes.some((n) => n.id === e.source && n.label === selectedNode.label)
                  ).length === 0 && (
                    <div className="text-xs text-slate-500 italic py-2 text-center">
                      No direct edges for this node in the current depth view.
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-xs text-slate-500 italic py-8 text-center">
                Select a node to inspect its graph connections.
              </div>
            )}
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800/80 text-[11px] text-slate-500 flex items-center justify-between">
            <span>PostgreSQL `graph_edges` table</span>
            <span className="text-emerald-400 font-mono">Status: Connected</span>
          </div>
        </div>
      </div>
    </div>
  );
};
