"use client";

import React, { useState, useEffect } from "react";
import {
  BookmarkCheck,
  Plus,
  Trash2,
  ToggleLeft,
  ToggleRight,
  Search,
  Building2,
  Tag,
  Languages,
  Check,
  AlertCircle,
  ExternalLink,
} from "lucide-react";

interface WatchlistItem {
  id: string;
  name: string;
  description?: string | null;
  entities: string[];
  keywords: string[];
  languages: string[];
  is_active: boolean;
  matching_stories_count: number;
  created_at: string;
  updated_at: string;
}

export default function WatchlistsPage() {
  const [watchlists, setWatchlists] = useState<WatchlistItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);

  // Form State
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [entitiesInput, setEntitiesInput] = useState("");
  const [keywordsInput, setKeywordsInput] = useState("");
  const [selectedLangs, setSelectedLangs] = useState<string[]>(["ta", "hi", "en"]);
  const [submitting, setSubmitting] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  const fetchWatchlists = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/watchlists");
      if (res.ok) {
        const data = await res.json();
        setWatchlists(data);
      }
    } catch (err) {
      console.warn("Watchlists fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWatchlists();
  }, []);

  const handleCreateWatchlist = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || submitting) return;

    setSubmitting(true);
    const entities = entitiesInput.split(",").map((s) => s.trim()).filter(Boolean);
    const keywords = keywordsInput.split(",").map((s) => s.trim()).filter(Boolean);

    try {
      const res = await fetch("http://localhost:8000/api/v1/watchlists", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          description,
          entities,
          keywords,
          languages: selectedLangs,
        }),
      });

      if (res.ok) {
        const newWl = await res.json();
        setWatchlists((prev) => [newWl, ...prev]);
        setShowModal(false);
        setName("");
        setDescription("");
        setEntitiesInput("");
        setKeywordsInput("");
        setStatusMsg("Watchlist created successfully.");
        setTimeout(() => setStatusMsg(null), 3000);
      }
    } catch (err) {
      console.error("Create watchlist error:", err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleToggle = async (wlId: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/watchlists/${wlId}/toggle`, {
        method: "POST",
      });
      if (res.ok) {
        const data = await res.json();
        setWatchlists((prev) =>
          prev.map((w) => (w.id === wlId ? { ...w, is_active: data.is_active } : w))
        );
      }
    } catch (err) {
      console.error("Toggle error:", err);
    }
  };

  const handleDelete = async (wlId: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/watchlists/${wlId}`, {
        method: "DELETE",
      });
      if (res.ok || res.status === 204) {
        setWatchlists((prev) => prev.filter((w) => w.id !== wlId));
      }
    } catch (err) {
      console.error("Delete error:", err);
    }
  };

  const toggleLanguage = (lang: string) => {
    setSelectedLangs((prev) =>
      prev.includes(lang) ? prev.filter((l) => l !== lang) : [...prev, lang]
    );
  };

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-md bg-cyan-500/10 text-cyan-400 text-xs font-mono mb-2 border border-cyan-500/20">
            <BookmarkCheck className="w-3.5 h-3.5" />
            AGENT 1 DISCOVERY TRACKING
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
            Analyst Watchlists & Entity Radar
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1 max-w-2xl">
            Targeted tracking profiles that feed Agent 1 Discovery and context enrichment pipelines.
          </p>
        </div>

        <button
          onClick={() => setShowModal(true)}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold shadow-lg shadow-cyan-500/20 transition-all shrink-0"
        >
          <Plus className="w-4 h-4" /> Create Watchlist
        </button>
      </div>

      {statusMsg && (
        <div className="p-3 rounded-lg bg-emerald-950/40 border border-emerald-500/40 text-emerald-300 text-xs flex items-center gap-2">
          <Check className="w-4 h-4" /> {statusMsg}
        </div>
      )}

      {/* Watchlists Grid */}
      {loading ? (
        <div className="p-12 text-center text-slate-400 bg-slate-900/40 rounded-2xl border border-slate-800">
          <div className="w-8 h-8 border-4 border-cyan-500/20 border-t-cyan-500 rounded-full animate-spin mx-auto mb-3" />
          <p className="text-xs font-mono">Loading Analyst Watchlists...</p>
        </div>
      ) : watchlists.length === 0 ? (
        <div className="p-12 text-center text-slate-400 bg-slate-900/40 rounded-2xl border border-slate-800">
          <BookmarkCheck className="w-8 h-8 text-slate-600 mx-auto mb-3" />
          <p className="text-sm font-medium text-slate-300">No watchlists configured.</p>
          <p className="text-xs text-slate-500 mt-1">Create a watchlist to begin monitoring entities and topics.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {watchlists.map((wl) => (
            <div
              key={wl.id}
              className={`p-6 rounded-2xl border transition-all relative overflow-hidden backdrop-blur-sm ${
                wl.is_active
                  ? "bg-slate-900/90 border-slate-800 shadow-xl"
                  : "bg-slate-950/40 border-slate-900 opacity-60"
              }`}
            >
              <div className="flex items-start justify-between gap-4 mb-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <h3 className="text-base font-bold text-white tracking-tight">{wl.name}</h3>
                    <span
                      className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${
                        wl.is_active
                          ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                          : "bg-slate-800 text-slate-400 border-slate-700"
                      }`}
                    >
                      {wl.is_active ? "ACTIVE" : "PAUSED"}
                    </span>
                  </div>
                  {wl.description && (
                    <p className="text-xs text-slate-400 leading-relaxed">{wl.description}</p>
                  )}
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={() => handleToggle(wl.id)}
                    className="text-slate-400 hover:text-cyan-400 transition-colors"
                    title={wl.is_active ? "Pause Watchlist" : "Activate Watchlist"}
                  >
                    {wl.is_active ? (
                      <ToggleRight className="w-6 h-6 text-cyan-400" />
                    ) : (
                      <ToggleLeft className="w-6 h-6 text-slate-600" />
                    )}
                  </button>
                  <button
                    onClick={() => handleDelete(wl.id)}
                    className="p-1 text-slate-500 hover:text-rose-400 transition-colors"
                    title="Delete Watchlist"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Target Entities & Keywords */}
              <div className="space-y-3 pt-3 border-t border-slate-800/80 text-xs">
                <div>
                  <span className="text-[10px] font-mono uppercase text-slate-500 flex items-center gap-1 mb-1.5">
                    <Building2 className="w-3 h-3 text-cyan-400" /> Tracked Entities:
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {wl.entities.map((e, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-0.5 rounded bg-slate-950 text-slate-300 border border-slate-800 text-[11px]"
                      >
                        {e}
                      </span>
                    ))}
                  </div>
                </div>

                {wl.keywords.length > 0 && (
                  <div>
                    <span className="text-[10px] font-mono uppercase text-slate-500 flex items-center gap-1 mb-1.5">
                      <Tag className="w-3 h-3 text-purple-400" /> Tracked Keywords:
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {wl.keywords.map((k, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-0.5 rounded bg-slate-950 text-slate-400 border border-slate-800 text-[10px] font-mono"
                        >
                          #{k}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Footer Metrics */}
                <div className="pt-3 border-t border-slate-800/60 flex items-center justify-between text-[11px] text-slate-400">
                  <span className="flex items-center gap-1 font-mono">
                    <Languages className="w-3 h-3 text-purple-400" />
                    {wl.languages.map((l) => l.toUpperCase()).join(", ")}
                  </span>
                  <span className="font-mono text-cyan-400 font-semibold">
                    {wl.matching_stories_count} matching stories
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal: Create Watchlist */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-fade-in">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <BookmarkCheck className="w-5 h-5 text-cyan-400" />
                Configure New Analyst Watchlist
              </h3>
              <button
                onClick={() => setShowModal(false)}
                className="text-xs text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateWatchlist} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-300 font-medium mb-1">Watchlist Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g., Strategic Environmental & Compliance Radar"
                  required
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-medium mb-1">Description</label>
                <input
                  type="text"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Brief analytical objective"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-medium mb-1">Tracked Entities (comma separated)</label>
                <input
                  type="text"
                  value={entitiesInput}
                  onChange={(e) => setEntitiesInput(e.target.value)}
                  placeholder="Company X, State Board, Ministry of Power"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-medium mb-1">Keywords & Topics (comma separated)</label>
                <input
                  type="text"
                  value={keywordsInput}
                  onChange={(e) => setKeywordsInput(e.target.value)}
                  placeholder="inspection, audit, sanction, discharge, lawsuit"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-medium mb-2">Ingestion Languages</label>
                <div className="flex items-center gap-2">
                  {[
                    { code: "ta", label: "Tamil (தமிழ்)" },
                    { code: "hi", label: "Hindi (हिन्दी)" },
                    { code: "en", label: "English" },
                  ].map((l) => {
                    const isSelected = selectedLangs.includes(l.code);
                    return (
                      <button
                        key={l.code}
                        type="button"
                        onClick={() => toggleLanguage(l.code)}
                        className={`px-3 py-1.5 rounded-lg border font-mono transition-colors ${
                          isSelected
                            ? "bg-cyan-500/20 text-cyan-300 border-cyan-500/60"
                            : "bg-slate-950 text-slate-500 border-slate-800"
                        }`}
                      >
                        {l.label}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting || !name.trim()}
                  className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold disabled:opacity-50"
                >
                  {submitting ? "Saving..." : "Save Watchlist"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
